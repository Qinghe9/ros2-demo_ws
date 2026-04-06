

## 一键安装ros2

[ROS的最简单安装——鱼香一键安装_鱼香ros-CSDN博客](https://blog.csdn.net/m0_73745340/article/details/135281023)



## 在ubuntu中安装conda

使用多线程下载

```
# 安装aria
sudo apt install aria2

# 使用aria2下载
aria2c -x 16 -s 16 https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh
```

下载后运行

```bash
bash Anaconda3-2024.10-1-Linux-x86_64.sh
```

安装完成后**重启终端**即可



**环境配置已经导出来了，也可以使用以下命令一键创建安装环境，之后无需再安装其它包**

```bash
conda env create -f environment.yml
```



创建新环境

```bash
conda create -n ros2 python=3.10
```

## 安装Gazebo

1. 更新软件源

```bash
sudo apt update
sudo apt upgrade -y
```

2. 安装与 ROS Humble 兼容的 Gazebo

```bash
sudo apt install -y \
    gazebo \
    libgazebo-dev \
    gazebo-plugin-base \
    gazebo-common \
    ros-humble-gazebo-ros-pkgs
```

3. 验证安装的 Gazebo 版本

```bash
gazebo --version
```

## 安装 TurtleBot3 完整依赖

执行以下命令：

```bash
sudo apt install -y \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-msgs \
    ros-humble-turtlebot3-description \
    ros-humble-turtlebot3-simulations \
    ros-humble-turtlebot3-gazebo \
    ros-humble-gazebo-ros-pkgs
```

## 查看环境变量

1. 查看ros2

```bash
echo $ROS_DISTRO
```

示例输出

```bash
humble
```

2. 查看`AMENT_PREFIX_PATH`：

```bash
echo $AMENT_PREFIX_PATH
```

示例输出

```bash
/opt/ros/humble
```



## 启动步骤

### 建立工作空间

1. 查看当前目录

```bash
pwd
##输出/home/qinghe
```

2. 建立工作文件夹

```bash
mkdir ros2_ws/src
cd ros2_ws/
mkdir src
```

3. 将`student_starter_kit`包放在`src/`目录下，并把名字改成`tb3_course_student`，这是因为`CMakeLists.txt`文件中的项目名是这个

   ![76984469895](figures\1.png)

```bash
## 当前目录文件
cd ros2_ws
ls src/tb3_course_student
CMakeLists.txt  config  maps         src
README.md       launch  package.xml  worlds
```

## 编译项目

进入工作空间

```bash
cd ros2_ws
colcon build --packages-select tb3_course_student
source setup_ros2.sh
```

## SLAM建图

1. 配置SLAM参数

编辑` config/slam_toolbox_template.yaml` ：

```bash
# TODO: tune minimum_travel_distance / headings for better maps
minimum_travel_distance: 0.5
minimum_travel_heading: 0.5
# 修改成
minimum_travel_distance: 0.2
minimum_travel_heading: 0.2
```

减小这两个值以获得更密集的地图

2. 启动仿真环境（终端1）

```bash
# 打开终端1
cd ros2_ws
source setup_ros2.sh
ros2 launch tb3_course_student sim_world.launch.py
```

3. 启动SLAM（终端2）

```bash
# 终端2：启动SLAM
conda activate ros2
cd ros2_ws
source setup_ros2.sh
ros2 launch tb3_course_student slam.launch.py
```

4. 键盘控制机器人移动建图

```bash
# 终端3：启动键盘控制
conda activate ros2
cd ros2_ws
source setup_ros2.sh
ros2 run turtlebot3_teleop teleop_keyboard
```

控制说明：

- i ：前进
- j ：左转
- l ：右转
- , ：后退
- u / o ：左前/右前
- m / . ：左后/右后

建图技巧：

1. 缓慢移动机器人
2. 覆盖所有角落和障碍物
3. 在关键区域多走几次
4. 沿着墙壁边缘移动

![76985074918](figures\2.png)

5. 保存地图

```bash
# 终端4：保存地图
conda activate ros2
cd ros2_ws
source setup_ros2.sh
ros2 run nav2_map_server map_saver_cli -f src/tb3_course_student/maps/map
```

查看地图

```bash
sudo apt install imagemagick
display /home/qinghe/ros2_ws/src/tb3_course_student/maps/map.pgm
```

![76985071176](figures\3png)



（自动建图，参考资料

[hrnr/m-explore：多机器人探索的ROS软件包](https://github.com/hrnr/m-explore)）



最后，在运行SLAM的终端按` Ctrl+C `终止。





## 导航

1. 配置Nav2参数

   编辑` src/tb3_course_student/config/nav2_params_template.yaml` ，

```bash
# Nav2 parameter template (student)
amcl:
  ros__parameters:
    use_sim_time: true
    # TODO: complete AMCL params if used

planner_server:
  ros__parameters:
    use_sim_time: true
    planner_plugins: ["GridBased"] # TODO: choose planner and tune

controller_server:
  ros__parameters:
    use_sim_time: true
    controller_plugins: ["FollowPath"] # TODO: configure DWB or other local planner

```

   完整配置如下：

```bash
# Nav2 parameter template (student)
map_server:
  ros__parameters:
    use_sim_time: true
    yaml_filename: "maps/map.yaml"
    frame_id: "map"

amcl:
  ros__parameters:
    use_sim_time: true
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2
    alpha5: 0.2
    base_frame_id: "base_footprint"
    beam_skip_distance: 0.5
    beam_skip_error_threshold: 0.9
    beam_skip_threshold: 0.3
    do_beamskip: false
    global_frame_id: "map"
    lambda_short: 0.1
    laser_likelihood_max_dist: 2.0
    laser_max_range: 100.0
    laser_min_range: -1.0
    laser_model_type: "likelihood_field"
    max_beams: 60
    max_particles: 2000
    min_particles: 500
    odom_frame_id: "odom"
    pf_err: 0.05
    pf_z: 0.99
    recovery_alpha_fast: 0.0
    recovery_alpha_slow: 0.0
    resample_interval: 1
    robot_model_type: "nav2_amcl::DifferentialMotionModel"
    save_pose_rate: 0.5
    sigma_hit: 0.2
    tf_broadcast: true
    transform_tolerance: 1.0
    update_min_d: 0.2
    update_min_a: 0.5
    z_hit: 0.5
    z_max: 0.05
    z_rand: 0.5
    z_short: 0.05

planner_server:
  ros__parameters:
    use_sim_time: true
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: true
      allow_unknown: true

controller_server:
  ros__parameters:
    use_sim_time: true
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    progress_checker_plugin: "progress_checker"
    goal_checker_plugin: "goal_checker"
    controller_plugins: ["FollowPath"]
    
    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0
    
    goal_checker:
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25
    
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      debug_trajectory_details: false
      min_vel_x: 0.0
      min_vel_y: 0.0
      max_vel_x: 0.26
      max_vel_y: 0.0
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.26
      min_speed_theta: 0.0
      acc_lim_x: 2.5
      acc_lim_y: 0.0
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_y: 0.0
      decel_lim_theta: -3.2
      vx_samples: 20
      vy_samples: 1
      vtheta_samples: 20
      sim_time: 1.7
      linear_granularity: 0.05
      angular_granularity: 0.025
      transform_tolerance: 0.2
      xy_goal_tolerance: 0.25
      trans_stopped_velocity: 0.25
      short_circuit_trajectory_evaluation: true
      stateful: true
      critics: ["RotateToGoal", "Oscillation", "BaseObstacle", "GoalAlign", "PathAlign", "PathDist", "GoalDist"]
      BaseObstacle.scale: 0.02
      PathAlign.scale: 32.0
      PathAlign.forward_point_distance: 0.1
      GoalAlign.scale: 24.0
      GoalAlign.forward_point_distance: 0.1
      PathDist.scale: 32.0
      GoalDist.scale: 24.0
      RotateToGoal.scale: 32.0
      RotateToGoal.slowing_factor: 5.0
      Oscillation.scale: 1.0

local_costmap:
  ros__parameters:
    update_frequency: 5.0
    publish_frequency: 2.0
    global_frame: odom
    robot_base_frame: base_footprint
    use_sim_time: true
    rolling_window: true
    width: 3
    height: 3
    resolution: 0.05
    plugin_names: ["obstacle_layer", "inflation_layer"]
    plugin_namespaces: ["", ""]
    obstacle_layer:
      plugin: "nav2_costmap_2d::ObstacleLayer"
      enabled: true
      observation_sources: scan
      scan:
        topic: /scan
        max_obstacle_height: 2.0
        clearing: true
        marking: true
        data_type: "LaserScan"
        raytrace_max_range: 3.0
        raytrace_min_range: 0.0
        obstacle_max_range: 2.5
        obstacle_min_range: 0.0
    inflation_layer:
      plugin: "nav2_costmap_2d::InflationLayer"
      cost_scaling_factor: 3.0
      inflation_radius: 0.55
    always_send_full_costmap: true
    footprint_padding: 0.03
    footprint: "[ [0.2, 0.15], [0.2, -0.15], [-0.2, -0.15], [-0.2, 0.15] ]"

global_costmap:
  ros__parameters:
    update_frequency: 1.0
    publish_frequency: 1.0
    global_frame: map
    robot_base_frame: base_footprint
    use_sim_time: true
    plugin_names: ["static_layer", "obstacle_layer", "inflation_layer"]
    plugin_namespaces: ["", "", ""]
    static_layer:
      plugin: "nav2_costmap_2d::StaticLayer"
      map_subscribe_transient_local: true
    obstacle_layer:
      plugin: "nav2_costmap_2d::ObstacleLayer"
      enabled: true
      observation_sources: scan
      scan:
        topic: /scan
        max_obstacle_height: 2.0
        clearing: true
        marking: true
        data_type: "LaserScan"
        raytrace_max_range: 3.0
        raytrace_min_range: 0.0
        obstacle_max_range: 2.5
        obstacle_min_range: 0.0
    inflation_layer:
      plugin: "nav2_costmap_2d::InflationLayer"
      cost_scaling_factor: 3.0
      inflation_radius: 0.55
    always_send_full_costmap: true
    footprint_padding: 0.03
    footprint: "[ [0.2, 0.15], [0.2, -0.15], [-0.2, -0.15], [-0.2, 0.15] ]"

# # Nav2 parameter template (student)
# amcl:
#   ros__parameters:
#     use_sim_time: true
#     # TODO: complete AMCL params if used

# planner_server:
#   ros__parameters:
#     use_sim_time: true
#     planner_plugins: ["GridBased"] # TODO: choose planner and tune

# controller_server:
#   ros__parameters:
#     use_sim_time: true
#     controller_plugins: ["FollowPath"] # TODO: configure DWB or other local planner
```

2. 启动导航系统

```bash
# 确保仿真仍在运行
# 终端3：启动导航
conda activate ros2
cd ros2_ws
source setup_ros2.sh
ros2 launch tb3_course_student nav2_stub.launch.py
```

3. 然后检查

```bash
ros2 topic echo /tf_static
ros2 service list | grep map_server
ros2 service list | grep amcl
```

4.测试导航(新终端)

```bash
# 终端4：发送导航目标
conda activate ros2
cd ros2_ws
source setup_ros2.sh

# 手动发送导航目标
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 1.0, z: 0.0}, orientation: {w: 1.0}}}}"
```



![76986895313](figures\4.png)





## 航点导航实现

1. 实现waypoint_nav.py

   编辑`src/tb3_course_student/src/waypoint_nav.py `，完整实现如下：

```bash
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus
import math

class WaypointNav(Node):
    def __init__(self):
        super().__init__('waypoint_nav')
        self.action_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.waypoints = [
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 1.57),
            (0.0, 1.0, 3.14),
            (0.0, 0.0, 0.0)
        ]
        self.current_waypoint_index = 0

    def send_goal(self, x, y, yaw):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        
        quaternion = self.yaw_to_quaternion(yaw)
        goal_msg.pose.pose.orientation = quaternion
        
        self.get_logger().info(f'Sending goal to waypoint: ({x}, {y}, {yaw})')
        return self.action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)

    def yaw_to_quaternion(self, yaw):
        quaternion = PoseStamped().pose.orientation
        quaternion.x = 0.0
        quaternion.y = 0.0
        quaternion.z = math.sin(yaw / 2.0)
        quaternion.w = math.cos(yaw / 2.0)
        return quaternion

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().debug(f'Feedback: {feedback}')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        self.get_logger().info('Goal accepted')
        self.get_future_result = goal_handle.get_result_async()
        self.get_future_result.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        status = future.result().status
        
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Waypoint {self.current_waypoint_index} reached successfully!')
            self.current_waypoint_index += 1
            if self.current_waypoint_index < len(self.waypoints):
                self.navigate_to_next_waypoint()
            else:
                self.get_logger().info('All waypoints completed!')
        else:
            self.get_logger().error(f'Goal failed with status: {status}')

    def navigate_to_next_waypoint(self):
        if self.current_waypoint_index < len(self.waypoints):
            x, y, yaw = self.waypoints[self.current_waypoint_index]
            self.action_client.wait_for_server()
            future = self.send_goal(x, y, yaw)
            future.add_done_callback(self.goal_response_callback)

    def run_waypoints(self):
        self.get_logger().info('Waiting for action server...')
        self.action_client.wait_for_server()
        self.get_logger().info('Action server available, starting waypoint navigation')
        self.navigate_to_next_waypoint()

def main():
    rclpy.init()
    node = WaypointNav()
    node.run_waypoints()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

启动导航可视化节点

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True
```



1. 设置权限

```bash
chmod +x ros2_ws/src/tb3_course_student/src/waypoint_nav.py
```

3. 重新编译

```bash
cd ros2_ws
colcon build --packages-select tb3_course_student
```

4. 运行航点导航

```bash
# 确保仿真和导航系统都在运行
# 终端4：运行航点导航
cd ros2_ws
source setup_ros2.sh
ros2 launch tb3_course_student waypoint_stub.launch.py
```

![76986965642](figures\5.png)




# 常见问题

## 1. 编译时报错

```bash
colcon build --packages-select tb3_course_student
Starting >>> tb3_course_student
--- stderr: tb3_course_student                         
Traceback (most recent call last):
  File "/opt/ros/humble/share/ament_cmake_core/cmake/core/package_xml_2_cmake.py", line 22, in <module>
    from catkin_pkg.package import parse_package_string
ModuleNotFoundError: No module named 'catkin_pkg'
```

安装即可

```bash
 pip install catkin_pkg
```

## 2. 启动SLAM仿真时找不到包

```bash
ros2 launch tb3_course_student sim_world.launch.py
Package 'tb3_course_student' not found: "package 'tb3_course_student' not found, searching: ['/opt/ros/humble']"
```

检查环境变量

```bash
printenv | grep AMENT
AMENT_PREFIX_PATH=/opt/ros/humble
```

写一个设置环境变量的脚本



使用方法

```bash
cd ros2_ws
chmod +x setup_ros2.sh

# 方式1：直接执行（查看信息）
./setup_ros2.sh

# 方式2：加载到当前终端（实际设置环境）
source setup_ros2.sh

# 方式3：带参数使用
source setup_ros2.sh --ros-distro humble --workspace /home/user/ros2_ws

# 方式4：查看帮助
./setup_ros2.sh --help

#验证环境
ros2 pkg list | grep tb3_course_student
```



```bash
ros2 launch nav2_bringup tb3_simulation_launch.py
```



# 导航进阶

配置navigation 2参数,把默认的nav2参数复制到工作空间

```bash
 cp /opt/ros/humble/share/nav2_bringup/params/nav2_params.yaml src/tb3_course_student/config/
```



lauch文件中使用`nav2_bringup`里的启动文件，会加快我们的导航启动速度

```bash
(ros2) airsim@AIPhy:/home/qinghe/ros2_ws$ cd /opt/ros/humble/share/nav2_bringup/rviz/
(ros2) airsim@AIPhy:/opt/ros/humble/share/nav2_bringup/rviz$ ls -l
total 32
-rw-r--r-- 1 root root 18303 Nov 18 01:56 nav2_default_view.rviz
-rw-r--r-- 1 root root 12002 Nov 18 01:56 nav2_namespaced_view.rviz
```

在文件中修改：

```bash
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz_config_dir = os.path.join(
        nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
        
        ......
  launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_bringup_dir, '/launch', '/bringup_launch.py']),
```



启动

```bash
conda activate ros2
cd ros2_ws
source setup_ros2.sh
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
ros2 launch tb3_course_student nav2.launch.py 
```



全局代价地图开关

![77020671194](figures\6.png)

局部代价地图开关

![77020679976](figures\7.png)



一开始会报tf错误

![77029414077](C:\Users\AIPhy\Desktop\ros2启动\figures\9.png)

需要给机器人一个大概的位置，amcl会基于这个位置做大概的估计

在rviz中，选择2D Pose Estimate来标定位置

![77029426427](C:\Users\AIPhy\Desktop\ros2启动\figures\10.png)

单点导航

![77029451595](C:\Users\AIPhy\Desktop\ros2启动\figures\11.png)

![77029469618](C:\Users\AIPhy\Desktop\ros2启动\figures\12.png)

其中，蓝色的线是局部规划路径

多点导航

通过这个插件可以取消导航任务，也可以设置多个目标点的导航，点击最下面的 Waypoint/Nav Through Poses Mode ，接着使用 Nav2 Goal 依次设置多个路点，比如下图中设置了五个路点，让机器人绕过咖啡桌再到左前方的目标点。



![77020679976](figures\8.png)



![77029550622](C:\Users\AIPhy\Desktop\ros2启动\figures\13.png)

![77029564307](C:\Users\AIPhy\Desktop\ros2启动\figures\14.png)



动态避障

![77029611062](C:\Users\AIPhy\Desktop\ros2启动\figures\18.png)

在规划的路径中间放一个圆柱

![77029622045](C:\Users\AIPhy\Desktop\ros2启动\figures\17.png)

![77029657014](C:\Users\AIPhy\Desktop\ros2启动\figures\16.png)

路线变了

## 使用话题初始化机器人位置信息

查看节点

```bash
ros2 node info /amcl
/amcl
  Subscribers:
    /bond: bond/msg/Status
    /clock: rosgraph_msgs/msg/Clock
    /initialpose: geometry_msgs/msg/PoseWithCovarianceStamped # 用于接受初始化未知的信息，直接向这个话题发布数据
    /map: nav_msgs/msg/OccupancyGrid
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /scan: sensor_msgs/msg/LaserScan
  Publishers:
    /amcl/transition_event: lifecycle_msgs/msg/TransitionEvent
    /amcl_pose: geometry_msgs/msg/PoseWithCovarianceStamped
    /bond: bond/msg/Status
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /particle_cloud: nav2_msgs/msg/ParticleCloud
    /rosout: rcl_interfaces/msg/Log
    /tf: tf2_msgs/msg/TFMessage
  Service Servers:
    /amcl/change_state: lifecycle_msgs/srv/ChangeState
    /amcl/describe_parameters: rcl_interfaces/srv/DescribeParameters
    /amcl/get_available_states: lifecycle_msgs/srv/GetAvailableStates
    /amcl/get_available_transitions: lifecycle_msgs/srv/GetAvailableTransitions
    /amcl/get_parameter_types: rcl_interfaces/srv/GetParameterTypes
    /amcl/get_parameters: rcl_interfaces/srv/GetParameters
    /amcl/get_state: lifecycle_msgs/srv/GetState
    /amcl/get_transition_graph: lifecycle_msgs/srv/GetAvailableTransitions
    /amcl/list_parameters: rcl_interfaces/srv/ListParameters
    /amcl/set_parameters: rcl_interfaces/srv/SetParameters
    /amcl/set_parameters_atomically: rcl_interfaces/srv/SetParametersAtomically
    /reinitialize_global_localization: std_srvs/srv/Empty
    /request_nomotion_update: std_srvs/srv/Empty
    /set_initial_pose: nav2_msgs/srv/SetInitialPose
  Service Clients:

  Action Servers:

  Action Clients:

```

在gazebo中，查看机器人在物理坐标系的位置

![77029744798](C:\Users\AIPhy\Desktop\ros2启动\figures\15.png)

使用命令行发布数据

```bash
ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: 'map'}}" --once
##usage
--once 代表只发布一次

```

发布结果

```bash
ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: 'map'}}" --once
Waiting for at least 1 matching subscription(s)...
Waiting for at least 1 matching subscription(s)...
Waiting for at least 1 matching subscription(s)...
publisher: beginning loop
publishing #1: geometry_msgs.msg.PoseWithCovarianceStamped(header=std_msgs.msg.Header(stamp=builtin_interfaces.msg.Time(sec=0, nanosec=0), frame_id='map'), pose=geometry_msgs.msg.PoseWithCovariance(pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=0.0, y=0.0, z=0.0), orientation=geometry_msgs.msg.Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)), covariance=array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0.])))
```

打开rviz，发现机器人已经初始化完成

![77029816761](C:\Users\AIPhy\Desktop\ros2启动\figures\19.png)

## 使用话题初始化机器人位姿

构建功能包

```bash
ros2 pkg create app --build-type ament_python --license Apache-2.0
```



编写`init_pose.py`

```bash
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy


def main():
    rclpy.init()
    navigator = BasicNavigator()
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0
    navigator.setInitialPose(initial_pose)
    navigator.waitUntilNav2Active()
    rclpy.spin(navigator)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

在`setup.py`中添加可执行文件

```bash
    entry_points={
        'console_scripts': [
            'init_pose = app.init_pose:main',
            
        ],
    },
```

启动

```bash
cd ros2_ws
colcon build

ros2 run app init_pose.py
```

## 使用TF获取机器人的实时位置

编写`get_pose.py`

```bash
import rclpy
from rclpy.node import Node
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion


class TFListener(Node):

    def __init__(self):
        super().__init__('tf2_listener')
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.timer = self.create_timer(1, self.get_transform)

    def get_transform(self):
        try:
            tf = self.buffer.lookup_transform(
                'map', 'base_footprint', rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
            transform = tf.transform
            rotation_euler = euler_from_quaternion([
                transform.rotation.x,
                transform.rotation.y,
                transform.rotation.z,
                transform.rotation.w
            ])
            self.get_logger().info(
                f'平移:{transform.translation},旋转四元数:{transform.rotation}:旋转欧拉角:{rotation_euler}\n')
        except Exception as e:
            self.get_logger().warn(f'不能够获取坐标变换，原因: {str(e)}')


def main():
    rclpy.init()
    node = TFListener()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```



启动

```bash
ros2 run app get_pose
```



结果

![77044250680](C:\Users\AIPhy\Desktop\ros2启动\figures\20.png)



此时tf树如下：

![77044312485](C:\Users\AIPhy\Desktop\ros2启动\figures\21.png)

## 调用接口进行单点导航

查看动作节点

```bash
 ros2 action list -t
/assisted_teleop [nav2_msgs/action/AssistedTeleop]
/backup [nav2_msgs/action/BackUp]
/compute_path_through_poses [nav2_msgs/action/ComputePathThroughPoses]
/compute_path_to_pose [nav2_msgs/action/ComputePathToPose]
/drive_on_heading [nav2_msgs/action/DriveOnHeading]
/follow_path [nav2_msgs/action/FollowPath]
/follow_waypoints [nav2_msgs/action/FollowWaypoints]
/navigate_through_poses [nav2_msgs/action/NavigateThroughPoses]
/navigate_to_pose [nav2_msgs/action/NavigateToPose] ## 此服务用于处理导航到点的请求
/smooth_path [nav2_msgs/action/SmoothPath]
/spin [nav2_msgs/action/Spin]
/wait [nav2_msgs/action/Wait]
```



查看`nav2_msgs/action/NavigateToPose`接口的内容

```bash
ros2 interface  show nav2_msgs/action/NavigateToPose
```

详细信息如下

```bash
ros2 interface  show nav2_msgs/action/NavigateToPose
#goal definition  客户端发给服务端的目标
geometry_msgs/PoseStamped pose
        std_msgs/Header header
                builtin_interfaces/Time stamp
                        int32 sec
                        uint32 nanosec
                string frame_id
        Pose pose
                Point position
                        float64 x
                        float64 y
                        float64 z
                Quaternion orientation
                        float64 x 0
                        float64 y 0
                        float64 z 0
                        float64 w 1
string behavior_tree
---
#result definition
std_msgs/Empty result
---
#feedback definition 服务端给客户端的反馈
geometry_msgs/PoseStamped current_pose
        std_msgs/Header header
                builtin_interfaces/Time stamp
                        int32 sec
                        uint32 nanosec
                string frame_id
        Pose pose
                Point position
                        float64 x
                        float64 y
                        float64 z
                Quaternion orientation
                        float64 x 0
                        float64 y 0
                        float64 z 0
                        float64 w 1
builtin_interfaces/Duration navigation_time
        int32 sec
        uint32 nanosec
builtin_interfaces/Duration estimated_time_remaining
        int32 sec
        uint32 nanosec
int16 number_of_recoveries
float32 distance_remaining
```

发送一个动作请求给动作服务器

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 1.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}" --feedback
```

机器人会前往`x=2.0,y=1.0`的导航点

![77044408839](C:\Users\AIPhy\Desktop\ros2启动\figures\22.png)

反馈信息如下：

```bash
Feedback:
    current_pose:
  header:
    stamp:
      sec: 2400
      nanosec: 322000000
    frame_id: map
  pose:
    position:
      x: 2.215651025703489
      y: 0.8998455012894506
      z: 0.009995265644415878
    orientation:
      x: 0.0013824475913305277
      y: 0.0006800653647380359
      z: 0.12035791056717506
      w: 0.9927293688179377
navigation_time:
  sec: 15
  nanosec: 0
estimated_time_remaining:
  sec: 0
  nanosec: 0
number_of_recoveries: 0
distance_remaining: 0.21967321634292603

Result:
    result: {}

Goal finished with status: SUCCEEDED
```

编写`nav2pose.py`实现上述功能

```bash
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.duration import Duration


def main():
    # 节点初始化
    rclpy.init()
    navigator = BasicNavigator()
    # 等待导航启动完成
    navigator.waitUntilNav2Active()
    # 设置目标点坐标
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose.pose.position.x = 3.0
    goal_pose.pose.position.y = 2.0
    goal_pose.pose.orientation.w = 1.0
    # 发送目标接收反馈结果
    navigator.goToPose(goal_pose)
    # 等待导航完成
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()# 获取导航反馈
        navigator.get_logger().info(
            f'预计: {Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9} s 后到达')
        # 超时自动取消
        if Duration.from_msg(feedback.navigation_time) > Duration(seconds=600.0):
            navigator.cancelTask()
    # 最终结果判断
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info('导航结果：成功')
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warn('导航结果：被取消')
    elif result == TaskResult.FAILED:
        navigator.get_logger().error('导航结果：失败')
    else:
        navigator.get_logger().error('导航结果：返回状态无效')

if __name__ == '__main__':
    main()
```



结果如下：

![77044479433](C:\Users\AIPhy\Desktop\ros2启动\figures\23.png)

部分日志

```bash
ros2 run app nav2pose 
[INFO] [1770444725.493806965] [basic_navigator]: Nav2 is ready for use!
[INFO] [1770444725.494500958] [basic_navigator]: Navigating to goal: 3.0 2.0...
[INFO] [1770444725.596935328] [basic_navigator]: 预计: 0.0 s 后到达
[INFO] [1770444725.697630929] [basic_navigator]: 预计: 0.0 s 后到达
[INFO] [1770444726.303088897] [basic_navigator]: 预计: 0.0 s 后到达
[INFO] [1770444726.404134796] [basic_navigator]: 预计: 0.0 s 后到达
[INFO] [1770444726.504992740] [basic_navigator]: 预计: 100.681973601 s 后到达
[INFO] [1770444726.605901125] [basic_navigator]: 预计: 79.979905847 s 后到达
[INFO] [1770444726.707114597] [basic_navigator]: 预计: 29.420197098 s 后到达
[INFO] [1770444726.808149855] [basic_navigator]: 预计: 14.369722743 s 后到达
[INFO] [1770444726.908805215] [basic_navigator]: 预计: 8.000298201 s 后到达
......
```

## 使用接口完成多点导航

查看动作信息

```bash
ros2 action info /follow_waypoints -t [nav2_msgs/action/FollowWaypoints] 
```

详细信息如下：

```bash
 ros2 action info /follow_waypoints -t
Action: /follow_waypoints
Action clients: 1
    /rviz_navigation_dialog_action_client [nav2_msgs/action/FollowWaypoints]
Action servers: 0
```

查看这个消息接口的内容

```bash
ros2 interface show nav2_msgs/action/FollowWaypoints
```

内容如下

```bash
 ros2 interface show nav2_msgs/action/FollowWaypoints
#goal definition
geometry_msgs/PoseStamped[] poses
        std_msgs/Header header
                builtin_interfaces/Time stamp
                        int32 sec
                        uint32 nanosec
                string frame_id
        Pose pose
                Point position
                        float64 x
                        float64 y
                        float64 z
                Quaternion orientation
                        float64 x 0
                        float64 y 0
                        float64 z 0
                        float64 w 1
---
#result definition
int32[] missed_waypoints
---
#feedback definition
uint32 current_waypoint
```

编写`waypoint_flollow.py`

```bash
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.duration import Duration

def main():
    # 节点初始化
    rclpy.init()
    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()
    # 创建点集
    goal_poses = []

    # 添加第一个点
    goal_pose1 = PoseStamped()
    goal_pose1.header.frame_id = 'map'
    goal_pose1.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose1.pose.position.x = 1.0
    goal_pose1.pose.position.y = 1.0
    goal_pose1.pose.orientation.w = 1.0
    goal_poses.append(goal_pose1)

    # 添加第二个点
    goal_pose2 = PoseStamped()
    goal_pose2.header.frame_id = 'map'
    goal_pose2.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose2.pose.position.x = 2.0
    goal_pose2.pose.position.y = 0.0
    goal_pose2.pose.orientation.w = 1.0
    goal_poses.append(goal_pose2)
    
    # 添加第三个点
    goal_pose3 = PoseStamped()
    goal_pose3.header.frame_id = 'map'
    goal_pose3.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose3.pose.position.x = 2.0
    goal_pose3.pose.position.y = 2.0
    goal_pose3.pose.orientation.w = 1.0
    goal_poses.append(goal_pose3)
    
    # 调用路点导航服务
    navigator.followWaypoints(goal_poses)
    # 判断结束及获取反馈
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        navigator.get_logger().info(
            f'当前目标编号：{feedback.current_waypoint}')
    # 最终结果判断
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info('导航结果：成功')
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warn('导航结果：被取消')
    elif result == TaskResult.FAILED:
        navigator.get_logger().error('导航结果：失败')
    else:
        navigator.get_logger().error('导航结果：返回状态无效')

if __name__ == '__main__':
    main()
```

启动

```bash
colcon build
source setup_ros2.sh
ros2 run app waypoint_flollow 
```

![77046437664](C:\Users\AIPhy\Desktop\ros2启动\figures\24.png)

部分日志如下

```bash
ros2 run app waypoint_flollow 
[INFO] [1770464342.785435047] [basic_navigator]: amcl/get_state service not available, waiting...
[INFO] [1770464343.787977930] [basic_navigator]: amcl/get_state service not available, waiting...
[INFO] [1770464346.292236297] [basic_navigator]: Setting initial pose
[INFO] [1770464346.292582027] [basic_navigator]: Publishing Initial Pose
[INFO] [1770464346.293163342] [basic_navigator]: Waiting for amcl_pose to be received
[INFO] [1770464346.293425067] [basic_navigator]: Setting initial pose
[INFO] [1770464346.293612535] [basic_navigator]: Publishing Initial Pose
[INFO] [1770464346.293870304] [basic_navigator]: Waiting for amcl_pose to be received
[INFO] [1770464346.294057948] [basic_navigator]: Setting initial pose
[INFO] [1770464346.294431585] [basic_navigator]: Publishing Initial Pose
[INFO] [1770464346.294648973] [basic_navigator]: Waiting for amcl_pose to be received
[INFO] [1770464352.363999917] [basic_navigator]: Nav2 is ready for use!
[INFO] [1770464352.364844588] [basic_navigator]: Following 3 goals....
[INFO] [1770464352.474859480] [basic_navigator]: 当前目标编号：0
[INFO] [1770464352.575756783] [basic_navigator]: 当前目标编号：0
[INFO] [1770464359.981125827] [basic_navigator]: 当前目标编号：0
[INFO] [1770464360.082816943] [basic_navigator]: 当前目标编号：0
[INFO] [1770464360.183698611] [basic_navigator]: 当前目标编号：0
[INFO] [1770464360.284300862] [basic_navigator]: 当前目标编号：1
[INFO] [1770464367.665401717] [basic_navigator]: 当前目标编号：1
[INFO] [1770464367.766460275] [basic_navigator]: 当前目标编号：1
[INFO] [1770464382.408876133] [basic_navigator]: 当前目标编号：2
[INFO] [1770464382.611066236] [basic_navigator]: 当前目标编号：2
[INFO] [1770464382.711730617] [basic_navigator]: 当前目标编号：2
[INFO] [1770464382.743518010] [basic_navigator]: 导航结果：成功
```





## 编写巡检控制节点

创建功能包

```bash
ros2 pkg create autopartol --build-type ament_python --dependencies rclpy nav2_simple_commander
```

语音合成和图像相关功能包

```bash
sudo apt install python3-pip  -y
sudo apt install espeak-ng -y
sudo pip3 install espeakng
sudo apt install ros-$ROS_DISTRO-tf-transformations
sudo pip3 install transforms3d
```

[启动导航和单点与路点导航 · GitBook](https://bluesnie.github.io/Learning-notes/ROS2/%E4%B8%A4%E8%BD%AE%E5%B7%AE%E9%80%9F%E7%A7%BB%E5%8A%A8%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E7%AF%87/%E7%AC%AC17%E7%AB%A0-%E5%BB%BA%E5%9B%BE%E4%B8%8E%E5%AF%BC%E8%88%AA%E5%AE%9E%E7%8E%B0/navigation/002-%E5%90%AF%E5%8A%A8%E5%AF%BC%E8%88%AA%E5%92%8C%E5%8D%95%E7%82%B9%E4%B8%8E%E8%B7%AF%E7%82%B9%E5%AF%BC%E8%88%AA.html)

创建语音消息接口

```bash
ros2 pkg create autopartol_interfaces  --dependencies rosidl_default_generators
```

删除包中的`include`和`src`文件夹，创建`srv`文件夹

创建`Speech.srv`文件，此文件声明语音播报消息服务接口

```bash
string text    # 合成文字
---
bool result    # 合成结果
```



修改`CMakelists.txt`文件

```bash
# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
rosidl_default_generators(${PROJECT_NAME}
  "srv/Speech.srv"

)
```

修改`package.xml`,声明功能包，大概在最后几行

```bash
  <export>
    <build_type>ament_cmake</build_type>
  </export>
  
  <member_of_group>rosidl_interface_packages</member_of_group>
</package>

```

编写语音合成服务节点

编写`speaker.py`

```bash
import rclpy
from rclpy.node import Node
from autopartol_interfaces.srv import Speech
import espeakng

class Speaker(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        # 创建服务端，服务类型为Speech，服务名称为'speech'，回调函数为self.speak_callback
        self.speech_service = self.create_service(
            Speech, 'speech', self.speak_callback)
        # 创建espeakng对象，设置语音为中文
        self.speaker = espeakng.Speaker()
        self.speaker.voice = 'zh'
        # 日志提示服务端已启动
        self.get_logger().info('服务端已启动，等待客户端请求')  

    # 服务回调函数，用于处理客户端请求
    def speak_callback(self, request, response):
        self.get_logger().info('正在朗读 %s' % request.text)
        self.speaker.say(request.text)# 朗读请求中的文本
        self.speaker.wait()
        response.result = True
        return response


def main(args=None):
    rclpy.init(args=args)
    node = Speaker('speaker')# 创建节点，节点名称为'speaker'
    rclpy.spin(node)
    rclpy.shutdown()
```

启动

```bash
 ros2 run autopartol speaker
```

查看服务列表，是否有Speech的服务

```bash
 ros2 service list
```

部分服务如下

```bash
/speaker/get_parameter_types
/speaker/get_parameters
/speaker/list_parameters
/speaker/set_parameters
/speaker/set_parameters_atomically
/speech
```

调用speech服务

```bash
ros2 service call /speech autopartol_interfaces/srv/Speech "{text: 你好}"
```

另一个终端显示

```bash
 ros2 run autopartol  speaker
[INFO] [1770471132.774105580] [speaker]: 服务端已启动，等待客户端请求
[INFO] [1770471349.163430459] [speaker]: 正在朗读 你好
['espeak-ng', '-v', 'zh', '-s', '175', '-p', '50', '-a', '100', '-g', '0', '你好']

```





编写`partol_node.py`

```bash
import rclpy
from geometry_msgs.msg import PoseStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from rclpy.duration import Duration
# 添加服务接口
from autopatrol_interfaces.srv import SpeachText
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_node'):
        super().__init__(node_name)
        # 导航相关定义
        self.declare_parameter('initial_point', [0.0, 0.0, 0.0]) # 初始位置
        self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57]) # 目标位置
        self.initial_point_ = self.get_parameter('initial_point').value
        self.target_points_ = self.get_parameter('target_points').value

        # 实时位置获取 TF 相关定义
        self.buffer_ = Buffer()
        self.listener_ = TransformListener(self.buffer_, self)
        self.speach_client_ = self.create_client(SpeachText, 'speech_text')

        # 订阅与保存图像相关定义
        self.declare_parameter('image_save_path', '')
        self.image_save_path = self.get_parameter('image_save_path').value
        self.bridge = CvBridge()
        self.latest_image = None
        self.subscription_image = self.create_subscription(
            Image, '/camera_sensor/image_raw', self.image_callback, 10)

    def image_callback(self, msg):
        """
        将最新的消息放到 latest_image 中
        """
        self.latest_image = msg

    def record_image(self):
        """
        记录图像
        """
        if self.latest_image is not None:
          pose = self.get_current_pose()
          cv_image = self.bridge.imgmsg_to_cv2(self.latest_image)
          cv2.imwrite(f'{self.image_save_path}image_{pose.translation.x:3.2f}_{pose.translation.y:3.2f}.png', cv_image)


    def speach_text(self, text):
        """
        调用服务播放语音
        """
        while not self.speach_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('语合成服务未上线，等待中。。。')

        request = SpeachText.Request()
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
        """
        通过 x,y,yaw 合成 PoseStamped
        """
        pose = PoseStamped()  # 创建位姿消息
        pose.header.frame_id = 'map' # 位姿参考坐标系
        pose.pose.position.x = x # 位姿 x 坐标
        pose.pose.position.y = y # 位姿 y 坐标
        # 欧拉角转换为四元数
        rotation_quat = quaternion_from_euler(0, 0, yaw)
        pose.pose.orientation.x = rotation_quat[0]
        pose.pose.orientation.y = rotation_quat[1]
        pose.pose.orientation.z = rotation_quat[2]
        pose.pose.orientation.w = rotation_quat[3]
        return pose # 返回位姿

    def init_robot_pose(self):
        """
        初始化机器人位姿
        """
        # 从参数获取初始化点
        self.initial_point_ = self.get_parameter('initial_point').value
        # 合成位姿并进行初始化
        self.setInitialPose(self.get_pose_by_xyyaw(
            self.initial_point_[0], self.initial_point_[1], self.initial_point_[2]))
        # 等待直到导航激活
        self.waitUntilNav2Active()

    def get_target_points(self):
        """
        通过参数值获取目标点集合        
        """
        points = []
        self.target_points_ = self.get_parameter('target_points').value
        for index in range(int(len(self.target_points_)/3)):
            x = self.target_points_[index*3]
            y = self.target_points_[index*3+1]
            yaw = self.target_points_[index*3+2]
            points.append([x, y, yaw])
            self.get_logger().info(f'获取到目标点: {index}->({x},{y},{yaw})')
        return points

    def nav_to_pose(self, target_pose):
        """
        导航到指定位姿
        """
        self.waitUntilNav2Active()
        result = self.goToPose(target_pose)
        while not self.isTaskComplete():
            feedback = self.getFeedback()
            if feedback:
                self.get_logger().info(f'预计: {Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9} s 后到达')
        # 最终结果判断
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
        """
        通过TF获取当前位姿
        """
        while rclpy.ok():
            try:
                tf = self.buffer_.lookup_transform(
                    'map', 'base_footprint', rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
                transform = tf.transform
                rotation_euler = euler_from_quaternion([
                    transform.rotation.x,
                    transform.rotation.y,
                    transform.rotation.z,
                    transform.rotation.w
                ])
                self.get_logger().info(
                    f'平移:{transform.translation},旋转四元数:{transform.rotation}:旋转欧拉角:{rotation_euler}')
                return transform
            except Exception as e:
                self.get_logger().warn(f'不能够获取坐标变换，原因: {str(e)}')
    
def main():
    rclpy.init()
    patrol = PatrolNode()
    patrol.speach_text(text='正在初始化位置')
    patrol.init_robot_pose()
    patrol.speach_text(text='位置初始化完成')

    while rclpy.ok():
        for point in patrol.get_target_points():
            x, y, yaw = point[0], point[1], point[2]
            # 导航到目标点
            target_pose = patrol.get_pose_by_xyyaw(x, y, yaw)
            patrol.speach_text(text=f'准备前往目标点{x},{y}')
            patrol.nav_to_pose(target_pose)
            patrol.speach_text(text=f"已到达目标点{x},{y},准备记录图像")
            patrol.record_image()
            patrol.speach_text(text=f"图像记录完成")
    rclpy.shutdown()

if __name__ == '__main__':
    main()

```

启动

```bash
ros2 run autopartol partol_node --ros-args --param-file /home/qinghe/ros2_ws/src/autopartol/config/partol_config.yaml
```



自动生成配置文件

```bash
ros2 param dump /partol_node
```

修改配置文件，设置导航点

```bash
patrol_node:
  ros__parameters:
    initial_point: [0.0, 0.0, 0.0]
    target_points: [
      0.0, 0.0, 0.0,
      1.0, 0.0, 3.14,
      1.0, 1.0, 1.57,
      0.0, 0.0, 1.57,
      1.5, 1.5, 3.14
      ]
```

编写`autopartol.launch.py`

```bash

```



修改`setup.py`

```bash
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/partol_config.yaml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.py')),

    ],  
```

启动

```bash
colcon build
source setup_ros2.sh

```

安装图片相关包

```bash
sudo apt install ros-$ROS_DISTRO-tf-transformations
sudo pip3 install transforms3d
```



[turtlebot3/turtlebot3_example/turtlebot3_example at main · ROBOTIS-GIT/turtlebot3](https://github.com/ROBOTIS-GIT/turtlebot3/tree/main/turtlebot3_example/turtlebot3_example)







## URDF

生成urdf文件

```bash
urdf_to_graphviz car.urdf 
```

![77425590610](figures\26.png)