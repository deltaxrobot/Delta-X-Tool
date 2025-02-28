-- Conveyor Control Example
-- This script demonstrates conveyor movement and synchronization

-- Get devices
local conveyor = get_device("Conveyor 1")
local robot = get_device("Robot 1")

if not conveyor or not robot then
    print("Error: Required devices not found!")
    return
end

-- Configure conveyor
print("Configuring conveyor...")
send_command(conveyor, "M310 1")  -- Set to Position Mode
wait_response()

send_command(conveyor, "M313 200")  -- Set movement speed to 200mm/s
wait_response()

-- Initialize robot
print("Initializing robot...")
home_robot(robot)
move_to(robot, 0, 0, 50)  -- Move to safe position

-- Main process loop
print("Starting main process...")
for i = 1, 5 do
    print("Cycle", i)
    
    -- Move conveyor to pickup position
    print("Moving conveyor to pickup position...")
    move_conveyor_to(conveyor, i * 100)  -- Move 100mm each cycle
    
    -- Robot pick sequence
    print("Executing pick sequence...")
    move_to(robot, 100, 0, 50)   -- Move above pickup
    move_to(robot, 100, 0, 0)    -- Move down
    move_to(robot, 100, 0, 50)   -- Move up with part
    
    -- Move conveyor to place position
    print("Moving conveyor to place position...")
    move_conveyor_to(conveyor, i * 100 + 50)  -- Move additional 50mm
    
    -- Robot place sequence
    print("Executing place sequence...")
    move_to(robot, 0, 100, 50)   -- Move above place
    move_to(robot, 0, 100, 0)    -- Move down
    move_to(robot, 0, 100, 50)   -- Move up
    
    print("Cycle", i, "completed")
end

-- Return to home position
print("Returning to home position...")
home_robot(robot)
move_conveyor_to(conveyor, 0)  -- Return conveyor to start

print("Process completed successfully!") 