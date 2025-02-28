import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# Kích thước Robot Delta
base_radius = 10
effector_radius = 3
arm_length = 15

# Các góc đặt cánh tay
angles = np.array([0, 120, 240])

# Hàm tính toán điểm base (trên cùng)
def get_base_points():
    rad = np.radians(angles)
    x = base_radius * np.cos(rad)
    y = base_radius * np.sin(rad)
    z = np.zeros(3)
    return np.vstack([x, y, z]).T

# Hàm tính toán điểm effector (bên dưới)
def get_effector_points(xc, yc, zc):
    rad = np.radians(angles)
    x = xc + effector_radius * np.cos(rad)
    y = yc + effector_radius * np.sin(rad)
    z = np.array([zc, zc, zc])
    return np.vstack([x, y, z]).T

# Hàm vẽ robot Delta hoàn chỉnh
def draw_robot(ax, effector_pos):
    ax.clear()
    ax.set_xlim(-25, 25)
    ax.set_ylim(-25, 25)
    ax.set_zlim(-30, 10)
    ax.grid(True)
    ax.set_box_aspect([1,1,1])

    base_pts = get_base_points()
    effector_pts = get_effector_points(*effector_pos)

    # Vẽ tam giác base trên cùng
    base_cycle = np.vstack([base_pts, base_pts[0]])
    ax.plot(base_cycle[:,0], base_cycle[:,1], base_cycle[:,2], 'k-', linewidth=2)

    # Vẽ tam giác effector bên dưới
    eff_cycle = np.vstack([effector_pts, effector_pts[0]])
    ax.plot(eff_cycle[:,0], eff_cycle[:,1], eff_cycle[:,2], 'r-', linewidth=2)

    # Tính và vẽ các tay robot
    for b, e in zip(base_pts, effector_pts):
        # Trung điểm của mỗi tay (đơn giản hóa tay đòn chỉ là một đoạn thẳng)
        mid_point = (b + e) / 2
        # Kiểm tra độ dài tay có phù hợp không, nếu không thì điều chỉnh lại Z
        current_length = np.linalg.norm(e - b)
        if current_length > arm_length * 2:
            print("Điểm nằm ngoài tầm với của robot!")
            return
        vertical_drop = np.sqrt(arm_length**2 - (current_length / 2)**2)
        mid_point[2] -= vertical_drop  # điểm giữa cánh tay hạ xuống dưới

        # Vẽ đoạn từ base xuống mid_point và từ mid_point xuống effector
        ax.plot([b[0], mid_point[0]], [b[1], mid_point[1]], [b[2], mid_point[2]], 'b-', linewidth=1.5)
        ax.plot([mid_point[0], e[0]], [mid_point[1], e[1]], [mid_point[2], e[2]], 'g-', linewidth=1.5)

    # Đánh dấu effector
    ax.scatter(*effector_pos, color='magenta', s=100)

    ax.set_title("3D Delta Robot Simulation")

# Quỹ đạo mẫu: chuyển động vòng tròn
t = np.linspace(0, 2*np.pi, 100)
traj_x = 5 * np.cos(t)
traj_y = 5 * np.sin(t)
traj_z = -15 + 3 * np.sin(2*t)

fig = plt.figure(figsize=(9, 9))
ax = fig.add_subplot(111, projection='3d')

def animate(i):
    effector_pos = (traj_x[i], traj_y[i], traj_z[i])
    draw_robot(ax, effector_pos)

ani = FuncAnimation(fig, animate, frames=len(t), interval=50, repeat=True)

plt.show()
