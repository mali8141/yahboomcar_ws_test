from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock',
        ),
        Node(
            package='yahboom_laser_filter',
            executable='laser_filter_node',
            name='laser_filter_node',
            parameters=[
                {'angle_min': -180.0, 'angle_max': 180.0},
                {'use_sim_time': use_sim_time},
            ],
        ),
    ])
