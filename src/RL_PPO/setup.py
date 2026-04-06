from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'RL_PPO'

data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
]

dirs_to_install = ['launch', 'config']
for dir_name in dirs_to_install:
    abs_dir = os.path.join(os.path.dirname(__file__), dir_name)
    if os.path.isdir(abs_dir):
        files = glob(os.path.join(abs_dir, '**', '*'), recursive=True)
        for file in files:
            if os.path.isfile(file):
                rel_path = os.path.relpath(file, os.path.dirname(__file__))
                dest_dir = os.path.join('share', package_name, os.path.dirname(rel_path))
                data_files.append((dest_dir, [file]))

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools', 'numpy>=1.23', 'torch', 'gymnasium', 'matplotlib'],
    zip_safe=True,
    maintainer='Qinghe',
    maintainer_email='3065256767@qq.com',
    description='PPO-based Reinforcement Learning Navigation Algorithm',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'train_node = RL_PPO.trainer:main',
            'deploy_node = RL_PPO.deploy_node:main',
        ],
    },
)