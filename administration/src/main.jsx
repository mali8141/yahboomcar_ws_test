import { StrictMode, useCallback, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const DEFAULT_API = 'http://127.0.0.1:8080';
const apiBase = () =>
  (localStorage.getItem('wises-api-url') || DEFAULT_API).replace(/\/$/, '');

async function request(path, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status})`);
  }

  return payload;
}

function MapCanvas({ map, robot, goal, yaw, route, machines, heatmapPoints, onSelect, drawingRect, onDrawStart, onDrawMove, onDrawEnd, interactive = false }) {
  const ref = useRef(null);
  const viewportRef = useRef(null);
  const dragRef = useRef(null);
  const suppressClickRef = useRef(false);
  const [viewport, setViewport] = useState({ width: 0, height: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const mapWidthM = map ? map.info.width * map.info.resolution : 0;
  const mapHeightM = map ? map.info.height * map.info.resolution : 0;
  const basePixelsPerMeter = viewport.width && viewport.height && mapWidthM && mapHeightM
    ? Math.min((viewport.width - 32) / mapWidthM, (viewport.height - 32) / mapHeightM)
    : 1;
  const canvasStyle = map ? {
    width: `${mapWidthM * basePixelsPerMeter * zoom}px`,
    height: `${mapHeightM * basePixelsPerMeter * zoom}px`,
    transform: `translate(calc(-50% + ${pan.x}px), calc(-50% + ${pan.y}px))`,
  } : undefined;

  useEffect(() => {
    if (!viewportRef.current) return undefined;
    const updateViewport = () => {
      const box = viewportRef.current.getBoundingClientRect();
      setViewport({ width: box.width, height: box.height });
    };
    updateViewport();
    const observer = new ResizeObserver(updateViewport);
    observer.observe(viewportRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [map]);

  useEffect(() => {
    if (!map || !ref.current) return;
    const canvas = ref.current;
    const ctx = canvas.getContext('2d');
    const { width, height, resolution, origin } = map.info;
    canvas.width = width;
    canvas.height = height;
    const image = ctx.createImageData(width, height);
    for (let row = 0; row < height; row += 1) {
      for (let col = 0; col < width; col += 1) {
        const value = map.data[row * width + col];
        const shade =
          value < 0 ? 178 : 255 - Math.round(Math.min(value, 100) * 2.55);
        const pixel = ((height - row - 1) * width + col) * 4;
        image.data[pixel] = shade;
        image.data[pixel + 1] = shade;
        image.data[pixel + 2] = shade;
        image.data[pixel + 3] = 255;
      }
    }
    ctx.putImageData(image, 0, 0);
    (heatmapPoints || []).forEach((point) => {
      const x = (point.x - origin.position.x) / resolution;
      const y = height - (point.y - origin.position.y) / resolution;
      const probability = Math.max(0, Math.min(1, Number(point.probability) || 0));
      const red = Math.round(34 + probability * 186);
      const green = Math.round(197 - probability * 161);
      ctx.fillStyle = `rgb(${red}, ${green}, 60)`;
      ctx.beginPath();
      ctx.arc(x, y, Math.max(7, width / 55), 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#991b1b';
      ctx.lineWidth = 1;
      ctx.stroke();
    });
    const marker = (point, color, angle, size) => {
      const x = (point.x - origin.position.x) / resolution;
      const y = height - (point.y - origin.position.y) / resolution;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(-angle);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(size, 0);
      ctx.lineTo(-size, size * 0.65);
      ctx.lineTo(-size, -size * 0.65);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    };
    if (robot) marker(robot, '#155eef', robot.yaw, 8);
    if (goal) marker(goal, '#f79009', Number(yaw) || 0, 7);
    if (route?.waypoints?.length) {
      ctx.strokeStyle = '#15803d';
      ctx.lineWidth = Math.max(2, width / 300);
      ctx.beginPath();
      route.waypoints.forEach((waypoint, index) => {
        const x = (waypoint.pose.x - origin.position.x) / resolution;
        const y = height - (waypoint.pose.y - origin.position.y) / resolution;
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
      route.waypoints.forEach((waypoint, index) => {
        const x = (waypoint.pose.x - origin.position.x) / resolution;
        const y = height - (waypoint.pose.y - origin.position.y) / resolution;
        ctx.fillStyle = '#15803d';
        ctx.beginPath();
        ctx.arc(x, y, Math.max(4, width / 180), 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.font = `${Math.max(10, width / 70)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(index + 1), x, y);
      });
      (route.regions || []).forEach((region) => {
        ctx.strokeStyle = '#b42318';
        ctx.fillStyle = '#b4231826';
        const left = (region.min_x - origin.position.x) / resolution;
        const top = height - (region.max_y - origin.position.y) / resolution;
        const regionWidth = (region.max_x - region.min_x) / resolution;
        const regionHeight = (region.max_y - region.min_y) / resolution;
        ctx.fillRect(left, top, regionWidth, regionHeight);
        ctx.strokeRect(left, top, regionWidth, regionHeight);
      });
    }
    (machines || route?.machines || []).forEach((machine, index) => {
      const x = (machine.x - origin.position.x) / resolution;
      const y = height - (machine.y - origin.position.y) / resolution;
      ctx.fillStyle = '#7c3aed';
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, Math.max(7, width / 130), 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.font = `${Math.max(10, width / 75)}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(index + 1), x, y);
    });
    if (drawingRect) {
      const left = (drawingRect.min_x - origin.position.x) / resolution;
      const top = height - (drawingRect.max_y - origin.position.y) / resolution;
      ctx.strokeStyle = '#b42318';
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(left, top,
        (drawingRect.max_x - drawingRect.min_x) / resolution,
        (drawingRect.max_y - drawingRect.min_y) / resolution);
      ctx.setLineDash([]);
    }
  }, [map, robot, goal, yaw, route, machines, heatmapPoints, drawingRect]);

  const pointFromEvent = (event) => {
    const box = ref.current.getBoundingClientRect();
    const x = (event.clientX - box.left) * ref.current.width / box.width;
    const y = (event.clientY - box.top) * ref.current.height / box.height;
    return {
      x: map.info.origin.position.x + x * map.info.resolution,
      y: map.info.origin.position.y + (map.info.height - y) * map.info.resolution,
    };
  };
  const click = (event) => {
    if (!map || !ref.current) return;
    if (suppressClickRef.current) {
      suppressClickRef.current = false;
      return;
    }
    onSelect?.(pointFromEvent(event));
  };
  const changeZoom = (nextZoom, event) => {
    const boundedZoom = Math.max(0.5, Math.min(8, nextZoom));
    if (event && ref.current) {
      const box = ref.current.getBoundingClientRect();
      const offset = {
        x: event.clientX - (box.left + box.width / 2),
        y: event.clientY - (box.top + box.height / 2),
      };
      setPan((current) => ({
        x: current.x + offset.x * (1 - boundedZoom / zoom),
        y: current.y + offset.y * (1 - boundedZoom / zoom),
      }));
    }
    setZoom(boundedZoom);
  };
  const pointerDown = (event) => {
    suppressClickRef.current = false;
    if (!interactive || event.button !== 0 || onDrawStart) return;
    dragRef.current = { x: event.clientX, y: event.clientY, moved: false };
    ref.current.setPointerCapture(event.pointerId);
  };
  const pointerMove = (event) => {
    const drag = dragRef.current;
    if (drag) {
      const deltaX = event.clientX - drag.x;
      const deltaY = event.clientY - drag.y;
      if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) drag.moved = true;
      setPan((current) => ({ x: current.x + deltaX, y: current.y + deltaY }));
      drag.x = event.clientX;
      drag.y = event.clientY;
      return;
    }
    onDrawMove?.(pointFromEvent(event));
  };
  const pointerUp = (event) => {
    if (dragRef.current) {
      suppressClickRef.current = dragRef.current.moved;
      dragRef.current = null;
      ref.current.releasePointerCapture(event.pointerId);
      return;
    }
    onDrawEnd?.(pointFromEvent(event));
  };
  const wheel = (event) => {
    if (!interactive) return;
    event.preventDefault();
    changeZoom(zoom * (event.deltaY < 0 ? 1.15 : 1 / 1.15), event);
  };

  return <div ref={viewportRef} className="map-canvas-shell" onWheel={wheel}>
    {interactive && <div className="map-controls" aria-label="Map controls">
      <button type="button" onClick={() => changeZoom(zoom * 1.25)} aria-label="Zoom in">+</button>
      <button type="button" onClick={() => changeZoom(zoom / 1.25)} aria-label="Zoom out">−</button>
      <button type="button" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} aria-label="Reset map view">Reset</button>
    </div>}
    <canvas ref={ref} style={canvasStyle} onClick={click} onPointerDown={(event) => {
      pointerDown(event);
      if (!dragRef.current) onDrawStart?.(pointFromEvent(event));
    }} onPointerMove={pointerMove} onPointerUp={pointerUp}
      aria-label="Navigation map" />
  </div>;
}

function Navigation({ map, mapError, status, goal, setGoal, route }) {
  const [yaw, setYaw] = useState('0');
  const [message, setMessage] = useState('');
  const [chargeMessage, setChargeMessage] = useState('');
  const [patrolMessage, setPatrolMessage] = useState('');
  const send = async (event) => {
    event.preventDefault(); setMessage('Sending target…');
    try {
      await request('/commands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: 'manual_goal',
          x: Number(goal.x),
          y: Number(goal.y),
          yaw: Number(yaw),
          frame_id: map?.header?.frame_id || 'map',
        }),
      });
      setMessage('Navigation target submitted.');
    } catch (error) {
      setMessage(`Target was not sent: ${error.message}`);
    }
  };
  const returnToCharger = async () => {
    setChargeMessage('Returning to charging station…');
    try {
      await request('/commands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'change_mode', mode: 'charging' }),
      });
      setChargeMessage('Robot is returning to the charging station.');
    } catch (error) {
      setChargeMessage(`Command failed: ${error.message}`);
    }
  };
  const startPatrol = async () => {
    setPatrolMessage('Starting patrol route…');
    try {
      await request('/commands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'start_patrol' }),
      });
      setPatrolMessage('Patrol route started.');
    } catch (error) {
      setPatrolMessage(`Command failed: ${error.message}`);
    }
  };
  return (
    <div className="navigation-layout">
      <section className="panel map-panel">
        <div className="panel-heading">
          <div>
            <h2>Current navigation map</h2>
            <p>
              {map
                ? `${map.info.width} × ${map.info.height} cells · ${map.info.resolution} m/cell · ${map.header.frame_id}`
                : mapError || 'Loading map…'}
            </p>
          </div>
        </div>
        <div className="map-viewport">
          {map ? (
            <MapCanvas
              map={map}
              robot={status.position}
              goal={goal}
              yaw={yaw}
              route={route}
              onSelect={setGoal}
              interactive
            />
          ) : (
            <p>{mapError || 'Loading map…'}</p>
          )}
        </div>
        <p className="help">
          Click the map to choose a target. Blue is the robot, orange is the
          selected target, green is the patrol route, and red outlines are
          regions of interest.
        </p>
      </section>

      <section className="panel card">
        <h2>Manual navigation target</h2>
        <form onSubmit={send}>
          <label>
            X (m)
            <input
              type="number"
              step="any"
              value={goal?.x ?? ''}
              onChange={(event) =>
                setGoal({ ...goal, x: Number(event.target.value) })
              }
              required
            />
          </label>
          <label>
            Y (m)
            <input
              type="number"
              step="any"
              value={goal?.y ?? ''}
              onChange={(event) =>
                setGoal({ ...goal, y: Number(event.target.value) })
              }
              required
            />
          </label>
          <label>
            Yaw (rad)
            <input
              type="number"
              step="any"
              value={yaw}
              onChange={(event) => setYaw(event.target.value)}
              required
            />
          </label>
          <button type="submit">Send navigation target</button>
        </form>
        <p className="message">{message}</p>
      </section>

      <section className="panel card">
        <h2>Robot status</h2>
        <dl>
          <dt>Mode</dt>
          <dd>{status.mode || '—'}</dd>
          <dt>Action</dt>
          <dd>{status.action || '—'}</dd>
          <dt>Navigation</dt>
          <dd>{status.navigation_status || '—'}</dd>
          <dt>Position</dt>
          <dd>
            {status.position
              ? `${status.position.x.toFixed(2)}, ${status.position.y.toFixed(2)} m`
              : status.position_error || 'Unavailable'}
          </dd>
          <dt>Map</dt>
          <dd>{status.map_id || '—'}</dd>
          {status.patrol?.route_id != null && (
            <>
              <dt>Patrol route</dt>
              <dd>{status.patrol.route_id}</dd>
              <dt>Waypoint</dt>
              <dd>{status.patrol.waypoint_index + 1} / {status.patrol.total_waypoints}</dd>
              {status.patrol.active_task && (
                <>
                  <dt>Active task</dt>
                  <dd>{status.patrol.active_task.type}</dd>
                </>
              )}
            </>
          )}
          <dt>Battery</dt>
          <dd>
            {status.battery != null ? (
              <>
                {status.battery.percentage.toFixed(1)}% &nbsp;·&nbsp; {status.battery.voltage.toFixed(2)} V
                <div className="battery-bar-wrap">
                  <div
                    className={
                      'battery-bar ' +
                      (status.battery.percentage > 50
                        ? 'high'
                        : status.battery.percentage > 20
                        ? 'medium'
                        : 'low')
                    }
                    style={{ width: `${status.battery.percentage}%` }}
                  />
                </div>
              </>
            ) : '—'}
          </dd>
        </dl>
        <button
          type="button"
          className="patrol-btn"
          onClick={startPatrol}
          disabled={status.action === 'patrol'}
        >
          {status.action === 'patrol' ? 'Patrol in progress…' : 'Run patrol route'}
        </button>
        <p className="message">{patrolMessage}</p>
        <button
          type="button"
          className="charge-btn"
          onClick={returnToCharger}
        >
          Return to charging station
        </button>
        <p className="message">{chargeMessage}</p>
      </section>
    </div>
  );
}

function RouteEditor({ map, selectedMap, route, setRoute, close, save }) {
  const [message, setMessage] = useState('');
  const [drawingRegion, setDrawingRegion] = useState(false);
  const [drawingStart, setDrawingStart] = useState(null);
  const [drawingRect, setDrawingRect] = useState(null);
  const [movingIndex, setMovingIndex] = useState(null);
  const [placingWaypoint, setPlacingWaypoint] = useState(false);
  const [placingMachine, setPlacingMachine] = useState(false);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') { setMovingIndex(null); setPlacingWaypoint(false); setDrawingRegion(false); setPlacingMachine(false); } };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const addOrMoveWaypoint = (point) => {
    if (placingMachine) {
      const machineNumber = (route.machines || []).length + 1;
      setRoute((cur) => ({
        ...cur,
        machines: [...(cur.machines || []), {
          id: `machine-${Date.now()}`,
          name: `Machine ${machineNumber}`,
          x: point.x,
          y: point.y,
        }],
      }));
      setPlacingMachine(false);
      return;
    }
    if (movingIndex !== null) {
      setRoute((cur) => ({
        ...cur,
        waypoints: cur.waypoints.map((wp, i) =>
          i === movingIndex ? { ...wp, pose: { ...wp.pose, ...point } } : wp,
        ),
      }));
      setMovingIndex(null);
      return;
    }
    if (!placingWaypoint) return;
    setRoute((cur) => ({
      ...cur,
      waypoints: [...cur.waypoints, {
        id: `waypoint-${cur.waypoints.length + 1}`,
        pose: { ...point, yaw: 0 },
      }],
    }));
    setPlacingWaypoint(false);
  };

  const updateYaw = (index, value) => {
    setRoute((cur) => ({
      ...cur,
      waypoints: cur.waypoints.map((wp, i) =>
        i === index ? { ...wp, pose: { ...wp.pose, yaw: Number(value) } } : wp,
      ),
    }));
  };

  const updateIgnoreRegions = (index, value) => {
    setRoute((cur) => ({
      ...cur,
      waypoints: cur.waypoints.map((wp, i) =>
        i === index ? { ...wp, ignore_regions: value } : wp,
      ),
    }));
  };

  const updateSampleAudio = (index, value) => {
    setRoute((cur) => ({
      ...cur,
      waypoints: cur.waypoints.map((wp, i) =>
        i === index ? { ...wp, sample_audio: value } : wp,
      ),
    }));
  };

  const remove = (index) => {
    if (movingIndex === index) setMovingIndex(null);
    setRoute((cur) => ({
      ...cur,
      waypoints: cur.waypoints.filter((_, i) => i !== index),
    }));
  };

  const moveUp = (index) => {
    if (index === 0) return;
    setRoute((cur) => {
      const wps = [...cur.waypoints];
      [wps[index - 1], wps[index]] = [wps[index], wps[index - 1]];
      return { ...cur, waypoints: wps };
    });
    setMovingIndex((prev) => (prev === index ? index - 1 : prev === index - 1 ? index : prev));
  };

  const moveDown = (index) => {
    setRoute((cur) => {
      if (index >= cur.waypoints.length - 1) return cur;
      const wps = [...cur.waypoints];
      [wps[index], wps[index + 1]] = [wps[index + 1], wps[index]];
      return { ...cur, waypoints: wps };
    });
    setMovingIndex((prev) =>
      route.waypoints.length - 1 > index
        ? prev === index ? index + 1 : prev === index + 1 ? index : prev
        : prev,
    );
  };

  const finishRegion = (end) => {
    if (!drawingRegion || !drawingStart) return;
    const region = {
      id: `region-${Date.now()}`,
      min_x: Math.min(drawingStart.x, end.x),
      min_y: Math.min(drawingStart.y, end.y),
      max_x: Math.max(drawingStart.x, end.x),
      max_y: Math.max(drawingStart.y, end.y),
    };
    if (region.max_x - region.min_x > 0.05 && region.max_y - region.min_y > 0.05) {
      setRoute((cur) => ({ ...cur, regions: [...(cur.regions || []), region] }));
    }
    setDrawingStart(null);
    setDrawingRect(null);
  };

  const removeRegion = (regionIndex) => setRoute((cur) => ({
    ...cur,
    regions: (cur.regions || []).filter((_, i) => i !== regionIndex),
  }));

  const updateMachine = (index, value) => setRoute((cur) => ({
    ...cur,
    machines: (cur.machines || []).map((machine, machineIndex) =>
      machineIndex === index ? { ...machine, name: value } : machine),
  }));

  const removeMachine = (index) => setRoute((cur) => ({
    ...cur,
    machines: (cur.machines || []).filter((_, machineIndex) => machineIndex !== index),
  }));

  const submit = async () => {
    setMessage('Saving patrol path…');
    try {
      await save(route);
      setMessage('Patrol path saved.');
    } catch (error) {
      setMessage(`Could not save path: ${error.message}`);
    }
  };

  const mapCursor = movingIndex !== null || placingWaypoint || placingMachine ? 'crosshair-move' : drawingRegion ? 'crosshair' : undefined;

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) close();
    }}>
      <section className="route-editor" role="dialog" aria-modal="true" aria-labelledby="route-editor-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Patrol path</p>
            <h2 id="route-editor-title">Edit {selectedMap.name}</h2>
          </div>
          <button type="button" className="secondary-btn" onClick={close}>Close</button>
        </div>
        <div className="editor-layout">
          {/* ── Left: map ── */}
          <div className="editor-map-col">
            <div className="map-viewport editor-map" style={mapCursor ? { cursor: mapCursor } : undefined}>
              <MapCanvas map={map} route={route} onSelect={drawingRegion ? undefined : addOrMoveWaypoint} interactive
                drawingRect={drawingRect}
                onDrawStart={drawingRegion ? (point) => {
                  setDrawingStart(point);
                  setDrawingRect({ ...point, min_x: point.x, min_y: point.y, max_x: point.x, max_y: point.y });
                } : undefined}
                onDrawMove={drawingStart ? (point) => setDrawingRect({
                  min_x: Math.min(drawingStart.x, point.x), min_y: Math.min(drawingStart.y, point.y),
                  max_x: Math.max(drawingStart.x, point.x), max_y: Math.max(drawingStart.y, point.y),
                }) : undefined}
                onDrawEnd={finishRegion} />
            </div>
            <p className="help">
              {movingIndex !== null
                ? `Click the map to place waypoint ${movingIndex + 1}. Press Escape to cancel.`
                : placingWaypoint ? 'Click the map to place a waypoint. Drag to pan.'
                : placingMachine ? 'Click the map to place a machine.' : 'Select a map tool to add a waypoint, place a machine, or draw an ROI.'}
            </p>
          </div>

          {/* ── Right: waypoint list panel ── */}
          <div className="waypoint-panel">
            <div className="waypoint-panel-header">
              <h3>{route.waypoints.length} waypoint{route.waypoints.length !== 1 ? 's' : ''}</h3>
              <button
                type="button"
                className={`secondary-btn roi-toggle-btn${placingWaypoint ? ' roi-active' : ''}`}
                onClick={() => {
                  setPlacingWaypoint(!placingWaypoint);
                  setMovingIndex(null);
                  setDrawingRegion(false);
                  setPlacingMachine(false);
                  setDrawingStart(null);
                  setDrawingRect(null);
                }}
              >
                {placingWaypoint ? 'Cancel waypoint' : 'Add waypoint'}
              </button>
              <button
                type="button"
                className={`secondary-btn roi-toggle-btn${drawingRegion ? ' roi-active' : ''}`}
                onClick={() => {
                  setDrawingRegion(!drawingRegion);
                  setDrawingStart(null);
                  setDrawingRect(null);
                  setMovingIndex(null);
                  setPlacingWaypoint(false);
                  setPlacingMachine(false);
                }}
              >
                {drawingRegion ? 'Cancel ROI' : 'Draw ROI'}
              </button>
              <button
                type="button"
                className={`secondary-btn roi-toggle-btn${placingMachine ? ' roi-active' : ''}`}
                onClick={() => { setPlacingMachine(!placingMachine); setDrawingRegion(false); setDrawingStart(null); setDrawingRect(null); setMovingIndex(null); setPlacingWaypoint(false); }}
              >
                {placingMachine ? 'Cancel machine' : 'Place machine'}
              </button>
            </div>

            <div className="waypoint-scroll">
              {route.waypoints.map((waypoint, index) => (
                <div
                  className={`waypoint-row${movingIndex === index ? ' waypoint-moving' : ''}`}
                  key={waypoint.id || index}
                >
                  <div className="waypoint-reorder">
                    <button
                      type="button"
                      className="icon-btn"
                      title="Move up"
                      disabled={index === 0}
                      onClick={() => moveUp(index)}
                    >▲</button>
                    <button
                      type="button"
                      className="icon-btn"
                      title="Move down"
                      disabled={index === route.waypoints.length - 1}
                      onClick={() => moveDown(index)}
                    >▼</button>
                  </div>
                  <div className="waypoint-body">
                    <div className="waypoint-coords">
                      <span className="waypoint-index">{index + 1}</span>
                      <span className="waypoint-pos">{waypoint.pose.x.toFixed(2)}, {waypoint.pose.y.toFixed(2)} m</span>
                      <div className="waypoint-actions">
                        <button
                          type="button"
                          className={`icon-btn relocate-btn${movingIndex === index ? ' relocate-active' : ''}`}
                          title="Move on map"
                          onClick={() => setMovingIndex(movingIndex === index ? null : index)}
                        >⊕</button>
                        <button
                          type="button"
                          className="icon-btn danger-icon-btn"
                          title="Remove waypoint"
                          onClick={() => remove(index)}
                        >×</button>
                      </div>
                    </div>
                    <label className="yaw-label">
                      Yaw (rad)
                      <input type="number" step="any" value={waypoint.pose.yaw}
                        onChange={(event) => updateYaw(index, event.target.value)} />
                    </label>
                    <label className="ignore-regions-label">
                      <input
                        type="checkbox"
                        checked={waypoint.ignore_regions === true}
                        onChange={(event) => updateIgnoreRegions(index, event.target.checked)}
                      />
                      Ignore ROIs until reaching this waypoint
                    </label>
                    <label className="sample-audio-label">
                      <input
                        type="checkbox"
                        checked={waypoint.sample_audio === true}
                        onChange={(event) => updateSampleAudio(index, event.target.checked)}
                      />
                      Record audio at this waypoint
                    </label>
                  </div>
                </div>
              ))}

              {(route.regions || []).length > 0 && (
                <div className="regions-section">
                  <p className="regions-heading">Regions of interest</p>
                  {(route.regions || []).map((region, regionIndex) => (
                    <div className="region-row" key={region.id || regionIndex}>
                      <div className="region-info">
                        <span>ROI {regionIndex + 1}</span>
                        <span className="region-coords">
                          ({region.min_x.toFixed(2)}, {region.min_y.toFixed(2)}) → ({region.max_x.toFixed(2)}, {region.max_y.toFixed(2)})
                        </span>
                      </div>
                      <button
                        type="button"
                        className="icon-btn danger-icon-btn"
                        title="Remove ROI"
                        onClick={() => removeRegion(regionIndex)}
                      >×</button>
                    </div>
                  ))}
                </div>
              )}
              {(route.machines || []).length > 0 && (
                <div className="regions-section">
                  <p className="regions-heading">Machines</p>
                  {(route.machines || []).map((machine, machineIndex) => (
                    <div className="region-row" key={machine.id || machineIndex}>
                      <div className="region-info">
                        <input value={machine.name || ''} aria-label={`Machine ${machineIndex + 1} name`}
                          onChange={(event) => updateMachine(machineIndex, event.target.value)} />
                        <span className="region-coords">({machine.x.toFixed(2)}, {machine.y.toFixed(2)})</span>
                      </div>
                      <button type="button" className="icon-btn danger-icon-btn" title="Remove machine"
                        onClick={() => removeMachine(machineIndex)}>×</button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="waypoint-panel-footer">
              <button type="button" onClick={submit} disabled={!route.waypoints.length}>
                Save patrol path
              </button>
              <p className="message">{message}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function MapLibrary({ maps, current, mapData, refresh, apply, loadRoute, saveRoute }) {
  const [message, setMessage] = useState('');
  const [editing, setEditing] = useState(null);
  const select = async (map) => {
    setMessage(`Loading ${map.name} into Nav2…`);
    try {
      await apply(map);
      setMessage(
        `${map.name} is active. Set the robot localization pose before navigating.`,
      );
    } catch (error) {
      setMessage(`Map was not applied: ${error.message}`);
    }
  };
  const edit = async (selectedMap) => {
    setMessage(`Opening ${selectedMap.name}…`);
    try {
      if (selectedMap.id !== current) await apply(selectedMap);
      const result = await loadRoute(selectedMap.id);
      setEditing({ map: selectedMap, route: result.route });
      setMessage('');
    } catch (error) {
      setMessage(`Could not open map editor: ${error.message}`);
    }
  };

  return (
    <section className="panel library">
      <div className="panel-heading">
        <div>
          <h2>Available maps</h2>
          <p>Map folders advertised by the robot.</p>
        </div>
        <button type="button" onClick={refresh}>
          Refresh maps
        </button>
      </div>
      <div className="map-list">
        {maps.length === 0 && <p>No valid map folders were advertised.</p>}
        {maps.map((map) => (
          <article
            className={`map-entry ${map.id === current ? 'current' : ''}`}
            key={map.id}
          >
            <h3>{map.name}</h3>
            {map.id === current && <div className="map-thumbnail"><MapCanvas map={mapData} /></div>}
            {map.id !== current && <div className="map-thumbnail unavailable">Apply map to preview</div>}
            <p>{map.id === current ? 'Currently active' : 'Ready to load'}</p>
            <p>{map.waypoint_count ? `${map.waypoint_count} patrol waypoints` : 'No patrol path yet'}</p>
            <button type="button" className="secondary-btn" onClick={() => edit(map)}>Edit patrol path</button>
            <button
              type="button"
              onClick={() => select(map)}
            >
              {map.id === current ? 'Reload active map' : 'Apply this map'}
            </button>
          </article>
        ))}
      </div>
      <p className="message">{message}</p>
      {editing && (
        <RouteEditor
          map={mapData}
          selectedMap={editing.map}
          route={editing.route}
          setRoute={(update) => setEditing((currentEditing) => ({
            ...currentEditing, route: typeof update === 'function' ? update(currentEditing.route) : update,
          }))}
          close={() => setEditing(null)}
          save={async (route) => { await saveRoute(editing.map.id, route); await refresh(); }}
        />
      )}
    </section>
  );
}

function PatrolHistory({ map, currentMap, route, refresh }) {
  const [runs, setRuns] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const loadRuns = async () => {
    try {
      const result = await request('/patrol-runs');
      setRuns(result.runs || []);
      if (!selectedId && result.runs?.length) setSelectedId(result.runs[0].id);
      setError('');
    } catch (loadError) { setError(loadError.message); }
  };
  useEffect(() => { loadRuns(); }, []);
  useEffect(() => {
    const run = runs.find((item) => item.id === selectedId);
    if (!run) { setSelected(null); return; }
    request(`/patrol-runs/${encodeURIComponent(run.map_id)}/${encodeURIComponent(run.id)}`)
      .then((result) => setSelected(result.run))
      .catch((loadError) => setError(loadError.message));
  }, [runs, selectedId]);
  const matchingMap = selected?.map_id === currentMap;
  return (
    <section className="panel patrol-history">
      <div className="panel-heading">
        <div><h2>Patrol history</h2><p>Saved audio locations and failure probability by run.</p></div>
        <button type="button" onClick={() => { refresh(); loadRuns(); }}>Refresh runs</button>
      </div>
      <div className="history-layout">
        <div className="run-list">
          {runs.length === 0 && <p>No completed patrol runs have been saved.</p>}
          {runs.map((run) => (
            <button type="button" className={`run-entry${run.id === selectedId ? ' selected' : ''}`} key={`${run.map_id}-${run.id}`} onClick={() => setSelectedId(run.id)}>
              <strong>{run.id}</strong><span>{run.map_id} · {run.point_count || run.recording_count || 0} audio recordings</span>
            </button>
          ))}
        </div>
        <div>
          {selected && matchingMap ? (
            <>
              <div className="map-viewport history-map"><MapCanvas map={map} route={route} machines={selected.machines} heatmapPoints={selected.points} /></div>
              <p className="help">Red intensity indicates the saved failure probability at each audio location.</p>
              <div className="machine-results">
                {(selected.machines || []).map((machine) => (
                  <div className="machine-result" key={machine.id}>
                    <strong>{machine.name}</strong>
                    <span>{machine.failure_probability == null ? 'No samples' : `${(machine.failure_probability * 100).toFixed(1)}% failure probability`}</span>
                    <small>{machine.sample_count} nearest sample{machine.sample_count === 1 ? '' : 's'}</small>
                  </div>
                ))}
              </div>
            </>
          ) : selected ? (
            <p className="message">Load map <strong>{selected.map_id}</strong> to view this run on its map. The run and its recordings are preserved.</p>
          ) : <p className="message">Select a patrol run to inspect its audio map.</p>}
        </div>
      </div>
      {error && <p className="message">Could not load patrol history: {error}</p>}
    </section>
  );
}

function App() {
  const [apiUrl, setApiUrl] = useState(apiBase());
  const [tab, setTab] = useState('navigation');
  const [map, setMap] = useState(null);
  const [mapError, setMapError] = useState('');
  const [maps, setMaps] = useState([]);
  const [status, setStatus] = useState({});
  const [patrolRoute, setPatrolRoute] = useState(null);
  const [goal, setGoal] = useState(null);
  const [connection, setConnection] = useState('Connecting…');
  const connect = useCallback(async () => {
    localStorage.setItem('wises-api-url', apiUrl.replace(/\/$/, ''));
    try {
      const [mapData, statusData, mapsData] = await Promise.all([
        request('/map'),
        request('/get_status'),
        request('/maps'),
      ]);
      setMap(mapData);
      setStatus(statusData);
      setMaps(mapsData.maps || []);
      if (statusData.map_id) {
        try {
          setPatrolRoute((await request(
            `/routes/${encodeURIComponent(statusData.map_id)}`,
          )).route);
        } catch {
          setPatrolRoute(null);
        }
      } else {
        setPatrolRoute(null);
      }
      setMapError('');
      setConnection('Connected');
    } catch (error) {
      setConnection(`Disconnected: ${error.message}`);
      setMapError(error.message);
    }
  }, [apiUrl]);
  useEffect(() => {
    if (!status.map_id) {
      setPatrolRoute(null);
      return;
    }
    let cancelled = false;
    request(`/routes/${encodeURIComponent(status.map_id)}`)
      .then((result) => {
        if (!cancelled) setPatrolRoute(result.route);
      })
      .catch(() => {
        if (!cancelled) setPatrolRoute(null);
      });
    return () => { cancelled = true; };
  }, [status.map_id]);
  useEffect(() => {
    connect();
    const timer = setInterval(async () => {
      try {
        setStatus(await request('/get_status'));
        setConnection('Connected');
      } catch (error) {
        setConnection(`Disconnected: ${error.message}`);
      }
    }, 2000);

    return () => clearInterval(timer);
  }, [connect]);

  const refreshMaps = async () => {
    const result = await request('/maps');
    setMaps(result.maps || []);
  };

  const applyMap = async (selected) => {
    await request('/set_map', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ map_id: selected.id }),
    });
    await connect();
  };
  const loadRoute = (mapId) => request(`/routes/${encodeURIComponent(mapId)}`);
  const saveRoute = async (mapId, route) => {
    await request(`/routes/${encodeURIComponent(mapId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ route }),
    });
    if (mapId === status.map_id) setPatrolRoute(route);
  };

  return (
    <>
      <header>
        <div>
          <p className="eyebrow">WISES Robot</p>
          <h1>Admin console</h1>
        </div>
        <form
          className="connection-form"
          onSubmit={(event) => {
            event.preventDefault();
            connect();
          }}
        >
          <label>
            Robot API
            <input
              type="url"
              value={apiUrl}
              onChange={(event) => setApiUrl(event.target.value)}
              required
            />
          </label>
          <button type="submit">Connect</button>
        </form>
      </header>

      <nav className="tabs">
        <button
          className={tab === 'navigation' ? 'active' : ''}
          onClick={() => setTab('navigation')}
        >
          Navigation
        </button>
        <button
          className={tab === 'maps' ? 'active' : ''}
          onClick={() => setTab('maps')}
        >
          Map library
        </button>
        <button
          className={tab === 'history' ? 'active' : ''}
          onClick={() => setTab('history')}
        >
          Patrol history
        </button>
      </nav>

      <main>
        {tab === 'navigation' ? (
          <Navigation
            map={map}
            mapError={mapError}
            status={status}
            goal={goal}
            setGoal={setGoal}
            route={patrolRoute}
          />
        ) : tab === 'maps' ? (
          <MapLibrary
            maps={maps}
            current={status.map_id}
            mapData={map}
            refresh={refreshMaps}
            apply={applyMap}
            loadRoute={loadRoute}
            saveRoute={saveRoute}
          />
        ) : (
          <PatrolHistory map={map} currentMap={status.map_id} route={patrolRoute} refresh={connect} />
        )}
      </main>

      <footer>API: {connection}</footer>
    </>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
