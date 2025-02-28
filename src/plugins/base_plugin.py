from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class BasePlugin(QWidget):
    """Base class for all plugins"""
    
    # Signals
    log_message = pyqtSignal(str)  # For logging messages
    command_sent = pyqtSignal(str, object)  # Command and target device
    command_response = pyqtSignal(str, object)  # Response and source device
    
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.name = "Base Plugin"
        self.description = "Base plugin class"
        
    def initialize(self):
        """Called when plugin is loaded"""
        pass
        
    def cleanup(self):
        """Called when plugin is unloaded"""
        pass
        
    def get_widget(self):
        """Returns the widget to be displayed"""
        return self
        
    def send_command(self, command, device):
        """Send a command to a device and wait for response"""
        self.command_sent.emit(command, device)
        
    def handle_response(self, response, device):
        """Handle response from device"""
        self.command_response.emit(response, device) 