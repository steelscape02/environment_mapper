"""
testbench.py
============
Emulates a LiDAR on a pan/tilt servo gimbal and injects the readings into lidar_mapper
so you can watch the point cloud build up in a live Open3D window.

The sensor sits at the origin, 1 m above the floor. Each commanded (pan, tilt) pair is
ray-cast into a synthetic scene to produce a distance, with optional noise and dropouts.

Usage
-----
    python testbench.py --selftest                 # math checks only, no window
    python testbench.py                            # room scene, live window
    python testbench.py --scene sphere --rate 2000
    python testbench.py --pan-range -180 180 --pan-step 1.5 --noise 0.02 --dropout 0.01
    python testbench.py --headless --save out.ply  # run to completion, no window
"""
from __future__ import annotations

import argparse
import math
import time
from typing import Iterator, List, Optional, Tuple

import numpy as np

from mapper import LiveViewer, Measurement, PointCloudMapper, SensorConfig

Vec = np.ndarray


# --------------------------------------------------------------------------- scene primitives
class Sphere:
    def __init__(self, center, radius):
        self.c = np.asarray(center, float)
        self.r = float(radius)

    def hit(self, o: Vec, d: Vec) -> Optional[float]:
        oc = o - self.c
        b = float(np.dot(oc, d))
        disc = b * b - (float(np.dot(oc, oc)) - self.r ** 2)
        if disc < 0:
            return None
        s = math.sqrt(disc)
        t = -b - s
        if t <= 1e-6:
            t = -b + s
        return t if t > 1e-6 else None


class Box:
    """Axis-aligned box. inside=True means the ray starts inside it (a room)."""

    def __init__(self, lo, hi, inside=False):
        self.lo = np.asarray(lo, float)
        self.hi = np.asarray(hi, float)
        self.inside = inside

    def hit(self, o: Vec, d: Vec) -> Optional[float]:
        with np.errstate(divide="ignore", invalid="ignore"):
            t1 = (self.lo - o) / d
            t2 = (self.hi - o) / d
        # Parallel rays outside the slab never hit
        parallel = np.abs(d) < 1e-12
        if not self.inside and np.any(parallel & ((o < self.lo) | (o > self.hi))):
            return None
        tnear = np.where(parallel, -np.inf, np.minimum(t1, t2)).max()
        tfar = np.where(parallel, np.inf, np.maximum(t1, t2)).min()
        if tnear > tfar or tfar <= 1e-6:
            return None
        if self.inside:
            return float(tfar)
        return float(tnear) if tnear > 1e-6 else None


def build_scene(name: str) -> list:
    if name == "sphere":
        return [Sphere((2.0, 0.0, 0.0), 1.0)]
    if name == "wall":
        return [Box((3.0, -10, -10), (3.5, 10, 10))]  # flat wall 3 m ahead
    # default: room with a sphere and a crate (sensor 1 m above floor)
    return [
        Box((-3.0, -2.5, -1.0), (3.0, 2.5, 1.5), inside=True),
        Sphere((1.8, 0.8, -0.4), 0.6),
        Box((-2.0, -1.6, -1.0), (-1.0, -0.6, -0.2)),
    ]


def raycast(scene: list, pan_deg: float, tilt_deg: float, max_range: float) -> float:
    az, el = math.radians(pan_deg), math.radians(tilt_deg)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    o = np.zeros(3)
    best = math.inf
    for obj in scene:
        t = obj.hit(o, d)
        if t is not None and t < best:
            best = t
    return best if best <= max_range else math.inf  # inf = no return


# --------------------------------------------------------------------------- scan pattern
def raster_scan(pan_range, tilt_range, pan_step, tilt_step) -> Iterator[Tuple[float, float]]:
    """Boustrophedon raster: sweep pan, step tilt, reverse pan direction each row."""
    tilts = np.arange(tilt_range[0], tilt_range[1] + 1e-9, tilt_step)
    pans = np.arange(pan_range[0], pan_range[1] + 1e-9, pan_step)
    for i, tilt in enumerate(tilts):
        for pan in (pans if i % 2 == 0 else pans[::-1]):
            yield float(pan), float(tilt)


# --------------------------------------------------------------------------- simulated sensor
def simulated_lidar(
    scene: list,
    scan: Iterator[Tuple[float, float]],
    rate_hz: float,
    noise_m: float,
    angle_noise_deg: float,
    dropout: float,
    max_range: float,
    seed: int = 0,
) -> Iterator[Measurement]:
    """Generator that behaves like a sensor driver: yields Measurements at ~rate_hz."""
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    for i, (pan, tilt) in enumerate(scan):
        # Pace output to the requested sample rate
        ahead = (t0 + i / rate_hz) - time.perf_counter()
        if ahead > 0.001:
            time.sleep(ahead)

        dist = raycast(scene, pan, tilt, max_range)
        if math.isfinite(dist):
            dist += rng.normal(0, noise_m)
        if rng.random() < dropout:
            dist = math.nan
        # Servo angle reported to the mapper can differ slightly from the true one
        yield Measurement(
            pan_deg=pan + rng.normal(0, angle_noise_deg),
            tilt_deg=tilt + rng.normal(0, angle_noise_deg),
            distance_m=dist,
            timestamp=time.perf_counter() - t0,
        )


# --------------------------------------------------------------------------- self test
def selftest() -> bool:
    """Check the polar->XYZ math against hand-computed vectors."""
    s2 = math.sqrt(2)
    cases = [
        # pan, tilt, dist, expected xyz
        (0, 0, 1, (1, 0, 0)),
        (90, 0, 1, (0, 1, 0)),
        (-90, 0, 1, (0, -1, 0)),
        (180, 0, 2, (-2, 0, 0)),
        (0, 90, 1, (0, 0, 1)),
        (0, -90, 1, (0, 0, -1)),
        (0, 45, s2, (1, 0, 1)),
        (45, 0, s2, (1, 1, 0)),
    ]
    ok = True
    mapper = PointCloudMapper()
    for pan, tilt, d, exp in cases:
        got = mapper.polar_to_xyz([pan], [tilt], [d])[0]
        good = np.allclose(got, exp, atol=1e-9)
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] pan={pan:>4} tilt={tilt:>4} d={d:.3f} -> {np.round(got, 4)} (expected {exp})")

    # Inverted pan
    m = PointCloudMapper(SensorConfig(pan_invert=True))
    good = np.allclose(m.polar_to_xyz([90], [0], [1])[0], (0, -1, 0), atol=1e-9)
    ok &= good
    print(f"  [{'PASS' if good else 'FAIL'}] pan_invert flips Y")

    # Lidar mounting offset (5 cm forward, 3 cm up on the tilt servo)
    m = PointCloudMapper(SensorConfig(lidar_offset_m=(0.05, 0.0, 0.03)))
    g1 = m.polar_to_xyz([0], [0], [1])[0]
    g2 = m.polar_to_xyz([0], [90], [1])[0]
    good = np.allclose(g1, (1.05, 0, 0.03), atol=1e-9) and np.allclose(g2, (-0.03, 0, 1.05), atol=1e-9)
    ok &= good
    print(f"  [{'PASS' if good else 'FAIL'}] lidar_offset applied in tilt frame")

    # Range filtering
    m = PointCloudMapper(SensorConfig(min_range_m=0.1, max_range_m=5.0))
    n = m.add_batch([0, 0, 0, 0], [0, 0, 0, 0], [0.01, 1.0, 9.0, math.nan])
    good = n == 1 and m.rejected == 3
    ok &= good
    print(f"  [{'PASS' if good else 'FAIL'}] range / NaN rejection ({m.accepted} kept, {m.rejected} rejected)")

    # Ray caster round trip: flat wall at x=3 -> every mapped point should have x ~= 3
    scene = build_scene("wall")
    m = PointCloudMapper()
    for pan, tilt in raster_scan((-40, 40), (-20, 20), 5, 5):
        m.add(Measurement(pan, tilt, raycast(scene, pan, tilt, 12.0)))
    pts, _ = m.snapshot()
    good = len(pts) > 0 and np.allclose(pts[:, 0], 3.0, atol=1e-6)
    ok &= good
    print(f"  [{'PASS' if good else 'FAIL'}] raycast -> mapper round trip on flat wall ({len(pts)} pts all at x=3)")

    print("SELFTEST", "PASSED" if ok else "FAILED")
    return ok


# --------------------------------------------------------------------------- main
def main() -> int:
    p = argparse.ArgumentParser(description="Simulated pan/tilt LiDAR testbench for lidar_mapper")
    p.add_argument("--scene", choices=["room", "sphere", "wall"], default="room")
    p.add_argument("--pan-range", type=float, nargs=2, default=(-90.0, 90.0), metavar=("MIN", "MAX"))
    p.add_argument("--tilt-range", type=float, nargs=2, default=(-30.0, 60.0), metavar=("MIN", "MAX"))
    p.add_argument("--pan-step", type=float, default=1.0, help="degrees between samples along a sweep")
    p.add_argument("--tilt-step", type=float, default=2.0, help="degrees between sweeps")
    p.add_argument("--rate", type=float, default=600.0, help="samples per second")
    p.add_argument("--noise", type=float, default=0.01, help="range noise sigma (m)")
    p.add_argument("--angle-noise", type=float, default=0.0, help="servo angle noise sigma (deg)")
    p.add_argument("--dropout", type=float, default=0.0, help="probability a sample returns nothing")
    p.add_argument("--max-range", type=float, default=12.0)
    p.add_argument("--color-by", choices=["height", "distance", "none"], default="height")
    p.add_argument("--point-size", type=float, default=3.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--selftest", action="store_true", help="run math checks and exit")
    p.add_argument("--headless", action="store_true", help="no window; run the whole scan immediately")
    p.add_argument("--save", metavar="FILE", help="write final cloud to FILE (.ply/.pcd) on exit")
    a = p.parse_args()

    if a.selftest:
        return 0 if selftest() else 1

    mapper = PointCloudMapper(SensorConfig(max_range_m=a.max_range))
    scene = build_scene(a.scene)
    scan = raster_scan(a.pan_range, a.tilt_range, a.pan_step, a.tilt_step)
    total = len(np.arange(a.pan_range[0], a.pan_range[1] + 1e-9, a.pan_step)) * len(
        np.arange(a.tilt_range[0], a.tilt_range[1] + 1e-9, a.tilt_step)
    )
    rate = 1e9 if a.headless else a.rate
    source = simulated_lidar(scene, scan, rate, a.noise, a.angle_noise, a.dropout, a.max_range, a.seed)

    print(f"[testbench] scene={a.scene} samples={total} rate={'max' if a.headless else a.rate} Hz "
          f"(~{total / a.rate:.1f} s)" if not a.headless else f"[testbench] scene={a.scene} samples={total} (headless)")

    if a.headless:
        for m in source:
            mapper.add(m)
        print(f"[testbench] mapped {mapper.accepted} points, rejected {mapper.rejected}")
    else:
        LiveViewer(mapper, title=f"Testbench: {a.scene}", point_size=a.point_size, color_by=a.color_by).run(source)

    if a.save:
        mapper.save(a.save, a.color_by)
        print(f"[testbench] saved {mapper.num_points} points to {a.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())