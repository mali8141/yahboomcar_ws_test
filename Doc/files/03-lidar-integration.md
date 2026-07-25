# Dual-LiDAR Sensor Integration

This document covers how the M3Pro's two physical LiDAR units were
modeled in the digital twin, and how their scans are merged and filtered
into the single `/scan` topic that SLAM and Nav2 consume — mirroring the
real hardware's sensing pipeline.

## Files added

| File | Purpose |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.lidar_links.xacro` | Adds `laser0_frame` / `laser1_frame` links and the two Gazebo ray-sensor plugins that simulate the physical LiDARs |

## Files modified

| File | Change |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.urdf.xacro` | Added the `xacro:include` for the lidar xacro and an instantiation of the `M3Pro_lidar_links` macro (currently commented out — see **Current status** below) |
| `M3Pro_ws/src/slam_mapping/config/mapper_params_online_async.yaml` | `base_frame` corrected to `base_link`; `scan_topic` corrected to `/scan_multi` |

## Existing hardware-side pipeline reused as-is

These packages already existed for the real robot and are reused unchanged
so that simulation and hardware share the same downstream scan-processing
pipeline:

- `M3Pro_ws/src/M3Pro_core/ira_laser_tools` — `laserscan_multi_merger`
  node + `config/laserscan_merge.yaml`
- `M3Pro_ws/src/M3Pro_core/yahboom_laser_filter` — `laser_filter_node`
  + `launch/laser_filter_node_multi.xml`

## Why these changes were necessary

The real M3Pro has two independent LiDAR units mounted at different
corners of the chassis, each publishing its own `LaserScan`. Rather than
simulate a single idealized 360° sensor (which would diverge from the
real perception stack), the digital twin models **both** physical units
separately, so that everything downstream — the merge node, the filter
node, SLAM, Nav2 — runs identically whether the scans originate from
Gazebo's ray sensors or the real hardware drivers.

The SLAM config fixes were necessary because the default
`mapper_params_online_async.yaml` (adapted from a generic `slam_toolbox`
example) referenced `base_footprint` and `/scan`, neither of which exist
in this robot's TF tree / topic layout: the URDF's root/base frame is
`base_link`, and the merged (not filtered) scan topic is `/scan_multi`.

## How the pipeline works

```
Gazebo ray sensor "laser0"  ──►  /scan0  ─┐
                                            ├──► laserscan_multi_merger ──► /scan_multi ──► laser_filter_node ──► /scan
Gazebo ray sensor "laser1"  ──►  /scan1  ─┘         (ira_laser_tools)        │                 (yahboom_laser_filter)
                                                                              └──► consumed directly by slam_toolbox
```

### Sensor definitions (`M3Pro.lidar_links.xacro`)

Two fixed links, `laser0_frame` and `laser1_frame`, are attached to
`base_link` at the physical mounting offsets measured from the real
robot:

| Frame | Offset (x, y, z) | Gazebo topic | Range |
|---|---|---|---|
| `laser0_frame` | `-0.11617, 0.09156, 0.1253` | `/scan0` | 0.05 – 12.0 m |
| `laser1_frame` | `0.10766, -0.09078, 0.1253` | `/scan1` | 0.12 – 8.0 m |

Each is a Gazebo `ray` sensor with `libgazebo_ros_ray_sensor.so`, a
360-sample full-circle horizontal scan (`-3.14159` to `3.14159` rad),
10 Hz update rate, and Gaussian noise (`stddev = 0.01`) to avoid
unrealistically perfect scans.

### Merge and filter (existing, reused)

- `laserscan_multi_merger` (`ira_laser_tools`) subscribes to `/scan0` and
  `/scan1` and republishes a single combined scan on `/scan_multi`, in
  the `base_link` frame (`destination_frame` in `laserscan_merge.yaml`).
- `laser_filter_node` (`yahboom_laser_filter`) takes `/scan_multi` and
  republishes a filtered `/scan` (angle range `-180°` to `180°`), which
  is the topic Nav2's costmaps ultimately expect.
- `slam_toolbox` is configured to consume `/scan_multi` directly (not the
  filtered `/scan`), with `base_frame: base_link` and `odom_frame: odom`.

### Naming constraint discovered along the way

Xacro macro names cannot contain dots — dots are reserved for xacro's
namespace/property syntax (`${prefix.foo}`). File names like
`M3Pro.lidar_links.xacro` are fine (the filename isn't parsed by xacro),
but the `<xacro:macro name="...">` declared inside must use underscores
(`M3Pro_lidar_links`), which is why the macro name differs from the
filename.

## Current status

Map creation with this pipeline has been confirmed working. However, in
the current `M3Pro.urdf.xacro`, the lidar include/instantiation is
temporarily commented out while the base-movement tipping fix
(`M3Pro.wheel_friction.xacro`, see `02-robot-base-movement.md`) was being
isolated and validated in isolation:

```xml
<!-- <xacro:include filename="$(find yahboom_M3Pro_description)/urdf/M3Pro.lidar_links.xacro"/> -->
...
<!-- <xacro:M3Pro_lidar_links/> -->
```

To re-enable both LiDARs, uncomment both lines and rebuild
(`colcon build --packages-select yahboom_M3Pro_description --symlink-install`).

## How to test

```bash
source yahboomcar_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
# in a second terminal (after sourcing M3Pro_ws too):
ros2 launch ira_laser_tools merge_multi.launch.py
ros2 topic echo /scan_multi --once
```
