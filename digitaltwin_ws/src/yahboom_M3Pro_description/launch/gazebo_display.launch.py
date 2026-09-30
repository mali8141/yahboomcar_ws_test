import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_path = get_package_share_directory('yahboom_M3Pro_description')
    world_path = os.path.join(pkg_path, 'worlds', 'maze_visualFeatures.world')

    gui        = LaunchConfiguration('gui')
    bridge_tf  = LaunchConfiguration('bridge_tf')
    world_name = LaunchConfiguration('world_name')


    share_parent = os.path.dirname(pkg_path)
    existing_resource_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=share_parent + (':' + existing_resource_path if existing_resource_path else '')
    )

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_path, 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    gz_sim_headless = ExecuteProcess(
        cmd=['gz', 'sim', '-r', '--headless-rendering', '-s', world_path],
        output='screen',
        condition=UnlessCondition(gui),
    )

    gz_sim_gui = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        output='screen',
        condition=IfCondition(gui),
    )

    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-topic', 'robot_description',
                    '-name', 'M3Pro',
                    '-z', '0.05',
                ],
                output='screen',
            )
        ]
    )
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            # Publish on /odom_raw so realworld_ws bringup EKF reads it directly,
            # matching what the physical robot's wheel encoder driver publishes.
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan0@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/scan1@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # IMU raw data: bridge as /imu/data_raw so imu_filter_madgwick in
            # bringup can process it identically to the physical hardware path.
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # Camera info (non-image; parameter_bridge handles this type)
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            # Ground-truth pose from model-level PosePublisher plugin.
            '/model/M3Pro/pose@geometry_msgs/msg/Pose[gz.msgs.Pose',
        ],
        remappings=[
            ('/odom',              '/odom_raw'),
            ('/imu',               '/imu/data_raw'),
            ('/camera/camera_info', '/camera/color/camera_info'),
        ],
        output='screen',
    )

    # Bridge Gazebo's TF tree (odom->base_footprint + wheel joint transforms
    # published by the DiffDrive plugin) into ROS2 /tf.
    #
    # MUST be disabled (bridge_tf:=false) when running as a backend for
    # realworld_ws: the real robot's ekf_filter_node owns odom->base_footprint,
    # and a second publisher on that frame causes localization to jump.
    #
    # Sim-only pipelines (run_lidar_pipeline.sh, run_navigation_pipeline.sh)
    # leave this at the default (true) so wheel and camera transforms resolve.
    bridge_tf_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_tf',
        arguments=['/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'],
        output='screen',
        condition=IfCondition(bridge_tf),
    )

    # ros_gz_image bridges raw image topics (parameter_bridge cannot handle Image)
    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=[
            '/camera/image',        # → /camera/color/image_raw (remapped below)
            '/camera/depth_image',  # → /camera/depth/image_raw (remapped below)
        ],
        remappings=[
            ('/camera/image',       '/camera/color/image_raw'),
            ('/camera/depth_image', '/camera/depth/image_raw'),
        ],
        output='screen',
    )


    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # Gazebo Harmonic names sensor frames as <model>/<link>/<sensor> in the
    # bridged message headers, but robot_state_publisher uses the URDF link
    # names.  Publish identity transforms so the laser merger (and any other
    # consumer) can resolve the Gazebo frame names through the URDF TF tree.
    laser0_frame_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='laser0_frame_alias',
        arguments=['--frame-id', 'laser0_frame',
                   '--child-frame-id', 'M3Pro/base_footprint/laser0'],
        parameters=[{'use_sim_time': True}],
    )

    laser1_frame_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='laser1_frame_alias',
        arguments=['--frame-id', 'laser1_frame',
                   '--child-frame-id', 'M3Pro/base_footprint/laser1'],
        parameters=[{'use_sim_time': True}],
    )

    # Gazebo names the RGBD sensor frame as <model>/<link>/<sensor>.
    # Alias it to the URDF optical frame so image consumers can resolve TF.
    camera_frame_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_frame_alias',
        arguments=['--frame-id', 'camera_color_optical_frame',
                   '--child-frame-id', 'M3Pro/Camera/camera_rgbd'],
        parameters=[{'use_sim_time': True}],
    )
    # IMU sensor frame alias.
    # Adding base_footprint as a zero-inertia URDF root causes Gazebo's
    # URDF→SDF converter to merge base_link into base_footprint (inertia-less
    # parent absorbs the inertial child).  The IMU, declared on base_link,
    # therefore appears as M3Pro/base_footprint/imu_sensor in bridged messages.
    imu_frame_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='imu_frame_alias',
        arguments=['--frame-id', 'base_link',
                   '--child-frame-id', 'M3Pro/base_footprint/imu_sensor'],
        parameters=[{'use_sim_time': True}],
    )

    # ground_truth_publisher reads /model/M3Pro/pose (geometry_msgs/Pose) bridged in the main parameter_bridge process.
    # Publishes world-frame ground-truth poses for whitelisted Gazebo models.
    ground_truth_publisher = Node(
        package='yahboom_M3Pro_description',
        executable='ground_truth_publisher',
        name='ground_truth_publisher',
        parameters=[{
            'use_sim_time': True,
            'model_names':  ['M3Pro'],
        }],
        output='screen',
    )


    return LaunchDescription([
        DeclareLaunchArgument(
            'gui', default_value='true',
            description='Launch Gazebo GUI (requires GPU/GL)'),
        DeclareLaunchArgument(
            'bridge_tf', default_value='true',
            description=(
                'Bridge Gazebo TF to ROS2 /tf. '
                'Set false when running as a realworld_ws sim backend so '
                'ekf_filter_node remains the sole odom->base_footprint publisher.'
            )),
        DeclareLaunchArgument(
            'world_name', default_value='maze_visualFeatures',
            description='SDF world name (must match <world name="…"> in the .world file).'),
        set_gz_resource_path,
        rsp,
        gz_sim_headless,
        gz_sim_gui,
        spawn_robot,
        bridge,
        bridge_tf_node,
        image_bridge,
        joint_state_publisher,
        laser0_frame_alias,
        laser1_frame_alias,
        camera_frame_alias,
        imu_frame_alias,
        ground_truth_publisher,
    ])
