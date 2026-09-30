from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    declared_arguments = []
    declared_env_vars = []
    declared_parameters = []

    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    start_rsp = LaunchConfiguration("start_rsp")

    declared_arguments.append(
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(
                get_package_share_directory("ira_laser_tools"),
                "config",
                "laserscan_merge.yaml",
            ),
            description="Path to param config in yaml format",
        ),
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation (Gazebo) clock",
        ),
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "start_rsp",
            default_value="true",
            description="Launch robot_state_publisher + joint_state_publisher. "
                        "Set false when another node (e.g. Gazebo) already owns the robot model.",
        ),
    )

    laser_merge = Node(
        package="ira_laser_tools",
        executable="laserscan_multi_merger",
        name="laserscan_multi_merger",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
    )

    display_launch_file = os.path.join(
        get_package_share_directory('M3Pro'),
        'launch',
        'display.launch.py'
    )

    nodes = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(display_launch_file),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
            condition=IfCondition(start_rsp),
        ),
        laser_merge,
    ]

    return LaunchDescription(
        declared_parameters + declared_arguments + declared_env_vars + nodes
    )
