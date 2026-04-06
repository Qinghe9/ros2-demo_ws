#!/usr/bin/env python3
"""
工业级三点巡航行为树启动文件
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """生成启动描述"""
    
    # 获取包路径
    bt_package_share = get_package_share_directory('bt_package')
    student_kit_share = get_package_share_directory('student_starter_kit')
    
    # 行为树 XML 文件路径
    bt_xml_path = os.path.join(bt_package_share, 'resource', 'forward_behavior_tree1.xml')
    
    # 参数声明
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )
    
    enable_groot_monitor_arg = DeclareLaunchArgument(
        'enable_groot_monitor',
        default_value='true',
        description='Enable Groot Monitor'
    )
    
    groot_port_arg = DeclareLaunchArgument(
        'groot_port',
        default_value='1666',
        description='Groot Monitor TCP port'
    )
    
    # 启动导航（包含 Nav2）
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(student_kit_share, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }.items()
    )
    
    # 启动行为树节点
    bt_node = Node(
        package='bt_package',
        executable='industrial_patrol_bt',
        name='industrial_patrol_bt',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'bt_xml_file': bt_xml_path,
            'enable_groot_monitor': LaunchConfiguration('enable_groot_monitor'),
            'groot_port': LaunchConfiguration('groot_port')
        }]
    )
    
    # 启动 Groot Monitor 节点（可选）
    groot_monitor_node = Node(
        package='bt_package',
        executable='groot_monitor',
        name='groot_monitor',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'monitor_port': LaunchConfiguration('groot_port')
        }],
        condition=IfCondition(LaunchConfiguration('enable_groot_monitor'))
    )
    
    return LaunchDescription([
        use_sim_time_arg,
        enable_groot_monitor_arg,
        groot_port_arg,
        navigation_launch,
        bt_node,
        groot_monitor_node
    ])