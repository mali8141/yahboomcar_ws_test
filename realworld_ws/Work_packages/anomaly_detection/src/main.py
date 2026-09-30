import argparse
from pathlib import Path

import helper

import cos_distance as cos_distance
import sine_detector as sine_detector

class AnomalyDetector:
    DETECTORS = {
        'cosine_distance': 'cosine_distance_probability',
        'sine_strength': 'sine_strength_probability',
        'sine_distance': 'sine_distance_probability',
    }

    @classmethod
    def available_detectors(cls):
        return tuple(cls.DETECTORS)

    def detect(self, detector, known_good_embedding, known_bad_embedding,
               unknown_embedding):
        try:
            method_name = self.DETECTORS[detector]
        except KeyError as error:
            available = ', '.join(self.available_detectors())
            raise ValueError(
                f'Unknown detector {detector!r}; choose one of: {available}') from error

        return getattr(self, method_name)(
            known_good_embedding, known_bad_embedding, unknown_embedding)

    def cosine_distance_probability(self, known_good_embedding, known_bad_embedding, unknown_embedding):
        return cos_distance.run(known_good_embedding, known_bad_embedding, unknown_embedding)

    def sine_strength_probability(self, known_good_embedding, known_bad_embedding, unknown_embedding):
        return sine_detector.run_sine_strength(known_good_embedding, known_bad_embedding, unknown_embedding)

    def sine_distance_probability(self, known_good_embedding, known_bad_embedding, unknown_embedding):
        return sine_detector.run_sine_distance(known_good_embedding, known_bad_embedding, unknown_embedding)

#### For Standalone Testing ####
def main():
    argument_parser = argparse.ArgumentParser(description="Arguments for anomaly detection")

    argument_parser.add_argument("--known-good", nargs="+", default=[], help="Audio files or folders")
    argument_parser.add_argument("--known-bad", nargs="+", default=[], help="Audio files or folders")
    argument_parser.add_argument("--unknown", nargs="+", default=[], help="Audio files or folders")

    argument_parser.add_argument(
        '--detector', choices=AnomalyDetector.available_detectors(),
        default='cosine_distance', help='Detector to use')
    arguments = argument_parser.parse_args()

    try:
        known_good_paths = helper.expand_paths(arguments.known_good)
        known_bad_paths = helper.expand_paths(arguments.known_bad)
        unknown_paths = helper.expand_paths(arguments.unknown)
    except ValueError as error:
        argument_parser.error(str(error))

    anomaly_detector = AnomalyDetector()

    probabilities = anomaly_detector.detect(
        arguments.detector, known_good_paths, known_bad_paths, unknown_paths)
    print("------------------------------------------------------------")
    print(f"{arguments.detector} probabilities:", probabilities)
    print("------------------------------------------------------------")

if __name__ == '__main__':
    main()