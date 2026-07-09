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

  ./gen build basemap --check                rebuild and byte-compare
  ./gen build basemap                        splice into index.html
  uv run tools/build_basemap.py --emit-routes
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
GEOJSON = ROOT / "ancestry_geospatial.geojson"

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
EARTH_KM = 6371.0088
KM_PER_DEG = 111.19508


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

ROUTE_META = [
    ("path.zimmerman_surname", "route.zimmerman_surname", "zimmerman", "solid", ["convergence", "zimmerman"]),
    ("path.nauer", "route.nauer", "zimmerman", "solid", ["convergence", "zimmerman"]),
    ("path.nauer_candidate_lorenz", "route.nauer_candidate", "zimmerman", "conjectural", ["zimmerman"]),
    ("path.mundell", "route.mundell_rust", "mundell", "solid", ["convergence", "mundell"]),
    ("path.rust_candidate_john_f_ethel_b_rupert", "route.rust_candidate", "mundell", "conjectural", ["mundell"]),
    ("path.dible_surname", "route.dible_surname", "dible", "solid", ["convergence", "dible"]),
    ("path.long_sleight", "route.long_sleight", "dible", "solid", ["convergence", "dible"]),
    ("path.mcclelland_love", "route.mcclelland_love", "dible", "conjectural", ["dible"]),
    ("path.connelly_durham", "route.connelly_durham", "connelly", "solid", ["convergence", "connelly"]),
    ("path.claar_white_stropes", "route.claar_stropes", "connelly", "solid", ["convergence", "connelly"]),
]


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


def route_meta_js():
    records = []
    for _, route_id, anchor, grade, plates in ROUTE_META:
        plist = "[" + ",".join(f'"{plate}"' for plate in plates) + "]"
        records.append(f'{{id:"{route_id}",anchor:"{anchor}",grade:"{grade}",plates:{plist}}}')
    return "const ROUTE_META = [ " + ", ".join(records) + " ];"


def lonlat_vec(lon, lat):
    lon_r, lat_r = lon * D, lat * D
    c = math.cos(lat_r)
    return c * math.cos(lon_r), c * math.sin(lon_r), math.sin(lat_r)


def vec_lonlat(v):
    x, y, z = v
    hyp = math.hypot(x, y)
    return math.atan2(y, x) / D, math.atan2(z, hyp) / D


def slerp(a, b, t):
    va, vb = lonlat_vec(*a), lonlat_vec(*b)
    dot = max(-1.0, min(1.0, va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2]))
    omega = math.acos(dot)
    if omega < 1e-9:
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    so = math.sin(omega)
    wa = math.sin((1 - t) * omega) / so
    wb = math.sin(t * omega) / so
    return vec_lonlat((va[0] * wa + vb[0] * wb, va[1] * wa + vb[1] * wb, va[2] * wa + vb[2] * wb))


def point_line_distance(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    if norm == 0:
        return math.hypot(px - ax, py - ay)
    return abs(dx * (ay - py) - dy * (ax - px)) / norm


def sample_great_circle(a, b, project, tol=0.6, depth=0):
    pa, pb = project(*a), project(*b)
    mid = slerp(a, b, 0.5)
    pm = project(*mid)
    if depth >= 16 or point_line_distance(pm, pa, pb) <= tol:
        return [a, b]
    left = sample_great_circle(a, mid, project, tol, depth + 1)
    right = sample_great_circle(mid, b, project, tol, depth + 1)
    return left[:-1] + right


def close_point(a, b, eps=1e-9):
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


def clip_segment_rect(a, b, lo_x, lo_y, hi_x, hi_y):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in [(-dx, ax - lo_x), (dx, hi_x - ax), (-dy, ay - lo_y), (dy, hi_y - ay)]:
        if p == 0:
            if q < 0:
                return None
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return None
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return None
                if t < t1:
                    t1 = t
    return (ax + dx * t0, ay + dy * t0), (ax + dx * t1, ay + dy * t1)


def clip_polyline_geo(points, window):
    lo_x, lo_y, hi_x, hi_y = window
    chains, current = [], []
    for i in range(len(points) - 1):
        clipped = clip_segment_rect(points[i], points[i + 1], lo_x, lo_y, hi_x, hi_y)
        if clipped is None:
            if len(current) > 1:
                chains.append(current)
            current = []
            continue
        a, b = clipped
        if current and close_point(current[-1], a):
            if not close_point(current[-1], b):
                current.append(b)
        else:
            if len(current) > 1:
                chains.append(current)
            current = [a]
            if not close_point(a, b):
                current.append(b)
    if len(current) > 1:
        chains.append(current)
    return chains


def route_chain_from_sequence(feature, places):
    props = feature["properties"]
    steps = sorted(props["sequence"], key=lambda item: item["order"])
    chain = []
    for step in steps:
        coords = places[step["place_id"]]["coordinates"]
        if coords is None:
            print(f'{feature["id"]}: sequence place {step["place_id"]} has no coordinates', file=sys.stderr)
            raise SystemExit(1)
        chain.append({"coords": (coords[0], coords[1]), "event_id": step["event_id"]})
    return chain


def route_project_segments(chain, project, window, grade):
    segments = []
    for i in range(len(chain) - 1):
        a, b = chain[i], chain[i + 1]
        if close_point(a["coords"], b["coords"]):
            continue
        sampled = sample_great_circle(a["coords"], b["coords"], project)
        clipped = clip_polyline_geo(sampled, window)
        conjectural = grade == "conjectural" or a["event_id"].startswith("target.") or b["event_id"].startswith("target.")
        for part in clipped:
            projected = [project(lon, lat) for lon, lat in part]
            slim = simplify(projected, 0.6)
            if len(slim) >= 2:
                segments.append({"c": conjectural, "chain": slim, "before": len(projected), "after": len(slim)})
    return segments


def combine_route_segments(segments):
    combined = []
    for segment in segments:
        if not combined or combined[-1]["c"] != segment["c"] or not close_point(combined[-1]["chains"][-1][-1], segment["chain"][0], 0.05):
            combined.append({"c": segment["c"], "chains": [segment["chain"]], "before": segment["before"], "after": segment["after"]})
            continue
        combined[-1]["chains"][-1] = combined[-1]["chains"][-1] + segment["chain"][1:]
        combined[-1]["before"] += segment["before"] - 1
        combined[-1]["after"] += segment["after"] - 1
    return combined


def routes_for_base(features, places, project, window):
    by_path = {feature["id"]: feature for feature in features}
    routes = {}
    for path_id, route_id, _, grade, _ in ROUTE_META:
        if path_id not in by_path:
            print(f"{path_id}: temporal_path feature missing", file=sys.stderr)
            raise SystemExit(1)
        chain = route_chain_from_sequence(by_path[path_id], places)
        routes[route_id] = combine_route_segments(route_project_segments(chain, project, window, grade))
    return routes


def route_obj_js(item, include_q):
    fields = [f'd:{json.dumps(to_path(item["chains"], False), separators=(",", ":"))}']
    if item["c"]:
        fields.append("c:1")
    if include_q:
        x, y = item["chains"][0][0]
        fields.append(f"q:[{fmt(x)},{fmt(y)}]")
    return "{" + ",".join(fields) + "}"


def routes_js(name, routes):
    parts = []
    for _, route_id, _, grade, _ in ROUTE_META:
        items = []
        q_done = False
        for item in routes[route_id]:
            include_q = grade == "conjectural" and not q_done and item["chains"]
            items.append(route_obj_js(item, include_q))
            q_done = q_done or include_q
        parts.append(f'"{route_id}":[' + ",".join(items) + "]")
    return f"const {name} = {{" + ",".join(parts) + "};"


def build_routes():
    geo = json.loads(GEOJSON.read_text())
    features = [f for f in geo["features"] if f["properties"].get("feature_kind") == "temporal_path"]
    if len(features) != len(ROUTE_META):
        print(f"expected {len(ROUTE_META)} temporal_path features, found {len(features)}", file=sys.stderr)
        raise SystemExit(1)
    routes_mig = routes_for_base(features, geo["place_registry"], project_migration, MIG_WINDOW)
    routes_ks = routes_for_base(features, geo["place_registry"], project_kansas, KS_WINDOW)
    mig_scale = (N * RHO0 / math.cos(40 * D)) * MIG_S / EARTH_KM
    ks_scale = KS_S / KM_PER_DEG
    return "\n".join([
        route_meta_js(),
        routes_js("ROUTES_MIG", routes_mig),
        routes_js("ROUTES_KS", routes_ks),
        "// SCALE_UPK is svg units per km at the plate reference latitude.",
        f"const SCALE_UPK = {{ migration: {mig_scale:.6f}, kansas: {ks_scale:.6f} }};",
    ])


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
    return {"basemap-proj": proj, "basemap-paths": paths, "basemap-routes": build_routes()}


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
    print("index.html regions rewritten; run ./gen stamp --write next")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--emit-routes", action="store_true")
    group.add_argument("--emit-all", action="store_true")
    args = parser.parse_args()
    if args.emit_routes:
        print(build_routes())
        return 0
    blocks = build()
    if args.emit_all:
        print(blocks["basemap-proj"])
        print(blocks["basemap-paths"])
        print(blocks["basemap-routes"])
        print(f'const MIGRATION_GRATICULE_D = "{graticule()}";')
        print(f'const MIGRATION_FAN_D = "{fan_ring()}";')
        return 0
    if args.check:
        return check(blocks)
    return write(blocks)


if __name__ == "__main__":
    raise SystemExit(main())
