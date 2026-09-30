import datetime
import queue
import threading

import numpy as np
import rclpy
import soundfile as sf
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class Uma16TopicRecorderNode(Node):
    def __init__(self):
        super().__init__('uma16_topic_recorder')

        self.declare_parameter('samplerate', 48000)
        self.declare_parameter('channels', 16)
        self.declare_parameter('filename', '')

        self.samplerate = self.get_parameter('samplerate').value
        self.channels = self.get_parameter('channels').value
        filename = self.get_parameter('filename').value

        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uma16_recording_{timestamp}.wav"
        self.filename = filename

        self.q: queue.Queue = queue.Queue()
        self.is_recording = True

        self.file = sf.SoundFile(
            self.filename,
            mode='w',
            samplerate=self.samplerate,
            channels=self.channels,
            subtype='PCM_16',
        )

        self.subscription = self.create_subscription(
            Float32MultiArray,
            'uma16/audio',
            self.audio_callback,
            10,
        )

        self.writer_thread = threading.Thread(target=self.file_writer, daemon=True)
        self.writer_thread.start()

        self.get_logger().info(f"Recording to {self.filename}...")
        self.get_logger().info(
            f"Channels: {self.channels} | Sample Rate: {self.samplerate} Hz"
        )

    def audio_callback(self, msg: Float32MultiArray):
        frames = msg.layout.dim[0].size
        channels = msg.layout.dim[1].size
        data = np.array(msg.data, dtype=np.float32).reshape(frames, channels)
        self.q.put(data)

    def file_writer(self):
        while self.is_recording or not self.q.empty():
            try:
                data = self.q.get(timeout=0.1)
                self.file.write(data)
            except queue.Empty:
                pass

    def destroy_node(self):
        self.get_logger().info("Stopping recording and cleaning up...")
        self.is_recording = False

        if hasattr(self, 'writer_thread'):
            self.writer_thread.join()

        if hasattr(self, 'file'):
            self.file.close()

        self.get_logger().info(f"Recording safely saved to: {self.filename}")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Uma16TopicRecorderNode()
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
