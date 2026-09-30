import json
import math
from pathlib import Path

import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import DockRobot, NavigateToPose
from nav2_msgs.srv import LoadMap
from nav_msgs.srv import GetMap
from std_msgs.msg import Float32
from tf2_ros import (Buffer, ConnectivityException, ExtrapolationException,
                     LookupException, TransformListener)

from .brain_state import RobotMode, RobotAction

from . import math_helper


def _map_catalog(root_value):
    """Return map YAML files directly owned by folders beneath maps_root."""
    root = Path(root_value).expanduser().resolve()
    if not root.is_dir():
        return [], root

    maps = []
    for folder in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if not folder.is_dir():
            continue
        folder = folder.resolve()
        try:
            folder.relative_to(root)
        except ValueError:
            continue
        candidates = list(folder.glob('*.yaml')) + list(folder.glob('*.yml'))
        candidates.sort(key=lambda path: (
            path.name not in ('map.yaml', 'map.yml'), path.name.lower()))
        for candidate in candidates:
            resolved = candidate.resolve()
            try:
                resolved.relative_to(folder.resolve())
            except ValueError:
                continue
            try:
                contents = resolved.read_text(encoding='utf-8')
            except OSError:
                continue
            if 'image:' in contents and 'resolution:' in contents and 'origin:' in contents:
                maps.append({
                    'id': folder.name,
                    'name': folder.name,
                    'map_yaml': resolved,
                })
                break
    return maps, root


def list_maps(self):
    maps, _ = _map_catalog(self.maps_root)
    return 200, {
        'maps': [map_summary(self, item) for item in maps],
        'current_map_id': self.state.map_id,
    }


def map_summary(self, item):
    route, _ = read_route(self, item['id'], allow_empty=True)
    return {
        'id': item['id'],
        'name': item['name'],
        'has_route': route is not None and bool(route.get('waypoints')),
        'waypoint_count': len(route.get('waypoints', [])) if route else 0,
    }


def _map_by_id(self, map_id):
    maps, _ = _map_catalog(self.maps_root)
    return next((item for item in maps if item['id'] == map_id), None)


def _route_path(self, map_id):
    selected = _map_by_id(self, map_id)
    if selected is None:
        return None, 'unknown map_id'
    return selected['map_yaml'].parent / 'route.json', None


def read_route(self, map_id, allow_empty=False):
    route_path, error = _route_path(self, map_id)
    if error:
        return None, error
    try:
        route = json.loads(route_path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        if allow_empty:
            return {'id': map_id, 'frame_id': self.map_frame, 'waypoints': []}, None
        return None, f'no route.json found for map {map_id!r}'
    except (OSError, json.JSONDecodeError) as read_error:
        return None, f'failed to read route.json: {read_error}'
    return _validate_route(route, map_id)


def _validate_route(route, map_id):
    if not isinstance(route, dict):
        return None, 'route must be a JSON object'
    waypoints = route.get('waypoints')
    if not isinstance(waypoints, list):
        return None, 'route.json must contain a "waypoints" list'
    legacy_regions = []
    for index, waypoint in enumerate(waypoints):
        if not isinstance(waypoint, dict):
            return None, f'waypoint {index} must be an object'
        pose = waypoint.get('pose')
        if not isinstance(pose, dict):
            return None, f'waypoint {index} must contain a pose object'
        if not isinstance(waypoint.get('ignore_regions', False), bool):
            return None, f'waypoint {index} ignore_regions must be a boolean'
        if not isinstance(waypoint.get('sample_audio', False), bool):
            return None, f'waypoint {index} sample_audio must be a boolean'
        if not all(isinstance(pose.get(key), (int, float))
                   and math.isfinite(pose[key]) for key in ('x', 'y', 'yaw')):
            return None, f'waypoint {index} missing valid pose.x / pose.y / pose.yaw'
        waypoint_regions = waypoint.get('regions', [])
        if not isinstance(waypoint_regions, list):
            return None, f'waypoint {index} regions must be a list'
        for region_index, region in enumerate(waypoint_regions):
            legacy_region = dict(region)
            legacy_region.setdefault('id', f'waypoint-{index}-region-{region_index}')
            legacy_regions.append(legacy_region)
    regions = route.get('regions', [])
    if not isinstance(regions, list):
        return None, 'route regions must be a list'
    regions = regions + legacy_regions
    for region_index, region in enumerate(regions):
        if not isinstance(region, dict):
            return None, f'region {region_index} must be an object'
        bounds = [region.get(key) for key in ('min_x', 'min_y', 'max_x', 'max_y')]
        if not all(isinstance(value, (int, float)) and math.isfinite(value)
                   for value in bounds):
            return None, f'region {region_index} has invalid bounds'
        if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
            return None, f'region {region_index} must have positive size'
    normalized = dict(route)
    normalized['id'] = str(route.get('id') or map_id)
    normalized['frame_id'] = str(route.get('frame_id') or 'map')
    normalized['waypoints'] = [
        {key: value for key, value in waypoint.items() if key != 'regions'}
        for waypoint in waypoints
    ]
    normalized['regions'] = regions
    return normalized, None


def get_route(self, map_id):
    route, error = read_route(self, map_id, allow_empty=True)
    if error:
        return 404, {'error': error}
    return 200, {'map_id': map_id, 'route': route}


def _patrol_runs_dir(self, map_id):
    selected = _map_by_id(self, map_id)
    return selected['map_yaml'].parent / 'patrol_runs' if selected else None


def list_patrol_runs(self):
    runs = []
    for map_item in _map_catalog(self.maps_root)[0]:
        runs_dir = map_item['map_yaml'].parent / 'patrol_runs'
        if not runs_dir.is_dir():
            continue
        for run_dir in sorted(runs_dir.iterdir(), reverse=True):
            if not run_dir.is_dir() or run_dir.name in ('.', '..'):
                continue
            run_path = run_dir / 'run.json'
            try:
                metadata = json.loads(run_path.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                continue
            points_path = run_dir / 'audio_map.json'
            try:
                points = json.loads(points_path.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                points = []
            recordings_path = run_dir / 'recordings_metadata.json'
            try:
                recordings = json.loads(recordings_path.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                recordings = []
            runs.append({
                **metadata,
                'map_id': map_item['id'],
                'point_count': len(points),
                'recording_count': len(recordings) if isinstance(recordings, list) else 0,
            })
    return 200, {'runs': runs}


def get_patrol_run(self, map_id, run_id):
    runs_dir = _patrol_runs_dir(self, map_id)
    if runs_dir is None or Path(run_id).name != run_id:
        return 404, {'error': 'unknown patrol run'}
    run_dir = runs_dir / run_id
    if not run_dir.is_dir():
        return 404, {'error': 'unknown patrol run'}
    try:
        metadata = json.loads((run_dir / 'run.json').read_text(encoding='utf-8'))
        points_path = run_dir / 'audio_map.json'
        points = json.loads(points_path.read_text(encoding='utf-8')) \
            if points_path.exists() else []
        recordings_path = run_dir / 'recordings_metadata.json'
        recordings = json.loads(recordings_path.read_text(encoding='utf-8')) \
            if recordings_path.exists() else []
    except FileNotFoundError:
        return 404, {'error': 'unknown patrol run'}
    except (OSError, json.JSONDecodeError) as error:
        return 500, {'error': f'failed to read patrol run: {error}'}
    return 200, {
        'run': {
            **metadata,
            'map_id': map_id,
            'points': points if isinstance(points, list) else [],
            'recordings': recordings if isinstance(recordings, list) else [],
        },
    }


def save_route(self, map_id, payload):
    if self.state.action == RobotAction.PATROL and self.state.map_id == map_id:
        return 409, {'error': 'cannot edit the active route while patrol is running'}
    route_path, error = _route_path(self, map_id)
    if error:
        return 404, {'error': error}
    route, error = _validate_route(payload.get('route'), map_id) \
        if isinstance(payload, dict) else (None, 'route must be a JSON object')
    if error:
        return 400, {'error': error}
    if not route['waypoints']:
        return 400, {'error': 'route must contain at least one waypoint'}
    try:
        route_path.write_text(json.dumps(route, indent=2) + '\n', encoding='utf-8')
    except OSError as write_error:
        return 500, {'error': f'failed to save route.json: {write_error}'}
    return 200, {'map_id': map_id, 'route': route}


def set_map(self, payload, response):
    """Load one advertised map, never an arbitrary browser-supplied path."""
    if not isinstance(payload, dict) or not isinstance(payload.get('map_id'), str):
        response.set_result((400, {'error': 'map_id must be a map advertised by GET /maps'}))
        return

    maps, _ = _map_catalog(self.maps_root)
    selected = next((item for item in maps if item['id'] == payload['map_id']), None)
    if selected is None:
        response.set_result((404, {'error': 'unknown map_id'}))
        return
    if not self.map_load_client.service_is_ready():
        response.set_result((503, {'error': 'Nav2 map load service is unavailable'}))
        return

    if self._goal_handle is not None:
        self._goal_handle.cancel_goal_async()
        self._goal_handle = None

    request = LoadMap.Request()
    # This Nav2/map_io version expects a normal absolute filesystem path here.
    # Although newer documentation also describes file:// URIs, this install
    # passes the URI through as a literal filename and rejects it.
    request.map_url = str(selected['map_yaml'])
    self.state.navigation_status = 'loading_map'
    self.map_load_client.call_async(request).add_done_callback(
        lambda future: on_map_loaded(self, selected, response, future))


def on_map_loaded(self, selected, response_future, future):
    try:
        result = future.result()
        if result.result != LoadMap.Response.RESULT_SUCCESS:
            self.state.navigation_status = 'map_load_failed'
            response_future.set_result((422, {
                'error': 'Nav2 rejected the map',
                'result': result.result,
            }))
            return
        self.state.map_id = selected['id']
        self.state.active_goal = None
        self.state.navigation_status = 'idle'
        response_future.set_result((200, {
            'status': 'loaded',
            'map': {'id': selected['id'], 'name': selected['name']},
        }))
    except Exception as error:
        self.state.navigation_status = 'map_load_failed'
        self.get_logger().error(f'Unable to load map: {error}')
        response_future.set_result((503, {'error': f'failed to load map: {error}'}))


def send_goal(self, payload):
    if self.state.action == RobotAction.PATROL:
        return 409, {'error': 'navigation is not allowed while patrol is active',
                        'state': self.state.as_dict()}
    try:
        x = float(payload['x'])
        y = float(payload['y'])
        yaw = float(payload.get('yaw', 0.0))
        frame_id = str(payload.get('frame_id', self.map_frame))
        if not all(math.isfinite(value) for value in (x, y, yaw)) or not frame_id:
            raise ValueError('x, y, yaw, and frame_id must be finite, non-empty values')
    except (KeyError, TypeError, ValueError) as error:
        return 400, {'error': f'invalid goal: {error}'}
    if not self.navigate_client.server_is_ready():
        return 503, {'error': 'Nav2 NavigateToPose action server is unavailable'}

    goal = NavigateToPose.Goal()
    goal.pose.header.frame_id = frame_id
    goal.pose.header.stamp = self.get_clock().now().to_msg()
    goal.pose.pose.position.x = x
    goal.pose.pose.position.y = y
    goal.pose.pose.orientation = math_helper.yaw_to_quaternion(yaw)
    self.state.active_goal = {'frame_id': frame_id, 'x': x, 'y': y, 'yaw': yaw}
    self.state.navigation_status = 'submitting'
    self.navigate_client.send_goal_async(goal).add_done_callback(
        lambda future: on_goal_response(self, future))
    return 202, {'status': 'submitted', 'goal': self.state.active_goal}

def on_goal_response(self, future):
    """Record Nav2's decision and subscribe for the final result."""
    try:
        goal_handle = future.result()
    except Exception as error:
        self.state.navigation_status = 'failed_to_send'
        self.get_logger().error(f'Unable to submit navigation goal: {error}')
        return

    if not goal_handle.accepted:
        self.state.navigation_status = 'rejected'
        self.get_logger().warning('Nav2 rejected the navigation goal')
        return

    self._goal_handle = goal_handle
    self.state.navigation_status = 'executing'
    goal_handle.get_result_async().add_done_callback(
        lambda future: on_goal_result(self, future))

def on_goal_result(self, future):
    """Store the terminal Nav2 action status; advance patrol when in PATROL mode."""
    try:
        result = future.result()
        statuses = {
            GoalStatus.STATUS_SUCCEEDED: 'succeeded',
            GoalStatus.STATUS_CANCELED: 'canceled',
            GoalStatus.STATUS_ABORTED: 'aborted',
        }
        self.state.navigation_status = statuses.get(result.status, 'unknown')
        self.get_logger().info(
            f'Navigation goal finished with status: {self.state.navigation_status}')
    except Exception as error:
        self.state.navigation_status = 'failed'
        self.get_logger().error(f'Navigation goal did not return a result: {error}')
    finally:
        self._goal_handle = None

    if (self.state.action == RobotAction.PATROL
            and self._audio_pause_requested
            and self.state.navigation_status == 'canceled'):
        start_audio_recording(self)
        return

    if (self.state.action == RobotAction.PATROL
            and self.state.navigation_status == 'succeeded'):
        waypoints = self.state.patrol_waypoints()
        current_waypoint = (waypoints[self.state.patrol_index]
                            if self.state.patrol_index < len(waypoints) else {})
        if current_waypoint.get('sample_audio', False):
            self._audio_resume_advance = True
            start_audio_recording(self)
            return

    # Drive the patrol loop: only advance on clean success; abort/cancel/fail
    # leave the robot stopped so a human can intervene.
    if (self.state.action == RobotAction.PATROL
            and self.state.navigation_status == 'succeeded'):
        advance_patrol(self)


def get_map(self, response):
    """Fetch the occupancy grid currently served by Nav2's map server."""
    if not self.map_client.service_is_ready():
        response.set_result((503, {
            'error': 'Nav2 map service is unavailable',
        }))
        return
    self.map_client.call_async(GetMap.Request()).add_done_callback(
        lambda future: on_map_response(self, response, future))


def on_map_response(self, response_future, future):
    try:
        occupancy_grid = future.result().map
        origin = occupancy_grid.info.origin
        response_future.set_result((200, {
            'header': {
                'frame_id': occupancy_grid.header.frame_id,
                'stamp': {
                    'sec': occupancy_grid.header.stamp.sec,
                    'nanosec': occupancy_grid.header.stamp.nanosec,
                },
            },
            'info': {
                'map_load_time': {
                    'sec': occupancy_grid.info.map_load_time.sec,
                    'nanosec': occupancy_grid.info.map_load_time.nanosec,
                },
                'resolution': occupancy_grid.info.resolution,
                'width': occupancy_grid.info.width,
                'height': occupancy_grid.info.height,
                'origin': {
                    'position': {
                        'x': origin.position.x,
                        'y': origin.position.y,
                        'z': origin.position.z,
                    },
                    'orientation': {
                        'x': origin.orientation.x,
                        'y': origin.orientation.y,
                        'z': origin.orientation.z,
                        'w': origin.orientation.w,
                    },
                },
            },
            'data': list(occupancy_grid.data),
        }))
    except Exception as error:
        self.get_logger().error(f'Unable to retrieve the Nav2 map: {error}')
        response_future.set_result((503, {
            'error': f'failed to retrieve the Nav2 map: {error}',
        }))

def load_route(self):
    """Load route.json from the active map's directory.

    Returns (route_dict, None) on success, (None, error_str) on failure.
    The route is validated for the minimum required fields only.
    """
    if self.state.map_id is None:
        return None, 'no map loaded'
    route, error = read_route(self, self.state.map_id)
    if error:
        return None, error
    if not route['waypoints']:
        return None, 'route.json must contain a non-empty "waypoints" list'
    return route, None


def _send_patrol_goal(self, waypoint):
    """Issue a NavigateToPose goal for one patrol waypoint (fire-and-forget)."""
    pose = waypoint['pose']
    frame_id = self.state.patrol_route.get('frame_id', self.map_frame)
    x = float(pose['x'])
    y = float(pose['y'])
    yaw = float(pose['yaw'])
    goal = NavigateToPose.Goal()
    goal.pose.header.frame_id = frame_id
    goal.pose.header.stamp = self.get_clock().now().to_msg()
    goal.pose.pose.position.x = x
    goal.pose.pose.position.y = y
    goal.pose.pose.orientation = math_helper.yaw_to_quaternion(yaw)
    self.state.active_goal = {'frame_id': frame_id, 'x': x, 'y': y, 'yaw': yaw}
    self.state.active_task = waypoint.get('task')
    self.state.navigation_status = 'submitting'
    self.navigate_client.send_goal_async(goal).add_done_callback(
        lambda future: on_goal_response(self, future))
    wp_id = waypoint.get('id', self.state.patrol_index)
    self.get_logger().info(
        f'Patrol: driving to waypoint {wp_id!r} '
        f'({x:.2f}, {y:.2f}) task={self.state.active_task}')


def start_audio_recording(self):
    """Request one recording after the current patrol goal has stopped."""
    if self._audio_waiting_for_done:
        return
    message = Float32()
    message.data = self.audio_recording_duration
    self.audio_trigger_pub.publish(message)
    self._audio_waiting_for_done = True
    self._audio_waiting_since = self.get_clock().now()
    self.state.audio_recording = True
    self.state.navigation_status = 'recording_audio'
    self.get_logger().info(
        f'Patrol: recording {self.audio_recording_duration:.1f}s of audio')


def advance_patrol(self):
    """Advance to the next waypoint or finish the route.

    Called after a patrol goal succeeds (task dispatch not yet implemented;
    task handlers will call this when they finish).
    """
    waypoints = self.state.patrol_waypoints()
    next_index = self.state.patrol_index + 1

    if next_index < len(waypoints):
        self.state.patrol_index = next_index
        _send_patrol_goal(self, waypoints[next_index])
    else:
        # Route complete: stay in AUTO, go idle.
        route_id = self.state.patrol_route.get('id', '?')
        self.get_logger().info(
            f'Patrol route {route_id!r} complete — returning to idle')
        self.state.action = RobotAction.IDLE
        self.state.active_goal = None
        self.state.active_task = None
        self.state.navigation_status = 'idle'
        # patrol_route and patrol_index are intentionally kept so callers can
        # inspect what route just finished; they are reset on the next start.


def dock_robot(self):
    """Send a DockRobot goal to the docking_server and return 202 immediately."""
    if self.state.mode == RobotMode.CHARGING:
        return 409, {'error': 'already docking', 'state': self.state.as_dict()}
    self.state.mode = RobotMode.CHARGING
    self.state.navigation_status = 'docking'
    goal = DockRobot.Goal()
    goal.use_dock_id = True
    goal.dock_id = self.dock_id
    self.dock_client.send_goal_async(goal).add_done_callback(
        lambda future: on_dock_response(self, future))
    return 202, {'status': 'submitted', 'dock_id': self.dock_id}


def on_dock_response(self, future):
    """Record the docking server's accept/reject decision."""
    try:
        goal_handle = future.result()
    except Exception as error:
        self.state.navigation_status = 'idle'
        self.state.mode = RobotMode.IDLE
        self.get_logger().error(f'Unable to submit dock goal: {error}')
        return
    if not goal_handle.accepted:
        self.state.navigation_status = 'idle'
        self.state.mode = RobotMode.IDLE
        self.get_logger().warning('Docking server rejected the dock goal')
        return
    goal_handle.get_result_async().add_done_callback(
        lambda future: on_dock_result(self, future))


def on_dock_result(self, future):
    """Update state once docking completes, fails, or is cancelled."""
    try:
        result = future.result()
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.state.navigation_status = 'docked'
            self.get_logger().info('Docking succeeded')
        elif result.status == GoalStatus.STATUS_CANCELED:
            self.state.navigation_status = 'idle'
            self.state.mode = RobotMode.IDLE
            self.get_logger().info('Docking cancelled')
        else:
            self.state.navigation_status = 'idle'
            self.state.mode = RobotMode.IDLE
            self.get_logger().warning(
                f'Docking aborted (error_code={result.result.error_code})')
    except Exception as error:
        self.state.navigation_status = 'idle'
        self.state.mode = RobotMode.IDLE
        self.get_logger().error(f'Dock goal result error: {error}')

def get_pose(self):
    try:
        transform = self.tf_buffer.lookup_transform(
            self.map_frame, self.base_frame, rclpy.time.Time())
    except (LookupException, ConnectivityException, ExtrapolationException) as error:
        return 503, {'error': f'failed to get robot pose: {error}'}
    position = transform.transform.translation
    orientation = transform.transform.rotation
    yaw = math_helper.quaternion_to_yaw(orientation)
    return 200, {
        'frame_id': self.map_frame,
        'x': position.x,
        'y': position.y,
        'yaw': yaw,
    }
