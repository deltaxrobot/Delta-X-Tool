# Script Plugin Documentation

Script Plugin cho phép bạn viết các kịch bản điều khiển thiết bị bằng ngôn ngữ Lua. Plugin này cung cấp một môi trường lập trình đơn giản nhưng mạnh mẽ để tự động hóa các tác vụ.

## Giao diện

1. Script Editor:
   - Vùng soạn thảo code Lua
   - Hỗ trợ syntax highlighting
   - Các nút điều khiển:
     - Run: Chạy script
     - Stop: Dừng script đang chạy
     - Load: Tải script từ file
     - Save: Lưu script ra file

2. Output Console:
   - Hiển thị kết quả thực thi
   - Log các lệnh gửi và phản hồi
   - Thông báo lỗi (nếu có)

## Các hàm có sẵn

### Quản lý thiết bị

```lua
-- Lấy thiết bị theo tên
device = get_device("Robot 1")

-- Lấy tất cả thiết bị theo loại
robots = get_devices_by_type("robot")  -- Các loại: "robot", "conveyor", "encoder"
```

### Điều khiển thiết bị

```lua
-- Gửi lệnh trực tiếp
send_command(device, "G28")  -- Gửi G-code
wait_response()  -- Đợi phản hồi

-- Di chuyển robot
move_to(device, x, y, z[, speed])  -- speed là tùy chọn
home_robot(device)  -- Về home

-- Điều khiển conveyor
set_conveyor_speed(device, speed)  -- Đặt tốc độ
move_conveyor_to(device, position[, speed])  -- Di chuyển đến vị trí

-- Đọc encoder
position = get_encoder_position(device)
```

### Tiện ích

```lua
-- In ra console
print("Text", value1, value2, ...)

-- Tạm dừng
sleep(seconds)

-- Đợi điều kiện
wait_until(function()
    -- return true khi điều kiện thỏa mãn
    return condition
end[, timeout])
```

## Ví dụ

### 1. Di chuyển robot đơn giản

```lua
-- Lấy robot
robot = get_device("Robot 1")
if not robot then
    print("Không tìm thấy robot!")
    return
end

-- Home robot
home_robot(robot)

-- Di chuyển qua các điểm
move_to(robot, 100, 0, 50)    -- X=100, Y=0, Z=50
move_to(robot, 100, 100, 50)  -- X=100, Y=100, Z=50
move_to(robot, 0, 100, 50)    -- X=0, Y=100, Z=50
move_to(robot, 0, 0, 50)      -- X=0, Y=0, Z=50
```

### 2. Điều khiển robot và conveyor

```lua
-- Lấy thiết bị
robot = get_device("Robot 1")
conveyor = get_device("Conveyor 1")

-- Cấu hình conveyor
set_conveyor_speed(conveyor, 200)  -- 200mm/s

-- Vòng lặp xử lý
for i = 1, 5 do
    -- Di chuyển conveyor
    move_conveyor_to(conveyor, i * 100)  -- Di chuyển 100mm mỗi lần
    
    -- Di chuyển robot xuống pick
    move_to(robot, 100, 0, 0, 1000)
    
    -- Di chuyển robot lên
    move_to(robot, 100, 0, 50, 1000)
    
    print("Hoàn thành chu kỳ", i)
end
```

### 3. Đồng bộ robot với encoder

```lua
-- Lấy thiết bị
robot = get_device("Robot 1")
encoder = get_device("Encoder 1")

-- Đợi encoder đến vị trí
wait_until(function()
    position = get_encoder_position(encoder)
    return position >= 100  -- Đợi đến vị trí 100mm
end, 10)  -- Timeout sau 10 giây

-- Di chuyển robot
move_to(robot, 100, 0, 0)
```

## Lưu ý

1. Mỗi lệnh gửi đến thiết bị cần có `wait_response()` để đợi phản hồi
2. Sử dụng `print()` để debug script
3. Xử lý lỗi bằng cách kiểm tra thiết bị tồn tại trước khi sử dụng
4. Có thể dừng script bất cứ lúc nào bằng nút Stop
5. Lưu script thường xuyên để tránh mất dữ liệu

## Mở rộng

Bạn có thể tạo các hàm tiện ích của riêng mình để tái sử dụng:

```lua
-- Hàm di chuyển theo hình chữ nhật
function move_rectangle(robot, width, height, z)
    move_to(robot, 0, 0, z)
    move_to(robot, width, 0, z)
    move_to(robot, width, height, z)
    move_to(robot, 0, height, z)
    move_to(robot, 0, 0, z)
end

-- Sử dụng hàm
robot = get_device("Robot 1")
move_rectangle(robot, 100, 50, 30)
``` 