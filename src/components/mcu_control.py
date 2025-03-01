from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                           QPushButton, QLabel, QGroupBox, QTextEdit, QCheckBox,
                           QLineEdit)
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class MCUControl(QWidget):
    connection_status_changed = pyqtSignal(bool)
    log_message = pyqtSignal(str)
    response_received = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.read_data)
        
        # Auto-connect timers
        self.auto_connect_timer = QTimer()
        self.auto_connect_timer.timeout.connect(self.try_auto_connect)
        self.port_response_timer = QTimer()
        self.port_response_timer.timeout.connect(self.port_timeout)
        self.port_response_timer.setSingleShot(True)
        
        self.current_test_port = None
        self.ports_to_test = []
        self.init_ui()
        self.update_ports()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Add spacing between elements
        
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
        
        # Baud rate selection
        baud_layout = QHBoxLayout()
        self.baud_combo = QComboBox()
        for baud in [9600, 19200, 38400, 57600, 115200]:
            self.baud_combo.addItem(str(baud))
        self.baud_combo.setCurrentText("115200")
        baud_layout.addWidget(QLabel("Baud:"))
        baud_layout.addWidget(self.baud_combo)
        connection_layout.addLayout(baud_layout)
        
        # Auto-connect checkbox
        self.auto_connect_cb = QCheckBox("Auto Connect")
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
        
        # Communication group
        comm_group = QGroupBox("Communication")
        comm_layout = QVBoxLayout()
        comm_layout.setSpacing(10)  # Add spacing between elements
        
        # Send area
        send_layout = QHBoxLayout()
        send_layout.setSpacing(10)  # Add spacing between elements
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command to send...")
        self.command_input.returnPressed.connect(self.send_command)
        send_layout.addWidget(self.command_input)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_command)
        send_btn.setFixedWidth(100)  # Fixed width for send button
        send_layout.addWidget(send_btn)
        
        comm_layout.addLayout(send_layout)
        
        # Received data display
        self.received_text = QTextEdit()
        self.received_text.setReadOnly(True)
        self.received_text.setMinimumHeight(300)  # Increase minimum height
        comm_layout.addWidget(self.received_text)
        
        comm_group.setLayout(comm_layout)
        layout.addWidget(comm_group)
        
        # Set margins and spacing
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add stretch at the bottom to push everything up
        layout.addStretch(1)

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
                    self.serial_port.setBaudRate(int(self.baud_combo.currentText()))
                    if self.serial_port.open(QSerialPort.ReadWrite):
                        self.connect_btn.setText("Disconnect")
                        self.port_combo.setEnabled(False)
                        self.refresh_btn.setEnabled(False)
                        self.baud_combo.setEnabled(False)
                        self.connection_status_changed.emit(True)
                        self.log_message.emit(f"Connected to {self.port_combo.currentText()} at {self.baud_combo.currentText()} baud")
                    else:
                        self.log_message.emit(f"Failed to open port {self.port_combo.currentText()}")
                except Exception as e:
                    self.log_message.emit(f"Error: {str(e)}")
        else:  # Disconnect
            self.stop_auto_connect()
            self.serial_port.close()
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.connection_status_changed.emit(False)
            self.log_message.emit("Disconnected")

    def send_command(self):
        if self.serial_port.isOpen():
            command = self.command_input.text().strip()
            if command:
                try:
                    # Add newline if not present
                    if not command.endswith('\n'):
                        command += '\n'
                    self.serial_port.write(command.encode())
                    self.log_message.emit(f"Sent: {command.strip()}")
                    self.command_input.clear()
                except Exception as e:
                    self.log_message.emit(f"Error sending command: {str(e)}")
        else:
            self.log_message.emit("Error: Not connected to device")

    def read_data(self):
        """Read data from serial port"""
        while self.serial_port.canReadLine():
            data = self.serial_port.readLine().data().decode().strip()
            self.log_message.emit(f"Received: {data}")
            self.response_received.emit(data, self)
            self.received_text.append(data)

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
                # Start response timeout timer
                self.port_response_timer.start(1000)  # 1 second timeout
            else:
                # If connection failed, try next port immediately
                self.try_next_port()
        else:
            # No more ports to test
            self.stop_auto_connect()
            self.log_message.emit("Auto-connect: No device found")

    def try_connect_to_port(self, port_name):
        """Attempt to connect to a specific port"""
        if self.serial_port.isOpen():
            self.serial_port.close()
        
        self.serial_port.setPortName(port_name)
        self.serial_port.setBaudRate(int(self.baud_combo.currentText()))
        
        if self.serial_port.open(QSerialPort.ReadWrite):
            self.log_message.emit(f"Testing port {port_name}...")
            # Update UI to show current port
            self.port_combo.setCurrentText(port_name)
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.connection_status_changed.emit(True)
            return True
        else:
            self.log_message.emit(f"Failed to open port {port_name}")
            return False

    def port_timeout(self):
        """Called when no response is received from current port within timeout period"""
        if self.serial_port.isOpen():
            self.serial_port.close()
        self.log_message.emit(f"No response from {self.current_test_port}")
        self.try_next_port()

    def stop_auto_connect(self):
        """Stop all auto-connect related timers"""
        self.auto_connect_timer.stop()
        self.port_response_timer.stop()
        if not self.serial_port.isOpen():
            self.auto_connect_cb.setChecked(False)
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.baud_combo.setEnabled(True)
        self.log_message.emit("Auto-connect stopped") 