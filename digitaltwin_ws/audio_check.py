#!/usr/bin/env python3
"""
audio_check.py - quick sanity checker for the uma16/audio stream.

Prints, once per received chunk:
  - message rate (Hz)
  - chunk shape (frames x channels)
  - RMS level in dBFS
  - dominant frequency (Hz)
  - whether all channels are identical

Usage (after sourcing the workspace):
  python3 audio_check.py
"""
import time

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

SAMPLERATE = 48000


class AudioCheck(Node):
    def __init__(self):
        super().__init__('audio_check')
        self.create_subscription(Float32MultiArray, 'uma16/audio', self.cb, 10)
        self.last_t = None
        self.get_logger().info('Listening on uma16/audio ...')

    def cb(self, msg: Float32MultiArray):
        now = time.monotonic()
        rate = 0.0 if self.last_t is None else 1.0 / (now - self.last_t)
        self.last_t = now

        frames = msg.layout.dim[0].size
        chans = msg.layout.dim[1].size
        data = np.asarray(msg.data, dtype=np.float32).reshape(frames, chans)

        mono = data[:, 0]
        rms = float(np.sqrt(np.mean(mono ** 2)))
        dbfs = 20.0 * np.log10(rms + 1e-12)

        spec = np.abs(np.fft.rfft(mono * np.hanning(frames)))
        freqs = np.fft.rfftfreq(frames, 1.0 / SAMPLERATE)
        dom = float(freqs[np.argmax(spec[1:]) + 1])  # skip DC bin

        identical = bool(np.allclose(data, data[:, :1]))

        self.get_logger().info(
            f'{rate:5.2f} Hz | {frames}x{chans} | '
            f'{dbfs:6.1f} dBFS | dominant {dom:6.0f} Hz | '
            f'channels identical: {identical}'
        )


def main():
    rclpy.init()
    node = AudioCheck()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
