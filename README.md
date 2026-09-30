# WISES_Robot

The base robot is a Yahboom ROSMASTER M3Pro mecanum-drive mobile base with a 5-DOF arm, dual LiDAR, RGB-D camera and IMU. The original stack has been migrated to run ROS 2 Jazzy on a Jetson Orin Nano onboard computer.

Additional sensor have been added to the robot, including a UMA-16 microphone array and a custom audio-map package. The 5-DOF arm has been remove to make space for these new sensors.

---

## Further docs

| Goal | Start here |
|---|---|
| First-time setup on the robot | [`setup.md`](realworld_ws/docs/setup.md) |
| Run the Gazebo simulation | [`digitaltwin_ws/README.md`](digitaltwin_ws/README.md) |
| Start the robot and run SLAM | [`realworld_ws/custom_scripts/README.md`](realworld_ws/custom_scripts/README.md) |
| UMA-16 microphone array | [`realworld_ws/custom_Sensors_ws/src/uma16/README.md`](realworld_ws/custom_Sensors_ws/src/uma16/README.md) |
| `realworld_ws` package inventory | [`realworld_ws/Readme.md`](realworld_ws/docs/Readme.md) |
