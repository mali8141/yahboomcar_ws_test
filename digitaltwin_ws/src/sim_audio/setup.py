from setuptools import find_packages, setup

package_name = 'sim_audio'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='WISES',
    maintainer_email='todo@todo.com',
    description='Simulated audio field tools for the Gazebo digital twin.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'audio_field_builder = sim_audio.audio_field_builder:main',
            'sim_audio_publisher  = sim_audio.sim_audio_publisher:main',
            'view_audio_field     = sim_audio.view_audio_field:main',
        ],
    },
)
