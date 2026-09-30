#!/bin/bash

# Custom Navigation Script with Obstacle Avoidance

# Usage: ./run_nav_2d_localization.sh [--sim]
#   --sim      Run against the digitaltwin_ws Gazebo sim.
#   --no-gui   Don't launch RViz GUI for visualization.


#################
#### Cleanup ####
#################

cleanup() {
    echo "------------------------------------------------"
    echo "Stopping processes..."

    # Graceful SIGINT to each tracked process and its entire subtree
    for pid in "${PIDS[@]}"; do
        kill -INT "$pid" 2>/dev/null
        # Also signal the process group in case ros2 launch created one
        kill -INT -- "-$pid" 2>/dev/null
    done
    sleep 2

    # Force-kill any survivors and their children
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            # Kill entire subtree rooted at $pid
            pkill -9 -P "$pid" 2>/dev/null
            kill -9 "$pid" 2>/dev/null
        fi
    done

    # Last-resort: catch any orphaned ros2/component_container/rviz2 processes
    pkill -9 -f "ros2 launch" 2>/dev/null
    pkill -9 -f "component_container" 2>/dev/null
    pkill -9 -f "rviz2" 2>/dev/null

    wait 2>/dev/null
    echo "All processes stopped."
    echo "------------------------------------------------"
}

trap cleanup EXIT INT TERM
PIDS=()

###############
#### Flags ####
###############

SIM_MODE=false
GUI_MODE=true
for arg in "$@"; do
    [[ "$arg" == "--sim" ]] && SIM_MODE=true
    [[ "$arg" == "--no-gui" ]] && GUI_MODE=false
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

MAP_OUT_DIR="${MAP_VAULT_DIR}/gmapping_$(date +%Y%m%d_%H%M%S)"

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

# When deployed to robot, params are in home directory
CUSTOM_PARAMS="./config/nav2_params_2d_localization.yaml"
CUSTOM_PARAMS_SIM="./config/nav2_params_2d_localization_sim.yaml"

###########################
#### Starting ROS2 NAV ####
###########################

echo -e "${GREEN}=== Starting Custom Autonomous Navigation ===${NC}"
echo ""

# 1. Start base sensors
echo -e "${GREEN}[1/3] Starting base sensors and robot hardware...${NC}"
if [[ "$SIM_MODE" == "true" ]]; then
    ros2 launch M3Pro_navigation base_bringup.launch.py use_sim_time:=true &
else
    ros2 launch M3Pro_navigation base_bringup.launch.py &
fi

PIDS+=($!)
sleep 3

# 2. Start Nav2 with custom parameters and AMCL localization
echo -e "${GREEN}[2/3] Starting Nav2 with custom parameters (AMCL localization enabled)...${NC}"

if [[ "$SIM_MODE" == "true" ]]; then
    ros2 launch M3Pro_navigation navigation2.launch.py params_file:="$CUSTOM_PARAMS_SIM" use_sim_time:=true &
else
    ros2 launch M3Pro_navigation navigation2.launch.py params_file:="$CUSTOM_PARAMS" &
fi

PIDS+=($!)
sleep 3


# 3. Launch visualizer
if [[ "$GUI_MODE" == "true" ]]; then
    echo -e "${GREEN}[3/3] Starting RViz visualizer...${NC}"

    if [[ "$SIM_MODE" == "true" ]]; then
        ros2 launch M3Pro_navigation nav_rviz.launch.py use_sim_time:=true &
    else
        ros2 launch M3Pro_navigation nav_rviz.launch.py &
    fi

    PIDS+=($!)
fi

# 7. Wait indefinitely until a signal (like Ctrl+C) is caught
wait
