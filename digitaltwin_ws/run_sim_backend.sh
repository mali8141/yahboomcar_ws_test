#!/bin/bash
# Used to run all services needed to act as a backend for the realworld_ws

# Usage: ./run_sim_backend.sh [--build]
#   --build    Build digitaltwin_ws packages before starting.

#################
#### Cleanup ####
#################

# Kill all child processes on exit (Ctrl+C, error, or normal exit)
cleanup() { kill 0 2>/dev/null; }
trap cleanup EXIT INT TERM

###############
#### Flags ####
###############

BUILD_PACKAGES=false
for arg in "$@"; do
    [[ "$arg" == "--build" ]] && BUILD_PACKAGES=true
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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

#### Build digitaltwin_ws packages if requested ####
if [ "$BUILD_PACKAGES" = true ]; then
    echo -e "${GREEN}Building digitaltwin_ws packages... ${NC}"
    cd $DIGITALTWIN_WS
    rm -rf build/ install/ log/
    colcon build --symlink-install
fi

source ${DIGITALTWIN_WS}/install/setup.bash

################################
#### Script specific Config ####
################################

## Sim audio publisher. Drop-in replacement for uma16 stream_publisher.
#SIM_AUDIO_FIELD="${SIM_AUDIO_FIELD:-$HOME/maps/audio_probe_field.npz}" # point to the pre-generated audio sample field
#SIM_AUDIO_FIELD="${SIM_AUDIO_FIELD:-$HOME/maps/all_sources.npz}" # point to the pre-generated audio sample field
SIM_AUDIO_FIELD="${SIM_AUDIO_FIELD:-$HOME/maps/missing_source_2.npz}" # point to the pre-generated audio sample field

####################
#### Launch sim ####
####################

echo -e "${GREEN}Starting sim_audio_publisher (field: $SIM_AUDIO_FIELD)... ${NC}"
ros2 run sim_audio sim_audio_publisher --ros-args -p field_path:="$SIM_AUDIO_FIELD" &

echo -e "${GREEN}Starting battery_simulator... ${NC}"
ros2 run yahboom_M3Pro_description battery_simulator &

echo -e "${GREEN}Starting Gazebo server... ${NC}"
ros2 launch yahboom_M3Pro_description gazebo_display.launch.py bridge_tf:=false &


echo -e "${GREEN}All processes started. Press Ctrl+C to stop.${NC}"
wait