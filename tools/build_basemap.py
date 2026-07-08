#!/usr/bin/env python3
"""Rebuild the pre-projected SVG basemap constants baked into index.html.

Source data is Natural Earth (public domain), pinned to one immutable
commit of nvkelso/natural-earth-vector with a SHA256 per file, cached in
tools/basemap-data/ (gitignored). The output is byte-identical to the
constants shipped since the v5 pipeline landed; --check proves it.

The v5 algorithm, kept exactly as it landed: Lambert conformal conic
(parallels 30/50, central meridian -42, reference latitude 40) for the
migration plate and a local equirectangular window for the Kansas plate;
rings clipped in RAW longitude space to [-179.9, 139.9] BEFORE projection
(kills the 140E Russia seam that once drew a water slash through Poland);
Sutherland-Hodgman ring clip and segment-drop polyline clip in projected
space; Douglas-Peucker simplification; a shoelace-area bowtie filter
(big bbox, near-zero area = self-cancelling ribbon) backstopping any
remaining degenerate rings; paths emitted as absolute-M/relative-l
rounded to 0.1. The fan and graticule are computed at runtime in
index.html from the same constants; --emit-all prints them here too for
cross-validation.

  uv run tools/build_basemap.py --check      rebuild and byte-compare
  uv run tools/build_basemap.py --write      splice into index.html
  uv run tools/build_basemap.py --emit-all   print everything to stdout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
CACHE = ROOT / "tools" / "basemap-data"

NE_COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
NE_BASE = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson"
NE_FILES = {
    "ne_110m_admin_0_countries.geojson":
        "6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f",
    "ne_110m_admin_1_states_provinces_lines.geojson":
        "f204e94d5c4d16c6ce4b59ecb50e264bd95c22b9138d8a994c010c222e186aad",
    "ne_110m_lakes.geojson":
        "eb02ecc86c82004fccbf979058bfabbbd6c2d07968c7844d38eb1c9152d2ffc9",
    "ne_50m_admin_1_states_provinces_lines.geojson":
        "72cca93c850d412628a5da4bc5ebfe21ba4d376eb34611bde6b623ee73f0fdcf",
}

D = math.pi / 180
P1, P2 = 30 * D, 50 * D
LON0, LAT0 = -42 * D, 40 * D
N = math.log(math.cos(P1) / math.cos(P2)) / math.log(
    math.tan(math.pi / 4 + P2 / 2) / math.tan(math.pi / 4 + P1 / 2)
)
F = math.cos(P1) * math.tan(math.pi / 4 + P1 / 2) ** N / N
RHO0 = F / math.tan(math.pi / 4 + LAT0 / 2) ** N

MIG_WINDOW = (-106.0, 24.0, 22.0, 54.5)
GEO_CLIP = (-179.9, 5.0, 139.9, 72.0)
MIG_VB = (1000.0, 540.0)


def lcc_raw(lon, lat):
    lat = max(-84.0, min(84.0, lat))
    rho = F / math.tan(math.pi / 4 + lat * D / 2) ** N
    theta = N * (lon * D - LON0)
    return rho * math.sin(theta), RHO0 - rho * math.cos(theta)


def window_extent():
    lon_min, lat_min, lon_max, lat_max = MIG_WINDOW
    xs, ys = [], []
    steps = 64
    for i in range(steps + 1):
        t = i / steps
        for lon, lat in [
            (lon_min + t * (lon_max - lon_min), lat_min),
            (lon_min + t * (lon_max - lon_min), lat_max),
            (lon_min, lat_min + t * (lat_max - lat_min)),
            (lon_max, lat_min + t * (lat_max - lat_min)),
        ]:
            x, y = lcc_raw(lon, lat)
            xs.append(x)
            ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


X_MIN, X_MAX, Y_MIN, Y_MAX = window_extent()
MIG_S = min(MIG_VB[0] / (X_MAX - X_MIN), MIG_VB[1] / (Y_MAX - Y_MIN))
MIG_W = (X_MAX - X_MIN) * MIG_S
MIG_H = (Y_MAX - Y_MIN) * MIG_S


def project_migration(lon, lat):
    x, y = lcc_raw(lon, lat)
    return (x - X_MIN) * MIG_S, (Y_MAX - y) * MIG_S


KS_WINDOW = (-103.5, 38.4, -94.5, 42.5)
KS_K = math.cos(40.45 * D)
KS_VB_W = 1000.0
KS_S = KS_VB_W / ((KS_WINDOW[2] - KS_WINDOW[0]) * KS_K)
KS_VB_H = (KS_WINDOW[3] - KS_WINDOW[1]) * KS_S


def project_kansas(lon, lat):
    return (lon - KS_WINDOW[0]) * KS_K * KS_S, (KS_WINDOW[3] - lat) * KS_S


def rings_of(geom):
    gtype, coords = geom["type"], geom["coordinates"]
    if gtype == "Polygon":
        return list(coords)
    if gtype == "MultiPolygon":
        return [ring for poly in coords for ring in poly]
    if gtype == "LineString":
        return [coords]
    if gtype == "MultiLineString":
        return list(coords)
    return []


def clip_ring_rect(ring, lo_x, lo_y, hi_x, hi_y):
    edges = [
        lambda p: p[0] >= lo_x, lambda p: p[0] <= hi_x,
        lambda p: p[1] >= lo_y, lambda p: p[1] <= hi_y,
    ]

    def intersect(a, b, idx):
        ax, ay = a
        bx, by = b
        if idx < 2:
            x = lo_x if idx == 0 else hi_x
            t = (x - ax) / (bx - ax)
            return (x, ay + t * (by - ay))
        y = lo_y if idx == 2 else hi_y
        t = (y - ay) / (by - ay)
        return (ax + t * (bx - ax), y)

    out = ring
    for idx, inside in enumerate(edges):
        if not out:
            return []
        result = []
        prev = out[-1]
        for cur in out:
            if inside(cur):
                if not inside(prev):
                    result.append(intersect(prev, cur, idx))
                result.append(cur)
            elif inside(prev):
                result.append(intersect(prev, cur, idx))
            prev = cur
        out = result
    return out


def clip_polyline_rect(points, lo_x, lo_y, hi_x, hi_y):
    def inside(p):
        return lo_x <= p[0] <= hi_x and lo_y <= p[1] <= hi_y

    segments, current = [], []
    for p in points:
        if inside(p):
            current.append(p)
        else:
            if len(current) > 1:
                segments.append(current)
            current = []
    if len(current) > 1:
        segments.append(current)
    return segments


def simplify(points, tol):
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        lo, hi = stack.pop()
        ax, ay = points[lo]
        bx, by = points[hi]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        best, best_i = -1.0, -1
        for i in range(lo + 1, hi):
            px, py = points[i]
            if norm == 0:
                dist = math.hypot(px - ax, py - ay)
            else:
                dist = abs(dx * (ay - py) - dy * (ax - px)) / norm
            if dist > best:
                best, best_i = dist, i
        if best > tol:
            keep[best_i] = True
            stack.append((lo, best_i))
            stack.append((best_i, hi))
    return [p for p, k in zip(points, keep) if k]


def shoelace(points):
    area = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def solid(chain, w, h):
    xs = [p[0] for p in chain]
    ys = [p[1] for p in chain]
    if max(xs) < 0.5 or min(xs) > w - 0.5 or max(ys) < 0.5 or min(ys) > h - 0.5:
        return False  # never enters the window
    area = shoelace(chain)
    bbox = (max(xs) - min(xs)) * (max(ys) - min(ys))
    if area < 4.0:
        return False  # microscopic sliver
    if bbox > 400.0 and area < 0.12 * bbox:
        return False  # self-crossing bowtie ribbon: big bbox, cancelling lobes
    return True


def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def to_path(chains, closed):
    parts = []
    for chain in chains:
        if len(chain) < 2:
            continue
        x0, y0 = chain[0]
        cmds = [f"M{fmt(x0)} {fmt(y0)}"]
        px, py = x0, y0
        for x, y in chain[1:]:
            dx, dy = x - px, y - py
            if abs(dx) < 0.05 and abs(dy) < 0.05:
                continue
            cmds.append(f"l{fmt(dx)} {fmt(dy)}")
            px, py = x, y
        if len(cmds) > 1:
            if closed:
                cmds.append("Z")
            parts.append("".join(cmds))
    return "".join(parts)


def build_layer(features, project, w, h, tol, closed, pad):
    g_lo_x, g_lo_y, g_hi_x, g_hi_y = GEO_CLIP
    chains = []
    for feature in features:
        for ring in rings_of(feature["geometry"]):
            geo = [(lon, lat) for lon, lat, *_ in ring]
            if closed:
                geo_parts = [clip_ring_rect(geo, g_lo_x, g_lo_y, g_hi_x, g_hi_y)]
            else:
                geo_parts = clip_polyline_rect(geo, g_lo_x, g_lo_y, g_hi_x, g_hi_y)
            for part in geo_parts:
                if len(part) < 2:
                    continue
                projected = [project(lon, lat) for lon, lat in part]
                if closed:
                    clipped = clip_ring_rect(projected, -pad, -pad, w + pad, h + pad)
                    if len(clipped) >= 3:
                        slim = simplify(clipped, tol)
                        if len(slim) >= 3 and solid(slim, w, h):
                            chains.append(slim)
                else:
                    for seg in clip_polyline_rect(projected, 0, 0, w, h):
                        slim = simplify(seg, tol)
                        if len(slim) >= 2:
                            chains.append(slim)
    return to_path(chains, closed)


def graticule():
    chains = []
    lon_min, lat_min, lon_max, lat_max = MIG_WINDOW
    for lon in range(-100, 30, 10):
        pts = [project_migration(lon, lat_min + i * (lat_max - lat_min) / 60) for i in range(61)]
        chains.extend(clip_polyline_rect(pts, 0, 0, MIG_W, MIG_H))
    for lat in range(30, 60, 10):
        pts = [project_migration(lon_min + i * (lon_max - lon_min) / 120, lat) for i in range(121)]
        chains.extend(clip_polyline_rect(pts, 0, 0, MIG_W, MIG_H))
    return to_path([simplify(c, 0.4) for c in chains], False)


def fan_ring():
    lon_min, lat_min, lon_max, lat_max = MIG_WINDOW
    steps = 240
    fan = []
    for i in range(steps + 1):
        fan.append(project_migration(lon_min + (lon_max - lon_min) * i / steps, lat_min))
    for i in range(steps + 1):
        fan.append(project_migration(lon_max, lat_min + (lat_max - lat_min) * i / steps))
    for i in range(steps + 1):
        fan.append(project_migration(lon_max - (lon_max - lon_min) * i / steps, lat_max))
    for i in range(steps + 1):
        fan.append(project_migration(lon_min, lat_max - (lat_max - lat_min) * i / steps))
    return "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in fan) + "Z"


def fetch(name):
    want = NE_FILES[name]
    path = CACHE / name
    if path.exists():
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got == want:
            return json.loads(path.read_text())["features"]
        print(f"cached {name} has sha256 {got}, expected {want}; re-downloading", file=sys.stderr)
    CACHE.mkdir(parents=True, exist_ok=True)
    url = f"{NE_BASE}/{name}"
    print(f"downloading {url}")
    data = urllib.request.urlopen(url, timeout=120).read()
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        print(f"{name}: downloaded sha256 {got} != pinned {want}", file=sys.stderr)
        raise SystemExit(1)
    path.write_bytes(data)
    return json.loads(data.decode())["features"]


def self_check(land_d):
    import re
    bad = 0
    for sp in land_d.split("M")[1:]:
        nums = re.findall(r"-?\d+\.?\d*", sp)
        x, y = float(nums[0]), float(nums[1])
        pts = [(x, y)]
        for j in range(2, len(nums) - 1, 2):
            x += float(nums[j])
            y += float(nums[j + 1])
            pts.append((x, y))
        xs = [p[0] for p in pts]
        if max(xs) - min(xs) > 600 and shoelace(pts) < 0.12 * (max(xs) - min(xs)) * 40:
            bad += 1
    if bad:
        print(f"self-check failed: {bad} surviving wide bowtie ring(s)", file=sys.stderr)
        raise SystemExit(1)


def build():
    countries = fetch("ne_110m_admin_0_countries.geojson")
    lines_110 = fetch("ne_110m_admin_1_states_provinces_lines.geojson")
    lakes = fetch("ne_110m_lakes.geojson")
    lines_50 = fetch("ne_50m_admin_1_states_provinces_lines.geojson")

    land_d = build_layer(countries, project_migration, MIG_W, MIG_H, 1.2, True, 12)
    self_check(land_d)
    borders_d = build_layer(lines_110, project_migration, MIG_W, MIG_H, 1.2, False, 0)
    lakes_d = build_layer(lakes, project_migration, MIG_W, MIG_H, 1.0, True, 0)
    ks_borders_d = build_layer(lines_50, project_kansas, KS_VB_W, KS_VB_H, 0.6, False, 0)

    lon_min, lat_min, lon_max, lat_max = MIG_WINDOW
    proj = "\n".join([
        "// Basemap generated from Natural Earth (public domain) via build_basemap.py.",
        f"const MIG_VIEW = {{ w: {fmt(MIG_W)}, h: {fmt(MIG_H)} }};",
        f"const KS_VIEW = {{ w: {fmt(KS_VB_W)}, h: {fmt(KS_VB_H)} }};",
        "const MIG_PROJ = { p1: 30, p2: 50, lon0: -42, "
        f"xMin: {X_MIN:.6f}, yMax: {Y_MAX:.6f}, s: {MIG_S:.6f} }};",
        f"const KS_PROJ = {{ lonMin: {KS_WINDOW[0]}, latMax: {KS_WINDOW[3]}, "
        f"k: {KS_K:.6f}, s: {KS_S:.6f}, lonMax: {KS_WINDOW[2]}, latMin: {KS_WINDOW[1]} }};",
        f"const MIG_WINDOW = {{ lonMin: {fmt(lon_min)}, latMin: {fmt(lat_min)}, "
        f"lonMax: {fmt(lon_max)}, latMax: {fmt(lat_max)} }};",
    ])
    paths = "\n".join([
        f'const MIGRATION_LAND_D = "{land_d}";',
        f'const MIGRATION_BORDERS_D = "{borders_d}";',
        f'const MIGRATION_LAKES_D = "{lakes_d}";',
        f'const KANSAS_BORDERS_D = "{ks_borders_d}";',
    ])
    return {"basemap-proj": proj, "basemap-paths": paths}


def region_bounds(html, tag):
    begin = f"// BEGIN GENERATED {tag}"
    end = f"// END GENERATED {tag}"
    if html.count(begin) != 1 or html.count(end) != 1:
        print(f"index.html must contain exactly one {begin} / {end} pair", file=sys.stderr)
        raise SystemExit(1)
    start = html.index("\n", html.index(begin)) + 1
    return start, html.index(end)


def check(blocks):
    html = HTML.read_text()
    stale = 0
    for tag, generated in blocks.items():
        start, stop = region_bounds(html, tag)
        current = html[start:stop].rstrip("\n")
        if current != generated:
            stale += 1
            cur_lines, gen_lines = current.split("\n"), generated.split("\n")
            print(f"{tag}: region differs from generator output", file=sys.stderr)
            for i in range(max(len(cur_lines), len(gen_lines))):
                c = cur_lines[i] if i < len(cur_lines) else "<absent>"
                g = gen_lines[i] if i < len(gen_lines) else "<absent>"
                if c != g:
                    print(f"  line {i + 1}: html {c[:80]!r} vs built {g[:80]!r}", file=sys.stderr)
        else:
            print(f"{tag}: byte-identical ({stop - start} bytes)")
    return 1 if stale else 0


def write(blocks):
    html = HTML.read_text()
    for tag, generated in blocks.items():
        start, stop = region_bounds(html, tag)
        html = html[:start] + generated + "\n" + html[stop:]
    HTML.write_text(html)
    print("index.html regions rewritten; run tools/stamp.py --write next")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--emit-all", action="store_true")
    args = parser.parse_args()
    blocks = build()
    if args.emit_all:
        print(blocks["basemap-proj"])
        print(blocks["basemap-paths"])
        print(f'const MIGRATION_GRATICULE_D = "{graticule()}";')
        print(f'const MIGRATION_FAN_D = "{fan_ring()}";')
        return 0
    if args.check:
        return check(blocks)
    return write(blocks)


if __name__ == "__main__":
    raise SystemExit(main())
