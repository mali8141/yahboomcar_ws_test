#!/usr/bin/env python3
"""
Simple fake odometry node.
Since we don't have real wheel encoders, we FAKE the robot's position
by integrating the velocity commands we send it (dead reckoning).
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from nav_msgs.msg import Odometry
import tf2_ros


class FakeOdomDriver(Node):
    def __init__(self):
        super().__init__('fake_odom_driver')

        # Current estimated pose (starts at origin)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # Last received velocity command
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        self.last_time = self.get_clock().now()

        # Listen for velocity commands
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)

        # Publish fake odometry + TF
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Update pose 30 times per second
        self.create_timer(1.0 / 30.0, self.update_pose)

    def cmd_vel_callback(self, msg):
        # Just remember the latest commanded velocity
        self.vx = msg.linear.x
        self.vy = msg.linear.y
        self.wz = msg.angular.z

    def update_pose(self):
        # How much time passed since last update?
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        if dt <= 0:
            return

        # Basic physics: new_position = old_position + velocity * time
        # (rotated into the odom frame using current heading theta)
        self.x += (self.vx * math.cos(self.theta) - self.vy * math.sin(self.theta)) * dt
        self.y += (self.vx * math.sin(self.theta) + self.vy * math.cos(self.theta)) * dt
        self.theta += self.wz * dt

        # Convert heading angle -> quaternion (ROS needs quaternions for orientation)
        q = Quaternion()
        q.z = math.sin(self.theta / 2.0)
        q.w = math.cos(self.theta / 2.0)

        # Publish as an Odometry message
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = q
        self.odom_pub.publish(odom)

        # Also broadcast the same info as a TF transform (odom -> base_link)
        # so RViz knows where to draw the robot
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation = q
        self.tf_broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = FakeOdomDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()