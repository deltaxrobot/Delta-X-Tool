-- Generated movement script
local robot = get_device('Robot 1')
if not robot then
    print('Error: Robot not found!')
    return
end

robot:set_speed(1000)

-- Home robot
print('Homing robot...')
robot:home()

-- Draw circle
local center_x = 8.0
local center_y = -10.0
local radius = 156.0833110873805

for angle = 0, 360, 10 do
    local rad = math.rad(angle)
    local x = center_x + radius * math.cos(rad)
    local y = center_y + radius * math.sin(rad)
    robot:move_to(x, y, -850.0)
end
-- Move to start point
robot:move_to(-400.0, 400.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 400.0, -850.0)
-- Move to start point
robot:move_to(400.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 350.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 350.0, -850.0)
-- Move to start point
robot:move_to(350.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(350.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 300.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 300.0, -850.0)
-- Move to start point
robot:move_to(300.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(300.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 250.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 250.0, -850.0)
-- Move to start point
robot:move_to(250.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(250.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 200.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 200.0, -850.0)
-- Move to start point
robot:move_to(200.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(200.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 150.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 150.0, -850.0)
-- Move to start point
robot:move_to(150.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(150.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 100.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 100.0, -850.0)
-- Move to start point
robot:move_to(100.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(100.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 50.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 50.0, -850.0)
-- Move to start point
robot:move_to(50.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(50.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, 0.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, 0.0, -850.0)
-- Move to start point
robot:move_to(0.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(0.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -50.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -50.0, -850.0)
-- Move to start point
robot:move_to(-50.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-50.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -100.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -100.0, -850.0)
-- Move to start point
robot:move_to(-100.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-100.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -150.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -150.0, -850.0)
-- Move to start point
robot:move_to(-150.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-150.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -200.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -200.0, -850.0)
-- Move to start point
robot:move_to(-200.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-200.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -250.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -250.0, -850.0)
-- Move to start point
robot:move_to(-250.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-250.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -300.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -300.0, -850.0)
-- Move to start point
robot:move_to(-300.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-300.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -350.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -350.0, -850.0)
-- Move to start point
robot:move_to(-350.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-350.0, 400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(400.0, -400.0, -850.0)
-- Move to start point
robot:move_to(-400.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(-400.0, 400.0, -850.0)
-- Move to start point
robot:move_to(0.0, -400.0, -850.0)
-- Draw line to end point
robot:move_to(0.0, 400.0, -850.0)

print('Movement completed!')