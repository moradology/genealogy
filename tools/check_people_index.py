#!/usr/bin/env python3
"""Verify the public people projection is current and internally closed.

Family structure is validated by ``check_family_core.py`` and projected by
``build_people_index.py``.  This presentation check deliberately has no legacy
HTML-registry parser: the embedded JSON and name index must be byte-for-byte
derived from the canonical JSONL stores.
"""

from __future__ import annotations

import re
import sys

import build_people_index


def main() -> int:
    failures: list[str] = []
    try:
        original, rendered, payload = build_people_index.build(
            build_people_index.ROOT
        )
    except build_people_index.ProjectionError as exc:
        print(f"check_people_index: {exc}", file=sys.stderr)
        return 1

    if original != rendered:  # dicts: any page drift
        failures.append(
            "generated people blocks drifted; run uv run tools/build_people_index.py"
        )

    entries = payload.get("people")
    if payload.get("v") != 2 or not isinstance(entries, list):
        failures.append("people-index must be the v2 individual projection")
        entries = []

    occupied: dict[tuple[str, int], str] = {}
    hrefs: set[str] = set()
    for entry in entries:
        identifier = entry.get("i")
        kind = entry.get("k")
        name = entry.get("n")
        anchor = entry.get("h")
        if kind not in {"person", "gap"}:
            failures.append(f"{identifier} has invalid projection kind {kind!r}")
        if kind == "person" and isinstance(name, str) and " + " in name:
            failures.append(f"{identifier} still combines multiple people")
        if isinstance(anchor, str):
            hrefs.add(anchor)
        for slot in entry.get("ah", []):
            key = (entry.get("a"), slot)
            if key in occupied:
                failures.append(
                    f"{key[0]}-{key[1]} is owned by both {occupied[key]} and {identifier}"
                )
            else:
                occupied[key] = str(identifier)

    row_ids = set(
        re.findall(r'<div class="person" id="((?:person|gap)\.[^"]+)"',
                   "\n".join(original.values()))
    )
    missing_rows = sorted(row_ids - hrefs)
    if missing_rows:
        failures.append(
            "public family rows missing from the canonical projection: "
            + ", ".join(missing_rows)
        )

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(
            f"check_people_index: {len(failures)} failure(s)", file=sys.stderr
        )
        return 1
    print(
        f"check_people_index: {len(entries)} canonical entries; "
        f"{len(occupied)} pedigree slots; {len(row_ids)} public rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
