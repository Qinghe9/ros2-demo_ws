from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bt_tree_dir = get_package_share_directory('bt_tree')
    bt_xml_file = os.path.join(bt_tree_dir, 'behavior_trees', 'navigate_to_pose.xml')
    
    # 使用 student_starter_kit 包中的地图
    map_file = '/home/qinghe/ros2-demo_ws/src/student_starter_kit/maps/0319map.yaml'
    
    return LaunchDescription([
        Node(
            package='bt_tree',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[
                {'bt_xml_file': bt_xml_file},
                {'max_ticks': 100},
                {'tick_interval_ms': 100},
                {'map': map_file}
            ]
        )
    ])