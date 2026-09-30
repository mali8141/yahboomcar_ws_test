# Robot Base Movement (Mecanum Drive in Simulation)

This document covers how the M3Pro's four-mecanum-wheel holonomic base
was made to move in Gazebo Harmonic (gz-sim), including the approach that was
tried and abandoned, the approach that was kept, and the wheel-tipping issue
that came with it.

## Files added

| File | Purpose |
|---|---|
| `digitaltwin_ws/src/yahboom_M3Pro_description/urdf/M3Pro.planar_move.xacro` | Gazebo plugin macro (`M3Pro_gazebo_planar_move`) providing holonomic base motion via the gz-sim `DiffDrive` system |
| `digitaltwin_ws/src/yahboom_M3Pro_description/urdf/M3Pro.wheel_friction.xacro` | Gazebo plugin macro (`M3Pro_wheel_friction`) overriding per-wheel friction coefficients |

## Files modified

| File | Change |
|---|---|
| `digitaltwin_ws/src/yahboom_M3Pro_description/urdf/M3Pro.urdf.xacro` | Included the two new xacro files and instantiated their macros; wheel joints changed to `continuous`; removed all `ros2_control`-related includes |
| `digitaltwin_ws/src/yahboom_M3Pro_description/launch/gazebo_display.launch.py` | Removed the `ros2_control` / controller-manager spawning; added `joint_state_publisher` to keep publishing joint states now that `joint_state_broadcaster` is gone |

## Files removed

- The `ros2_control` xacro includes and controller-manager YAML that were previously wired into the URDF and launch file (kept only in `digitaltwin_ws/src/M3Pro_config` where they still serve MoveIt2's mock-hardware arm control, which is unrelated to base motion).

## Why these changes were necessary

### Attempt 1: `ros2_control` + `mecanum_drive_controller` (abandoned)

The physically correct way to simulate a mecanum base is to give
`ros2_control`'s `mecanum_drive_controller` real wheel joints to actuate,
with Gazebo's physics engine resolving the angled-roller friction
that produces net omnidirectional motion. This was implemented and
debugged to the point where the controller reached `active` state and
produced correct per-wheel velocity commands, requiring several fixes
along the way:

- Wheel joints had to be `continuous`, not `fixed`.
- XML comments had to be stripped from the `robot_description` string
  before it was re-passed as a `--param` argument internally by
  `gazebo_ros2_control`, since an embedded `--` sequence inside a
  `<!-- ... -->` comment broke its argument parser.
- `libgazebo_ros_init.so` had to be loaded so Gazebo publishes `/clock`;
  without it, sim time stays frozen and the controller computes `.nan`
  reference velocities. (In Gazebo Harmonic `/clock` is bridged by
  `ros_gz_bridge`, so this step is no longer needed.)
- Wheel collision geometry had to be simple cylinders with friction tags
  (rather than the imported mesh) for the physics engine to compute contact
  friction at all.

**Despite all of this, the chassis never translated.** Gazebo's physics
engine models wheel-ground contact as a simple point-friction model and
has no way to represent the angled rollers on a mecanum wheel; plain
cylinder collision geometry cannot reproduce the diagonal force component
that real mecanum wheels generate. This was confirmed as a fundamental
limitation of Gazebo's default physics, not a configuration error, and is
documented as a known digital-twin simulation limitation in the thesis.

### Attempt 2: `gz-sim-diff-drive-system` (kept)

Given the above, the pragmatic choice was to drive the chassis
**kinematically**: the `gz::sim::systems::DiffDrive` plugin
(`gz-sim-diff-drive-system`) reads `/cmd_vel` and directly sets the base
link's planar velocity in the world, rather than deriving motion from
individually actuated wheel joints. This sacrifices physical
wheel-contact realism in exchange for correct, real-time holonomic
kinematics matching how the real M3Pro behaves at the base-frame level —
which is what Nav2 and SLAM actually consume (`/odom`, `/tf`), so it is
the right trade-off for this thesis's navigation/path-planning focus.

> **Note on naming:** In Gazebo Classic, this functionality was provided
> by `libgazebo_ros_planar_move.so`. In Gazebo Harmonic (gz-sim), the
> equivalent is the `gz::sim::systems::DiffDrive` system declared with
> `filename="gz-sim-diff-drive-system"` in the URDF/SDF `<plugin>` block.

### The tipping ("wheelie") side effect

With the kinematic drive plugin, the wheel joints become **passive collision
geometry** — the plugin moves `base_link` directly and never spins them.
Gazebo's default friction (`mu1 = mu2 = 1.0`) at the wheel-ground contact
patches then fights the chassis's commanded velocity: the wheels "stick"
to the ground while the body is forced to move, and combined with the base
link's CoM being offset high and rearward (`xyz="-0.023, ..., 0.092"`),
this produced a pitch torque that made the chassis rear up during forward
motion. Increasing wheel mass does not fix this (mass isn't the cause);
lowering the wheel-ground friction coefficients is the correct fix, since
the wheels aren't doing real propulsion under the kinematic driver and
don't need realistic ground grip.

## How it works

```
/cmd_vel (geometry_msgs/Twist)
        │
        ▼
gz::sim::systems::DiffDrive  (plugin on base_link)
        │  sets base_link linear x/y + angular z directly
        ▼
Gazebo Harmonic physics steps base_link's pose
        │
        ├──► /odom (nav_msgs/Odometry)    [odom_topic: odom]
        └──► odom → base_link TF          [tf_topic: tf, bridged via ros_gz_bridge]
```

> **odom → base_link TF note:** Gazebo Harmonic publishes TF under the
> model's internal topic namespace, which is not bridged by `ros_gz_bridge`'s
> `/tf` entry. `gazebo_display.launch.py` therefore derives the
> `odom → base_link` transform from the already-bridged `/odom` topic via
> the `odom_to_tf` node (`yahboom_M3Pro_description/odom_to_tf.py`).

Plugin configuration (`M3Pro.planar_move.xacro`):

| Parameter | Value | Meaning |
|---|---|---|
| `left_joint` / `right_joint` | `lwheel1_Joint`, `lwheel2_Joint` / `rwheel1_Joint`, `rwheel2_Joint` | Wheel joints used for odometry computation |
| `wheel_separation` | `0.293` m | Track width |
| `wheel_radius` | `0.04` m | Wheel radius |
| `odom_publish_frequency` | `50` Hz | Odometry + TF publish rate |
| `topic` | `cmd_vel` | Subscribed velocity command topic |
| `frame_id` / `child_frame_id` | `odom` / `base_link` | TF frames published |

Friction fix (`M3Pro.wheel_friction.xacro`) overrides `mu1`/`mu2` on all
four wheel links (`lwheel1`, `lwheel2`, `rwheel1`, `rwheel2`) down from
Gazebo's default of `1.0`. The current tuned value is `0.50` — high
enough that the robot doesn't skate/slide on the maze floor, low enough
that it no longer pitches up under forward commands.

## Current status

Both macros are active and instantiated in `M3Pro.urdf.xacro`:

```xml
<xacro:include filename="$(find yahboom_M3Pro_description)/urdf/M3Pro.planar_move.xacro"/>
<xacro:include filename="$(find yahboom_M3Pro_description)/urdf/M3Pro.wheel_friction.xacro"/>
...
<xacro:M3Pro_gazebo_planar_move/>
<xacro:M3Pro_wheel_friction/>
```

Base motion is functional; the tipping issue has been mitigated by the
friction fix above.

## How to test

```bash
source digitaltwin_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
# in a second terminal:
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

`teleop_twist_keyboard` publishes directly to `/cmd_vel` with no
remapping needed, since the `DiffDrive` plugin is configured to subscribe there.
