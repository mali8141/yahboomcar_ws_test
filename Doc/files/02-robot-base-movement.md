# Robot Base Movement (Mecanum Drive in Simulation)

This document covers how the M3Pro's four-mecanum-wheel holonomic base
was made to move in Gazebo Classic, including the approach that was tried
and abandoned, the approach that was kept, and the wheel-tipping issue
that came with it.

## Files added

| File | Purpose |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.planar_move.xacro` | Gazebo plugin macro (`M3Pro_gazebo_planar_move`) providing holonomic base motion |
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.wheel_friction.xacro` | Gazebo plugin macro (`M3Pro_wheel_friction`) overriding per-wheel ODE friction coefficients |

## Files modified

| File | Change |
|---|---|
| `yahboomcar_ws/src/yahboom_M3Pro_description/urdf/M3Pro.urdf.xacro` | Included the two new xacro files and instantiated their macros; wheel joints changed to `continuous`; removed all `ros2_control`-related includes |
| `yahboomcar_ws/src/yahboom_M3Pro_description/launch/gazebo_display.launch.py` | Removed the `ros2_control` / controller-manager spawning; added `joint_state_publisher` to keep publishing joint states now that `joint_state_broadcaster` is gone |

## Files removed

- The `ros2_control` xacro includes and controller-manager YAML that were previously wired into the URDF and launch file (kept only in `yahboomcar_ws/src/M3Pro_config` where they still serve MoveIt2's mock-hardware arm control, which is unrelated to base motion).

## Why these changes were necessary

### Attempt 1: `ros2_control` + `mecanum_drive_controller` (abandoned)

The physically correct way to simulate a mecanum base is to give
`ros2_control`'s `mecanum_drive_controller` real wheel joints to actuate,
with Gazebo's ODE physics engine resolving the angled-roller friction
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
  reference velocities.
- Wheel collision geometry had to be simple cylinders with friction tags
  (rather than the imported mesh) for ODE to compute contact friction at
  all.

**Despite all of this, the chassis never translated.** Gazebo Classic's
ODE physics engine models wheel-ground contact as a simple point-friction
model and has no way to represent the angled rollers on a mecanum wheel;
plain cylinder collision geometry cannot reproduce the diagonal force
component that real mecanum wheels generate. This was confirmed as a
fundamental limitation of Gazebo Classic ODE, not a configuration error,
and is documented as a known digital-twin simulation limitation in the
thesis.

### Attempt 2: `libgazebo_ros_planar_move` (kept)

Given the above, the pragmatic choice was to drive the chassis
**kinematically**: `libgazebo_ros_planar_move` reads `/cmd_vel` (including
its `y` component, which is what makes the omnidirectional/holonomic
motion possible) and directly sets the base link's planar velocity in the
world, rather than deriving motion from individually actuated wheel
joints. This sacrifices physical wheel-contact realism in exchange for
correct, real-time holonomic kinematics matching how the real M3Pro
behaves at the base-frame level — which is what Nav2 and SLAM actually
consume (`/odom`, `/tf`), so it is the right trade-off for this thesis's
navigation/path-planning focus.

### The tipping ("wheelie") side effect

With `planar_move`, the wheel joints become **passive collision
geometry** — the plugin moves `base_link` directly and never spins them.
Gazebo's default ODE friction (`mu1 = mu2 = 1.0`) at the wheel-ground
contact patches then fights the chassis's commanded velocity: the wheels
"stick" to the ground while the body is forced to move, and combined with
the base link's CoM being offset high and rearward
(`xyz="-0.023, ..., 0.092"`), this produced a pitch torque that made the
chassis rear up during forward motion. Increasing wheel mass does not fix
this (mass isn't the cause); lowering the wheel-ground friction
coefficients is the correct fix, since the wheels aren't doing real
propulsion under `planar_move` and don't need realistic ground grip.

## How it works

```
/cmd_vel (geometry_msgs/Twist)
        │
        ▼
libgazebo_ros_planar_move  (plugin on base_link)
        │  sets base_link linear x/y + angular z directly
        ▼
Gazebo physics steps base_link's pose
        │
        ├──► /odom (nav_msgs/Odometry)      [publish_odom: true]
        └──► odom → base_link TF            [publish_odom_tf: true]
```

Plugin configuration (`M3Pro.planar_move.xacro`):

| Parameter | Value | Meaning |
|---|---|---|
| `robot_base_frame` | `base_link` | Frame the plugin moves |
| `odometry_frame` | `odom` | Frame odometry is published in |
| `update_rate` / `publish_rate` | `50` Hz | Physics + odom publish rate |
| `covariance_x/y/yaw` | `0.0001 / 0.0001 / 0.01` | Odometry covariance fed to SLAM/localization |

Friction fix (`M3Pro.wheel_friction.xacro`) overrides `mu1`/`mu2` on all
four wheel links (`lwheel1`, `lwheel2`, `rwheel1`, `rwheel2`) down from
Gazebo's default of `1.0`. The current tuned value is `0.51` — high
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
source yahboomcar_ws/install/setup.bash
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py
# in a second terminal:
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

`teleop_twist_keyboard` publishes directly to `/cmd_vel` with no
remapping needed, since `planar_move` is configured to subscribe there.
