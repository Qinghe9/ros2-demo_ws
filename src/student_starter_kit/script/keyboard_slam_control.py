#!/usrusr/bin/env python3
"""
Keyboard Control for SLAM Mapping
Manual control of turtlebot3 for precise map building
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import termios
import tty
import select
import os


class KeyboardSLAMControl(Node):
    def __init__(self):
        super().__init__('keyboard_slam_control')
        
        # Publisher for robot velocity
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Control parameters - slow and precise for SLAM
        self.linear_speed = 0.08   # Very slow linear speed (m/s)
        self.angular_speed = 0.3   # Slow angular speed (rad/s)
        self.boost_factor = 2.0    # Speed boost when holding Shift
        
        self.get_logger().info('Keyboard SLAM Control Started')
        self.get_logger().info('Controls:')
        self.get_logger().info('  w/s : Forward/Backward')
        self.get_logger().info('  a/d : Turn Left/Right')
        self.get_logger().info('  W/S/A/D : Fast movement (2x speed)')
        self.get_logger().info('  space : Stop')
        self.get_logger().info('  q : Quit')
        self.get_logger().info(f'Linear speed: {self.linear_speed} m/s')
        self.get_logger().info(f'Angular speed: {self.angular_speed} rad/s')
    
    def get_key(self):
        """Get a single keypress from stdin"""
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key
    
    def run(self):
        """Main control loop"""
        self.settings = termios.tcgetattr(sys.stdin)
        
        try:
            while True:
                key = self.get_key()
                
                twist = Twist()
                
                # Check for uppercase (boost mode)
                boost = key.isupper()
                speed_mult = self.boost_factor if boost else 1.0
                
                if key.lower() == 'w':
                    twist.linear.x = self.linear_speed * speed_mult
                elif key.lower() == 's':
                    twist.linear.x = -self.linear_speed * speed_mult
                elif key.lower() == 'a':
                    twist.angular.z = self.angular_speed * speed_mult
                elif key.lower() == 'd':
                    twist.angular.z = -self.angular_speed * speed_mult
                elif key == ' ':
                    # Stop
                    pass
                elif key == 'q':
                    self.get_logger().info('Quitting...')
                    break
                else:
                    # Unknown key, stop
                    pass
                
                self.cmd_vel_pub.publish(twist)
                self.get_logger().info(f'Cmd: linear={twist.linear.x:.2f}, angular={twist.angular.z:.2f}')
                
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
        finally:
            # Stop the robot
            twist = Twist()
            self.cmd_vel_pub.publish(twist)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardSLAMControl()
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()