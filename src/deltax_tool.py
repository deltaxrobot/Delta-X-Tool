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
        self.setMinimumSize(1024, 768)  # Minimum size
        # Set window to maximize on startup
        self.showMaximized()
        
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
                min-height: fit-content;  /* Allow group box to expand based on content */
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
                padding: 8px 15px;  /* Adjusted padding */
                border-radius: 5px;
                font-size: 14px;
                min-height: 30px;  /* Reduced minimum height */
                min-width: 80px;  /* Minimum width for buttons */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 5px 10px;  /* Adjusted padding */
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
                min-height: 30px;  /* Reduced minimum height */
            }
            QTextEdit, QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
                padding: 5px;
                min-height: 30px;  /* Reduced minimum height */
            }
            QLabel {
                font-size: 14px;
                min-height: 25px;  /* Reduced minimum height */
            }
            QTabWidget::pane {
                border: 2px solid #3498db;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #bdc3c7;
                padding: 8px 15px;  /* Adjusted padding */
                font-size: 14px;
                min-height: 30px;  /* Reduced minimum height */
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QGridLayout {
                spacing: 8px;  /* Reduced spacing */
            }
            QVBoxLayout, QHBoxLayout {
                spacing: 8px;  /* Reduced spacing */
            }
            QSplitter::handle {
                background-color: #bdc3c7;
                height: 2px;
            }
            QStackedWidget {
                padding: 0px;
                margin: 0px;
            }
        """)

    def init_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create main horizontal splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Left and Center - Device Manager
        self.device_manager = DeviceManager()
        self.main_splitter.addWidget(self.device_manager)
        
        # Right side - Plugin Tabs
        self.plugin_tabs = QTabWidget()
        self.main_splitter.addWidget(self.plugin_tabs)
        
        # Set initial splitter sizes (70% left, 30% right)
        total_width = 1000  # Reference width
        self.main_splitter.setSizes([700, 300])
        
        # Enable interactive resizing
        self.main_splitter.setHandleWidth(5)  # Make the handle easier to grab
        self.main_splitter.setChildrenCollapsible(False)  # Prevent panels from being collapsed
        
        layout.addWidget(self.main_splitter)
        
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