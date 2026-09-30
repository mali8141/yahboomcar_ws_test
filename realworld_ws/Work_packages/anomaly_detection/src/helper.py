from pathlib import Path

import librosa
import numpy as np
from panns_inference import AudioTagging
from scipy.spatial.distance import cdist, cosine

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
SAMPLE_RATE = 32_000

def load_model(device: str):
    """Load PANNs CNN14 pretrained model (auto-downloads checkpoint on first run)."""
    return AudioTagging(checkpoint_path=None, device=device)

def get_embedding(model, path: Path) -> np.ndarray:
    """Return a 2048-dim PANNs embedding for a single audio file."""
    audio, _ = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    audio = audio[None, :]           # (1, T)
    _, emb = model.inference(audio)  # emb: (1, 2048)
    return emb[0].astype(np.float64)

def expand_paths(values):
    paths = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(
                child for child in path.iterdir()
                if child.is_file() and child.suffix.lower() in AUDIO_EXTS
            ))
        elif path.is_file():
            paths.append(path)
        else:
            raise ValueError(f"Path does not exist or is not a file/directory: {path}")
    return paths

def get_fft(audio_path, n_bands=256):
    """Return the average magnitude in each frequency band of an audio file."""
    if n_bands < 1:
        raise ValueError("n_bands must be at least 1")

    # Keep the recording's native sample rate and load the complete recording.
    audio, _ = librosa.load(audio_path, sr=None, mono=True)

    spectrum = np.abs(np.fft.rfft(audio))
    bands = np.array_split(spectrum, n_bands)

    return np.array([
        np.mean(band) if band.size else 0.0
        for band in bands
    ])

def cosine_distances(known_good, known_bad, unknown):
    distances = []

    for unknown_sample in unknown:
        distances_to_good = [cosine(unknown_sample, known_good_sample) for known_good_sample in known_good]
        distances_to_bad = [cosine(unknown_sample, known_bad_sample) for known_bad_sample in known_bad]

        avg_distance_to_good = sum(distances_to_good) / len(distances_to_good) if distances_to_good else None
        avg_distance_to_bad = sum(distances_to_bad) / len(distances_to_bad) if distances_to_bad else None

        min_distance_to_good = min(distances_to_good) if distances_to_good else None
        min_distance_to_bad = min(distances_to_bad) if distances_to_bad else None

        max_distance_to_good = max(distances_to_good) if distances_to_good else None
        max_distance_to_bad = max(distances_to_bad) if distances_to_bad else None

        distances.append({
            "avg_distance_to_good": avg_distance_to_good,
            "avg_distance_to_bad": avg_distance_to_bad,
            "min_distance_to_good": min_distance_to_good,
            "min_distance_to_bad": min_distance_to_bad,
            "max_distance_to_good": max_distance_to_good,
            "max_distance_to_bad": max_distance_to_bad,
        })

    return distances