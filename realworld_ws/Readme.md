# Real-World Workspace — ROSMASTER M3Pro (Original Yahboom Repo)

This folder holds Yahboom's **original, unmodified** ROS 2 repository for
the ROSMASTER M3Pro, as shipped by the manufacturer. It's kept as-is —
untouched — so it stays a reliable reference for anything not yet ported
to the simulation side of this project.

It is **not** meant to be built or run on the development laptop. It's
meant to run on the robot's onboard computer (Jetson Nano or Raspberry
Pi), where the real sensors, motors, and serial devices actually exist.

The simulation counterpart, [`digitaltwin_ws`](../digitaltwin_ws), only
contains the subset of packages actually needed so far — everything else
stays here until a task calls for it, at which point it gets copied over
and adapted rather than carried as unused weight in the sim workspace.

## Top-level Docker launch scripts

| Script | Purpose |
|---|---|
| `Docker_M3Pro-nano.sh` | Launches Yahboom's pre-built Docker image on a Jetson Nano compute board, with device passthrough for the arm's serial port, USB, camera, mic/speaker, and X11 display |
| `Docker_M3Pro-pi.sh` | Same, for a Raspberry Pi compute board |
| `Docker_M3Pro_Joy-nano.sh` / `Docker_M3Pro_Joy-pi.sh` | Same as above, configured for joystick/gamepad teleop instead of keyboard |

These only make sense on the physical robot itself — they pass through
hardware device paths (`/dev/myserial`, `/dev/bus/usb`, `/dev/snd`, etc.)
that don't exist on a development machine.

## `yahboomcar_ws/src/` — hardware enablement & robot description

| Package | What it does | Status |
|---|---|---|
| `yahboom_M3Pro_description` | URDF/xacro, meshes, worlds, spawn/display launch files | ✅ Ported to `digitaltwin_ws` |
| `M3Pro_config` | MoveIt2 motion-planning config for the arm (defaults to mock hardware, so it's sim-capable) | Not yet ported — planned for arm manipulation work |
| `arm_kin` | Forward/inverse kinematics service (pure math via KDL) | Not yet ported — planned for arm manipulation work |
| `arm_interface` | Service/message definitions consumed by `arm_kin` | Not yet ported — planned for arm manipulation work |
| `arm_driver` | Opens `/dev/ttyUSB0` and drives the arm's servos via Yahboom's `Rosmaster_Lib` | Real-hardware only — never goes into the sim workspace |
| `arm_msgs` | Message types used to command the arm from the sim→real bridge | Real-hardware only |
| `M3Pro_MoveIt_demo` | `random_move.py` (sim-testable MoveGroup demo) + `SimulationToMachine.py` (mirrors simulated arm motion onto the physical arm) | Not yet ported — the bridge script is only meaningful once real hardware is involved |
| `test_config` | Leftover MoveIt Setup Assistant scaffold for a different Yahboom product (`dofbot_pro`) | Unused, likely stray boilerplate |
| `M3Pro_KCF` | KCF visual object-tracking implementation | Out of scope — vision tracking not part of the thesis pipeline |
| `M3Pro_demo` | Bundle of demo scripts: AprilTag detection, color tracking, gestures, dance routines | Out of scope — manufacturer demo features |
| `yahboom_M3Pro_DepthCam` | Reads the **real** depth-camera driver's topics (different layout than the simulated camera) | Real-hardware only |
| `yahboom_M3Pro_laser` | Real-hardware laser-based obstacle avoidance/tracking | Real-hardware only |
| `yahboomcar_ctrl` | Custom joystick/keyboard teleop nodes | Unused — stock `teleop_twist_keyboard` is used instead |
| `yahboomcar_msgs` | Custom message types feeding the vision/demo packages | Only used by the out-of-scope vision packages above |

## `M3Pro_ws/src/` — navigation, SLAM, and higher-level behavior

| Package | What it does | Status |
|---|---|---|
| `M3Pro_core/ira_laser_tools` | Merges multiple LiDAR scans into one (`laserscan_multi_merger`) | ✅ Ported to `digitaltwin_ws` |
| `M3Pro_core/yahboom_laser_filter` | Filters/cleans laser scan data | ✅ Ported to `digitaltwin_ws` |
| `slam_mapping` | SLAM launch/config — `slam_toolbox` (adopted), plus unused `cartographer`/`gmapping` alternatives | ✅ Ported to `digitaltwin_ws` as `slam_engine` |
| `yahboom_mapping` | Saved map output (`.pgm` / `.yaml`) | ✅ Ported to `digitaltwin_ws` as `saved_maps` |
| `M3Pro_navigation` | Nav2 + Cartographer launch files and params | ✅ Ported to `digitaltwin_ws` — awaiting the Nav2 rollout task |
| `M3Pro_core/imu_tools` | IMU data filtering utilities | Not yet ported — no IMU work started |
| `M3Pro_core/openslam_gmapping`, `M3Pro_core/slam_gmapping` | Alternate SLAM backend (gmapping) | Unused — `slam_toolbox` was adopted instead |
| `M3Pro` (a second package, not `_description`) | Duplicate meshes + multi-robot display launch files | Redundant with `yahboom_M3Pro_description` |
| `M3Pro_KCF` (a second copy, distinct from the one in `yahboomcar_ws`) | Same KCF tracker | Redundant, out of scope |
| `calibration` | Measures real wheel-odometry accuracy against ground truth | Real-hardware only — meaningless in sim |
| `ekf_bringup` | `robot_localization` EKF fusing wheel odometry + IMU | Not yet ported — relevant once a localization strategy is chosen |
| `updatecostmap` | Custom Nav2 costmap update node | Not yet ported — future Nav2 work |
| `patrol` | Simple waypoint-patrol behavior | Not yet ported — planned validation step after Nav2 is working |
| `yahboom_multi` | Multi-robot AMCL/Nav2 coordination (`robot1/2/3_*`) | Out of scope — this project is single-robot |
| `interfaces`, `largemodel`, `largemodel_arm`, `text_chat` | Yahboom's LLM-based voice-assistant stack | Out of scope — unrelated product feature |
| `ros_robot_app/*` (`laserscan_to_point_publisher`, `robot_pose_publisher_ros2`, `yahboom_app_save_map`, `yahboom_web_savmap_interfaces`) | Support nodes for Yahboom's companion mobile app | Out of scope — app remote-control feature |

## How this fits into the project

Yahboom ships this as one repository covering every feature of the
physical robot — driving, arm control, SLAM/navigation, object tracking,
voice assistant, and a companion phone app — regardless of relevance to
any specific use case. This project only needs a narrow slice of it, which
is why `digitaltwin_ws` is much smaller: packages get copied over from
here and adapted only once a task actually requires them, rather than
carried across as unused dead weight in the simulation workspace.