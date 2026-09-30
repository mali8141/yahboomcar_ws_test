import subprocess

import numpy as np
import rclpy
import rclpy.executors
import sounddevice as sd
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, MultiArrayDimension

_UMA16_PA_SOURCE = 'alsa_input.usb-miniDSP_UMA16v2_00026-00.multichannel-input'


class Uma16AudioPublisherNode(Node):
    def __init__(self):
        super().__init__('uma16_audio_publisher')

        self.declare_parameter('device_index', 0)
        self.declare_parameter('device', 'UMA16v2')
        self.declare_parameter('samplerate', 48000)
        self.declare_parameter('channels', 16)
        self.declare_parameter('chunk_size', 8192)
        self.declare_parameter('suspend_pulse', True)

        device_index = self.get_parameter('device_index').value
        device_param = self.get_parameter('device').value

        # device_index takes priority: if non-negative, use it directly
        if device_index >= 0:
            self.device = device_index
            self.get_logger().info(f"Using device index {device_index}")
        elif device_param.isdigit():
            self.device = int(device_param)
            self.get_logger().info(f"Using device name (resolved to index): {device_param}")
        else:
            self.device = device_param if device_param else None
            self.get_logger().info(f"Using device name: {self.device}")
        self.samplerate = self.get_parameter('samplerate').value
        self.channels = self.get_parameter('channels').value
        self.chunk_size = self.get_parameter('chunk_size').value

        self.publisher_ = self.create_publisher(Float32MultiArray, 'uma16/audio', 10)

        if self.get_parameter('suspend_pulse').value:
            self._suspend_pulse_source()

        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                device=self.device,
                channels=self.channels,
                blocksize=self.chunk_size,
                callback=self.audio_callback,
            )
            self.stream.start()
            self.get_logger().info(
                f"Streaming {self.channels}ch @ {self.samplerate}Hz on topic 'uma16/audio'"
            )
        except Exception as e:
            self.get_logger().error(f"Failed to open audio device: {e}")
            raise

    def _suspend_pulse_source(self):
        try:
            result = subprocess.run(
                ['pactl', 'suspend-source', _UMA16_PA_SOURCE, '1'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self.get_logger().info('Suspended PulseAudio UMA16v2 source; opening hardware directly')
            else:
                self.get_logger().debug(f'pactl suspend-source: {result.stderr.strip()}')
        except Exception as e:
            self.get_logger().debug(f'Could not suspend PulseAudio source: {e}')

    def audio_callback(self, indata, frames, time, status):
        if not rclpy.ok():
            return
        if status:
            self.get_logger().warning(f"Audio stream status: {status}")

        msg = Float32MultiArray()
        msg.layout.dim = [
            MultiArrayDimension(label='frames', size=frames, stride=frames * self.channels),
            MultiArrayDimension(label='channels', size=self.channels, stride=self.channels),
        ]
        msg.data = indata.astype(np.float32).flatten().tolist()
        self.publisher_.publish(msg)

    def destroy_node(self):
        self.get_logger().info("Stopping audio stream...")
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Uma16AudioPublisherNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
