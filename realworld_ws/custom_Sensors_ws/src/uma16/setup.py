from setuptools import find_packages, setup

package_name = 'uma16'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data={
            'uma16_acoustic_overlay': ['config/*.xml'],
        },
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sir Kuhnhero',
    maintainer_email='',
    description='contains a number of ROS2 nodes for the UMA16v2 microphone array',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'stream_publisher = uma16_audio_publisher.uma16_audio_publisher:main',
            'stream_recorder = uma16_topic_recorder.uma16_topic_recorder:main',
            'acoustic_overlay = uma16_acoustic_overlay.uma16_acoustic_overlay:main',
            'standalone_recorder = standalone_recorder.recorder:main',
        ],
    },
)
