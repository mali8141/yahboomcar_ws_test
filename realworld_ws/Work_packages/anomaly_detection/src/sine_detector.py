import helper
import numpy as np

# gives higher results that cosine distance but lower than sine strength (around 0.4 for known-good)
def run_sine_distance(known_good_paths, known_bad_paths, unknown_paths):
    known_good_ffts = [helper.get_fft(p) for p in known_good_paths]
    known_bad_ffts = [helper.get_fft(p) for p in known_bad_paths]
    unknown_ffts = [helper.get_fft(p) for p in unknown_paths]

    #TODO: add option to ser out specific frequency bands to use for distance calculation, or to use all bands

    distances = helper.cosine_distances(known_good_ffts, known_bad_ffts, unknown_ffts)

    probabilities = []

    for path, distance in zip(unknown_paths, distances):
        avg_distance_to_good = distance["avg_distance_to_good"]

        if avg_distance_to_good is not None:
            probability = avg_distance_to_good
        else:
            probability = None

        probabilities.append({
            "unknown_path": path,
            "probability": probability
        })

    return probabilities

#! gives weirdly high probabilities even for known-good recordings (1 - 2).
def run_sine_strength(known_good_paths, known_bad_paths, unknown_paths):
    known_good_ffts = np.asarray([helper.get_fft(p) for p in known_good_paths])
    unknown_ffts = np.asarray([helper.get_fft(p) for p in unknown_paths])

    if known_good_ffts.size == 0:
        raise ValueError("At least one known-good recording is required")

    #TODO: add option to ser out specific frequency bands to use for distance calculation, or to use all bands

    # Mean magnitude for each FFT band
    known_good_mean = np.mean(known_good_ffts, axis=0)

    # Mean absolute deviation for each band
    known_good_average_deviation = np.mean(np.abs(known_good_ffts - known_good_mean), axis=0)
    reference_deviation = float(np.mean(known_good_average_deviation))

    probabilities = []

    for unknown_path, unknown_fft in zip(unknown_paths, unknown_ffts):
        # Calculate the mean absolute deviation of the unknown FFT from the known good
        unknown_deviation_from_good = np.mean(np.abs(unknown_fft - known_good_mean))

        # Calculate the probability based on the deviations
        if reference_deviation > 0:
            probability = float(unknown_deviation_from_good / reference_deviation)
        elif unknown_deviation_from_good > 0:
            probability = 1.0
        else:
            probability = 0.0

        probabilities.append({
            "unknown_path": unknown_path,
            "probability": probability
        })

    return probabilities
