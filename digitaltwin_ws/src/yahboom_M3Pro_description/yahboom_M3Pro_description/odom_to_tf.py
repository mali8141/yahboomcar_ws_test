"""
odom_to_tf.py
Converts /odom (nav_msgs/msg/Odometry) to a TF broadcast for odom -> base_link.

Gazebo Harmonic scopes its diff-drive TF output under the model topic namespace,
so the ros_gz_bridge /tf mapping never receives the odom->base_link transform.
This node derives it from the already-bridged /odom topic instead.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdomToTF(Node):
    def __init__(self):
        super().__init__('odom_to_tf')

        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self._odom_frame = self.get_parameter('odom_frame').get_parameter_value().string_value
        self._base_frame = self.get_parameter('base_frame').get_parameter_value().string_value

        self._br = TransformBroadcaster(self)
        self._sub = self.create_subscription(Odometry, '/odom', self._cb, 50)

        self.get_logger().info(
            f'odom_to_tf: broadcasting {self._odom_frame} -> {self._base_frame} from /odom')

    def _cb(self, msg: Odometry):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = self._odom_frame
        t.child_frame_id = self._base_frame
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self._br.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTF()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
