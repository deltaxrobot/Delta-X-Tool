-- Basic Robot Control Example
-- This script demonstrates basic robot movement commands

-- Get robot device
local robot = get_device("Robot 1")
if not robot then
    print("Error: Robot not found!")
    return
end

-- Set movement speed
robot:set_speed(1000)  -- 1000mm/min

-- Home the robot first
print("Homing robot...")
robot:home()

-- Move in a square pattern
print("Moving in square pattern...")
robot:move_to(0, 0, -850)      -- Move to starting position
robot:move_to(100, 0, -850)    -- Move right
robot:move_to(100, 100, -850)  -- Move forward
robot:move_to(0, 100, -850)    -- Move left
robot:move_to(0, 0, -850)      -- Return to start

print("Square movement completed!")

-- Move in a circular pattern
print("Moving in circular pattern...")
local radius = 100
local center_x = 50
local center_y = 50
local z_height = -850

for angle = 0, 360, 10 do
    local rad = math.rad(angle)
    local x = center_x + radius * math.cos(rad)
    local y = center_y + radius * math.sin(rad)
    robot:move_to(x, y, z_height)
end

print("Circle movement completed!")
print("All movements completed successfully!") 