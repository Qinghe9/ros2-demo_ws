#!/usr/bin/env python3
"""
Launch file for navigation using pre-built map
Integrates turtlebot3_waffle in Gazebo with Nav2 navigation stack
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package directories
    pkg_share = get_package_share_directory('student_starter_kit')
    turtlebot3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    nav2_share = get_package_share_directory('nav2_bringup')
    
    # Paths
    world_file = os.path.join(pkg_share, 'worlds', 'test.world')
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'my_rviz.rviz')
    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    map_file = os.path.join(pkg_share, 'maps', '0319map.yaml')
    
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
    
    resolution_arg = DeclareLaunchArgument(
        'resolution',
        default_value='0.05',
        description='Resolution of a grid cell in the published occupancy grid'
    )
    
    publish_period_sec_arg = DeclareLaunchArgument(
        'publish_period_sec',
        default_value='1.0',
        description='OccupancyGrid publishing period'
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
    
    # Spawn turtlebot3_waffle in Gazebo with delay
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
    
    # Localization with map server and AMCL
    localization_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, 'launch', 'localization_launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': nav2_params_file,
            'map': map_file
        }.items()
    )
    
    # Navigation stack
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': nav2_params_file
        }.items()
    )
    
    # Delay localization to wait for Gazebo and robot to be ready
    delayed_localization = TimerAction(
        period=10.0,
        actions=[localization_bringup]
    )
    
    # Delay Nav2 to wait for localization to be ready
    delayed_nav2 = TimerAction(
        period=15.0,
        actions=[nav2_bringup]
    )
    
    # RViz with Nav2 configuration
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )
    
    # Delay RViz to allow TF to stabilize
    delayed_rviz = TimerAction(
        period=3.0,
        actions=[rviz_node]
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
        delayed_localization,
        delayed_nav2,
        delayed_rviz,
    ])

