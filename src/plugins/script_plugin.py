from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QSplitter, QLabel, QFileDialog,
                           QListWidget, QMessageBox, QCompleter, QPlainTextEdit,
                           QSizePolicy, QDialog, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, pyqtSignal
from PyQt5.QtGui import (QTextCharFormat, QSyntaxHighlighter, QColor, QFont, 
                        QTextCursor, QPainter, QTextFormat)
import lupa
from lupa import LuaRuntime
import os
import re
import time
import threading
from datetime import datetime
import math
import traceback
import sys

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.robot_control import RobotControl
from components.conveyor_control import ConveyorControl
from components.encoder_control import EncoderControl

from .base_plugin import BasePlugin

# Constants
MAX_SCRIPT_RUNTIME = 30000  # 30 seconds
SCRIPT_CHECK_INTERVAL = 100  # 100ms
MAX_QUEUE_SIZE = 1000
SCRIPT_STOP_TIMEOUT = 5  # 5 seconds

class LuaSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Lua keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))  # Blue
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "break", "do", "else", "elseif", "end", "false", "for",
            "function", "if", "in", "local", "nil", "not", "or", "repeat",
            "return", "then", "true", "until", "while"
        ]
        for word in keywords:
            pattern = f"\\b{word}\\b"
            self.highlighting_rules.append((pattern, keyword_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#098658"))  # Dark green
        self.highlighting_rules.append(("\\b[0-9]+\\b", number_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#A31515"))  # Dark red
        self.highlighting_rules.append(("\".*\"", string_format))
        self.highlighting_rules.append(("'.*'", string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#008000"))  # Green
        self.highlighting_rules.append(("--[^\n]*", comment_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#795E26"))  # Brown
        self.highlighting_rules.append(("\\b\\w+(?=\\()", function_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class ScriptEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set editor style
        self.setFont(QFont("Consolas", 10))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
            }
        """)
        
        self.highlighter = LuaSyntaxHighlighter(self.document())
        
        # Enable line numbers
        self.line_number_area = LineNumberArea(self)
        
        # Connect signals for line number updates
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        # Initialize the line number area
        self.updateLineNumberAreaWidth()
        
        # Initialize completer
        self.completer = None
        
    def setCompleter(self, completer):
        if self.completer:
            self.completer.disconnect(self)
        self.completer = completer
        if self.completer:
            self.completer.setWidget(self)
            self.completer.activated.connect(self.insertCompletion)
            
    def insertCompletion(self, completion):
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)
        
    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()
        
    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
                
        # Show completions after typing 2 characters
        isShortcut = (event.modifiers() == Qt.ControlModifier and
                     event.key() == Qt.Key_Space)
                     
        if not self.completer or not isShortcut:
            super().keyPressEvent(event)
            
        ctrlOrShift = event.modifiers() in (Qt.ControlModifier, Qt.ShiftModifier)
        if not self.completer or (ctrlOrShift and len(event.text()) == 0):
            return
            
        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="  # End of word characters
        hasModifier = (event.modifiers() != Qt.NoModifier) and not ctrlOrShift
        
        completionPrefix = self.textUnderCursor()
        
        if not isShortcut and (hasModifier or len(event.text()) == 0 or
                              len(completionPrefix) < 2 or
                              event.text()[-1] in eow):
            self.completer.popup().hide()
            return
            
        if completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            self.completer.popup().setCurrentIndex(
                self.completer.completionModel().index(0, 0))
                
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
                   self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _=None):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()
            
    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor("#E8F2FF")  # Light blue background
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        
        self.setExtraSelections(extraSelections)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#FAFAFA"))  # Very light gray background

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#666666"))  # Darker gray for numbers
                painter.drawText(0, int(top), self.line_number_area.width() - 5, 
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Script Editor Help")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Editor Help tab
        editor_help = QTextEdit()
        editor_help.setReadOnly(True)
        editor_help.setHtml("""
            <h2>Script Editor Help</h2>
            
            <h3>Code Completion</h3>
            <p>The editor provides code completion to help you write scripts faster:</p>
            <ul>
                <li><b>Auto-complete:</b> Type at least 2 characters to see suggestions</li>
                <li><b>Manual trigger:</b> Press Ctrl + Space to show all available completions</li>
                <li><b>Navigation:</b> Use Up/Down arrows to select from the list</li>
                <li><b>Insert:</b> Press Enter or Tab to insert the selected completion</li>
                <li><b>Cancel:</b> Press Esc to close the completion list</li>
            </ul>
            
            <h3>Available Completions</h3>
            <ul>
                <li><b>Lua Keywords:</b> function, local, if, then, else, end, for, while, etc.</li>
                <li><b>Device Functions:</b> get_device, move_to, set_speed, home, etc.</li>
                <li><b>Conveyor Functions:</b> conveyor_move, conveyor_stop, conveyor_step</li>
                <li><b>Encoder Functions:</b> get_encoder_position, reset_encoder, set_encoder_mode</li>
                <li><b>Utility Functions:</b> sleep, get_time, average, median, print</li>
                <li><b>Math Functions:</b> math.sin, math.cos, math.tan, math.abs, math.sqrt, etc.</li>
                <li><b>Common Variables:</b> robot, conveyor, encoder, position, speed, steps</li>
            </ul>
            
            <h3>Editor Features</h3>
            <ul>
                <li><b>Syntax Highlighting:</b> Keywords, numbers, strings, and comments are color-coded</li>
                <li><b>Line Numbers:</b> Line numbers are displayed on the left side</li>
                <li><b>Current Line:</b> The current line is highlighted in light blue</li>
                <li><b>Documentation:</b> Click the ▼/▶ button to show/hide documentation</li>
            </ul>
            
            <h3>Keyboard Shortcuts</h3>
            <ul>
                <li><b>Ctrl + Space:</b> Show code completion</li>
                <li><b>Ctrl + S:</b> Save current script</li>
                <li><b>Ctrl + Z:</b> Undo</li>
                <li><b>Ctrl + Y:</b> Redo</li>
                <li><b>Ctrl + F:</b> Find text</li>
                <li><b>Ctrl + H:</b> Replace text</li>
            </ul>
        """)
        tab_widget.addTab(editor_help, "Editor Help")
        
        # Device Functions tab
        device_funcs = QTextEdit()
        device_funcs.setReadOnly(True)
        device_funcs.setHtml("""
            <h2>Device Control Functions</h2>
            
            <h3>Basic Device Control</h3>
            <pre>
get_device(name)          -- Get device by name (Robot 1, Conveyor 1, Encoder 1)
            </pre>
            
            <h3>Robot Functions</h3>
            <pre>
robot:move_to(x, y, z)    -- Move robot to position (mm)
robot:set_speed(speed)    -- Set movement speed (mm/s)
robot:home()              -- Home all axes
robot:set_output(pin, on) -- Control digital output (pin: 0-15)
robot:set_pwm(pin, value) -- Set PWM output (pin: 0-15, value: 0-255)
            </pre>
            
            <h3>Conveyor Functions</h3>
            <pre>
conveyor_move(dev, dir, speed)  -- Move conveyor (dir: "forward"/"backward", speed: 0-100)
conveyor_stop(dev)              -- Stop conveyor movement
conveyor_step(dev, steps, speed) -- Move specific steps
            </pre>
            
            <h3>Encoder Functions</h3>
            <pre>
get_encoder_position(dev)       -- Get current position
reset_encoder(dev)              -- Reset position to zero
set_encoder_mode(dev, mode)     -- Set mode ("absolute"/"relative")
            </pre>
        """)
        tab_widget.addTab(device_funcs, "Device Functions")
        
        # Utility Functions tab
        util_funcs = QTextEdit()
        util_funcs.setReadOnly(True)
        util_funcs.setHtml("""
            <h2>Utility Functions</h2>
            
            <h3>Time Functions</h3>
            <pre>
sleep(seconds)            -- Pause execution
get_time()               -- Get current time (seconds)
            </pre>
            
            <h3>Data Processing</h3>
            <pre>
average(values)          -- Calculate average of array
median(values)           -- Calculate median of array
print(...)               -- Print to output console
            </pre>
            
            <h3>Math Functions</h3>
            <pre>
math.sin(x)              -- Sine function
math.cos(x)              -- Cosine function
math.tan(x)              -- Tangent function
math.abs(x)              -- Absolute value
math.sqrt(x)             -- Square root
math.pi                  -- Pi constant
math.rad(deg)            -- Convert degrees to radians
math.deg(rad)            -- Convert radians to degrees
            </pre>
        """)
        tab_widget.addTab(util_funcs, "Utility Functions")
        
        # Code Examples tab
        examples = QTextEdit()
        examples.setReadOnly(True)
        examples.setHtml("""
            <h2>Code Examples</h2>
            
            <h3>Basic Robot Movement</h3>
            <pre>
-- Get robot device
local robot = get_device("Robot 1")
if not robot then
    print("Error: Robot not found!")
    return
end

-- Move to position
robot:set_speed(100)      -- Set speed to 100mm/s
robot:move_to(0, 0, 100)  -- Move to X=0, Y=0, Z=100
sleep(1)                  -- Wait for 1 second

-- Control outputs
robot:set_output(1, true)   -- Turn on output 1
sleep(0.5)                  -- Wait for 0.5 seconds
robot:set_output(1, false)  -- Turn off output 1
            </pre>
            
            <h3>Conveyor Control</h3>
            <pre>
-- Get conveyor device
local conveyor = get_device("Conveyor 1")
if not conveyor then
    print("Error: Conveyor not found!")
    return
end

-- Move conveyor forward
conveyor_move(conveyor, "forward", 50)  -- 50% speed
sleep(2)                                -- Run for 2 seconds

-- Stop conveyor
conveyor_stop(conveyor)
sleep(1)

-- Move specific steps
conveyor_step(conveyor, 1000, 30)  -- 1000 steps at 30% speed
            </pre>
            
            <h3>Encoder Monitoring</h3>
            <pre>
-- Get encoder device
local encoder = get_device("Encoder 1")
if not encoder then
    print("Error: Encoder not found!")
    return
end

-- Reset and configure encoder
reset_encoder(encoder)
set_encoder_mode(encoder, "absolute")

-- Monitor position
for i = 1, 10 do
    local pos = get_encoder_position(encoder)
    print("Position:", pos)
    sleep(0.5)
end
            </pre>
            
            <h3>Combined Example</h3>
            <pre>
-- Get all devices
local robot = get_device("Robot 1")
local conveyor = get_device("Conveyor 1")
local encoder = get_device("Encoder 1")

-- Check connections
if not (robot and conveyor and encoder) then
    print("Error: Some devices not found!")
    return
end

-- Initialize
robot:set_speed(100)
reset_encoder(encoder)

-- Main loop
for i = 1, 5 do
    -- Move robot to pick position
    robot:move_to(0, 0, 100)
    sleep(1)
    
    -- Start conveyor and monitor position
    conveyor_move(conveyor, "forward", 30)
    local target_pos = 1000
    
    while get_encoder_position(encoder) < target_pos do
        print("Position:", get_encoder_position(encoder))
        sleep(0.1)
    end
    
    -- Stop when target reached
    conveyor_stop(conveyor)
    print("Target position reached")
end
            </pre>
        """)
        tab_widget.addTab(examples, "Code Examples")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                color: #212529;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #E9ECEF;
                border-color: #CED4DA;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

class ScriptPlugin(BasePlugin):
    # Signal for logging messages
    log_message = pyqtSignal(str)
    
    def __init__(self, device_manager):
        super().__init__(device_manager)
        self.name = "Script"
        self.description = "Lua scripting for device control"
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.current_device = None
        self.command_queue = []
        self.queue_lock = threading.Lock()
        self.waiting_response = False
        self.scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts')
        
        # Script execution control
        self.script_running = False
        self.stop_requested = False
        self.script_timeout = None
        self.lua_thread = None
        
        # Initialize UI and setup environment
        self.init_ui()
        self.setup_lua_env()
        self.load_script_list()
        
        # Connect signals
        self.log_message.connect(self.output_console.append)
        
    def handle_script_timeout(self):
        """Handle script timeout"""
        if self.script_running:
            self.log_message.emit("Script execution timeout")
            self.stop_script()
            
    def check_queue_size(self):
        """Check if command queue is not too large"""
        with self.queue_lock:
            if len(self.command_queue) >= MAX_QUEUE_SIZE:
                self.log_message.emit("Command queue overflow")
                self.stop_script()
                return False
        return True

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Editor Section
        editor_section = QWidget()
        editor_layout = QVBoxLayout(editor_section)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Editor header with current file label and help button
        editor_header = QWidget()
        editor_header_layout = QHBoxLayout(editor_header)
        editor_header_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("Script Editor")
        editor_header_layout.addWidget(editor_label)
        
        self.current_file_label = QLabel("")
        editor_header_layout.addWidget(self.current_file_label)
        editor_header_layout.addStretch()
        
        help_btn = QPushButton("Help")
        help_btn.setStyleSheet("""
            QPushButton {
                padding: 2px 8px;
                background: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                color: #212529;
                font-size: 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background: #E9ECEF;
                border-color: #CED4DA;
            }
        """)
        help_btn.clicked.connect(self.show_help)
        editor_header_layout.addWidget(help_btn)
        
        editor_layout.addWidget(editor_header)
        
        # Script editor
        self.script_editor = ScriptEditor()
        editor_layout.addWidget(self.script_editor)
        
        # Add auto-completion
        self.completer = QCompleter(self.get_completion_words())
        self.script_editor.setCompleter(self.completer)
        
        # Editor buttons
        button_layout = QHBoxLayout()
        button_style = """
            QPushButton {
                padding: 4px 12px;
                background: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                color: #212529;
            }
            QPushButton:hover {
                background: #E9ECEF;
                border-color: #CED4DA;
            }
            QPushButton:disabled {
                background: #E9ECEF;
                color: #6C757D;
            }
        """
        
        self.run_btn = QPushButton("Run Script")
        self.run_btn.setStyleSheet(button_style)
        self.run_btn.clicked.connect(self.run_script)
        button_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(button_style)
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(button_style)
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
        
        # Create vertical splitter for editor and files
        editor_files_splitter = QSplitter(Qt.Vertical)
        editor_files_splitter.addWidget(editor_section)
        editor_files_splitter.addWidget(files_section)
        
        # Store splitter for later use
        self.editor_files_splitter = editor_files_splitter
        
        # Set initial sizes (85% editor, 15% files)
        total_height = 1000  # Reference height
        editor_files_splitter.setSizes([850, 150])
        
        # Make editor section expand and push others down
        editor_section.setMinimumHeight(400)  # Increased minimum height for editor
        editor_section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Set fixed heights for files section
        files_section.setMaximumHeight(200)  # Limit files section height
        files_section.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        # Set stretch factors for the splitter
        editor_files_splitter.setStretchFactor(0, 1)  # Editor stretches
        editor_files_splitter.setStretchFactor(1, 0)  # Files section doesn't stretch
        
        main_layout.addWidget(editor_files_splitter)
        
        # Output console at bottom
        console_label = QLabel("Output Console")
        main_layout.addWidget(console_label)
        
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setMaximumHeight(150)  # Limit console height
        main_layout.addWidget(self.output_console)
        
        layout.addWidget(main_widget)
        
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
                    f.write("""--[[
Script Name: {name}
Created: {date}
Description: Control script for DeltaX robot system
]]--

-- Get devices
local robot = get_device("Robot 1")
local conveyor = get_device("Conveyor 1")
local encoder = get_device("Encoder 1")

-- Check device connections
if not robot then
    print("Error: Robot not found!")
    return
end

-- Your code here
print("Script started...")

""".format(
    name=os.path.basename(filename),
    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
))
                
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
        """Set up the Lua environment with functions and error handling"""
        try:
            # Add global functions to Lua environment
            lua_globals = self.lua.globals()
            
            # Add print function
            def lua_print(*args):
                message = " ".join(str(arg) for arg in args)
                self.output_console.append(message)
            lua_globals.print = lua_print
            
            # Basic device functions with error handling
            def get_device(name):
                try:
                    if not isinstance(name, str):
                        raise TypeError("Device name must be a string")
                        
                    for i in range(self.device_manager.device_list.count()):
                        item = self.device_manager.device_list.item(i)
                        if item.text() == name:
                            device = item.device
                            if device is None:
                                raise Exception(f"Device {name} is not connected")
                            return device
                    raise Exception(f"Device {name} not found")
                except Exception as e:
                    lua_print(f"Error getting device: {str(e)}")
                    return None
            lua_globals.get_device = get_device
            
            # Conveyor specific functions with error handling
            def conveyor_move(conveyor, direction, speed):
                try:
                    if not isinstance(conveyor, ConveyorControl):
                        raise TypeError("First argument must be a conveyor device")
                    if direction not in ["forward", "backward"]:
                        raise ValueError("Direction must be 'forward' or 'backward'")
                    if not isinstance(speed, (int, float)) or speed < 0 or speed > 100:
                        raise ValueError("Speed must be between 0 and 100")
                        
                    if direction == "forward":
                        conveyor.move_forward(speed)
                    else:
                        conveyor.move_backward(speed)
                    return True
                except Exception as e:
                    lua_print(f"Error moving conveyor: {str(e)}")
                    return False
            lua_globals.conveyor_move = conveyor_move
            
            def conveyor_stop(conveyor):
                try:
                    if not isinstance(conveyor, ConveyorControl):
                        raise TypeError("Argument must be a conveyor device")
                    conveyor.stop()
                    return True
                except Exception as e:
                    lua_print(f"Error stopping conveyor: {str(e)}")
                    return False
            lua_globals.conveyor_stop = conveyor_stop
            
            def conveyor_step(conveyor, steps, speed):
                try:
                    if not isinstance(conveyor, ConveyorControl):
                        raise TypeError("First argument must be a conveyor device")
                    if not isinstance(steps, (int, float)):
                        raise TypeError("Steps must be a number")
                    if not isinstance(speed, (int, float)) or speed < 0 or speed > 100:
                        raise ValueError("Speed must be between 0 and 100")
                        
                    conveyor.move_steps(steps, speed)
                    return True
                except Exception as e:
                    lua_print(f"Error stepping conveyor: {str(e)}")
                    return False
            lua_globals.conveyor_step = conveyor_step
            
            # Encoder specific functions with error handling
            def get_encoder_position(encoder):
                try:
                    if not isinstance(encoder, EncoderControl):
                        raise TypeError("Argument must be an encoder device")
                    return encoder.get_position()
                except Exception as e:
                    lua_print(f"Error getting encoder position: {str(e)}")
                    return None
            lua_globals.get_encoder_position = get_encoder_position
            
            def reset_encoder(encoder):
                try:
                    if not isinstance(encoder, EncoderControl):
                        raise TypeError("Argument must be an encoder device")
                    encoder.reset_position()
                    return True
                except Exception as e:
                    lua_print(f"Error resetting encoder: {str(e)}")
                    return False
            lua_globals.reset_encoder = reset_encoder
            
            def set_encoder_mode(encoder, mode):
                try:
                    if not isinstance(encoder, EncoderControl):
                        raise TypeError("First argument must be an encoder device")
                    if mode not in ["absolute", "relative"]:
                        raise ValueError("Mode must be 'absolute' or 'relative'")
                    encoder.set_mode(mode)
                    return True
                except Exception as e:
                    lua_print(f"Error setting encoder mode: {str(e)}")
                    return False
            lua_globals.set_encoder_mode = set_encoder_mode
            
            # Math and utility functions
            lua_globals.math = {
                'pi': math.pi,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'abs': math.fabs,
                'floor': math.floor,
                'ceil': math.ceil,
                'rad': math.radians,
                'deg': math.degrees,
                'sqrt': math.sqrt,
                'min': min,
                'max': max
            }
            
            # Time functions with error handling
            def sleep(seconds):
                try:
                    if not isinstance(seconds, (int, float)) or seconds < 0:
                        raise ValueError("Sleep time must be a non-negative number")
                    if self.stop_requested:
                        return
                    time.sleep(seconds)
                except Exception as e:
                    lua_print(f"Error in sleep: {str(e)}")
            lua_globals.sleep = sleep
            
            def get_time():
                try:
                    return time.time()
                except Exception as e:
                    lua_print(f"Error getting time: {str(e)}")
                    return 0
            lua_globals.get_time = get_time
            
            # Data processing functions with error handling
            def average(values):
                try:
                    if not isinstance(values, (list, tuple)):
                        raise TypeError("Expected list or tuple")
                    if not values:
                        return 0
                    numeric_values = [float(x) for x in values]
                    return sum(numeric_values) / len(numeric_values)
                except Exception as e:
                    lua_print(f"Error calculating average: {str(e)}")
                    return 0
            lua_globals.average = average
            
            def median(values):
                try:
                    if not isinstance(values, (list, tuple)):
                        raise TypeError("Expected list or tuple")
                    if not values:
                        return 0
                    numeric_values = sorted([float(x) for x in values])
                    mid = len(numeric_values) // 2
                    if len(numeric_values) % 2 == 0:
                        return (numeric_values[mid-1] + numeric_values[mid]) / 2
                    return numeric_values[mid]
                except Exception as e:
                    lua_print(f"Error calculating median: {str(e)}")
                    return 0
            lua_globals.median = median
            
            # Add stop check function
            def check_stop():
                return self.stop_requested
            lua_globals.check_stop = check_stop
            
        except Exception as e:
            self.log_message.emit(f"Error setting up Lua environment: {str(e)}")
            self.output_console.append(traceback.format_exc())

    def run_script(self):
        """Run the current script"""
        try:
            # Reset state
            self.script_running = True
            self.stop_requested = False
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.output_console.clear()
            
            # Set up timeout
            self.script_timeout = QTimer()
            self.script_timeout.setSingleShot(True)
            self.script_timeout.timeout.connect(self.handle_script_timeout)
            self.script_timeout.start(MAX_SCRIPT_RUNTIME)
            
            # Get script content
            script = self.script_editor.toPlainText()
            
            # Create Lua function to handle script execution
            self.lua.execute("""
                function create_and_run_script(script_text)
                    -- Load the script
                    local fn, err = load(script_text)
                    if not fn then
                        error("Failed to load script: " .. tostring(err))
                    end
                    
                    -- Create coroutine
                    local co = coroutine.create(fn)
                    
                    -- Return both the coroutine and its initial run result
                    local success, result = coroutine.resume(co)
                    return co, success, result
                end
            """)
            
            # Run the script
            create_and_run = self.lua.globals().create_and_run_script
            self.lua_thread, success, result = create_and_run(script)
            
            if not success:
                raise Exception(str(result))
                
        except Exception as e:
            self.log_message.emit(f"Script error: {str(e)}")
            self.output_console.append(f"Error: {str(e)}")
            self.output_console.append(traceback.format_exc())
            self.stop_script()

    def stop_script(self):
        """Stop the current script safely"""
        try:
            self.stop_requested = True
            
            if hasattr(self, 'lua_thread'):
                # Set stop flag in Lua environment
                self.lua.globals().stop_requested = True
                
                # Create Lua function to safely stop script
                self.lua.execute("""
                    function safe_stop_script(co)
                        if not co then return end
                        
                        local status = coroutine.status(co)
                        if status == "suspended" then
                            -- Try to resume one last time to allow cleanup
                            pcall(coroutine.resume, co)
                        end
                    end
                """)
                
                # Stop the script
                safe_stop = self.lua.globals().safe_stop_script
                safe_stop(self.lua_thread)
                    
            # Clean up
            with self.queue_lock:
                self.command_queue.clear()
            self.waiting_response = False
            self.script_running = False
            
            # Reset UI
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            # Stop timeout timer
            if self.script_timeout:
                self.script_timeout.stop()
                
        except Exception as e:
            self.log_message.emit(f"Error stopping script: {str(e)}")
            self.output_console.append(traceback.format_exc())

    def process_queue(self):
        """Process commands in the queue"""
        try:
            if self.stop_requested:
                return
                
            with self.queue_lock:
                if not self.waiting_response and self.command_queue:
                    # Send next command
                    command = self.command_queue.pop(0)
                    self.waiting_response = True
                    self.send_command(command, self.current_device)
                    self.output_console.append(f"Sent: {command}")
                    
        except Exception as e:
            self.log_message.emit(f"Error processing queue: {str(e)}")
            self.output_console.append(traceback.format_exc())
            self.stop_script()

    def handle_response(self, response, device):
        """Handle device response"""
        try:
            if device == self.current_device:
                self.output_console.append(f"Received: {response}")
                self.waiting_response = False
                
                # Check if script should continue
                if self.stop_requested:
                    return
                    
                # Resume script execution
                if hasattr(self, 'lua_thread'):
                    # Create Lua function to safely resume script
                    self.lua.execute("""
                        function safe_resume_script(co)
                            if not co then return false, "No coroutine" end
                            
                            local status = coroutine.status(co)
                            if status == "suspended" then
                                return coroutine.resume(co)
                            end
                            return false, "Coroutine is " .. status
                        end
                    """)
                    
                    # Resume the script
                    safe_resume = self.lua.globals().safe_resume_script
                    success, result = safe_resume(self.lua_thread)
                    
                    if not success:
                        raise Exception(str(result))
                            
        except Exception as e:
            self.log_message.emit(f"Script error: {str(e)}")
            self.output_console.append(traceback.format_exc())
            self.stop_script()

    def get_completion_words(self):
        return [
            # Lua keywords
            "function", "local", "if", "then", "else", "end", "for", "while",
            "repeat", "until", "break", "return", "and", "or", "not",
            
            # Device functions
            "get_device", "move_to", "set_speed", "home", "set_output",
            "set_pwm", "conveyor_move", "conveyor_stop", "conveyor_step",
            "get_encoder_position", "reset_encoder", "set_encoder_mode",
            
            # Utility functions
            "sleep", "get_time", "average", "median", "print",
            
            # Math functions
            "math.sin", "math.cos", "math.tan", "math.abs", "math.sqrt",
            "math.pi", "math.rad", "math.deg", "math.floor", "math.ceil",
            
            # Common variables
            "robot", "conveyor", "encoder", "position", "speed", "steps",
            "forward", "backward", "absolute", "relative"
        ]

    def show_help(self):
        """Show the help dialog"""
        dialog = HelpDialog(self)
        dialog.exec_() 