from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QGroupBox, QTreeWidget, QTreeWidgetItem,
                           QStackedWidget, QFrame, QMenu)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QCursor

from .robot_control import RobotControl
from .conveyor_control import ConveyorControl
from .encoder_control import EncoderControl

class DeviceManager(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.devices = {
            'robots': [],
            'conveyors': [],
            'encoders': []
        }
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side - Device Tree
        left_panel = QVBoxLayout()
        
        # Add device buttons
        add_group = QGroupBox("Add Device")
        add_layout = QHBoxLayout()
        
        add_robot_btn = QPushButton("Robot")
        add_robot_btn.clicked.connect(lambda: self.add_device('robot'))
        add_layout.addWidget(add_robot_btn)
        
        add_conveyor_btn = QPushButton("Conveyor")
        add_conveyor_btn.clicked.connect(lambda: self.add_device('conveyor'))
        add_layout.addWidget(add_conveyor_btn)
        
        add_encoder_btn = QPushButton("Encoder")
        add_encoder_btn.clicked.connect(lambda: self.add_device('encoder'))
        add_layout.addWidget(add_encoder_btn)
        
        add_group.setLayout(add_layout)
        left_panel.addWidget(add_group)
        
        # Device tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Devices")
        self.tree.setMinimumWidth(200)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemClicked.connect(self.device_selected)
        
        # Create root items
        self.robot_root = QTreeWidgetItem(self.tree, ["Robots"])
        self.conveyor_root = QTreeWidgetItem(self.tree, ["Conveyors"])
        self.encoder_root = QTreeWidgetItem(self.tree, ["Encoders"])
        
        left_panel.addWidget(self.tree)
        
        # Add left panel to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)
        layout.addWidget(left_widget)
        
        # Right side - Device Control
        self.stack = QStackedWidget()
        self.stack.addWidget(QWidget())  # Empty widget for initial state
        layout.addWidget(self.stack)
        
        # Set stretch factors
        layout.setStretch(0, 1)  # Left panel
        layout.setStretch(1, 4)  # Right panel

    def add_device(self, device_type):
        if device_type == 'robot':
            device = RobotControl()
            parent = self.robot_root
            name = f"Robot {len(self.devices['robots']) + 1}"
            self.devices['robots'].append(device)
        elif device_type == 'conveyor':
            device = ConveyorControl()
            parent = self.conveyor_root
            name = f"Conveyor {len(self.devices['conveyors']) + 1}"
            self.devices['conveyors'].append(device)
        else:  # encoder
            device = EncoderControl()
            parent = self.encoder_root
            name = f"Encoder {len(self.devices['encoders']) + 1}"
            self.devices['encoders'].append(device)
        
        # Connect log signal
        device.log_message.connect(self.log_message.emit)
        
        # Add to tree
        item = QTreeWidgetItem(parent, [name])
        item.device = device
        parent.setExpanded(True)
        
        # Add to stack
        self.stack.addWidget(device)

    def device_selected(self, item):
        if hasattr(item, 'device'):
            # Find the index of the device widget in the stack
            index = self.stack.indexOf(item.device)
            if index != -1:
                self.stack.setCurrentIndex(index)

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item and hasattr(item, 'device'):
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            rename_action = menu.addAction("Rename")
            
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            
            if action == remove_action:
                self.remove_device(item)
            elif action == rename_action:
                self.tree.editItem(item)

    def remove_device(self, item):
        device = item.device
        device_type = None
        
        # Find device type
        if device in self.devices['robots']:
            device_type = 'robots'
        elif device in self.devices['conveyors']:
            device_type = 'conveyors'
        elif device in self.devices['encoders']:
            device_type = 'encoders'
        
        if device_type:
            # Remove from devices list
            self.devices[device_type].remove(device)
            # Remove from stack
            self.stack.removeWidget(device)
            # Remove from tree
            item.parent().removeChild(item)
            # Delete the device
            device.deleteLater()
            
            # Set stack to first page if no devices left
            if self.stack.count() == 0:
                self.stack.addWidget(QWidget()) 