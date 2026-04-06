import os
from sys import set_int_max_str_digits
from numpy import safe_eval
from setuptools import find_packages, setup

package_name = 'student_starter_kit'

data_files = [
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
]

# Add directories to data_files
dirs_to_install = ['urdf', 'meshes', 'launch', 'rviz', 'worlds', 'config', 'script', 'maps']
for dir_name in dirs_to_install:
    # Get absolute path to the directory
    abs_dir = os.path.join(os.path.dirname(__file__), dir_name)
    if os.path.isdir(abs_dir):
        # Get all files in the directory
        import glob
        files = glob.glob(abs_dir + '/**/*', recursive=True)
        if files:
            # For each file, add it to data_files
            for file in files:
                # Skip directories, only add files
                if not os.path.isfile(file):
                    continue
                # Get relative path from package root
                rel_path = os.path.relpath(file, os.path.dirname(__file__))
                # Create destination directory
                dest_dir = 'share/' + package_name + '/' + os.path.dirname(rel_path)
                data_files.append((dest_dir, [file]))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']) + ['script'],
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Qinghe',
    maintainer_email='3065256767@qq.com',
    description='python demo pkg',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'smart_explor = script.smart_explor:main',
            'init_pose = script.init_pose:main',
            'get_pose = script.get_pose:main',
            'nav2pose = script.nav2pose:main',
            'waypoint_flollow = script.waypoint_flollow:main',
            'automatic_mapping = script.automatic_mapping:main',
            
        ],
    },
)