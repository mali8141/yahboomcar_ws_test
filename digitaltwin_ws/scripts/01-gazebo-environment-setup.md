# Gazebo Environment Setup

This document covers how the ROSMASTER M3Pro digital twin was brought up in
Gazebo Harmonic (gz-sim): the simulation world, the spawn pipeline, and the
launch architecture that ties URDF processing, physics, and visualization
together.

## Files added

| File | Purpose |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/worlds/maze.world` | Gazebo Harmonic SDF world (maze layout) used as the test environment |
| `yahboomcar_ws/src/yahboom_M3Pro_description/launch/gazebo_display.launch.py` | Top-level launch file: starts Gazebo, spawns the robot, publishes robot state and joint states |
| `yahboomcar_ws/src/yahboom_M3Pro_description/launch/rsp.launch.py` | Processes the xacro into `robot_description` and runs `robot_state_publisher` |

## Files modified

| File | Change |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/setup.py` | Added explicit `data_files` glob entries for `worlds/*.*`, `config/*.yaml`, and `launch/*.py*` so `colcon build` installs them into the package share directory |

## Why these changes were necessary

The M3Pro description package originally only shipped a URDF and meshes
(exported from SolidWorks) meant for RViz visualization, not simulation.
Bringing it into Gazebo Harmonic required three additional pieces:

1. **A world file.** Gazebo Harmonic (gz-sim) needs an SDF world to load — an
   empty world is fine for basic checks, but a maze layout gives SLAM and Nav2
   something non-trivial to map and navigate around later in the thesis. The
   maze world is written in SDF 1.9 (Harmonic's dialect) and does not use any
   Gazebo Classic–specific tags or system plugins.
2. **A spawn + bridge pipeline.** `robot_description` (from xacro) needs to
   reach both `robot_state_publisher` (for TF) and `gz sim` (to instantiate
   the model). Sensors publish on internal Gazebo topics and are bridged to ROS
   via `ros_gz_bridge` (parameter bridge for most types) and `ros_gz_image`
   (for raw `Image` messages, which `parameter_bridge` cannot handle). The
   launch file is split into `rsp.launch.py` (state publisher) included by
   `gazebo_display.launch.py` (gz-sim process + spawn + bridge nodes).
3. **Package data installation.** `ament_python` packages do not install
   arbitrary files by default — every directory referenced by a launch
   file at runtime (`worlds/`, `config/`) has to be explicitly listed in
   `setup.py`'s `data_files`, or `get_package_share_directory()` calls at
   launch time fail to find them after `colcon build`.

## How the pipeline works

```
xacro (M3Pro.urdf.xacro)
        │  xacro.process_file()
        ▼
robot_description (XML string)
        │
        ├──► robot_state_publisher   (publishes /tf, /tf_static)
        │
        └──► gz sim (gz_ros_create)  (spawns the model in the running
                                       gz-sim world)
```

`gazebo_display.launch.py` orchestrates this in order:

1. Sets `GZ_SIM_RESOURCE_PATH` so gz-sim can resolve `package://` mesh URIs.
2. Includes `rsp.launch.py`, which runs `xacro.process_file()` on
   `M3Pro.urdf.xacro` and publishes the result on `robot_description` via
   `robot_state_publisher`.
3. Starts `gz sim` itself as a raw process, loading `maze.world`. Unlike
   Gazebo Classic, gz-sim does not need explicit `libgazebo_ros_init.so` or
   `libgazebo_ros_factory.so` system plugins — the `ros_gz_bridge` package
   provides `/clock` bridging and the `gz_ros_create` service handles spawning.
4. After a `TimerAction` delay (to let gz-sim finish loading the world), runs
   `gz_ros_create`, which reads the `robot_description` topic and spawns the
   robot 0.05 m above the ground plane.
5. Starts `joint_state_publisher` to publish states for the (currently
   passive) arm and wheel joints, so RViz2 can still render the full TF tree.
6. Starts `ros_gz_bridge` and `ros_gz_image` nodes to bridge Gazebo sensor
   topics to ROS. Gazebo Harmonic scopes sensor frames as
   `<model>/<link>/<sensor>` in bridged message headers; identity-transform
   alias nodes (`static_transform_publisher`) map those scoped names back to
   the URDF link frames expected by the rest of the pipeline.

### Sensor frame aliasing

Gazebo Harmonic names sensor frames as `<model>/<link>/<sensor>` in bridged
message headers, while `robot_state_publisher` uses the plain URDF link names.
`gazebo_display.launch.py` publishes identity `static_transform_publisher`
nodes to alias each Gazebo-scoped frame name back to the URDF frame name:

| Gazebo frame | URDF frame |
|---|---|
| `M3Pro/laser0_frame/laser0` | `laser0_frame` |
| `M3Pro/laser1_frame/laser1` | `laser1_frame` |
| `M3Pro/Camera/camera_rgbd` | `camera_color_optical_frame` |
| `M3Pro/base_link/imu_sensor` | `base_link` |

### A note on world-file discipline

Gazebo (both Classic and Harmonic) bakes whatever is spawned into the world
when you use **Save World As** from the GUI. If the robot is in the scene,
the saved `.world` file gains a static copy, conflicting with the dynamic
spawn call on the next launch (duplicate model name / unexpected static robot).
**Rule followed throughout this project: only save the world file when
the world is empty of spawned robots.**

## How to run it

```bash
source digitaltwin_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
```

This opens gz-sim with the maze world loaded and the M3Pro spawned, and
publishes the full robot TF tree so RViz2 can attach to it separately.

