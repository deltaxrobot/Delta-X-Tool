from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QListWidget, QMenu, QMessageBox,
                           QStackedWidget, QTabWidget, QListWidgetItem, QSplitter,
                           QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSerialPort import QSerialPortInfo
import sys
import os

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.script_plugin import ScriptPlugin
from plugins.drawing_plugin import DrawingPlugin

from .robot_control import RobotControl
from .conveyor_control import ConveyorControl
from .encoder_control import EncoderControl
from .mcu_control import MCUControl

class DeviceManager(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.devices = []  # List of all devices
        self.plugins = {}  # Dictionary of loaded plugins
        self.init_ui()
        self.load_plugins()

    def init_ui(self):
        # Main layout
        layout = QHBoxLayout(self)
        
        # Left panel - Device List
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Add device button
        add_btn = QPushButton("Add Device")
        add_btn.clicked.connect(self.show_add_menu)
        left_layout.addWidget(add_btn)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_list.customContextMenuRequested.connect(self.show_context_menu)
        self.device_list.currentItemChanged.connect(self.device_selected)
        left_layout.addWidget(self.device_list)
        
        # Set fixed width for left panel
        left_panel.setFixedWidth(200)
        layout.addWidget(left_panel)
        
        # Right panel with splitter
        right_panel = QSplitter(Qt.Vertical)
        
        # Device control area
        self.stack = QStackedWidget()
        self.stack.addWidget(QWidget())  # Empty widget for initial state
        right_panel.addWidget(self.stack)
        
        # Log display area
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        log_label = QLabel("Communication Log")
        log_layout.addWidget(log_label)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        log_layout.addWidget(self.log_display)
        
        log_widget.setMaximumHeight(200)  # Set maximum height for log section
        right_panel.addWidget(log_widget)
        
        # Set splitter sizes (80% device area, 20% log)
        right_panel.setSizes([800, 200])
        
        # Add right panel to main layout
        layout.addWidget(right_panel)
        
        # Set stretch factors
        layout.setStretch(0, 0)  # Device list - fixed width
        layout.setStretch(1, 1)  # Right panel - stretches to fill space
        
        # Remove margins to maximize space
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Connect log signal
        self.log_message.connect(self.log_display.append)

    def load_plugins(self):
        """Load all available plugins"""
        # Load Script plugin
        script_plugin = ScriptPlugin(self)
        self.add_plugin(script_plugin)
        
        # Load Drawing plugin
        drawing_plugin = DrawingPlugin(self)
        self.add_plugin(drawing_plugin)
        
        # Connect plugin signals
        for plugin in self.plugins.values():
            plugin.command_sent.connect(self.handle_plugin_command)
            plugin.log_message.connect(self.log_message.emit)

    def add_plugin(self, plugin):
        """Add a plugin to the system"""
        self.plugins[plugin.name] = plugin
        # Note: We don't add the plugin to our UI anymore, 
        # it will be added to the main window's plugin panel
        plugin.initialize()

    def get_plugins(self):
        """Return all loaded plugins"""
        return self.plugins.values()

    def handle_plugin_command(self, command, device):
        """Handle command from plugin to device"""
        if hasattr(device, 'send_command'):
            device.send_command(command)
        
    def show_add_menu(self):
        menu = QMenu(self)
        robot_action = menu.addAction("Add Robot")
        conveyor_action = menu.addAction("Add Conveyor")
        encoder_action = menu.addAction("Add Encoder")
        mcu_action = menu.addAction("Add MCU")
        
        action = menu.exec_(self.mapToGlobal(self.sender().pos()))
        
        if action == robot_action:
            self.add_device('robot')
        elif action == conveyor_action:
            self.add_device('conveyor')
        elif action == encoder_action:
            self.add_device('encoder')
        elif action == mcu_action:
            self.add_device('mcu')

    def add_device(self, device_type):
        # Create device
        if device_type == 'robot':
            device = RobotControl()
            name = f"Robot {sum(1 for d in self.devices if isinstance(d, RobotControl)) + 1}"
        elif device_type == 'conveyor':
            device = ConveyorControl()
            name = f"Conveyor {sum(1 for d in self.devices if isinstance(d, ConveyorControl)) + 1}"
        elif device_type == 'encoder':
            device = EncoderControl()
            name = f"Encoder {sum(1 for d in self.devices if isinstance(d, EncoderControl)) + 1}"
        else:  # mcu
            device = MCUControl()
            name = f"MCU {sum(1 for d in self.devices if isinstance(d, MCUControl)) + 1}"
        
        # Connect device signals
        device.log_message.connect(self.log_message.emit)
        device.response_received.connect(self.handle_device_response)
        
        # Add to devices list
        self.devices.append(device)
        
        # Add to list widget
        item = QListWidgetItem(name)
        item.device = device
        self.device_list.addItem(item)
        
        # Add to stack
        self.stack.addWidget(device)
        
        # Select the new device
        self.device_list.setCurrentItem(item)

    def handle_device_response(self, response, device):
        """Handle response from device and forward to plugins"""
        # Display response in log
        device_name = "Unknown Device"
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item.device == device:
                device_name = item.text()
                break
        
        self.log_message.emit(f"{device_name}: {response}")
        
        # Forward response to plugins
        for plugin in self.plugins.values():
            plugin.handle_response(response, device)

    def device_selected(self, current, previous):
        if current and hasattr(current, 'device'):
            index = self.stack.indexOf(current.device)
            if index != -1:
                self.stack.setCurrentIndex(index)

    def show_context_menu(self, position):
        item = self.device_list.itemAt(position)
        if item:
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            rename_action = menu.addAction("Rename")
            
            action = menu.exec_(self.device_list.viewport().mapToGlobal(position))
            
            if action == remove_action:
                self.remove_device(item)
            elif action == rename_action:
                self.device_list.editItem(item)

    def remove_device(self, item):
        if item and hasattr(item, 'device'):
            device = item.device
            # Remove from devices list
            self.devices.remove(device)
            # Remove from stack
            self.stack.removeWidget(device)
            # Remove from list
            self.device_list.takeItem(self.device_list.row(item))
            # Delete the device
            device.deleteLater()
            
            # Set stack to first page if no devices left
            if self.stack.count() == 0:
                self.stack.addWidget(QWidget()) 