from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.logging import get_logger
import time

def main():
    rclpy.init()
    logger = get_logger('bt_navigator_node')
    navigator = BasicNavigator()
    
    # 等待 Nav2 激活
    navigator.waitUntilNav2Active()
    logger.info("Nav2 已激活")
    
    # 设置初始位姿（如果需要）
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.position.z = 0.0
    initial_pose.pose.orientation.x = 0.0
    initial_pose.pose.orientation.y = 0.0
    initial_pose.pose.orientation.z = 0.0
    initial_pose.pose.orientation.w = 1.0
    navigator.setInitialPose(initial_pose)
    logger.info("初始位姿已设置")
    
    # 等待 Nav2 再次激活（设置初始位姿后需要）
    navigator.waitUntilNav2Active()
    
    # 示例：设置目标点导航
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose.pose.position.x = 1.0  # 修改为你的目标 X
    goal_pose.pose.position.y = 1.0  # 修改为你的目标 Y
    goal_pose.pose.position.z = 0.0
    goal_pose.pose.orientation.w = 1.0
    
    logger.info("开始导航到目标点 [x:1.0, y:1.0]")
    navigator.goToPose(goal_pose)
    
    # 等待导航完成
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            logger.info(f"导航中... 距离目标: {feedback.distance_remaining:.2f}m")
        time.sleep(0.5)
    
    # 检查结果
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        logger.info("导航成功!")
    elif result == TaskResult.FAILED:
        logger.info("导航失败!")
    elif result == TaskResult.CANCELLED:
        logger.info("导航已取消!")
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
