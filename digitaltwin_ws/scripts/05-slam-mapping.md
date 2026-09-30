# SLAM Mapping (slam_toolbox)

This document covers how the digital twin builds an occupancy grid map of
the Gazebo maze world from the merged dual-LiDAR scan, using
`slam_toolbox` in online async mapping mode, and how that map is saved
for the later Nav2 localization phase.

## Files added

| File | Purpose |
|---|---|
| `digitaltwin_ws/src/slam/slam_engine/launch/online_async_launch.py` | Launches the `slam_toolbox` async mapping node |
| `digitaltwin_ws/src/slam/slam_engine/config/mapper_params_online_async.yaml` | slam_toolbox tuning parameters (frames, topics, scan matching, loop closure) |
| `digitaltwin_ws/src/slam/saved_maps/launch/save_map.launch.py` | Wraps `nav2_map_server`'s `map_saver_cli` to persist the finished map |
| `digitaltwin_ws/src/slam/saved_maps/maps/` | Output location for saved `.yaml` / `.pgm` map pairs |

## Existing pipeline reused as input

SLAM does not talk to the raw LiDARs directly — it consumes the already-merged
scan produced by the dual-LiDAR integration step:

- `ira_laser_tools` `laserscan_multi_merger` node — merges `/scan0` and
  `/scan1` into a single `/scan_multi` in the `base_link` frame
- Wheel odometry (`/odom`) — used as the motion prior for scan matching

## Why these changes were necessary

A raw occupancy grid can't be built from a single LiDAR scan — it has to
be assembled incrementally as the robot moves, with each new scan
registered against the growing map to correct for wheel-odometry drift.
`slam_toolbox` was chosen over the alternative (Cartographer, whose dead
launch variants are being removed from the workspace) because it publishes
directly to standard ROS 2 topics/TF that Nav2 and `nav2_map_server`
consume without any conversion step, and because its `mapping` /
`localization` mode switch means the same node can later replace AMCL
entirely if the holonomic-planner comparison chapter calls for it.

## How it works

```
Gazebo Harmonic (front + rear LiDAR)
        │
        ├──► /scan0 ──┐
        └──► /scan1 ──┤
                       ▼
            ira_laser_tools merger
                       │
                       ▼
                 /scan_multi (base_link frame)
                       │
        /odom ────────►│
                       ▼
         slam_toolbox (async_slam_toolbox_node)
         scan matching + pose graph + loop closure
                       │
        ┌──────────────┴──────────────┐
        ▼                              ▼
   /map (occupancy grid)        map → odom TF
   updated every 3.0 s          published every 0.02 s
```

Key parameters (`mapper_params_online_async.yaml`):

| Parameter | Value | Meaning |
|---|---|---|
| `mode` | `mapping` | Building a new map (vs `localization`, replaying against a fixed map) |
| `scan_topic` | `/scan_multi` | Consumes the merged scan, not raw `/scan0`/`/scan1` |
| `odom_frame` / `base_frame` / `map_frame` | `odom` / `base_link` / `map` | TF frames read/written |
| `solver_plugin` | `solver_plugins::CeresSolver` | Backend used for pose-graph optimization |
| `do_loop_closing` | `true` | Retroactively corrects the pose graph when the robot revisits a mapped area |
| `min_laser_range` / `max_laser_range` | `0.5` / `4.0` m | Returns outside this range are excluded from mapping (note: narrower than the merger's own `range_min: 0.05`, so very close-range returns are intentionally filtered at the SLAM stage) |
| `map_update_interval` | `3.0` s | How often the `/map` occupancy grid is refreshed |
| `transform_publish_period` | `0.02` s | How often the `map → odom` TF is published |

## Map saving

Once teleop/exploration has covered the environment with a clean,
loop-closed map, it's saved to disk via:

```bash
ros2 run nav2_map_server map_saver_cli -f <path/to/saved_maps/maps/map_name>
```

This reads live from the `/map` topic (not from disk), so `slam_toolbox`
must still be running when this command executes. It produces
`map_name.yaml` (resolution, origin, occupied/free thresholds) and
`map_name.pgm` (the occupancy grid image), both placed under
`saved_maps/maps/` so `nav2_bringup`'s AMCL localization phase can load
them directly via `get_package_share_directory("saved_maps")`.

## Known issue: mapping vs. localization mode not yet run in parallel

`slam_toolbox` supports a `localization` mode that could run continuously
in place of AMCL during the navigation phase, using the same scan-matching
engine that built the map. This is still an open decision (see the Nav2
task doc) — for now, SLAM only runs in `mapping` mode to produce a static
map that AMCL then localizes against.

## Current status

Dual-LiDAR SLAM mapping is complete and validated: `map_maze.yaml` /
`map_maze.pgm` have been saved to `saved_maps/maps/` and are in active use
as the static map for the Nav2 localization phase.

## How to test

```bash
source digitaltwin_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py &
ros2 run ira_laser_tools laserscan_multi_merger --ros-args --params-file \
  install/ira_laser_tools/share/ira_laser_tools/config/laserscan_merge.yaml &
ros2 launch slam_engine online_async_launch.py use_sim_time:=true &
ros2 launch slam_engine slam_view.launch.py   # RViz, confirm /map is populating
# drive the robot to cover the whole world, then:
ros2 run nav2_map_server map_saver_cli -f src/slam/saved_maps/maps/map_maze
```

## `run_lidar_pipeline.sh`

The four manual steps above (Gazebo, scan merger, `slam_toolbox`, RViz) have
to come up in a fixed order with the right delays between them, and all
need to be torn down together cleanly afterward. `run_lidar_pipeline.sh`
automates this into one command.

### Why it was created

Running each node in its own terminal is error-prone during repeated
mapping test runs: the merger has to wait for Gazebo to actually spawn the
robot before `/scan0`/`/scan1` exist, and stopping five separate terminals
in the right order every time (or worse, closing the terminal window
directly) reliably leaves gz-sim and other nodes running in the
background — which then breaks the *next* run with port/topic conflicts
that are confusing to debug if you don't know to check for stale
processes first. Wrapping the whole pipeline in one script with a single
Ctrl+C shutdown removes both problems.

### How it works

```
Pre-flight cleanup (kill any stale gz sim/merger/slam_toolbox/rviz2
                      processes left over from a previous run)
        │
        ▼
[1/4] Gazebo Harmonic (gz sim) + robot + maze spawn  (setsid, backgrounded)
        │  sleep 8s — gz-sim needs time to spawn the robot before
        │             /scan0 and /scan1 exist for the merger to read
        ▼
[2/4] ira_laser_tools laserscan_multi_merger
        │  sleep 3s
        ▼
[3/4] slam_toolbox (online_async_launch.py)
        │  sleep 3s
        ▼
[4/4] RViz2 (slam_view.launch.py)
        │
        ▼
   wait (script blocks here until Ctrl+C)
```

Each node is started with `setsid`, giving it its own process group, and
its PID is stored in the `PIDS[]` array. On `SIGINT`/`SIGTERM`/`SIGHUP`/`EXIT`,
the `cleanup()` trap sends `SIGTERM` to each stored process group, then —
since gz-sim can leave orphan `ruby`/`gz`/`gz sim` processes after a plain
group kill — force-kills everything a second time with `pkill -9` as a
safety net, so Ctrl+C reliably leaves a clean slate for the next run.

### How to run it

```bash
cd digitaltwin_ws
./run_lidar_pipeline.sh
```

Wait for all four `[n/4]` stages to print, then drive the robot around
the maze (teleop) until the map in RViz is fully closed with no
misaligned walls, and save it in a second terminal per the **Map saving**
section above. Press **Ctrl+C** in the pipeline's terminal when done to
shut everything down cleanly.
