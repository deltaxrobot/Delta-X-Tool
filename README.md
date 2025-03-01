# DeltaX Tool

A powerful control and scripting tool for DeltaX robot systems.

## Features

### Script Editor
- **Lua Scripting**: Write and execute Lua scripts to control robots, conveyors, and encoders
- **Code Completion**: Intelligent code suggestions for Lua keywords and device functions
- **Syntax Highlighting**: Color-coded syntax for better code readability
- **Line Numbers**: Visual line numbering for easy code navigation
- **Documentation**: Built-in help system with function references and code examples

### Device Control
- **Robot Control**: Move robot, set speed, control outputs
- **Conveyor Control**: Forward/backward movement, step control
- **Encoder Integration**: Position monitoring, mode configuration

### File Management
- **Script Organization**: Create, save, and manage Lua script files
- **Template System**: New scripts created with helpful templates
- **File Browser**: Easy access to saved scripts

## Getting Started

### Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install PyQt5 lupa
```

### Basic Usage
1. Launch DeltaX Tool
2. Connect to your devices
3. Create a new script or open an existing one
4. Write your control script using Lua
5. Run the script to control your devices

### Example Script
```lua
-- Get devices
local robot = get_device("Robot 1")
local conveyor = get_device("Conveyor 1")
local encoder = get_device("Encoder 1")

-- Check connections
if not robot then
    print("Error: Robot not found!")
    return
end

-- Basic movement sequence
robot:set_speed(100)      -- Set speed to 100mm/s
robot:move_to(0, 0, 100)  -- Move to position
sleep(1)                  -- Wait for 1 second
```

## Available Functions

### Robot Functions
- `robot:move_to(x, y, z)` - Move robot to position (mm)
- `robot:set_speed(speed)` - Set movement speed (mm/s)
- `robot:home()` - Home all axes
- `robot:set_output(pin, on)` - Control digital output
- `robot:set_pwm(pin, value)` - Set PWM output

### Conveyor Functions
- `conveyor_move(dev, dir, speed)` - Move conveyor
- `conveyor_stop(dev)` - Stop conveyor
- `conveyor_step(dev, steps, speed)` - Move specific steps

### Encoder Functions
- `get_encoder_position(dev)` - Get current position
- `reset_encoder(dev)` - Reset position to zero
- `set_encoder_mode(dev, mode)` - Set mode (absolute/relative)

### Utility Functions
- `sleep(seconds)` - Pause execution
- `get_time()` - Get current time
- `average(values)` - Calculate array average
- `median(values)` - Calculate array median
- `print(...)` - Print to output console

## Keyboard Shortcuts
- `Ctrl + Space`: Show code completion
- `Ctrl + S`: Save script
- `Ctrl + Z`: Undo
- `Ctrl + Y`: Redo
- `Ctrl + F`: Find text
- `Ctrl + H`: Replace text

## Contributing
Feel free to submit issues and enhancement requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details. 