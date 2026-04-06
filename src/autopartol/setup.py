from setuptools import find_packages, setup
import glob

package_name = 'autopartol'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('autopartol/launch/*.launch.py')),
        ('share/' + package_name + '/config', ['config/partol_config.yaml']),
    
    ],  
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='airsim',
    maintainer_email='airsim@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'partol_node = autopartol.partol_node:main',
            'speaker = autopartol.speaker:main',
        ],
    },
)
