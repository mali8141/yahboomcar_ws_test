#!/bin/bash

# 3
# RTAB-Map full fusion (RGB-D camera + merged LiDAR + wheel odom + IMU)
# 2d & 3d map
#
# Usage: ./mapper_rtab_full_fusion.sh [--sim]
#   --sim   Run against the digitaltwin_ws Gazebo sim.
#           Assumes start_core_robot.sh --sim is already running (sim_bridge handles
#           EKF, laser merger/filter, odom relay, TF fixups).
#           Skips Orbbec camera driver; uses Gazebo-bridged camera topics directly.

#################
#### Cleanup ####
#################

cleanup() {
    # Save 2D map while slam_gmapping is still alive
    echo -e "${GREEN}------------------------------------------------${NC}"

    mkdir -p "$MAP_OUT_DIR"

    echo -e "${GREEN}Saving 2D map to $MAP_OUT_DIR...${NC}"
    ros2 launch slam_mapping save_map.launch.py
    sleep 2

    cp $MAP_NAV_DIR/*.pgm "$MAP_OUT_DIR/"
    cp $MAP_NAV_DIR/*.yaml "$MAP_OUT_DIR/"

    echo -e "${GREEN}------------------------------------------------${NC}"
    echo -e "${GREEN}Stopping processes...${NC}"

    # Graceful: SIGINT to each process group
    for pid in "${PIDS[@]}"; do
        kill -INT -- "-$pid" 1>/dev/null
    done
    sleep 3

    # Force-kill any survivors
    for pid in "${PIDS[@]}"; do
        kill -9 -- "-$pid" 1>/dev/null
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

MAP_OUT_DIR="${MAP_VAULT_DIR}/rtab_full_fusion"

#############################
#### Pre-flight cleanup  ####
#############################

echo -e "${YELLOW}Cleaning up any leftover mapper processes from a previous run...${NC}"
pkill -9 -f "rtabmap"                  2>/dev/null || true
pkill -9 -f "rtabmap_ros"              2>/dev/null || true
pkill -9 -f "rviz2"                    2>/dev/null || true
sleep 3

#############################
#### Starting ROS2 Nodes ####
#############################

echo -e "${GREEN}=== Starting RTAB-Map (full fusion) ===${NC}"
echo ""
echo -e "${GREEN}[1/1] Starting RTAB-Map (full fusion: RGBD VO + LiDAR ICP odometry, seeded by EKF wheel+IMU odom)...${NC}"
ros2 launch rtabmap_launch rtabmap.launch.py \
    rgb_topic:=/camera/color/image_raw \
    depth_topic:=/camera/depth/image_raw \
    camera_info_topic:=/camera/color/camera_info \
    scan_topic:=/scan \
    odom_topic:=/odom \
    imu_topic:=/imu/data \
    wait_imu_to_init:=true \
    frame_id:=base_link \
    use_sim_time:=$( [[ "$SIM_MODE" == "true" ]] && echo "true" || echo "false" ) \
    rviz:=true \
    rtabmap_viz:=false \
    approx_sync:=true \
    approx_sync_max_interval:=0.1 \
    qos:=2 \
    visual_odometry:=true \
    icp_odometry:=true \
    subscribe_scan:=true \
    sync_queue_size:=50 \
    topic_queue_size:=50 \
    icp_odometry_args:="--wait_imu_to_init true \
        --Reg/Strategy 1 \
        --Reg/Force3DoF true \
        --Odom/Strategy 0 \
        --Odom/ResetCountdown 1 \
        --Odom/GuessMotion true \
        --Odom/FillInfoData true \
        --OdomF2M/MaxSize 2000 \
        --OdomF2M/BundleAdjustment 0 \
        --Icp/PointToPlane false \
        --Icp/MaxCorrespondenceDistance 0.1 \
        --Icp/Iterations 30 \
        --Icp/VoxelSize 0.05" \
    rtabmap_args:="--delete_db_on_start \
        --Reg/Strategy 3 \
        --Reg/Force3DoF true \
        --Grid/Sensor 0 \
        --Grid/3D false \
        --Grid/RayTracing true \
        --Vis/FeatureType 6 \
        --Vis/MaxFeatures 1000 \
        --RGBD/ProximityBySpace true \
        --RGBD/ProximityMaxGraphDepth 0 \
        --RGBD/AngularUpdate 0.05 \
        --RGBD/LinearUpdate 0.05 \
        --Mem/STMSize 30 \
        --Rtabmap/DetectionRate 1.0" &
PIDS+=($!)

echo -e "${GREEN}Full fusion SLAM running | Press Ctrl+C to save and stop.${NC}"
wait