#!/usr/bin/env bash
#
# environment_setup.sh
#
# One-shot environment bootstrap for the M3Pro digital-twin workspace.
# Target: Ubuntu 22.04 + ROS 2 Humble.
#
# What this does, in order:
#   1. Sanity-checks the OS and that ROS 2 Humble is installed/sourced.
#   2. Runs rosdep against src/ to resolve whatever it can from package.xml.
#   3. Installs a hand-picked list of packages that rosdep WON'T catch,
#      because several package.xml files in this repo under-declare their
#      real runtime dependencies (e.g. slam_mapping and yahboom_mapping
#      declare no <depend> tags at all, despite needing slam_toolbox).
#   4. Optionally installs Python-only deps via pip.
#   5. Runs colcon build.
#
# Usage:
#   chmod +x environment_setup.sh
#   ./environment_setup.sh
#
# Safe to re-run — every step is idempotent.

set -uo pipefail  # NOT -e: we want to report every failure, not die on the first one

# ---------------------------------------------------------------------------
# 0. Config
# ---------------------------------------------------------------------------
ROS_DISTRO_EXPECTED="humble"
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${WORKSPACE_DIR}/src"

FAILED_STEPS=()

log()  { echo -e "\n\033[1;36m==> $*\033[0m"; }
warn() { echo -e "\033[1;33m[WARN] $*\033[0m"; }
err()  { echo -e "\033[1;31m[ERROR] $*\033[0m"; }

# ---------------------------------------------------------------------------
# 1. OS / ROS sanity checks
# ---------------------------------------------------------------------------
log "Checking OS and ROS 2 environment"

if ! grep -q "22.04" /etc/os-release 2>/dev/null; then
    warn "This script targets Ubuntu 22.04. Your /etc/os-release doesn't match — continuing anyway, but expect surprises."
fi

if [ -z "${ROS_DISTRO:-}" ]; then
    if [ -f "/opt/ros/${ROS_DISTRO_EXPECTED}/setup.bash" ]; then
        warn "ROS 2 ${ROS_DISTRO_EXPECTED} is installed but not sourced. Sourcing it for this script now."
        # shellcheck disable=SC1090
        source "/opt/ros/${ROS_DISTRO_EXPECTED}/setup.bash"
    else
        err "ROS 2 ${ROS_DISTRO_EXPECTED} was not found at /opt/ros/${ROS_DISTRO_EXPECTED}."
        err "Install it first: https://docs.ros.org/en/humble/Installation.html"
        exit 1
    fi
elif [ "${ROS_DISTRO}" != "${ROS_DISTRO_EXPECTED}" ]; then
    warn "Detected ROS_DISTRO=${ROS_DISTRO}, but this workspace targets ${ROS_DISTRO_EXPECTED}. Continuing anyway."
fi

if [ ! -d "${SRC_DIR}" ]; then
    err "No src/ directory found at ${SRC_DIR}. Run this script from the workspace root."
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. rosdep — resolve whatever the package.xml files declare correctly
# ---------------------------------------------------------------------------
log "Running rosdep against src/"

if ! command -v rosdep &>/dev/null; then
    warn "rosdep not found — installing it."
    sudo apt-get update -qq && sudo apt-get install -y python3-rosdep
fi

if [ ! -d /etc/ros/rosdep ] || [ -z "$(ls -A /etc/ros/rosdep/sources.list.d/ 2>/dev/null)" ]; then
    sudo rosdep init 2>/dev/null || true
fi
rosdep update

if ! rosdep install --from-paths "${SRC_DIR}" --ignore-src -r -y; then
    warn "rosdep reported some unresolvable keys (expected — several package.xml files here are incomplete). Continuing to the manual fallback list below."
    FAILED_STEPS+=("rosdep install")
fi

# ---------------------------------------------------------------------------
# 3. Manual fallback list
#
#    Now that package.xml files declare their real dependencies correctly
#    (yahboom_M3Pro_description, slam_engine, saved_maps, yahboom_laser_filter
#    were all fixed), rosdep should resolve most of this on its own.
#
#    This list remains necessary mainly for ira_laser_tools, whose
#    package.xml uses non-standard rosdep keys (libpcl-all-dev, libvtk-qt)
#    that don't map to real apt packages — plus a safety net in case
#    rosdep's local database is out of date on a given machine.
# ---------------------------------------------------------------------------
log "Installing known dependencies not covered by package.xml declarations"

APT_PACKAGES=(
    # --- Simulation core (Gazebo Classic + spawning/description) ---
    ros-humble-gazebo-ros-pkgs
    ros-humble-gazebo-ros
    ros-humble-xacro
    ros-humble-robot-state-publisher
    ros-humble-joint-state-publisher
    ros-humble-joint-state-publisher-gui

    # --- SLAM (slam_mapping / yahboom_mapping declare no deps at all) ---
    ros-humble-slam-toolbox

    # --- Navigation (M3Pro_navigation only declares nav2_bringup itself) ---
    ros-humble-navigation2
    ros-humble-nav2-bringup
    ros-humble-nav2-map-server

    # --- Dual-LiDAR merge pipeline (ira_laser_tools uses non-rosdep keys) ---
    libpcl-dev
    ros-humble-pcl-ros
    ros-humble-laser-geometry
    ros-humble-tf2-ros
    libvtk9-qt-dev

    # --- Teleop for manual testing ---
    ros-humble-teleop-twist-keyboard

    # --- Visualization ---
    ros-humble-rviz2
)

sudo apt-get update -qq
for pkg in "${APT_PACKAGES[@]}"; do
    if dpkg -s "${pkg}" &>/dev/null; then
        echo "  [ok] ${pkg} already installed"
    else
        echo "  [installing] ${pkg}"
        if ! sudo apt-get install -y "${pkg}"; then
            err "Failed to install ${pkg} — package name may differ on your distro/architecture."
            FAILED_STEPS+=("apt: ${pkg}")
        fi
    fi
done

# ---------------------------------------------------------------------------
# 4. Python-only dependencies (pip)
#    Add anything here that a pure-python node needs and that apt doesn't
#    package cleanly. Empty by default — fill in as new nodes need it.
# ---------------------------------------------------------------------------
PIP_PACKAGES=(
    # e.g. "numpy"
)

if [ "${#PIP_PACKAGES[@]}" -gt 0 ]; then
    log "Installing Python (pip) dependencies"
    pip3 install --break-system-packages "${PIP_PACKAGES[@]}" \
        || FAILED_STEPS+=("pip install")
fi

# ---------------------------------------------------------------------------
# 5. Build the workspace
# ---------------------------------------------------------------------------
log "Building workspace with colcon"

if ! command -v colcon &>/dev/null; then
    warn "colcon not found — installing it."
    sudo apt-get install -y python3-colcon-common-extensions
fi

cd "${WORKSPACE_DIR}"
if ! colcon build --symlink-install; then
    err "colcon build failed — see output above."
    FAILED_STEPS+=("colcon build")
fi

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
log "Setup summary"

if [ "${#FAILED_STEPS[@]}" -eq 0 ]; then
    echo -e "\033[1;32mAll steps completed successfully.\033[0m"
    echo "Next: source ${WORKSPACE_DIR}/install/setup.bash"
else
    warn "Completed with issues in the following step(s):"
    for step in "${FAILED_STEPS[@]}"; do
        echo "  - ${step}"
    done
    echo "Review the messages above — some may be safe to ignore (e.g. an optional package already satisfied by another route)."
fi