import os
import re
import xacro

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')

    pkg_path = get_package_share_directory('yahboom_M3Pro_description')
    xacro_file = os.path.join(pkg_path, 'urdf', 'M3Pro.urdf.xacro')

    robot_description_config = xacro.process_file(xacro_file)
    robot_description = robot_description_config.toxml()

    # Strip XML comments — gazebo_ros2_control re-passes robot_description
    # as a "--param" override internally, and embedded "--" sequences
    # inside <!-- ... --> comments break its argument parser.
    robot_description = re.sub(r'<!--.*?-->', '', robot_description, flags=re.DOTALL)

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