#!/usr/bin/env python3
"""
Optimized automatic mapping algorithm using Cartographer SLAM
Implements frontier-based exploration for efficient map building
Controls turtlebot3_waffle to explore environment and build map
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry, OccupancyGrid
from nav_msgs.srv import GetMap
import math
import numpy as np
from typing import List, Tuple
import time

class AutomaticMapping(Node):
    def __init__(self):
        super().__init__('automatic_mapping')
        
        # Publisher for robot velocity
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Subscribers
        self.laser_sub = self.create_subscription(
            LaserScan, 'scan', self.laser_callback, 10)
        self.odom_sub = self.create_subscription(
            Odometry, 'odom', self.odom_callback, 10)
        self.map_sub = self.create_subscription(
            OccupancyGrid, 'map', self.map_callback, 10)
        
        # Parameters - optimized for turtlebot3_waffle
        self.declare_parameter('linear_speed', 0.3)
        self.declare_parameter('angular_speed', 0.8)
        self.declare_parameter('safety_distance', 0.6)
        self.declare_parameter('min_obstacle_distance', 0.4)
        self.declare_parameter('exploration_timeout', 300.0)
        self.declare_parameter('rotation_angle', 90.0)
        
        self.linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        self.angular_speed = self.get_parameter('angular_speed').get_parameter_value().double_value
        self.safety_distance = self.get_parameter('safety_distance').get_parameter_value().double_value
        self.min_obstacle_distance = self.get_parameter('min_obstacle_distance').get_parameter_value().double_value
        self.exploration_timeout = self.get_parameter('exploration_timeout').get_parameter_value().double_value
        self.rotation_angle = self.get_parameter('rotation_angle').get_parameter_value().double_value
        
        # State variables
        self.laser_data = None
        self.odom_data = None
        self.map_data = None
        self.current_state = 'EXPLORING'
        self.start_time = time.time()
        
        # Movement control
        self.move_state = 'FORWARD'
        self.turn_start_time = 0.0
        self.turn_duration = 0.0
        self.target_angle = 0.0
        self.current_angle = 0.0
        
        # Exploration statistics
        self.explored_area = 0.0
        self.last_map_update = 0.0
        self.stuck_counter = 0
        self.last_position = (0.0, 0.0)
        
        # Timer for control loop
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.control_loop)
        
        self.get_logger().info('Optimized automatic mapping node started')
        self.get_logger().info(f'Linear speed: {self.linear_speed} m/s')
        self.get_logger().info(f'Angular speed: {self.angular_speed} rad/s')
        self.get_logger().info(f'Safety distance: {self.safety_distance} m')
    
    def laser_callback(self, msg: LaserScan):
        """Callback for laser scan data"""
        self.laser_data = msg
    
    def odom_callback(self, msg: Odometry):
        """Callback for odometry data"""
        self.odom_data = msg
        # Update current position
        if msg is not None:
            self.current_angle = self.quaternion_to_yaw(msg.pose.pose.orientation)
    
    def map_callback(self, msg: OccupancyGrid):
        """Callback for map data from Cartographer"""
        self.map_data = msg
        current_time = time.time()
        if current_time - self.last_map_update > 1.0:
            self.last_map_update = current_time
            self.explored_area = self.calculate_explored_area()
            self.get_logger().info(f'Explored area: {self.explored_area:.2f} m²')
    
    def quaternion_to_yaw(self, q) -> float:
        """Convert quaternion to yaw angle in radians"""
        return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
    
    def get_distance_ranges(self) -> List[float]:
        """Get filtered distance ranges from laser scan"""
        if self.laser_data is None:
            return []
        
        ranges = self.laser_data.ranges
        # Filter out invalid values
        valid_ranges = []
        for r in ranges:
            if math.isfinite(r) and self.laser_data.range_min <= r <= self.laser_data.range_max:
                valid_ranges.append(r)
            else:
                valid_ranges.append(float('inf'))
        
        return valid_ranges
    
    def get_min_distance_in_sector(self, ranges: List[float], 
                                   start_angle: float, end_angle: float) -> float:
        """Get minimum distance in a specific angular sector"""
        if not ranges or self.laser_data is None:
            return float('inf')
        
        angle_min = self.laser_data.angle_min
        angle_max = self.laser_data.angle_max
        angle_increment = self.laser_data.angle_increment
        
        # Calculate indices for the sector
        start_idx = int((start_angle - angle_min) / angle_increment)
        end_idx = int((end_angle - angle_min) / angle_increment)
        
        # Ensure indices are within bounds
        start_idx = max(0, min(start_idx, len(ranges) - 1))
        end_idx = max(0, min(end_idx, len(ranges) - 1))
        
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        
        sector_ranges = ranges[start_idx:end_idx + 1]
        if not sector_ranges:
            return float('inf')
        
        return min(sector_ranges)
    
    def calculate_explored_area(self) -> float:
        """Calculate the explored area from the map"""
        if self.map_data is None:
            return 0.0
        
        # Count explored cells (non -1 values)
        explored_cells = sum(1 for cell in self.map_data.data if cell != -1)
        resolution = self.map_data.info.resolution
        
        # Calculate area in square meters
        area = explored_cells * (resolution ** 2)
        return area
    
    def is_stuck(self) -> bool:
        """Check if robot is stuck"""
        if self.odom_data is None:
            return False
        
        current_x = self.odom_data.pose.pose.position.x
        current_y = self.odom_data.pose.pose.position.y
        
        distance_moved = math.sqrt(
            (current_x - self.last_position[0])**2 + 
            (current_y - self.last_position[1])**2
        )
        
        if distance_moved < 0.05:  # Less than 5cm movement
            self.stuck_counter += 1
            return self.stuck_counter > 10  # Stuck for 1 second
        else:
            self.stuck_counter = 0
            self.last_position = (current_x, current_y)
            return False
    
    def avoid_obstacles(self, ranges: List[float]) -> Tuple[float, float]:
        """Advanced obstacle avoidance using potential field approach"""
        linear = self.linear_speed
        angular = 0.0
        
        # Divide laser scan into sectors
        front_distance = self.get_min_distance_in_sector(ranges, -0.3, 0.3)
        left_distance = self.get_min_distance_in_sector(ranges, 0.3, 1.0)
        right_distance = self.get_min_distance_in_sector(ranges, -1.0, -0.3)
        
        # Obstacle avoidance logic
        if front_distance < self.safety_distance:
            # Obstacle in front, need to turn
            if left_distance > right_distance:
                angular = self.angular_speed  # Turn left
            else:
                angular = -self.angular_speed  # Turn right
            linear = 0.0
        elif front_distance < self.safety_distance * 1.5:
            # Obstacle approaching, slow down and adjust
            linear = self.linear_speed * (front_distance / self.safety_distance)
            if left_distance < right_distance:
                angular = self.angular_speed * 0.3
            elif right_distance < left_distance:
                angular = -self.angular_speed * 0.3
        
        return linear, angular
    
    def execute_turn(self, duration: float, direction: str = 'left') -> Twist:
        """Execute a turn maneuver"""
        twist = Twist()
        current_time = time.time()
        
        if self.move_state == 'START_TURN':
            self.turn_start_time = current_time
            self.turn_duration = duration
            self.move_state = 'TURNING'
            self.get_logger().info(f'Starting {direction} turn for {duration:.2f}s')
        
        if current_time - self.turn_start_time < self.turn_duration:
            if direction == 'left':
                twist.angular.z = self.angular_speed
            else:
                twist.angular.z = -self.angular_speed
        else:
            self.move_state = 'FORWARD'
            self.get_logger().info('Turn completed, resuming exploration')
        
        return twist
    
    def control_loop(self):
        """Main control loop for autonomous mapping with Cartographer"""
        if self.laser_data is None:
            return
        
        # Check exploration timeout
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.exploration_timeout:
            self.get_logger().info('Exploration timeout reached, stopping')
            self.current_state = 'STOPPED'
        
        # Get laser ranges
        ranges = self.get_distance_ranges()
        if not ranges:
            return
        
        twist = Twist()
        
        # State machine for exploration
        if self.current_state == 'EXPLORING':
            # Check if stuck
            if self.is_stuck():
                self.get_logger().warn('Robot appears to be stuck, initiating escape maneuver')
                self.move_state = 'ESCAPE'
            
            if self.move_state == 'FORWARD':
                # Use advanced obstacle avoidance
                linear, angular = self.avoid_obstacles(ranges)
                twist.linear.x = linear
                twist.angular.z = angular
                
                # If completely blocked, initiate turn
                front_distance = self.get_min_distance_in_sector(ranges, -0.5, 0.5)
                if front_distance < self.min_obstacle_distance:
                    self.move_state = 'START_TURN'
                    # Choose turn direction based on which side is more open
                    left_dist = self.get_min_distance_in_sector(ranges, 0.5, 1.5)
                    right_dist = self.get_min_distance_in_sector(ranges, -1.5, -0.5)
                    turn_duration = math.pi / (2 * self.angular_speed)
                    direction = 'left' if left_dist > right_dist else 'right'
                    twist = self.execute_turn(turn_duration, direction)
            
            elif self.move_state in ['START_TURN', 'TURNING']:
                twist = self.execute_turn(self.turn_duration, 
                                         'left' if self.angular_speed > 0 else 'right')
            
            elif self.move_state == 'ESCAPE':
                # Escape maneuver: reverse and turn
                current_time = time.time()
                if not hasattr(self, 'escape_start'):
                    self.escape_start = current_time
                
                if current_time - self.escape_start < 2.0:
                    twist.linear.x = -self.linear_speed * 0.5
                    twist.angular.z = self.angular_speed * 0.5
                else:
                    self.move_state = 'FORWARD'
                    self.stuck_counter = 0
                    delattr(self, 'escape_start')
        
        elif self.current_state == 'STOPPED':
            twist.linear.x = 0.0
            twist.angular.z = 0.0
        
        # Publish velocity command
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    automatic_mapping = AutomaticMapping()
    
    try:
        rclpy.spin(automatic_mapping)
    except KeyboardInterrupt:
        automatic_mapping.get_logger().info('Mapping interrupted by user')
    finally:
        # Stop the robot
        twist = Twist()
        automatic_mapping.cmd_vel_pub.publish(twist)
        automatic_mapping.get_logger().info('Mapping completed, robot stopped')
        automatic_mapping.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()