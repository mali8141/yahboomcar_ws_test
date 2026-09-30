#!/usr/bin/env python3
"""Visualize recorded audio clips as an interpolated heatmap overlaid on the occupancy grid.

Each triggered recording is a standalone .wav file placed at the robot's
position when it was captured. This tool reads every recording's audio,
computes a frequency-band intensity for it on the fly, and interpolates
those scattered points into a heatmap - no pre-built audio grid is needed.

Usage:
    python3 view_audio_map.py
    python3 view_audio_map.py --point 12
    python3 view_audio_map.py realworld_ws/data --radius 0.5 --bins 64

Click the band button to cycle through frequency bands. Click a recording point
to view its spectrogram in the third panel, or use --point with a recording ID
or filename to select one on startup.

Expects the directory to contain:
    - map.pgm + map.yaml           (from nav2 map_saver, optional - only used
                                     for the background overlay)
    - recordings_metadata.json     (from audio_recorder node)
    - recordings/*.wav             (from audio_recorder node)
"""
import argparse
import json
import sys
import wave
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.widgets import Button
from PIL import Image
from scipy.interpolate import RBFInterpolator
from scipy.signal import spectrogram


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------
def load_occupancy_map(map_dir: Path):
    yaml_file = map_dir / 'map.yaml'
    if not yaml_file.exists():
        return None, None

    meta = {}
    for line in yaml_file.read_text().splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            meta[key.strip()] = val.strip()

    pgm_path = map_dir / meta.get('image', 'map.pgm')
    if not pgm_path.exists():
        return None, None

    img = np.array(Image.open(pgm_path))
    return img, meta


def parse_map_yaml_geometry(meta):
    """Pull resolution + origin (x, y) out of a parsed map.yaml dict."""
    resolution = float(meta.get('resolution', 0.05))
    origin_str = meta.get('origin', '[0.0, 0.0, 0.0]').strip().strip('[]')
    parts = [p.strip() for p in origin_str.split(',') if p.strip()]
    origin_x = float(parts[0]) if len(parts) > 0 else 0.0
    origin_y = float(parts[1]) if len(parts) > 1 else 0.0
    return resolution, origin_x, origin_y


def load_recordings_metadata(metadata_path: Path):
    if not metadata_path.exists():
        print(f"Error: {metadata_path} not found")
        sys.exit(1)

    with open(metadata_path) as f:
        records = json.load(f)

    if not isinstance(records, list) or not records:
        print(f"Error: {metadata_path} contains no recordings")
        sys.exit(1)

    return records


def read_wav_channels(wav_path: Path):
    """Read a WAV file into a (frames, channels) float32 array in [-1, 1],
    plus its sample rate. Only 16-bit PCM (what the recorder writes) is
    supported."""
    with wave.open(str(wav_path), 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Unsupported sample width {sampwidth} bytes (expected 16-bit PCM)")

    audio_int16 = np.frombuffer(raw, dtype=np.int16)
    audio = audio_int16.astype(np.float32) / 32768.0
    audio = audio.reshape(-1, n_channels)
    return audio, framerate


def compute_signature(channel_data, n_bins):
    """Same style of normalized frequency-band signature the old mapper
    node used to compute live, just run here on a full recording."""
    if len(channel_data) < n_bins * 2:
        return None

    spectrum = np.abs(np.fft.rfft(channel_data))
    freq_bins = np.array_split(spectrum, n_bins)
    signature = np.array(
        [np.mean(b) if len(b) > 0 else 0.0 for b in freq_bins], dtype=np.float32
    )
    max_val = signature.max()
    if max_val > 0:
        signature /= max_val
    return signature


def load_recording_points(map_dir: Path, records, recordings_subdir, channel_selector, n_bins):
    """Read every recording's WAV file and pair it with the robot position
    recorded for it. Returns a list of point dicts and the sample rate
    (assumed consistent across recordings)."""
    recordings_dir = map_dir / recordings_subdir
    points = []
    sample_rate = None

    for entry in records:
        filename = entry.get('filename')
        pos = entry.get('end_position') or entry.get('start_position')
        if pos is None:
            print(f"Skipping {filename}: no robot position was recorded for it")
            continue

        wav_path = recordings_dir / filename if filename else None
        if wav_path is None or not wav_path.exists():
            fallback = Path(entry.get('filepath', ''))
            if fallback.exists():
                wav_path = fallback
            else:
                print(f"Skipping {filename}: WAV file not found ({wav_path})")
                continue

        try:
            audio, framerate = read_wav_channels(wav_path)
        except (OSError, wave.Error, ValueError) as e:
            print(f"Skipping {filename}: could not read WAV ({e})")
            continue

        n_channels = audio.shape[1]
        if channel_selector == 'mean':
            channel_data = audio.mean(axis=1)
        else:
            idx = min(int(channel_selector), n_channels - 1)
            channel_data = audio[:, idx]

        signature = compute_signature(channel_data, n_bins)
        if signature is None:
            print(f"Skipping {filename}: recording too short for {n_bins} FFT bins")
            continue

        if sample_rate is None:
            sample_rate = framerate

        points.append({
            'id': entry.get('id'),
            'filename': filename,
            'x': pos['x'],
            'y': pos['y'],
            'frame': pos.get('frame', 'map'),
            'timestamp': entry.get('start_time_utc'),
            'duration_s': entry.get('actual_duration_s'),
            'signature': signature,
            'audio': channel_data,
            'sample_rate': framerate,
            'wav_path': wav_path,
        })

    if not points:
        print("No recordings could be loaded (missing files or positions). Nothing to display.")
        sys.exit(1)

    return points, sample_rate or 48000


# ----------------------------------------------------------------------
# Band math (unchanged concept, now operates on a stack of per-recording
# signatures instead of a (H, W, n_bins) grid)
# ----------------------------------------------------------------------
def compute_band_intensity(points, band, n_bins):
    sigs = np.stack([p['signature'] for p in points])  # (N, n_bins)
    if band == 'all':
        return sigs.mean(axis=1)
    elif band == 'low':
        return sigs[:, :n_bins // 4].mean(axis=1)
    elif band == 'mid':
        return sigs[:, n_bins // 4:3 * n_bins // 4].mean(axis=1)
    elif band == 'high':
        return sigs[:, 3 * n_bins // 4:].mean(axis=1)
    else:
        idx = int(band)
        return sigs[:, min(idx, n_bins - 1)]


def interpolate_points(points_x, points_y, values, grid_step, radius):
    if len(points_x) < 3:
        return None, None, None

    pad_m = radius * 1.5
    x_min, x_max = points_x.min() - pad_m, points_x.max() + pad_m
    y_min, y_max = points_y.min() - pad_m, points_y.max() + pad_m

    grid_x = np.arange(x_min, x_max, grid_step)
    grid_y = np.arange(y_min, y_max, grid_step)
    mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)

    coords = np.column_stack([points_x, points_y])
    query_pts = np.column_stack([mesh_x.ravel(), mesh_y.ravel()])

    rbf = RBFInterpolator(coords, values, kernel='thin_plate_spline', smoothing=0.01)
    interp_values = rbf(query_pts).reshape(mesh_x.shape)
    interp_values = np.clip(interp_values, 0, None)

    extent = [x_min, x_max, y_min, y_max]
    return interp_values, extent, (points_x, points_y, values)


def band_label(band, sample_rate, n_bins):
    bin_width_hz = (sample_rate / 2) / n_bins
    if band == 'all':
        return f"All (0-{sample_rate//2} Hz)"
    elif band == 'low':
        return f"Low (0-{int(n_bins//4 * bin_width_hz)} Hz)"
    elif band == 'mid':
        return f"Mid ({int(n_bins//4 * bin_width_hz)}-{int(3*n_bins//4 * bin_width_hz)} Hz)"
    elif band == 'high':
        return f"High ({int(3*n_bins//4 * bin_width_hz)}-{sample_rate//2} Hz)"
    else:
        idx = int(band)
        return f"Bin {idx} ({int(idx * bin_width_hz)}-{int((idx+1) * bin_width_hz)} Hz)"


def build_band_options(sample_rate, n_bins):
    bin_width_hz = (sample_rate / 2) / n_bins
    options = [
        ('all', f"All (0-{sample_rate//2} Hz)"),
        ('low', f"Low (0-{int(n_bins//4 * bin_width_hz)} Hz)"),
        ('mid', f"Mid ({int(n_bins//4 * bin_width_hz)}-{int(3*n_bins//4 * bin_width_hz)} Hz)"),
        ('high', f"High ({int(3*n_bins//4 * bin_width_hz)}-{sample_rate//2} Hz)"),
    ]
    for i in range(0, n_bins, max(1, n_bins // 8)):
        lo = int(i * bin_width_hz)
        hi = int((i + 1) * bin_width_hz)
        options.append((str(i), f"Bin {i} ({lo}-{hi} Hz)"))
    return options


# ----------------------------------------------------------------------
# Viewer
# ----------------------------------------------------------------------
class AudioRecordingsViewer:
    def __init__(self, points, sample_rate, n_bins, occ_img, occ_meta, radius, alpha, grid_step,
                 initial_point=None):
        self.points = points
        self.sample_rate = sample_rate
        self.n_bins = n_bins
        self.occ_img = occ_img
        self.radius = radius
        self.alpha = alpha
        self.grid_step = grid_step

        self.occ_extent = None
        if occ_img is not None and occ_meta is not None:
            resolution, origin_x, origin_y = parse_map_yaml_geometry(occ_meta)
            self.occ_extent = [
                origin_x, origin_x + occ_img.shape[1] * resolution,
                origin_y, origin_y + occ_img.shape[0] * resolution,
            ]
            if self.grid_step is None:
                self.grid_step = resolution
        if self.grid_step is None:
            self.grid_step = 0.05

        self.band_options = build_band_options(self.sample_rate, self.n_bins)
        self.current_band = 'all'
        self.selected_point = None
        self.spec_colorbar = None
        self.status_text = None
        self.point_markers = []

        self._setup_figure()
        self._render(self.current_band)
        self._connect_point_selection()
        if initial_point is not None:
            self._show_spectrogram(initial_point)

    def _setup_figure(self):
        self.fig = plt.figure(figsize=(16, 9), facecolor='#f4f1ea')
        self.fig.canvas.manager.set_window_title('Audio Recording Map')

        self.ax_interp = self.fig.add_axes([0.035, 0.11, 0.285, 0.78])
        self.ax_overlay = self.fig.add_axes([0.355, 0.11, 0.285, 0.78])
        self.ax_spec = self.fig.add_axes([0.675, 0.11, 0.29, 0.78])
        self.ax_spec_cbar = self.fig.add_axes([0.97, 0.11, 0.015, 0.78])
        self.ax_spec_cbar.set_visible(False)
        self.ax_spec.text(0.5, 0.5, 'Click a recording point\nto view its spectrogram',
                  ha='center', va='center', fontsize=12, color='#6d665c',
                  transform=self.ax_spec.transAxes)
        self.ax_spec.set_axis_off()

        self.fig.text(0.05, 0.95, 'AUDIO RECORDING MAP', fontsize=15, weight='bold',
                      color='#24211d', va='center')
        self.fig.text(0.05, 0.918, 'Select a point to inspect its spectrum',
                      fontsize=9, color='#6d665c', va='center')
        self.ax_btn = self.fig.add_axes([0.66, 0.925, 0.29, 0.045])
        self.btn = Button(self.ax_btn, f'Band: {self.band_options[0][1]}')
        self.btn.on_clicked(self._cycle_band)
        self.status_text = self.fig.text(0.05, 0.045, 'No point selected', fontsize=9,
                                         color='#6d665c', va='center')

    def _cycle_band(self, event):
        band_keys = [key for key, _ in self.band_options]
        current_index = band_keys.index(self.current_band)
        self.current_band = band_keys[(current_index + 1) % len(band_keys)]
        label = band_label(self.current_band, self.sample_rate, self.n_bins)
        self.btn.label.set_text(f'Band: {label}')
        self._render(self.current_band)
        self.fig.canvas.draw_idle()

    def _render(self, band):
        self.ax_interp.clear()
        self.ax_overlay.clear()
        self.ax_overlay.set_visible(True)
        self.ax_spec.set_axis_off()
        self.point_markers = []

        values = compute_band_intensity(self.points, band, self.n_bins)
        label = band_label(band, self.sample_rate, self.n_bins)

        points_x = np.array([p['x'] for p in self.points])
        points_y = np.array([p['y'] for p in self.points])

        interp_map, extent, sample_pts = interpolate_points(
            points_x, points_y, values, self.grid_step, self.radius
        )

        cmap = plt.get_cmap('inferno').copy()

        if interp_map is not None:
            vmin, vmax = 0, interp_map.max() if interp_map.max() > 0 else 1.0
            norm = Normalize(vmin=vmin, vmax=vmax)
            pts_x, pts_y, pts_v = sample_pts

            self.ax_interp.imshow(interp_map, cmap=cmap, origin='lower',
                                  extent=extent, aspect='equal', norm=norm)
            self.ax_interp.scatter(pts_x, pts_y, c='white', s=24,
                                   edgecolors='black', linewidths=0.5, zorder=5)
            self.ax_interp.set_title(f'Interpolated Recordings Map\n{label} ({len(self.points)} recordings)')
            self.ax_interp.set_xlabel('x (meters)')
            self.ax_interp.set_ylabel('y (meters)')

            if self.occ_img is not None:
                self.ax_overlay.imshow(self.occ_img, cmap='gray', origin='lower',
                                       extent=self.occ_extent)
                self.ax_overlay.imshow(interp_map, cmap=cmap, origin='lower',
                                       extent=extent, alpha=self.alpha, norm=norm)
                self.ax_overlay.scatter(pts_x, pts_y, c='cyan', s=22,
                                        edgecolors='none', zorder=5, alpha=0.7)
                self.ax_overlay.set_xlim(extent[0], extent[1])
                self.ax_overlay.set_ylim(extent[2], extent[3])
                self.ax_overlay.set_title(f'Overlay on Occupancy Map\n{label}')
            else:
                self.ax_overlay.imshow(interp_map, cmap=cmap, origin='lower',
                                       extent=extent, norm=norm)
                self.ax_overlay.scatter(pts_x, pts_y, c=pts_v, cmap=cmap, s=48,
                                        edgecolors='white', linewidths=1, zorder=5, norm=norm)
                self.ax_overlay.set_title(f'Sample Points\n{label}')
            self.ax_overlay.set_xlabel('x (meters)')
            self.ax_overlay.set_ylabel('y (meters)')
        else:
            if self.occ_img is not None:
                self.ax_interp.imshow(self.occ_img, cmap='gray', origin='lower',
                                      extent=self.occ_extent)
            self.ax_interp.scatter(points_x, points_y, c=values, cmap=cmap, s=60,
                                   edgecolors='white', linewidths=0.8, zorder=5)
            self.ax_interp.set_title(f'Audio Recordings (< 3 points)\n{label}')
            self.ax_interp.set_xlabel('x (meters)')
            self.ax_interp.set_ylabel('y (meters)')
            self.ax_overlay.set_visible(False)

        self._draw_selected_point()

    def _draw_selected_point(self):
        if self.selected_point is None:
            return

        point_x = self.selected_point['x']
        point_y = self.selected_point['y']
        for axis in (self.ax_interp, self.ax_overlay):
            if axis.get_visible():
                marker, = axis.plot(point_x, point_y, marker='*', markersize=16,
                                    markerfacecolor='#fff3a6', markeredgecolor='#d1493f',
                                    markeredgewidth=1.5, zorder=10)
                axis.annotate(f"ID {self.selected_point['id']}", (point_x, point_y),
                              xytext=(7, 7), textcoords='offset points', fontsize=8,
                              color='#24211d', weight='bold', zorder=11,
                              bbox={'boxstyle': 'round,pad=0.25', 'fc': '#fff3a6',
                                    'ec': '#d1493f', 'alpha': 0.9})
                self.point_markers.append(marker)

    def _connect_point_selection(self):
        self.fig.canvas.mpl_connect('button_press_event', self._select_point)

    def _select_point(self, event):
        if (event.inaxes not in (self.ax_interp, self.ax_overlay)
            or event.xdata is None or event.ydata is None):
            return

        distances = [
            (point['x'] - event.xdata) ** 2 + (point['y'] - event.ydata) ** 2
            for point in self.points
        ]
        nearest_index = int(np.argmin(distances))
        axis_limits = event.inaxes.get_xlim(), event.inaxes.get_ylim()
        click_tolerance = max(self.grid_step * 4,
                              min(axis_limits[0][1] - axis_limits[0][0],
                                  axis_limits[1][1] - axis_limits[1][0]) * 0.02)
        if distances[nearest_index] > click_tolerance ** 2:
            self.status_text.set_text('No recording near that location')
            self.fig.canvas.draw_idle()
            return

        point = self.points[nearest_index]
        self.status_text.set_text(
            f"Selected ID {point['id']}  |  ({point['x']:.2f}, {point['y']:.2f}) m  |  "
            f"{point['filename']}"
        )
        self._render(self.current_band)
        self._show_spectrogram(point)

    def _show_spectrogram(self, point):
        self.selected_point = point
        if self.status_text is not None:
            self.status_text.set_text(
                f"Selected ID {point['id']}  |  ({point['x']:.2f}, {point['y']:.2f}) m  |  "
                f"{point['filename']}"
            )
        frequencies, times, power = spectrogram(
            point['audio'], fs=point.get('sample_rate', self.sample_rate),
            nperseg=min(1024, len(point['audio'])), noverlap=None,
        )
        power_db = 10 * np.log10(np.maximum(power, np.finfo(float).tiny))

        self.ax_spec.clear()
        self.ax_spec.set_axis_on()
        self.ax_spec_cbar.set_visible(True)

        vmax = float(power_db.max())
        image = self.ax_spec.pcolormesh(times, frequencies, power_db, shading='auto',
                                        cmap='magma', vmin=max(vmax - 80, float(power_db.min())),
                                        vmax=vmax)
        if self.spec_colorbar is None:
            self.spec_colorbar = self.fig.colorbar(image, cax=self.ax_spec_cbar)
            self.spec_colorbar.set_label('Power (dB)')
        else:
            self.spec_colorbar.update_normal(image)
        self.ax_spec.set_title(
            f"Spectrogram: point {point['id']} at ({point['x']:.2f}, {point['y']:.2f})\n"
            f"{point['filename']}"
        )
        self.ax_spec.set_xlabel('Time (seconds)')
        self.ax_spec.set_ylabel('Frequency (Hz)')
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    default_map_dir = Path(__file__).resolve().parents[2] / 'data'
    parser.add_argument('map_dir', nargs='?', default=str(default_map_dir),
                        help=f'Directory containing recordings_metadata.json (default: {default_map_dir})')
    parser.add_argument('--radius', type=float, default=0.3,
                        help='Interpolation influence radius in meters (default: 0.3)')
    parser.add_argument('--alpha', type=float, default=0.7,
                        help='Overlay opacity (0-1)')
    parser.add_argument('--bins', type=int, default=64,
                        help='Number of FFT bins to compute per recording (default: 64)')
    parser.add_argument('--channel', default='mean',
                        help="Which recorded channel to analyze: an index (0, 1, ...) "
                             "or 'mean' to average all channels (default: mean)")
    parser.add_argument('--recordings-subdir', default='recordings',
                        help="Subdirectory containing the .wav files (default: recordings)")
    parser.add_argument('--metadata-file', default='recordings_metadata.json',
                        help="Metadata filename inside map_dir (default: recordings_metadata.json)")
    parser.add_argument('--grid-step', type=float, default=None,
                        help='Interpolation grid resolution in meters '
                             '(default: map resolution if available, else 0.05)')
    parser.add_argument('--raw', action='store_true',
                        help='Print raw recording stats')
    parser.add_argument('--point',
                        help='Open a spectrogram for a recording ID or filename on startup')
    args = parser.parse_args()

    map_dir = Path(args.map_dir).expanduser()
    channel_selector = args.channel if args.channel == 'mean' else int(args.channel)

    records = load_recordings_metadata(map_dir / args.metadata_file)
    points, sample_rate = load_recording_points(
        map_dir, records, args.recordings_subdir, channel_selector, args.bins
    )
    initial_point = None
    if args.point is not None:
        initial_point = next(
            (point for point in points
             if str(point['id']) == args.point or point['filename'] == args.point),
            None,
        )
        if initial_point is None:
            parser.error(f"point '{args.point}' was not found in {map_dir}")
    occ_img, occ_meta = load_occupancy_map(map_dir)

    if args.raw:
        print("=" * 60)
        print("RAW RECORDINGS DATA")
        print(f"  loaded: {len(points)} / {len(records)} recordings")
        print(f"  sample_rate: {sample_rate} Hz, fft_bins: {args.bins}, channel: {args.channel}")
        for p in points:
            print(f"  [{p['id']}] {p['filename']}: pos=({p['x']:.2f}, {p['y']:.2f}) "
                  f"dur={p['duration_s']}s t={p['timestamp']}")
        print("=" * 60)

    print(f"Loaded {len(points)} recordings, {args.bins} FFT bins, "
          f"sample_rate={sample_rate}Hz")
    print("Use the band button at the top to switch frequency bands.")

    viewer = AudioRecordingsViewer(points, sample_rate, args.bins, occ_img, occ_meta,
                                    args.radius, args.alpha, args.grid_step, initial_point)
    viewer.show()


if __name__ == '__main__':
    main()