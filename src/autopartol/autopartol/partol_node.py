# import rclpy
# from geometry_msgs.msg import PoseStamped, Pose
# from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
# from tf2_ros import TransformListener, Buffer
# from tf_transformations import euler_from_quaternion, quaternion_from_euler
# from rclpy.duration import Duration
# # 添加服务接口
# from autopartol_interfaces.srv import Speech
# from sensor_msgs.msg import Image
# from cv_bridge import CvBridge
# import cv2

# class PatrolNode(BasicNavigator):
#     def __init__(self, node_name='patrol_node'):
#         super().__init__(node_name)
#         # 导航相关定义
#         self.declare_parameter('initial_point', [0.0, 0.0, 0.0]) # 初始位置
#         self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57]) # 目标位置
#         self.initial_point_ = self.get_parameter('initial_point').value
#         self.target_points_ = self.get_parameter('target_points').value

#         # 实时位置获取 TF 相关定义
#         self.buffer_ = Buffer()
#         self.listener_ = TransformListener(self.buffer_, self)
#         self.speach_client_ = self.create_client(Speech, 'speech')

#         # 订阅与保存图像相关定义
#         self.declare_parameter('image_save_path', '')
#         self.image_save_path = self.get_parameter('image_save_path').value
#         self.bridge = CvBridge()
#         self.latest_image = None
#         self.subscription_image = self.create_subscription(
#             Image, '/camera_sensor/image_raw', self.image_callback, 10)

#     def image_callback(self, msg):
#         """
#         将最新的消息放到 latest_image 中
#         """
#         self.latest_image = msg

#     def record_image(self):
#         """
#         记录图像
#         """
#         if self.latest_image is not None:
#           pose = self.get_current_pose()
#           cv_image = self.bridge.imgmsg_to_cv2(self.latest_image)
#           cv2.imwrite(f'{self.image_save_path}image_{pose.translation.x:3.2f}_{pose.translation.y:3.2f}.png', cv_image)


#     def speach(self, text):
#         """
#         调用服务播放语音
#         """
#         # 等待语音合成服务上线
#         while not self.speach_client_.wait_for_service(timeout_sec=1.0):
#             self.get_logger().info('语音合成服务未上线，等待中。。。')
#         # 创建服务请求
#         request = Speech.Request()
#         request.text = text
#         # 异步调用服务
#         future = self.speach_client_.call_async(request)
#         # 等待服务响应完成
#         rclpy.spin_until_future_complete(self, future)
#         if future.result() is not None:
#             result = future.result().result
#             if result:
#                 self.get_logger().info(f'语音合成成功：{text}')
#             else:
#                 self.get_logger().warn(f'语音合成失败：{text}')
#         else:
#             self.get_logger().warn('语音合成服务请求失败')

#     def get_pose_by_xyyaw(self, x, y, yaw):
#         """
#         通过 x,y,yaw 合成 PoseStamped
#         """
#         pose = PoseStamped()  # 创建位姿消息
#         pose.header.frame_id = 'map' # 位姿参考坐标系
#         pose.pose.position.x = x # 位姿 x 坐标
#         pose.pose.position.y = y # 位姿 y 坐标
#         # 欧拉角转换为四元数
#         rotation_quat = quaternion_from_euler(0, 0, yaw)
#         pose.pose.orientation.x = rotation_quat[0]
#         pose.pose.orientation.y = rotation_quat[1]
#         pose.pose.orientation.z = rotation_quat[2]
#         pose.pose.orientation.w = rotation_quat[3]
#         return pose # 返回位姿

#     def init_robot_pose(self):
#         """
#         初始化机器人位姿
#         """
#         # 从参数获取初始化点
#         self.initial_point_ = self.get_parameter('initial_point').value
#         # 合成位姿并进行初始化
#         self.setInitialPose(self.get_pose_by_xyyaw(
#             self.initial_point_[0], self.initial_point_[1], self.initial_point_[2]))
#         # 等待直到导航激活
#         self.waitUntilNav2Active()

#     def get_target_points(self):
#         """
#         通过参数值获取目标点集合        
#         """
#         points = []
#         self.target_points_ = self.get_parameter('target_points').value
#         for index in range(int(len(self.target_points_)/3)):
#             x = self.target_points_[index*3]
#             y = self.target_points_[index*3+1]
#             yaw = self.target_points_[index*3+2]
#             points.append([x, y, yaw])
#             self.get_logger().info(f'获取到目标点: {index}->({x},{y},{yaw})')
#         return points

#     def nav_to_pose(self, target_pose):
#         """
#         导航到指定位姿
#         """
#         self.waitUntilNav2Active()
#         result = self.goToPose(target_pose)
#         while not self.isTaskComplete():
#             feedback = self.getFeedback()
#             if feedback:
#                 self.get_logger().info(f'预计: {Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9} s 后到达')
#                 self.get_logger().info(f'剩余距离: {feedback.distance_remaining:.2f} m')
#         # 最终结果判断
#         result = self.getResult()
#         if result == TaskResult.SUCCEEDED:
#             self.get_logger().info('导航结果：成功')
#         elif result == TaskResult.CANCELED:
#             self.get_logger().warn('导航结果：被取消')
#         elif result == TaskResult.FAILED:
#             self.get_logger().error('导航结果：失败')
#         else:
#             self.get_logger().error('导航结果：返回状态无效')

#     def get_current_pose(self):
#         """
#         通过TF获取当前位姿
#         """
#         while rclpy.ok():
#             try:
#                 tf = self.buffer_.lookup_transform(
#                     'map', 'base_footprint', rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
#                 transform = tf.transform
#                 rotation_euler = euler_from_quaternion([
#                     transform.rotation.x,
#                     transform.rotation.y,
#                     transform.rotation.z,
#                     transform.rotation.w
#                 ])
#                 self.get_logger().info(
#                     f'平移:{transform.translation},旋转四元数:{transform.rotation}:旋转欧拉角:{rotation_euler}')
#                 return transform
#             except Exception as e:
#                 self.get_logger().warn(f'不能够获取坐标变换，原因: {str(e)}')
    
# def main():
#     rclpy.init()
#     patrol = PatrolNode()
#     patrol.speach('正在初始化位置')
#     patrol.init_robot_pose()
#     patrol.speach('位置初始化完成')

#     while rclpy.ok():
#         for point in patrol.get_target_points():
#             x, y, yaw = point[0], point[1], point[2]
#             # 导航到目标点
#             target_pose = patrol.get_pose_by_xyyaw(x, y, yaw)
#             patrol.speach(f'准备前往目标点{x},{y}')
#             patrol.nav_to_pose(target_pose)
#             patrol.speach(f"已到达目标点{x},{y},准备记录图像")
#             patrol.record_image()
#             patrol.speach(f"图像记录完成")
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()
#!/usr/bin/env python3
import rclpy
from geometry_msgs.msg import PoseStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from rclpy.duration import Duration
from rclpy.parameter import Parameter
from autopartol_interfaces.srv import Speech
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import yaml
import sys
import os


class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_node'):
        super().__init__(node_name)
        
        # ====================================================================
        # ⭐ 导航相关参数（添加默认值，防止参数未设置时报错）
        # ====================================================================
        self.declare_parameter('initial_point', [0.0, 0.0, 0.0])
        self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        self.declare_parameter('image_save_path', '/tmp/patrol_images/')
        
        self.initial_point_ = self.get_parameter('initial_point').value
        self.target_points_ = self.get_parameter('target_points').value
        self.image_save_path = self.get_parameter('image_save_path').value
        
        # 确保保存目录存在
        os.makedirs(self.image_save_path, exist_ok=True)

        self.buffer_ = Buffer()
        self.listener_ = TransformListener(self.buffer_, self)
        
        self.speach_client_ = self.create_client(Speech, 'speech')

        self.bridge = CvBridge()
        self.latest_image = None
        self.subscription_image = self.create_subscription(
            Image, '/camera_sensor/image_raw', self.image_callback, 10)

    def image_callback(self, msg):
        """将最新的消息放到 latest_image 中"""
        self.latest_image = msg

    def record_image(self):
        """记录图像"""
        if self.latest_image is not None:
            pose = self.get_current_pose()
            cv_image = self.bridge.imgmsg_to_cv2(self.latest_image)
            filename = f'{self.image_save_path}image_{pose.translation.x:.2f}_{pose.translation.y:.2f}.png'
            cv2.imwrite(filename, cv_image)
            self.get_logger().info(f'图像已保存：{filename}')
        else:
            self.get_logger().warn('暂无最新图像，跳过保存')

    def speach(self, text):
        """调用服务播放语音"""
        while not self.speach_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('语音合成服务未上线，等待中。。。')
        
        request = Speech.Request()
        request.text = text
        future = self.speach_client_.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            result = future.result().result
            if result:
                self.get_logger().info(f'语音合成成功：{text}')
            else:
                self.get_logger().warn(f'语音合成失败：{text}')
        else:
            self.get_logger().warn('语音合成服务请求失败')

    def get_pose_by_xyyaw(self, x, y, yaw):
        """通过 x,y,yaw 合成 PoseStamped"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = x
        pose.pose.position.y = y
        rotation_quat = quaternion_from_euler(0, 0, yaw)
        pose.pose.orientation.x = rotation_quat[0]
        pose.pose.orientation.y = rotation_quat[1]
        pose.pose.orientation.z = rotation_quat[2]
        pose.pose.orientation.w = rotation_quat[3]
        return pose

    def init_robot_pose(self):
        """初始化机器人位姿"""
        self.initial_point_ = self.get_parameter('initial_point').value
        self.get_logger().info(f'初始位置：{self.initial_point_}')
        
        self.setInitialPose(self.get_pose_by_xyyaw(
            self.initial_point_[0], self.initial_point_[1], self.initial_point_[2]))
        self.waitUntilNav2Active()
        self.get_logger().info('Nav2 已激活')

    def get_target_points(self):
        """通过参数值获取目标点集合"""
        points = []
        self.target_points_ = self.get_parameter('target_points').value
        
        if len(self.target_points_) % 3 != 0:
            self.get_logger().error(f'target_points 长度必须是 3 的倍数，当前长度：{len(self.target_points_)}')
            return points
        
        for index in range(int(len(self.target_points_) / 3)):
            x = self.target_points_[index * 3]
            y = self.target_points_[index * 3 + 1]
            yaw = self.target_points_[index * 3 + 2]
            points.append([x, y, yaw])
            self.get_logger().info(f'目标点 {index}: ({x}, {y}, {yaw:.2f} rad)')
        
        return points

    def nav_to_pose(self, target_pose):
        """导航到指定位姿"""
        self.waitUntilNav2Active()
        self.goToPose(target_pose)
        
        while not self.isTaskComplete():
            feedback = self.getFeedback()
            if feedback:
                self.get_logger().info(
                    f'预计：{Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9:.1f} s 后到达，'
                    f'剩余距离：{feedback.distance_remaining:.2f} m')
        
        result = self.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('导航结果：成功')
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('导航结果：被取消')
        elif result == TaskResult.FAILED:
            self.get_logger().error('导航结果：失败')
        else:
            self.get_logger().error('导航结果：返回状态无效')

    def get_current_pose(self):
        """通过 TF 获取当前位姿"""
        try:
            tf = self.buffer_.lookup_transform(
                'map', 'base_footprint', rclpy.time.Time(), rclpy.time.Duration(seconds=1.0))
            transform = tf.transform
            rotation_euler = euler_from_quaternion([
                transform.rotation.x,
                transform.rotation.y,
                transform.rotation.z,
                transform.rotation.w
            ])
            self.get_logger().info(
                f'位置：({transform.translation.x:.2f}, {transform.translation.y:.2f}), '
                f'朝向：{rotation_euler[2]:.2f} rad')
            return transform
        except Exception as e:
            self.get_logger().warn(f'无法获取坐标变换：{str(e)}')
            # 返回一个默认值避免程序崩溃
            from geometry_msgs.msg import Transform
            return Transform()


def load_param_file(node, param_file_path):
    """
    手动加载参数文件到节点
    """
    if not os.path.exists(param_file_path):
        node.get_logger().error(f'参数文件不存在：{param_file_path}')
        return False
    
    try:
        with open(param_file_path, 'r', encoding='utf-8') as f:
            params = yaml.safe_load(f)
        
        # 查找节点对应的参数
        node_name = node.get_name()
        if node_name in params and 'ros__parameters' in params[node_name]:
            node_params = params[node_name]['ros__parameters']
            
            for name, value in node_params.items():
                try:
                    param_type = Parameter.Type.from_parameter_value(value)
                    param = Parameter(name, param_type, value)
                    node.set_parameters([param])
                    node.get_logger().info(f'加载参数：{name} = {value}')
                except Exception as e:
                    node.get_logger().warn(f'设置参数 {name} 失败：{e}')
        else:
            node.get_logger().warn(f'参数文件中未找到节点 {node_name} 的配置')
        
        return True
    except Exception as e:
        node.get_logger().error(f'加载参数文件失败：{e}')
        return False


def parse_args(args):
    """
    ⭐ 解析命令行参数，提取 --param-file
    """
    param_file = None
    clean_args = []
    
    i = 0
    while i < len(args):
        if args[i] == '--param-file' and i + 1 < len(args):
            param_file = args[i + 1]
            i += 2
        elif args[i].startswith('--param-file='):
            param_file = args[i].split('=', 1)[1]
            i += 1
        else:
            clean_args.append(args[i])
            i += 1
    
    return param_file, clean_args


def main():

    args = sys.argv[1:]
    param_file, clean_args = parse_args(args)
    rclpy.init(args=clean_args)
    patrol = PatrolNode('patrol_node')
    if param_file:
        patrol.get_logger().info(f'加载参数文件：{param_file}')
        load_param_file(patrol, param_file)
    else:
        patrol.get_logger().warn('未指定参数文件，使用默认参数')
        patrol.get_logger().info(f'默认初始位置：{patrol.initial_point_}')
        patrol.get_logger().info(f'默认目标点：{patrol.target_points_}')

    try:
        patrol.speach('正在初始化位置')
        patrol.init_robot_pose()
        patrol.speach('位置初始化完成')
        
        while rclpy.ok():
            points = patrol.get_target_points()
            if not points:
                patrol.get_logger().error('没有有效的目标点，退出循环')
                break
            
            for point in points:
                if not rclpy.ok():
                    break
                
                x, y, yaw = point[0], point[1], point[2]
                target_pose = patrol.get_pose_by_xyyaw(x, y, yaw)
                
                patrol.speach(f'准备前往目标点 {x}, {y}')
                patrol.nav_to_pose(target_pose)
                patrol.speach(f'已到达目标点 {x}, {y}, 准备记录图像')
                patrol.record_image()
                patrol.speach('图像记录完成')
    
    except KeyboardInterrupt:
        patrol.get_logger().info('收到中断信号，正在退出...')
    except Exception as e:
        patrol.get_logger().error(f'运行错误：{e}')
    finally:
        patrol.speach('巡逻任务结束')
        patrol.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()