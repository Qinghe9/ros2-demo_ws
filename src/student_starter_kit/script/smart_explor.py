
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry, OccupancyGrid
import numpy as np
import time
import math

class UltimateSlamExplorer(Node):
    def __init__(self):
        super().__init__('ultimate_slam_explorer')
        
        # ROS 接口
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)

        # 运动参数
        self.linear_vel = 0.22
        self.angular_vel = 0.8
        self.obstacle_threshold = 0.40  # 避障距离
        
        # 状态控制
        self.state = 'FORWARD'
        self.last_state_change = time.time()
        self.is_stuck = False
        
        # 记忆与位姿
        self.curr_pose = {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
        self.visited_map = {}  # 记录网格访问次数 {(gx, gy): count}
        self.grid_resolution = 0.3 # 0.3米一个网格
        
        # 地图分析
        self.latest_map = None
        self.total_unknown_cells = 0
        self.completion_threshold = 0.98 # 理论覆盖率目标
        self.start_time = time.time()
        self.last_growth_time = time.time()
        self.last_free_count = 0

        self.get_logger().info("🚀 全覆盖智能探索器启动！(集成了地图感知与防边缘游走逻辑)")



    def odom_callback(self, msg):
        self.curr_pose['x'] = msg.pose.pose.position.x
        self.curr_pose['y'] = msg.pose.pose.position.y
        
        # 四元数转 Yaw
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.curr_pose['yaw'] = math.atan2(siny_cosp, cosy_cosp)

        # 记录足迹
        gx = int(self.curr_pose['x'] / self.grid_resolution)
        gy = int(self.curr_pose['y'] / self.grid_resolution)
        self.visited_map[(gx, gy)] = self.visited_map.get((gx, gy), 0) + 1

    def map_callback(self, msg):
        self.latest_map = msg
        data = np.array(msg.data)
        
        # 统计地图状态
        free_count = np.count_nonzero(data == 0)
        unknown_count = np.count_nonzero(data == -1)
        
        # 检查地图是否还在增长
        if free_count > self.last_free_count:
            self.last_free_count = free_count
            self.last_growth_time = time.time()
        
        self.total_unknown_cells = unknown_count

    def get_map_value(self, x, y):
        """获取地图上某个物理坐标的状态"""
        if self.latest_map is None: return -1
        
        origin_x = self.latest_map.info.origin.position.x
        origin_y = self.latest_map.info.origin.position.y
        res = self.latest_map.info.resolution
        width = self.latest_map.info.width
        
        mx = int((x - origin_x) / res)
        my = int((y - origin_y) / res)
        
        if 0 <= mx < width and 0 <= my < self.latest_map.info.height:
            return self.latest_map.data[my * width + mx]
        return -1 # 越界视为未知

    def evaluate_direction(self, angle_offset, laser_dist):
        """
        核心评估：不仅避障和避开历史路径，还要寻找地图中的“未知点”。
        """
        target_yaw = self.curr_pose['yaw'] + angle_offset
        
        # 预测前方 1.0 米处的位置
        look_ahead = 1.0
        tx = self.curr_pose['x'] + math.cos(target_yaw) * look_ahead
        ty = self.curr_pose['y'] + math.sin(target_yaw) * look_ahead
        
        # 1. 雷达距离分 (基础)
        score = laser_dist
        
        # 2. 历史访问惩罚 (解决打转)
        gx, gy = int(tx/self.grid_resolution), int(ty/self.grid_resolution)
        visit_count = self.visited_map.get((gx, gy), 0)
        score -= (visit_count * 1.5) 
        
        # 3. 未知区域奖励 (解决边缘游走)
        # 采样目标点周围的状态
        map_val = self.get_map_value(tx, ty)
        if map_val == -1: # 如果前方是未探测区域，大幅加分
            score += 2.5
            
        return score


    def scan_callback(self, msg):
        if self.latest_map is None: return

        # --- 检查任务是否完成 ---
        # 如果地图超过 45 秒没变化，且已经运行了一段时间，则认为完成
        if time.time() - self.last_growth_time > 45.0 and (time.time() - self.start_time > 60.0):
            self.get_logger().info("🏁 [SUCCESS] 地图全覆盖完成，区域已无新增长点。")
            self.stop_robot()
            time.sleep(2.0)
            rclpy.shutdown()
            return

        ranges = np.array(msg.ranges)
        ranges[np.isinf(ranges)] = msg.range_max
        
        # 区域定义
        front_ranges = np.concatenate([ranges[-30:], ranges[:30]])
        front_min = np.min(front_ranges[front_ranges > 0.1])
        
        cmd = Twist()

        # --- 状态机 ---
        if self.state == 'FORWARD':
            if front_min < self.obstacle_threshold:
                # 遇障决策：评估 5 个方向 (-90, -45, 0, 45, 90 度)
                angles = [-1.57, -0.78, 0.78, 1.57]
                scores = []
                
                # 获取各个方向的雷达均值
                l_dist = np.mean(ranges[45:90])
                r_dist = np.mean(ranges[-90:-45])
                
                l_score = self.evaluate_direction(0.8, l_dist)
                r_score = self.evaluate_direction(-0.8, r_dist)

                if l_score > r_score:
                    self.state = 'TURN_LEFT'
                else:
                    self.state = 'TURN_RIGHT'
                
                self.last_state_change = time.time()
                self.get_logger().info(f"🔄 转向决策: 左分 {l_score:.2f} vs 右分 {r_score:.2f}")
            else:
                # 直行逻辑：加入轻微的“向未知区域偏移”
                cmd.linear.x = self.linear_vel
                # 每秒尝试寻找更优的微偏转角度，避免死板直行
                if self.evaluate_direction(0.2, 2.0) > self.evaluate_direction(-0.2, 2.0):
                    cmd.angular.z = 0.05
                else:
                    cmd.angular.z = -0.05

        elif self.state in ['TURN_LEFT', 'TURN_RIGHT']:
            cmd.angular.z = self.angular_vel if self.state == 'TURN_LEFT' else -self.angular_vel
            # 退出条件：前方变空旷 且 已经转了足够时间
            if front_min > self.obstacle_threshold * 1.8 and (time.time() - self.last_state_change > 1.0):
                self.state = 'FORWARD'
                
        # 兜底脱困：如果长时间处于某种转向状态，强制前行或反转
        if time.time() - self.last_state_change > 5.0 and self.state != 'FORWARD':
            self.state = 'FORWARD'
            self.last_state_change = time.time()

        self.cmd_pub.publish(cmd)

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    explorer = UltimateSlamExplorer()
    try:
        rclpy.spin(explorer)
    except KeyboardInterrupt:
        explorer.get_logger().info("🛑 用户强制停止")
    finally:
        explorer.stop_robot()
        explorer.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()