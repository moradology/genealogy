#!/usr/bin/env python3
"""Verify that every cross-reference id in the repo resolves.

Checks src.* references (reasoning traces, search frames) against
research/sources/source-index.json, and event.*/person.*/place.* references
against ancestry_geospatial.geojson plus the inline event data in index.html.
Run: uv run tools/check_refs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ID_RE = re.compile(r"\b(src|event|person|place|case)\.[A-Za-z0-9_.-]+\b")


def defined_ids() -> set[str]:
    ids: set[str] = set()
    index = json.loads((ROOT / "research" / "sources" / "source-index.json").read_text())
    for record in index["sources"]:
        ids.add(record["id"])
    geo = json.loads((ROOT / "ancestry_geospatial.geojson").read_text())
    for feature in geo.get("features", []):
        fid = feature.get("id")
        if isinstance(fid, str):
            ids.add(fid)
        props = feature.get("properties") or {}
        for key in ("person_id", "place_id", "event_id"):
            value = props.get(key)
            if isinstance(value, str):
                ids.add(value)
        for value in props.get("participants") or []:
            if isinstance(value, str):
                ids.add(value)
        for step in props.get("sequence") or []:
            for key in ("place_id", "event_id"):
                value = step.get(key)
                if isinstance(value, str):
                    ids.add(value)
    registry = geo.get("metadata", {}).get("place_registry") or {}
    ids.update(k for k in registry if isinstance(k, str))
    html = (ROOT / "index.html").read_text()
    for match in re.finditer(r'"id":"(event\.[^"]+)"', html):
        ids.add(match.group(1))
    for match in re.finditer(r'id="((?:person|case)\.[A-Za-z0-9_.-]+)"', html):
        ids.add(match.group(1))
    return ids


def referenced_ids() -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    paths = sorted((ROOT / "research" / "reasoning-traces").glob("*.md"))
    frames_dir = ROOT / "research" / "search-frames"
    if frames_dir.exists():
        paths.extend(sorted(frames_dir.glob("*.md")))
    for path in paths:
        found = [m.group(0).rstrip(".") for m in ID_RE.finditer(path.read_text())]
        if found:
            refs[str(path.relative_to(ROOT))] = found
    return refs


def main() -> int:
    known = defined_ids()
    failures = []
    for origin, refs in referenced_ids().items():
        for ref in refs:
            if ref not in known:
                failures.append((origin, ref))
    if failures:
        for origin, ref in failures:
            print(f"UNRESOLVED {ref} referenced from {origin}", file=sys.stderr)
        return 1
    print(f"check_refs: all references resolve ({len(known)} ids known)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
