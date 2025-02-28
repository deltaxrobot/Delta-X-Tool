from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                           QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                           QGroupBox, QGridLayout, QTabWidget, QLineEdit,
                           QCheckBox, QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class EncoderControl(QWidget):
    log_message = pyqtSignal(str)  # Signal to emit log messages

    def __init__(self):
        super().__init__()
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.read_data)
        
        # Position update timer
        self.position_update_timer = QTimer()
        self.position_update_timer.timeout.connect(self.request_position)
        
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
        mode_group = QGroupBox("Response Mode")
        mode_layout = QGridLayout()
        
        self.mode_buttons = QButtonGroup()
        modes = [
            ("Absolute Mode", 0, "All positions relative to origin"),
            ("Relative Mode", 1, "Positions relative to previous position")
        ]
        
        for i, (name, mode, tooltip) in enumerate(modes):
            radio = QRadioButton(name)
            radio.setToolTip(tooltip)
            radio.mode_value = mode
            self.mode_buttons.addButton(radio)
            mode_layout.addWidget(radio, 0, i)
        
        self.mode_buttons.buttons()[0].setChecked(True)  # Set Absolute Mode as default
        self.mode_buttons.buttonClicked.connect(self.change_mode)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Position Monitoring Group
        monitor_group = QGroupBox("Position Monitoring")
        monitor_layout = QGridLayout()
        
        # Current position display
        self.position_display = QLineEdit()
        self.position_display.setReadOnly(True)
        monitor_layout.addWidget(QLabel("Current Position (mm):"), 0, 0)
        monitor_layout.addWidget(self.position_display, 0, 1)
        
        # Update interval
        self.update_interval = QSpinBox()
        self.update_interval.setRange(100, 10000)
        self.update_interval.setValue(200)
        self.update_interval.setSingleStep(100)
        monitor_layout.addWidget(QLabel("Update Interval (ms):"), 1, 0)
        monitor_layout.addWidget(self.update_interval, 1, 1)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.get_pos_btn = QPushButton("Get Position")
        self.get_pos_btn.clicked.connect(self.request_position)
        control_layout.addWidget(self.get_pos_btn)
        
        self.auto_update_cb = QCheckBox("Auto Update")
        self.auto_update_cb.stateChanged.connect(self.toggle_auto_update)
        control_layout.addWidget(self.auto_update_cb)
        
        monitor_layout.addLayout(control_layout, 2, 0, 1, 2)
        
        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # Calibration Group
        calibration_group = QGroupBox("Calibration")
        calibration_layout = QGridLayout()
        
        # Pulses per mm
        self.pulses_per_mm = QDoubleSpinBox()
        self.pulses_per_mm.setRange(0.1, 100)
        self.pulses_per_mm.setValue(5.12)
        self.pulses_per_mm.setSingleStep(0.01)
        calibration_layout.addWidget(QLabel("Pulses/mm:"), 0, 0)
        calibration_layout.addWidget(self.pulses_per_mm, 0, 1)
        
        # Apply calibration button
        self.apply_calibration_btn = QPushButton("Apply Calibration")
        self.apply_calibration_btn.clicked.connect(self.apply_calibration)
        calibration_layout.addWidget(self.apply_calibration_btn, 1, 0, 1, 2)
        
        calibration_group.setLayout(calibration_layout)
        layout.addWidget(calibration_group)

        # Proximity Sensor Group
        sensor_group = QGroupBox("Proximity Sensor")
        sensor_layout = QGridLayout()
        
        # Sensor status display
        self.sensor_status = QLineEdit()
        self.sensor_status.setReadOnly(True)
        sensor_layout.addWidget(QLabel("Sensor Status:"), 0, 0)
        sensor_layout.addWidget(self.sensor_status, 0, 1)
        
        # Control buttons
        sensor_control = QHBoxLayout()
        
        self.read_sensor_btn = QPushButton("Read Sensor")
        self.read_sensor_btn.clicked.connect(lambda: self.send_command("M319 V"))
        sensor_control.addWidget(self.read_sensor_btn)
        
        self.monitor_sensor_cb = QCheckBox("Monitor Changes")
        self.monitor_sensor_cb.stateChanged.connect(self.toggle_sensor_monitoring)
        sensor_control.addWidget(self.monitor_sensor_cb)
        
        sensor_layout.addLayout(sensor_control, 1, 0, 1, 2)
        
        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)
        
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
                        # Check if it's an encoder
                        self.send_command("IsXEncoder")
                    else:
                        self.log_message.emit(f"Failed to open port {self.port_combo.currentText()}")
                except Exception as e:
                    self.log_message.emit(f"Error: {str(e)}")
        else:
            self.stop_auto_connect()  # Stop any auto-connect process
            self.position_update_timer.stop()
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
            self.log_message.emit("Auto-connect: No X Encoder found")

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
            self.send_command("IsXEncoder")
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
            
            if data == "YesXEncoder":
                self.connect_btn.setText("Disconnect")
                self.port_combo.setEnabled(False)
                self.refresh_btn.setEnabled(False)
                self.log_message.emit(f"X Encoder found on {self.port_combo.currentText()}")
            elif data.startswith("P:"):
                # Update position display
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
            self.log_message.emit("Error: Not connected to encoder")

    def change_mode(self, button):
        self.send_command(f"M316 {button.mode_value}")

    def request_position(self):
        self.send_command("M317")

    def toggle_auto_update(self, state):
        if state:
            interval = self.update_interval.value()
            self.send_command(f"M317 T{interval}")
            self.position_update_timer.start(interval)
        else:
            self.position_update_timer.stop()
            self.send_command("M317")  # Get position one last time

    def apply_calibration(self):
        self.send_command(f"M318 S{self.pulses_per_mm.value()}")

    def toggle_sensor_monitoring(self, state):
        if state:
            self.send_command("M319 T")  # Enable auto feedback
        else:
            self.send_command("M319 V")  # Just get current value 