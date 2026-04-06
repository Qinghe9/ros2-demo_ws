"""Launch file for PPO Training with TensorBoard support."""

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
                    'total_episodes': 2000,
                    'max_steps_per_episode': 500,
                    'batch_size': 128,
                    'update_epochs': 10,
                    'save_interval': 50,
                    'log_interval': 10,
                }
            ]
        )
    ])