# Sensor Module Node

## General idea

`sensor_publisher` (package `sensor_module`) polls a microcontroller over a serial connection at a fixed rate and republishes whatever it reads as a JSON string on a ROS 2 topic.

Each tick it writes `read\n` to the serial port and waits (up to 0.8s) for a response line starting with `>`, formatted as comma-separated `key:value` pairs, e.g.:

```
>temp_c:21.4,humidity:38.0,pressure_pa:101325.0
```

That line is parsed into a dict and published as JSON on `/sensor_module/data` (default topic). If the serial port can't be opened, `pyserial` isn't installed, the MCU doesn't respond in time, or the line can't be parsed, the node publishes a default fallback payload (`{"temp_c": 0.0, "humidity": 0.0, "pressure_pa": 0.0}`) instead of crashing — so a missing/disconnected sensor board degrades gracefully rather than taking the rest of the sensor suite down with it.

```
SensorModule MCU (serial, "read" / ">key:val,..." protocol)
        │
        ▼
  sensor_publisher ──► /sensor_module/data (std_msgs/String, JSON payload)
```

---

## Dependencies

```bash
pip3 install --user pyserial
```

If pip refuses with an "externally-managed-environment" error:
```bash
pip3 install --break-system-packages pyserial
```

ROS 2 packages required (included in a standard ROS 2 install): `rclpy`, `std_msgs`.

If `pyserial` is missing entirely, the node still starts and runs — it just logs a warning once and publishes the fallback payload forever.

---

## Build

```bash
cd ros2_ws
colcon build --packages-select sensor_module
source install/setup.bash
```

---

## Running

Directly:
```bash
ros2 run sensor_module sensor_publisher
```

Via the launch file (lets you override parameters as launch arguments):
```bash
ros2 launch sensor_module sensor_module.launch.py port:=/dev/ttyUSB0 baud:=9600 rate_hz:=10.0
```

Via the wrapper script: `./scripts/run_sensor_module_publisher.sh` (see [scripts.md](scripts.md)).

Or as part of the full suite via `./scripts/run_sensor_suit.sh`.

---

## Parameters

Pass parameters with `--ros-args -p name:=value`, or as launch arguments if using the launch file.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `port` | `/dev/ttyUSB0` | Serial device path of the MCU. |
| `baud` | `9600` | Serial baud rate. Must match the MCU's firmware configuration. |
| `topic` | `/sensor_module/data` | ROS 2 topic to publish JSON payloads on. |
| `rate_hz` | `10.0` | Polling rate in Hz — how often the node writes `read` and waits for a response. |

---

## Key parameters explained

- **`port`** must point at the actual MCU, not just any USB-serial adapter. On boards with more than one USB-serial device (e.g. a robot chassis controller and a separate sensor board), the kernel's `/dev/ttyUSB*` numbering is enumeration-order-dependent and can silently swap after a reboot or replug. Prefer a stable path instead of a raw `/dev/ttyUSBn`:
  ```bash
  ls -la /dev/serial/by-id/
  ```
  This lists one persistent symlink per physical device (keyed by USB vendor/product/serial), which you can pass as `port` instead of `/dev/ttyUSB0`. If your system has a udev rule assigning a friendly symlink (e.g. `/dev/myserial`, `/dev/mic`), that works too — check `/etc/udev/rules.d/` for existing rules on your board.
- **`baud`** has no effect on whether the port can be *opened* — a wrong baud rate opens successfully but yields garbage or no parsable `>...` lines, which the node then reports as fallback data rather than an error. If you're only ever seeing the fallback payload, check this before suspecting a hardware fault.
- **`rate_hz`** trades responsiveness for serial bus load; each tick blocks up to 0.8s waiting for a reply, so setting `rate_hz` faster than the MCU can actually respond just means every tick times out and publishes the fallback payload.

---

## Topics

| Topic | Message type | Direction |
|-------|-------------|-----------|
| `/sensor_module/data` (configurable via `topic`) | `std_msgs/msg/String` | output — JSON-encoded dict of whatever keys the MCU reports |

---

## Troubleshooting

**`Cannot open <port>: ...; publishing default values`:** The port doesn't exist, is already held open by another process, or you lack permission. Check:
```bash
ls -la /dev/ttyUSB*
fuser -v /dev/ttyUSB0
groups $USER   # should include 'dialout'
```

**`Serial error: device reports readiness to read but returned no data (device disconnected or multiple access on port?)`:** Something else already has the serial port open — commonly another ROS node or a vendor-provided bridge (e.g. a chassis controller's micro-ROS agent) pointed at the same physical device. Only one process can own a serial port at a time; find the other owner with `fuser -v <port>` or `lsof <port>` and stop it, or point `sensor_publisher` at a different port using a stable `/dev/serial/by-id/...` path as described above.

**Only ever getting the fallback payload `{"temp_c": 0.0, ...}`:** Either `pyserial` isn't installed, the port/baud is wrong, or the MCU firmware isn't replying to `read\n` with a `>key:val,...` line within 0.8s.
