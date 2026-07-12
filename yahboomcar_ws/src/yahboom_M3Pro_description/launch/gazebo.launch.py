import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('yahboom_M3Pro_description')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    default_model_path = os.path.join(pkg_description, 'urdf', 'M3Pro.urdf')

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=default_model_path,
        description='Absolute path to robot urdf/xacro file'
    )

    # Turns the urdf (via xacro) into the robot_description parameter
    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]),
        value_type=str
    )

    # Publishes /tf and /robot_description so Gazebo + RViz can see the model
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    # Starts gzserver + gzclient (the actual Gazebo simulator + GUI)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        )
    )

    # Spawns the robot model described on /robot_description into the running world
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'M3Pro', '-z', '0.05'],
        output='screen'
    )

    return LaunchDescription([
        model_arg,
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
    ])