#!/usr/bin/env python3
"""
工业级三点巡航行为树节点实现
Industrial Patrol Behavior Tree Nodes
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool
from sensor_msgs.msg import LaserScan
import py_trees
import py_trees_ros
from py_trees.common import Status
import time


class NavigateToPoseAction(py_trees.behaviour.Behaviour):
    """导航到目标点位动作节点"""
    
    def __init__(self, name="NavigateToPose"):
        super().__init__(name)
        self.blackboard = self.attach_blackboard_client(name=name)
        self.blackboard.register_key("goal", access=py_trees.common.Access.READ)
        
    def setup(self, **kwargs):
        try:
            self.node = kwargs['node']
        except KeyError as e:
            error_message = "didn't find 'node' in setup's kwargs [{}][{}]".format(self.qualified_name)
            raise KeyError(error_message) from e
            
        self._action_client = ActionClient(
            self.node,
            NavigateToPose,
            'navigate_to_pose'
        )
        self._sent_goal = False
        self._goal_handle = None
        
        self.logger.info(f"[{self.name}] 导航动作客户端已创建")
        return True
        
    def initialise(self):
        self._sent_goal = False
        self._goal_handle = None
        self.logger.info(f"[{self.name}] 开始导航到目标点")
        
    def update(self):
        if not self._sent_goal:
            goal_pose = self.blackboard.goal
            
            if not self._action_client.wait_for_server(timeout_sec=1.0):
                self.logger.error(f"[{self.name}] 导航服务不可用")
                return Status.FAILURE
                
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = goal_pose
            
            self._send_goal_future = self._action_client.send_goal_async(
                goal_msg,
                feedback_callback=self._feedback_callback
            )
            self._sent_goal = True
            return Status.RUNNING
            
        if self._goal_handle is None:
            if self._send_goal_future.done():
                self._goal_handle = self._send_goal_future.result()
                if not self._goal_handle.accepted:
                    self.logger.error(f"[{self.name}] 导航目标被拒绝")
                    return Status.FAILURE
                self._get_result_future = self._goal_handle.get_result_async()
            return Status.RUNNING
            
        if self._get_result_future.done():
            result = self._get_result_future.result().result
            status = self._get_result_future.result().status
            
            if status == 4:  # SUCCEEDED
                self.logger.info(f"[{self.name}] 导航成功到达目标")
                return Status.SUCCESS
            else:
                self.logger.error(f"[{self.name}] 导航失败，状态码: {status}")
                return Status.FAILURE
                
        return Status.RUNNING
        
    def terminate(self, new_status):
        if self._goal_handle is not None and new_status == Status.INVALID:
            self._goal_handle.cancel_goal_async()
            
    def _feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        remaining = feedback.distance_remaining
        self.logger.debug(f"[{self.name}] 距离目标: {remaining:.2f}m")


class IsObstacleDetected(py_trees.behaviour.Behaviour):
    """障碍物检测条件节点"""
    
    def __init__(self, name="IsObstacleDetected", detection_range=0.5):
        super().__init__(name)
        self.detection_range = detection_range
        self.obstacle_detected = False
        
    def setup(self, **kwargs):
        try:
            self.node = kwargs['node']
        except KeyError as e:
            error_message = "didn't find 'node' in setup's kwargs [{}][{}]".format(self.qualified_name)
            raise KeyError(error_message) from e
            
        self._laser_sub = self.node.create_subscription(
            LaserScan,
            'scan',
            self._laser_callback,
            10
        )
        self.logger.info(f"[{self.name}] 障碍物检测节点已创建，检测距离: {detection_range}m")
        return True
        
    def _laser_callback(self, msg):
        # 检查前方是否有障碍物
        ranges = [r for r in msg.ranges if r > 0.1]  # 过滤无效值
        if ranges:
            min_distance = min(ranges)
            self.obstacle_detected = min_distance < self.detection_range
            
    def initialise(self):
        self.obstacle_detected = False
        
    def update(self):
        if self.obstacle_detected:
            self.logger.warn(f"[{self.name}] 检测到障碍物！")
            return Status.SUCCESS  # 检测到障碍物，返回成功以触发等待
        return Status.FAILURE  # 未检测到障碍物


class IsCancelRequested(py_trees.behaviour.Behaviour):
    """取消请求检测条件节点"""
    
    def __init__(self, name="IsCancelRequested"):
        super().__init__(name)
        self.cancel_requested = False
        
    def setup(self, **kwargs):
        try:
            self.node = kwargs['node']
        except KeyError as e:
            error_message = "didn't find 'node' in setup's kwargs [{}][{}]".format(self.qualified_name)
            raise KeyError(error_message) from e
            
        self._cancel_sub = self.node.create_subscription(
            Bool,
            '/patrol_cancel',
            self._cancel_callback,
            10
        )
        self.logger.info(f"[{self.name}] 取消检测节点已创建")
        return True
        
    def _cancel_callback(self, msg):
        self.cancel_requested = msg.data
        
    def initialise(self):
        self.cancel_requested = False
        
    def update(self):
        if self.cancel_requested:
            self.logger.warn(f"[{self.name}] 收到取消请求！")
            return Status.FAILURE  # 取消请求，返回失败
        return Status.SUCCESS  # 继续执行


class LogInfo(py_trees.behaviour.Behaviour):
    """INFO级别日志节点"""
    
    def __init__(self, name="LogInfo", message=""):
        super().__init__(name)
        self.message = message
        
    def update(self):
        # 解析Blackboard变量
        msg = self._parse_message(self.message)
        self.logger.info(msg)
        return Status.SUCCESS
        
    def _parse_message(self, message):
        """解析消息中的Blackboard变量"""
        # 简单实现，可以扩展为更复杂的解析
        return message


class LogWarn(LogInfo):
    """WARN级别日志节点"""
    
    def __init__(self, name="LogWarn", message=""):
        super().__init__(name, message)
        
    def update(self):
        msg = self._parse_message(self.message)
        self.logger.warn(msg)
        return Status.SUCCESS


class Wait(py_trees.behaviour.Behaviour):
    """等待动作节点"""
    
    def __init__(self, name="Wait", duration=1.0):
        super().__init__(name)
        self.duration = duration
        self.start_time = None
        
    def initialise(self):
        self.start_time = time.time()
        
    def update(self):
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            return Status.SUCCESS
        return Status.RUNNING


def create_tree():
    """创建行为树"""
    # 加载XML行为树文件
    import os
    from py_trees import xml
    
    pkg_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    xml_path = os.path.join(pkg_path, 'resource', 'forward_behavior_tree1.xml')
    
    try:
        with open(xml_path, 'r') as f:
            xml_content = f.read()
        
        tree = xml.from_string(xml_content)
        return tree
    except Exception as e:
        print(f"加载行为树失败: {e}")
        return None


def main():
    rclpy.init()
    node = Node("industrial_patrol_bt")
    
    # 创建行为树
    tree = create_tree()
    
    try:
        while rclpy.ok():
            tree.tick()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
        
    rclpy.shutdown()


if __name__ == '__main__':
    main()