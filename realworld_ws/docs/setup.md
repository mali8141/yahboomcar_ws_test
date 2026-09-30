
# Setup

## Overview

In the following we will describe everything necessary to setup a clean ubuntu install. We assume ubuntu 24.04 and ROS2 Jazzy has already been installed and the WISES repo has been cloned to **home/jetson/**.

For instruction on how to setup a seperate VNC look [here](vnc_setup.md).

## Additional packages

In addition to the usual packages we also require th following. Without them the original yahboom packages won't build correctly.

```sh
sudo apt install ros-jazzy-image-transport ros-jazzy-pcl-ros ros-jazzy-navigation2 ros-jazzy-nav2-bringup python3-vcstool ros-jazzy-cartographer-ros ros-jazzy-joint-state-publisher ros-jazzy-xacro ros-jazzy-rtabmap-ros ros-jazzy-camera-info-manager ros-jazzy-image-transport ros-jazzy-image-publisher ros-jazzy-compressed-image-transport ros-jazzy-image-transport-plugins ros-jazzy-slam-toolbox ros-jazzy-opennav-docking

pip install "empy==3.3.4" catkin_pkg lark-parser lark rosdistro rospkg numpy scipy librosa panns-inference torch torchaudio
```

### Audio analyzer model

The audio analyzer automatically downloads the pretrained PANNs CNN14 model the first time it
runs. To download the model manually from a terminal before starting the analyzer, run:

```sh
python3 -c "from panns_inference import AudioTagging; AudioTagging(checkpoint_path=None, device='cpu'); print('PANNs model downloaded')"
```

Run this command with the same Python environment used by `ros2 run anomaly_detection`. The model
is stored in the PyTorch cache and will not be downloaded again unless the cache is removed.

To get the camera working we also need to install the following:

```sh
cd ~/WISES_Robot/realworld_ws/yahboomcar_ws/src
git clone https://github.com/orbbec/OrbbecSDK_ROS2.git
cd .. && colcon build --symlink-install --packages-up-to orbbec_camera
```

Additionally we need to install the microros agent:

```sh
mkdir -p ~/microROS_agent/src
cd ~/microROS_agent/src
git clone -b jazzy https://github.com/micro-ROS/micro_ros_setup.git
cd ~/microROS_agent
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh
```


## .bashrc changes

Run this to emulate th behavious of the original terminal.

```sh
cat >> ~/.bashrc << 'EOF'

# ROS 2 environment
source /opt/ros/jazzy/setup.bash
source /home/jetson/WISES_Robot/realworld_ws/yahboomcar_ws/install/setup.bash
source /home/jetson/WISES_Robot/realworld_ws/M3Pro_ws/install/setup.bash
source /home/jetson/microROS_agent/install/setup.bash

export ROS_DOMAIN_ID=30
export LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

export MACHINE=OrinNano
export ROBOT_TYPE=ROSMASTER-M3Pro
export CAMERA_TYPE=dabai_dcw2
export RADAR=Tmini-plus*2

# System info display
read -r rows cols < <(stty size)
SystemInfo="System Information"
SystemInfoLength=${#SystemInfo}
half_cols=$((cols / 2))
padding=$((half_cols - SystemInfoLength / 2))
echo -e "\033[2J\033[31m\033[1;${padding}H[${SystemInfo}]\033[0m"
echo "------------------------------------------------------------------------"
echo -e "\033[33mIP_Address_1: $(hostname -I | awk '{print $1}')\033[0m"
echo -e "\033[33mIP_Address_2: $(hostname -I | awk '{print $2}')\033[0m"
echo -e "MACHINE: \033[32m$MACHINE\033[0m           | ROS_DISTRO: \033[32m jazzy \033[0m    | ROS_DOMAIN_ID: \033[32m $ROS_DOMAIN_ID \033[0m "
echo -e "ROBOT_TYPE: \033[32m$ROBOT_TYPE\033[0m | CAMERA_TYPE: \033[32m$CAMERA_TYPE\033[0m | RADAR: \033[32m$RADAR\033[0m"
echo "------------------------------------------------------------------------"
```

Close it with `EOF`

## USB Devices

We also need to setup the usb devices to make sure they are on the correct address.

1. Find the device:
```sh
# List all serial devices currently connected
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
# Look for something like "USB Serial Device" or "ttyUSB0" / "ttyACM0"
```

2. Get its unique identifiers:
```sh
# Replace /dev/ttyUSB0 with whatever you found above
udevadm info -a /dev/ttyUSB0 | grep -E "idVendor|idProduct|serial"
```

3. Create the udev rule:
```sh
# Replace the vendor/product IDs with what you found
sudo bash -c 'cat > /etc/udev/rules.d/99-myserial.rules << EOF
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="02C4EB87", SYMLINK+="myserial", MODE="0666"
EOF'
```

4. Activate it:
```sh
sudo udevadm control --reload-rules
sudo udevadm trigger
```

5. Verify:
```sh
ls -l /dev/myserial
```

The simlink will persist across reboots. For our setup the commands 3 to 5 are already made for our hardware. No need to run 1 and 2.
