# Depth Camera Integration

This document covers how the M3Pro's RGB-D camera was added to the
digital twin, matching the topic layout the real hardware's depth-camera
driver already publishes.

## Files added

| File | Purpose |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.camera_links.xacro` | Adds the optical frame and the Gazebo RGB-D camera sensor plugin |

## Files modified

| File | Change |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.urdf.xacro` | Added the `xacro:include` for the camera xacro and an instantiation of the `M3Pro_camera_links` macro (currently commented out — see **Current status** below) |

## Existing hardware-side node referenced (not yet compatible with sim)

- `M3Pro_ws/src/ros_robot_app/laserscan_to_point_publisher/laserscan_to_point_publisher/pub_rgb_image.py`
  — subscribes to the camera's RGB topic on the real robot; blocked from
  working in simulation by the topic-doubling issue described below.

## Why these changes were necessary

The imported SolidWorks URDF already contained a `Camera` link (mesh +
inertial only, attached to `base_link` via a `revolute` joint with
`lower=upper=0`, i.e. effectively fixed) but no sensor behavior — it was
purely visual/geometric. Gazebo needs an explicit sensor plugin attached
to that link to actually generate image and depth data.

To keep the simulated stream consumable by the same nodes the real
hardware feeds, the plugin publishes under the `/camera/...` namespace
and topic names (`color/image_raw`, `depth/image_raw`, `depth/points`,
etc.) that mirror the real depth-camera driver's layout, and adds a
dedicated `camera_color_optical_frame` so image and point-cloud axes
follow the ROS REP-103 optical convention (`+z` forward, `+x` right,
`+y` down) rather than the URDF's default `+x` forward convention —
without this, RViz2 and any image-based perception node would receive
correctly-shaped data with an incorrectly-oriented frame.

## How it works

```
Gazebo depth camera sensor (on Camera link)
        │  libgazebo_ros_camera.so
        ├──► /camera/color/image_raw        (sensor_msgs/Image, RGB)
        ├──► /camera/color/camera_info
        ├──► /camera/depth/image_raw         (sensor_msgs/Image, depth)
        ├──► /camera/depth/camera_info
        └──► /camera/depth/points            (sensor_msgs/PointCloud2)
```

Sensor configuration (`M3Pro.camera_links.xacro`):

| Parameter | Value |
|---|---|
| Sensor type | `depth` (RGB-D) |
| Resolution | 640 × 480, `R8G8B8` |
| `horizontal_fov` | 1.047 rad (~60°) |
| Clip near/far | 0.1 m / 10.0 m |
| `update_rate` | 15 Hz |
| `frame_name` | `camera_color_optical_frame` |

A fixed joint (`camera_color_optical_joint`) rotates from the `Camera`
link's URDF frame into the optical frame via `rpy="-1.5708 0 -1.5708"`,
which is the standard REP-103 correction rotation used whenever a
sensor's mechanical/URDF frame doesn't already follow the optical-frame
convention.

## Known issue: topic namespace doubling

The plugin's ROS block sets `<namespace>/camera</namespace>` and then
remaps `image_raw:=color/image_raw`. Combined with the plugin's own
default namespacing behavior, this currently produces a doubled
namespace at runtime (`/camera/camera/color/image_raw` instead of the
intended `/camera/color/image_raw`). This has been identified as the
blocker preventing `pub_rgb_image.py` from working against the simulated
camera, since that script subscribes to the un-doubled topic name used
by the real hardware driver. **Fix pending**: either drop the leading
`<namespace>` tag and let the `camera_name`/remappings fully qualify the
topic, or adjust the remap targets to account for the namespace prefix
being applied twice.

## Current status

Camera link visuals were confirmed to render correctly in Gazebo. As with
the LiDAR integration, the include/instantiation is currently commented
out in `M3Pro.urdf.xacro` while the base-movement tipping fix was being
isolated and validated on its own:

```xml
<!-- <xacro:include filename="$(find yahboom_M3Pro_description)/urdf/M3Pro.camera_links.xacro"/> -->
...
<!-- <xacro:M3Pro_camera_links/> -->
```

To re-enable, uncomment both lines, rebuild
(`colcon build --packages-select yahboom_M3Pro_description --symlink-install`),
and resolve the namespace-doubling issue above before relying on
`pub_rgb_image.py` in simulation.

## How to test

```bash
source yahboomcar_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
# in a second terminal:
ros2 topic list | grep camera
ros2 run rqt_image_view rqt_image_view
```
