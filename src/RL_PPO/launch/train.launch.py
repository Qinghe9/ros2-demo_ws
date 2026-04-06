"""Launch file for PPO Training."""

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
            executable='train_node',
            name='ppo_trainer',
            output='screen',
            parameters=[
                config_file,
                {
                    'total_episodes': 1000,
                    'max_steps_per_episode': 500,
                    'batch_size': 64,
                    'update_epochs': 10,
                    'save_interval': 100,
                }
            ]
        )
    ])