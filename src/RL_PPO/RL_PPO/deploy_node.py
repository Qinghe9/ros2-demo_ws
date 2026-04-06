"""Deployment Node for PPO Navigation."""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformListener, Buffer
import numpy as np
import os
from ament_index_python.packages import get_package_share_directory

from RL_PPO.ppo_agent import PPOAgent


class PPONavigationNode(Node):
    """PPO Navigation Deployment Node."""
    
    def __init__(self):
        super().__init__('ppo_navigation_node')
        
        self.declare_parameters(
            namespace='',
            parameters=[
                ('model_path', ''),
                ('max_linear_vel', 0.5),
                ('max_angular_vel', 1.0),
                ('goal_tolerance', 0.5),
            ]
        )
        
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value
        self.goal_tolerance = self.get_parameter('goal_tolerance').value
        
        self.cmd_pub = self.create_publisher(
            Twist, 
            '/cmd_vel', 
            10
        )
        
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        self.laser_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            10
        )
        
        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_callback,
            10
        )
        
        self.robot_pos = np.array([0.0, 0.0])
        self.robot_yaw = 0.0
        self.goal_pos = np.array([1.0, 1.0])
        self.laser_ranges = np.ones(8) * 10.0
        
        self.agent = self._load_model()
        
        self.timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('PPO Navigation Node initialized')
        
    def _load_model(self):
        model_path = self.get_parameter('model_path').value
        if not model_path:
            pkg_share = get_package_share_directory('RL_PPO')
            model_path = os.path.join(pkg_share, 'models', 'ppo_model_final.pt')
        
        agent = PPOAgent(state_dim=12, action_dim=8)
        if os.path.exists(model_path):
            agent.load(model_path)
            self.get_logger().info(f'Model loaded from {model_path}')
        else:
            self.get_logger().warn(f'Model not found at {model_path}, using random policy')
        return agent
    
    def odom_callback(self, msg: Odometry):
        self.robot_pos = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y
        ])
        q = msg.pose.pose.orientation
        self.robot_yaw = np.arctan2(2.0 * (q.w * q.z + q.x * q.y),
                                     1.0 - 2.0 * (q.y**2 + q.z**2))
    
    def laser_callback(self, msg: LaserScan):
        ranges = np.array(msg.ranges)
        ranges = np.nan_to_num(ranges, nan=10.0, posinf=10.0, neginf=0.0)
        
        step = len(ranges) // 8
        for i in range(8):
            start = i * step
            end = (i + 1) * step
            self.laser_ranges[i] = np.min(ranges[start:end]) / 10.0
    
    def goal_callback(self, msg: PoseStamped):
        self.goal_pos = np.array([
            msg.pose.position.x,
            msg.pose.position.y
        ])
        self.get_logger().info(f'New goal received: {self.goal_pos}')
    
    def _get_observation(self):
        goal_vec = self.goal_pos - self.robot_pos
        distance = np.linalg.norm(goal_vec)
        if distance > 1e-6:
            goal_vec = goal_vec / distance
        else:
            goal_vec = np.array([0.0, 0.0])
        
        goal_angle = np.arctan2(goal_vec[1], goal_vec[0])
        relative_angle = goal_angle - self.robot_yaw
        relative_angle = np.arctan2(np.sin(relative_angle), np.cos(relative_angle))
        
        obs = np.concatenate([
            goal_vec,
            [self.robot_pos[0] / 10.0, self.robot_pos[1] / 10.0],
            self.laser_ranges
        ])
        
        return obs.astype(np.float32)
    
    def control_loop(self):
        distance = np.linalg.norm(self.goal_pos - self.robot_pos)
        
        if distance < self.goal_tolerance:
            twist = Twist()
            self.cmd_pub.publish(twist)
            return
        
        obs = self._get_observation()
        action = self.agent.select_action(obs, deterministic=True)
        
        action_angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
        target_angle = action_angles[action]
        
        current_heading = np.arctan2(
            self.goal_pos[1] - self.robot_pos[1],
            self.goal_pos[0] - self.robot_pos[0]
        )
        angle_diff = np.arctan2(np.sin(current_heading - self.robot_yaw),
                                 np.cos(current_heading - self.robot_yaw))
        
        twist = Twist()
        twist.linear.x = self.max_linear_vel * min(1.0, distance)
        twist.angular.z = np.clip(angle_diff, -self.max_angular_vel, self.max_angular_vel)
        
        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = PPONavigationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()