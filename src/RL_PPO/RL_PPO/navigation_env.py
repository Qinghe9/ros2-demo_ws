"""Navigation Environment for PPO Training with ROS 2/Gazebo Integration."""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
import threading
import time
import math


def euler_from_quaternion(quaternion):
    """
    Convert quaternion to euler angles (roll, pitch, yaw).
    Custom implementation to avoid tf_transformations dependency issues.
    """
    x, y, z, w = quaternion
    
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)
    
    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    return roll, pitch, yaw


class NavigationEnv(gym.Env):
    """ROS 2 Navigation environment for PPO training using real Gazebo world."""
    
    def __init__(self, max_steps=500, map_size=10.0, use_real_ros=False):
        super().__init__()
        
        self.max_steps = max_steps
        self.map_size = map_size
        self.current_step = 0
        self.use_real_ros = use_real_ros
        
        # State: [robot_x, robot_y, robot_yaw, goal_x, goal_y, 8 laser ranges]
        self.state_dim = 3 + 2 + 8  # 13 dimensions
        
        # Action: 8 discrete directions (0-7, representing 8 angles)
        self.action_dim = 8
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.state_dim,),
            dtype=np.float32
        )
        
        self.action_space = spaces.Discrete(self.action_dim)
        
        # Robot state
        self.robot_pos = np.array([0.0, 0.0])
        self.robot_yaw = 0.0
        self.goal_pos = np.array([5.0, 5.0])
        self.laser_ranges = np.ones(8) * 10.0
        
        # ROS 2 integration
        if self.use_real_ros:
            self.ros_node = None
            self.cmd_vel_pub = None
            self.odom_sub = None
            self.scan_sub = None
            self.ros_thread = None
            self._init_ros()
    
    def _init_ros(self):
        """Initialize ROS 2 node and subscribers."""
        if not rclpy.ok():
            rclpy.init()
        
        self.ros_node = Node('ppo_nav_env')
        
        # Publishers
        self.cmd_vel_pub = self.ros_node.create_publisher(Twist, '/cmd_vel', 10)
        
        # Subscribers
        self.odom_sub = self.ros_node.create_subscription(
            Odometry, '/odom', self._odom_callback, 10
        )
        self.scan_sub = self.ros_node.create_subscription(
            LaserScan, '/scan', self._scan_callback, 10
        )
        
        # Data flags
        self.odom_received = False
        self.scan_received = False
        
        # Start ROS spin thread
        self.ros_thread = threading.Thread(target=self._ros_spin)
        self.ros_thread.daemon = True
        self.ros_thread.start()
        
        # Wait for sensor data
        self.ros_node.get_logger().info('Waiting for sensor data...')
        timeout = 10.0
        start_time = time.time()
        while not (self.odom_received and self.scan_received):
            if time.time() - start_time > timeout:
                self.ros_node.get_logger().warn('Timeout waiting for sensor data')
                break
            time.sleep(0.1)
        
        self.ros_node.get_logger().info('ROS 2 environment initialized')
    
    def _ros_spin(self):
        """ROS spin thread."""
        while rclpy.ok():
            rclpy.spin_once(self.ros_node, timeout_sec=0.1)
    
    def _odom_callback(self, msg):
        """Odometry callback."""
        self.robot_pos[0] = msg.pose.pose.position.x
        self.robot_pos[1] = msg.pose.pose.position.y
        
        # Convert quaternion to yaw using custom implementation
        orientation_q = msg.pose.pose.orientation
        orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
        (_, _, self.robot_yaw) = euler_from_quaternion(orientation_list)
        
        self.odom_received = True
    
    def _scan_callback(self, msg):
        """Laser scan callback - downsample to 8 beams."""
        ranges = np.array(msg.ranges)
        # Replace inf with max range
        ranges = np.where(np.isinf(ranges), msg.range_max, ranges)
        ranges = np.where(np.isnan(ranges), msg.range_max, ranges)
        
        # Downsample to 8 beams
        num_beams = len(ranges)
        indices = np.linspace(0, num_beams - 1, 8, dtype=int)
        self.laser_ranges = ranges[indices]
        
        self.scan_received = True
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.current_step = 0
        
        # Random initial position
        self.robot_pos = np.random.uniform(-self.map_size/2, self.map_size/2, size=2)
        self.robot_yaw = np.random.uniform(0, 2 * np.pi)
        
        # Random goal position (ensure it's far enough from robot)
        while True:
            self.goal_pos = np.random.uniform(-self.map_size/2, self.map_size/2, size=2)
            if np.linalg.norm(self.goal_pos - self.robot_pos) > 2.0:
                break
        
        # Reset laser ranges
        self.laser_ranges = np.ones(8) * 10.0
        
        return self._get_observation(), {}
    
    def step(self, action):
        self.current_step += 1
        
        if self.use_real_ros:
            # Real robot control via ROS 2
            action_angle = action * (2 * np.pi / self.action_dim)
            
            # Create velocity command
            cmd_vel = Twist()
            cmd_vel.linear.x = 0.3  # Constant forward speed
            cmd_vel.angular.z = action_angle - self.robot_yaw  # Turn to desired angle
            
            # Publish command
            self.cmd_vel_pub.publish(cmd_vel)
            
            # Wait for robot to move (simulate time step)
            time.sleep(0.1)
            
            # Stop robot
            cmd_vel.linear.x = 0.0
            cmd_vel.angular.z = 0.0
            self.cmd_vel_pub.publish(cmd_vel)
        else:
            # Simulation mode
            action_angle = action * (2 * np.pi / self.action_dim)
            
            # Move robot with smaller step size for finer control
            step_size = 0.3
            new_pos = self.robot_pos.copy()
            new_pos[0] += step_size * np.cos(action_angle)
            new_pos[1] += step_size * np.sin(action_angle)
            
            # Check bounds before moving
            if -self.map_size/2 <= new_pos[0] <= self.map_size/2 and \
               -self.map_size/2 <= new_pos[1] <= self.map_size/2:
                self.robot_pos = new_pos
                self.robot_yaw = action_angle
            else:
                # Hit wall - small penalty but don't terminate
                reward = -1.0
                truncated = False
                return self._get_observation(), reward, False, truncated, {}
            
            # Keep robot within map bounds
            self.robot_pos = np.clip(self.robot_pos, -self.map_size/2, self.map_size/2)
            
            # Update laser ranges (simulated)
            self._update_laser_ranges()
        
        # Calculate reward
        distance_to_goal = np.linalg.norm(self.goal_pos - self.robot_pos)
        
        # Initialize progress tracking if not exists
        if not hasattr(self, 'prev_distance') or self.prev_distance is None:
            self.prev_distance = distance_to_goal
        
        # Reward for getting closer to goal
        reward = -0.05  # Reduced step penalty
        
        # Progress reward: positive if getting closer, negative if moving away
        progress = self.prev_distance - distance_to_goal
        reward += progress * 2.0  # Reward for making progress
        
        self.prev_distance = distance_to_goal
        
        # Bonus for reaching goal
        if distance_to_goal < 0.5:
            reward += 100.0
            done = True
        else:
            done = False
        
        # Check for collision (simulated) - more lenient threshold
        min_laser = np.min(self.laser_ranges)
        if min_laser < 0.15:  # Reduced threshold for collision
            reward -= 5.0  # Reduced penalty
            done = True
        elif min_laser < 0.3:  # Warning zone
            reward -= 0.3 * (0.3 - min_laser)  # Gradual penalty
        
        # Check max steps
        if self.current_step >= self.max_steps:
            done = True
        
        truncated = False
        
        return self._get_observation(), reward, done, truncated, {}
    
    def _get_observation(self):
        """Get current observation."""
        obs = np.concatenate([
            self.robot_pos,
            [self.robot_yaw],
            self.goal_pos,
            self.laser_ranges
        ])
        return obs.astype(np.float32)
    
    def _update_laser_ranges(self):
        """Simulate laser scan readings."""
        # Simple simulation: laser ranges depend on distance to goal and walls
        for i in range(8):
            angle = i * (2 * np.pi / 8)
            # Distance to goal in this direction
            dx = self.goal_pos[0] - self.robot_pos[0]
            dy = self.goal_pos[1] - self.robot_pos[1]
            goal_dist = np.sqrt(dx**2 + dy**2)
            
            # Distance to walls
            wall_dist = self.map_size / 2 - np.abs(self.robot_pos[0] * np.cos(angle) + 
                                                     self.robot_pos[1] * np.sin(angle))
            
            self.laser_ranges[i] = min(goal_dist, wall_dist, 10.0)
    
    def get_state_dim(self):
        """Get state dimension."""
        return self.state_dim
    
    def render(self):
        """Render the environment (not implemented)."""
        pass
    
    def close(self):
        """Close the environment."""
        if self.use_real_ros and self.ros_node is not None:
            self.ros_node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()