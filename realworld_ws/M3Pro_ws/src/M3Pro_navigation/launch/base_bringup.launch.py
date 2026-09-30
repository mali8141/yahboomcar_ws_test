import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    # When use_sim_time is true, the sim's Gazebo stack already owns RSP/JSP.
    start_rsp = PythonExpression(
        ["'false' if '", use_sim_time, "' == 'true' else 'true'"]
    )

    laser_merge_launch_file = os.path.join(
        get_package_share_directory('ira_laser_tools'),
        'launch',
        'merge_multi.launch.py'
    )
    laser_filter_launch_file = os.path.join(
        get_package_share_directory('yahboom_laser_filter'),
        'launch',
        'laser_filter_node.launch.py'
    )

    imu_filter_madgwick_launch_file = os.path.join(
        get_package_share_directory('imu_filter_madgwick'),
        'launch',
        'imu_filter.launch.py'
    )

    ekf_odom_launch_file = os.path.join(
        get_package_share_directory('ekf_bringup'),
        'launch',
        'ekf.launch.py'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true',
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(imu_filter_madgwick_launch_file),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(laser_merge_launch_file),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'start_rsp': start_rsp,
            }.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(laser_filter_launch_file),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

        # ekf: fuses odom_raw + imu → /odom and broadcasts odom→base_footprint TF
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(ekf_odom_launch_file),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

    ])














