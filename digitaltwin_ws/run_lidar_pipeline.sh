#!/bin/bash
# run_lidar_pipeline.sh
# Launches the full Gazebo + dual-lidar merge + SLAM + RViz2 pipeline
# in one command, and cleanly kills everything on Ctrl+C.

set -e

########################################
#### Locate root & setup enviroment ####
########################################

## Locate repository root and load environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO_ROOT="$SCRIPT_DIR"
while [ ! -f "$REPO_ROOT/.env" ]; do
    if [ "$REPO_ROOT" = "/" ]; then
        echo "Error: could not find .env file in any parent directory of $SCRIPT_DIR" >&2
        exit 1
    fi
    REPO_ROOT="$(dirname "$REPO_ROOT")"
done

ENV_FILE="$REPO_ROOT/.env"

# Read .env and export variables (handles VAR=value and VAR=${OTHER_VAR})
set -a  # Automatically export all variables
source "$ENV_FILE"
set +a

source "$DIGITALTWIN_WS/install/setup.bash"

PIDS=()

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cleaning up any leftover processes from a previous run...${NC}"
pkill -9 -f "gz sim" 2>/dev/null || true
pkill -9 -f "laserscan_multi_merger" 2>/dev/null || true
pkill -9 -f "slam_toolbox" 2>/dev/null || true
pkill -9 -f "rviz2" 2>/dev/null || true
pkill -9 -f "ros_gz" 2>/dev/null || true
pkill -9 -f "robot_state_publisher" 2>/dev/null || true
sleep 1

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all nodes...${NC}"
    for pid in "${PIDS[@]}"; do
        # negative pid kills the whole process group (setsid gave each its own)
        kill -TERM "-$pid" 2>/dev/null || true
    done
    sleep 1
    pkill -9 -f "gz sim" 2>/dev/null || true
    pkill -9 -f "laserscan_multi_merger" 2>/dev/null || true
    pkill -9 -f "slam_toolbox" 2>/dev/null || true
    pkill -9 -f "rviz2" 2>/dev/null || true
    pkill -9 -f "ros_gz" 2>/dev/null || true
    pkill -9 -f "robot_state_publisher" 2>/dev/null || true

    wait 2>/dev/null || true
    echo -e "${GREEN}Done.${NC}"
}
trap cleanup SIGINT SIGTERM SIGHUP EXIT

echo -e "${GREEN}[1/4] Starting Gazebo + robot + maze...${NC}"
setsid ros2 launch yahboom_M3Pro_description gazebo_display.launch.py &
PIDS+=($!)
sleep 8   # give Gazebo time to spawn the robot before the merger looks for /scan0,/scan1

echo -e "${GREEN}[2/4] Starting lidar scan merger...${NC}"
setsid ros2 run ira_laser_tools laserscan_multi_merger --ros-args --params-file \
    "$DIGITALTWIN_WS/install/ira_laser_tools/share/ira_laser_tools/config/laserscan_merge.yaml" \
    -p use_sim_time:=true &
PIDS+=($!)
sleep 3

echo -e "${GREEN}[3/4] Starting SLAM (slam_toolbox)...${NC}"
setsid ros2 launch slam_engine online_async_launch.py use_sim_time:=true &
PIDS+=($!)
sleep 3

echo -e "${GREEN}[4/4] Starting RViz2...${NC}"
setsid ros2 launch slam_engine slam_view.launch.py use_sim_time:=true &
PIDS+=($!)

echo ""
echo -e "${GREEN}All nodes started. Press Ctrl+C in this terminal to stop everything.${NC}"
wait