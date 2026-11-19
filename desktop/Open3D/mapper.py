"""
lidar_mapper.py
===============
Point cloud mapper for a single-beam LiDAR mounted on a two-servo (pan/tilt) gimbal.

Input  : (pan_deg, tilt_deg, distance_m) measurements, from any source
Output : an Open3D point cloud, plus a live non-blocking viewer

Coordinate convention (right-handed, sensor frame, origin = pan/tilt axis intersection)
    +X : forward  (pan = 0, tilt = 0)
    +Y : left     (pan = +90)
    +Z : up       (tilt = +90)
    pan  = azimuth about +Z, counter-clockwise positive
    tilt = elevation above the XY plane, positive upward

    x = d * cos(tilt) * cos(pan)
    y = d * cos(tilt) * sin(pan)
    z = d * sin(tilt)

Swapping in real hardware later: write any iterable/generator that yields `Measurement`
objects (e.g. parsing a serial stream) and hand it to `LiveViewer.run(...)` or loop over it
calling `mapper.add(...)`. Nothing else needs to change.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional, Tuple

import numpy as np
import open3d as o3d


# --------------------------------------------------------------------------- data types
@dataclass(frozen=True)
class Measurement:
    """One LiDAR return plus the servo angles at the time it was taken."""
    pan_deg: float
    tilt_deg: float
    distance_m: float
    timestamp: float = 0.0


@dataclass
class SensorConfig:
    """Mechanical / sensor calibration."""
    min_range_m: float = 0.05
    max_range_m: float = 12.0
    # Added to commanded servo angles (calibrates servo zero position)
    pan_offset_deg: float = 0.0
    tilt_offset_deg: float = 0.0
    # Flip direction if a servo is mounted so positive command moves the wrong way
    pan_invert: bool = False
    tilt_invert: bool = False
    # LiDAR optical origin relative to the pan/tilt axis intersection, expressed in the
    # tilt-servo frame (x along beam, y left, z up). Leave at 0 for an ideal point gimbal.
    lidar_offset_m: Tuple[float, float, float] = (0.0, 0.0, 0.0)


# --------------------------------------------------------------------------- colormap
_GRADIENT = np.array(
    [
        [0.10, 0.20, 0.90],  # blue
        [0.00, 0.80, 0.90],  # cyan
        [0.10, 0.85, 0.20],  # green
        [0.95, 0.90, 0.10],  # yellow
        [0.95, 0.15, 0.10],  # red
    ]
)


def colorize(values: np.ndarray, vmin: Optional[float] = None, vmax: Optional[float] = None) -> np.ndarray:
    """Map scalar values to RGB (N,3) via a blue->red gradient."""
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return np.zeros((0, 3))
    vmin = float(values.min()) if vmin is None else vmin
    vmax = float(values.max()) if vmax is None else vmax
    span = max(vmax - vmin, 1e-9)
    t = np.clip((values - vmin) / span, 0.0, 1.0) * (len(_GRADIENT) - 1)
    lo = np.floor(t).astype(int)
    hi = np.minimum(lo + 1, len(_GRADIENT) - 1)
    frac = (t - lo)[:, None]
    return _GRADIENT[lo] * (1 - frac) + _GRADIENT[hi] * frac


# --------------------------------------------------------------------------- mapper
class PointCloudMapper:
    """Accumulates measurements into a growing point cloud. Thread-safe."""

    def __init__(self, config: Optional[SensorConfig] = None, capacity: int = 100_000):
        self.cfg = config or SensorConfig()
        self._pts = np.empty((capacity, 3), dtype=np.float64)
        self._dist = np.empty(capacity, dtype=np.float64)
        self._n = 0
        self._lock = threading.Lock()
        self.accepted = 0
        self.rejected = 0
        self.last_point: Optional[np.ndarray] = None

    # ---- geometry
    def polar_to_xyz(self, pan_deg, tilt_deg, dist_m) -> np.ndarray:
        """Vectorised servo angles + range -> XYZ in the sensor frame. Returns (N,3)."""
        cfg = self.cfg
        pan = np.asarray(pan_deg, dtype=float)
        tilt = np.asarray(tilt_deg, dtype=float)
        d = np.asarray(dist_m, dtype=float)

        az = np.radians((-pan if cfg.pan_invert else pan) + cfg.pan_offset_deg)
        el = np.radians((-tilt if cfg.tilt_invert else tilt) + cfg.tilt_offset_deg)
        ox, oy, oz = cfg.lidar_offset_m

        # Point in tilt-servo frame: beam hit plus mounting offset
        x = d + ox
        y = np.full_like(d, oy)
        z = np.full_like(d, oz)

        # Tilt: rotate about Y so positive tilt raises the beam
        ce, se = np.cos(el), np.sin(el)
        xp = ce * x - se * z
        zp = se * x + ce * z
        # Pan: rotate about Z
        ca, sa = np.cos(az), np.sin(az)
        X = ca * xp - sa * y
        Y = sa * xp + ca * y
        return np.stack([X, Y, zp], axis=-1)

    # ---- ingestion
    def add(self, m: Measurement) -> bool:
        return self.add_batch([m.pan_deg], [m.tilt_deg], [m.distance_m]) == 1

    def add_batch(self, pan_deg, tilt_deg, dist_m) -> int:
        """Add many measurements. Out-of-range / NaN returns are dropped. Returns #accepted."""
        pan = np.atleast_1d(np.asarray(pan_deg, dtype=float))
        tilt = np.atleast_1d(np.asarray(tilt_deg, dtype=float))
        dist = np.atleast_1d(np.asarray(dist_m, dtype=float))

        valid = np.isfinite(dist) & (dist >= self.cfg.min_range_m) & (dist <= self.cfg.max_range_m)
        n_ok = int(valid.sum())
        with self._lock:
            self.rejected += int(valid.size - n_ok)
        if n_ok == 0:
            return 0

        xyz = self.polar_to_xyz(pan[valid], tilt[valid], dist[valid])
        with self._lock:
            need = self._n + n_ok
            if need > len(self._pts):
                new_cap = max(need, 2 * len(self._pts))
                self._pts = np.resize(self._pts, (new_cap, 3))
                self._dist = np.resize(self._dist, new_cap)
            self._pts[self._n:need] = xyz
            self._dist[self._n:need] = dist[valid]
            self._n = need
            self.accepted += n_ok
            self.last_point = xyz[-1].copy()
        return n_ok

    # ---- access
    @property
    def num_points(self) -> int:
        return self._n

    def snapshot(self) -> Tuple[np.ndarray, np.ndarray]:
        """Thread-safe copy of (points (N,3), distances (N,))."""
        with self._lock:
            return self._pts[: self._n].copy(), self._dist[: self._n].copy()

    def clear(self) -> None:
        with self._lock:
            self._n = 0
            self.accepted = self.rejected = 0
            self.last_point = None

    def to_open3d(self, color_by: str = "height", voxel_size: Optional[float] = None) -> o3d.geometry.PointCloud:
        """Build an Open3D cloud. color_by: 'height' | 'distance' | 'none'."""
        pts, dist = self.snapshot()
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        if len(pts) and color_by != "none":
            scalar = pts[:, 2] if color_by == "height" else dist
            pcd.colors = o3d.utility.Vector3dVector(colorize(scalar))
        if voxel_size:
            pcd = pcd.voxel_down_sample(voxel_size)
        return pcd

    def save(self, path: str, color_by: str = "height") -> None:
        """Write the cloud to disk (.ply / .pcd / .xyz...)."""
        o3d.io.write_point_cloud(path, self.to_open3d(color_by))


# --------------------------------------------------------------------------- live viewer
class LiveViewer:
    """
    Non-blocking Open3D window that redraws as the mapper fills up.

    A background thread drains the measurement source into the mapper while the main
    thread (required by most GUI backends) runs the render loop.
    """

    def __init__(
        self,
        mapper: PointCloudMapper,
        title: str = "LiDAR Pan/Tilt Mapper",
        width: int = 1280,
        height: int = 800,
        point_size: float = 3.0,
        color_by: str = "height",
        fps: float = 30.0,
        show_beam: bool = True,
    ):
        self.mapper = mapper
        self.title, self.width, self.height = title, width, height
        self.point_size = point_size
        self.color_by = color_by
        self.fps = fps
        self.show_beam = show_beam
        self.stop = threading.Event()
        self.source_done = threading.Event()

    def _pump(self, source: Iterable[Measurement]) -> None:
        try:
            for m in source:
                if self.stop.is_set():
                    break
                self.mapper.add(m)
        finally:
            self.source_done.set()

    def run(self, source: Iterable[Measurement]) -> None:
        """Start consuming `source` and show the window. Returns when the window is closed."""
        vis = o3d.visualization.Visualizer()
        vis.create_window(self.title, self.width, self.height)
        opt = vis.get_render_option()
        opt.point_size = self.point_size
        opt.background_color = np.array([0.04, 0.04, 0.06])

        # Placeholder point so the geometry is never empty when added
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.zeros((1, 3)))
        pcd.colors = o3d.utility.Vector3dVector(np.array([[1.0, 1.0, 1.0]]))
        vis.add_geometry(pcd)
        vis.add_geometry(o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.4))

        beam = o3d.geometry.LineSet()
        beam.points = o3d.utility.Vector3dVector(np.zeros((2, 3)))
        beam.lines = o3d.utility.Vector2iVector([[0, 1]])
        beam.colors = o3d.utility.Vector3dVector([[1.0, 0.1, 0.1]])
        if self.show_beam:
            vis.add_geometry(beam)

        worker = threading.Thread(target=self._pump, args=(source,), daemon=True)
        worker.start()

        last_draw, last_n, view_reset, announced = 0.0, 0, False, False
        period = 1.0 / self.fps
        try:
            while vis.poll_events():
                now = time.perf_counter()
                if now - last_draw >= period:
                    last_draw = now
                    n = self.mapper.num_points
                    if n != last_n and n > 0:
                        cloud = self.mapper.to_open3d(self.color_by)
                        pcd.points = cloud.points
                        pcd.colors = cloud.colors
                        vis.update_geometry(pcd)
                        last_n = n
                        if not view_reset and n >= 100:
                            vis.reset_view_point(True)
                            view_reset = True
                    lp = self.mapper.last_point
                    if self.show_beam and lp is not None:
                        beam.points = o3d.utility.Vector3dVector(np.array([[0, 0, 0], lp]))
                        vis.update_geometry(beam)
                vis.update_renderer()
                if self.source_done.is_set() and not announced:
                    announced = True
                    print(
                        f"[viewer] source finished: {self.mapper.accepted} points mapped, "
                        f"{self.mapper.rejected} rejected. Close the window to exit."
                    )
                time.sleep(0.004)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop.set()
            vis.destroy_window()