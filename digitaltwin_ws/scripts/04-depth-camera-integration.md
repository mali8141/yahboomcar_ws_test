# Depth Camera Integration

This document covers how the M3Pro's RGB-D camera was added to the
digital twin, matching the topic layout the real hardware's depth-camera
driver already publishes.

## Files added

| File | Purpose |
|---|---|
| `digitaltwin_ws/src/yahboom_M3Pro_description/urdf/M3Pro.camera_links.xacro` | Adds the optical frame and the Gazebo Harmonic `rgbd_camera` sensor; data bridged to ROS via `ros_gz_bridge` and `ros_gz_image` in `gazebo_display.launch.py` |

## Files modified

| File | Change |
|---|---|
| `digitaltwin_ws/src/yahboom_M3Pro_description/urdf/M3Pro.urdf.xacro` | Added the `xacro:include` for the camera xacro and an instantiation of the `M3Pro_camera_links` macro |

## Existing hardware-side node referenced (not yet compatible with sim)

- `realworld_ws/src/ros_robot_app/laserscan_to_point_publisher/laserscan_to_point_publisher/pub_rgb_image.py`
  — subscribes to the camera's RGB topic on the real robot; blocked from
  working in simulation by the topic-doubling issue described below.

## Why these changes were necessary

The imported SolidWorks URDF already contained a `Camera` link (mesh +
inertial only, attached to `base_link` via a `revolute` joint with
`lower=upper=0`, i.e. effectively fixed) but no sensor behavior — it was
purely visual/geometric. Gazebo Harmonic needs an explicit sensor block
attached to that link (`type="rgbd_camera"`) to actually generate image and
depth data; unlike Gazebo Classic, there is no `libgazebo_ros_camera.so`
plugin — the sensor is declared natively in the URDF/SDF and its output is
bridged to ROS via `ros_gz_bridge` (for topic types parameter_bridge handles)
and `ros_gz_image` (for raw `Image` messages).

To keep the simulated stream consumable by the same nodes the real
hardware feeds, the sensor publishes under the `/camera/...` namespace
and topic names (`color/image_raw`, `depth/image_raw`, `depth/points`,
etc.) that mirror the real depth-camera driver's layout, and adds a
dedicated `camera_color_optical_frame` so image and point-cloud axes
follow the ROS REP-103 optical convention (`+z` forward, `+x` right,
`+y` down) rather than the URDF's default `+x` forward convention —
without this, RViz2 and any image-based perception node would receive
correctly-shaped data with an incorrectly-oriented frame.

## How it works

```
Gazebo Harmonic rgbd_camera sensor (on Camera link)
        │  type="rgbd_camera", bridged via ros_gz_bridge + ros_gz_image
        ├──► /camera/color/image_raw        (sensor_msgs/Image, RGB)
        ├──► /camera/color/camera_info
        ├──► /camera/depth/image_raw         (sensor_msgs/Image, depth)
        ├──► /camera/depth/camera_info
        └──► /camera/points                  (sensor_msgs/PointCloud2)
```

Sensor configuration (`M3Pro.camera_links.xacro`):

| Parameter | Value |
|---|---|
| Sensor type | `rgbd_camera` (Gazebo Harmonic built-in) |
| Resolution | 640 × 480, `R8G8B8` |
| `horizontal_fov` | 1.047 rad (~60°) |
| Clip near/far | 0.1 m / 10.0 m |
| `update_rate` | 15 Hz |
| Frame | `camera_color_optical_frame` (aliased from `M3Pro/Camera/camera_rgbd` via `static_transform_publisher`) |

A fixed joint (`camera_color_optical_joint`) rotates from the `Camera`
link's URDF frame into the optical frame via `rpy="-1.5708 0 -1.5708"`,
which is the standard REP-103 correction rotation used whenever a
sensor's mechanical/URDF frame doesn't already follow the optical-frame
convention.

## Known issue: topic namespace doubling

The Gazebo Harmonic `rgbd_camera` sensor publishes under the topic prefix
declared via `<topic>camera</topic>`. Combined with `ros_gz_bridge`'s
topic mapping rules, this can produce a doubled namespace at runtime
(`/camera/camera/color/image_raw` instead of `/camera/color/image_raw`).
This has been identified as the blocker preventing `pub_rgb_image.py`
from working against the simulated camera. **Fix pending**: adjust
the `ros_gz_bridge` or `ros_gz_image` topic mapping in
`gazebo_display.launch.py` to avoid the double prefix.

## Current status

Camera link visuals confirmed rendering correctly in Gazebo Harmonic.
The include/instantiation in `M3Pro.urdf.xacro` is active:

```xml
<xacro:include filename="$(find yahboom_M3Pro_description)/urdf/M3Pro.camera_links.xacro"/>
...
<xacro:M3Pro_camera_links/>
```

The namespace-doubling issue is still pending before `pub_rgb_image.py`
can be used against the simulation.

## How to test

```bash
source digitaltwin_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
# in a second terminal:
ros2 topic list | grep camera
ros2 run rqt_image_view rqt_image_view
```
