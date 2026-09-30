from setuptools import find_packages, setup

package_name = 'audio_map'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kuhnhero',
    maintainer_email='',
    description='Audio mapping layer for SLAM comparison',
    license='MIT',
    entry_points={
        'console_scripts': [
            'audio_mapper = audio_map.audio_mapper_node:main',
            'audio_recording_trigger = audio_map.audio_recording_trigger:main',
        ],
    },
)
