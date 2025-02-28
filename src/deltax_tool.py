import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QTextEdit, QTabWidget)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt
from components.robot_control import RobotControl
from components.conveyor_control import ConveyorControl
from components.encoder_control import EncoderControl
from components.device_manager import DeviceManager

class DeltaXTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaX Tool")
        self.setMinimumSize(1024, 768)  # Larger size for touch screens
        self.setGeometry(100, 100, 1200, 800)
        
        # Setup UI
        self.init_ui()
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px;  /* Larger padding for touch */
                border-radius: 5px;
                font-size: 14px;  /* Larger font for touch */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 10px;  /* Larger padding for touch */
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;  /* Larger font for touch */
            }
            QTextEdit, QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;  /* Larger font for touch */
                padding: 5px;
            }
            QLabel {
                font-size: 14px;  /* Larger font for touch */
            }
            QTabWidget::pane {
                border: 2px solid #3498db;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #bdc3c7;
                padding: 15px;  /* Larger padding for touch */
                font-size: 14px;  /* Larger font for touch */
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create device manager
        self.device_manager = DeviceManager()
        self.device_manager.log_message.connect(self.log_message)
        layout.addWidget(self.device_manager)
        
        # Add log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

    def log_message(self, message):
        self.log_text.append(message)
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeltaXTool()
    window.show()
    sys.exit(app.exec_()) 