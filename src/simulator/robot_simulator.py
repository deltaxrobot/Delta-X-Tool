import serial
import time
import threading
from queue import Queue, Empty
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

from .robot_state import RobotState
from .gcode_parser import GCodeParser

class RobotSimulator(QObject):
    # Signal to update 3D visualization
    movement_started = pyqtSignal(float, float, float, float)  # x, y, z, duration
    movement_finished = pyqtSignal()

    def __init__(self, port: str = 'COM1', baudrate: int = 115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.command_queue = Queue()
        
        # Initialize robot state and G-code parser
        self.robot_state = RobotState()
        self.gcode_parser = GCodeParser(self.robot_state)
        
        # Communication threads
        self.reader_thread: Optional[threading.Thread] = None
        self.processor_thread: Optional[threading.Thread] = None
        
        # Movement simulation
        self.current_movement_thread: Optional[threading.Thread] = None
        self.movement_lock = threading.Lock()

    def start(self):
        """Start the robot simulator."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            
            self.running = True
            self.reader_thread = threading.Thread(target=self._reader_loop)
            self.processor_thread = threading.Thread(target=self._processor_loop)
            
            self.reader_thread.daemon = True
            self.processor_thread.daemon = True
            
            self.reader_thread.start()
            self.processor_thread.start()
            
            print(f"Robot simulator started on {self.port}")
            
        except serial.SerialException as e:
            print(f"Error opening serial port {self.port}: {e}")
            self.running = False

    def stop(self):
        """Stop the robot simulator."""
        self.running = False
        if self.reader_thread:
            self.reader_thread.join()
        if self.processor_thread:
            self.processor_thread.join()
        if self.serial:
            self.serial.close()

    def _reader_loop(self):
        """Read commands from serial port."""
        buffer = ""
        
        while self.running:
            if self.serial and self.serial.in_waiting:
                char = self.serial.read().decode('ascii')
                
                if char == '\n':
                    command = buffer.strip()
                    if command:
                        self.command_queue.put(command)
                    buffer = ""
                else:
                    buffer += char
            else:
                time.sleep(0.001)  # Small delay to prevent CPU hogging

    def _processor_loop(self):
        """Process commands from the queue."""
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
                success, response, delay = self.gcode_parser.execute_command(command)
                
                if success and delay > 0:
                    # For movement commands, simulate real-time movement
                    if command.startswith(('G0', 'G1')):
                        self._simulate_movement(delay)
                    else:
                        # For non-movement commands, just wait
                        time.sleep(delay)
                
                # Send response
                if self.serial:
                    response_str = response + "\n"
                    self.serial.write(response_str.encode('ascii'))
                    
            except Empty:
                continue
            except Exception as e:
                print(f"Error processing command: {e}")

    def _simulate_movement(self, duration: float):
        """Simulate robot movement in real-time."""
        with self.movement_lock:
            # Signal movement start with target position and duration
            self.movement_started.emit(
                self.robot_state.current_position.x,
                self.robot_state.current_position.y,
                self.robot_state.current_position.z,
                duration
            )
            
            # Wait for the movement duration
            time.sleep(duration)
            
            # Signal movement completion
            self.movement_finished.emit()

def main():
    """Main entry point for the robot simulator."""
    simulator = RobotSimulator()
    simulator.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down simulator...")
        simulator.stop()

if __name__ == '__main__':
    main() 