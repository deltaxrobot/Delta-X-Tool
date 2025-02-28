from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QSplitter, QLabel, QFileDialog,
                           QListWidget, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import lupa
from lupa import LuaRuntime
import os
from datetime import datetime

from .base_plugin import BasePlugin

class ScriptPlugin(BasePlugin):
    def __init__(self, device_manager):
        super().__init__(device_manager)
        self.name = "Script"
        self.description = "Lua scripting for device control"
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.current_device = None
        self.command_queue = []
        self.waiting_response = False
        self.scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts')
        self.init_ui()
        self.setup_lua_env()
        self.load_script_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Editor Section
        editor_section = QWidget()
        editor_layout = QVBoxLayout(editor_section)
        
        # Editor header with current file label
        editor_header = QWidget()
        editor_header_layout = QHBoxLayout(editor_header)
        editor_header_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("Script Editor")
        editor_header_layout.addWidget(editor_label)
        
        self.current_file_label = QLabel("")
        editor_header_layout.addWidget(self.current_file_label)
        
        editor_layout.addWidget(editor_header)
        
        # Script editor
        self.script_editor = QTextEdit()
        editor_layout.addWidget(self.script_editor)
        
        # Editor buttons
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Run Script")
        self.run_btn.clicked.connect(self.run_script)
        button_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_current_script)
        button_layout.addWidget(save_btn)
        
        editor_layout.addLayout(button_layout)
        
        # Script Files Section
        files_section = QWidget()
        files_layout = QVBoxLayout(files_section)
        
        # Files header with buttons
        files_header = QWidget()
        files_header_layout = QHBoxLayout(files_header)
        files_header_layout.setContentsMargins(0, 0, 0, 0)
        
        files_label = QLabel("Script Files")
        files_header_layout.addWidget(files_label)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_script_list)
        files_header_layout.addWidget(refresh_btn)
        
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_script)
        files_header_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_script)
        files_header_layout.addWidget(delete_btn)
        
        files_layout.addWidget(files_header)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.itemDoubleClicked.connect(self.load_selected_script)
        files_layout.addWidget(self.script_list)
        
        # Create vertical splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(editor_section)
        splitter.addWidget(files_section)
        
        # Set initial sizes (70% editor, 30% files)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
        
        # Output console at bottom
        console_label = QLabel("Output Console")
        layout.addWidget(console_label)
        
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setMaximumHeight(150)  # Limit console height
        layout.addWidget(self.output_console)
        
        # Timer for processing command queue
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_queue)
        self.queue_timer.start(100)  # Check queue every 100ms

    def load_script_list(self):
        """Load all .lua scripts from the scripts directory"""
        self.script_list.clear()
        
        # Ensure scripts directory exists
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
        
        # Load all .lua files
        for root, _, files in os.walk(self.scripts_dir):
            for file in files:
                if file.endswith('.lua'):
                    # Get relative path from scripts directory
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.scripts_dir)
                    self.script_list.addItem(rel_path)

    def load_selected_script(self, item):
        """Load the selected script into the editor"""
        script_path = os.path.join(self.scripts_dir, item.text())
        try:
            with open(script_path, 'r') as f:
                self.script_editor.setPlainText(f.read())
            self.current_file_label.setText(item.text())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading script: {str(e)}")

    def new_script(self):
        """Create a new script file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "New Script",
            self.scripts_dir,
            "Lua Scripts (*.lua)"
        )
        
        if filename:
            # Ensure the file has .lua extension
            if not filename.endswith('.lua'):
                filename += '.lua'
            
            try:
                # Create new file with template
                with open(filename, 'w') as f:
                    f.write("""-- New Script
-- Created: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

-- Get devices
local robot = get_device("Robot 1")
if not robot then
    print("Error: Robot not found!")
    return
end

-- Your code here
print("Script started...")

""")
                
                # Reload script list and select new file
                self.load_script_list()
                rel_path = os.path.relpath(filename, self.scripts_dir)
                items = self.script_list.findItems(rel_path, Qt.MatchExactly)
                if items:
                    self.script_list.setCurrentItem(items[0])
                    self.load_selected_script(items[0])
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error creating script: {str(e)}")

    def delete_script(self):
        """Delete the selected script"""
        current_item = self.script_list.currentItem()
        if not current_item:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {current_item.text()}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                script_path = os.path.join(self.scripts_dir, current_item.text())
                os.remove(script_path)
                self.load_script_list()
                if current_item.text() == self.current_file_label.text():
                    self.script_editor.clear()
                    self.current_file_label.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error deleting script: {str(e)}")

    def save_current_script(self):
        """Save the current script"""
        current_file = self.current_file_label.text()
        if not current_file:
            # If no current file, do Save As
            self.new_script()
            return
            
        try:
            script_path = os.path.join(self.scripts_dir, current_file)
            with open(script_path, 'w') as f:
                f.write(self.script_editor.toPlainText())
            QMessageBox.information(self, "Success", "Script saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving script: {str(e)}")

    def setup_lua_env(self):
        # Add global functions to Lua environment
        lua_globals = self.lua.globals()
        
        # Function to get device by name
        def get_device(name):
            for i in range(self.device_manager.device_list.count()):
                item = self.device_manager.device_list.item(i)
                if item.text() == name:
                    return item.device
            return None
        lua_globals.get_device = get_device
        
        # Function to get all devices of a type
        def get_devices_by_type(device_type):
            devices = []
            for device in self.device_manager.devices:
                if (device_type == "robot" and isinstance(device, RobotControl)) or \
                   (device_type == "conveyor" and isinstance(device, ConveyorControl)) or \
                   (device_type == "encoder" and isinstance(device, EncoderControl)):
                    devices.append(device)
            return devices
        lua_globals.get_devices_by_type = get_devices_by_type
        
        # Function to send command to device
        def send_command(device, command):
            self.current_device = device
            self.command_queue.append(command)
        lua_globals.send_command = send_command
        
        # Function to wait for response
        def wait_response():
            while self.waiting_response or self.command_queue:
                self.lua.execute("coroutine.yield()")
        lua_globals.wait_response = wait_response
        
        # Function to sleep for a duration
        def sleep(seconds):
            self.lua.execute(f"os.execute('sleep {seconds}')")
        lua_globals.sleep = sleep
        
        # Function to print to output console
        def print_output(*args):
            text = " ".join(str(arg) for arg in args)
            self.output_console.append(text)
        lua_globals.print = print_output
        
        # Add some utility functions
        utility_code = """
        -- Wait until a condition is met
        function wait_until(condition_func, timeout)
            local start_time = os.time()
            while not condition_func() do
                if timeout and os.time() - start_time > timeout then
                    error("Timeout waiting for condition")
                end
                coroutine.yield()
            end
        end
        
        -- Move robot to position
        function move_to(device, x, y, z, speed)
            speed = speed or 1000  -- default speed
            send_command(device, string.format("G1 X%.2f Y%.2f Z%.2f F%d", x, y, z, speed))
            wait_response()
        end
        
        -- Home robot
        function home_robot(device)
            send_command(device, "G28")
            wait_response()
        end
        
        -- Set conveyor speed
        function set_conveyor_speed(device, speed)
            send_command(device, string.format("M311 %.2f", speed))
            wait_response()
        end
        
        -- Move conveyor to position
        function move_conveyor_to(device, position, speed)
            if speed then
                send_command(device, string.format("M313 %.2f", speed))
                wait_response()
            end
            send_command(device, string.format("M312 %.2f", position))
            wait_response()
        end
        
        -- Get encoder position
        function get_encoder_position(device)
            send_command(device, "M317")
            wait_response()
            -- Note: Response handling needs to be implemented
        end
        """
        self.lua.execute(utility_code)

    def run_script(self):
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.output_console.clear()
        
        try:
            # Create coroutine for script
            script = self.script_editor.toPlainText()
            self.lua_thread = self.lua.eval(f"coroutine.create(function() {script} end)")
            
            # Start script execution
            success, result = self.lua.eval("coroutine.resume")(self.lua_thread)
            if not success:
                self.log_message.emit(f"Script error: {result}")
                self.output_console.append(f"Error: {result}")
                self.stop_script()
                
        except Exception as e:
            self.log_message.emit(f"Script error: {str(e)}")
            self.output_console.append(f"Error: {str(e)}")
            self.stop_script()

    def stop_script(self):
        self.command_queue.clear()
        self.waiting_response = False
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def process_queue(self):
        if not self.waiting_response and self.command_queue:
            # Send next command
            command = self.command_queue.pop(0)
            self.waiting_response = True
            self.send_command(command, self.current_device)
            self.output_console.append(f"Sent: {command}")

    def handle_response(self, response, device):
        if device == self.current_device:
            self.output_console.append(f"Received: {response}")
            self.waiting_response = False
            
            # Resume script execution
            if hasattr(self, 'lua_thread'):
                success, result = self.lua.eval("coroutine.resume")(self.lua_thread)
                if not success:
                    self.log_message.emit(f"Script error: {result}")
                    self.output_console.append(f"Error: {result}")
                    self.stop_script() 