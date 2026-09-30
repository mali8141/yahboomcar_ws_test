import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'sensor_module'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sir Kuhnhero',
    maintainer_email='robin@markand.de',
    description='ROS2 node that reads sensor data from the SensorModule MCU over serial.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'sensor_publisher = sensor_module.sensor_publisher:main',
        ],
    },
)
