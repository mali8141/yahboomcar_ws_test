from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
import os


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')

    # When use_sim_time is true, the digitaltwin's Gazebo stack already owns
    # robot_state_publisher / joint_state_publisher via gazebo_display.launch.py.
    # Suppress them inside the laser merger sub-launch to avoid duplicate RSP.
    start_rsp = PythonExpression(
        ["'false' if '", use_sim_time, "' == 'true' else 'true'"]
    )

    ekf_yaml = os.path.join(
        get_package_share_directory('ekf_bringup'),
        'params',
        'yahboom_M3Pro_ekf.yaml',
    )

    laser_merge_launch_file = os.path.join(
        get_package_share_directory('ira_laser_tools'),
        'launch',
        'merge_multi.launch.py',
    )

    laser_filter_launch_file = os.path.join(
        get_package_share_directory('yahboom_laser_filter'),
        'launch',
        'laser_filter_node.launch.py',
    )

    # ------------------------------------------------------------------ #
    # IMU filter                                                           #
    # Converts /imu/data_raw → /imu/data for the EKF.                    #
    # Hardware: micro-ROS publishes /imu/data_raw directly.               #
    # Sim:      Gazebo bridges its IMU as /imu/data_raw (matching hw).    #
    # ------------------------------------------------------------------ #
    imu_filter_madgwick_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_madgwick_node',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ------------------------------------------------------------------ #
    # EKF                                                                  #
    # Fuses /odom_raw + /imu/data → /odometry/filtered (remapped → /odom) #
    # and broadcasts odom → base_footprint TF.                            #
    # Hardware: /odom_raw from wheel encoders via micro-ROS.              #
    # Sim:      /odom_raw from Gazebo diff-drive bridge (same topic name). #
    # ------------------------------------------------------------------ #
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            ekf_yaml,
            {'use_sim_time': use_sim_time},
        ],
        remappings=[('/odometry/filtered', '/odom')],
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock',
        ),

        imu_filter_madgwick_node,
        ekf_node,

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

    ])
