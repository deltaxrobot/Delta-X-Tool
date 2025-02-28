import re
from typing import Dict, Any, Optional, Tuple
from .robot_state import Position, RobotState
import math

class GCodeParser:
    def __init__(self, robot_state: RobotState):
        self.robot_state = robot_state
        self.absolute_mode = True  # G90 is default
        self.current_feedrate = 200  # Default feedrate (mm/s)
        self.current_acceleration = 5000  # Default acceleration (mm/s^2)
        self.current_jerk = 1200000  # Default jerk (mm/s^3)
        
    def parse_params(self, command: str) -> Dict[str, float]:
        """Parse G-code parameters from command string."""
        params = {}
        pattern = r'([A-Z])([-+]?\d*\.?\d+)'
        matches = re.finditer(pattern, command)
        
        for match in matches:
            param, value = match.groups()
            params[param] = float(value)
            
        return params

    def calculate_movement_time(self, start: Position, end: Position, feedrate: float) -> float:
        """Calculate the time needed for a movement."""
        dx = end.x - start.x
        dy = end.y - start.y
        dz = end.z - start.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Simple time calculation based on distance and feedrate
        return distance / feedrate if feedrate > 0 else 0

    def execute_command(self, command: str) -> Tuple[bool, str, float]:
        """Execute a G-code command and return (success, response, delay)."""
        command = command.upper().strip()
        if not command:
            return True, "Ok\n", 0
            
        # Extract command type and parameters
        parts = command.split()
        cmd_type = parts[0]
        params = self.parse_params(command)
        
        try:
            # Special commands
            if cmd_type == 'ISDELTA':
                return True, "YesDelta\n", 0
                
            # Movement commands
            if cmd_type in ['G0', 'G1', 'G01', 'G00']:
                return self._handle_linear_move(params)
                
            # Arc movement
            elif cmd_type in ['G2', 'G02', 'G3', 'G03']:
                return self._handle_arc_move(cmd_type, params)
                
            # Dwell
            elif cmd_type in ['G4', 'G04']:
                return self._handle_dwell(params)
                
            # Direct theta control
            elif cmd_type in ['G6', 'G06']:
                return self._handle_theta_control(params)
                
            # Homing
            elif cmd_type == 'G28':
                return self._handle_homing()
                
            # Movement mode
            elif cmd_type == 'G90':
                self.absolute_mode = True
                return True, "Ok\n", 0
                
            elif cmd_type == 'G91':
                self.absolute_mode = False
                return True, "Ok\n", 0
                
            # Get position
            elif cmd_type == 'G93':
                pos = self._handle_get_position()
                return True, pos[1] + "\n", pos[2]  # Position response already includes coordinates
                
            # Output control
            elif cmd_type in ['M3', 'M03', 'M4', 'M04']:
                return self._handle_output_on(params)
                
            elif cmd_type in ['M5', 'M05']:
                return self._handle_output_off(params)
                
            # Input reading
            elif cmd_type in ['M7', 'M07']:
                resp = self._handle_read_input(params)
                return True, resp[1] + "\n", resp[2]  # Input readings already include proper format
                
            # Movement parameters
            elif cmd_type == 'M203':
                return self._handle_set_jerk(params)
                
            elif cmd_type == 'M204':
                return self._handle_set_acceleration(params)
                
            elif cmd_type == 'M205':
                return self._handle_set_velocity(params)
                
            elif cmd_type == 'M206':
                return self._handle_set_offset(params)
                
            elif cmd_type == 'M207':
                return self._handle_set_z_safe(params)
                
            else:
                return False, f"error: Unknown command {cmd_type}\n", 0
                
        except Exception as e:
            return False, f"error: {str(e)}\n", 0

    def _handle_linear_move(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle G0/G1 linear movement commands."""
        # Update feedrate if specified
        if 'F' in params:
            self.current_feedrate = params['F']
        if 'A' in params:
            self.current_acceleration = params['A']
        if 'J' in params:
            self.current_jerk = params['J']
            
        # Calculate target position
        target = Position(
            x=params.get('X', self.robot_state.current_position.x if self.absolute_mode else 0),
            y=params.get('Y', self.robot_state.current_position.y if self.absolute_mode else 0),
            z=params.get('Z', self.robot_state.current_position.z if self.absolute_mode else 0)
        )
        
        if not self.absolute_mode:
            target.x += self.robot_state.current_position.x
            target.y += self.robot_state.current_position.y
            target.z += self.robot_state.current_position.z
            
        # Calculate movement time
        move_time = self.calculate_movement_time(
            self.robot_state.current_position,
            target,
            self.current_feedrate
        )
        
        # Update position
        self.robot_state.current_position = target
        
        return True, "Ok\n", move_time

    def _handle_arc_move(self, cmd_type: str, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle G2/G3 arc movement commands."""
        # For simulation, we'll treat arc moves as linear moves
        # In a real implementation, proper arc interpolation would be needed
        result = self._handle_linear_move(params)
        return True, "Ok\n", result[2]

    def _handle_dwell(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle G4 dwell command."""
        if 'P' not in params:
            return False, "error: Missing P parameter for dwell\n", 0
        return True, "Ok\n", params['P'] / 1000  # Convert ms to seconds

    def _handle_theta_control(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle G6 direct theta control."""
        # Update theta angles in robot state
        if 'X' in params:
            self.robot_state.theta1 = params['X']
        if 'Y' in params:
            self.robot_state.theta2 = params['Y']
        if 'Z' in params:
            self.robot_state.theta3 = params['Z']
        return True, "Ok\n", 0.1  # Small delay for angle changes

    def _handle_homing(self) -> Tuple[bool, str, float]:
        """Handle G28 homing command."""
        self.robot_state.current_position = Position(0, 0, -750)  # Home position
        return True, "Ok\n", 2.0  # Typical homing time

    def _handle_get_position(self) -> Tuple[bool, str, float]:
        """Handle G93 get position command."""
        pos = self.robot_state.current_position
        return True, f"{pos.x:.3f},{pos.y:.3f},{pos.z:.3f}", 0

    def _handle_output_on(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M3/M4 output on commands."""
        if 'D' in params:
            pin = int(params['D'])
            self.robot_state.digital_outputs[pin] = True
        elif 'P' in params and 'W' in params:
            pin = int(params['P'])
            value = int(params['W'])
            self.robot_state.pwm_outputs[pin] = value
        return True, "Ok\n", 0

    def _handle_output_off(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M5 output off command."""
        if 'D' in params:
            pin = int(params['D'])
            self.robot_state.digital_outputs[pin] = False
        elif 'P' in params:
            pin = int(params['P'])
            self.robot_state.pwm_outputs[pin] = 0
        return True, "Ok\n", 0

    def _handle_read_input(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M7 input reading command."""
        responses = []
        for param, value in params.items():
            pin = int(value)
            if param == 'I':
                val = self.robot_state.digital_inputs.get(pin, 0)
                responses.append(f"I{pin} V{val}")
            elif param == 'A':
                val = self.robot_state.analog_inputs.get(pin, 0)
                responses.append(f"A{pin} V{val}")
        return True, "\n".join(responses), 0

    def _handle_set_jerk(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M203 set jerk command."""
        if 'J' in params:
            self.current_jerk = params['J']
        return True, "Ok\n", 0

    def _handle_set_acceleration(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M204 set acceleration command."""
        if 'A' in params:
            self.current_acceleration = params['A']
        return True, "Ok\n", 0

    def _handle_set_velocity(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M205 set velocity command."""
        if 'S' in params:
            self.robot_state.begin_end_velocity = params['S']
        return True, "Ok\n", 0

    def _handle_set_offset(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M206 set offset command."""
        if 'X' in params:
            self.robot_state.x_offset = params['X']
        if 'Y' in params:
            self.robot_state.y_offset = params['Y']
        if 'Z' in params:
            self.robot_state.z_offset = params['Z']
        return True, "Ok\n", 0

    def _handle_set_z_safe(self, params: Dict[str, float]) -> Tuple[bool, str, float]:
        """Handle M207 set Z safe command."""
        if 'Z' in params:
            self.robot_state.z_safe = params['Z']
        return True, "Ok\n", 0 