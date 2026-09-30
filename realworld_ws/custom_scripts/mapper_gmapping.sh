#!/bin/bash

# 1
# GMapping (Rao-Blackwellized particle filter) Uses merged LiDAR (/scan) + EKF-fused wheel odom.
# 2d map
#
# Usage: ./mapper_gmapping.sh [--sim]
#   --sim   Run against the digitaltwin_ws Gazebo sim.
#           Assumes start_core_robot.sh --sim is already running (sim_bridge handles
#           bringup, EKF, laser merger/filter). Skips UMA16 and audio nodes.

#################
#### Cleanup ####
#################

cleanup() {
    # EXIT is also raised after INT/TERM; do not save or stop twice.
    [[ "${CLEANUP_DONE:-false}" == "true" ]] && return
    CLEANUP_DONE=true

    # Save 2D map while slam_gmapping is still alive
    echo -e "${GREEN}------------------------------------------------${NC}"

    mkdir -p "$MAP_OUT_DIR"

    echo -e "${GREEN}Saving 2D map to $MAP_OUT_DIR...${NC}"
    if ros2 launch slam_mapping save_map.launch.py; then
        sleep 1
        cp "$MAP_NAV_DIR"/*.pgm "$MAP_OUT_DIR/" 2>/dev/null || true
        cp "$MAP_NAV_DIR"/*.yaml "$MAP_OUT_DIR/" 2>/dev/null || true
    else
        echo -e "${YELLOW}Map save failed; no map was available on the map topic.${NC}"
    fi

    echo -e "${GREEN}------------------------------------------------${NC}"
    echo -e "${GREEN}Stopping processes...${NC}"

    # Graceful: SIGINT to each process group
    for pid in "${PIDS[@]}"; do
        kill -INT -- "-$pid" 1>/dev/null 2>&1 || true
    done
    sleep 1

    # Force-kill any survivors
    for pid in "${PIDS[@]}"; do
        kill -9 -- "-$pid" 1>/dev/null 2>&1 || true
    done

    wait &>/dev/null
    echo -e "${GREEN}All processes stopped.${NC}"
    echo -e "${GREEN}------------------------------------------------${NC}"
    exit 0
}

trap cleanup EXIT INT TERM
PIDS=()

###############
#### Flags ####
###############

SIM_MODE=false
for arg in "$@"; do
    [[ "$arg" == "--sim" ]] && SIM_MODE=true
done

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

if [[ "$SIM_MODE" == "false" ]]; then
    source /home/jetson/microROS_agent/install/setup.bash
fi

source $YAHBOOMCAR_WS/install/setup.bash
source $M3PRO_WS/install/setup.bash
source $SLAM_WS/install/setup.bash
source $SENSORS_WS/install/setup.bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################
#### Script specific Config ####
################################

MAP_OUT_DIR="${MAP_VAULT_DIR}/gmapping"

#############################
#### Pre-flight cleanup  ####
#############################

# Kill any stale mapper nodes from a previous run that didn't exit cleanly.
echo -e "${YELLOW}Cleaning up any leftover mapper processes from a previous run...${NC}"
pkill -9 -f "ekf_filter_node"          2>/dev/null || true
pkill -9 -f "imu_filter_madgwick"      2>/dev/null || true
pkill -9 -f "laserscan_multi_merger"   2>/dev/null || true
pkill -9 -f "yahboom_laser_filter"     2>/dev/null || true
pkill -9 -f "slam_gmapping"            2>/dev/null || true
pkill -9 -f "rviz2"                    2>/dev/null || true
sleep 3

#############################
#### Starting ROS2 Nodes ####
#############################

# In sim mode bringup.launch.py handles EKF + laser merger/filter with sim time.
# On hardware it runs without sim time.
if [[ "$SIM_MODE" == "true" ]]; then
    echo -e "${GREEN}[1/3] Starting bringup (sim mode)...${NC}"
    setsid ros2 launch slam_mapping bringup.launch.py use_sim_time:=true &
    PIDS+=($!)
else
    echo -e "${GREEN}[1/3] Starting bringup (hardware mode)...${NC}"
    setsid ros2 launch slam_mapping bringup.launch.py &
    PIDS+=($!)
fi
sleep 3

if [[ "$SIM_MODE" == "true" ]]; then
    echo -e "${GREEN}[2/3] Starting GMapping (sim mode)...${NC}"
    setsid ros2 launch slam_gmapping slam_gmapping.launch.py use_sim_time:=true &
else
    echo -e "${GREEN}[2/3] Starting GMapping (hardware mode)...${NC}"
    setsid ros2 launch slam_gmapping slam_gmapping.launch.py &
fi
PIDS+=($!)
sleep 3

#echo -e "${GREEN}[3/3] Starting audio mapper...${NC}"
#setsid ros2 run audio_map audio_mapper --ros-args -p save_dir:="$MAP_OUT_DIR" &
#PIDS+=($!)
#setsid ros2 run audio_map audio_recording_trigger &
#PIDS+=($!)
#sleep 3

echo -e "${GREEN}Starting visualizer...${NC}"
setsid ros2 launch slam_mapping slam_view.launch.py &
PIDS+=($!)

echo -e "${GREEN}All nodes are running | Press Ctrl+C to stop.${NC}"
wait