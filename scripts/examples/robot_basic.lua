-- Basic Robot Control Example
-- This script demonstrates basic robot movement commands

-- Get robot device
local robot = get_device("Robot 1")
if not robot then
    print("Error: Robot not found!")
    return
end

-- Home the robot first
print("Homing robot...")
home_robot(robot)

-- Move in a square pattern
print("Moving in square pattern...")
move_to(robot, 0, 0, 50)      -- Move to starting position
move_to(robot, 100, 0, 50)    -- Move right
move_to(robot, 100, 100, 50)  -- Move forward
move_to(robot, 0, 100, 50)    -- Move left
move_to(robot, 0, 0, 50)      -- Return to start

print("Square movement completed!")

-- Move in a circular pattern
print("Moving in circular pattern...")
local radius = 50
local center_x = 50
local center_y = 50
local z_height = 30

for angle = 0, 360, 10 do
    local rad = math.rad(angle)
    local x = center_x + radius * math.cos(rad)
    local y = center_y + radius * math.sin(rad)
    move_to(robot, x, y, z_height)
end

print("Circle movement completed!")
print("All movements completed successfully!") 