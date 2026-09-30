# Patrol brain

`patrol_brain` exposes a local HTTP API for reading the robot pose and sending
manual Nav2 `NavigateToPose` goals. Start the Nav2 stack first, then build and
run the node:

```bash
cd ~/ubuntu_vm/WISES_Robot/realworld_ws/patrol_ws
colcon build --packages-select patrol_brain
source install/setup.bash
ros2 run patrol_brain patrol_brain
```

The API listens on `http://127.0.0.1:8080` by default. It requires Nav2's
`navigate_to_pose` action server and a valid `map` to `base_footprint` TF
transform. To expose it on a trusted network, override the host explicitly:

```bash
ros2 run patrol_brain patrol_brain --ros-args -p host:=0.0.0.0
```

This API is unauthenticated; do not expose it outside a trusted network.

## Terminal API

### Send a manual navigation goal

`x` and `y` are metres in the selected coordinate frame. `yaw` is radians and
defaults to `0`; `frame_id` defaults to `map`.

```bash
curl --fail-with-body -X POST http://127.0.0.1:8080/commands \
  -H 'Content-Type: application/json' \
  --data '{"command":"manual_goal","x":1.25,"y":-0.50,"yaw":1.5708,"frame_id":"map"}'
```

The endpoint returns HTTP `202` once the goal has been handed to Nav2. It
returns `503` if Nav2's action server is not ready.

### Check navigation state

```bash
curl --fail-with-body http://127.0.0.1:8080/get_status
```

The response includes `navigation_status` (`idle`, `submitting`, `executing`,
`succeeded`, `canceled`, `aborted`, or `rejected`), the `active_goal`, and the
latest pose when localization is available.

`GET /status` is retained as an alias for `GET /get_status`.

### Get the current pose

```bash
curl --fail-with-body http://127.0.0.1:8080/position
```

A `503` response means the required TF transform is not available yet.

### Get Nav2's current map

```bash
curl --fail-with-body http://127.0.0.1:8080/map
```

The response is the occupancy grid currently returned by Nav2's
`map_server/map` service: metadata in `info` plus row-major cell values in
`data` (`-1` unknown, `0` free, `100` occupied). A `503` response means the
map server is not available. If your Nav2 map service uses another name, start
the node with `--ros-args -p map_service:=<service-name>`.

### List and load advertised maps

Map folders are discovered directly beneath `~/maps` by default. Each folder
must contain a valid map YAML (`.yaml` or `.yml`) with `image`, `resolution`,
and `origin` fields.

```bash
curl --fail-with-body http://127.0.0.1:8080/maps

curl --fail-with-body -X PUT http://127.0.0.1:8080/set_map \
  -H 'Content-Type: application/json' \
  --data '{"map_id":"office"}'
```

`set_map` accepts only an ID returned by `/maps`; it does not accept arbitrary
paths. It loads the chosen map through Nav2's `map_server/load_map` service.
After a map change, provide a new localization initial pose before sending a
navigation goal. Set a different map root or service name when starting the
node with `-p maps_root:=/path/to/maps` or `-p map_load_service:=name`.

### Change mode

```bash
curl --fail-with-body -X POST http://127.0.0.1:8080/commands \
  -H 'Content-Type: application/json' \
  --data '{"command":"change_mode","mode":"manual"}'
```

Supported modes are `auto`, `idle`, `manual`, `patrol`, and `charging`.
Manual goals automatically switch the brain to `manual` mode. Goals are
rejected while in `patrol` or `charging` mode.

`start_patrol` currently changes the mode only; it does not yet execute a
patrol route.
