from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                           QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                           QGroupBox, QGridLayout, QTabWidget, QLineEdit,
                           QCheckBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class ConveyorControl(QWidget):
    log_message = pyqtSignal(str)  # Signal to emit log messages

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
        
        # Connection group
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()
        
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
        layout.addWidget(mode_group)

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
        layout.addWidget(params_group)

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
        layout.addWidget(output_group)

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
        layout.addWidget(config_group)
        
        layout.addStretch()

    def update_ports(self):
        self.port_combo.clear()
        for port in QSerialPortInfo.availablePorts():
            self.port_combo.addItem(port.portName())

    def toggle_connection(self):
        if not self.serial_port.isOpen():
            if self.auto_connect_cb.isChecked():
                # Start auto-connect process
                self.start_auto_connect()
            else:
                # Normal connection process
                try:
                    self.serial_port.setPortName(self.port_combo.currentText())
                    self.serial_port.setBaudRate(QSerialPort.Baud115200)
                    if self.serial_port.open(QSerialPort.ReadWrite):
                        # Check if it's a conveyor
                        self.send_command("IsXConveyor")
                    else:
                        self.log_message.emit(f"Failed to open port {self.port_combo.currentText()}")
                except Exception as e:
                    self.log_message.emit(f"Error: {str(e)}")
        else:
            self.stop_auto_connect()  # Stop any auto-connect process
            self.serial_port.close()
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.log_message.emit("Disconnected")

    def toggle_auto_connect(self, state):
        if not state and self.serial_port.isOpen():
            # If turning off auto-connect while connected, disconnect
            self.toggle_connection()

    def try_auto_connect(self):
        """Periodic check for auto-connect status"""
        if not self.serial_port.isOpen():
            self.try_next_port()

    def start_auto_connect(self):
        """Start the auto-connect process"""
        self.ports_to_test = [port.portName() for port in QSerialPortInfo.availablePorts()]
        if self.ports_to_test:
            self.try_next_port()
        else:
            self.log_message.emit("No COM ports available")
            self.auto_connect_cb.setChecked(False)

    def try_next_port(self):
        """Try connecting to the next available port"""
        if self.ports_to_test:
            self.current_test_port = self.ports_to_test.pop(0)
            self.try_connect_to_port(self.current_test_port)
            # Start response timeout timer
            self.port_response_timer.start(500)  # 500ms timeout
        else:
            self.port_response_timer.stop()
            self.auto_connect_cb.setChecked(False)
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.log_message.emit("Auto-connect: No X Conveyor found")

    def port_timeout(self):
        """Called when no response is received from current port within timeout period"""
        if self.serial_port.isOpen():
            self.serial_port.close()
        self.log_message.emit(f"No response from {self.current_test_port}")
        self.try_next_port()  # Try next port immediately

    def try_connect_to_port(self, port_name):
        """Attempt to connect to a specific port"""
        if self.serial_port.isOpen():
            self.serial_port.close()
        
        self.serial_port.setPortName(port_name)
        self.serial_port.setBaudRate(QSerialPort.Baud115200)
        
        if self.serial_port.open(QSerialPort.ReadWrite):
            self.log_message.emit(f"Testing port {port_name}...")
            self.send_command("IsXConveyor")
        else:
            self.log_message.emit(f"Failed to open port {port_name}")
            self.try_next_port()  # Try next port if can't open current one

    def stop_auto_connect(self):
        """Stop all auto-connect related timers and close port"""
        self.auto_connect_timer.stop()
        self.port_response_timer.stop()
        if self.serial_port.isOpen():
            self.serial_port.close()
        self.log_message.emit("Auto-connect stopped")

    def read_data(self):
        while self.serial_port.canReadLine():
            data = self.serial_port.readLine().data().decode().strip()
            self.log_message.emit(f"Received: {data}")
            
            if data == "YesXConveyor":
                self.connect_btn.setText("Disconnect")
                self.port_combo.setEnabled(False)
                self.refresh_btn.setEnabled(False)
                self.log_message.emit(f"X Conveyor found on {self.port_combo.currentText()}")

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