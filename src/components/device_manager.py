from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QGroupBox, QListWidget, QListWidgetItem,
                           QStackedWidget, QFrame, QMenu, QToolButton)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QCursor

from .robot_control import RobotControl
from .conveyor_control import ConveyorControl
from .encoder_control import EncoderControl

class DeviceManager(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.devices = []  # List of all devices
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side panel
        left_panel = QVBoxLayout()
        
        # Add device toolbar
        add_layout = QHBoxLayout()
        add_layout.setSpacing(2)
        
        # Add device label
        add_layout.addWidget(QLabel("Add:"))
        
        # Add device buttons
        for device_type, label in [('robot', 'R'), ('conveyor', 'C'), ('encoder', 'E')]:
            btn = QToolButton()
            btn.setText(label)
            btn.setToolTip(f"Add {device_type.capitalize()}")
            btn.clicked.connect(lambda checked, d=device_type: self.add_device(d))
            btn.setMaximumWidth(30)
            add_layout.addWidget(btn)
        
        add_layout.addStretch()
        left_panel.addLayout(add_layout)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.setMinimumWidth(150)
        self.device_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_list.customContextMenuRequested.connect(self.show_context_menu)
        self.device_list.currentItemChanged.connect(self.device_selected)
        left_panel.addWidget(self.device_list)
        
        # Add left panel to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(200)
        layout.addWidget(left_widget)
        
        # Right side - Device Control
        self.stack = QStackedWidget()
        self.stack.addWidget(QWidget())  # Empty widget for initial state
        layout.addWidget(self.stack)
        
        # Set stretch factors
        layout.setStretch(0, 1)  # Left panel
        layout.setStretch(1, 4)  # Right panel

    def add_device(self, device_type):
        # Create device
        if device_type == 'robot':
            device = RobotControl()
            name = f"Robot {sum(1 for d in self.devices if isinstance(d, RobotControl)) + 1}"
        elif device_type == 'conveyor':
            device = ConveyorControl()
            name = f"Conveyor {sum(1 for d in self.devices if isinstance(d, ConveyorControl)) + 1}"
        else:  # encoder
            device = EncoderControl()
            name = f"Encoder {sum(1 for d in self.devices if isinstance(d, EncoderControl)) + 1}"
        
        # Connect log signal
        device.log_message.connect(self.log_message.emit)
        
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