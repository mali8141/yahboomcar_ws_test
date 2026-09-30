#!/bin/bash
# run_navigation_pipeline.sh
# Launches Gazebo + robot, the dual-lidar scan merger, Nav2 (AMCL +
# planner + controller), and RViz2 in one command, and cleanly kills
# everything on Ctrl+C.
#
# NOTE: Nav2 will come up localized but idle. You still need to set the
# initial pose manually in RViz2 ("2D Pose Estimate") before AMCL will
# publish the map->odom transform - that step can't be automated from
# here since it depends on where the robot actually is in Gazebo.

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

################################
#### Script specific Config ####
################################

MAP_PATH="$(ros2 pkg prefix saved_maps)/share/saved_maps/maps/map_maze.yaml"
NAV2_LOG="/tmp/nav2_$(date +%s).log"

#############################
#### Pre-flight cleanup  ####
#############################

# Kill any stale processes left over from a previous run that didn't shut
# down cleanly (e.g. terminal closed directly instead of Ctrl+C).
echo -e "${YELLOW}Cleaning up any leftover processes from a previous run...${NC}"
pkill -9 -f "gz sim" 2>/dev/null || true
pkill -9 -f "laserscan_multi_merger" 2>/dev/null || true
pkill -9 -f "component_container_isolated" 2>/dev/null || true   # nav2_container (amcl, costmaps, planner, controller, etc.)
pkill -9 -f "rviz2" 2>/dev/null || true
pkill -9 -f "ros_gz" 2>/dev/null || true
pkill -9 -f "robot_state_publisher" 2>/dev/null || true
pkill -9 -f "slam_toolbox" 2>/dev/null || true
sleep 1

#################
#### Cleanup ####
#################

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all nodes...${NC}"
    for pid in "${PIDS[@]}"; do
        # negative pid kills the whole process group (setsid gave each its own)
        kill -TERM "-$pid" 2>/dev/null || true
    done

    # gz sim and Nav2's composed-node container can survive the group kill
    # above, so force them directly as a safety net.
    sleep 1
    pkill -9 -f "gz sim" 2>/dev/null || true
    pkill -9 -f "laserscan_multi_merger" 2>/dev/null || true
    pkill -9 -f "component_container_isolated" 2>/dev/null || true
    pkill -9 -f "rviz2" 2>/dev/null || true
    pkill -9 -f "ros_gz" 2>/dev/null || true
    pkill -9 -f "robot_state_publisher" 2>/dev/null || true
    pkill -9 -f "slam_toolbox" 2>/dev/null || true

    wait 2>/dev/null || true
    echo -e "${GREEN}Done.${NC}"
}
trap cleanup SIGINT SIGTERM SIGHUP EXIT

# Resolve the map path up front; fail fast with a clear message if the
# saved_maps package isn't built yet, instead of failing deep inside Nav2.
if [ ! -f "$MAP_PATH" ]; then
    echo -e "${RED}ERROR: map file not found at $MAP_PATH${NC}"
    echo -e "${YELLOW}Build the workspace first: colcon build --packages-select saved_maps${NC}"
    exit 1
fi

##############################
#### Starting ROS2 Nodes  ####
##############################

echo -e "${GREEN}=== Starting Navigation Pipeline ===${NC}"
echo ""

echo -e "${GREEN}[1/4] Starting Gazebo + robot + maze...${NC}"
setsid ros2 launch yahboom_M3Pro_description gazebo_display.launch.py &
PIDS+=($!)
sleep 8   # give Gazebo time to spawn the robot before the merger looks for /scan0,/scan1

echo -e "${GREEN}[2/4] Starting lidar scan merger...${NC}"
setsid ros2 run ira_laser_tools laserscan_multi_merger --ros-args --params-file \
    "$DIGITALTWIN_WS/install/ira_laser_tools/share/ira_laser_tools/config/laserscan_merge.yaml" &
PIDS+=($!)
sleep 3

echo -e "${GREEN}[3/4] Starting Nav2 (AMCL localization + planner + controller)...${NC}"
setsid bash -c "ros2 launch M3Pro_navigation localization_bringup_launch.py \
    use_sim_time:=true \
    map:='$MAP_PATH' 2>&1 | tee '$NAV2_LOG'" &
PIDS+=($!)
sleep 8

echo -e "${GREEN}[4/4] Starting RViz2...${NC}"
setsid ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true &
PIDS+=($!)

echo -e "${GREEN}Press Ctrl+C in this terminal to stop everything.${NC}"
wait
