from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QGroupBox
from PyQt5.QtCore import Qt, pyqtSlot
from .opengl_widget import DeltaRobotWidget
import math

class DeltaControlWidget(QWidget):
    """Widget combining Delta robot visualization with position control sliders."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create OpenGL widget for robot visualization
        self.robot_widget = DeltaRobotWidget(self)
        main_layout.addWidget(self.robot_widget, 1)  # Give it stretch factor of 1
        
        # Create slider controls
        slider_group = QGroupBox("Position Controls")
        slider_layout = QVBoxLayout(slider_group)
        
        # X position slider
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self.x_slider = QSlider(Qt.Horizontal)
        self.x_slider.setMinimum(0)
        self.x_slider.setMaximum(100)
        self.x_slider.setValue(50)  # Center position
        self.x_slider.setTickPosition(QSlider.TicksBelow)
        self.x_slider.setTickInterval(10)
        self.x_value_label = QLabel("0 mm")
        x_layout.addWidget(self.x_slider)
        x_layout.addWidget(self.x_value_label)
        slider_layout.addLayout(x_layout)
        
        # Y position slider
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.y_slider = QSlider(Qt.Horizontal)
        self.y_slider.setMinimum(0)
        self.y_slider.setMaximum(100)
        self.y_slider.setValue(50)  # Center position
        self.y_slider.setTickPosition(QSlider.TicksBelow)
        self.y_slider.setTickInterval(10)
        self.y_value_label = QLabel("0 mm")
        y_layout.addWidget(self.y_slider)
        y_layout.addWidget(self.y_value_label)
        slider_layout.addLayout(y_layout)
        
        # Z position slider
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Z:"))
        self.z_slider = QSlider(Qt.Horizontal)
        self.z_slider.setMinimum(0)
        self.z_slider.setMaximum(100)
        self.z_slider.setValue(50)  # Middle position
        self.z_slider.setTickPosition(QSlider.TicksBelow)
        self.z_slider.setTickInterval(10)
        self.z_value_label = QLabel("-500 mm")
        z_layout.addWidget(self.z_slider)
        z_layout.addWidget(self.z_value_label)
        slider_layout.addLayout(z_layout)
        
        # Add slider group to main layout
        main_layout.addWidget(slider_group)
        
        # Connect signals and slots
        self.x_slider.valueChanged.connect(self.update_position)
        self.y_slider.valueChanged.connect(self.update_position)
        self.z_slider.valueChanged.connect(self.update_position)
        
        # Connect robot position signal to update labels
        self.robot_widget.position_changed.connect(self.update_position_labels)
        
        # Robot position limits
        self.x_min, self.x_max = -300, 300
        self.y_min, self.y_max = -300, 300
        self.z_min, self.z_max = -800, -200
        
        # Set initial position
        self.update_position()
    
    def slider_to_position(self, slider_value, min_val, max_val):
        """
        Convert slider value (0-100) to actual position using a non-linear mapping.
        Uses a quadratic function to provide more precision in the center.
        """
        # Normalize slider value to -1 to 1 range
        normalized = (slider_value / 50.0) - 1.0
        
        # Apply non-linear mapping (cubic function for more precision in center)
        # This gives more control in the center region
        if normalized >= 0:
            factor = normalized * normalized * (3 - 2 * normalized)
        else:
            factor = -(-normalized * -normalized * (3 - 2 * -normalized))
        
        # Scale to min-max range
        mid_val = (min_val + max_val) / 2
        half_range = (max_val - min_val) / 2
        return mid_val + factor * half_range
    
    def position_to_slider(self, position, min_val, max_val):
        """
        Convert actual position to slider value (0-100).
        Inverse of slider_to_position function.
        """
        # Normalize position to -1 to 1 range
        mid_val = (min_val + max_val) / 2
        half_range = (max_val - min_val) / 2
        normalized = (position - mid_val) / half_range
        
        # Apply inverse of non-linear mapping
        # For cubic function, we use an approximation
        if normalized >= 0:
            factor = math.pow(normalized, 1/3)
        else:
            factor = -math.pow(-normalized, 1/3)
        
        # Convert to slider range (0-100)
        return int((factor + 1.0) * 50.0)
    
    @pyqtSlot(int)
    def update_position(self, _=None):
        """Update the robot position based on slider values."""
        # Convert slider values to actual positions using non-linear mapping
        x = self.slider_to_position(self.x_slider.value(), self.x_min, self.x_max)
        y = self.slider_to_position(self.y_slider.value(), self.y_min, self.y_max)
        z = self.slider_to_position(self.z_slider.value(), self.z_min, self.z_max)
        
        # Update position labels
        self.x_value_label.setText(f"{int(x)} mm")
        self.y_value_label.setText(f"{int(y)} mm")
        self.z_value_label.setText(f"{int(z)} mm")
        
        # Update robot position with a short animation
        self.robot_widget.start_movement(x, y, z, 0.5)  # 0.5 second animation
    
    @pyqtSlot(float, float, float)
    def update_position_labels(self, x, y, z):
        """Update position labels and sliders when robot position changes."""
        # Update labels
        self.x_value_label.setText(f"{int(x)} mm")
        self.y_value_label.setText(f"{int(y)} mm")
        self.z_value_label.setText(f"{int(z)} mm")
        
        # Convert actual positions to slider values
        x_slider = self.position_to_slider(x, self.x_min, self.x_max)
        y_slider = self.position_to_slider(y, self.y_min, self.y_max)
        z_slider = self.position_to_slider(z, self.z_min, self.z_max)
        
        # Update sliders without triggering valueChanged signals
        self.x_slider.blockSignals(True)
        self.y_slider.blockSignals(True)
        self.z_slider.blockSignals(True)
        
        self.x_slider.setValue(x_slider)
        self.y_slider.setValue(y_slider)
        self.z_slider.setValue(z_slider)
        
        self.x_slider.blockSignals(False)
        self.y_slider.blockSignals(False)
        self.z_slider.blockSignals(False)