from setuptools import setup


package_name = 'anomaly_detection'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kuhnhero',
    maintainer_email='todo@todo.com',
    description='ROS 2 wrapper for location-specific anomalous sound detection',
    license='MIT',
    entry_points={
        'console_scripts': [
            'anomaly_detector = anomaly_detection.anomaly_detector_node:main',
        ],
    },
)