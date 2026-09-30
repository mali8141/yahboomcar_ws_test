# Nav2 Localization & Autonomous Navigation (AMCL)

This document covers how the digital twin localizes against a
pre-built static map using AMCL and runs Nav2's planner/controller stack
to autonomously navigate the Gazebo maze world.

## Files added

| File | Purpose |
|---|---|
| `digitaltwin_ws/src/M3Pro_navigation/launch/navigation2.launch.py` | Includes `nav2_bringup`'s `bringup_launch.py` (map_server + AMCL + planner + controller + BT navigator) |
| `digitaltwin_ws/src/M3Pro_navigation/launch/navigation_launch.py` | Nav2 stack only (no map_server/AMCL) — used for exploration/mapping-mode Nav2, not localization |
| `digitaltwin_ws/src/M3Pro_navigation/param/yahboom_M3Pro.yaml` | Nav2 parameter file: AMCL, costmaps, controller, planner |
| `digitaltwin_ws/run_navigation_pipeline.sh` | Automates Gazebo + scan merger + Nav2 (AMCL) + RViz2 in one command |

## Files modified

| File | Change |
|---|---|
| `param/yahboom_M3Pro.yaml` | `robot_model_type` set to `nav2_amcl::OmniMotionModel` (was a differential-drive model, incorrect for the mecanum base); both `voxel_layer` costmap plugin blocks removed; `use_sim_time` inconsistencies resolved |
| `navigation2.launch.py` | `map` default updated from `M3Pro_navigation/map/yahboom_map.yaml` to `saved_maps/maps/map_maze.yaml`, so the SLAM-produced map is loaded automatically |

## Existing pipeline reused as input

- `ira_laser_tools` `laserscan_multi_merger` — same `/scan_multi` feed used
  for SLAM is reused here as AMCL's observation source
- `saved_maps/maps/map_maze.yaml` — the static map produced by the SLAM
  mapping stage (see `05-slam-mapping.md`)

## Why these changes were necessary

Nav2's stock parameter file (and `nav2_amcl` in general) defaults to a
differential-drive motion model, which assumes the robot cannot move
sideways. The M3Pro's four-mecanum-wheel base is holonomic — it can
strafe and rotate independently of its heading — so a differential model
would systematically mispredict particle motion during AMCL's predict
step, degrading localization accuracy specifically during sideways
movement. Switching to `OmniMotionModel` corrects this, and is one of the
concrete, quantifiable ways the thesis's holonomic-aware navigation
contribution shows up in the localization layer itself, not just the
controller.

The two `voxel_layer` blocks were removed because they require a 3D
point cloud / depth source that wasn't reliably available at the time
this was configured, and were causing costmap plugin load failures;
`obstacle_layer` (2D LaserScan-based) is sufficient given the current
sensor setup.

## How it works

```
Gazebo (front + rear LiDAR)
        │
        ├──► /scan0 ──┐
        └──► /scan1 ──┤
                       ▼
            ira_laser_tools merger
                       │
                       ▼
                 /scan_multi
                       │
saved_maps/maps/       │
map_maze.yaml ────► map_server ──► /map (static, unchanging)
                       │
                       ▼
                 AMCL (particle filter)
        odom_frame → base_frame,  OmniMotionModel
                       │
                       ▼
              map → odom TF  +  /amcl_pose (with covariance)
                       │
                       ▼
        planner_server + controller_server (FollowPath)
        global_costmap (map frame) / local_costmap (odom frame, rolling)
                       │
                       ▼
                    /cmd_vel
```

Key parameters (`yahboom_M3Pro.yaml`):

| Section | Parameter | Value | Meaning |
|---|---|---|---|
| `amcl` | `robot_model_type` | `nav2_amcl::OmniMotionModel` | Correct motion model for a holonomic mecanum base |
| `amcl` | `laser_model_type` | `likelihood_field` | Scan-matching method used to weight particles |
| `amcl` | `max_particles` | `2000` | Upper bound on the particle filter population |
| `global_costmap` | `global_frame` | `map` | Costmap used for long-range planning, static-layer fed by `/map` |
| `local_costmap` | `global_frame` | `odom` | Costmap used for immediate obstacle avoidance, rolling window (`width`/`height: 3`) centered on the robot |
| `controller_server` | `min_vel_y` / `max_vel_y` | `0.0` / `0.3` | Lateral velocity enabled — holonomic strafing available to the local planner |
| `controller_server` | `controller_frequency` | `5.0` Hz | Rate at which `FollowPath` recomputes velocity commands |

**Global vs. local costmap distinction:** the global costmap plans the
overall path against the static `map_maze.yaml` map, while the local
costmap operates in the drifting `odom` frame and only sees a 3×3 m
rolling window around the robot — this is what lets Nav2 react to
obstacles not present in the static map (e.g. anything moved after the
map was saved) without needing to touch the global plan.

## Map loading verification

Since the map is only loaded once at launch, it's worth confirming the
right file was actually picked up before debugging anything else:

```bash
ros2 param get /map_server yaml_filename
```

This should report the full path ending in `saved_maps/maps/map_maze.yaml`.
If it reports a different filename, `navigation2.launch.py`'s `map`
default (or an explicit `map:=` override) is pointing at the wrong file —
see the **Known issue** below for the specific pitfall that caused this
in practice.

## Known issue: `Invalid frame ID "map"` on startup

AMCL will loop with `Invalid frame ID "map"` errors if it comes up before
`/scan_multi` exists — i.e. if the `ira_laser_tools` merger isn't running
yet, or hasn't received `/scan0`/`/scan1` yet. AMCL has nothing to match
particles against without a live scan, so it never publishes the
`map → odom` transform and everything downstream that expects the `map`
frame fails. **Fix**: ensure the merger is fully up (confirmed by
`ros2 topic echo /scan_multi --once` returning data) before launching
Nav2 — `run_navigation_pipeline.sh` handles this ordering with fixed
delays between stages (see below).

## Known issue: AMCL requires manual pose initialization

Nav2 comes up localized-but-idle: AMCL's particle filter starts as a
uniform cloud across the map and needs an initial pose estimate to
converge in a reasonable number of scans. This has to be set manually in
RViz2 via **2D Pose Estimate**, clicking where the robot actually is in
Gazebo — it can't be automated from the launch file since it depends on
the robot's actual (variable) starting position in the world.

## Current status

AMCL localization is working against `map_maze.yaml`: the particle cloud
converges after a short pose estimate + small robot motion, and
`map → odom` publishes correctly (verified via
`ros2 run tf2_ros tf2_echo map odom`). First short Nav2 goals have not
yet been stress-tested through tight maze corridors — initial testing is
being kept to short, open-ground goals to isolate localization/planning
correctness from the still-unresolved wheel-friction/tipping issue during
acceleration.

## How to test

```bash
source digitaltwin_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py &
ros2 run ira_laser_tools laserscan_multi_merger --ros-args --params-file \
  install/ira_laser_tools/share/ira_laser_tools/config/laserscan_merge.yaml &
ros2 launch M3Pro_navigation navigation2.launch.py use_sim_time:=true &
ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true
# in RViz2: "2D Pose Estimate" -> click the robot's actual pose in Gazebo
# confirm localization:
ros2 run tf2_ros tf2_echo map odom
# then use "Nav2 Goal" in RViz2 to send a short, open-ground goal first
```

## `run_navigation_pipeline.sh`

Like `run_lidar_pipeline.sh` for the SLAM stage, this script automates
the four-stage Nav2 startup (Gazebo, scan merger, Nav2/AMCL, RViz2) into
one command with a single clean shutdown, instead of five manually
ordered terminals.

### Why it was created

The same two problems that motivated `run_lidar_pipeline.sh` apply here:
staged startup ordering (the merger needs `/scan0`/`/scan1` to exist
before it can publish `/scan_multi`, and Nav2 needs `/scan_multi` before
AMCL can localize) and reliable cleanup of gz-sim, which can leave
orphan `ruby`/`gz`/`gz sim` processes after a plain process-group
`SIGTERM`. A second, Nav2-specific reason: the map path is resolved once
up front (`ros2 pkg prefix saved_maps`) and checked for existence before
anything else launches, so a missing or unbuilt map fails fast with a
clear message instead of failing deep inside Nav2's lifecycle bringup
where it's harder to diagnose.

### How it works

```
Pre-flight cleanup (kill any stale gz sim/merger/nav2 component
                      container/rviz2/slam_toolbox processes)
        │
        ▼
Resolve MAP_PATH via `ros2 pkg prefix saved_maps` and fail fast if
map_maze.yaml doesn't exist there
        │
        ▼
[1/4] Gazebo Harmonic (gz sim) + robot + maze spawn  (setsid, backgrounded)
        │  sleep 8s — gz-sim needs time to spawn the robot before
        │             /scan0 and /scan1 exist for the merger to read
        ▼
[2/4] ira_laser_tools laserscan_multi_merger
        │  sleep 3s
        ▼
[3/4] Nav2 (navigation2.launch.py: map_server + AMCL + planner +
      controller, map:="$MAP_PATH")
        │  sleep 5s — Nav2's lifecycle-managed stack (map_server, AMCL,
        │             both costmaps, planner, controller) takes longer
        │             to reach the active state than the SLAM stage's
        │             single node
        ▼
[4/4] RViz2 (nav2_bringup rviz_launch.py)
        │
        ▼
   wait (script blocks here until Ctrl+C)
```

As with the SLAM pipeline script, each stage is started with `setsid`
into its own process group, PIDs are collected in `PIDS[]`, and the
`cleanup()` trap on `SIGINT`/`SIGTERM`/`SIGHUP`/`EXIT` sends `SIGTERM` to
each group followed by a `pkill -9` safety net — extended here to also
match Nav2's `component_container_isolated` process (the container hosting
AMCL, both costmaps, planner, and controller as composed nodes), which
needs the same forceful cleanup as gz-sim.

### How to run it

```bash
cd digitaltwin_ws
./run_navigation_pipeline.sh
```

Wait for all four `[n/4]` stages to print, then in RViz2 click
**2D Pose Estimate** and set the robot's actual pose before Nav2 will
localize and accept goals. Press **Ctrl+C** in the pipeline's terminal
to shut everything down cleanly.
