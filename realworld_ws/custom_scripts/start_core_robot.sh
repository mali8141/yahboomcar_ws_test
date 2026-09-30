#!/bin/bash
set -e

# Usage: ./start_core_robot.sh [--record] [--sim]
#   --record           Record audio
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
    [[ "$arg" == "--record" ]] && RECORD=true
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


## Audio setup (skip if pactl not available or device not connected)
if command -v pactl &>/dev/null; then
    sleep 3
    pactl set-default-sink alsa_output.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.analog-stereo 2>/dev/null || echo "Audio sink not found, skipping"
    pactl set-default-source alsa_input.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.mono-fallback 2>/dev/null || echo "Audio source not found, skipping"
fi


if [[ "$SIM_MODE" == "false" ]]; then
    ##################################################
    #### Start physical robot specific components ####
    ##################################################

    ## Starting joy controller
    echo -e "${GREEN}Starting joy controller...${NC}"
    ros2 launch yahboomcar_ctrl yahboomcar_joy_launch.py &
    ros2 run yahboomcar_ctrl yahboom_joy_M3Pro &

    ## Starting micro-ROS agent
    sleep 3
    if [ -f "$MICROROS_WS/install/setup.bash" ]; then
        source $MICROROS_WS/install/setup.bash
        if [ -n "$DISPLAY" ]; then
            gnome-terminal --title=mircoROS_Agent -- bash -c "export ROS_DOMAIN_ID=30 && source /opt/ros/jazzy/setup.bash && source $MICROROS_WS/install/setup.bash && ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/myserial -b 2000000"
        else
            echo -e "${GREEN}Starting micro-ROS agent in background...${NC}"
            bash -c "export ROS_DOMAIN_ID=30 && source /opt/ros/jazzy/setup.bash && source $MICROROS_WS/install/setup.bash && ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/myserial -b 2000000" &
        fi
    else
        echo -e "${RED}WARNING: micro-ROS agent not found at $MICROROS_WS${NC}"
    fi

    ## Starting custom sensor suite (UMA16 microphone + acoustic overlay)
    ##! untested
    set -euo pipefail
    export OPENBLAS_NUM_THREADS=1

    echo -e "${GREEN}Starting UMA16 stream publisher...${NC}"
    ros2 run uma16 stream_publisher --ros-args -p device_index:=-1 &

    echo -e "${GREEN}Starting UMA16 acoustic overlay...${NC}"
    ros2 run uma16 acoustic_overlay --ros-args -p threshold_db:=0.0 &

    if $RECORD; then
        echo -e "${GREEN}Starting UMA16 stream recorder...${NC}"
        ros2 run uma16 stream_recorder &
    fi

    ###################################################
    #### Start robot general components (hardware) ####
    ###################################################

    ## start audio map recorder
    echo -e "${GREEN}Starting audio map recorder...${NC}"
    ros2 run audio_map audio_mapper --ros-args -p save_dir:="$SOUND_MAP_DIR"
else
    ##############################################
    #### Start robot general components (sim) ####
    ##############################################

    ## Sim mode: start sensor processing pipeline pointed at Gazebo topics
    echo -e "${GREEN}Starting audio map recorder...${NC}"
    ros2 run audio_map audio_mapper use_sim_time:=true --ros-args -p save_dir:="$SOUND_MAP_DIR"
fi

# Wait for background processes so Ctrl+C can clean them up
wait
