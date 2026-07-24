#!/bin/bash
# run_lidar_pipeline.sh
# Launches the full Gazebo + dual-lidar merge + SLAM + RViz2 pipeline
# in one command, and cleanly kills everything on Ctrl+C.

set -e

# --- adjust these two paths if your workspaces live elsewhere ---
YAHBOOM_WS=~/yahboomcar_ws_test/yahboomcar_ws
M3PRO_WS=~/yahboomcar_ws_test/M3Pro_ws

source /opt/ros/humble/setup.bash
source "$YAHBOOM_WS/install/setup.bash"
source "$M3PRO_WS/install/setup.bash"

PIDS=()

# Pre-flight: kill any stale processes left over from a previous run that
# didn't shut down cleanly (e.g. terminal closed directly instead of Ctrl+C).
echo "Cleaning up any leftover processes from a previous run..."
killall -9 gzserver gzclient 2>/dev/null || true
pkill -9 -f "laserscan_multi_merger" 2>/dev/null || true
pkill -9 -f "slam_toolbox" 2>/dev/null || true
pkill -9 -f "rviz2" 2>/dev/null || true
pkill -9 -f "spawn_entity.py" 2>/dev/null || true
pkill -9 -f "robot_state_publisher" 2>/dev/null || true
sleep 1

cleanup() {
    echo ""
    echo "Shutting down all nodes..."
    for pid in "${PIDS[@]}"; do
        # negative pid kills the whole process group (setsid gave each its own)
        kill -TERM "-$pid" 2>/dev/null || true
    done

    # Gazebo Classic's gzserver/gzclient fork into their own session and
    # routinely survive the group kill above, so force them (and any other
    # lingering pipeline nodes) directly as a safety net.
    sleep 1
    killall -9 gzserver gzclient 2>/dev/null || true
    pkill -9 -f "laserscan_multi_merger" 2>/dev/null || true
    pkill -9 -f "slam_toolbox" 2>/dev/null || true
    pkill -9 -f "rviz2" 2>/dev/null || true
    pkill -9 -f "spawn_entity.py" 2>/dev/null || true
    pkill -9 -f "robot_state_publisher" 2>/dev/null || true

    wait 2>/dev/null || true
    echo "Done."
}
trap cleanup SIGINT SIGTERM SIGHUP EXIT

echo "[1/4] Starting Gazebo + robot + maze..."
setsid ros2 launch yahboom_M3Pro_description gazebo_display.launch.py &
PIDS+=($!)
sleep 8   # give Gazebo time to spawn the robot before the merger looks for /scan0,/scan1

echo "[2/4] Starting lidar scan merger..."
setsid ros2 run ira_laser_tools laserscan_multi_merger --ros-args --params-file "$M3PRO_WS/install/ira_laser_tools/share/ira_laser_tools/config/laserscan_merge.yaml" &
PIDS+=($!)
sleep 3

echo "[3/4] Starting SLAM (slam_toolbox)..."
setsid ros2 launch slam_mapping online_async_launch.py use_sim_time:=true &
PIDS+=($!)
sleep 3

echo "[4/4] Starting RViz2..."
setsid ros2 launch slam_mapping slam_view.launch.py use_sim_time:=true &
PIDS+=($!)

echo ""
echo "All nodes started. Press Ctrl+C in this terminal to stop everything."
wait