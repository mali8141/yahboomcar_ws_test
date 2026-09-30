"""Policy state kept separate from ROS and HTTP transport code."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RobotMode(str, Enum):
    AUTO = 'auto'
    IDLE = 'idle'
    MANUAL = 'manual'
    PATROL = 'patrol'
    CHARGING = 'charging'

class RobotAction(str, Enum):
    IDLE = 'idle'
    NAVIGATE = 'navigate'
    PATROL = 'patrol'
    CHARGE = 'charge'


@dataclass
class BrainState:
    mode: RobotMode = RobotMode.MANUAL
    action: RobotAction = RobotAction.IDLE
    navigation_status: str = 'idle'
    active_goal: dict | None = None
    map_id: str | None = None
    # Patrol route currently loaded (full parsed JSON object).
    patrol_route: dict | None = None
    # Index of the next waypoint to drive to within patrol_route['waypoints'].
    patrol_index: int = 0
    # Task dict from the waypoint the robot is currently travelling toward,
    # or None when no task is active on the current leg.
    active_task: dict | None = None
    # Audio pause state for the current patrol leg.
    audio_recording: bool = False

    def patrol_waypoints(self) -> list:
        if self.patrol_route is None:
            return []
        return self.patrol_route.get('waypoints', [])

    def as_dict(self):
        wps = self.patrol_waypoints()
        return {
            'mode': self.mode.value, 'action': self.action.value,
            'navigation_status': self.navigation_status,
            'active_goal': self.active_goal,
            'map_id': self.map_id,
            'patrol': {
                'route_id': self.patrol_route['id'] if self.patrol_route else None,
                'total_waypoints': len(wps),
                'waypoint_index': self.patrol_index,
                'active_task': self.active_task,
                'audio_recording': self.audio_recording,
            },
        }
