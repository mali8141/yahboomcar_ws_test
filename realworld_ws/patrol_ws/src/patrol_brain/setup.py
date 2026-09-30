from setuptools import find_packages, setup

package_name = 'patrol_brain'

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
    maintainer='kuhnhero',
    maintainer_email='todo@todo.com',
    description='Local HTTP API for Nav2 goals and robot pose lookup.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'patrol_brain = patrol_brain.patrol_brain_node:main',
        ],
    },
)
