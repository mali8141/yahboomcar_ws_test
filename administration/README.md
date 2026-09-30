# Administration frontend

The frontend loads the live occupancy grid from `GET /map`, polls robot state
from `GET /get_status` (with `GET /status` retained as an alias), and submits
clicked targets to `POST /commands`.

The **Map library** tab lists valid map folders from the robot's `~/maps`
directory and applies the selected entry with `PUT /set_map`. A map folder must
contain a map YAML file (`.yaml` or `.yml`) with `image`, `resolution`, and
`origin` fields, plus the referenced image and any other map assets. The robot
accepts only these advertised map IDs; the browser cannot provide arbitrary
filesystem paths.

Each map can be opened in the patrol-path editor. The editor reads and writes
the map's `route.json` through `GET /routes/<map_id>` and
`PUT /routes/<map_id>`. Waypoints are stored as `{ "pose": { "x", "y", "yaw" } }`
objects and are followed in their displayed order.
Routes may also contain an independent `regions` array of map-space bounding
boxes: `{ "id", "min_x", "min_y", "max_x", "max_y" }`. These regions are
not tied to waypoints. During patrol the robot logs a message when it enters
one of these regions. Legacy waypoint-level regions are promoted when read.

Install the frontend dependencies and run it locally:

```bash
cd administration
npm install
npm run dev
```

Open <http://127.0.0.1:8000>, enter the patrol-brain address (by default
`http://127.0.0.1:8080`), then click the map to select a target. Enter the
desired yaw and select **Send navigation target**.

The patrol brain allows this frontend origin by default. If the frontend is
hosted elsewhere, configure the patrol brain's `cors_allowed_origins` ROS
parameter with that origin. The API is unauthenticated, so use it only on a
trusted network.

The app is a Vite/React project. Create a deployable static build with
`npm run build`; the output is written to `dist/`.
