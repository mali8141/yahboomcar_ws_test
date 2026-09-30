"""
battery_simulator.py
====================
Simulates a simplified robot battery for the digital twin.

Discharge / Charge model
------------------------
- Idle drain:    0.5 % per minute
- Driving drain: extra 4.0 % per minute added while /cmd_vel has non-zero linear or angular velocity.
- Charging:      When the robot is within the ``coupling_radius``of the charging dock, the battery charges at ``charge_rate_per_min`` % per minute. Discharge is suppressed while charging.

Publishes
---------
/battery  (sensor_msgs/BatteryState)
    percentage  : 0.0–1.0
    voltage     : linearly interpolated 10.0 V (empty) – 12.6 V (full)
    current     : positive while charging (+1.0 A), negative while driving
                  (-0.5 A), zero when idle
    charge      : NaN (unmeasured)
    present     : True
    power_supply_status    : CHARGING (1) while on pad, DISCHARGING (2) otherwise
    power_supply_health    : POWER_SUPPLY_HEALTH_GOOD (1)
    power_supply_technology: POWER_SUPPLY_TECHNOLOGY_LION (2)

#TODO double check this with thre realworld robot battery topic
    
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState


# BatteryState constants (sensor_msgs does not expose them as Python names)
_STATUS_CHARGING    = 1
_STATUS_DISCHARGING = 2
_HEALTH_GOOD        = 1
_TECHNOLOGY_LION    = 2

_VOLTAGE_EMPTY = 10.0   # V at 0 %
_VOLTAGE_FULL  = 12.6   # V at 100 %


class BatterySimulator(Node):
    def __init__(self):
        super().__init__('battery_simulator')

        self.declare_parameter('publish_hz',             1.0)
        self.declare_parameter('initial_percentage',     1.0)
        self.declare_parameter('idle_drain_per_min',     0.5)
        self.declare_parameter('driving_drain_per_min',  4.0)
        self.declare_parameter('charge_rate_per_min',   10.0)
        self.declare_parameter('cmd_vel_topic',       '/cmd_vel')
        self.declare_parameter('ground_truth_topic',  '/ground_truth/M3Pro/odom')
        self.declare_parameter('dock_x',              0.0)
        self.declare_parameter('dock_y',              0.0)
        self.declare_parameter('coupling_radius',     0.10)

        self._percentage: float = float(
            self.get_parameter('initial_percentage').value)
        self._percentage = max(0.0, min(1.0, self._percentage))

        self._idle_drain_per_s: float = (
            self.get_parameter('idle_drain_per_min').value / 60.0 / 100.0)
        self._driving_drain_per_s: float = (
            self.get_parameter('driving_drain_per_min').value / 60.0 / 100.0)
        self._charge_per_s: float = (
            self.get_parameter('charge_rate_per_min').value / 60.0 / 100.0)

        self._dock_x: float = float(self.get_parameter('dock_x').value)
        self._dock_y: float = float(self.get_parameter('dock_y').value)
        self._coupling_radius: float = float(self.get_parameter('coupling_radius').value)

        self._is_driving: bool = False
        self._gt_x: float | None = None
        self._gt_y: float | None = None

        cmd_vel_topic: str = self.get_parameter('cmd_vel_topic').value
        self.create_subscription(Twist, cmd_vel_topic, self._cmd_vel_cb, 10)

        gt_topic: str = self.get_parameter('ground_truth_topic').value
        self.create_subscription(Odometry, gt_topic, self._gt_cb, 10)

        self._pub = self.create_publisher(BatteryState, '/battery', 10)

        hz: float = self.get_parameter('publish_hz').value
        self._dt: float = 1.0 / hz
        self.create_timer(self._dt, self._tick)

        self.get_logger().info(
            f'battery_simulator ready: '
            f'idle={self.get_parameter("idle_drain_per_min").value:.2f}%/min  '
            f'driving=+{self.get_parameter("driving_drain_per_min").value:.2f}%/min  '
            f'charge=+{self.get_parameter("charge_rate_per_min").value:.2f}%/min  '
            f'dock=({self._dock_x:.2f}, {self._dock_y:.2f})  '
            f'radius={self._coupling_radius:.2f} m  '
            f'topic=/battery'
        )


    # ------------------------------------------------------------------
    def _cmd_vel_cb(self, msg: Twist) -> None:
        """Mark driving if any linear or angular velocity component is non-zero."""
        self._is_driving = (
            abs(msg.linear.x) > 1e-4
            or abs(msg.linear.y) > 1e-4
            or abs(msg.angular.z) > 1e-4
        )

    def _gt_cb(self, msg: Odometry) -> None:
        """Cache the latest ground-truth position from the Gazebo sim."""
        self._gt_x = msg.pose.pose.position.x
        self._gt_y = msg.pose.pose.position.y

    def _is_near_dock(self) -> bool:
        """Return True when the sim ground-truth position is within
        coupling_radius of the dock.  Returns False if no ground-truth
        message has arrived yet."""
        if self._gt_x is None:
            return False
        dx = self._gt_x - self._dock_x
        dy = self._gt_y - self._dock_y
        return math.hypot(dx, dy) < self._coupling_radius

    def _tick(self) -> None:
        is_driving = self._is_driving
        # Reset driving flag each tick; stays high only while /cmd_vel publishes.
        self._is_driving = False

        charging = self._is_near_dock()

        if charging:
            self._percentage = min(1.0, self._percentage + self._charge_per_s * self._dt)
            current = 1.0   # A, positive = charging
        else:
            drain = self._idle_drain_per_s
            if is_driving:
                drain += self._driving_drain_per_s
            self._percentage = max(0.0, self._percentage - drain * self._dt)
            current = -0.5 if is_driving else 0.0

        voltage = _VOLTAGE_EMPTY + self._percentage * (_VOLTAGE_FULL - _VOLTAGE_EMPTY)

        msg = BatteryState()
        msg.header.stamp        = self.get_clock().now().to_msg()
        msg.header.frame_id     = 'battery'
        msg.percentage          = self._percentage
        msg.voltage             = voltage
        msg.current             = current
        msg.charge              = float('nan')
        msg.present             = True
        msg.power_supply_status     = _STATUS_CHARGING if charging else _STATUS_DISCHARGING
        msg.power_supply_health     = _HEALTH_GOOD
        msg.power_supply_technology = _TECHNOLOGY_LION
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BatterySimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
