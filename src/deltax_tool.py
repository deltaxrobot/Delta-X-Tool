import sys
import os

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTabWidget, QSplitter)
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
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left and Center - Device Manager
        self.device_manager = DeviceManager()
        main_splitter.addWidget(self.device_manager)
        
        # Right side - Plugin Tabs
        self.plugin_tabs = QTabWidget()
        main_splitter.addWidget(self.plugin_tabs)
        
        # Set initial splitter sizes (80% left+center, 20% right)
        main_splitter.setSizes([800, 200])
        
        layout.addWidget(main_splitter)
        
        # Add plugins to the right panel
        self.setup_plugins()

    def setup_plugins(self):
        """Add all plugins from device manager to the right panel"""
        for plugin in self.device_manager.get_plugins():
            self.plugin_tabs.addTab(plugin, plugin.name)

    def log_message(self, message):
        self.log_text.append(message)
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

def main():
    app = QApplication(sys.argv)
    
    # Apply modern style
    app.setStyle('Fusion')
    
    window = DeltaXTool()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 