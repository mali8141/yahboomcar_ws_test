from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('port',     default_value='/dev/ttyUSB0',       description='Serial port of the MCU'),
        DeclareLaunchArgument('baud',     default_value='9600',                description='Serial baud rate'),
        DeclareLaunchArgument('topic',    default_value='/sensor_module/data', description='ROS2 topic to publish on'),
        DeclareLaunchArgument('rate_hz',  default_value='10.0',                description='Publish rate in Hz'),

        Node(
            package='sensor_module',
            executable='sensor_publisher',
            name='sensor_publisher',
            output='screen',
            parameters=[{
                'port':    LaunchConfiguration('port'),
                'baud':    LaunchConfiguration('baud'),
                'topic':   LaunchConfiguration('topic'),
                'rate_hz': LaunchConfiguration('rate_hz'),
            }],
        ),
    ])
