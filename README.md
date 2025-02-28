# DeltaX Tool

A modern and user-friendly GUI application for controlling DeltaX robot using G-code commands.

## Features

- Modern, touch-friendly interface
- Real-time robot control
- Position control (G0/G1)
- Direct angle control (G6)
- Homing function (G28)
- Absolute/Relative positioning modes (G90/G91)
- Position feedback (G93)
- Digital and PWM output control (M03/M04/M05)
- Manual G-code command input
- Communication logging
- Auto-detection of COM ports

## Requirements

- Python 3.6 or higher
- PyQt5
- pyserial

## Installation

1. Clone or download this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
cd src
python deltax_tool.py
```

2. Connect to robot:
   - Select the COM port from the dropdown list
   - Click "Connect" (baudrate is set to 115200)
   - The connection status will be shown in the log area

3. Control the robot:
   - Use the "Movement Control" tab for position control
   - Enter coordinates and angles in the input fields
   - Set feed rate and acceleration as needed
   - Click "Move" to execute the movement
   - Use "Home" to perform homing operation
   - Use "Get Position" to read current position
   - Switch between absolute and relative modes using the mode buttons

4. Control outputs:
   - Set digital output pin number (0-15) and click ON/OFF
   - Set PWM output pin (0-15) and value (0-255)
   - Click "Set PWM" to apply PWM value

5. Manual commands:
   - Switch to "Manual Command" tab
   - Enter any G-code command
   - Press Enter or click "Send Command"

6. Monitor communication:
   - All sent commands and received responses are logged
   - Use "Clear Log" to clear the log area

## Note

All commands sent to the robot automatically include a newline character. 