from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextEdit, QComboBox,
                             QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from .opengl_widget import DeltaRobotWidget
from .delta_control_widget import DeltaControlWidget
from ..robot_simulator import RobotSimulator
import serial

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delta Robot Simulator")
        self.setMinimumSize(1200, 800)
        
        # Create simulator instance
        self.simulator = None
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create left panel (controls)
        left_panel = self.create_left_panel()
        layout.addWidget(left_panel)
        
        # Create right panel (3D view with position controls)
        right_panel = self.create_right_panel()
        layout.addWidget(right_panel)
        
        # Set layout proportions
        layout.setStretch(0, 1)  # Left panel
        layout.setStretch(1, 2)  # Right panel

    def create_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)
        
        self.port_combo = QComboBox()
        self.port_combo.addItems(['COM1', 'COM2', 'COM3', 'COM4'])
        self.port_combo.setCurrentText('COM1')
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baud_combo.setCurrentText('115200')
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(QLabel("Baud:"))
        conn_layout.addWidget(self.baud_combo)
        conn_layout.addWidget(self.connect_btn)
        
        layout.addWidget(conn_group)
        
        # Position group
        pos_group = QGroupBox("Current Position")
        pos_layout = QVBoxLayout(pos_group)
        
        self.pos_label = QLabel("X: 0.000  Y: 0.000  Z: -750.000")
        pos_layout.addWidget(self.pos_label)
        
        layout.addWidget(pos_group)
        
        # Log group
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        return widget

    def create_right_panel(self):
        self.delta_control_widget = DeltaControlWidget()
        # Connect position changed signal to update position label
        self.delta_control_widget.robot_widget.position_changed.connect(self.update_position_label)
        return self.delta_control_widget

    def toggle_connection(self):
        """Toggle serial connection."""
        if self.simulator and self.simulator.running:
            if self.simulator:
                self.simulator.stop()
            self.simulator = None
            self.connect_btn.setText("Connect")
            self.log_message("Disconnected")
        else:
            try:
                # Create simulator on COM1
                self.simulator = RobotSimulator(port='COM1', baudrate=115200)
                
                # Connect simulator signals
                self.simulator.movement_started.connect(self.on_movement_started)
                self.simulator.movement_finished.connect(self.on_movement_finished)
                
                # Start simulator
                self.simulator.start()
                
                self.connect_btn.setText("Disconnect")
                self.log_message("Connected to COM1 at 115200 baud")
                
            except Exception as e:
                self.log_message(f"Error connecting: {str(e)}")
                if self.simulator:
                    self.simulator.stop()
                self.simulator = None

    @pyqtSlot(float, float, float, float)
    def on_movement_started(self, x: float, y: float, z: float, duration: float):
        """Handle movement start signal from simulator."""
        self.delta_control_widget.robot_widget.start_movement(x, y, z, duration)
        self.pos_label.setText(f"X: {x:.3f}  Y: {y:.3f}  Z: {z:.3f}")

    @pyqtSlot()
    def on_movement_finished(self):
        """Handle movement finish signal from simulator."""
        self.delta_control_widget.robot_widget.stop_movement()

    @pyqtSlot(float, float, float)
    def update_position_label(self, x: float, y: float, z: float):
        """Update position label when robot position changes."""
        self.pos_label.setText(f"X: {x:.3f}  Y: {y:.3f}  Z: {z:.3f}")

    def log_message(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Handle application close."""
        if self.simulator:
            self.simulator.stop()
        event.accept() 