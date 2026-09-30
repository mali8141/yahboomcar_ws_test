#!/bin/bash
set -euo pipefail

# This scrip simply runns the same patrol a defined number of times. Usefull for gathering the initial known good sound daata of a patrol route.
# Usage: ./run_patrol_test.sh MAP_ID [REPEATS]
# The selected map's route.json supplies the patrol waypoints.

MAP_ID="${1:-}"
REPEATS="${2:-${PATROL_REPEATS:-1}}"
API_URL="${PATROL_API_URL:-http://127.0.0.1:8080}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROBOT_PID=""

if [[ -z "$MAP_ID" || ! "$REPEATS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: $0 MAP_ID [REPEATS]" >&2
    exit 2
fi

cleanup() {
    if [[ -n "$ROBOT_PID" ]]; then
        kill -TERM "-$ROBOT_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

wait_for_api() {
    for _ in {1..60}; do
        if curl -fsS "$API_URL/get_status" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "ERROR: patrol_brain API did not become available at $API_URL" >&2
    return 1
}

wait_for_state() {
    local expected="$1"
    for _ in {1..3600}; do
        local status
        status="$(curl -fsS "$API_URL/get_status")"
        if grep -q '"action"[[:space:]]*:[[:space:]]*"'"$expected"'"' <<< "$status"; then
            return 0
        fi
        if grep -q '"navigation_status"[[:space:]]*:[[:space:]]*"\(aborted\|failed\|canceled\|rejected\)"' <<< "$status"; then
            echo "ERROR: patrol navigation failed: $status" >&2
            return 1
        fi
        sleep 1
    done
    echo "ERROR: timed out waiting for patrol state '$expected'" >&2
    return 1
}

if ! curl -fsS "$API_URL/get_status" >/dev/null 2>&1; then
    echo "Starting patrol robot components..."
    setsid "$SCRIPT_DIR/start_patrol_robot.sh" &
    ROBOT_PID=$!
fi

wait_for_api

echo "Loading patrol map: $MAP_ID"
curl --fail-with-body -sS -X PUT "$API_URL/set_map" \
    -H 'Content-Type: application/json' \
    --data "{\"map_id\":\"$MAP_ID\"}" >/dev/null

for ((run = 1; run <= REPEATS; run++)); do
    echo "Starting patrol $run/$REPEATS"
    curl --fail-with-body -sS -X POST "$API_URL/commands" \
        -H 'Content-Type: application/json' \
        --data '{"command":"start_patrol"}' >/dev/null
    wait_for_state patrol
    wait_for_state idle
    echo "Patrol $run/$REPEATS complete"
done