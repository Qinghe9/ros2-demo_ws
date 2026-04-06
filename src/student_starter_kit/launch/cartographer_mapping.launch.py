#!/usr/bin/env python3
"""
Launch file for automatic mapping using Cartographer SLAM with Gazebo simulation
Integrates turtlebot3_waffle in Gazebo with Cartographer for SLAM
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package directories
    turtlebot3_cartographer_share = get_package_share_directory('turtlebot3_cartographer')
    pkg_share = get_package_share_directory('student_starter_kit')
    turtlebot3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    
    # Paths
    world_file = os.path.join(pkg_share, 'worlds', 'test.world')
    
    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    
    # Cartographer configuration from turtlebot3_cartographer package
    cartographer_config_dir = LaunchConfiguration('cartographer_config_dir', default=os.path.join(
                                                  turtlebot3_cartographer_share, 'config'))
    configuration_basename = LaunchConfiguration('configuration_basename',
                                                 default='turtlebot3_lds_2d.lua')

    resolution = LaunchConfiguration('resolution', default='0.05')
    publish_period_sec = LaunchConfiguration('publish_period_sec', default='1.0')

    # RViz configuration from student_starter_kit package (with RobotModel enabled)
    rviz_config_dir = os.path.join(pkg_share, 'rviz', 'my_rviz.rviz')
    
    # Set TURTLEBOT3_MODEL environment variable
    turtlebot3_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle')
    
    # Set Gazebo model path to include turtlebot3 models
    turtlebot3_gazebo_models = os.path.join(turtlebot3_gazebo_share, 'models')
    gazebo_model_path = SetEnvironmentVariable(
        'GAZEBO_MODEL_PATH',
        turtlebot3_gazebo_models + ':' + os.environ.get('GAZEBO_MODEL_PATH', '')
    )

    return LaunchDescription([
        # Environment variables
        turtlebot3_model,
        gazebo_model_path,
        
        # Launch arguments
        DeclareLaunchArgument(
            'world',
            default_value=world_file,
            description='Path to world file'),
        DeclareLaunchArgument(
            'cartographer_config_dir',
            default_value=cartographer_config_dir,
            description='Full path to config file to load'),
        DeclareLaunchArgument(
            'configuration_basename',
            default_value=configuration_basename,
            description='Name of lua file for cartographer'),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Use RViz if true'),
        DeclareLaunchArgument(
            'x_pose',
            default_value='0.0',
            description='X position of robot'),
        DeclareLaunchArgument(
            'y_pose',
            default_value='0.0',
            description='Y position of robot'),
        DeclareLaunchArgument(
            'resolution',
            default_value=resolution,
            description='Resolution of a grid cell in the published occupancy grid'),
        DeclareLaunchArgument(
            'publish_period_sec',
            default_value=publish_period_sec,
            description='OccupancyGrid publishing period'),
        
        # Gazebo server with custom world
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_ros_share, 'launch', 'gzserver.launch.py')
            ),
            launch_arguments={
                'world': LaunchConfiguration('world')
            }.items()
        ),
        
        # Gazebo client
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_ros_share, 'launch', 'gzclient.launch.py')
            )
        ),
        
        # Robot state publisher from turtlebot3_gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(turtlebot3_gazebo_share, 'launch', 'robot_state_publisher.launch.py')
            ),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }.items()
        ),
        
        # Spawn turtlebot3_waffle in Gazebo with delay
        TimerAction(
            period=5.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(turtlebot3_gazebo_share, 'launch', 'spawn_turtlebot3.launch.py')
                    ),
                    launch_arguments={
                        'x_pose': LaunchConfiguration('x_pose'),
                        'y_pose': LaunchConfiguration('y_pose')
                    }.items()
                )
            ]
        ),

        # Cartographer SLAM node
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=['-configuration_directory', cartographer_config_dir,
                       '-configuration_basename', configuration_basename]),

        # Cartographer occupancy grid node
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.dirname(os.path.abspath(__file__)), '/occupancy_grid.launch.py']),
            launch_arguments={'use_sim_time': use_sim_time, 'resolution': resolution,
                              'publish_period_sec': publish_period_sec}.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(use_rviz),
            output='screen'),
    ])