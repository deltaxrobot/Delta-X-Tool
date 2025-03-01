--[[
Script Name: pick_place.lua
Created: 2025-03-01 17:12:21
Description: Control script for DeltaX robot system
]]--

-- Get devices
local robot = get_device("Robot 1")
local conveyor = get_device("Conveyor 1")
local encoder = get_device("Encoder 1")

-- Check device connections
if not robot then
    print("Error: Robot not found!")
    return
end

-- Your code here
print("Script started...")

