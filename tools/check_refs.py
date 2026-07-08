#!/usr/bin/env python3
"""Verify the cross-reference id universe is closed.

Definitions and references are kept strictly apart, so a typo in a
reference can no longer define itself (the flaw in the previous version
of this checker). Definitions: verifiedEventData ids and person./case.
anchors in index.html, geojson feature-level ids, the geojson top-level
place_registry (top level, not metadata -- the old path silently read
nothing), geojson person_id/participants (interim person registry until
the person anchors land), and the source ledger. References: research
markdown (reasoning traces and search frames), geojson link endpoints and
route sequences, and the familyLinkData block in index.html.

Also enforced: geojson feature ids unique; familyLinkData ids match
geojson link_id set exactly; familyLinkData endpoints resolve to
verifiedEventData (the map runtime draws only those); every geojson
source_refs URL is in the ledger; ledger URLs unique; id grammar for
person.* and case.*.

Run: uv run tools/check_refs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ID_RE = re.compile(r"\b(src|event|person|place|case)\.[A-Za-z0-9_.-]+\b")
# Anchors are single-segment (person.doyle_zimmerman); everyone else is
# person.<surname>.<given> — at most one extra dot (Slate 1 id grammar).
PERSON_GRAMMAR = re.compile(r"person\.[a-z0-9_]+(\.[a-z0-9_]+)?\Z")
CASE_GRAMMAR = re.compile(r"case\.\d{2}\Z")


def family_link_block(html: str) -> str:
    start = html.index("const familyLinkData")
    return html[start:html.index("];", start)]


def collect_definitions(html: str, geo: dict, ledger: dict, failures: list[str]) -> set[str]:
    ids: set[str] = set()
    for record in ledger["sources"]:
        ids.add(record["id"])
    for match in re.finditer(r'"id":"(event\.[^"]+)"', html):
        ids.add(match.group(1))
    for match in re.finditer(r'id="((?:person|case)\.[A-Za-z0-9_.-]+)"', html):
        ids.add(match.group(1))
    seen_fids: set[str] = set()
    for feature in geo["features"]:
        fid = feature.get("id")
        if not isinstance(fid, str):
            failures.append(f"feature without string id: {json.dumps(feature.get('properties', {}).get('feature_kind'))}")
            continue
        if fid in seen_fids:
            failures.append(f"duplicate feature id {fid}")
        seen_fids.add(fid)
        props = feature.get("properties") or {}
        # person_id/participants are the person registry until index.html
        # carries person.* anchors for every row; then they become references.
        value = props.get("person_id")
        if isinstance(value, str):
            ids.add(value)
        for value in props.get("participants") or []:
            if isinstance(value, str):
                ids.add(value)
    ids.update(seen_fids)
    ids.update(k for k in geo.get("place_registry") or {} if isinstance(k, str))
    return ids


def collect_references(geo: dict) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    paths = sorted((ROOT / "research" / "reasoning-traces").glob("*.md"))
    frames_dir = ROOT / "research" / "search-frames"
    if frames_dir.exists():
        paths.extend(sorted(frames_dir.rglob("*.md")))
    for path in paths:
        origin = str(path.relative_to(ROOT))
        for match in ID_RE.finditer(path.read_text()):
            refs.append((origin, match.group(0).rstrip(".")))
    for feature in geo["features"]:
        props = feature.get("properties") or {}
        origin = f"geojson {feature.get('id')}"
        for key in ("from_event_ids", "to_event_ids"):
            for value in props.get(key) or []:
                if isinstance(value, str):
                    refs.append((origin, value))
        value = props.get("to_event_id")
        if isinstance(value, str):
            refs.append((origin, value))
        value = props.get("place_id")
        if isinstance(value, str):
            refs.append((origin, value))
        for step in props.get("sequence") or []:
            for key in ("event_id", "place_id"):
                value = step.get(key)
                if isinstance(value, str):
                    refs.append((origin, value))
    return refs


def check_links(html: str, geo: dict, failures: list[str]) -> None:
    block = family_link_block(html)
    html_links = set(re.findall(r'id: "(link\.[^"]+)"', block))
    geo_links = set()
    for feature in geo["features"]:
        value = (feature.get("properties") or {}).get("link_id")
        if isinstance(value, str):
            geo_links.add(value)
    for missing in sorted(html_links - geo_links):
        failures.append(f"familyLinkData {missing} has no geojson family_link twin")
    for missing in sorted(geo_links - html_links):
        failures.append(f"geojson link_id {missing} has no familyLinkData twin")
    verified = set(re.findall(r'"id":"(event\.[^"]+)"', html))
    for ref in sorted(set(re.findall(r'"(event\.[^"]+)"', block))):
        if ref not in verified:
            failures.append(f"familyLinkData endpoint {ref} not in verifiedEventData")


def check_source_urls(geo: dict, ledger: dict, failures: list[str]) -> None:
    ledger_urls: set[str] = set()
    for record in ledger["sources"]:
        url = record["url"]
        if url in ledger_urls:
            failures.append(f"ledger URL appears twice: {url}")
        ledger_urls.add(url)
    for feature in geo["features"]:
        props = feature.get("properties") or {}
        for url in props.get("source_refs") or []:
            if isinstance(url, str) and url not in ledger_urls:
                failures.append(f"geojson {feature.get('id')} cites URL absent from ledger: {url}")


def check_grammar(ids: set[str], failures: list[str]) -> None:
    for value in sorted(ids):
        if value.startswith("person.") and PERSON_GRAMMAR.fullmatch(value) is None:
            failures.append(f"person id violates grammar person.[a-z0-9_]+: {value}")
        if value.startswith("case.") and CASE_GRAMMAR.fullmatch(value) is None:
            failures.append(f"case id violates grammar case.NN: {value}")


def main() -> int:
    html = (ROOT / "index.html").read_text()
    geo = json.loads((ROOT / "ancestry_geospatial.geojson").read_text())
    ledger = json.loads((ROOT / "research" / "sources" / "source-index.json").read_text())

    failures: list[str] = []
    known = collect_definitions(html, geo, ledger, failures)
    references = collect_references(geo)
    # case.* resolution is dormant until the Docket lands its anchors in
    # index.html (Slate 1 W5): validation traces legitimately cite future
    # cases. Once ANY case anchor exists, every case ref must resolve.
    docket_live = any(k.startswith("case.") for k in known)
    pending_cases = set()
    for origin, ref in references:
        if ref not in known:
            if ref.startswith("case.") and not docket_live:
                pending_cases.add(ref)
                continue
            failures.append(f"UNRESOLVED {ref} referenced from {origin}")
    if pending_cases:
        print(f"check_refs: {len(pending_cases)} case refs pending the Docket "
              f"({', '.join(sorted(pending_cases))})")
    check_links(html, geo, failures)
    check_source_urls(geo, ledger, failures)
    check_grammar(known | {ref for _, ref in references}, failures)

    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        print(f"check_refs: {len(failures)} failure(s)", file=sys.stderr)
        return 1
    print(f"check_refs: {len(references)} references resolve against {len(known)} defined ids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
