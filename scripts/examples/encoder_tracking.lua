-- Encoder Tracking Example
-- This script demonstrates tracking objects using encoder feedback

-- Get devices
local encoder = get_device("Encoder 1")
local robot = get_device("Robot 1")

if not encoder or not robot then
    print("Error: Required devices not found!")
    return
end

-- Configure encoder
print("Configuring encoder...")
send_command(encoder, "M316 1")  -- Set to Relative Mode
wait_response()

-- Initialize robot
print("Initializing robot...")
home_robot(robot)
move_to(robot, 0, 0, 50)  -- Move to safe position

-- Reset encoder position
print("Resetting encoder position...")
send_command(encoder, "M317 R")
wait_response()

-- Enable position tracking
print("Starting position tracking...")
send_command(encoder, "M317 T100")  -- Auto report every 100ms
wait_response()

-- Track and pick objects
print("Waiting for objects...")
local picked_count = 0
local target_count = 3  -- Pick 3 objects

while picked_count < target_count do
    -- Wait for object detection
    wait_until(function()
        local pos = get_encoder_position(encoder)
        return pos >= 100  -- Object detected at 100mm
    end, 30)  -- Timeout after 30 seconds
    
    -- Object detected
    print("Object detected! Executing pick sequence...")
    
    -- Get current position
    local current_pos = get_encoder_position(encoder)
    print("Object at position:", current_pos)
    
    -- Calculate pick position (adjust X based on encoder position)
    local pick_x = 100 + current_pos * 0.1  -- Scale factor for demo
    
    -- Execute pick sequence
    move_to(robot, pick_x, 0, 50)   -- Move above
    move_to(robot, pick_x, 0, 0)    -- Pick
    move_to(robot, pick_x, 0, 50)   -- Lift
    
    -- Place sequence
    move_to(robot, 0, 100, 50)      -- Move to place
    move_to(robot, 0, 100, 0)       -- Place
    move_to(robot, 0, 100, 50)      -- Lift
    
    -- Reset encoder for next object
    send_command(encoder, "M317 R")
    wait_response()
    
    picked_count = picked_count + 1
    print("Picked object", picked_count, "of", target_count)
end

-- Cleanup
print("Disabling position tracking...")
send_command(encoder, "M317")  -- Disable auto reporting
wait_response()

-- Return to home
print("Returning to home position...")
home_robot(robot)

print("Process completed successfully!") 