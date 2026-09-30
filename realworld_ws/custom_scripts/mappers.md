# Mapper Scripts

Three mapping scripts are provided, each targeting a different sensor configuration. All support a `--sim` flag for use against the `digitaltwin_ws` Gazebo simulation; in that mode `start_core_robot.sh --sim` must already be running (the `sim_bridge` handles EKF, laser merger/filter, and TF).

Maps are saved on `Ctrl+C` via a `cleanup` trap before processes are killed.

---

## `mapper_gmapping.sh`

**Algorithm:** GMapping — Rao-Blackwellized particle filter SLAM  
**Output:** 2D occupancy grid  
**Sensors:** Merged LiDAR (`/scan`) + EKF-fused wheel odometry (`/odom`)

```sh
./mapper_gmapping.sh [--sim]
```

### What it starts

| Component | Real robot | Simulation |
|---|---|---|
| UMA-16 microphone | `ros2 run uma16 stream_publisher` | skipped |
| Sensor bringup (LiDAR merge/filter + EKF) | via `slam_mapping` launch | skipped (sim_bridge handles it) |
| GMapping | `slam_gmapping.launch.py` | `slam_gmapping` node with `use_sim_time:=true` |
| RViz visualizer | `slam_view.launch.py` | same |

### Map save

On `Ctrl+C`, calls `save_map.launch.py` then copies `.pgm` / `.yaml` files to `~/maps/gmapping/`.

---

## `mapper_rtab_visual_only.sh`

**Algorithm:** RTAB-Map with visual odometry only  
**Output:** 2D occupancy grid + 3D point-cloud database (`rtabmap.db`)  
**Sensors:** RGB-D camera only — no LiDAR, no wheel odometry

```sh
./mapper_rtab_visual_only.sh [--sim]
```

### Key RTAB-Map parameters

| Parameter | Value | Effect |
|---|---|---|
| `visual_odometry` | `true` | Pose estimated entirely from RGB-D features |
| `icp_odometry` | `false` | ICP disabled |
| `subscribe_scan` | `false` | LiDAR not used |
| `Vis/FeatureType` | `6` (GFTT/BRIEF) | Fast feature detector for embedded hardware |
| `Vis/MaxFeatures` | `500` | Feature budget per frame |
| `OdomF2M/MaxSize` | `1500` | Frame-to-map feature window |
| `Rtabmap/DetectionRate` | `1.0 Hz` | Loop-closure check rate |
| `Mem/STMSize` | `30` | Short-term memory node limit |
| `approx_sync_max_interval` | `0.1 s` | Timestamp tolerance for RGB+Depth sync |

### What it starts

| Component | Real robot | Simulation |
|---|---|---|
| Orbbec camera driver | `camera_bringup.launch.py` | skipped (Gazebo bridge provides topics) |
| RTAB-Map | `rtabmap.launch.py` (visual-only params) | same with `use_sim_time:=true` |

### Map save

On `Ctrl+C`: saves 2D map with `map_saver_cli` and copies `~/.ros/rtabmap.db` to `~/maps/rtabmap_visual_only/`. Session log is written to `~/maps/rtabmap_visual_only/mapping_<timestamp>.log`.

---

## `mapper_rtab_full_fusion.sh`

**Algorithm:** RTAB-Map with full multi-sensor fusion  
**Output:** 2D occupancy grid + 3D point-cloud database (`rtabmap.db`)  
**Sensors:** RGB-D camera + merged LiDAR (`/scan`) + EKF wheel odometry (`/odom`) + IMU (`/imu/data`)

```sh
./mapper_rtab_full_fusion.sh [--sim]
```

> **Odometry note:** verify with `ros2 topic info /odom --verbose` that `/odom` is the EKF-fused output (wheel + IMU). If your EKF republishes on a different topic (e.g. `/odometry/filtered`), update `odom_topic` in the script accordingly.

### Key RTAB-Map parameters

| Parameter | Value | Effect |
|---|---|---|
| `visual_odometry` | `false` | Uses external EKF odom, not visual odometry |
| `subscribe_scan` | `true` | LiDAR scan fused into occupancy grid |
| `wait_imu_to_init` | `true` | Waits for IMU before starting |
| `Reg/Strategy` | `3` (Visual+ICP) | Loop closure uses both appearance and geometry |
| `Reg/Force3DoF` | `true` | Constrains correction to the ground plane |
| `Grid/Sensor` | `0` (LiDAR) | Occupancy grid built from LiDAR, not depth camera |
| `Grid/RayTracing` | `true` | Clears free space in the occupancy grid |
| `RGBD/LinearUpdate` | `0.05 m` | Minimum travel before adding a new node |
| `RGBD/AngularUpdate` | `0.05 rad` | Minimum rotation before adding a new node |
| `RGBD/ProximityBySpace` | `true` | Enables space-proximity loop closure |
| `Icp/MaxCorrespondenceDistance` | `0.1 m` | ICP match radius |
| `Icp/VoxelSize` | `0.05 m` | Voxel downsample for ICP |
| `approx_sync_max_interval` | `0.1 s` | Timestamp tolerance for multi-topic sync |
| `sync_queue_size` / `topic_queue_size` | `50` | Queue depth for multi-sensor sync |

### What it starts

| Component | Real robot | Simulation |
|---|---|---|
| Sensors (camera + LiDAR + EKF) | `rtab_bringup.launch.py` | skipped (sim_bridge handles it) |
| RTAB-Map | `rtabmap.launch.py` (full-fusion params) | same with `use_sim_time:=true` |

### Map save

On `Ctrl+C`: saves 2D map with `map_saver_cli` and copies `~/.ros/rtabmap.db` to `~/maps/rtabmap_full_fusion/`. Session log is written to `~/maps/rtabmap_full_fusion/mapping_<timestamp>.log`.

---

## Comparison

| | `mapper_gmapping.sh` | `mapper_rtab_visual_only.sh` | `mapper_rtab_full_fusion.sh` |
|---|---|---|---|
| Algorithm | GMapping (particle filter) | RTAB-Map | RTAB-Map |
| Map type | 2D only | 2D + 3D | 2D + 3D |
| Odometry source | Wheel (EKF) | Visual | Wheel (EKF) + IMU |
| LiDAR used | Yes | No | Yes |
| RGB-D camera used | No | Yes | Yes |
| IMU used | No | No | Yes (init gate) |
| Best for | Fast 2D nav maps, no camera | Camera-only hardware | Most accurate; full sensor suite |
| Map output path | `~/maps/gmapping/` | `~/maps/rtabmap_visual_only/` | `~/maps/rtabmap_full_fusion/` |
