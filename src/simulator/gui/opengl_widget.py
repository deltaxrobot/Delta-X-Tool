from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtOpenGL import *
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import numpy as np
import math
import time

class DeltaRobotWidget(QGLWidget):
    position_changed = pyqtSignal(float, float, float)  # Signal for position updates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        
        # Camera parameters
        self.camera_distance = 1500  # Increased for better view
        self.camera_x = 0
        self.camera_y = 0
        self.camera_rotation = [30, 45, 0]  # Better initial view angle
        
        # Robot geometric parameters (mm)
        self.base_radius = 150  # Radius of fixed base platform
        self.end_radius = 75    # Radius of moving end effector platform
        self.upper_arm = 250    # Length of upper arms (parallel with base)
        self.lower_arm = 500    # Length of lower arms (parallelogram links)
        self.base_height = 20   # Height of base platform
        self.end_height = 10    # Height of end effector platform
        
        # Current position and movement
        self.current_position = [0, 0, -500]  # Adjusted initial Z position
        self.target_position = [0, 0, -500]
        self.movement_start_time = 0
        self.movement_duration = 0
        self.is_moving = False
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_movement)
        self.animation_timer.start(16)  # ~60 FPS
        
        # Mouse tracking for rotation
        self.last_pos = None
        self.setMouseTracking(True)

    def draw_cylinder(self, radius, height, slices=32):
        """Draw a cylinder with given radius and height."""
        quad = gluNewQuadric()
        gluCylinder(quad, radius, radius, height, slices, 1)
        
        # Draw top and bottom circles
        glPushMatrix()
        glRotatef(180, 1, 0, 0)
        gluDisk(quad, 0, radius, slices, 1)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0, height)
        gluDisk(quad, 0, radius, slices, 1)
        glPopMatrix()

    def draw_arm(self, length, radius=5):
        """Draw a single arm segment."""
        self.draw_cylinder(radius, length)

    def draw_joint(self, radius=8):
        """Draw a spherical joint."""
        quad = gluNewQuadric()
        gluSphere(quad, radius, 16, 16)

    def draw_base_platform(self):
        """Draw the fixed base platform."""
        glColor3f(0.7, 0.7, 0.7)  # Gray color
        self.draw_cylinder(self.base_radius, self.base_height)
        
        # Draw mounting points for upper arms
        glColor3f(0.4, 0.4, 0.4)  # Darker gray for joints
        for i in range(3):
            angle = i * 120
            x = self.base_radius * math.cos(math.radians(angle))
            y = self.base_radius * math.sin(math.radians(angle))
            
            glPushMatrix()
            glTranslatef(x, y, 0)
            self.draw_joint()
            glPopMatrix()

    def draw_end_effector(self):
        """Draw the moving end effector platform."""
        glColor3f(0.5, 0.5, 1.0)  # Blue color
        self.draw_cylinder(self.end_radius, self.end_height)
        
        # Draw mounting points for lower arms
        glColor3f(0.3, 0.3, 0.8)  # Darker blue for joints
        for i in range(3):
            angle = i * 120
            x = self.end_radius * math.cos(math.radians(angle))
            y = self.end_radius * math.sin(math.radians(angle))
            
            glPushMatrix()
            glTranslatef(x, y, 0)
            self.draw_joint()
            glPopMatrix()

    def draw_parallelogram_arm(self, base_pos, end_pos):
        """Draw a complete arm assembly with parallel linkage structure."""
        # Calculate vectors and angles
        dx = end_pos[0] - base_pos[0]
        dy = end_pos[1] - base_pos[1]
        dz = end_pos[2] - base_pos[2]
        
        # Calculate horizontal angle for upper arm
        angle_z = math.degrees(math.atan2(dy, dx))
        
        # Calculate horizontal distance
        horizontal_dist = math.sqrt(dx*dx + dy*dy)
        
        # Calculate vertical angle for lower arms (negative because Z points downward in OpenGL)
        angle_y = -math.degrees(math.atan2(-dz, horizontal_dist))
        
        # Constants for parallel structure
        parallel_offset = 20  # Distance between parallel arms
        
        # Save original matrix state
        glPushMatrix()
        
        # Move to the base position and draw base joint
        glTranslatef(base_pos[0], base_pos[1], base_pos[2])
        glColor3f(0.4, 0.4, 0.4)
        self.draw_joint(10)
        
        # Save the base matrix for later use
        base_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        
        # Rotate to align with the arm direction (around Z axis)
        glRotatef(angle_z, 0, 0, 1)
        
        # Draw upper arm (fixed to the base)
        glColor3f(1.0, 0.6, 0.0)
        self.draw_arm(self.upper_arm, 8)
        
        # Move to the end of upper arm (elbow position)
        glTranslatef(self.upper_arm, 0, 0)
        
        # Draw elbow joint
        glColor3f(0.4, 0.4, 0.4)
        self.draw_joint(10)
        
        # Save the elbow matrix for later use
        elbow_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        elbow_pos = [elbow_matrix[3][0], elbow_matrix[3][1], elbow_matrix[3][2]]
        
        # Draw first lower arm
        glPushMatrix()
        # Apply rotation for the lower arm (around Y axis)
        glRotatef(angle_y, 0, 1, 0)
        
        # Draw the lower arm
        glColor3f(0.8, 0.5, 0.0)
        self.draw_arm(self.lower_arm, 7)
        
        # Move to the end of the lower arm
        glTranslatef(self.lower_arm, 0, 0)
        
        # Draw end joint
        glColor3f(0.4, 0.4, 0.4)
        self.draw_joint(10)
        
        # Save the end position of the first lower arm
        end_lower_first = glGetFloatv(GL_MODELVIEW_MATRIX)
        end_pos_first = [end_lower_first[3][0], end_lower_first[3][1], end_lower_first[3][2]]
        glPopMatrix()
        
        # Draw the vertical connector at the elbow
        glPushMatrix()
        # Draw a vertical rod (along Z axis)
        glRotatef(90, 1, 0, 0)
        glColor3f(0.9, 0.9, 0.0)  # Yellow
        self.draw_arm(parallel_offset, 4)
        glPopMatrix()
        
        # Draw second lower arm (offset by parallel_offset in Z direction)
        glPushMatrix()
        # Move up by the parallel offset
        glTranslatef(0, 0, parallel_offset)
        
        # Draw joint at the start of second lower arm
        glColor3f(0.4, 0.4, 0.4)
        self.draw_joint(10)
        
        # Apply same rotation as first lower arm
        glRotatef(angle_y, 0, 1, 0)
        
        # Draw the second lower arm
        glColor3f(0.8, 0.5, 0.0)
        self.draw_arm(self.lower_arm, 7)
        
        # Move to the end of the second lower arm
        glTranslatef(self.lower_arm, 0, 0)
        
        # Draw end joint
        glColor3f(0.4, 0.4, 0.4)
        self.draw_joint(10)
        
        # Save the end position of the second lower arm
        end_lower_second = glGetFloatv(GL_MODELVIEW_MATRIX)
        end_pos_second = [end_lower_second[3][0], end_lower_second[3][1], end_lower_second[3][2]]
        glPopMatrix()
        
        # Draw the connecting rod between the end points of the lower arms
        glPushMatrix()
        # Calculate the vector from first end to second end
        connector_vec = [
            end_pos_second[0] - end_pos_first[0],
            end_pos_second[1] - end_pos_first[1],
            end_pos_second[2] - end_pos_first[2]
        ]
        
        # Move to the end of the first lower arm
        glTranslatef(
            end_pos_first[0] - elbow_pos[0],
            end_pos_first[1] - elbow_pos[1],
            end_pos_first[2] - elbow_pos[2]
        )
        
        # Draw a vertical rod (along Z axis)
        glRotatef(90, 1, 0, 0)
        glColor3f(0.9, 0.9, 0.0)  # Yellow
        self.draw_arm(parallel_offset, 4)
        glPopMatrix()
        
        # Restore original matrix state
        glPopMatrix()

    def paintGL(self):
        """Render the OpenGL scene."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)  # Explicitly set matrix mode
        glLoadIdentity()
        
        # Set camera position
        glTranslatef(self.camera_x, self.camera_y, -self.camera_distance)
        glRotatef(self.camera_rotation[0], 1, 0, 0)
        glRotatef(self.camera_rotation[1], 0, 1, 0)
        glRotatef(self.camera_rotation[2], 0, 0, 1)
        
        # Draw coordinate system
        self.draw_coordinate_system()
        
        # Draw base platform
        glPushMatrix()
        self.draw_base_platform()
        glPopMatrix()
        
        # Draw end effector at current position
        glPushMatrix()
        glTranslatef(self.current_position[0], self.current_position[1], self.current_position[2])
        self.draw_end_effector()
        glPopMatrix()
        
        # Draw arms
        for i in range(3):
            angle = i * 120
            # Calculate base mounting point
            base_x = self.base_radius * math.cos(math.radians(angle))
            base_y = self.base_radius * math.sin(math.radians(angle))
            base_z = self.base_height
            
            # Calculate end effector mounting point
            end_x = self.current_position[0] + self.end_radius * math.cos(math.radians(angle))
            end_y = self.current_position[1] + self.end_radius * math.sin(math.radians(angle))
            end_z = self.current_position[2]
            
            # Draw complete arm assembly
            self.draw_parallelogram_arm(
                [base_x, base_y, base_z],
                [end_x, end_y, end_z]
            )

    def draw_coordinate_system(self):
        """Draw XYZ coordinate axes."""
        glLineWidth(2.0)
        glBegin(GL_LINES)
        # X axis (red)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(100, 0, 0)
        # Y axis (green)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 100, 0)
        # Z axis (blue)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 100)
        glEnd()
        glLineWidth(1.0)

    def initializeGL(self):
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)  # Add normalization for better lighting
        
        # Set up light
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])  # Increased ambient light
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 1.0, 4000.0)  # Adjusted near and far planes

    def start_movement(self, x: float, y: float, z: float, duration: float):
        """Start a movement to a new position."""
        self.target_position = [x, y, z]
        self.movement_start_time = time.time()
        self.movement_duration = duration
        self.is_moving = True

    def stop_movement(self):
        """Stop the current movement."""
        self.current_position = self.target_position.copy()
        self.is_moving = False
        self.updateGL()

    def update_movement(self):
        """Update movement animation."""
        if not self.is_moving:
            return
            
        current_time = time.time()
        elapsed = current_time - self.movement_start_time
        
        if elapsed >= self.movement_duration:
            self.stop_movement()
            return
            
        # Calculate interpolated position
        t = elapsed / self.movement_duration
        self.current_position = [
            self.current_position[0] + (self.target_position[0] - self.current_position[0]) * t,
            self.current_position[1] + (self.target_position[1] - self.current_position[1]) * t,
            self.current_position[2] + (self.target_position[2] - self.current_position[2]) * t
        ]
        
        self.updateGL()

    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_pos is None:
            self.last_pos = event.pos()
            return
            
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()
        
        if event.buttons() & Qt.LeftButton:
            self.camera_rotation[0] += dy * 0.5
            self.camera_rotation[1] += dx * 0.5
            self.camera_rotation[0] = min(max(self.camera_rotation[0], -90), 90)
            self.updateGL()
            
        self.last_pos = event.pos()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.camera_distance -= delta * 0.1
        self.camera_distance = min(max(self.camera_distance, 100), 2000)
        self.updateGL()

    def set_position(self, x, y, z):
        """Update the robot's current position."""
        self.current_position = [x, y, z]
        self.updateGL()
        self.position_changed.emit(x, y, z) 