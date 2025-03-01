# DeltaX Tool

A modern and user-friendly GUI application for controlling DeltaX robot system, including the main robot, conveyor, encoder, and MCU devices. The tool provides an intuitive interface for real-time control, monitoring, and automation of the DeltaX robotic system.

## Features

### Robot Control
- Modern, touch-friendly interface with optimized layout
- Real-time position control (G0/G1)
- Direct angle control (G6)
- Homing function (G28)
- Absolute/Relative positioning modes (G90/G91)
- Position feedback (G93)
- Digital and PWM output control (M03/M04/M05)
- Manual G-code command input
- Communication logging
- Intelligent auto-detection and connection of COM ports

### Conveyor Control
- Intuitive two-column layout for easy access to all functions
- Multiple motion modes: Continuous, Step, and Distance
- Configurable speed and acceleration parameters
- Output control for motor direction and enable signals
- Real-time encoder position monitoring
- Encoder configuration options:
  - Mode selection (Absolute/Relative/Input Pin/Button)
  - Pulses per mm calibration
  - Scale factor adjustment
  - Direction reversal option

### Encoder Integration
- Support for industrial encoder feedback
- Position tracking in absolute and relative modes
- Configurable parameters for accurate measurements
- Real-time position updates
- Position reset and reference point setting
- Input pin monitoring for external triggers

### MCU Device Support
- Dedicated interface for MCU device control
- Auto-detection and connection management
- Serial communication with configurable baud rate
- Command sending and response monitoring
- Status display and error handling

## Requirements

- Python 3.8 or higher
- PyQt5
- pyserial
- Operating System: Windows 10/11, Linux (Ubuntu 20.04+)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/deltaxrobot/Delta-X-Tool.git
cd deltax_tool
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application
```bash
cd src
python deltax_tool.py
```

### Device Connection
1. **Auto-Connect Mode:**
   - Enable "Auto Connect" checkbox
   - The system will automatically scan and connect to available devices
   - Connection status is displayed in the respective device panels

2. **Manual Connection:**
   - Select the appropriate COM port from the dropdown list
   - Choose the baud rate (default: 115200 for robot, 9600 for other devices)
   - Click "Connect" button
   - Monitor connection status in the log area

### Robot Control
1. **Position Control:**
   - Use the Movement Control panel
   - Enter X, Y, Z coordinates or A, B, C angles
   - Set feed rate and acceleration
   - Click "Move" to execute
   - Use "Home" for homing operation

2. **Output Control:**
   - Set digital output pins (0-15)
   - Configure PWM outputs (0-255)
   - Monitor output states

### Conveyor Operation
1. **Motion Control:**
   - Select desired motion mode (Continuous/Step/Distance)
   - Configure speed and acceleration
   - Use direction controls for movement
   - Monitor encoder position in real-time

2. **Encoder Settings:**
   - Choose encoder mode
   - Set pulses per mm and scale factor
   - Configure direction and reference points
   - Enable auto-update for position monitoring

### Communication Monitoring
- All device communications are logged in respective panels
- Use "Clear Log" to reset the display
- Error messages and warnings are highlighted
- Connection status is continuously updated

## Documentation

Detailed documentation for specific components:
- [Robot G-Code Commands](gcode-deltaxs.md)
- [Industrial Conveyor Protocol](gc_industrial_conveyor.md)
- [Encoder Communication](gc_encoder.md)

## Troubleshooting

1. **Connection Issues:**
   - Verify COM port availability
   - Check device power and USB connections
   - Ensure correct baud rate settings
   - Review connection logs for error messages

2. **Communication Errors:**
   - Check cable connections
   - Verify device firmware compatibility
   - Reset devices if necessary
   - Review command syntax

## Note

- Commands are automatically terminated with newline characters
- Device configurations are saved between sessions
- Auto-connect settings persist after restart
- Error handling ensures safe operation
- Regular updates improve functionality and stability

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 