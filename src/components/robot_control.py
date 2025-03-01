from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                           QPushButton, QLabel, QSpinBox, QDoubleSpinBox, 
                           QGroupBox, QGridLayout, QTabWidget, QLineEdit,
                           QCheckBox)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class RobotControl(QWidget):
    position_updated = pyqtSignal(dict)  # Signal to emit when position is updated
    connection_status_changed = pyqtSignal(bool)  # Signal to emit when connection status changes
    log_message = pyqtSignal(str)  # Signal to emit log messages
    response_received = pyqtSignal(str, object)  # Signal for device responses (response, device)

    def __init__(self):
        super().__init__()
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.read_data)
        self.buffer = ""
        self.last_command = None
        
        # Auto-connect timers
        self.auto_connect_timer = QTimer()
        self.auto_connect_timer.timeout.connect(self.try_auto_connect)
        self.port_response_timer = QTimer()
        self.port_response_timer.timeout.connect(self.port_timeout)
        self.port_response_timer.setSingleShot(True)  # Timer runs only once
        
        self.current_test_port = None
        self.ports_to_test = []
        self.init_ui()
        self.update_ports()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top section with Connection and System Commands side by side
        top_layout = QHBoxLayout()
        
        # Connection group
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(10)  # Add spacing between elements
        
        # Port selection
        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        port_layout.addWidget(QLabel("Port:"))
        port_layout.addWidget(self.port_combo)
        connection_layout.addLayout(port_layout)
        
        # Auto-connect checkbox
        self.auto_connect_cb = QCheckBox("Auto Connect")
        self.auto_connect_cb.stateChanged.connect(self.toggle_auto_connect)
        connection_layout.addWidget(self.auto_connect_cb)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_ports)
        connection_layout.addWidget(self.refresh_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_btn)
        
        connection_layout.addStretch()
        connection_group.setLayout(connection_layout)
        connection_group.setMaximumHeight(100)  # Limit height of connection group
        top_layout.addWidget(connection_group)

        # System commands group
        sys_group = QGroupBox("System Commands")
        sys_layout = QHBoxLayout()
        sys_layout.setSpacing(10)  # Add spacing between elements

        reset_btn = QPushButton("Reset (M999)")
        reset_btn.clicked.connect(lambda: self.send_gcode("M999"))
        sys_layout.addWidget(reset_btn)

        stop_btn = QPushButton("Emergency Stop (M112)")
        stop_btn.clicked.connect(lambda: self.send_gcode("M112"))
        stop_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        sys_layout.addWidget(stop_btn)

        sys_group.setLayout(sys_layout)
        sys_group.setMaximumHeight(100)  # Match height with connection group
        top_layout.addWidget(sys_group)
        
        # Add top section to main layout
        layout.addLayout(top_layout)

        # Create tab widget for robot controls
        tab_widget = QTabWidget()

        # Position control tab
        pos_tab = QWidget()
        pos_layout = QHBoxLayout()  # Change to horizontal layout for two columns
        
        # Left column
        left_column = QVBoxLayout()
        
        # Position control group
        pos_group = QGroupBox("Position Control")
        pos_grid = QGridLayout()
        
        # X, Y, Z position
        self.pos_spinboxes = {}
        for i, axis in enumerate(['X', 'Y', 'Z']):
            label = QLabel(f"{axis}:")
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-1000, 1000)
            spinbox.setSingleStep(1)
            spinbox.setDecimals(2)
            pos_grid.addWidget(label, i, 0)
            pos_grid.addWidget(spinbox, i, 1)
            self.pos_spinboxes[axis] = spinbox
            
        # W, U, V angles
        for i, axis in enumerate(['W', 'U', 'V']):
            label = QLabel(f"{axis}:")
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-360, 360)
            spinbox.setSingleStep(1)
            spinbox.setDecimals(2)
            pos_grid.addWidget(label, i, 2)
            pos_grid.addWidget(spinbox, i, 3)
            self.pos_spinboxes[axis] = spinbox

        # Movement parameters in their own group
        move_params_group = QGroupBox("Movement Parameters")
        move_params_layout = QGridLayout()
        
        self.feed_rate = QSpinBox()
        self.feed_rate.setRange(0, 1000)
        self.feed_rate.setValue(200)
        move_params_layout.addWidget(QLabel("Feed Rate (mm/s):"), 0, 0)
        move_params_layout.addWidget(self.feed_rate, 0, 1)
        
        self.acceleration = QSpinBox()
        self.acceleration.setRange(0, 10000)
        self.acceleration.setValue(5000)
        move_params_layout.addWidget(QLabel("Acceleration (mm/s²):"), 1, 0)
        move_params_layout.addWidget(self.acceleration, 1, 1)

        self.start_velocity = QSpinBox()
        self.start_velocity.setRange(0, 1000)
        self.start_velocity.setValue(0)
        move_params_layout.addWidget(QLabel("Start Velocity (mm/s):"), 2, 0)
        move_params_layout.addWidget(self.start_velocity, 2, 1)

        self.end_velocity = QSpinBox()
        self.end_velocity.setRange(0, 1000)
        self.end_velocity.setValue(0)
        move_params_layout.addWidget(QLabel("End Velocity (mm/s):"), 3, 0)
        move_params_layout.addWidget(self.end_velocity, 3, 1)

        self.junction_deviation = QDoubleSpinBox()
        self.junction_deviation.setRange(0, 10)
        self.junction_deviation.setValue(0.1)
        self.junction_deviation.setSingleStep(0.01)
        move_params_layout.addWidget(QLabel("Junction Deviation:"), 4, 0)
        move_params_layout.addWidget(self.junction_deviation, 4, 1)
        
        move_params_group.setLayout(move_params_layout)
        pos_grid.addWidget(move_params_group, 5, 0, 1, 4)

        # Movement buttons in a horizontal layout
        move_buttons = QHBoxLayout()
        
        move_btn = QPushButton("Move (G1)")
        move_btn.clicked.connect(self.send_move_command)
        move_buttons.addWidget(move_btn)
        
        home_btn = QPushButton("Home (G28)")
        home_btn.clicked.connect(self.home_robot)
        move_buttons.addWidget(home_btn)
        
        get_pos_btn = QPushButton("Get Position (G93)")
        get_pos_btn.clicked.connect(lambda: self.send_gcode("G93"))
        move_buttons.addWidget(get_pos_btn)
        
        pos_grid.addLayout(move_buttons, 6, 0, 1, 4)

        # Arc movement buttons
        arc_buttons = QHBoxLayout()
        
        arc_cw_btn = QPushButton("Arc CW (G2)")
        arc_cw_btn.clicked.connect(self.send_arc_command_cw)
        arc_buttons.addWidget(arc_cw_btn)

        arc_ccw_btn = QPushButton("Arc CCW (G3)")
        arc_ccw_btn.clicked.connect(self.send_arc_command_ccw)
        arc_buttons.addWidget(arc_ccw_btn)
        
        pos_grid.addLayout(arc_buttons, 7, 0, 1, 4)

        # Mode buttons
        mode_buttons = QHBoxLayout()
        
        self.abs_mode_btn = QPushButton("Absolute Mode (G90)")
        self.abs_mode_btn.clicked.connect(self.set_absolute_mode)
        mode_buttons.addWidget(self.abs_mode_btn)
        
        self.rel_mode_btn = QPushButton("Relative Mode (G91)")
        self.rel_mode_btn.clicked.connect(self.set_relative_mode)
        mode_buttons.addWidget(self.rel_mode_btn)
        
        pos_grid.addLayout(mode_buttons, 8, 0, 1, 4)

        pos_group.setLayout(pos_grid)
        left_column.addWidget(pos_group)
        
        # Add left column to main layout
        pos_layout.addLayout(left_column)

        # Right column
        right_column = QVBoxLayout()
        
        # Jog control group
        jog_group = QGroupBox("Jog Control")
        jog_layout = QGridLayout()

        # Step size selection at top
        self.step_size = QDoubleSpinBox()
        self.step_size.setRange(0.1, 100)
        self.step_size.setValue(10)
        self.step_size.setSingleStep(0.1)
        jog_layout.addWidget(QLabel("Step Size (mm):"), 0, 0, 1, 2)
        jog_layout.addWidget(self.step_size, 0, 2, 1, 2)

        # Create jog buttons in a grid
        jog_buttons = {
            'X+': (1, 2), 'X-': (1, 0),
            'Y+': (2, 2), 'Y-': (2, 0),
            'Z+': (3, 2), 'Z-': (3, 0),
            'W+': (4, 2), 'W-': (4, 0),
            'U+': (5, 2), 'U-': (5, 0),
            'V+': (6, 2), 'V-': (6, 0),
        }

        # Make buttons larger
        button_style = "QPushButton { min-width: 50px; min-height: 50px; }"
        
        for label, (row, col) in jog_buttons.items():
            btn = QPushButton(label)
            btn.setStyleSheet(button_style)
            axis = label[0]
            direction = 1 if '+' in label else -1
            if axis in ['W', 'U', 'V']:  # For rotational axes
                btn.pressed.connect(lambda a=axis, d=direction: self.start_angle_jog(a, d))
                btn.released.connect(lambda a=axis: self.stop_angle_jog(a))
            else:  # For linear axes
                btn.pressed.connect(lambda a=axis, d=direction: self.start_jog(a, d))
                btn.released.connect(lambda a=axis: self.stop_jog(a))
            jog_layout.addWidget(btn, row, col)
            # Add axis labels in middle column
            if col == 0:  # Only add label once per axis
                label = QLabel(axis)
                label.setAlignment(Qt.AlignCenter)
                jog_layout.addWidget(label, row, 1)

        jog_group.setLayout(jog_layout)
        right_column.addWidget(jog_group)

        # Add spacer to push jog control to top
        right_column.addStretch()
        
        # Add right column to main layout
        pos_layout.addLayout(right_column)
        
        pos_tab.setLayout(pos_layout)
        tab_widget.addTab(pos_tab, "Position")

        # Manual command tab
        manual_tab = QWidget()
        manual_layout = QVBoxLayout()
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter G-code command...")
        self.command_input.returnPressed.connect(self.send_manual_command)
        manual_layout.addWidget(self.command_input)
        
        send_btn = QPushButton("Send Command")
        send_btn.clicked.connect(self.send_manual_command)
        manual_layout.addWidget(send_btn)
        
        manual_tab.setLayout(manual_layout)
        tab_widget.addTab(manual_tab, "Manual Command")

        # Output control tab
        output_tab = QWidget()
        output_layout = QVBoxLayout()
        
        # Digital outputs
        digital_group = QGroupBox("Digital Outputs")
        digital_layout = QGridLayout()
        
        self.digital_spinbox = QSpinBox()
        self.digital_spinbox.setRange(0, 15)
        digital_layout.addWidget(QLabel("Digital Pin:"), 0, 0)
        digital_layout.addWidget(self.digital_spinbox, 0, 1)
        
        digital_on_btn = QPushButton("ON (M03)")
        digital_on_btn.clicked.connect(self.digital_output_on)
        digital_layout.addWidget(digital_on_btn, 0, 2)
        
        digital_off_btn = QPushButton("OFF (M05)")
        digital_off_btn.clicked.connect(self.digital_output_off)
        digital_layout.addWidget(digital_off_btn, 0, 3)
        
        digital_group.setLayout(digital_layout)
        output_layout.addWidget(digital_group)
        
        # PWM outputs
        pwm_group = QGroupBox("PWM Outputs")
        pwm_layout = QGridLayout()
        
        self.pwm_pin_spinbox = QSpinBox()
        self.pwm_pin_spinbox.setRange(0, 15)
        pwm_layout.addWidget(QLabel("PWM Pin:"), 0, 0)
        pwm_layout.addWidget(self.pwm_pin_spinbox, 0, 1)
        
        self.pwm_value_spinbox = QSpinBox()
        self.pwm_value_spinbox.setRange(0, 255)
        pwm_layout.addWidget(QLabel("PWM Value:"), 0, 2)
        pwm_layout.addWidget(self.pwm_value_spinbox, 0, 3)
        
        pwm_set_btn = QPushButton("Set PWM (M03)")
        pwm_set_btn.clicked.connect(self.set_pwm_output)
        pwm_layout.addWidget(pwm_set_btn, 0, 4)
        
        pwm_group.setLayout(pwm_layout)
        output_layout.addWidget(pwm_group)
        
        output_layout.addStretch()
        output_tab.setLayout(output_layout)
        tab_widget.addTab(output_tab, "Outputs")

        layout.addWidget(tab_widget)

    def update_ports(self):
        """Update available COM ports, filtering out non-physical ports"""
        self.port_combo.clear()
        for port in QSerialPortInfo.availablePorts():
            # Only add physical ports (USB or COM)
            if (port.hasProductIdentifier() or 
                port.hasVendorIdentifier() or 
                (port.portName().startswith("COM") and port.portName() != "COM1")):
                self.port_combo.addItem(port.portName())

    def toggle_connection(self):
        if not self.serial_port.isOpen():  # Connect
            if self.auto_connect_cb.isChecked():
                # Start auto-connect process
                self.connect_btn.setText("Searching...")
                self.port_combo.setEnabled(False)
                self.refresh_btn.setEnabled(False)
                self.start_auto_connect()
            else:
                # Normal connection process
                try:
                    self.serial_port.setPortName(self.port_combo.currentText())
                    self.serial_port.setBaudRate(QSerialPort.Baud115200)
                    if self.serial_port.open(QSerialPort.ReadWrite):
                        self.connect_btn.setText("Disconnect")
                        self.port_combo.setEnabled(False)
                        self.refresh_btn.setEnabled(False)
                        self.connection_status_changed.emit(True)
                        self.log_message.emit(f"Connected to {self.port_combo.currentText()} at 115200 baud")
                        # Get current position
                        self.send_gcode("G93")
                    else:
                        self.log_message.emit(f"Failed to open port {self.port_combo.currentText()}")
                except Exception as e:
                    self.log_message.emit(f"Error: {str(e)}")
        else:  # Disconnect
            self.stop_auto_connect()  # Stop any auto-connect process
            self.serial_port.close()
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.connection_status_changed.emit(False)
            self.log_message.emit("Disconnected")

    def send_gcode(self, command):
        if self.serial_port.isOpen():
            try:
                # Add newline if not present
                if not command.endswith('\n'):
                    command += '\n'
                self.serial_port.write(command.encode())
                self.last_command = command.strip()  # Store last command without newline
                self.log_message.emit(f"Sent: {command.strip()}")
            except Exception as e:
                self.log_message.emit(f"Error sending command: {str(e)}")
        else:
            self.log_message.emit("Error: Not connected to robot")

    def read_data(self):
        """Read data from serial port"""
        while self.serial_port.canReadLine():
            data = self.serial_port.readLine().data().decode().strip()
            self.log_message.emit(f"Received: {data}")
            self.response_received.emit(data, self)  # Emit response with self as device
            
            # Handle special responses
            if data == "YesDelta" and self.last_command == "IsDelta":
                self.log_message.emit("Robot detected!")
                # Stop auto-connect process since we found the robot
                self.port_response_timer.stop()
                self.auto_connect_timer.stop()
                # Update UI to show current port
                self.port_combo.setCurrentText(self.serial_port.portName())
                self.connect_btn.setText("Disconnect")
                self.port_combo.setEnabled(False)
                self.refresh_btn.setEnabled(False)
                self.connection_status_changed.emit(True)
                # Get current position
                self.send_gcode("G93")
            elif data == "ok" and self.last_command == "G28":
                # After homing, request current position
                self.send_gcode("G93")
            
            # Parse position data
            if ',' in data and len(data.split(',')) >= 3:
                try:
                    x, y, z = map(float, data.split(',')[:3])
                    self.pos_spinboxes['X'].setValue(x)
                    self.pos_spinboxes['Y'].setValue(y)
                    self.pos_spinboxes['Z'].setValue(z)
                    self.position_updated.emit({'X': x, 'Y': y, 'Z': z})
                except ValueError:
                    pass

    def send_move_command(self):
        command = "G1"
        # Add position parameters if changed
        for axis, spinbox in self.pos_spinboxes.items():
            if not spinbox.value() == 0:
                command += f" {axis}{spinbox.value()}"
        # Add movement parameters
        if self.feed_rate.value() > 0:
            command += f" F{self.feed_rate.value()}"
        if self.acceleration.value() > 0:
            command += f" A{self.acceleration.value()}"
        if self.junction_deviation.value() > 0:
            command += f" J{self.junction_deviation.value()}"
        if self.start_velocity.value() > 0:
            command += f" S{self.start_velocity.value()}"
        if self.end_velocity.value() > 0:
            command += f" E{self.end_velocity.value()}"
        self.send_gcode(command)

    def home_robot(self):
        """Send home command and store it as last command"""
        self.send_gcode("G28")

    def set_absolute_mode(self):
        self.send_gcode("G90")
        self.abs_mode_btn.setStyleSheet("background-color: #27ae60")
        self.rel_mode_btn.setStyleSheet("")

    def set_relative_mode(self):
        self.send_gcode("G91")
        self.rel_mode_btn.setStyleSheet("background-color: #27ae60")
        self.abs_mode_btn.setStyleSheet("")

    def start_jog(self, axis, direction):
        """Start jog movement with current step size"""
        step = self.step_size.value() * direction
        self.send_gcode("G91")  # Set to relative mode
        self.send_gcode(f"G1 {axis}{step} F{self.feed_rate.value()}")

    def stop_jog(self, axis):
        """Stop jog movement"""
        self.send_gcode("G90")  # Return to absolute mode
        self.send_gcode("G93")  # Get current position

    def digital_output_on(self):
        pin = self.digital_spinbox.value()
        self.send_gcode(f"M03 D{pin}")

    def digital_output_off(self):
        pin = self.digital_spinbox.value()
        self.send_gcode(f"M05 D{pin}")

    def set_pwm_output(self):
        pin = self.pwm_pin_spinbox.value()
        value = self.pwm_value_spinbox.value()
        self.send_gcode(f"M03 P{pin} W{value}")

    def send_manual_command(self):
        command = self.command_input.text()
        if command:
            self.send_gcode(command)
            self.command_input.clear()

    def toggle_auto_connect(self, state):
        """Only update checkbox state, actual auto-connect starts when clicking connect"""
        if not state and self.serial_port.isOpen():
            # If turning off auto-connect while connected, stay connected
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)

    def try_auto_connect(self):
        """Periodic check for auto-connect status"""
        if not self.serial_port.isOpen():
            self.try_next_port()

    def start_auto_connect(self):
        """Start the auto-connect process"""
        self.ports_to_test = [port.portName() for port in QSerialPortInfo.availablePorts()]
        if self.ports_to_test:
            # Start the auto-connect timer
            self.auto_connect_timer.start(2000)  # Check every 2 seconds
            self.try_next_port()
        else:
            self.log_message.emit("No COM ports available")
            self.auto_connect_cb.setChecked(False)

    def try_next_port(self):
        """Try connecting to the next available port"""
        if self.ports_to_test:
            self.current_test_port = self.ports_to_test.pop(0)
            if self.try_connect_to_port(self.current_test_port):
                # Send IsDelta command to check if this is a robot
                self.send_gcode("IsDelta")
                # Start response timeout timer
                self.port_response_timer.start(1000)  # 1 second timeout
            else:
                # If connection failed, try next port immediately
                self.try_next_port()
        else:
            # No more ports to test
            self.stop_auto_connect()
            self.log_message.emit("Auto-connect: No Delta robot found")

    def try_connect_to_port(self, port_name):
        """Attempt to connect to a specific port"""
        if self.serial_port.isOpen():
            self.serial_port.close()
        
        self.serial_port.setPortName(port_name)
        self.serial_port.setBaudRate(QSerialPort.Baud115200)
        
        if self.serial_port.open(QSerialPort.ReadWrite):
            self.log_message.emit(f"Testing port {port_name}...")
            return True
        else:
            self.log_message.emit(f"Failed to open port {port_name}")
            return False

    def port_timeout(self):
        """Called when no response is received from current port within timeout period"""
        if self.serial_port.isOpen():
            self.serial_port.close()
        self.log_message.emit(f"No response from {self.current_test_port}")
        self.try_next_port()  # Try next port immediately

    def stop_auto_connect(self):
        """Stop all auto-connect related timers"""
        self.auto_connect_timer.stop()
        self.port_response_timer.stop()
        if not self.serial_port.isOpen():
            self.auto_connect_cb.setChecked(False)
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
        self.log_message.emit("Auto-connect stopped")

    def send_arc_command_cw(self):
        """Send G2 (clockwise arc) command"""
        command = "G2"
        # Add end position
        for axis, spinbox in self.pos_spinboxes.items():
            if not spinbox.value() == 0:
                command += f" {axis}{spinbox.value()}"
        # Add movement parameters
        if self.feed_rate.value() > 0:
            command += f" F{self.feed_rate.value()}"
        self.send_gcode(command)

    def send_arc_command_ccw(self):
        """Send G3 (counter-clockwise arc) command"""
        command = "G3"
        # Add end position
        for axis, spinbox in self.pos_spinboxes.items():
            if not spinbox.value() == 0:
                command += f" {axis}{spinbox.value()}"
        # Add movement parameters
        if self.feed_rate.value() > 0:
            command += f" F{self.feed_rate.value()}"
        self.send_gcode(command)

    def start_angle_jog(self, axis, direction):
        """Start jog movement for rotational axes with current step size"""
        step = self.step_size.value() * direction
        self.send_gcode("G91")  # Set to relative mode
        self.send_gcode(f"G1 {axis}{step} F{self.feed_rate.value()}")

    def stop_angle_jog(self, axis):
        """Stop jog movement for rotational axes"""
        self.send_gcode("G90")  # Return to absolute mode
        self.send_gcode("G93")  # Get current position

    def stop_auto_connect(self):
        """Stop all auto-connect related timers"""
        self.auto_connect_timer.stop()
        self.port_response_timer.stop()
        if not self.serial_port.isOpen():
            self.auto_connect_cb.setChecked(False)
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
        self.log_message.emit("Auto-connect stopped") 