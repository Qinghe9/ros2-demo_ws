from setuptools import setup
import os
from glob import glob

package_name = 'bt_package'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        # 安装package.xml
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 安装BT XML文件到share目录
        (os.path.join('share', package_name, 'resource'), 
         glob('resource/*.xml')),
        # 安装launch文件到share目录
        (os.path.join('share', package_name, 'launch'), 
         glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='Custom BT package for Nav2 waypoint navigation',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'bt_navigator = bt_package.bt_navigator:main',   
        'waypoint_follow = bt_package.waypoint_follow:main',
        'set_init_pose = bt_package.set_init_pose:main',
        'industrial_patrol_bt = bt_package.waypoint_follow:main',
    ],
},
)