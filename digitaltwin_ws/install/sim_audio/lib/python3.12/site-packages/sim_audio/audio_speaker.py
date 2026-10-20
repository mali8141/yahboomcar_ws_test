#!/usr/bin/env python3
"""
audio_speaker.py
================
Plays the microphone stream published on uma16/audio through the laptop
speakers, so the operator can hear what the robot "hears".

Works with both sources of uma16/audio without changes:
  - sim_audio_publisher   (Gazebo digital twin, pre-baked audio field)
  - uma16_audio_publisher (real UMA-16 array on the physical robot)

Pipeline
--------
  uma16/audio (Float32MultiArray, [frames, channels])
      -> pick one channel
      -> apply output gain
      -> jitter buffer (absorbs ROS timer / network jitter)
      -> sounddevice OutputStream (PortAudio) -> laptop speakers

Jitter buffer
-------------
The publisher sends chunks of chunk_size samples on a ROS timer, which does
not tick exactly every chunk_size / samplerate seconds. The audio device, on
the other hand, consumes samples at an exact rate. The buffer decouples the
two:
  - Playback starts only after prefill_ms of audio has been buffered.
  - On underrun (buffer empty) the device gets silence and the buffer
    re-prefills before playback resumes.
  - If the buffer grows beyond max_buffer_ms (publisher running faster than
    the device), the oldest samples are dropped to keep latency bounded.

Level monitoring
----------------
The RMS level of each received chunk is published in dBFS on
audio_speaker/level_db (std_msgs/Float32). Plot it with rqt_plot while
driving the robot to see the level rise as it approaches a source.

Parameters
----------
  audio_topic     Input topic.                          Default: uma16/audio
  channel         Channel index to play.                Default: 0
  samplerate      Must match the publisher.             Default: 48000
  gain            Linear output gain (1.0 = unchanged). Default: 1.0
  prefill_ms      Audio buffered before playback.       Default: 300
  max_buffer_ms   Latency cap; older audio is dropped.  Default: 1000
  device          PortAudio output device index or name substring;
                  empty = system default.               Default: ''
  blocksize       Device callback size in frames.       Default: 1024

Dependencies
------------
  sudo apt install libportaudio2
  pip install sounddevice --break-system-packages

Usage
-----
  ros2 run sim_audio audio_speaker
  ros2 run sim_audio audio_speaker --ros-args -p gain:=2.0 -p channel:=0
  python3 -c "import sounddevice as sd; print(sd.query_devices())"   # list devices
"""

from __future__ import annotations

import sys
import threading

import numpy as np
import rclpy
import rclpy.executors
from rclpy.node import Node
from std_msgs.msg import Float32, Float32MultiArray

try:
    import sounddevice as sd
except (ImportError, OSError) as _exc:  # OSError: libportaudio2 missing
    sd = None
    _SD_IMPORT_ERROR = _exc


_DBFS_FLOOR = -120.0  # reported level for digital silence


class JitterBuffer:
    """Thread-safe FIFO of float32 mono samples with prefill and latency cap."""

    def __init__(self, prefill: int, max_len: int):
        self._prefill = prefill
        self._max_len = max_len
        self._buf = np.zeros(0, dtype=np.float32)
        self._lock = threading.Lock()
        self._playing = False
        self.underruns = 0
        self.dropped = 0

    def push(self, samples: np.ndarray) -> None:
        with self._lock:
            self._buf = np.concatenate([self._buf, samples])
            excess = len(self._buf) - self._max_len
            if excess > 0:
                self._buf = self._buf[excess:]
                self.dropped += excess

    def pull(self, n: int) -> np.ndarray:
        """Return exactly n samples; silence while prefilling or on underrun."""
        with self._lock:
            if not self._playing:
                if len(self._buf) < self._prefill:
                    return np.zeros(n, dtype=np.float32)
                self._playing = True

            if len(self._buf) >= n:
                out = self._buf[:n]
                self._buf = self._buf[n:]
                return out

            # Underrun: play what is left, pad with silence, re-prefill.
            out = np.zeros(n, dtype=np.float32)
            out[:len(self._buf)] = self._buf
            self._buf = np.zeros(0, dtype=np.float32)
            self._playing = False
            self.underruns += 1
            return out

    def fill_ms(self, samplerate: int) -> float:
        with self._lock:
            return 1000.0 * len(self._buf) / samplerate


class AudioSpeaker(Node):
    def __init__(self):
        super().__init__('audio_speaker')

        # --- Parameters ---
        self.declare_parameter('audio_topic', 'uma16/audio')
        self.declare_parameter('channel', 0)
        self.declare_parameter('samplerate', 48000)
        self.declare_parameter('gain', 1.0)
        self.declare_parameter('prefill_ms', 300.0)
        self.declare_parameter('max_buffer_ms', 1000.0)
        self.declare_parameter('device', '')
        self.declare_parameter('blocksize', 1024)

        topic           = self.get_parameter('audio_topic').value
        self.channel    = int(self.get_parameter('channel').value)
        self.samplerate = int(self.get_parameter('samplerate').value)
        self.gain       = float(self.get_parameter('gain').value)
        prefill_ms      = float(self.get_parameter('prefill_ms').value)
        max_buffer_ms   = float(self.get_parameter('max_buffer_ms').value)
        device          = self.get_parameter('device').value
        blocksize       = int(self.get_parameter('blocksize').value)

        if sd is None:
            self.get_logger().fatal(
                f"sounddevice unavailable ({_SD_IMPORT_ERROR}). Install with:\n"
                "  sudo apt install libportaudio2\n"
                "  pip install sounddevice --break-system-packages"
            )
            raise RuntimeError('sounddevice unavailable')

        if max_buffer_ms <= prefill_ms:
            self.get_logger().warn(
                f"max_buffer_ms ({max_buffer_ms}) <= prefill_ms ({prefill_ms}); "
                f"raising max_buffer_ms to {2 * prefill_ms}."
            )
            max_buffer_ms = 2 * prefill_ms

        self._buffer = JitterBuffer(
            prefill=int(self.samplerate * prefill_ms / 1000.0),
            max_len=int(self.samplerate * max_buffer_ms / 1000.0),
        )
        self._clipped_chunks = 0
        self._warned_channel = False

        # --- Audio output ---
        device_arg = None
        if device != '':
            device_arg = int(device) if str(device).isdigit() else device

        self._stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype='float32',
            blocksize=blocksize,
            device=device_arg,
            callback=self._audio_callback,
        )
        self._stream.start()
        out_dev = sd.query_devices(self._stream.device)

        # --- ROS I/O ---
        self.create_subscription(Float32MultiArray, topic, self._audio_cb, 10)
        self._level_pub = self.create_publisher(Float32, 'audio_speaker/level_db', 10)
        self.create_timer(5.0, self._report_status)

        self.get_logger().info(
            f"audio_speaker ready — playing channel {self.channel} of '{topic}' "
            f"on '{out_dev['name']}' at {self.samplerate} Hz, gain={self.gain}, "
            f"prefill={prefill_ms:.0f} ms, max buffer={max_buffer_ms:.0f} ms"
        )

    # ------------------------------------------------------------------
    # Audio device callback (runs in the PortAudio thread)
    # ------------------------------------------------------------------

    def _audio_callback(self, outdata, frames, time_info, status) -> None:
        outdata[:, 0] = self._buffer.pull(frames)

    # ------------------------------------------------------------------
    # ROS subscriber callback
    # ------------------------------------------------------------------

    def _audio_cb(self, msg: Float32MultiArray) -> None:
        data = np.asarray(msg.data, dtype=np.float32)

        # Layout: dim[0] = frames, dim[1] = channels (UMA-16 convention).
        if len(msg.layout.dim) >= 2:
            n_ch = int(msg.layout.dim[1].size)
        else:
            n_ch = 1
        if n_ch < 1 or data.size % n_ch != 0:
            self.get_logger().warn(
                f"Malformed audio message: {data.size} values, {n_ch} channels; skipped.",
                throttle_duration_sec=5.0,
            )
            return

        frames = data.reshape(-1, n_ch)
        ch = self.channel
        if ch >= n_ch:
            if not self._warned_channel:
                self.get_logger().warn(
                    f"channel={ch} but message has {n_ch} channels; using channel 0."
                )
                self._warned_channel = True
            ch = 0

        mono = frames[:, ch] * self.gain

        # Level of the signal as received (before clipping), in dBFS.
        rms = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)))
        level_db = 20.0 * np.log10(rms) if rms > 0.0 else _DBFS_FLOOR
        self._level_pub.publish(Float32(data=float(max(level_db, _DBFS_FLOOR))))

        if np.abs(mono).max() > 1.0:
            self._clipped_chunks += 1
            mono = np.clip(mono, -1.0, 1.0)

        self._buffer.push(mono.astype(np.float32))

    # ------------------------------------------------------------------
    # Periodic status
    # ------------------------------------------------------------------

    def _report_status(self) -> None:
        b = self._buffer
        self.get_logger().info(
            f"buffer {b.fill_ms(self.samplerate):.0f} ms | underruns {b.underruns} | "
            f"dropped {b.dropped} samples | clipped chunks {self._clipped_chunks}"
        )

    def destroy_node(self) -> None:
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    try:
        node = AudioSpeaker()
    except Exception as e:  # sounddevice missing, bad device, etc.
        print(f"[audio_speaker] Fatal: {e}", file=sys.stderr)
        if rclpy.ok():
            rclpy.shutdown()
        return

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
