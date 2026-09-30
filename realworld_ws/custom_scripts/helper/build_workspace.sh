#!/bin/bash
set -e

# Usage: ./build_workspace.sh [--build_default] [--build_extra] [--sim]
#   --build_default    Clean and rebuild ALL workspaces before starting.
#   --build_extra      Build extra workspaces.
#   --build_all        Build all workspaces (default + extra).
#   --sim        build specific packages for the digitaltwin_ws Gazebo sim instead of physical hardware.

###############
#### Flags ####
###############

SIM_MODE=false
BUILD_DEFAULT=false
BUILD_EXTRA=false
for arg in "$@"; do
    [[ "$arg" == "--sim" ]] && SIM_MODE=true
    [[ "$arg" == "--build_default" ]] && BUILD_DEFAULT=true
    [[ "$arg" == "--build_extra" ]] && BUILD_EXTRA=true
    [[ "$arg" == "--build_all" ]] && BUILD_DEFAULT=true && BUILD_EXTRA=true
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

# Source .env file if it exists (loads workspace paths)
set -a  # Automatically export all variables
source "$ENV_FILE"
set +a

source /opt/ros/jazzy/setup.bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

##################################
#### Build default workspaces ####
##################################

if [ "$BUILD_DEFAULT" = true ]; then
    rm -rf $YAHBOOMCAR_WS/build $YAHBOOMCAR_WS/install $YAHBOOMCAR_WS/log
    rm -rf $M3PRO_WS/build $M3PRO_WS/install $M3PRO_WS/log
    
    if [ "$SIM_MODE" = true ]; then
        echo -e "${GREEN}Building yahboomcar and m3pro packages (for Gazebo sim)...${NC}"

        cd $YAHBOOMCAR_WS && colcon build --packages-skip orbbec_camera
        source $YAHBOOMCAR_WS/install/setup.bash
        cd $M3PRO_WS && colcon build --symlink-install
    else
        echo -e "${GREEN}Building yahboomcar and m3pro packages (for physical hardware)...${NC}"

        cd $YAHBOOMCAR_WS && colcon build --symlink-install
        source $YAHBOOMCAR_WS/install/setup.bash
        cd $M3PRO_WS && colcon build --symlink-install
    fi
fi

################################
#### Build extra workspaces ####
################################

if [ "$BUILD_EXTRA" = true ]; then
    #### Build SLAM workspace ####
    rm -rf $SLAM_WS/build $SLAM_WS/install $SLAM_WS/log
    echo -e "${GREEN}Building SLAM workspace...${NC}"
    cd $SLAM_WS && colcon build --symlink-install
    source $SLAM_WS/install/setup.bash

    #### Build custom sensors workspace ####
    rm -rf $SENSORS_WS/build $SENSORS_WS/install $SENSORS_WS/log
    echo -e "${GREEN}Building custom sensors...${NC}"
    cd $SENSORS_WS && colcon build --symlink-install
    source $SENSORS_WS/install/setup.bash
fi

