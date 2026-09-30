import json
import math
from pathlib import Path
from typing import Callable

import numpy as np
import rclpy
from rclpy.node import Node
from scipy.spatial.distance import cosine
from std_msgs.msg import String

#TODO this should be remove once I move to a venv
def _patch_numba_coverage_compat():
    try:
        import coverage
    except ImportError:
        return

    coverage_types = getattr(coverage, 'types', None)
    if coverage_types is None:
        return

    if not hasattr(coverage_types, 'Tracer') and hasattr(coverage_types, 'TracerCore'):
        coverage_types.Tracer = coverage_types.TracerCore

    for type_name in ('TShouldTraceFn', 'TShouldStartContextFn', 'TWarnFn'):
        if not hasattr(coverage_types, type_name):
            setattr(coverage_types, type_name, Callable)


_patch_numba_coverage_compat()

from main import AnomalyDetector


class AnomalyDetectorNode(Node):
    def __init__(self):
        super().__init__('anomaly_detector')
        self.declare_parameter('data_known', '')
        self.declare_parameter('request_topic', 'anomaly_detection/analyze_recording')
        self.declare_parameter('result_topic', 'anomaly_detection/result')
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('detector', 'cosine_distance')
        self.declare_parameter('anomaly_threshold', 0.30)
        self.declare_parameter('reference_radius_m', 0.25)
        self.declare_parameter('minimum_references', 1)

        self.detector = AnomalyDetector()
        self.data_known = Path(
            self.get_parameter('data_known').value).expanduser()
        self.detector_name = self.get_parameter('detector').value
        if self.detector_name not in self.detector.available_detectors():
            available = ', '.join(self.detector.available_detectors())
            raise ValueError(
                f'Unknown detector {self.detector_name!r}; choose one of: {available}')
        self.anomaly_threshold = float(
            self.get_parameter('anomaly_threshold').value)
        self.reference_radius_m = float(
            self.get_parameter('reference_radius_m').value)
        self.minimum_references = int(
            self.get_parameter('minimum_references').value)
        self.result_pub = self.create_publisher(
            String, self.get_parameter('result_topic').value, 10)
        self.request_sub = self.create_subscription(
            String,
            self.get_parameter('request_topic').value,
            self._request_callback,
            10,
        )

        self.known_samples_metadata = self._get_known_samples_metadata()

        self.get_logger().info(
            f'Anomaly detector listening on {self.get_parameter("request_topic").value!r}; '
            f'detector: {self.detector_name}, known data: {self.data_known}, '
            f'radius: {self.reference_radius_m:.2f}m')

    def _request_callback(self, msg: String):
        result = {'status': 'failed', 'reason': 'Unknown processing error'}
        request = {}
        try:
            request = json.loads(msg.data)
            recording_path = Path(
                request.get('recording_path', '')).expanduser()

            if not recording_path.exists():
                raise ValueError(f"Recording path does not exist: {recording_path}")

            self.get_logger().info(f'Analyzing recording: {recording_path}')

            recording_position = self._get_sample_position(recording_path)
            nearby_samples = self._get_samples_within_radius(recording_position, self.reference_radius_m)

            if len(nearby_samples) < self.minimum_references:
                fallback_samples = [sample['path'] for sample in self.known_samples_metadata]
                if len(fallback_samples) >= self.minimum_references:
                    self.get_logger().warning(
                        f'Only {len(nearby_samples)} known samples found within '
                        f'{self.reference_radius_m:.2f}m; using all '
                        f'{len(fallback_samples)} known samples for analysis')
                    nearby_samples = fallback_samples
                else:
                    raise ValueError(
                        f'Only {len(nearby_samples)} known samples found within '
                        f'{self.reference_radius_m:.2f}m and only '
                        f'{len(fallback_samples)} known samples exist; '
                        f'{self.minimum_references} required')

            probabilities = self.detector.detect(
                self.detector_name, nearby_samples, [], [recording_path])

            probability = probabilities[0]['probability']
            result_context = {
                'position': recording_position,
                'probability': probability,
                'recording': request.get('recording'),
                'run_id': request.get('run_id'),
                'map_id': request.get('map_id'),
                'location': request.get('location'),
            }

            if probability is not None and probability > self.anomaly_threshold:
                result = {'status': 'ok', 'result': 'anomaly', **result_context}
            else:
                result = {'status': 'ok', 'result': 'normal', **result_context}

        except Exception as e:
            self.get_logger().error(f'Error processing request: {e}')
            result = {
                'status': 'failed',
                'reason': str(e),
                'recording': request.get('recording'),
                'run_id': request.get('run_id'),
                'map_id': request.get('map_id'),
            }
        finally:
            output = String()

            output.data = json.dumps(result)
            self.result_pub.publish(output)

    def _get_known_samples_metadata(self):
        metadata = []
        if not self.data_known.is_dir():
            return metadata

        for metadata_path in sorted(self.data_known.rglob('recordings_metadata.json')):
            try:
                records = json.loads(metadata_path.read_text())
            except (OSError, json.JSONDecodeError) as error:
                self.get_logger().warning(
                    f'Could not read metadata file {metadata_path}: {error}')
                continue

            if not isinstance(records, list):
                continue

            for record in records:
                sample_path = self._resolve_sample_path(record, metadata_path.parent)
                position = self._position_from_record(record)
                if sample_path is not None and position is not None:
                    metadata.append({'path': sample_path, 'position': position})

        return metadata

    def _get_samples_within_radius(self, reference_position: tuple, radius_m: float):
        if radius_m < 0:
            raise ValueError('radius_m must be non-negative')

        reference_x, reference_y = reference_position
        radius_squared = radius_m ** 2
        return [
            sample['path']
            for sample in self.known_samples_metadata
            if (sample['position'][0] - reference_x) ** 2
            + (sample['position'][1] - reference_y) ** 2 <= radius_squared
        ]

    def _get_sample_position(self, sample_path: Path):
        sample_path = sample_path.expanduser().resolve()
        for sample in self.known_samples_metadata:
            if sample['path'].resolve() == sample_path:
                return sample['position']

        for parent in (sample_path.parent, *sample_path.parents):
            metadata_path = parent / 'recordings_metadata.json'
            if not metadata_path.is_file():
                continue

            try:
                records = json.loads(metadata_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue

            for record in records if isinstance(records, list) else []:
                resolved_path = self._resolve_sample_path(record, metadata_path.parent)
                position = self._position_from_record(record)
                if resolved_path is not None and position is not None and resolved_path.resolve() == sample_path:
                    return position

        raise ValueError(f'No position metadata found for recording: {sample_path}')

    @staticmethod
    def _position_from_record(record):
        position = record.get('end_position') or record.get('start_position')
        if not isinstance(position, dict) or 'x' not in position or 'y' not in position:
            return None
        try:
            return (float(position['x']), float(position['y']))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_sample_path(record, metadata_directory):
        filename = record.get('filename')
        filepath = record.get('filepath')

        candidates = []
        if filepath:
            candidates.append(Path(filepath).expanduser())
        if filename:
            candidates.extend((
                metadata_directory / 'recordings' / filename,
                metadata_directory / filename,
            ))

        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        return None

def main(args=None):
    rclpy.init(args=args)
    node = AnomalyDetectorNode()
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