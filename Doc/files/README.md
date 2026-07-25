# Digital Twin Documentation Index

Documentation for the Gazebo Classic / ROS 2 Humble digital twin of the
Yahboom ROSMASTER M3Pro, developed as part of the thesis *"Autonomous
Navigation and Path Planning for the ROSMaster M3Pro Mobile Manipulator:
A Digital Twin Approach Using ROS 2."*

Each document below covers one implemented feature: what changed, why it
was necessary, and how the pipeline works end to end.

1. [Gazebo Environment Setup](01-gazebo-environment-setup.md) — world
   file, spawn pipeline, launch architecture
2. [Robot Base Movement](02-robot-base-movement.md) — mecanum drive
   simulation via `planar_move`, the `ros2_control` attempt that was
   ruled out, and the wheel-friction/tipping fix
3. [Dual-LiDAR Integration](03-lidar-integration.md) — simulated
   LiDAR sensors, scan merging/filtering, SLAM topic wiring
4. [Depth Camera Integration](04-depth-camera-integration.md) —
   simulated RGB-D camera, optical-frame correction, known topic issue


   
Dependencies
System / ROS packages (one-time setup)

Assumes Ubuntu 22.04 with ROS 2 Humble already installed (ros-humble-desktop).

bash
sudo apt update
sudo apt install -y \
  ros-humble-xacro \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-teleop-twist-keyboard \
  ros-humble-slam-toolbox \
  ros-humble-tf2-ros \
  ros-humble-tf2-tools \
  ros-humble-laser-geometry \
  ros-humble-pcl-ros \
  libpcl-dev


## Repository layout (relevant packages)

This repo contains two ROS 2 workspaces:

- **`yahboomcar_ws`** — hardware enablement / driver layer, plus the
  robot description used for simulation (`yahboom_M3Pro_description`)
  and the MoveIt2 arm config (`M3Pro_config`).
- **`M3Pro_ws`** — higher-level task/behavior layer: Nav2, SLAM
  (`slam_mapping`), the laser merge/filter nodes (`ira_laser_tools`,
  `yahboom_laser_filter`), patrol, and multi-robot coordination.

The split between the two workspaces is about system layer, not about
which machine a node runs on — that is decided per-node based on
hardware dependencies (e.g. a node needing direct serial-port access must
run on the physical robot regardless of which workspace it lives in).

## Environment this was developed and tested on

- Ubuntu 22.04, X11
- ROS 2 Humble
- Gazebo Classic (11)
- Development laptop with an NVIDIA RTX 5050 hybrid GPU
