import json
import os
import tempfile
import wave
from datetime import datetime, timezone

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Float32, String
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException


class AudioRecorderNode(Node):
    """
    Records a WAV clip whenever it receives a trigger message from another
    ROS2 node, and nothing else - no continuous audio-signature mapping.

    Subscribes to:
      - uma16/audio (Float32MultiArray): raw multi-channel audio chunks.
        Only consumed while a recording is in progress.
      - audio_mapper/trigger_recording (std_msgs/Float32): triggers a
        recording. `data` is the requested length in seconds; a value <= 0
        falls back to `default_recording_duration`.

    Publishes:
      - audio_mapper/recording_done (std_msgs/String): a JSON payload with
        the full metadata entry for the recording that was just completed
        (or a failure reason), so the triggering node can read it straight
        off the ack without re-opening the metadata file.

    On completion of a recording, writes a .wav file to disk and appends
    an entry (filename, timestamps, duration, robot position, etc.) to a
    JSON metadata file. No analysis (e.g. frequency signatures) is done
    here - that's left to whichever node consumes the recordings.
    """

    def __init__(self):
        super().__init__('audio_recorder')

        self.declare_parameter('audio_topic', 'uma16/audio')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('sample_rate', 48000)
        self.declare_parameter('save_dir', '~/maps/audio_map')

        self.declare_parameter('recording_trigger_topic', 'audio_mapper/trigger_recording')
        self.declare_parameter('recording_done_topic', 'audio_mapper/recording_done')
        self.declare_parameter('recording_context_topic', 'audio_mapper/recording_context')
        self.declare_parameter('default_recording_duration', 60.0)  # seconds
        self.declare_parameter('max_recording_duration', 300.0)     # seconds, safety clamp
        self.declare_parameter('recording_channel', -1)             # -1 = record all channels
        self.declare_parameter('recordings_subdir', 'recordings')
        self.declare_parameter('recordings_metadata_filename', 'recordings_metadata.json')

        self.audio_topic = self.get_parameter('audio_topic').value
        self.map_frame = self.get_parameter('map_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.sample_rate = self.get_parameter('sample_rate').value
        self.save_dir = os.path.expanduser(self.get_parameter('save_dir').value)

        self.recording_trigger_topic = self.get_parameter('recording_trigger_topic').value
        self.recording_done_topic = self.get_parameter('recording_done_topic').value
        self.recording_context_topic = self.get_parameter('recording_context_topic').value
        self.default_recording_duration = float(self.get_parameter('default_recording_duration').value)
        self.max_recording_duration = float(self.get_parameter('max_recording_duration').value)
        self.recording_channel = int(self.get_parameter('recording_channel').value)
        self.recordings_dir = os.path.join(self.save_dir, self.get_parameter('recordings_subdir').value)
        self.recordings_metadata_path = os.path.join(
            self.save_dir, self.get_parameter('recordings_metadata_filename').value
        )
        self.run_save_dir = None

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # --- recording state ---
        self.recording_active = False
        self.recording_chunks = []       # list of (frames, channels) float32 arrays
        self.recording_frames_collected = 0
        self.recording_target_frames = 0
        self.recording_requested_duration = 0.0
        self.recording_start_wall_time = None
        self.recording_start_pose = None
        self.recording_channel_count = None
        self._recording_counter = 0

        self.audio_sub = self.create_subscription(
            Float32MultiArray,
            self.audio_topic,
            self._audio_callback,
            10
        )

        self.trigger_sub = self.create_subscription(
            Float32,
            self.recording_trigger_topic,
            self._trigger_recording_callback,
            10
        )
        self.context_sub = self.create_subscription(
            String, self.recording_context_topic, self._recording_context_callback, 10
        )

        self.done_pub = self.create_publisher(
            String,
            self.recording_done_topic,
            rclpy.qos.QoSProfile(
                depth=1,
                reliability=rclpy.qos.ReliabilityPolicy.RELIABLE,
                durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL,
            )
        )

        self.get_logger().info(
            f"Audio recorder armed on '{self.recording_trigger_topic}' "
            f"(default duration={self.default_recording_duration}s, "
            f"max={self.max_recording_duration}s) -> {self.recordings_dir}"
        )

    # ------------------------------------------------------------------
    # Audio ingestion - only kept while a recording is active
    # ------------------------------------------------------------------
    def _audio_callback(self, msg: Float32MultiArray):
        if not self.recording_active:
            return

        if len(msg.layout.dim) < 2:
            return

        frames = msg.layout.dim[0].size
        channels = msg.layout.dim[1].size
        data = np.array(msg.data, dtype=np.float32).reshape(frames, channels)

        self.recording_channel_count = channels
        self.recording_chunks.append(data)
        self.recording_frames_collected += frames

        if self.recording_frames_collected >= self.recording_target_frames:
            self._finalize_recording()

    def _get_robot_pose(self):
        """Look up the robot's current pose in the map frame via TF.
        Returns a dict {x, y, z, frame} or None if the lookup fails."""
        try:
            transform = self.tf_buffer.lookup_transform(
                self.map_frame, self.base_frame, rclpy.time.Time()
            )
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(f"TF lookup ({self.map_frame} -> {self.base_frame}) failed: {e}")
            return None

        return {
            'x': transform.transform.translation.x,
            'y': transform.transform.translation.y,
            'z': transform.transform.translation.z,
            'frame': self.map_frame,
        }

    # ------------------------------------------------------------------
    # On-demand WAV recording, triggered by another node
    # ------------------------------------------------------------------
    def _recording_context_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
            run_dir_value = payload.get('run_dir')
            if not run_dir_value:
                self.run_save_dir = None
                self.get_logger().info('Patrol recording context cleared')
                return
            run_dir = os.path.realpath(os.path.expanduser(run_dir_value))
        except (KeyError, TypeError, json.JSONDecodeError):
            self.get_logger().warn('Ignoring invalid recording context message')
            return
        if not os.path.isdir(run_dir):
            self.get_logger().warn(f'Ignoring recording context with missing directory: {run_dir}')
            return
        self.run_save_dir = run_dir
        self.get_logger().info(f'Patrol recordings will be saved under {run_dir}')

    def _trigger_recording_callback(self, msg: Float32):
        if self.recording_active:
            self.get_logger().warn(
                "Recording trigger received but a recording is already in progress - ignoring."
            )
            return

        requested_duration = float(msg.data) if msg.data and msg.data > 0 else self.default_recording_duration
        if requested_duration > self.max_recording_duration:
            self.get_logger().warn(
                f"Requested recording duration {requested_duration}s exceeds max "
                f"({self.max_recording_duration}s); clamping."
            )
            requested_duration = self.max_recording_duration

        self.recording_requested_duration = requested_duration
        self.recording_target_frames = int(requested_duration * self.sample_rate)
        self.recording_chunks = []
        self.recording_frames_collected = 0
        self.recording_channel_count = None
        self.recording_start_wall_time = datetime.now(timezone.utc)
        self.recording_start_pose = self._get_robot_pose()

        self.recording_active = True
        self.get_logger().info(
            f"Recording triggered: duration={requested_duration:.1f}s "
            f"(~{self.recording_target_frames} frames @ {self.sample_rate}Hz)"
        )

    def _finalize_recording(self):
        self.recording_active = False

        if not self.recording_chunks:
            self.get_logger().warn("Recording finished with no audio captured - skipping save.")
            self._publish_done({'status': 'failed', 'reason': 'no_audio_captured'})
            return

        audio = np.concatenate(self.recording_chunks, axis=0)  # (frames, channels)
        # Trim any overshoot so the file matches the requested duration.
        if audio.shape[0] > self.recording_target_frames:
            audio = audio[:self.recording_target_frames, :]

        if self.recording_channel_count is None:
            self.recording_channel_count = audio.shape[1]

        # Select channel(s) to write out.
        if self.recording_channel is not None and self.recording_channel >= 0:
            ch = min(self.recording_channel, audio.shape[1] - 1)
            out_audio = audio[:, ch:ch + 1]
        else:
            out_audio = audio

        actual_duration = out_audio.shape[0] / float(self.sample_rate)

        end_pose = self._get_robot_pose()
        end_wall_time = datetime.now(timezone.utc)

        save_dir = self.run_save_dir or self.save_dir
        recordings_dir = os.path.join(save_dir, self.get_parameter('recordings_subdir').value)
        metadata_path = os.path.join(
            save_dir, self.get_parameter('recordings_metadata_filename').value)
        os.makedirs(recordings_dir, exist_ok=True)

        self._recording_counter += 1
        timestamp_str = self.recording_start_wall_time.strftime('%Y%m%dT%H%M%SZ')
        filename = f"recording_{self._recording_counter:04d}_{timestamp_str}.wav"
        filepath = os.path.join(recordings_dir, filename)

        self._write_wav(filepath, out_audio, self.sample_rate)
        if not self._recording_file_ready(filepath):
            self.get_logger().error(
                f"Recording was written but is not ready to read: {filepath}"
            )
            self._publish_done({
                'status': 'failed',
                'reason': f'recording_file_not_ready: {filepath}',
            })
            self.recording_chunks = []
            self.recording_frames_collected = 0
            self.recording_target_frames = 0
            self.recording_channel_count = None
            self.recording_start_pose = None
            self.recording_start_wall_time = None
            return

        entry = {
            'id': self._recording_counter,
            'filename': filename,
            'filepath': filepath,
            'start_time_utc': self.recording_start_wall_time.isoformat(),
            'end_time_utc': end_wall_time.isoformat(),
            'requested_duration_s': self.recording_requested_duration,
            'actual_duration_s': round(actual_duration, 3),
            'sample_rate': self.sample_rate,
            'channels_recorded': out_audio.shape[1],
            'source_channel_count': self.recording_channel_count,
            'channel_selection': 'all' if self.recording_channel < 0 else self.recording_channel,
            'start_position': self.recording_start_pose,
            'end_position': end_pose,
        }

        self._append_recording_metadata(entry, metadata_path)

        # Include the full entry in the ack so the caller can read the
        # newest recording's metadata immediately, without re-reading the
        # metadata file from disk.
        self._publish_done({'status': 'done', 'entry': entry})

        pos_str = "unknown position"
        if end_pose is not None:
            pos_str = f"({end_pose['x']:.2f}, {end_pose['y']:.2f}) in '{end_pose['frame']}'"
        self.get_logger().info(
            f"Saved recording '{filename}' ({actual_duration:.1f}s) at {pos_str}"
        )

        # Reset state for the next trigger.
        self.recording_chunks = []
        self.recording_frames_collected = 0
        self.recording_target_frames = 0
        self.recording_channel_count = None
        self.recording_start_pose = None
        self.recording_start_wall_time = None

    def _publish_done(self, payload: dict):
        msg = String()
        msg.data = json.dumps(payload)
        self.done_pub.publish(msg)

    @staticmethod
    def _write_wav(filepath, audio_float, sample_rate):
        """Write a (frames, channels) float32 array (assumed range ~[-1, 1])
        to a 16-bit PCM WAV file."""
        n_channels = audio_float.shape[1]
        clipped = np.clip(audio_float, -1.0, 1.0)
        audio_int16 = (clipped * 32767.0).astype(np.int16)

        recordings_dir = os.path.dirname(filepath)
        fd, temporary_path = tempfile.mkstemp(
            prefix='.recording_', suffix='.wav', dir=recordings_dir)
        os.close(fd)
        try:
            with wave.open(temporary_path, 'wb') as wf:
                wf.setnchannels(n_channels)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            with open(temporary_path, 'rb') as audio_file:
                os.fsync(audio_file.fileno())
            os.replace(temporary_path, filepath)

            directory_fd = os.open(recordings_dir, os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _recording_file_ready(filepath):
        try:
            if not os.path.isfile(filepath) or os.path.getsize(filepath) <= 44:
                return False
            with wave.open(filepath, 'rb') as wf:
                return wf.getnframes() > 0
        except (OSError, wave.Error):
            return False

    def _append_recording_metadata(self, entry, metadata_path=None):
        """Append a recording entry to the JSON metadata file, preserving
        any entries already written in previous runs."""
        metadata_path = metadata_path or self.recordings_metadata_path
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

        records = []
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    records = json.load(f)
                if not isinstance(records, list):
                    self.get_logger().warn(
                        f"{metadata_path} did not contain a list - "
                        "starting a new one."
                    )
                    records = []
            except (json.JSONDecodeError, OSError) as e:
                self.get_logger().warn(
                    f"Could not read existing recordings metadata ({e}); starting a new file."
                )
                records = []

        records.append(entry)

        with open(metadata_path, 'w') as f:
            json.dump(records, f, indent=2)

    def destroy_node(self):
        if self.recording_active:
            self.get_logger().warn("Node shutting down mid-recording; discarding incomplete recording.")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AudioRecorderNode()
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