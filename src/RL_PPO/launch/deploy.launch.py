"""Launch file for PPO Navigation Deployment."""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('RL_PPO')
    config_file = os.path.join(pkg_share, 'config', 'ppo_config.yaml')
    
    return LaunchDescription([
        Node(
            package='RL_PPO',
            executable='deploy_node',
            name='ppo_navigation_node',
            output='screen',
            parameters=[
                config_file,
                {
                    'model_path': os.path.join(pkg_share, 'models', 'ppo_model_final.pt'),
                    'max_linear_vel': 0.5,
                    'max_angular_vel': 1.0,
                    'goal_tolerance': 0.5,
                }
            ]
        )
    ])