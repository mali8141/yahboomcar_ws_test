import os
import re

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')

    pkg_path = get_package_share_directory('yahboom_M3Pro_description')
    urdf_file = os.path.join(pkg_path, 'urdf', 'M3Pro.urdf')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    # Strip the <?xml ... ?> declaration — lxml (used by spawn_entity.py
    # downstream) refuses to parse a Python string that still has an
    # encoding declaration in it.
    robot_description = re.sub(r'^\s*<\?xml.*?\?>\s*', '', robot_description, count=1)

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time
        }]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),

        node_robot_state_publisher
    ])