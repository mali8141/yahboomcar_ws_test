"""Local HTTP bridge for sending Nav2 goals and reading the robot pose."""

import json
import queue
import threading
from concurrent.futures import Future
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import rclpy
from nav2_msgs.action import DockRobot, NavigateToPose
from nav2_msgs.srv import LoadMap
from nav_msgs.srv import GetMap
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Float32, String
from rclpy.action import ActionClient
from rclpy.node import Node
from tf2_ros import (Buffer, TransformListener)

from .brain_state import BrainState, RobotMode, RobotAction

from . import node_com_helper

class PatrolBrain(Node):
    """Owns ROS resources; HTTP worker threads hand work to this node's timer."""

    def __init__(self):
        super().__init__('patrol_brain')
        self.declare_parameter('host', '127.0.0.1')
        self.declare_parameter('port', 8080)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('navigate_action', 'navigate_to_pose')
        self.declare_parameter('dock_action', '/dock_robot')
        self.declare_parameter('dock_id', 'home_dock')
        self.declare_parameter('map_service', 'map_server/map')
        self.declare_parameter('map_load_service', 'map_server/load_map')
        self.declare_parameter('maps_root', '~/maps')
        self.declare_parameter('audio_recording_duration', 5.0)
        self.declare_parameter('audio_recording_distance', 0.1)
        self.declare_parameter('audio_recording_timeout', 20.0)
        self.declare_parameter('audio_trigger_topic', 'audio_mapper/trigger_recording')
        self.declare_parameter('audio_done_topic', 'audio_mapper/recording_done')
        self.declare_parameter(
            'anomaly_request_topic', 'anomaly_detection/analyze_recording')
        self.declare_parameter('anomaly_result_topic', 'anomaly_detection/result')
        self.declare_parameter('audio_context_topic', 'audio_mapper/recording_context')
        self.declare_parameter(
            'cors_allowed_origins',
            ['http://127.0.0.1:8000', 'http://localhost:8000'])

        self.map_frame = self.get_parameter('map_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.navigate_client = ActionClient(
            self, NavigateToPose,
            self.get_parameter('navigate_action').value)
        self.dock_client = ActionClient(
            self, DockRobot,
            self.get_parameter('dock_action').value)
        self.dock_id = self.get_parameter('dock_id').value
        self.map_client = self.create_client(
            GetMap, self.get_parameter('map_service').value)
        self.map_load_client = self.create_client(
            LoadMap, self.get_parameter('map_load_service').value)
        self.maps_root = self.get_parameter('maps_root').value
        self.audio_recording_duration = float(
            self.get_parameter('audio_recording_duration').value)
        self.audio_recording_distance = float(
            self.get_parameter('audio_recording_distance').value)
        self.audio_recording_timeout = float(
            self.get_parameter('audio_recording_timeout').value)
        self.audio_trigger_pub = self.create_publisher(
            Float32, self.get_parameter('audio_trigger_topic').value, 10)
        self.audio_done_sub = self.create_subscription(
            String, self.get_parameter('audio_done_topic').value,
            self._audio_done_cb, 10)
        self.anomaly_request_pub = self.create_publisher(
            String, self.get_parameter('anomaly_request_topic').value, 10)
        self.anomaly_result_sub = self.create_subscription(
            String, self.get_parameter('anomaly_result_topic').value,
            self._anomaly_result_cb, 10)
        self.audio_context_pub = self.create_publisher(
            String, self.get_parameter('audio_context_topic').value, 10)
        self.cors_allowed_origins = set(
            self.get_parameter('cors_allowed_origins').value)
        self._goal_handle = None
        self.requests = queue.Queue()
        self.state = BrainState()
        self._server = None
        self._battery: BatteryState | None = None
        self._inside_patrol_regions = set()
        self._last_patrol_pose = None
        self._last_patrol_regions = set()
        self._patrol_distance_since_recording = 0.0
        self._audio_pause_requested = False
        self._audio_waiting_for_done = False
        self._audio_waiting_since = None
        self._patrol_run = None
        self._pending_audio_analyses = set()
        self._patrol_completion_pending = False
        self.create_subscription(
            BatteryState, '/battery', self._battery_cb, 10)
        self.create_timer(0.02, self._process_requests)
        self.create_timer(0.5, self._check_patrol_regions)

        host = self.get_parameter('host').value
        port = self.get_parameter('port').value
        self._start_http_server(host, port)
        self.get_logger().info(
            f'Navigation API listening on http://{host}:{port} '
        )

    def _start_http_server(self, host, port):
        node = self

        class RequestHandler(BaseHTTPRequestHandler):

            def _reply(self, status, payload):
                encoded = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(encoded)))
                origin = self.headers.get('Origin')
                if origin in node.cors_allowed_origins:
                    self.send_header('Access-Control-Allow-Origin', origin)
                    self.send_header('Vary', 'Origin')
                self.end_headers()
                self.wfile.write(encoded)

            def do_OPTIONS(self):
                self.send_response(204)
                origin = self.headers.get('Origin')
                if origin in node.cors_allowed_origins:
                    self.send_header('Access-Control-Allow-Origin', origin)
                    self.send_header('Access-Control-Allow-Methods',
                                     'GET, POST, PUT, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers',
                                     'Content-Type')
                    self.send_header('Vary', 'Origin')
                self.end_headers()

            def _submit(self, operation, payload=None):
                response = Future()
                node.requests.put((operation, payload, response))
                try:
                    return response.result(timeout=5.0)
                except TimeoutError:
                    return 503, {'error': 'ROS node did not respond within 5 seconds'}

            def do_GET(self):
                if self.path == '/position':
                    status, payload = self._submit('get_pose')
                elif self.path == '/map':
                    status, payload = self._submit('get_map')
                elif self.path == '/maps':
                    status, payload = self._submit('list_maps')
                elif self.path.startswith('/routes/'):
                    map_id = unquote(self.path.removeprefix('/routes/'))
                    status, payload = self._submit('get_route', map_id)
                elif self.path == '/patrol-runs':
                    status, payload = self._submit('list_patrol_runs')
                elif self.path.startswith('/patrol-runs/'):
                    parts = self.path.removeprefix('/patrol-runs/').split('/', 1)
                    if len(parts) != 2:
                        status, payload = 400, {'error': 'map_id and run_id are required'}
                    else:
                        status, payload = self._submit(
                            'get_patrol_run', tuple(unquote(part) for part in parts))
                elif self.path in ('/status', '/get_status'):
                    status, payload = self._submit('get_status')
                else:
                    status, payload = 404, {'error': 'not found'}
                self._reply(status, payload)

            def do_POST(self):
                self._handle_json_write()

            def do_PUT(self):
                self._handle_json_write()

            def _handle_json_write(self):
                if self.path not in ('/get_status', '/commands', '/get_map', '/set_map') \
                    and not self.path.startswith('/routes/'):
                    self._reply(404, {'error': 'not found'})
                    return
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if length <= 0:
                        raise ValueError('request body is required')
                    body = json.loads(self.rfile.read(length).decode('utf-8'))
                except (ValueError, json.JSONDecodeError) as error:
                    self._reply(400, {'error': f'invalid JSON request: {error}'})
                    return
                operations = {
                    '/get_status': 'get_status', '/commands': 'set_command', '/set_map': 'set_map', '/get_map': 'get_map',
                }
                if self.path.startswith('/routes/'):
                    map_id = unquote(self.path.removeprefix('/routes/'))
                    status, payload = self._submit(
                        'save_route', (map_id, body))
                else:
                    status, payload = self._submit(operations[self.path], body)
                self._reply(status, payload)

        self._server = ThreadingHTTPServer((host, port), RequestHandler)
        threading.Thread(target=self._server.serve_forever,
                         name='navigation-api-http', daemon=True).start()

    def _process_requests(self):
        while True:
            try:
                operation, payload, response = self.requests.get_nowait()
            except queue.Empty:
                return
            if operation == 'get_status':
                pose_status, pose = node_com_helper.get_pose(self)
                status = self.state.as_dict()
                status['position'] = pose if pose_status == 200 else None
                if pose_status != 200:
                    status['position_error'] = pose.get('error')
                if self._battery is not None:
                    status['battery'] = {
                        'percentage': round(self._battery.percentage * 100.0, 1),
                        'voltage': round(self._battery.voltage, 2),
                    }
                response.set_result((200, status))
            elif operation == 'get_pose':
                response.set_result(node_com_helper.get_pose(self))
            elif operation == 'get_map':
                node_com_helper.get_map(self, response)
            elif operation == 'list_maps':
                response.set_result(node_com_helper.list_maps(self))
            elif operation == 'get_route':
                response.set_result(node_com_helper.get_route(self, payload))
            elif operation == 'list_patrol_runs':
                response.set_result(node_com_helper.list_patrol_runs(self))
            elif operation == 'get_patrol_run':
                map_id, run_id = payload
                response.set_result(node_com_helper.get_patrol_run(self, map_id, run_id))
            elif operation == 'save_route':
                map_id, route_payload = payload
                response.set_result(
                    node_com_helper.save_route(self, map_id, route_payload))
            elif operation == 'set_map':
                node_com_helper.set_map(self, payload, response)
            elif operation == 'set_command':
                response.set_result(self._handle_command(payload))
                
    def _handle_command(self, command):
        if not isinstance(command, dict):
            return 400, {'error': 'command must be a JSON object'}

        name = command.get('command')
        if name == 'change_mode':
            try:
                mode = RobotMode(command['mode'])
            except (KeyError, ValueError):
                return 400, {'error': 'mode must be idle, manual, patrol, auto, or charging'}
            if mode == RobotMode.CHARGING:
                return node_com_helper.dock_robot(self)
            if mode == RobotMode.AUTO:
                return self._start_auto(command)
            self.state.mode = mode
            self.state.action = RobotAction.IDLE
            return 200, self.state.as_dict()

        if name == 'return_to_charger':
            return node_com_helper.dock_robot(self)

        if name == 'manual_goal':
            self.state.mode = RobotMode.MANUAL
            return node_com_helper.send_goal(self, command)

        if name == 'start_patrol':
            return self._run_patrol()

        return 400, {'error': 'unknown command'}

    def _start_auto(self, _command):
        """Switch to AUTO mode and start the patrol route for the active map."""
        self.state.mode = RobotMode.AUTO
        return self._run_patrol()

    def _run_patrol(self):
        """Load and start the patrol route without changing the current mode.

        On success: action becomes PATROL and the first Nav2 goal is fired.
        On failure: action stays IDLE; mode is untouched.
        If the robot is already patrolling, returns 409.
        """
        if self.state.action == RobotAction.PATROL:
            return 409, {'error': 'patrol already in progress', 'state': self.state.as_dict()}
        route, error = node_com_helper.load_route(self)
        if error:
            self.get_logger().warning(f'Patrol: {error} — staying idle')
            self.state.action = RobotAction.IDLE
            return 200, {**self.state.as_dict(), 'warning': error}
        self.state.action = RobotAction.PATROL
        self.state.patrol_route = route
        self.state.patrol_index = 0
        self.state.active_task = None
        self.state.audio_recording = False
        self._last_patrol_pose = None
        self._last_patrol_regions.clear()
        self._patrol_distance_since_recording = 0.0
        self._audio_pause_requested = False
        self._audio_waiting_for_done = False
        self._audio_resume_advance = False
        self._pending_audio_analyses.clear()
        self._patrol_completion_pending = False
        self._patrol_run = self._create_patrol_run()
        self._publish_audio_context()
        node_com_helper._send_patrol_goal(self, route['waypoints'][0])
        return 200, self.state.as_dict()

    def _create_patrol_run(self):
        if self.state.map_id is None or self.state.patrol_route is None:
            raise RuntimeError('cannot create a patrol run without an active map and route')
        map_dir = Path(self.maps_root).expanduser().resolve() / self.state.map_id
        run_id = datetime.now(timezone.utc).strftime('run_%Y%m%dT%H%M%SZ')
        run_dir = map_dir / 'patrol_runs' / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / 'run.json').write_text(json.dumps({
            'id': run_id,
            'map_id': self.state.map_id,
            'started_at_utc': datetime.now(timezone.utc).isoformat(),
            'route_id': self.state.patrol_route.get('id'),
        }, indent=2) + '\n', encoding='utf-8')
        return {'id': run_id, 'path': run_dir}

    def _publish_audio_context(self):
        if not self._patrol_run:
            return
        message = String()
        message.data = json.dumps({'run_dir': str(self._patrol_run['path'])})
        self.audio_context_pub.publish(message)

    def _battery_cb(self, msg: BatteryState) -> None:
        """Cache the latest battery reading; called from the ROS executor thread."""
        self._battery = msg

    def _check_patrol_regions(self) -> None:
        """Track ROI distance and pause patrol for periodic audio recordings."""
        if self.state.action != RobotAction.PATROL:
            if self._patrol_run:
                run_metadata_path = self._patrol_run['path'] / 'run.json'
                try:
                    metadata = json.loads(run_metadata_path.read_text(encoding='utf-8'))
                    metadata['ended_at_utc'] = datetime.now(timezone.utc).isoformat()
                    run_metadata_path.write_text(
                        json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
                except (OSError, json.JSONDecodeError):
                    self.get_logger().warning('Could not finalize patrol run metadata')
                message = String()
                message.data = json.dumps({'run_dir': None})
                self.audio_context_pub.publish(message)
                self._patrol_run = None
            self._inside_patrol_regions.clear()
            self._last_patrol_pose = None
            self._last_patrol_regions.clear()
            self._patrol_distance_since_recording = 0.0
            return
        if self._audio_waiting_for_done:
            if (self._audio_waiting_since is not None
                    and (self.get_clock().now() - self._audio_waiting_since).nanoseconds / 1e9
                    >= self.audio_recording_timeout):
                self.get_logger().warning('Audio recording acknowledgement timed out; resuming patrol')
                self._resume_patrol_after_audio()
            return
        pose_status, pose = node_com_helper.get_pose(self)
        if pose_status != 200:
            return
        current_regions = set()
        for region in (self.state.patrol_route or {}).get('regions', []):
            region_id = region.get('id', 'unnamed-region')
            inside = (region['min_x'] <= pose['x'] <= region['max_x']
                      and region['min_y'] <= pose['y'] <= region['max_y'])
            if inside:
                current_regions.add(region_id)
                if region_id not in self._inside_patrol_regions:
                    self.get_logger().info(f'Patrol inside region={region_id!r}')
        self._inside_patrol_regions = current_regions
        if (self._last_patrol_pose is not None and current_regions
                and self._last_patrol_regions):
            dx = float(pose['x']) - float(self._last_patrol_pose['x'])
            dy = float(pose['y']) - float(self._last_patrol_pose['y'])
            self._patrol_distance_since_recording += (dx * dx + dy * dy) ** 0.5
        self._last_patrol_pose = pose
        self._last_patrol_regions = current_regions

        waypoints = self.state.patrol_waypoints()
        current_waypoint = (waypoints[self.state.patrol_index]
                            if self.state.patrol_index < len(waypoints) else {})
        if current_waypoint.get('ignore_regions', False):
            self._patrol_distance_since_recording = 0.0
            return
        if (current_regions and not current_waypoint.get('ignore_regions', False)
                and not self._audio_pause_requested
                and self._patrol_distance_since_recording >= self.audio_recording_distance):
            self._request_audio_pause()

    def _request_audio_pause(self) -> None:
        self._audio_pause_requested = True
        self._patrol_distance_since_recording = 0.0
        self.get_logger().info('Patrol ROI distance reached; pausing for audio recording')
        if self._goal_handle is None:
            node_com_helper.start_audio_recording(self)
            return
        self._goal_handle.cancel_goal_async()

    def _audio_done_cb(self, msg: String) -> None:
        if not self._audio_waiting_for_done:
            return
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            payload = {'status': 'failed'}
        if payload.get('status') != 'done':
            self.get_logger().warning(f'Audio recording failed: {payload}')
        else:
            recording = payload.get('entry')
            if not isinstance(recording, dict):
                self.get_logger().warning('Audio recording acknowledgement had no valid entry')
                self._resume_patrol_after_audio()
                return
            self._request_anomaly_analysis(recording)
            self.get_logger().info('Patrol audio recording complete; analyzing recording')
        self._resume_patrol_after_audio()

    def _request_anomaly_analysis(self, recording: dict) -> None:
        waypoints = self.state.patrol_waypoints()
        waypoint = (waypoints[self.state.patrol_index]
                    if self.state.patrol_index < len(waypoints) else {})
        location = waypoint.get('id', f'waypoint_{self.state.patrol_index}')
        request = String()
        recording_path = recording.get('filepath')
        if recording_path:
            self._pending_audio_analyses.add(str(recording_path))
        request.data = json.dumps({
            'recording_path': recording_path,
            'location': location,
            'position': recording.get('end_position') or recording.get('start_position'),
            'recording': recording,
            'run_id': self._patrol_run['id'] if self._patrol_run else None,
            'map_id': self.state.map_id,
        })
        self._append_audio_map_point({
            'position': recording.get('end_position') or recording.get('start_position'),
            'probability': None,
            'result': 'pending',
            'recording': recording,
            'run_id': self._patrol_run['id'] if self._patrol_run else None,
            'map_id': self.state.map_id,
        })
        self.anomaly_request_pub.publish(request)
        self.get_logger().info(
            f'Requested anomaly analysis for location {location!r}')

    def _anomaly_result_cb(self, msg: String) -> None:
        try:
            result = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Received invalid anomaly detection result')
            return
        recording = result.get('recording') or {}
        recording_path = recording.get('filepath')
        if recording_path:
            self._pending_audio_analyses.discard(str(recording_path))
        if result.get('status') == 'ok':
            #! using warning for now to make it more visible in logs; later switch to info
            self.get_logger().warning(f"Audio analysis at position {result.get('position')}: result={result.get('result')}, probability={result.get('probability')}, ")
            self._append_audio_map_point(result)
        else:
            self.get_logger().warning(
                f'Audio anomaly analysis failed: {result.get("reason", result)}')
        if self._patrol_completion_pending and not self._pending_audio_analyses:
            self._patrol_completion_pending = False
            node_com_helper.advance_patrol(self)

    def _append_audio_map_point(self, result):
        run_path = None
        if result.get('run_id') and result.get('map_id'):
            run_path = (
                Path(self.maps_root).expanduser().resolve()
                / str(result['map_id']) / 'patrol_runs' / str(result['run_id'])
            )
        if run_path is None:
            recording = result.get('recording') or {}
            recording_path = recording.get('filepath')
            if recording_path:
                candidate = Path(recording_path).expanduser().resolve().parent.parent
                if (candidate / 'run.json').is_file():
                    run_path = candidate
        if run_path is None or not run_path.is_dir():
            self.get_logger().warning(
                'Could not determine patrol run directory for audio analysis result')
            return
        position = result.get('position') or {}
        if isinstance(position, dict) and all(key in position for key in ('x', 'y')):
            x, y = position['x'], position['y']
        elif isinstance(position, (list, tuple)) and len(position) >= 2:
            x, y = position[0], position[1]
        else:
            self.get_logger().warning(
                f'Ignoring audio analysis result with invalid position: {position!r}')
            return
        path = run_path / 'audio_map.json'
        try:
            points = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
            if not isinstance(points, list):
                points = []
        except (OSError, json.JSONDecodeError):
            points = []
        point = {
            'x': float(x),
            'y': float(y),
            'probability': result.get('probability'),
            'result': result.get('result'),
            'recording': result.get('recording'),
        }
        recording_path = (point['recording'] or {}).get('filepath')
        existing_index = next(
            (index for index, existing in enumerate(points)
             if (existing.get('recording') or {}).get('filepath') == recording_path
             and recording_path),
            None,
        )
        if existing_index is None:
            points.append(point)
        else:
            points[existing_index] = {**points[existing_index], **point}
        path.write_text(json.dumps(points, indent=2) + '\n', encoding='utf-8')

    def _resume_patrol_after_audio(self) -> None:
        resume_after_node = self._audio_resume_advance
        self._audio_pause_requested = False
        self._audio_waiting_for_done = False
        self._audio_waiting_since = None
        self._audio_resume_advance = False
        self.state.audio_recording = False
        if self.state.action == RobotAction.PATROL:
            if resume_after_node:
                waypoints = self.state.patrol_waypoints()
                is_last_waypoint = self.state.patrol_index >= len(waypoints) - 1
                if is_last_waypoint and self._pending_audio_analyses:
                    self._patrol_completion_pending = True
                    self.state.navigation_status = 'analyzing_audio'
                    self.get_logger().info(
                        f'Waiting for {len(self._pending_audio_analyses)} '
                        'audio analysis result(s) before completing patrol')
                    return
                node_com_helper.advance_patrol(self)
                return
            waypoints = self.state.patrol_waypoints()
            if self.state.patrol_index < len(waypoints):
                node_com_helper._send_patrol_goal(
                    self, waypoints[self.state.patrol_index])

    def destroy_node(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PatrolBrain()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
