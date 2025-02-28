import math
import time
from dataclasses import dataclass
from typing import Optional, Dict
from PyQt5.QtCore import QObject, pyqtSignal

@dataclass
class Position:
    x: float = 0
    y: float = 0
    z: float = -750  # Default Z position
    w: float = 0.0  # Axis 4 angle
    u: float = 0.0  # Axis 5 angle
    v: float = 0.0  # Axis 6 angle

@dataclass
class MovementParams:
    feed_rate: float = 200.0  # mm/s
    acceleration: float = 5000.0  # mm/s^2
    jerk: float = 1200000.0  # mm/s^3
    begin_velocity: float = 0.0  # mm/s
    end_velocity: float = 0.0  # mm/s

class RobotState(QObject):
    # Signal emitted when position changes
    position_changed = pyqtSignal(float, float, float)

    def __init__(self):
        super().__init__()
        self.current_position = Position()
        self.movement_params = MovementParams()
        self.is_absolute_mode = True
        self.is_homed = False
        self.z_safe = -870  # Default Z safe limit
        self.last_command_time = time.time()
        
        # Position and movement
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0
        
        # Theta angles (for direct control)
        self.theta1 = 0
        self.theta2 = 0
        self.theta3 = 0
        
        # Movement parameters
        self.begin_end_velocity = 40  # Default begin/end velocity
        
        # I/O state
        self.digital_outputs: Dict[int, bool] = {}  # Pin number -> state
        self.digital_inputs: Dict[int, bool] = {}   # Pin number -> state
        self.analog_inputs: Dict[int, int] = {}     # Pin number -> value
        self.pwm_outputs: Dict[int, int] = {}      # Pin number -> value
        
        # Initialize default input values for simulation
        for i in range(8):  # Digital inputs 0-7
            self.digital_inputs[i] = False
        for i in range(4):  # Analog inputs 0-3
            self.analog_inputs[i] = 0

    def calculate_move_time(self, target: Position) -> float:
        """Calculate the time needed to move from current position to target."""
        dx = target.x - self.current_position.x
        dy = target.y - self.current_position.y
        dz = target.z - self.current_position.z
        
        # Calculate distance
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Simple time calculation based on constant velocity
        # In reality, this should account for acceleration and deceleration
        if distance == 0:
            return 0
            
        time_s = distance / self.movement_params.feed_rate
        return max(0.1, time_s)  # Minimum 0.1s for any movement

    def update_position(self, new_position: Position):
        """Update the current position."""
        self.current_position = new_position
        self.last_command_time = time.time()
        # Emit signal with new position
        self.position_changed.emit(
            new_position.x,
            new_position.y,
            new_position.z
        )

    def get_position_str(self) -> str:
        """Get current position as a string in the format expected by G93."""
        return f"{self.current_position.x:.3f},{self.current_position.y:.3f},{self.current_position.z:.3f}"

    def set_digital_output(self, pin: int, value: bool):
        """Set digital output pin state."""
        if 0 <= pin < 16:
            self.digital_outputs[pin] = value

    def set_pwm_output(self, pin: int, value: int, high_resolution: bool = False):
        """Set PWM output pin value."""
        if 0 <= pin < 16:
            max_value = 65535 if high_resolution else 255
            self.pwm_outputs[pin] = min(max(0, value), max_value)

    def get_digital_input(self, pin: int) -> Optional[bool]:
        """Get digital input pin state."""
        if 0 <= pin < 8:
            return self.digital_inputs[pin]
        return None

    def get_analog_input(self, pin: int) -> Optional[int]:
        """Get analog input pin value."""
        if 0 <= pin < 4:
            return self.analog_inputs[pin]
        return None 