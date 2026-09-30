# Acoustic Beamforming Overlay Node

## General idea

`acoustic_overlay` computes an acoustic heatmap from the UMA-16's 16-channel audio using beamforming (via the [Acoular](https://acoular.org/) library), without talking to any hardware itself. It subscribes to `uma16/audio` (published by `stream_publisher` — see [uma16_nodes.md](uma16_nodes.md)) and has two mutually-exclusive modes, selected with the `mode` parameter:

### Default `mode:=plane` (original behaviour, kept as a fallback)

1. Each incoming audio chunk is fed into Acoular as an in-memory `TimeSamples` source (no HDF5/cache files are written).
2. `PowerSpectra` + `BeamformerBase` compute a 2D acoustic power map over a **fixed rectangular plane** at a fixed distance in front of the mic array, evaluated at one target frequency band.
3. The power map is converted to sound-pressure level in dB (`L_p`), optionally floored at a minimum level to suppress quiet noise, flattened, and published as `Float32MultiArray` on `/beamforming_heatmap`.

```
uma16_audio_publisher ──► uma16/audio ──► uma16_acoustic_overlay (mode=plane) ──► /beamforming_heatmap
```

### `mode:=depth` (beamforms over real 3D geometry using the depth camera)

Beamforms over a grid of (azimuth, elevation) *directions* instead of a fixed plane, and uses the depth camera to look up the real range along each direction. Each grid point lands on an actual surface in the scene instead of an assumed plane at a guessed distance.

1. Subscribes to a depth `Image` + matching `CameraInfo` (defaults: `/camera/depth/image_raw`, `/camera/depth/camera_info` — matches the Orbbec DaBai DCW2 setup documented in `~/rtabmap_bringup/README.md` on the robot).
2. For each direction in the angular scan grid, rotates the mic-frame direction vector into the depth camera's optical frame, projects it to a pixel, and reads that pixel's depth — giving a real 3D point per direction instead of a fixed-plane assumption.
3. Feeds those live 3D points into Acoular via `ImportGrid` (positions set directly, no XML round-trip) and runs the same `PowerSpectra` + `BeamformerBase` + `L_p` pipeline as plane mode.
4. Publishes a `sensor_msgs/PointCloud2` (fields `x, y, z, intensity` (dB value)) on `/beamforming_heatmap_3d`, in the depth camera's own frame, so it drops straight into RViz/`rtabmap_viz` using the TF tree already set up for RTAB-Map.

```
stream_publisher ──► uma16/audio ───────┐
                                        ├──► uma16_acoustic_overlay (mode=depth) ──► /beamforming_heatmap_3d (PointCloud2)
   depth camera ──► image + camera_info ┘
```

Both modes have **no GUI**, they only publish data; visualizing it is left to a separate consumer (`scripts/visualize_heatmap.py` for `plane` mode's `Float32MultiArray`, RViz/`rtabmap_viz` for `depth` mode's `PointCloud2`).

---

## Dependencies

Install at the system level, not inside a virtualenv. ROS 2 nodes use the system Python and cannot see venv packages.

```bash
pip3 install --user scipy acoular numpy
```

If pip refuses with an "externally-managed-environment" error:
```bash
pip3 install --break-system-packages scipy acoular numpy
```

ROS 2 packages required (included in a standard ROS 2 install): `rclpy`, `std_msgs`, `sensor_msgs`, `sensor_msgs_py`, `cv_bridge`, `tf2_ros`, `geometry_msgs`. `sensor_msgs_py`/`tf2_ros`/`geometry_msgs` and `cv_bridge`'s actual use are specific to `mode:=depth` (point cloud construction, TF lookups, and depth image decoding, respectively). `mode:=plane` doesn't need any of them at runtime, they're just always-declared build deps.

---

## Build

```bash
cd ros2_ws/src
colcon build
source install/setup.bash
```

---

## Running

Requires `stream_publisher` to already be running and publishing on `uma16/audio`.

`plane` mode (default, no camera needed):
```bash
ros2 run uma16_acoustic_overlay uma16_acoustic_overlay
```

`depth` mode (needs the depth camera already running and publishing depth image + camera info — see `~/rtabmap_bringup/README.md` on the robot for bringing that up):
```bash
ros2 run uma16_acoustic_overlay uma16_acoustic_overlay --ros-args -p mode:=depth
```

Or, as part of the full suite, via `./scripts/run_sensor_suit.sh` (see [scripts.md](scripts.md)) — currently wires up `plane` mode only.

Read the computed heatmap from the topic directly, e.g.:
```bash
ros2 topic echo /beamforming_heatmap      # plane mode
ros2 topic echo /beamforming_heatmap_3d   # depth mode
```

Stop with **Ctrl+C**.

---

## Visualizing the output

This node has no GUI, so the raw `Float32MultiArray` on `/beamforming_heatmap` needs a separate viewer to actually look at it. Options, easiest first:

### `scripts/visualize_heatmap.py` (recommended)

A small standalone matplotlib viewer is included at [`scripts/visualize_heatmap.py`](../scripts/visualize_heatmap.py). It subscribes to `/beamforming_heatmap`, reshapes the flattened data back into the 2D grid, and shows it live as a colour-mapped image with a colorbar (dB scale).

Requires matplotlib on top of the dependencies above:
```bash
pip3 install --user matplotlib
```

Run it (with the workspace sourced, alongside a running `uma16_acoustic_overlay`):
```bash
./scripts/visualize_heatmap.py
```

If you changed any `grid_x_min/max`, `grid_y_min/max`, or `grid_increment` parameter away from the defaults, pass the matching grid dimensions — read them off the `Grid shape: (...)` line the overlay node logs on startup:
```bash
./scripts/visualize_heatmap.py --grid-x 41 --grid-y 41
```

To point it at a differently-named topic:
```bash
./scripts/visualize_heatmap.py --topic /beamforming_heatmap
```

### Quick sanity checks without a GUI

To confirm data is flowing and see raw numbers, without any plotting:
```bash
ros2 topic hz /beamforming_heatmap
ros2 topic echo /beamforming_heatmap
```

`rqt_plot` can plot individual array elements as a line graph over time (e.g. `/beamforming_heatmap/data[0]`), but it's a 1D line plot, not a 2D heatmap — useful for confirming a value is changing at all, not for spatial localization. `rqt_image_view` cannot be used here since this topic is `Float32MultiArray`, not `sensor_msgs/Image`.

---

## Parameters

Pass parameters with `--ros-args -p name:=value`. Multiple parameters can be chained:
```bash
ros2 run uma16_acoustic_overlay uma16_acoustic_overlay \
  --ros-args -p freq_band:=2000 -p threshold_db:=40.0
```

### Mode

| Parameter | Default | Description |
|-----------|---------|-------------|
| `mode` | `plane` | `plane` = original fixed-plane scan (below, unchanged). `depth` = angular scan using the depth camera for range (below). Read once at startup — switching modes means restarting the node. |

### Audio input

| Parameter | Default | Description |
|-----------|---------|-------------|
| `samplerate` | `48000` | Sample rate in Hz passed to Acoular. Must match `uma16_audio_publisher`'s `samplerate`. |
| `channels` | `16` | Documented channel count. Not currently used to reshape incoming data — the actual frame/channel counts are read from each message's own layout dimensions, so this has no effect on processing today. |
| `chunk_size` | `8192` | Number of audio frames processed per heatmap update. Incoming messages are truncated or zero-padded to this length. Must match `chunk_size` on `uma16_audio_publisher`. |

### Beamforming

| Parameter | Default | Description |
|-----------|---------|-------------|
| `freq_band` | `8000` | Target frequency (Hz) that beamforming is evaluated at. Choose this based on the dominant frequency of the sound source you're trying to localize (see the frequency guide below). |
| `block_size` | `128` | FFT block size used by Acoular's `PowerSpectra`. Larger values give better frequency resolution but coarser time resolution and more CPU per update. |
| `grid_x_min` / `grid_x_max` | `-0.2` / `0.2` | Horizontal extent of the scan grid, in metres, centred on the array. |
| `grid_y_min` / `grid_y_max` | `-0.2` / `0.2` | Vertical extent of the scan grid, in metres. |
| `grid_z` | `-0.3` | Distance from the microphone array to the scan plane, in metres (negative = in front of the array, per Acoular's convention). |
| `grid_increment` | `0.01` | Spacing between grid points, in metres. Smaller = finer spatial resolution, more grid points, more CPU per update. |
| `mic_geom_file` | bundled `config/uma16_geom.xml` | Path to the Acoular mic-geometry XML describing the UMA-16's 4×4 element layout. Only change this if you're using different microphone hardware or a modified geometry file. Used by both modes. |

Everything above this point in the table is `mode:=plane`-only.

### Beamforming — `mode:=depth` only

| Parameter | Default | Description |
|-----------|---------|-------------|
| `depth_image_topic` | `/camera/depth/image_raw` | Depth `sensor_msgs/Image` topic. Must be `16UC1` (millimetres) or `32FC1` (metres) encoding. |
| `depth_camera_info_topic` | `/camera/depth/camera_info` | Matching `CameraInfo` — supplies the pinhole intrinsics (`fx, fy, cx, cy`) used to project scan directions to pixels. |
| `mic_frame_id` | `''` (unset) | TF frame of the mic array. Empty = assume the array is co-located with, and aimed the same physical direction as, the depth camera (see below for what "same direction" means precisely). Set to a real frame (e.g. `mic_link`) once the array's mount is measured and published as a static transform — same pattern as `camera_link` in `~/rtabmap_bringup/bringup_rtabmap.launch.py` on the robot. |
| `az_min_deg` / `az_max_deg` | `-35.0` / `35.0` | Azimuth sweep of the angular scan grid, in degrees. |
| `el_min_deg` / `el_max_deg` | `-25.0` / `25.0` | Elevation sweep, in degrees. |
| `angle_increment_deg` | `2.0` | Spacing between scan directions, in degrees. Smaller = finer angular resolution, more directions, more CPU per update (36×26=936 directions at the defaults). |
| `max_depth_age_sec` | `1.0` | Reject and skip a beamforming update if the most recent depth image is older than this (robot/scene may have moved since). |
| `min_range_m` / `max_range_m` | `0.2` / `6.0` | Depth samples outside this range are treated as invalid and excluded, same as a zero/NaN depth reading. |
| `depth_median_ksize` | `3` | Side length (pixels) of the median-filter window read around each sampled depth pixel, instead of trusting one raw pixel. See "Key parameters explained" below — this isn't just noise cleanup, it materially affects whether a real source is distinguishable from noise. |
| `intensity_smoothing_alpha` | `0.3` | Exponential-moving-average weight (0–1) applied per fixed scan direction across audio chunks: `new = alpha*current + (1-alpha)*previous`. `1.0` = no smoothing (raw per-chunk value). Lower = smoother/slower to react to a source moving or turning on/off; higher = noisier but more responsive. See below. |

### Output

| Parameter | Default | Description |
|-----------|---------|-------------|
| `threshold_db` | `-inf` (disabled) | `plane` mode: floors the heatmap (values below are clamped up to it, as `NaN`). `depth` mode: points below this dB value are dropped from the output point cloud entirely, rather than being included as low-value points. Either way, raise this above your ambient noise floor to make only genuinely loud regions stand out. |

---

## Key parameters explained

- **`chunk_size` must match `uma16_audio_publisher`'s `chunk_size`.** Every `uma16/audio` message is truncated or zero-padded to this many frames before being handed to Acoular; a mismatch either throws away real audio (if the publisher sends more frames per message than this) or pads with silence (if it sends fewer), degrading the beamforming result either way.
- **`freq_band`** determines what "loud" means in the resulting heatmap — beamforming isolates energy at (and near) this one frequency, not the whole spectrum. Picking the wrong band means a genuinely loud source at a different frequency may not show up at all. See the frequency guide below.
- **Grid parameters (`grid_x_min/max`, `grid_y_min/max`, `grid_z`, `grid_increment`) define the flat scan plane** beamforming searches over — a rectangle at a single fixed distance (`grid_z`) in front of the microphone array. The published heatmap's shape is `((grid_x_max - grid_x_min) / grid_increment + 1, (grid_y_max - grid_y_min) / grid_increment + 1)`, logged on startup as `Grid shape: (...)`. The `Float32MultiArray` payload is this grid flattened (transposed then flattened) — a consumer must reshape it using that same grid shape to recover the 2D map.
- **`threshold_db`** only affects the published heatmap values, not detection logic — there's no separate "is a source present" flag in this node. To find a good value, first log or print the raw range of published values in your environment with `threshold_db` disabled (the default), then set the parameter just above the quiet-noise level you observe.
- **`depth_median_ksize` / `intensity_smoothing_alpha` (`depth` mode) — why a real, loud source can still look like pure noise without these.** Near-field beamforming's steering vector is sensitive to small errors in the *assumed range* to each grid point, not just its direction. `depth` mode rebuilds the entire grid from a live depth frame every audio chunk (~150ms), and structured-light depth has a few cm of per-pixel noise — enough that the *same* physical bearing can resolve to a meaningfully different assumed range from one chunk to the next. The result, confirmed on real hardware while building this: a genuinely loud, stable, correctly-localized source can look exactly like noise flickering around with no clear peak, because the steering vector for that direction is quietly "detuning" itself frame to frame. `depth_median_ksize` (median-filters the depth reading itself, reducing the raw per-pixel noise going in) and `intensity_smoothing_alpha` (averages the resulting dB value over time *per fixed direction*, so a persistent source survives a few noisy frames) together fix this. Diagnostic signature if you suspect this is happening: log the dB range over several messages — a real source should show a small number of directions sitting well above the rest (e.g. the noise floor cluttered around -180dB with a tight cluster of directions around -20dB), consistently in *roughly* the same handful of directions message to message. If instead the "loudest" direction changes almost every message with no repeatable cluster, that's this problem.
- **`mic_frame_id` and the co-located default (`depth` mode) — read this before trusting the output.** The mic array's own coordinate convention (from `mic_geom_file`) has forward = **-Z** (same convention as `grid_z` being negative in `plane` mode). The depth camera's frame is a ROS optical frame, forward = **+Z**, X right, Y down (REP-103). Leaving `mic_frame_id` empty assumes the array is merely co-located with, and aimed the same real-world direction as, the camera — but "same direction" under two frames with *opposite* forward-axis sign still requires converting between them (a 180° rotation about the shared right/X axis), which the node does automatically for the default case. Getting this step wrong doesn't produce a subtly-off result — it makes every scan direction look like it's behind the camera and silently drops 100% of points (confirmed hitting exactly this while building the feature). If you set a real `mic_frame_id` once the array is calibrated, this conversion is handled by whatever rotation TF reports instead, and the left/right, up/down mapping for `az`/`el` should be verified empirically (e.g. a clap test — see [acoustic_3d_fusion_ideas.md](acoustic_3d_fusion_ideas.md), "Idea E") rather than assumed from the code.

---

## Frequency guide

Beamforming analyses one frequency band at a time. Choose `freq_band` based on what you are trying to locate:

| Sound source | Suggested `freq_band` (Hz) |
|---|---|
| Clapping, finger snap | 1000–3000 |
| Talking (voice) | 500–2000 |
| High-pitched machinery, fan | 4000–8000 |
| Low hum, motor | 100–500 |

If unsure, start around 2000 Hz and adjust based on which value gives the clearest hotspot for your source.

---

## Topics

| Topic | Message type | Direction |
|-------|-------------|-----------|
| `uma16/audio` | `std_msgs/msg/Float32MultiArray` | input — from `uma16_audio_publisher`, both modes |
| `/beamforming_heatmap` | `std_msgs/msg/Float32MultiArray` | output, `mode:=plane` — flattened dB-scale heatmap, reshape using the logged grid shape |
| *(`depth_image_topic` param)* | `sensor_msgs/msg/Image` | input, `mode:=depth` only — default `/camera/depth/image_raw` |
| *(`depth_camera_info_topic` param)* | `sensor_msgs/msg/CameraInfo` | input, `mode:=depth` only — default `/camera/depth/camera_info` |
| `/beamforming_heatmap_3d` | `sensor_msgs/msg/PointCloud2` | output, `mode:=depth` only — fields `x, y, z, intensity` (dB), in the depth camera's frame |

---

## Troubleshooting

**`Error computing heatmap` logged every message:** Usually a shape mismatch — confirm `chunk_size` matches `uma16_audio_publisher`, and that the publisher is actually running (`ros2 topic hz uma16/audio`).

**Heatmap values look identical everywhere / no visible hotspot:** Check `freq_band` against your actual sound source's dominant frequency, and confirm `grid_z` is roughly the real distance from the array to the source.

**`No module named 'acoular'` or `No module named 'scipy'`:** These were installed into a virtualenv. Install at the system level instead:
```bash
deactivate
pip3 install --user scipy acoular
```

**`mode:=depth` — `"No valid depth samples in the angular scan window"` logged every message:** Most likely causes, in order of likelihood:
1. The depth camera isn't actually running, or isn't running on `depth_image_topic`/`depth_camera_info_topic` — check `ros2 topic hz <depth_image_topic>`.
2. The scan window (`az_min/max_deg`, `el_min/max_deg`) doesn't overlap the camera's actual FOV, or `min_range_m`/`max_range_m` don't match the scene (e.g. pointed at something farther than `max_range_m`).
3. A coordinate-convention bug — this exact symptom (100% of points rejected, not just some) is what a wrong `mic_frame_id`-related rotation looks like, since it makes every direction look like it's behind the camera. See the `mic_frame_id` entry above under "Key parameters explained" — confirmed and fixed once already while building this feature, worth re-checking first if this parameter's default handling is ever changed.

**`mode:=depth` — `"Waiting for depth image / camera info..."` logged every message:** The depth topics aren't publishing yet, or the topic names don't match — check `depth_image_topic`/`depth_camera_info_topic` against what's actually running (`ros2 topic list | grep camera`).

**`mode:=depth` — `"Depth image is N.NNs old"` logged repeatedly:** The depth camera feed has stalled (check it's still alive) or `max_depth_age_sec` is set tighter than the actual depth camera's update rate.

**`mode:=depth` — output looks like pure noise / no visible hotspot even with a known loud source present, and no warnings are logged:** This isn't a shape/connectivity error, so nothing gets logged — it's the near-field range-sensitivity issue described under `depth_median_ksize` above. First check it's actually this and not just "no real source in view": collect several messages and look at the *set* of directions with the highest dB, not just one message. A real source shows up as a small, repeatable cluster of directions sitting clearly above a much quieter, consistent background (background will often look like a `-150` to `-350` dB floor — that's expected, it's silence, not a bug). If instead the loudest direction keeps changing to somewhere basically random each message, increase `depth_median_ksize` and/or lower `intensity_smoothing_alpha` (more smoothing) and check again.
