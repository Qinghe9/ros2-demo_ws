#!/usr/bin/env python3
"""
Launch file for Gazebo simulation with TurtleBot3 and custom demo world
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package directories
    pkg_share = get_package_share_directory('student_starter_kit')
    turtlebot3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    
    # Paths
    world_file = os.path.join(pkg_share, 'worlds', 'test.world')
    
    # Set TURTLEBOT3_MODEL environment variable
    turtlebot3_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle')
    
    # Set Gazebo model path to include turtlebot3 models
    turtlebot3_gazebo_models = os.path.join(turtlebot3_gazebo_share, 'models')
    gazebo_model_path = SetEnvironmentVariable(
        'GAZEBO_MODEL_PATH',
        turtlebot3_gazebo_models + ':' + os.environ.get('GAZEBO_MODEL_PATH', '')
    )
    
    # Launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=world_file,
        description='Path to world file'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )
    
    x_pose_arg = DeclareLaunchArgument(
        'x_pose',
        default_value='0.0',
        description='X position of robot'
    )
    
    y_pose_arg = DeclareLaunchArgument(
        'y_pose',
        default_value='0.0',
        description='Y position of robot'
    )
    
    # Gazebo server with custom world
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={
            'world': LaunchConfiguration('world')
        }.items()
    )
    
    # Gazebo client
    gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gzclient.launch.py')
        )
    )
    
    # Robot state publisher from turtlebot3_gazebo
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo_share, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }.items()
    )
    
    # Spawn turtlebot3_waffle in Gazebo
    spawn_turtlebot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo_share, 'launch', 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': LaunchConfiguration('x_pose'),
            'y_pose': LaunchConfiguration('y_pose')
        }.items()
    )
    
    # Delay spawn to wait for Gazebo to be fully ready
    delayed_spawn = TimerAction(
        period=5.0,
        actions=[spawn_turtlebot]
    )
    
    # Launch depth camera node
    depth_camera_node = Node(
        package='depth_image_proc',
        executable='point_cloud_xyzrgb_node',
        name='depth_image_proc',
        remappings=[
                ('rgb/camera_info', '/camera/camera_info'),
                ('rgb/image_rect_color', '/camera/image_raw'),
                ('depth/image_rect', '/camera/depth/image_raw'),
                ('points', '/camera/point_cloud')
            ],
        parameters=[
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
                {'qos_overrides./camera/point_cloud.publisher.reliability': 'reliable'},
                {'qos_overrides./camera/point_cloud.publisher.history': 'keep_last'},
                {'qos_overrides./camera/point_cloud.publisher.depth': 10},
                {'qos_overrides./camera/depth/image_raw.subscription.reliability': 'reliable'},
                {'qos_overrides./camera/image_raw.subscription.reliability': 'reliable'},
                {'qos_overrides./camera/camera_info.subscription.reliability': 'reliable'}
            ]
    )

    return LaunchDescription([
        turtlebot3_model,
        gazebo_model_path,
        world_arg,
        use_sim_time_arg,
        x_pose_arg,
        y_pose_arg,
        gazebo_server,
        gazebo_client,
        robot_state_publisher,
        delayed_spawn,
        depth_camera_node,
    ])