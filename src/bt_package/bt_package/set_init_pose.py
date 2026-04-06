from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy
from rclpy.logging import get_logger

def main():
    rclpy.init()
    logger = get_logger('init_pose_node')
    navigator = BasicNavigator()

    # 设置初始位姿
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0
    navigator.setInitialPose(initial_pose)
    logger.info("初始位姿已设置: [x:0.0, y:0.0, yaw:0.0]")

    # 等待Nav2激活
    navigator.waitUntilNav2Active()
    logger.info("Nav2已激活，初始位姿设置完成")

    rclpy.spin(navigator)
    rclpy.shutdown()

if __name__ == '__main__':
    main()