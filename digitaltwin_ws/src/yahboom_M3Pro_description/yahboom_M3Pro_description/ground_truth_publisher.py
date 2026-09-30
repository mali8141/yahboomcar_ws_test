"""
ground_truth_publisher.py
=========================
Publishes ground-truth world-frame poses for a configurable whitelist of
Gazebo models by reading per-model pose topics published by the Gazebo
PosePublisher system plugin (model-level).

Parameters
----------
model_names : string[]   Models to track.   Default: ['M3Pro']

Output
------
/ground_truth/<model_name>/odom  (nav_msgs/Odometry)
    header.frame_id = 'world'
    child_frame_id  = 'base_footprint'
    pose.pose       = robot pose in world frame (from Gazebo ECS via PosePublisher)
    pose.covariance = zeroed (ground truth has no uncertainty)
    twist           = zeroed (not available from gz.msgs.Pose)
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose


DEFAULT_MODELS = ['M3Pro']


class GroundTruthPublisher(Node):
    def __init__(self):
        super().__init__('ground_truth_publisher')

        self.declare_parameter('model_names', DEFAULT_MODELS)

        model_names: list[str] = (
            self.get_parameter('model_names')
                .get_parameter_value().string_array_value
            or DEFAULT_MODELS
        )

        # One publisher + one subscriber per tracked model.
        # _pub_map  : model_name → Odometry publisher
        self._pub_map: dict[str, rclpy.publisher.Publisher] = {}

        for model_name in model_names:
            out_topic  = f'/ground_truth/{model_name}/odom'
            pose_topic = f'/model/{model_name}/pose'

            self._pub_map[model_name] = self.create_publisher(
                Odometry, out_topic, 10
            )

            # Closure over model_name for the callback.
            def _make_cb(name: str):
                def _cb(msg: Pose) -> None:
                    self._pose_cb(name, msg)
                return _cb

            self.create_subscription(Pose, pose_topic, _make_cb(model_name), 10)

            self.get_logger().info(
                f'ground_truth_publisher: tracking "{model_name}"'
                f' | in={pose_topic} → out={out_topic}'
            )

    def _pose_cb(self, model_name: str, msg: Pose) -> None:
        pub = self._pub_map.get(model_name)
        if pub is None:
            return

        odom = Odometry()
        odom.header.stamp    = self.get_clock().now().to_msg()
        odom.header.frame_id = 'world'
        odom.child_frame_id  = 'base_footprint'
        odom.pose.pose       = msg
        # covariance left zeroed — ground truth has no uncertainty
        # twist left zeroed — not available from gz.msgs.Pose

        pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = GroundTruthPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
