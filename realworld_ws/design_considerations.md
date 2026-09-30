# Design Considerations

For the physical tobot design and useage we assume the following:

## Sensors

**RGBD-Camera**:  single forward facing camera with a color and depth video feed. These publish to the topics: */camera/* (TODO check th actual topics agan)

**IMU**:

**Weel Odom**:

**2d Lidar**: Two lidars mounted to the front right and left back. these publish to the topics /scan0 and /scan1 repectifly and are combined into a singl lidar topic publishing to /scan

**Microphone**

## Movement

We assume the robot nly ever maps or navigates on a flat plane. As such we can use 2d navigation algorithms. The robot is assumed to be able to move forward, backward, and rotate in place ass well as drive in an arc.

## Sound mapping

We assume sound data is gathered from a single high qulity microphone.

## Chargin docke

We assume the charging docker is a induction charger allowing the robot to charge without physical contack as long as it is within a certain distance of the docker. The docker is assumed to be placed in a location that is easily accessible to the robot.