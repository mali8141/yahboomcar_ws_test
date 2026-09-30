#!/usr/bin/env python3
"""
Beamforming compute node that subscribes to uma16/audio (published by uma16_audio_publisher)
and computes an acoustic heatmap without connecting directly to the hardware.

Two modes, selected with the 'mode' parameter:

- 'plane' (default): the original behaviour. Beamforms over a fixed rectangular
  plane at a fixed distance in front of the mic array, published as a flattened
  Float32MultiArray on /beamforming_heatmap. Kept unchanged as a fallback.

- 'depth': beamforms over a grid of directions instead of a
  fixed plane and uses the depth camera to look up the actual range along each
  direction, so each grid point lands on a real 3D surface instead of an assumed
  plane. Published as a sensor_msgs/PointCloud2 (x, y, z, intensity=dB) on
  /beamforming_heatmap_3d, in the depth camera's own frame, so it drops straight
  into the existing TF tree for viewing in RViz/rtabmap_viz.
"""
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
from sensor_msgs_py import point_cloud2

import os
import numpy as np
import acoular as ac
import warnings

from cv_bridge import CvBridge
import tf2_ros
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException

warnings.filterwarnings("ignore")


def quat_to_rotation_matrix(x, y, z, w):
    """Quaternion (x, y, z, w) -> 3x3 rotation matrix."""
    n = np.sqrt(x * x + y * y + z * z + w * w)
    if n < 1e-9:
        return np.eye(3)
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


class BeamformingComputeFromTopicNode(Node):
    def __init__(self):
        super().__init__('beamforming_compute_from_topic')

        # --- Mode ---
        self.declare_parameter('mode', 'plane')  # 'plane' (fallback) or 'depth'
        self.mode = self.get_parameter('mode').value

        # --- Shared parameters ---
        self.declare_parameter('samplerate', 48000)
        self.declare_parameter('channels', 16)
        self.declare_parameter('chunk_size', 8192)  #! needs to be the same as in uma16_audio_publisher
        self.declare_parameter('freq_band', 8000)
        self.declare_parameter('mic_geom_file', os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'config/uma16_geom.xml'
        ))
        self.declare_parameter('block_size', 128)
        self.declare_parameter('threshold_db', -np.inf)

        self.fs = self.get_parameter('samplerate').value
        self.num_channels = self.get_parameter('channels').value
        self.chunk_size = self.get_parameter('chunk_size').value
        self.freq_band = self.get_parameter('freq_band').value
        self.block_size = self.get_parameter('block_size').value
        self.threshold_db = self.get_parameter('threshold_db').value
        self.mic_geom_file = self.get_parameter('mic_geom_file').value

        self.get_logger().info("Initializing mic geometry...")
        self.mg = ac.MicGeom(file=self.mic_geom_file)

        if self.mode == 'depth':
            self._init_depth_mode()
        else:
            self._init_plane_mode()

        # --- Subscriber (shared) ---
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'uma16/audio',
            self.audio_callback,
            10,
        )
        self.get_logger().info(f"Compute Node (from topic) is Live and Publishing... [mode={self.mode}]")

    # ------------------------------------------------------------------
    # 'plane' mode (original, unchanged behaviour)
    # ------------------------------------------------------------------
    def _init_plane_mode(self):
        self.declare_parameter('grid_x_min', -0.2)
        self.declare_parameter('grid_x_max', 0.2)
        self.declare_parameter('grid_y_min', -0.2)
        self.declare_parameter('grid_y_max', 0.2)
        self.declare_parameter('grid_z', -0.3)
        self.declare_parameter('grid_increment', 0.01)

        self.get_logger().info("Initializing plane grid and steering vector...")
        self.rg = ac.RectGrid(
            x_min=self.get_parameter('grid_x_min').value,
            x_max=self.get_parameter('grid_x_max').value,
            y_min=self.get_parameter('grid_y_min').value,
            y_max=self.get_parameter('grid_y_max').value,
            z=self.get_parameter('grid_z').value,
            increment=self.get_parameter('grid_increment').value,
        )
        self.st = ac.SteeringVector(grid=self.rg, mics=self.mg)
        self.grid_shape = (
            int((self.get_parameter('grid_x_max').value - self.get_parameter('grid_x_min').value) / self.get_parameter('grid_increment').value) + 1,
            int((self.get_parameter('grid_y_max').value - self.get_parameter('grid_y_min').value) / self.get_parameter('grid_increment').value) + 1,
        )
        self.get_logger().info(f"Grid shape: {self.grid_shape}")

        self.publisher_ = self.create_publisher(Float32MultiArray, '/beamforming_heatmap', 10)

    def _compute_plane(self, audio_2d):
        ts = ac.TimeSamples(data=audio_2d, sample_freq=float(self.fs))
        ps = ac.PowerSpectra(source=ts, block_size=self.block_size, window='Hanning', cached=False)
        bb = ac.BeamformerBase(freq_data=ps, steer=self.st, cached=False)
        pm = bb.synthetic(self.freq_band, 3)
        Lm = ac.L_p(pm)

        if np.isfinite(self.threshold_db):
            Lm = np.where(Lm < self.threshold_db, np.nan, Lm)

        heat_msg = Float32MultiArray()
        heat_msg.data = Lm.T.flatten().tolist()
        self.publisher_.publish(heat_msg)

    # ------------------------------------------------------------------
    # 'depth' mode: angular scan, range from the depth camera
    # ------------------------------------------------------------------
    def _init_depth_mode(self):
        self.declare_parameter('depth_image_topic', '/camera/depth/image_raw')
        self.declare_parameter('depth_camera_info_topic', '/camera/depth/camera_info')
        self.declare_parameter('mic_frame_id', '')
        self.declare_parameter('az_min_deg', -35.0)
        self.declare_parameter('az_max_deg', 35.0)
        self.declare_parameter('el_min_deg', -25.0)
        self.declare_parameter('el_max_deg', 25.0)
        self.declare_parameter('angle_increment_deg', 2.0)
        self.declare_parameter('max_depth_age_sec', 1.0)
        self.declare_parameter('min_range_m', 0.2)
        self.declare_parameter('max_range_m', 6.0)

        self.depth_image_topic = self.get_parameter('depth_image_topic').value
        self.depth_camera_info_topic = self.get_parameter('depth_camera_info_topic').value
        self.mic_frame_id = self.get_parameter('mic_frame_id').value
        self.max_depth_age_sec = self.get_parameter('max_depth_age_sec').value
        self.min_range_m = self.get_parameter('min_range_m').value
        self.max_range_m = self.get_parameter('max_range_m').value

        self.declare_parameter('depth_median_ksize', 3)
        self.declare_parameter('intensity_smoothing_alpha', 0.3)
        self.depth_median_ksize = self.get_parameter('depth_median_ksize').value
        self.intensity_smoothing_alpha = self.get_parameter('intensity_smoothing_alpha').value

        az = np.deg2rad(np.arange(
            self.get_parameter('az_min_deg').value,
            self.get_parameter('az_max_deg').value + 1e-6,
            self.get_parameter('angle_increment_deg').value,
        ))
        el = np.deg2rad(np.arange(
            self.get_parameter('el_min_deg').value,
            self.get_parameter('el_max_deg').value + 1e-6,
            self.get_parameter('angle_increment_deg').value,
        ))
        az_grid, el_grid = np.meshgrid(az, el)
        az_flat = az_grid.ravel()
        el_flat = el_grid.ravel()

        # Unit direction vectors in the mic array's own frame. Matches the array's
        # existing convention (mic_geom has all capsules at z=0, and the old plane
        # mode's grid_z is negative "in front" of the array) -> forward = -Z.
        # az=0/el=0 points straight ahead; az sweeps in the X-Z plane, el sweeps Y.
        # Which physical direction "az positive" / "el positive" actually points on
        # the real robot depends on how the array is mounted -- verify empirically
        # (e.g. a clap test) once mic_frame_id is calibrated, don't assume this from
        # the code alone.
        self._dirs_mic = np.stack([
            np.sin(az_flat) * np.cos(el_flat),
            np.sin(el_flat),
            -np.cos(az_flat) * np.cos(el_flat),
        ])  # shape (3, N)

        self.get_logger().info(
            f"Angular grid: {az_grid.shape[1]} az x {az_grid.shape[0]} el = {self._dirs_mic.shape[1]} directions"
        )

        self.bridge = CvBridge()
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Cached mic<-camera extrinsic, used until a real mic_frame_id is set and a
        # successful TF lookup updates it. NOT identity: the mic array follows
        # Acoular's convention (forward = -Z, matching the old plane mode's negative
        # grid_z), while the depth camera's frame is a ROS optical frame (forward =
        # +Z, X right, Y down, REP-103). Assuming the array is merely co-located and
        # aimed the same physical direction as the camera -- the most sensible
        # zero-config default -- still requires converting between these two
        # opposite forward-axis conventions, i.e. a 180 degree rotation about the
        # shared right/X axis. Getting this wrong doesn't produce a subtly-off
        # result, it makes every direction look like it's behind the camera and
        # rejects 100% of samples -- confirmed on real hardware while testing this.
        self._mic_from_cam_R = np.diag([1.0, -1.0, -1.0])
        self._mic_from_cam_t = np.zeros(3)

        # Per-direction exponential moving average of dB, indexed by position in the
        # fixed (az, el) grid (see intensity_smoothing_alpha below for why).
        self._ema_dB = np.full(self._dirs_mic.shape[1], np.nan)

        self.latest_depth_msg = None
        self.latest_camera_info = None
        self.depth_sub = self.create_subscription(Image, self.depth_image_topic, self._depth_cb, 5)
        self.info_sub = self.create_subscription(CameraInfo, self.depth_camera_info_topic, self._info_cb, 5)

        self.publisher_3d_ = self.create_publisher(PointCloud2, '/beamforming_heatmap_3d', 10)

    def _depth_cb(self, msg):
        self.latest_depth_msg = msg

    def _info_cb(self, msg):
        self.latest_camera_info = msg

    def _update_extrinsic(self, camera_frame_id, stamp):
        """Refresh the cached mic<-camera rotation/translation from TF, if configured.
        Falls back to (and keeps using) the last-good value on failure, so a missing
        or not-yet-published mic_frame_id degrades to the co-located assumption
        instead of blocking output entirely."""
        if not self.mic_frame_id:
            return
        try:
            t = self.tf_buffer.lookup_transform(self.mic_frame_id, camera_frame_id, stamp)
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(
                f"TF {self.mic_frame_id} <- {camera_frame_id} unavailable ({e}); "
                "using last-known/identity extrinsic.",
                throttle_duration_sec=5.0,
            )
            return
        q = t.transform.rotation
        tr = t.transform.translation
        self._mic_from_cam_R = quat_to_rotation_matrix(q.x, q.y, q.z, q.w)
        self._mic_from_cam_t = np.array([tr.x, tr.y, tr.z])

    def _compute_depth(self):
        depth_msg = self.latest_depth_msg
        info_msg = self.latest_camera_info
        if depth_msg is None or info_msg is None:
            self.get_logger().warn(
                f"Waiting for depth image ({self.depth_image_topic}) / camera info "
                f"({self.depth_camera_info_topic})...",
                throttle_duration_sec=5.0,
            )
            return None

        age = (self.get_clock().now() - rclpy.time.Time.from_msg(depth_msg.header.stamp)).nanoseconds / 1e9
        if age > self.max_depth_age_sec:
            self.get_logger().warn(
                f"Depth image is {age:.2f}s old (> max_depth_age_sec={self.max_depth_age_sec}s), skipping.",
                throttle_duration_sec=5.0,
            )
            return None

        self._update_extrinsic(depth_msg.header.frame_id, depth_msg.header.stamp)

        depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='passthrough')
        if depth_msg.encoding == '16UC1':
            depth = depth.astype(np.float32) / 1000.0
        elif depth_msg.encoding == '32FC1':
            depth = depth.astype(np.float32)
        else:
            self.get_logger().error(f"Unsupported depth encoding '{depth_msg.encoding}'")
            return None
        height, width = depth.shape

        k = info_msg.k
        fx, fy, cx, cy = k[0], k[4], k[2], k[5]

        # Rotate mic-frame directions into the camera optical frame, project to pixels.
        cam_from_mic_R = self._mic_from_cam_R.T
        dirs_cam = cam_from_mic_R @ self._dirs_mic  # (3, N)

        in_front = dirs_cam[2] > 1e-6
        u = np.full(dirs_cam.shape[1], -1.0)
        v = np.full(dirs_cam.shape[1], -1.0)
        u[in_front] = fx * dirs_cam[0, in_front] / dirs_cam[2, in_front] + cx
        v[in_front] = fy * dirs_cam[1, in_front] / dirs_cam[2, in_front] + cy

        ui = np.round(u).astype(int)
        vi = np.round(v).astype(int)
        valid = in_front & (ui >= 0) & (ui < width) & (vi >= 0) & (vi < height)

        # Median-filter depth over a small pixel window around each sampled point,
        # rather than reading one raw pixel. Structured-light depth has several cm
        # of per-pixel noise; near-field beamforming steering is sensitive to small
        # per-point range errors, so single-pixel sampling was making the same
        # nominal direction resolve to a meaningfully different assumed range (and
        # therefore a different steering vector) from one audio chunk to the next --
        # this is what was making a real, consistent loud direction look like noise
        # jumping around frame to frame. See intensity_smoothing_alpha below too.
        half_k = self.depth_median_ksize // 2
        z = np.full(dirs_cam.shape[1], np.nan)
        idxs = np.where(valid)[0]
        for idx in idxs:
            r, c = vi[idx], ui[idx]
            window = depth[max(0, r - half_k):r + half_k + 1, max(0, c - half_k):c + half_k + 1]
            window = window[np.isfinite(window) & (window > 0)]
            if window.size > 0:
                z[idx] = np.median(window)
        valid &= np.isfinite(z) & (z >= self.min_range_m) & (z <= self.max_range_m)

        if not np.any(valid):
            self.get_logger().warn("No valid depth samples in the angular scan window.", throttle_duration_sec=5.0)
            return None

        full_idx = np.where(valid)[0]
        zi = z[valid]
        p_cam = np.stack([
            (ui[valid] - cx) * zi / fx,
            (vi[valid] - cy) * zi / fy,
            zi,
        ])  # (3, M) in the depth camera's own frame -- used directly for publishing

        p_mic = self._mic_from_cam_R @ p_cam + self._mic_from_cam_t[:, None]  # (3, M), for beamforming

        return p_cam, p_mic, full_idx, depth_msg.header.frame_id, depth_msg.header.stamp

    def _beamform_and_publish_depth(self, audio_2d, p_cam, p_mic, full_idx, frame_id, stamp):
        grid = ac.ImportGrid()
        grid.pos = p_mic
        st = ac.SteeringVector(grid=grid, mics=self.mg)

        ts = ac.TimeSamples(data=audio_2d, sample_freq=float(self.fs))
        ps = ac.PowerSpectra(source=ts, block_size=self.block_size, window='Hanning', cached=False)
        bb = ac.BeamformerBase(freq_data=ps, steer=st, cached=False)
        pm = bb.synthetic(self.freq_band, 3)
        Lm = ac.L_p(pm).ravel()

        # Smooth per fixed (az, el) grid direction (not per 3D position, which
        # shifts every frame) -- a real, physically-stable loud direction should
        # persist here across several audio chunks even if any single chunk's
        # per-point depth/range noise makes it noisy on its own. See the note on
        # depth_median_ksize above for the other half of this fix.
        alpha = self.intensity_smoothing_alpha
        prev = self._ema_dB[full_idx]
        has_prev = np.isfinite(prev)
        smoothed = np.where(has_prev, alpha * Lm + (1 - alpha) * prev, Lm)
        self._ema_dB[full_idx] = smoothed
        Lm = smoothed

        keep = np.isfinite(Lm)
        if np.isfinite(self.threshold_db):
            keep &= Lm >= self.threshold_db
        if not np.any(keep):
            return

        header = self.latest_depth_msg.header
        header.frame_id = frame_id
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
        ]
        points = np.column_stack([p_cam[0, keep], p_cam[1, keep], p_cam[2, keep], Lm[keep]]).astype(np.float32)
        cloud = point_cloud2.create_cloud(header, fields, points)
        self.publisher_3d_.publish(cloud)

    # ------------------------------------------------------------------
    def audio_callback(self, msg):
        """Reconstruct 2D audio frames from the incoming ROS message and compute heatmap."""
        num_frames = msg.layout.dim[0].size
        num_ch = msg.layout.dim[1].size
        audio_2d = np.array(msg.data, dtype=np.float32).reshape((num_frames, num_ch))

        if num_frames < self.chunk_size:
            padded = np.zeros((self.chunk_size, num_ch), dtype=np.float32)
            padded[:num_frames, :] = audio_2d
            audio_2d = padded
        else:
            audio_2d = audio_2d[:self.chunk_size, :]

        try:
            if self.mode == 'depth':
                result = self._compute_depth()
                if result is None:
                    return
                p_cam, p_mic, full_idx, frame_id, stamp = result
                self._beamform_and_publish_depth(audio_2d, p_cam, p_mic, full_idx, frame_id, stamp)
            else:
                self._compute_plane(audio_2d)
        except Exception as e:
            self.get_logger().error(f"Error computing heatmap: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = BeamformingComputeFromTopicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Compute node (from topic) stopped.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
