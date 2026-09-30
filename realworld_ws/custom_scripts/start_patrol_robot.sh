#!/bin/bash
set -e

# Usage: ./start_patrol_robot.sh [--sim]
#   --sim              Run against the digitaltwin_ws Gazebo sim instead of
#                      physical hardware

#################
#### Cleanup ####
#################

# Kill all child processes on exit (Ctrl+C, error, or normal exit)
cleanup() { kill 0 2>/dev/null; }
trap cleanup EXIT INT TERM

###############
#### Flags ####
###############

SIM_MODE=false
RECORD=false
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

# ROS_DOMAIN_ID=30 is for the physical robot (network isolation). In sim mode both sides run on localhost and use the default domain (0).
[[ "$SIM_MODE" == "false" ]] && export ROS_DOMAIN_ID=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

source $YAHBOOMCAR_WS/install/setup.bash
source $M3PRO_WS/install/setup.bash
source $SLAM_WS/install/setup.bash
source $SENSORS_WS/install/setup.bash

#####################################
#### Start core Robot components ####
#####################################

echo -e "${GREEN}Starting core robot components...${NC}"
${REPO_ROOT}/realworld_ws/custom_scripts/start_core_robot.sh "$@" &
sleep 3

#######################################
#### Start patrol Robot components ####
#######################################

# Start NAV2 stack
echo -e "${GREEN}Starting NAV2 stack...${NC}"
#Q${REPO_ROOT}/realworld_ws/custom_scripts/nav_2d_localization.sh "$@" --no-gui &
${REPO_ROOT}/realworld_ws/custom_scripts/nav_2d_localization.sh "$@" &
sleep 3

# Start anomaly_detection node
echo -e "${GREEN}Starting anomaly_detection node...${NC}"
ros2 run anomaly_detection anomaly_detector \
    --ros-args \
    -p data_known:=${REPO_ROOT}/realworld_ws/data_known \
    -p reference_radius_m:=0.25 \
    -p detector:=sine_distance &
sleep 3

# Start patrol_brain node
echo -e "${GREEN}Starting patrol_brain node...${NC}"
ros2 run patrol_brain patrol_brain &

# Wait for background processes so Ctrl+C can clean them up
wait
