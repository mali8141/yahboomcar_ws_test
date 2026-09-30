#!/usr/bin/env python3
"""
audio_field_builder.py
======================
Generator for a pre-baked planar audio field consumed by sim_audio_publisher.

The field is a flat plane at a fixed height; sample points are arranged in a
regular grid. Each grid point stores a short looping mono waveform that
represents what the microphone would hear at that location.

Generator: sound_sources
------------------------
Sound sources are described in a JSON file. The file contains
a list of source objects with each source having a world position and a list of
frequency bands with independent intensities:

  [
    {
      "x": 3.0,
      "y": -2.5,
      "z": 0.0,          // optional, default 0.0
      "bands": [
        { "freq_min": 200,  "freq_max": 400,  "intensity": 0.8 },
        { "freq_min": 1000, "freq_max": 1200, "intensity": 0.3 }
      ]
    },
    {
      "x": -5.0,
      "y":  1.0,
      "bands": [
        { "freq_min": 500, "freq_max": 800, "intensity": 1.0 }
      ]
    }
  ]

Each band is synthesised as a single sinusoid at the band's centre frequency.
The contribution of each source at a grid point is scaled by 1/r² (inverse
square law). A floor distance of 0.1 m prevents division-by-zero when a grid
point coincides with a source.  Multiple sources and bands are summed. The
final waveform is normalised to [-1, 1] peak amplitude.

Usage
-----
  ros2 run sim_audio audio_field_builder   --sources scene.json --output maze_field
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


# ----------------------------------------------------------------
# Constants
# ----------------------------------------------------------------

SPEED_OF_SOUND = 343.0  # (m/s) stored in metadata for publisher reference
_MIN_DIST = 0.1          # (m) floor for inverse-square-law to avoid inf

# ----------------------------------------------------------------
# Sound-source data model
# ----------------------------------------------------------------

@dataclass
class FreqBand:
    """One frequency band for a sound source."""
    freq_min: float   # Hz — lower edge of the band
    freq_max: float   # Hz — upper edge of the band
    intensity: float  # linear amplitude weight [0, 1] at 1 m from source

    @property
    def centre(self) -> float:
        return 0.5 * (self.freq_min + self.freq_max)

    def validate(self) -> None:
        if self.freq_min <= 0 or self.freq_max <= 0:
            raise ValueError(f"Band frequencies must be positive, got [{self.freq_min}, {self.freq_max}]")
        if self.freq_min > self.freq_max:
            raise ValueError(f"freq_min ({self.freq_min}) > freq_max ({self.freq_max})")
        if not (0.0 < self.intensity <= 1.0):
            raise ValueError(f"intensity must be in (0, 1], got {self.intensity}")


@dataclass
class SoundSource:
    """A point sound source at a world position with one or more frequency bands."""
    x: float
    y: float
    z: float
    bands: list[FreqBand] = field(default_factory=list)

    def validate(self) -> None:
        if not self.bands:
            raise ValueError(f"Source at ({self.x}, {self.y}) has no bands")
        for b in self.bands:
            b.validate()


def load_sources(path: Path) -> list[SoundSource]:
    """Parse a JSON sound-sources file; return validated SoundSource list."""
    with open(path) as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError("Sound-sources JSON must be a top-level array")
    if not raw:
        raise ValueError("Sound-sources JSON array is empty")

    sources: list[SoundSource] = []
    for i, entry in enumerate(raw):
        try:
            bands = [
                FreqBand(
                    freq_min=float(b['freq_min']),
                    freq_max=float(b['freq_max']),
                    intensity=float(b['intensity']),
                )
                for b in entry['bands']
            ]
            src = SoundSource(
                x=float(entry['x']),
                y=float(entry['y']),
                z=float(entry.get('z', 0.0)),
                bands=bands,
            )
            src.validate()
            sources.append(src)
        except (KeyError, TypeError) as exc:
            raise ValueError(f"sources[{i}]: missing or invalid field — {exc}") from exc

    return sources


# ----------------------------------------------------------------
# Grid construction
# ----------------------------------------------------------------

def build_grid(x_min: float, x_max: float,
               y_min: float, y_max: float,
               spacing: float, height: float) -> np.ndarray:
    """Return float32 [N, 3] world-frame (x, y, z) of every grid point.

    Grid snaps to multiples of spacing starting from (x_min, y_min).
    """
    xs = np.arange(x_min, x_max + spacing * 0.5, spacing)
    ys = np.arange(y_min, y_max + spacing * 0.5, spacing)
    xx, yy = np.meshgrid(xs, ys)
    zz = np.full_like(xx, height)
    return np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=1).astype(np.float32)


# ----------------------------------------------------------------
# Frequency quantisation
# ----------------------------------------------------------------

def quantise_freq(f_target: float, samplerate: int, seq_len: int) -> float:
    """Return the nearest frequency with a whole number of periods in seq_len.

    Eliminates discontinuities at the loop boundary.
    f_valid = n * samplerate / seq_len  for integer n >= 1
    """
    bin_hz = samplerate / seq_len
    n = max(1, round(f_target / bin_hz))
    return n * bin_hz


# ----------------------------------------------------------------
# Sound-sources generator
# ----------------------------------------------------------------

def generate_sound_sources(points: np.ndarray,
                            sources: list[SoundSource],
                            samplerate: int,
                            seq_len: int) -> np.ndarray:
    """Build waveforms[N, seq_len] (mono, float32) from point sound sources.

    For each grid point:
      - For each source, compute Euclidean distance r (floored at _MIN_DIST).
      - For each band in that source, synthesise a sinusoid at the band
        centre frequency (quantised to loop cleanly) with amplitude
        = band.intensity / r².
      - Sum all contributions; normalise the whole field to peak 1.0.
    """
    n_points = len(points)
    t = np.arange(seq_len, dtype=np.float64) / samplerate

    # Pre-quantise every unique centre frequency once
    freq_cache: dict[float, float] = {}
    def qfreq(fc: float) -> float:
        if fc not in freq_cache:
            freq_cache[fc] = quantise_freq(fc, samplerate, seq_len)
        return freq_cache[fc]

    # Source positions as float64 array [S, 3]
    src_pos = np.array([[s.x, s.y, s.z] for s in sources], dtype=np.float64)

    waveforms = np.zeros((n_points, seq_len), dtype=np.float64)

    for i, pt in enumerate(points):
        pt64 = pt.astype(np.float64)
        for s_idx, src in enumerate(sources):
            r = float(np.linalg.norm(pt64 - src_pos[s_idx]))
            r = max(r, _MIN_DIST)
            inv_sq = 1.0 / (r * r)

            for band in src.bands:
                f = qfreq(band.centre)
                amp = band.intensity * inv_sq
                waveforms[i] += amp * np.sin(2.0 * np.pi * f * t)

    # Normalise to [-1, 1] peak across the entire field
    peak = np.abs(waveforms).max()
    if peak > 0.0:
        waveforms /= peak

    return waveforms.astype(np.float32)


# ----------------------------------------------------------------
# Top-level build
# ----------------------------------------------------------------

def build_field(sources: list[SoundSource],
                x_min: float, x_max: float,
                y_min: float, y_max: float,
                spacing: float, height: float,
                samplerate: int, seq_len: int,
                ) -> tuple[np.ndarray, np.ndarray]:
    """Build and return (points [N, 3], waveforms [N, seq_len])."""
    points = build_grid(x_min, x_max, y_min, y_max, spacing, height)
    waveforms = generate_sound_sources(points, sources, samplerate, seq_len)
    return points, waveforms


# ----------------------------------------------------------------
# I/O
# ----------------------------------------------------------------

def save_field(stem: Path,
               points: np.ndarray,
               waveforms: np.ndarray,
               sources: list[SoundSource],
               x_min: float, x_max: float,
               y_min: float, y_max: float,
               height: float, spacing: float,
               samplerate: int, seq_len: int,
               coord_frame: str,
               sources_path: str,
               ) -> tuple[Path, Path]:
    """Write <stem>.npz and <stem>_metadata.json.  Returns (npz_path, json_path)."""
    npz_path  = stem.with_suffix('.npz')
    json_path = Path(str(stem) + '_metadata.json')

    np.savez_compressed(
        npz_path,
        points=points,       # float32 [N, 3]
        waveforms=waveforms, # float32 [N, seq_len]  — mono, 1 channel per point
    )

    meta = {
        'schema_version': 3,
        'generator':    'sound_sources',
        'coord_frame':  coord_frame,
        'sources_file': str(sources_path),
        'bounds': {
            'x_min': x_min, 'x_max': x_max,
            'y_min': y_min, 'y_max': y_max,
            'height': height,
        },
        'grid': {
            'spacing':  spacing,
            'n_points': int(len(points)),
            'n_x':      int(np.unique(points[:, 0]).size),
            'n_y':      int(np.unique(points[:, 1]).size),
        },
        'audio': {
            'samplerate':     samplerate,
            'seq_len':        seq_len,
            'channels':       1,
            'speed_of_sound': SPEED_OF_SOUND,
        },
        'sources': [
            {
                'x': s.x, 'y': s.y, 'z': s.z,
                'bands': [
                    {'freq_min': b.freq_min, 'freq_max': b.freq_max,
                     'intensity': b.intensity, 'centre_hz': b.centre}
                    for b in s.bands
                ],
            }
            for s in sources
        ],
    }

    with open(json_path, 'w') as f:
        json.dump(meta, f, indent=2)

    return npz_path, json_path


# ----------------------------------------------------------------
# CLI
# ----------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='audio_field_builder',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --- Required ---
    p.add_argument(
        '--sources', '-s', required=True, metavar='FILE',
        help='Path to the JSON sound-sources file (required).',
    )

    # --- Output ---
    p.add_argument(
        '--output', '-o', default='audio_probe_field',
        help='Output file stem (no extension). Writes <stem>.npz and '
             '<stem>_metadata.json. Default: audio_probe_field',
    )

    # --- Grid ---
    g = p.add_argument_group('grid')
    g.add_argument('--x-min',   type=float, default=-10.0,
                   help='World X lower bound (m). Default: -10.0')
    g.add_argument('--x-max',   type=float, default=10.0,
                   help='World X upper bound (m). Default:  10.0')
    g.add_argument('--y-min',   type=float, default=-10.0,
                   help='World Y lower bound (m). Default: -10.0')
    g.add_argument('--y-max',   type=float, default=10.0,
                   help='World Y upper bound (m). Default:  10.0')
    g.add_argument('--spacing', type=float, default=0.25,
                   help='Grid spacing (m). Default: 0.25')
    g.add_argument('--height',  type=float, default=0.5,
                   help='Fixed Z height of all sample points (m). Default: 0.5')
    g.add_argument('--frame',   default='map',
                   help='ROS coordinate frame name stored in metadata. Default: map')

    # --- Audio ---
    a = p.add_argument_group('audio')
    a.add_argument('--samplerate', type=int, default=48000,
                   help='Sample rate in Hz. Must match the publisher. Default: 48000')
    a.add_argument('--seq-len', type=int, default=120000,
                   help='Samples stored per grid point (the looping sequence length). '
                        'Can be larger than the publisher chunk_size. '
                        'Default: 120000 (~2.5 s at 48 kHz)')

    return p


def main(args=None) -> None:
    parser = _build_parser()
    ns = parser.parse_args(args)

    # --- Load and validate sources ---
    sources_path = Path(ns.sources)
    if not sources_path.exists():
        print(f"ERROR: sources file not found: {sources_path}", file=sys.stderr)
        sys.exit(1)

    try:
        sources = load_sources(sources_path)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid sources file: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Validate grid args ---
    if ns.x_min >= ns.x_max:
        print("ERROR: x_min must be < x_max", file=sys.stderr)
        sys.exit(1)
    if ns.y_min >= ns.y_max:
        print("ERROR: y_min must be < y_max", file=sys.stderr)
        sys.exit(1)
    if ns.spacing <= 0:
        print("ERROR: spacing must be > 0", file=sys.stderr)
        sys.exit(1)

    # --- Size estimate ---
    n_x = len(np.arange(ns.x_min, ns.x_max + ns.spacing * 0.5, ns.spacing))
    n_y = len(np.arange(ns.y_min, ns.y_max + ns.spacing * 0.5, ns.spacing))
    n_points = n_x * n_y
    size_mb = n_points * ns.seq_len * 4 / 1024 / 1024   # mono float32
    n_bands_total = sum(len(s.bands) for s in sources)
    print(f"Building {n_x}×{n_y} = {n_points} point field  "
          f"({size_mb:.1f} MiB uncompressed)")
    print(f"Sources: {len(sources)}  total bands: {n_bands_total}")
    for i, s in enumerate(sources):
        band_summary = ', '.join(
            f"{b.freq_min:.0f}–{b.freq_max:.0f} Hz @{b.intensity:.2f}"
            for b in s.bands
        )
        print(f"  [{i}]  ({s.x}, {s.y}, {s.z})  bands: {band_summary}")

    t0 = time.monotonic()
    points, waveforms = build_field(
        sources=sources,
        x_min=ns.x_min, x_max=ns.x_max,
        y_min=ns.y_min, y_max=ns.y_max,
        spacing=ns.spacing, height=ns.height,
        samplerate=ns.samplerate, seq_len=ns.seq_len,
    )
    elapsed = time.monotonic() - t0
    print(f"Generated in {elapsed:.2f} s")

    stem = Path(ns.output)
    stem.parent.mkdir(parents=True, exist_ok=True)
    npz_path, json_path = save_field(
        stem=stem,
        points=points, waveforms=waveforms,
        sources=sources,
        x_min=ns.x_min, x_max=ns.x_max,
        y_min=ns.y_min, y_max=ns.y_max,
        height=ns.height, spacing=ns.spacing,
        samplerate=ns.samplerate, seq_len=ns.seq_len,
        coord_frame=ns.frame,
        sources_path=str(sources_path.resolve()),
    )
    print(f"Saved:  {npz_path}  ({npz_path.stat().st_size / 1024 / 1024:.1f} MiB compressed)")
    print(f"        {json_path}")


if __name__ == '__main__':
    main()
