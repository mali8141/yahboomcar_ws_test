import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'M3Pro'

    package_share = get_package_share_directory(package_name)

    # Change this filename if your main Xacro has another name.
    xacro_file = os.path.join(
        package_share,
        'urdf',
        'M3Pro.gazebo.xacro'
    )

    robot_description = xacro.process_file(
        xacro_file
    ).toxml()

    gazebo = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            '-s',
            'libgazebo_ros_factory.so'
        ],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                name='spawn_m3pro',
                output='screen',
                arguments=[
                    '-topic',
                    'robot_description',
                    '-entity',
                    'm3pro',
                    '-x',
                    '0.0',
                    '-y',
                    '0.0',
                    '-z',
                    '0.15'
                ]
            )
        ]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot
    ])