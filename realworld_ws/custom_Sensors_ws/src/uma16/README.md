# UMA-16 Nodes

## General idea

The UMA-16 is a 16-channel USB microphone array. Audio capture and recording and processing are split across multiple interchangeable pieces:

- **`stream_publisher`**: opens the UMA-16 via `sounddevice`/PortAudio and continuously streams all 16 channels as ROS 2 messages on the `uma16/audio` topic.
- **`stream_recorder`**: subscribes to `uma16/audio` and writes the incoming audio to a 16-channel WAV file on disk.
- **`acoustic_overlay`**: subscribes to `uma16/audio` and runs the beamforming heatmap algorithm, publishing the result on `/beamforming_heatmap` for visualization or further processing. For more details, see [acoustic_overlay.md](acoustic_overlay.md).
- **`standalone_recorder`**: reads the UMA-16 directly and writes a WAV file, with no ROS topic in between. Same result as the publisher+recorder pair, but as a single process with no other node able to consume the audio. Can not be run at the same time as `stream_publisher` because both try to open the hardware directly.

Use the publisher/recorder pair when something else also needs the live audio (e.g. `acoustic_overlay`, see [acoustic_overlay.md](acoustic_overlay.md)). Use the standalone recorder when you only need a WAV file.

```
UMA-16 microphone array
        │
        ▼
 stream_publisher  ──► uma16/audio (ROS 2 topic)
                                    │
                                    ├──► stream_recorder  ──► recording.wav
                                    │
                                    └──► acoustic_overlay (beamforming heatmap)

           -- or, without ROS in between --

 standalone_recorder  ──► recording.wav
```

---

## Dependencies


```sh
pip install "numpy>=1.26,<2" "scipy>=1.11,<1.14" acoular sounddevice
```

---

## Build

Only needed after editing Python source, not after changing parameters.

```bash
cd ros2_ws/src
colcon build
source install/setup.bash
```

---

## Running

### `stream_publisher`

```bash
ros2 run stream_publisher stream_publisher
```

Or via the wrapper script: `./scripts/run_uma16_publisher.sh` (see [scripts.md](scripts.md)).

On startup it also tries to suspend the PulseAudio source for the UMA-16 (`pactl suspend-source ...`) so it can open the hardware directly without conflicting with the desktop sound server. This is best-effort — if `pactl` isn't available or the suspend fails, it logs at debug level and continues anyway.

### `stream_recorder`

```bash
ros2 run stream_recorder stream_recorder
```

Requires `stream_publisher` to already be running and publishing on `uma16/audio`. Stop with **Ctrl+C** — the node drains its write queue and closes the WAV file cleanly before exiting.

### `standalone_recorder` (standalone)

```bash
ros2 run standalone_recorder standalone_recorder
```

Opens the UMA-16 directly; no publisher needed.

### Everything at once

`./scripts/run_sensor_suit.sh --record` starts the audio publisher, the acoustic overlay, and (because of `--record`) the topic recorder together. See [scripts.md](scripts.md).

---

## Parameters

Pass parameters with `--ros-args -p name:=value`. Multiple parameters can be chained:
```bash
ros2 run <package> <node> --ros-args -p param1:=value1 -p param2:=value2
```

### `stream_publisher`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `device_index` | `0` | sounddevice/PortAudio device index to open. Takes priority over `device` whenever it is `>= 0`. Set to `-1` to fall back to the `device` parameter instead. |
| `device` | `'UMA16v2'` | Device name (or numeric string) used when `device_index` is `-1`. Matched against PortAudio device names. |
| `samplerate` | `48000` | Sample rate in Hz. Must match the UMA-16's native rate and every downstream node (`stream_recorder`, `acoustic_overlay`). |
| `channels` | `16` | Number of input channels to capture. |
| `chunk_size` | `8192` | Number of audio frames per published message (the PortAudio block size). Must match `chunk_size` on `acoustic_overlay` — see [Key parameters explained](#key-parameters-explained) below. |
| `suspend_pulse` | `true` | If true, runs `pactl suspend-source` on the UMA-16's PulseAudio source before opening it directly. Set `false` if you don't use PulseAudio or want to manage this yourself. |

Example — select a specific device index and a smaller chunk size for lower latency:
```bash
ros2 run stream_publisher stream_publisher \
  --ros-args -p device_index:=2 -p chunk_size:=2048
```

Find your device index with:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

### `stream_recorder`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `samplerate` | `48000` | Must match the publisher's sample rate. |
| `channels` | `16` | Must match the publisher's channel count. |
| `filename` | `''` | Full path for the output WAV file. If empty, a timestamped filename (`uma16_recording_YYYYMMDD_HHMMSS.wav`) is generated in the current working directory. |

Example — write to a specific file:
```bash
ros2 run stream_recorder stream_recorder \
  --ros-args -p filename:='/home/kuhnhero/recordings/session1.wav'
```

### `standalone_recorder` (standalone_recorder)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `device` | `''` | sounddevice device index or name. Empty uses the system default input device. |
| `samplerate` | `48000` | Sample rate in Hz. |
| `channels` | `16` | Number of channels to record. |
| `filename` | `''` | Same auto-generated-filename behaviour as `uma16_topic_recorder`. |

---

## Key parameters explained

These values only work correctly when kept consistent across nodes — mismatches are a common source of garbled or silent recordings.

- **`samplerate` and `channels`** must be identical on every node in the chain (`stream_publisher` → `stream_recorder` and/or `acoustic_overlay`). The publisher opens the hardware with these values baked into the audio message layout; a subscriber with a different value will reshape the incoming buffer incorrectly.
- **`chunk_size`** (audio publisher) is the number of audio frames per ROS message, i.e. the PortAudio callback block size. Smaller values reduce latency but increase message-publishing overhead and CPU usage; larger values are more efficient but delay every downstream consumer by that many frames. `acoustic_overlay` has its own `chunk_size` parameter that must be set to the **same** value. It slices/pads each incoming message to that length before running beamforming.
- **`device_index` vs. `device`**: prefer `device_index` when you know the exact PortAudio index (fastest, no name matching). Use `device` (name substring) when the index might shift between reboots/USB replugs.

---

## Topics

| Topic | Message type | Direction |
|-------|-------------|-----------|
| `uma16/audio` | `std_msgs/msg/Float32MultiArray` | publisher → recorder / acoustic overlay / any other subscriber |

Each message carries one audio chunk (`chunk_size` frames × `channels` channels). The layout dimensions encode the shape:
- `layout.dim[0]` — number of frames in this chunk
- `layout.dim[1]` — number of channels

---

## Troubleshooting

**`Failed to open audio device`:** Another process already has the UMA-16 open (commonly PulseAudio/PipeWire, or a previous crashed node instance). Check with:

```bash
lsof /dev/snd/* 2>/dev/null
pactl list short sources | grep -i uma16
```

Setting `suspend_pulse:=true` (the default) usually resolves this by asking PulseAudio to release the device first.

**Recording is silent or garbled:** Check that `samplerate` and `channels` match on every node in the chain, and that `chunk_size` matches between `stream_publisher` and `acoustic_overlay` if both are running.

**Wrong device selected after a reboot/replug:** PortAudio device indices are not stable across enumeration changes. Prefer `-p device:='UMA16v2'` (name match) over a hardcoded `device_index` if this happens often.
