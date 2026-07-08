#!/usr/bin/env python3
"""Keep index.html's verifiedEventData and the geojson in lockstep.

Every displayed event must have a geojson feature with the same id, the
same Point coordinates, and matching fields (display name on the left,
geojson property on the right): type/event_type, date/date, sort/date_sort,
person/person_name, place/place_label, anchor/anchor,
confidence/confidence. Any forward mismatch fails.

The reverse direction -- geojson life_event features with no display twin
-- is a printed report only: which events appear on the plates is an
editorial choice, not a sync error.

Run: uv run tools/check_geo_sync.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FIELD_PAIRS = [
    ("type", "event_type"),
    ("date", "date"),
    ("sort", "date_sort"),
    ("person", "person_name"),
    ("place", "place_label"),
    ("anchor", "anchor"),
    ("confidence", "confidence"),
]


def displayed_events(html: str) -> list[dict]:
    start = html.index("const verifiedEventData")
    block = html[start:html.index("];", start)]
    events = []
    for line in block.splitlines():
        line = line.strip().rstrip(",")
        if line.startswith('{"id":"event.'):
            events.append(json.loads(line))
    return events


def main() -> int:
    html = (ROOT / "index.html").read_text()
    geo = json.loads((ROOT / "ancestry_geospatial.geojson").read_text())
    events = displayed_events(html)
    if len(events) < 24:
        print(f"parsed only {len(events)} verifiedEventData entries; parser or data broke", file=sys.stderr)
        return 1

    by_id = {f.get("id"): f for f in geo["features"]}
    failures = []
    for event in events:
        feature = by_id.get(event["id"])
        if feature is None:
            failures.append(f"{event['id']}: displayed but no geojson feature")
            continue
        geometry = feature.get("geometry") or {}
        props = feature.get("properties") or {}
        if geometry.get("type") != "Point":
            failures.append(f"{event['id']}: geojson geometry is {geometry.get('type')}, not Point")
        elif geometry.get("coordinates") != event["coords"]:
            failures.append(f"{event['id']}: coords {event['coords']} vs geojson {geometry.get('coordinates')}")
        for html_key, geo_key in FIELD_PAIRS:
            if event.get(html_key) != props.get(geo_key):
                failures.append(
                    f"{event['id']}: {html_key} {event.get(html_key)!r} vs geojson {geo_key} {props.get(geo_key)!r}")

    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        print(f"check_geo_sync: {len(failures)} mismatch(es)", file=sys.stderr)
        return 1

    displayed = {e["id"] for e in events}
    undisplayed = [fid for fid, f in by_id.items()
                   if (f.get("properties") or {}).get("feature_kind") == "life_event"
                   and fid not in displayed]
    print(f"check_geo_sync: {len(events)} displayed events match their geojson twins")
    print(f"  (editorial note: {len(undisplayed)} life_event features are not displayed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
