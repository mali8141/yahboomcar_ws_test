import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


class AudioRecordingTriggerNode(Node):
    """
    Periodically tells the audio_mapper node to record a short audio clip.

    Every `trigger_period` seconds it publishes a Float32 on
    `recording_trigger_topic` requesting `recording_duration` seconds of
    audio. If the previous recording hasn't finished yet (no acknowledgment
    received on `recording_done_topic`), it skips that tick and keeps
    waiting instead of firing overlapping requests - so the effective rate
    is "every second, unless the recorder is still busy from before".
    """

    def __init__(self):
        super().__init__('audio_recording_trigger')

        self.declare_parameter('recording_trigger_topic', 'audio_mapper/trigger_recording')
        self.declare_parameter('recording_done_topic', 'audio_mapper/recording_done')
        self.declare_parameter('recording_duration', 1.0)   # seconds of audio to request
        self.declare_parameter('trigger_period', 1.0)        # how often to attempt a trigger
        self.declare_parameter('done_timeout', 30.0)         # safety: give up waiting after this long

        self.recording_trigger_topic = self.get_parameter('recording_trigger_topic').value
        self.recording_done_topic = self.get_parameter('recording_done_topic').value
        self.recording_duration = float(self.get_parameter('recording_duration').value)
        self.trigger_period = float(self.get_parameter('trigger_period').value)
        self.done_timeout = float(self.get_parameter('done_timeout').value)

        self.trigger_pub = self.create_publisher(Float32, self.recording_trigger_topic, 10)
        self.done_sub = self.create_subscription(
            String,
            self.recording_done_topic,
            self._done_callback,
            10
        )

        self.waiting_for_done = False
        self.waiting_since = None
        self._trigger_count = 0

        self.timer = self.create_timer(self.trigger_period, self._timer_callback)

        self.get_logger().info(
            f"Trigger node started: requesting {self.recording_duration}s recordings "
            f"every {self.trigger_period}s on '{self.recording_trigger_topic}', "
            f"listening for completion on '{self.recording_done_topic}'"
        )

    def _timer_callback(self):
        if self.waiting_for_done:
            elapsed = (self.get_clock().now() - self.waiting_since).nanoseconds / 1e9
            if elapsed >= self.done_timeout:
                self.get_logger().warn(
                    f"No completion ack after {elapsed:.1f}s - giving up waiting and "
                    "triggering again anyway."
                )
                self.waiting_for_done = False
            else:
                self.get_logger().info(
                    f"Previous recording still in progress ({elapsed:.1f}s) - waiting before next trigger."
                )
                return

        self._send_trigger()

    def _send_trigger(self):
        self._trigger_count += 1
        msg = Float32()
        msg.data = self.recording_duration
        self.trigger_pub.publish(msg)

        self.waiting_for_done = True
        self.waiting_since = self.get_clock().now()

        self.get_logger().info(
            f"[trigger {self._trigger_count}] Requested {self.recording_duration}s recording."
        )

    def _done_callback(self, msg: String):
        if not self.waiting_for_done:
            # Unexpected ack (e.g. from a manual trigger elsewhere) - just log it.
            self.get_logger().debug(f"Received recording ack while not waiting: {msg.data}")
            return

        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            payload = {'status': 'unknown', 'raw': msg.data}

        if payload.get('status') == 'done':
            entry = payload.get('entry', {})
            self.get_logger().info(
                f"[trigger {self._trigger_count}] Recording complete: "
                f"{entry.get('filename')} ({entry.get('actual_duration_s')}s) "
                f"-> {entry.get('filepath')}"
            )
        else:
            self.get_logger().warn(
                f"[trigger {self._trigger_count}] Recording did not complete successfully: {payload}"
            )

        self.waiting_for_done = False
        self.waiting_since = None


def main(args=None):
    rclpy.init(args=args)
    node = AudioRecordingTriggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()