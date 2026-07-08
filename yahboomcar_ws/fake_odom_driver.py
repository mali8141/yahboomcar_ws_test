#!/usr/bin/env python3
"""
fake_odom_driver.py

A stand-in for the real ROSMASTER motor-driver node.
It does NOT talk to any hardware. It just:
  1. Subscribes to /cmd_vel
  2. Integrates (vx, vy, wz) over time -> a fake pose
  3. Publishes nav_msgs/Odometry on /odom
  4. Broadcasts the odom -> base_link TF

Use this when you don't have the real robot but want to see the
URDF move in RViz in response to teleop / keyboard / joystick commands.

Requirements:
  - Your URDF/robot_state_publisher must be running (display.launch.py)
  - Your URDF's root link must match --base-frame (default: base_footprint or base_link)
  - RViz Fixed Frame should be set to "odom" (or "base_footprint" if you don't care
    about drift, but "odom" is the normal convention)

Run:
  ros2 run <your_pkg> fake_odom_driver.py
  (or just: python3 fake_odom_driver.py, after chmod +x)

Then drive it with, e.g.:
  ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from nav_msgs.msg import Odometry
import tf2_ros


def yaw_to_quaternion(yaw: float) -> Quaternion:
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class FakeOdomDriver(Node):
    def __init__(self):
        super().__init__('fake_odom_driver')

        # ---- Parameters you may want to tweak ----
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('publish_rate_hz', 30.0)

        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        rate_hz = self.get_parameter('publish_rate_hz').value

        # Pose state (dead reckoning)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # Latest commanded velocity
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        self._last_time = self.get_clock().now()

        qos = QoSProfile(depth=10)
        self.sub = self.create_subscription(Twist, cmd_vel_topic, self.cmd_vel_cb, qos)
        self.odom_pub = self.create_publisher(Odometry, '/odom', qos)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        period = 1.0 / rate_hz
        self.timer = self.create_timer(period, self.update)

        self.get_logger().info(
            f'fake_odom_driver started. Listening on {cmd_vel_topic}, '
            f'publishing TF {self.odom_frame} -> {self.base_frame}'
        )

    def cmd_vel_cb(self, msg: Twist):
        self.vx = msg.linear.x
        self.vy = msg.linear.y   # non-zero for mecanum/omni chassis
        self.wz = msg.angular.z

    def update(self):
        now = self.get_clock().now()
        dt = (now - self._last_time).nanoseconds / 1e9
        self._last_time = now
        if dt <= 0.0:
            return

        # Integrate velocity in the robot's own frame into odom-frame pose
        delta_x = (self.vx * math.cos(self.theta) - self.vy * math.sin(self.theta)) * dt
        delta_y = (self.vx * math.sin(self.theta) + self.vy * math.cos(self.theta)) * dt
        delta_theta = self.wz * dt

        self.x += delta_x
        self.y += delta_y
        self.theta += delta_theta
        # keep theta in [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        q = yaw_to_quaternion(self.theta)

        # --- Publish Odometry message ---
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.linear.y = self.vy
        odom.twist.twist.angular.z = self.wz
        self.odom_pub.publish(odom)

        # --- Broadcast TF ---
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation = q
        self.tf_broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = FakeOdomDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
