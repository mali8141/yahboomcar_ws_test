# Gazebo Environment Setup

This document covers how the ROSMASTER M3Pro digital twin was brought up in
Gazebo Classic: the simulation world, the spawn pipeline, and the launch
architecture that ties URDF processing, physics, and visualization together.

## Files added

| File | Purpose |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/worlds/maze.world` | Custom Gazebo Classic world (maze layout) used as the test environment |
| `yahboomcar_ws/src/yahboom_M3Pro_description/launch/gazebo_display.launch.py` | Top-level launch file: starts Gazebo, spawns the robot, publishes robot state and joint states |
| `yahboomcar_ws/src/yahboom_M3Pro_description/launch/rsp.launch.py` | Processes the xacro into `robot_description` and runs `robot_state_publisher` |

## Files modified

| File | Change |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/setup.py` | Added explicit `data_files` glob entries for `worlds/*.*`, `config/*.yaml`, and `launch/*.py*` so `colcon build` installs them into the package share directory |

## Why these changes were necessary

The M3Pro description package originally only shipped a URDF and meshes
(exported from SolidWorks) meant for RViz visualization, not simulation.
Bringing it into Gazebo required three additional pieces:

1. **A world file.** Gazebo needs an SDF world to load — an empty world is
   fine for basic checks, but a maze layout gives SLAM and Nav2 something
   non-trivial to map and navigate around later in the thesis. The maze
   world was adapted from an Ignition Gazebo (SDF 1.8) source world into
   Gazebo Classic's SDF 1.7 dialect, removing plugins/tags Classic doesn't
   support and correcting the `<physics type="...">` declaration.
2. **A spawn pipeline.** `robot_description` (from xacro) needs to reach
   both `robot_state_publisher` (for TF) and Gazebo's `spawn_entity.py`
   (to instantiate the model in the world). These are two different
   consumers of the same URDF string, so the launch file is split into
   `rsp.launch.py` (state publisher) included by `gazebo_display.launch.py`
   (Gazebo process + spawn + joint states).
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
        └──► gazebo_ros spawn_entity.py  (subscribes to /robot_description topic,
                                           instantiates the model in the running
                                           Gazebo world)
```

`gazebo_display.launch.py` orchestrates this in order:

1. Sets `GAZEBO_MODEL_PATH` so Gazebo can resolve `package://` mesh URIs.
2. Includes `rsp.launch.py`, which runs `xacro.process_file()` on
   `M3Pro.urdf.xacro` and publishes the result on `robot_description` via
   `robot_state_publisher`.
3. Starts `gazebo` itself as a raw process, loading `maze.world` with the
   `libgazebo_ros_init.so` (provides `/clock`, required for `use_sim_time`)
   and `libgazebo_ros_factory.so` (provides the spawn/delete services)
   system plugins.
4. After a 3 second `TimerAction` delay (to let Gazebo finish loading the
   world), runs `spawn_entity.py`, which reads the `robot_description`
   topic and spawns the robot 0.05 m above the ground plane.
5. Starts `joint_state_publisher` to publish states for the (currently
   passive, non-actuated-by-Gazebo) arm and wheel joints, so RViz2 can
   still render the full TF tree.

### A note on world-file discipline

Gazebo Classic silently bakes in whatever is currently spawned when you use
**Save World As** from the GUI. If the robot is spawned when the world is
saved, the saved `.world` file gains a static copy of the robot model,
which then conflicts with the dynamic `spawn_entity` call on the next
launch (duplicate model name / unexpected static robot in the scene).
**Rule followed throughout this project: only save the world file when
the world is empty of spawned robots.**

## How to run it

```bash
source yahboomcar_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
```

This opens Gazebo with the maze world loaded and the M3Pro spawned, and
publishes the full robot TF tree so RViz2 can attach to it separately.
