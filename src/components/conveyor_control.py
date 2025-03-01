from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                           QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                           QGroupBox, QGridLayout, QTabWidget, QLineEdit,
                           QCheckBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class ConveyorControl(QWidget):
    log_message = pyqtSignal(str)  # Signal to emit log messages
    response_received = pyqtSignal(str, object)  # Signal for device responses (response, device)

    def __init__(self):
        super().__init__()
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.read_data)
        
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
        
        # Connection group at top
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(10)
        
        # Port selection
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_combo)
        
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
        layout.addWidget(connection_group)

        # Main content area with two columns
        content_layout = QHBoxLayout()
        
        # Left column
        left_column = QVBoxLayout()
        
        # Mode Selection Group
        mode_group = QGroupBox("Motion Mode")
        mode_layout = QGridLayout()
        
        self.mode_buttons = QButtonGroup()
        modes = [
            ("Output Mode", 0, "Output pins will be used as normal digital outputs"),
            ("Position Mode", 1, "Position controlled by serial commands"),
            ("Velocity Mode", 2, "Velocity controlled by serial commands"),
            ("Manual Mode", 3, "Velocity controlled by buttons")
        ]
        
        for i, (name, mode, tooltip) in enumerate(modes):
            radio = QRadioButton(name)
            radio.setToolTip(tooltip)
            radio.mode_value = mode
            self.mode_buttons.addButton(radio)
            mode_layout.addWidget(radio, i // 2, i % 2)
        
        self.mode_buttons.buttons()[0].setChecked(True)  # Set Output Mode as default
        self.mode_buttons.buttonClicked.connect(self.change_mode)
        
        mode_group.setLayout(mode_layout)
        left_column.addWidget(mode_group)

        # Control Parameters Group
        params_group = QGroupBox("Control Parameters")
        params_layout = QGridLayout()

        # Speed control for velocity mode
        self.velocity = QSpinBox()
        self.velocity.setRange(-1000, 1000)
        self.velocity.setValue(0)
        params_layout.addWidget(QLabel("Velocity (mm/s):"), 0, 0)
        params_layout.addWidget(self.velocity, 0, 1)
        
        # Position control
        self.position = QDoubleSpinBox()
        self.position.setRange(-10000, 10000)
        self.position.setValue(0)
        params_layout.addWidget(QLabel("Position (mm):"), 1, 0)
        params_layout.addWidget(self.position, 1, 1)
        
        # Speed for position moves
        self.move_speed = QSpinBox()
        self.move_speed.setRange(0, 1000)
        self.move_speed.setValue(300)
        params_layout.addWidget(QLabel("Move Speed (mm/s):"), 2, 0)
        params_layout.addWidget(self.move_speed, 2, 1)

        # Control buttons
        control_layout = QHBoxLayout()
        
        self.set_velocity_btn = QPushButton("Set Velocity")
        self.set_velocity_btn.clicked.connect(self.set_velocity)
        control_layout.addWidget(self.set_velocity_btn)
        
        self.move_to_pos_btn = QPushButton("Move to Position")
        self.move_to_pos_btn.clicked.connect(self.move_to_position)
        control_layout.addWidget(self.move_to_pos_btn)
        
        params_layout.addLayout(control_layout, 3, 0, 1, 2)
        
        params_group.setLayout(params_layout)
        left_column.addWidget(params_group)

        # Output Control Group
        output_group = QGroupBox("Output Control")
        output_layout = QGridLayout()
        
        # Digital output control
        self.digital_pin = QSpinBox()
        self.digital_pin.setRange(0, 15)
        output_layout.addWidget(QLabel("Digital Pin:"), 0, 0)
        output_layout.addWidget(self.digital_pin, 0, 1)
        
        digital_control = QHBoxLayout()
        self.digital_on_btn = QPushButton("ON")
        self.digital_on_btn.clicked.connect(self.digital_output_on)
        digital_control.addWidget(self.digital_on_btn)
        
        self.digital_off_btn = QPushButton("OFF")
        self.digital_off_btn.clicked.connect(self.digital_output_off)
        digital_control.addWidget(self.digital_off_btn)
        
        output_layout.addLayout(digital_control, 0, 2)
        
        output_group.setLayout(output_layout)
        left_column.addWidget(output_group)
        
        left_column.addStretch()
        
        # Right column
        right_column = QVBoxLayout()
        
        # Configuration Group
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()
        
        # Pulses per mm
        self.pulses_per_mm = QDoubleSpinBox()
        self.pulses_per_mm.setRange(0.1, 1000)
        self.pulses_per_mm.setValue(31.83)
        config_layout.addWidget(QLabel("Pulses/mm:"), 0, 0)
        config_layout.addWidget(self.pulses_per_mm, 0, 1)
        
        # Reverse direction
        self.reverse_direction = QCheckBox("Reverse Direction")
        config_layout.addWidget(self.reverse_direction, 1, 0)
        
        # Enable encoder
        self.enable_encoder = QCheckBox("Enable Encoder")
        config_layout.addWidget(self.enable_encoder, 1, 1)
        
        # Acceleration
        self.acceleration = QSpinBox()
        self.acceleration.setRange(0, 10000)
        self.acceleration.setValue(5000)
        config_layout.addWidget(QLabel("Acceleration (mm/s²):"), 2, 0)
        config_layout.addWidget(self.acceleration, 2, 1)
        
        # Apply config button
        self.apply_config_btn = QPushButton("Apply Configuration")
        self.apply_config_btn.clicked.connect(self.apply_configuration)
        config_layout.addWidget(self.apply_config_btn, 3, 0, 1, 2)
        
        config_group.setLayout(config_layout)
        right_column.addWidget(config_group)

        # Encoder Monitoring Group
        encoder_group = QGroupBox("Encoder Monitoring")
        encoder_layout = QGridLayout()
        
        # Encoder mode selection
        self.encoder_mode_buttons = QButtonGroup()
        encoder_modes = [
            ("Absolute Mode", 0, "Return absolute position value"),
            ("Relative Mode", 1, "Return relative position value"),
            ("Input Pin Mode", 2, "Use encoder port as input pins"),
            ("Button Mode", 3, "Connect to buttons to adjust conveyor speed")
        ]
        
        for i, (name, mode, tooltip) in enumerate(encoder_modes):
            radio = QRadioButton(name)
            radio.setToolTip(tooltip)
            radio.mode_value = mode
            self.encoder_mode_buttons.addButton(radio)
            encoder_layout.addWidget(radio, i // 2, i % 2)
        
        self.encoder_mode_buttons.buttons()[0].setChecked(True)  # Set Absolute Mode as default
        self.encoder_mode_buttons.buttonClicked.connect(self.change_encoder_mode)
        
        # Current position display
        self.position_display = QLineEdit()
        self.position_display.setReadOnly(True)
        encoder_layout.addWidget(QLabel("Current Position (mm):"), 2, 0)
        encoder_layout.addWidget(self.position_display, 2, 1)
        
        # Update interval
        self.update_interval = QSpinBox()
        self.update_interval.setRange(100, 10000)
        self.update_interval.setValue(200)
        self.update_interval.setSingleStep(100)
        encoder_layout.addWidget(QLabel("Update Interval (ms):"), 3, 0)
        encoder_layout.addWidget(self.update_interval, 3, 1)
        
        # Control buttons
        encoder_control = QHBoxLayout()
        
        self.get_pos_btn = QPushButton("Get Position")
        self.get_pos_btn.clicked.connect(self.request_position)
        encoder_control.addWidget(self.get_pos_btn)
        
        self.reset_pos_btn = QPushButton("Reset Position")
        self.reset_pos_btn.clicked.connect(lambda: self.send_command("M317 R"))
        encoder_control.addWidget(self.reset_pos_btn)
        
        self.auto_update_cb = QCheckBox("Auto Update")
        self.auto_update_cb.stateChanged.connect(self.toggle_auto_update)
        encoder_control.addWidget(self.auto_update_cb)
        
        encoder_layout.addLayout(encoder_control, 4, 0, 1, 2)
        
        # Encoder configuration
        encoder_config = QGridLayout()
        
        # Encoder pulses per mm
        self.encoder_pulses_per_mm = QDoubleSpinBox()
        self.encoder_pulses_per_mm.setRange(0.1, 100)
        self.encoder_pulses_per_mm.setValue(5.12)
        self.encoder_pulses_per_mm.setSingleStep(0.01)
        encoder_config.addWidget(QLabel("Encoder Pulses/mm:"), 0, 0)
        encoder_config.addWidget(self.encoder_pulses_per_mm, 0, 1)
        
        # Encoder scale factor
        self.encoder_scale = QSpinBox()
        self.encoder_scale.setRange(1, 4)
        self.encoder_scale.setValue(1)
        self.encoder_scale.setSingleStep(1)
        encoder_config.addWidget(QLabel("Scale Factor:"), 1, 0)
        encoder_config.addWidget(self.encoder_scale, 1, 1)
        
        # Reverse encoder direction
        self.reverse_encoder = QCheckBox("Reverse Encoder")
        encoder_config.addWidget(self.reverse_encoder, 2, 0, 1, 2)
        
        encoder_layout.addLayout(encoder_config, 5, 0, 1, 2)
        
        # Apply encoder config button
        self.apply_encoder_config_btn = QPushButton("Apply Encoder Configuration")
        self.apply_encoder_config_btn.clicked.connect(self.apply_encoder_configuration)
        encoder_layout.addWidget(self.apply_encoder_config_btn, 6, 0, 1, 2)
        
        encoder_group.setLayout(encoder_layout)
        right_column.addWidget(encoder_group)
        
        right_column.addStretch()

        # Add columns to content layout
        content_layout.addLayout(left_column)
        content_layout.addLayout(right_column)
        
        # Add content layout to main layout
        layout.addLayout(content_layout)

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
                        self.log_message.emit(f"Connected to {self.port_combo.currentText()} at 115200 baud")
                        # Check if it's a conveyor
                        self.send_command("IsXConveyor")
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
            self.log_message.emit("Disconnected")

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
        self.ports_to_test = [port.portName() for port in QSerialPortInfo.availablePorts() 
                             if (port.hasProductIdentifier() or 
                                 port.hasVendorIdentifier() or 
                                 (port.portName().startswith("COM") and port.portName() != "COM1"))]
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
                # Send IsXConveyor command to check if this is a conveyor
                self.send_command("IsXConveyor")
                # Start response timeout timer
                self.port_response_timer.start(1000)  # 1 second timeout
            else:
                # If connection failed, try next port immediately
                self.try_next_port()
        else:
            # No more ports to test
            self.stop_auto_connect()
            self.log_message.emit("Auto-connect: No X Conveyor found")

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

    def read_data(self):
        """Read data from serial port"""
        while self.serial_port.canReadLine():
            data = self.serial_port.readLine().data().decode().strip()
            self.log_message.emit(f"Received: {data}")
            self.response_received.emit(data, self)  # Emit response with self as device
            
            # Handle special responses
            if data == "YesXConveyor":
                self.log_message.emit("X Conveyor detected!")
                # Stop auto-connect process since we found the conveyor
                self.port_response_timer.stop()
                self.auto_connect_timer.stop()
                # Update UI to show current port
                self.port_combo.setCurrentText(self.serial_port.portName())
                self.connect_btn.setText("Disconnect")
                self.port_combo.setEnabled(False)
                self.refresh_btn.setEnabled(False)
            elif data.startswith("P0:"):  # Position data from encoder
                try:
                    position = float(data.split(":")[1])
                    self.position_display.setText(f"{position:.2f}")
                except (IndexError, ValueError):
                    pass

    def send_command(self, command):
        if self.serial_port.isOpen():
            try:
                if not command.endswith('\n'):
                    command += '\n'
                self.serial_port.write(command.encode())
                self.log_message.emit(f"Sent: {command.strip()}")
            except Exception as e:
                self.log_message.emit(f"Error sending command: {str(e)}")
        else:
            self.log_message.emit("Error: Not connected to conveyor")

    def change_mode(self, button):
        self.send_command(f"M310 {button.mode_value}")

    def set_velocity(self):
        self.send_command(f"M311 {self.velocity.value()}")

    def move_to_position(self):
        # First set the speed for position moves
        self.send_command(f"M313 {self.move_speed.value()}")
        # Then send the position command
        self.send_command(f"M312 {self.position.value()}")

    def digital_output_on(self):
        self.send_command(f"M314 P{self.digital_pin.value()} V1")

    def digital_output_off(self):
        self.send_command(f"M314 P{self.digital_pin.value()} V0")

    def apply_configuration(self):
        command = "M315"
        command += f" S{self.pulses_per_mm.value()}"  # Pulses per mm
        command += f" R{int(self.reverse_direction.isChecked())}"  # Reverse direction
        command += f" E{int(self.enable_encoder.isChecked())}"  # Enable encoder
        command += f" A{self.acceleration.value()}"  # Acceleration
        self.send_command(command)

    def change_encoder_mode(self, button):
        """Change encoder mode"""
        self.send_command(f"M316 {button.mode_value}")

    def request_position(self):
        """Request current position from encoder"""
        self.send_command("M317")

    def toggle_auto_update(self, state):
        """Toggle automatic position updates"""
        if state:
            interval = self.update_interval.value()
            self.send_command(f"M317 T{interval}")
        else:
            self.send_command("M317")  # Get position one last time

    def apply_encoder_configuration(self):
        """Apply encoder configuration"""
        command = "M318"
        command += f" S{self.encoder_pulses_per_mm.value()}"  # Pulses per mm
        command += f" R{int(self.reverse_encoder.isChecked())}"  # Reverse direction
        command += f" C{self.encoder_scale.value()}"  # Scale factor
        self.send_command(command) 