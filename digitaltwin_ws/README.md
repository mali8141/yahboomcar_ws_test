# Digital Twin — ROSMASTER M3Pro

Gazebo Harmonic / ROS 2 Jazzy digital twin of the Yahboom ROSMASTER M3Pro,
developed as part of the thesis *"Autonomous Navigation and Path Planning
for the ROSMaster M3Pro Mobile Manipulator: A Digital Twin Approach Using
ROS 2."*

This workspace is the **simulation-only** side of the project. Real-hardware
code (arm driver, serial-port nodes, etc.) lives separately in
[`realworld_ws`](../realworld_ws) and is pulled into this workspace only
once a given feature reaches the point of sim-to-real transfer.

## Documentation

Each document covers one implemented feature: what changed, why it was
necessary, and how the pipeline works end to end.

1. [Gazebo Environment Setup](scripts/01-gazebo-environment-setup.md) —
   world file, spawn pipeline, launch architecture
2. [Robot Base Movement](scripts/02-robot-base-movement.md) — mecanum
   drive simulation via `planar_move`, the `ros2_control` attempt that
   was ruled out, and the wheel-friction/tipping fix
3. [Dual-LiDAR Integration](scripts/03-lidar-integration.md) — simulated
   LiDAR sensors, scan merging/filtering, SLAM topic wiring
4. [Depth Camera Integration](scripts/04-depth-camera-integration.md) —
   simulated RGB-D camera, optical-frame correction, known topic issue
5. [SLAM Mapping](scripts/05-slam-mapping.md) —
   slam_toolbox setup, map saving, topic wiring
6. [Nav2 Navigation](scripts/06-nav2-navigation.md) —
   Nav2 stack, EKF, costmaps, path planning
7. [Simulated Audio Field](scripts/07-sim-audio-field.md) —
   pre-baked audio field, IDW interpolation, `audio_field_builder`, `sim_audio_publisher`, pipeline design and limitations

The full thesis write-up (`main.tex`/`main.pdf`) is in [`Doc/`](Doc/).

## Getting started

```bash
git clone https://github.com/mali8141/yahboomcar_ws_test.git
cd yahboomcar_ws_test/digitaltwin_ws
./environment_setup.sh
```

`environment_setup.sh` handles the full one-time setup: `rosdep` resolution,
the system packages `rosdep` misses (see the script's comments for why),
and the initial `colcon build`. It's safe to re-run any time.

After setup, in every new terminal:
```bash
source install/setup.bash
```

## Useing Gazebo sim with realworld_ws

The sim can be used in conjunction with the real-hardware workspace (`realworld_ws`) to test sim-to-real transfer of SLAM and navigation pipelines. The sim publishes the same topics as the real robot, so any nodes that work in the sim should work on the real robot without much modification.

To use the sim with `realworld_ws`, first start the sim bridge in one terminal:
```sh
source install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
```

Then in another terminal, start the real-hardware workspace:
```sh
cd ../realworld_ws/custom_scripts
./start_core_robot.sh --sim
```

In another terminal, you can then run any of the other compatible `realworld_ws` scripts. Not all sensors of the real robot have been simulated yet, so some scripts might fail.

As a replacment for the joy controller the following can be used to control the robot in the sim:
```sh
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Repository layout

Single colcon workspace under `src/`, grouped by subsystem:

```
digitaltwin_ws/
├── environment_setup.sh          # one-time dependency + build bootstrap
├── run_lidar_pipeline.sh         # automates the 4-stage dual-LiDAR SLAM pipeline
├── Doc/                          # thesis write-up (LaTeX source + PDF)
├── scripts/                      # per-feature task documentation (this README links to it)
└── src/
    ├── yahboom_M3Pro_description/  # URDF/xacro, meshes, worlds, spawn + display launch files
    ├── M3Pro_navigation/           # Nav2 launch/params (not yet exercised — next roadmap step)
    ├── lidar/
    │   ├── ira_laser_tools/        # laserscan_multi_merger: /scan0 + /scan1 → /scan_multi
    │   └── yahboom_laser_filter/   # laser scan filtering node
    └── slam/
        ├── slam_engine/            # slam_toolbox launch/config (formerly `slam_mapping`)
        └── saved_maps/             # saved map output (yahboom_map.pgm/.yaml)
```

Packages related to arm manipulation (`M3Pro_config`, `arm_kin`,
`arm_interface`, `M3Pro_MoveIt_demo`, etc.) and to features not yet started
(patrol, EKF localization, multi-robot) are intentionally **not** in this
workspace yet. They'll be copied in from the original Yahboom source as
each roadmap step is reached, rather than carried as unused dead weight.

## Environment this was developed and tested on

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic (gz-sim)
- Development laptop: Lenovo LOQ, NVIDIA GeForce RTX 5050