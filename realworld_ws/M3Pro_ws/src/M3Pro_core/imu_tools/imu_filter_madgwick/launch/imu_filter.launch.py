import os
import launch
import launch.actions
import launch.substitutions
import launch_ros.actions
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    config_dir = os.path.join(get_package_share_directory('imu_filter_madgwick'), 'config')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return launch.LaunchDescription(
        [
            DeclareLaunchArgument(
                'use_sim_time',
                default_value='false',
                description='Use simulation (Gazebo) clock',
            ),
            launch_ros.actions.Node(
                package='imu_filter_madgwick',
                executable='imu_filter_madgwick_node',
                name='imu_filter',
                output='screen',
                parameters=[
                    os.path.join(config_dir, 'imu_filter.yaml'),
                    {'use_sim_time': use_sim_time},
                ],
                remappings=[('/imu','/imu/data_raw')]
            )
        ]
    )
