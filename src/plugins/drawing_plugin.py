from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QSpinBox, QDoubleSpinBox, QGroupBox, 
                           QGraphicsView, QGraphicsScene, QMessageBox)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QColor, QPainter, QBrush
import os

from .base_plugin import BasePlugin

class DrawingArea(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Set up the view
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Set up the coordinate system
        self.scale(1, -1)  # Flip Y axis to match robot coordinates
        self.setSceneRect(-400, -400, 800, 800)  # Robot workspace
        
        # Drawing settings
        self.pen = QPen(Qt.blue, 2, Qt.SolidLine)
        self.drawing = False
        self.last_point = None
        self.current_tool = "line"  # line, rectangle, circle
        
        # Draw workspace boundaries
        self.draw_workspace()
        
    def draw_workspace(self):
        # Draw workspace circle
        workspace = self.scene.addEllipse(-350, -350, 700, 700, 
                                        QPen(Qt.gray, 1, Qt.DashLine))
        
        # Draw coordinate axes
        self.scene.addLine(-400, 0, 400, 0, QPen(Qt.red, 1))  # X axis
        self.scene.addLine(0, -400, 0, 400, QPen(Qt.green, 1))  # Y axis
        
        # Add grid (every 50mm)
        for i in range(-400, 401, 50):
            self.scene.addLine(i, -400, i, 400, 
                             QPen(QColor(200, 200, 200), 1, Qt.DotLine))
            self.scene.addLine(-400, i, 400, i,
                             QPen(QColor(200, 200, 200), 1, Qt.DotLine))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            scene_pos = self.mapToScene(event.pos())
            self.last_point = scene_pos
            
            if self.current_tool == "line":
                # Start new line
                self.current_item = self.scene.addLine(
                    scene_pos.x(), scene_pos.y(),
                    scene_pos.x(), scene_pos.y(),
                    self.pen
                )
            elif self.current_tool == "rectangle":
                # Start new rectangle
                self.current_item = self.scene.addRect(
                    scene_pos.x(), scene_pos.y(), 0, 0,
                    self.pen
                )
            elif self.current_tool == "circle":
                # Start new circle
                self.current_item = self.scene.addEllipse(
                    scene_pos.x(), scene_pos.y(), 0, 0,
                    self.pen
                )
    
    def mouseMoveEvent(self, event):
        if self.drawing:
            scene_pos = self.mapToScene(event.pos())
            
            if self.current_tool == "line":
                self.current_item.setLine(
                    self.last_point.x(), self.last_point.y(),
                    scene_pos.x(), scene_pos.y()
                )
            elif self.current_tool == "rectangle":
                rect = QRectF(self.last_point, scene_pos).normalized()
                self.current_item.setRect(rect)
            elif self.current_tool == "circle":
                radius = ((scene_pos.x() - self.last_point.x())**2 + 
                         (scene_pos.y() - self.last_point.y())**2)**0.5
                self.current_item.setRect(
                    self.last_point.x() - radius,
                    self.last_point.y() - radius,
                    radius * 2, radius * 2
                )
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.last_point = None
    
    def set_tool(self, tool):
        self.current_tool = tool
    
    def clear(self):
        self.scene.clear()
        self.draw_workspace()
    
    def get_path(self):
        """Convert drawn shapes to robot movement commands"""
        path = []
        for item in self.scene.items():
            # Skip grid lines and axes (which are QGraphicsLineItem)
            if item in [self.scene.items()[-1], self.scene.items()[-2]]:  # Skip workspace circle and axes
                continue
                
            # Check item type and extract coordinates
            if isinstance(item, type(self.scene.addLine(0,0,0,0))):  # Line
                line = item.line()
                path.append(("line", (line.x1(), line.y1(), line.x2(), line.y2())))
            elif isinstance(item, type(self.scene.addRect(0,0,0,0))):  # Rectangle
                rect = item.rect()
                path.append(("rectangle", (rect.x(), rect.y(), 
                                        rect.width(), rect.height())))
            elif isinstance(item, type(self.scene.addEllipse(0,0,0,0))):  # Circle
                ellipse = item.rect()
                path.append(("circle", (ellipse.center().x(), ellipse.center().y(),
                                      ellipse.width()/2)))
        return path

class DrawingPlugin(BasePlugin):
    def __init__(self, device_manager):
        super().__init__(device_manager)
        self.name = "Drawing"
        self.description = "Draw paths for robot movement"
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Drawing controls in horizontal layout at top
        controls = QGroupBox("Drawing Tools")
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        
        # Tool buttons
        self.line_btn = QPushButton("Line")
        self.line_btn.setCheckable(True)
        self.line_btn.setChecked(True)
        self.line_btn.clicked.connect(lambda: self.select_tool("line"))
        self.line_btn.setFixedWidth(80)
        controls_layout.addWidget(self.line_btn)
        
        self.rect_btn = QPushButton("Rectangle")
        self.rect_btn.setCheckable(True)
        self.rect_btn.clicked.connect(lambda: self.select_tool("rectangle"))
        self.rect_btn.setFixedWidth(80)
        controls_layout.addWidget(self.rect_btn)
        
        self.circle_btn = QPushButton("Circle")
        self.circle_btn.setCheckable(True)
        self.circle_btn.clicked.connect(lambda: self.select_tool("circle"))
        self.circle_btn.setFixedWidth(80)
        controls_layout.addWidget(self.circle_btn)
        
        # Add stretch to push Clear button to right
        controls_layout.addStretch()
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_drawing)
        self.clear_btn.setFixedWidth(80)
        controls_layout.addWidget(self.clear_btn)
        
        controls.setLayout(controls_layout)
        controls.setFixedHeight(80)  # Fixed height for controls
        layout.addWidget(controls)
        
        # Drawing area takes remaining space
        self.drawing_area = DrawingArea()
        self.drawing_area.setMinimumHeight(400)  # Minimum height for drawing area
        layout.addWidget(self.drawing_area, stretch=1)  # Give it stretch priority
        
        # Movement settings at bottom
        settings = QGroupBox("Movement Settings")
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(20)  # More space between settings
        
        # Z height
        z_layout = QHBoxLayout()
        z_layout.setSpacing(5)
        z_label = QLabel("Z Height:")
        z_label.setFixedWidth(60)
        z_layout.addWidget(z_label)
        
        self.z_height = QDoubleSpinBox()
        self.z_height.setRange(-900, 0)
        self.z_height.setValue(-850)
        self.z_height.setSuffix(" mm")
        self.z_height.setFixedWidth(100)
        z_layout.addWidget(self.z_height)
        settings_layout.addLayout(z_layout)
        
        # Add stretch between settings
        settings_layout.addStretch()
        
        # Speed
        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(5)
        speed_label = QLabel("Speed:")
        speed_label.setFixedWidth(50)
        speed_layout.addWidget(speed_label)
        
        self.speed = QSpinBox()
        self.speed.setRange(1, 2000)
        self.speed.setValue(1000)
        self.speed.setSuffix(" mm/min")
        self.speed.setFixedWidth(120)
        speed_layout.addWidget(self.speed)
        settings_layout.addLayout(speed_layout)
        
        settings.setLayout(settings_layout)
        settings.setFixedHeight(80)  # Fixed height for settings
        layout.addWidget(settings)
        
        # Execute button at bottom
        self.execute_btn = QPushButton("Execute Movement")
        self.execute_btn.clicked.connect(self.execute_movement)
        self.execute_btn.setFixedHeight(40)  # Taller execute button
        layout.addWidget(self.execute_btn)
    
    def select_tool(self, tool):
        # Uncheck other buttons
        for btn in [self.line_btn, self.rect_btn, self.circle_btn]:
            btn.setChecked(False)
            
        # Check selected button
        if tool == "line":
            self.line_btn.setChecked(True)
        elif tool == "rectangle":
            self.rect_btn.setChecked(True)
        elif tool == "circle":
            self.circle_btn.setChecked(True)
            
        # Set tool in drawing area
        self.drawing_area.set_tool(tool)
    
    def clear_drawing(self):
        self.drawing_area.clear()
    
    def execute_movement(self):
        """Convert drawing to robot movement script and execute"""
        try:
            # Get robot device
            robot = None
            for i in range(self.device_manager.device_list.count()):
                item = self.device_manager.device_list.item(i)
                if hasattr(item, 'device') and item.text() == "Robot 1":
                    robot = item.device
                    break
            
            if not robot:
                QMessageBox.warning(self, "Error", "Robot not found!")
                return
            
            # Generate script from path
            script = ["-- Generated movement script",
                     "local robot = get_device('Robot 1')",
                     "if not robot then",
                     "    print('Error: Robot not found!')",
                     "    return",
                     "end",
                     "",
                     f"robot:set_speed({self.speed.value()})",
                     "",
                     "-- Home robot",
                     "print('Homing robot...')",
                     "robot:home()",
                     ""]
            
            z = self.z_height.value()
            path = self.drawing_area.get_path()
            
            if not path:
                QMessageBox.warning(self, "Error", "No path drawn!")
                return
                
            for shape_type, coords in path:
                if shape_type == "line":
                    x1, y1, x2, y2 = coords
                    script.extend([
                        f"-- Move to start point",
                        f"robot:move_to({x1}, {y1}, {z})",
                        f"-- Draw line to end point", 
                        f"robot:move_to({x2}, {y2}, {z})"
                    ])
                elif shape_type == "rectangle":
                    x, y, w, h = coords
                    script.extend([
                        f"-- Draw rectangle",
                        f"robot:move_to({x}, {y}, {z})",
                        f"robot:move_to({x+w}, {y}, {z})",
                        f"robot:move_to({x+w}, {y+h}, {z})",
                        f"robot:move_to({x}, {y+h}, {z})",
                        f"robot:move_to({x}, {y}, {z})"
                    ])
                elif shape_type == "circle":
                    cx, cy, r = coords
                    script.extend([
                        f"-- Draw circle",
                        f"local center_x = {cx}",
                        f"local center_y = {cy}",
                        f"local radius = {r}",
                        f"",
                        f"for angle = 0, 360, 10 do",
                        f"    local rad = math.rad(angle)",
                        f"    local x = center_x + radius * math.cos(rad)",
                        f"    local y = center_y + radius * math.sin(rad)",
                        f"    robot:move_to(x, y, {z})",
                        f"end"
                    ])
            
            script.extend([
                "",
                "print('Movement completed!')"
            ])
            
            # Save script
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "scripts", "drawing.lua"
            )
            
            # Ensure scripts directory exists
            os.makedirs(os.path.dirname(script_path), exist_ok=True)
            
            with open(script_path, "w") as f:
                f.write("\n".join(script))
            
            # Execute script through script plugin
            script_plugin = None
            for plugin in self.device_manager.plugins.values():
                if plugin.name == "Script":
                    script_plugin = plugin
                    break
            
            if script_plugin:
                # Set the script content in the editor
                script_plugin.script_editor.setPlainText("\n".join(script))
                # Run the script
                script_plugin.run_script()
            else:
                QMessageBox.warning(self, "Error", "Script plugin not found!")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error executing movement: {str(e)}")
            import traceback
            print(traceback.format_exc()) 