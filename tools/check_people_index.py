#!/usr/bin/env python3
"""Verify the Slate 1 people-index registry stays synchronized.

The page now has one JSON people registry used by the pedigree-chart
renderer and the static Index of Names. This checker keeps that registry
closed against index.html: ids are unique, ahnentafel slots are unique
within each anchor, href targets resolve, every rendered person row is
covered by some registry entry, row-owned confidence tags match the
actual .tag class, and docket case refs stay inside case.01-case.21.

Run: uv run tools/check_people_index.py
"""

from __future__ import annotations

import json
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_refs", Path(__file__).with_name("check_refs.py"))
assert SPEC is not None and SPEC.loader is not None
check_refs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_refs)
PLANNED_CASES = check_refs.PLANNED_CASES
TAG_CLASSES = frozenset({"documented", "strong", "lead", "open"})


def people_index_block(html: str, failures: list[str]) -> str:
    blocks = [
        content for attrs, content in
        re.findall(r"<script([^>]*)>(.*?)</script>", html, flags=re.S | re.I)
        if 'type="application/json"' in attrs.lower() and 'id="people-index"' in attrs.lower()
    ]
    if len(blocks) != 1:
        failures.append(f"expected exactly one people-index JSON script, found {len(blocks)}")
        return "{}"
    return blocks[0]


def html_ids(html: str) -> set[str]:
    ids: set[str] = set()
    for quoted, bare in re.findall(r'\sid=(?:"([^"]+)"|([^\s>]+))', html):
        ids.add(quoted or bare)
    return ids


def person_tags(html: str, failures: list[str]) -> dict[str, str]:
    tags: dict[str, str] = {}
    row_re = re.compile(
        r'<div class="person" id="([^"]+)">(.*?)(?=\n\s*<div class="person" id="|\n\s*<div class="stem"|\n\s*</div>\n\s*</div>\n\s*</section>)',
        flags=re.S,
    )
    for person_id, block in row_re.findall(html):
        match = re.search(r'<span class="tag ([^"]+)"', block)
        if not match:
            failures.append(f"{person_id} has no .tag span")
            continue
        classes = [c for c in match.group(1).split() if c in TAG_CLASSES]
        if len(classes) != 1:
            failures.append(f"{person_id} has ambiguous tag classes: {match.group(1)}")
            continue
        tags[person_id] = classes[0]
    return tags


def main() -> int:
    html = (ROOT / "index.html").read_text()
    failures: list[str] = []
    payload = json.loads(people_index_block(html, failures))
    people = payload.get("people", [])
    if payload.get("v") != 1 or not isinstance(people, list):
        failures.append("people-index must be an object with v=1 and a people array")
        people = []

    seen_i: set[str] = set()
    seen_ah: dict[tuple[str, int], str] = {}
    h_values: set[str] = set()
    ids = html_ids(html)
    tags = person_tags(html, failures)

    for index, entry in enumerate(people, start=1):
        if not isinstance(entry, dict):
            failures.append(f"entry {index} is not an object")
            continue
        i = entry.get("i")
        a = entry.get("a")
        h = entry.get("h")
        t = entry.get("t")
        if not isinstance(i, str):
            failures.append(f"entry {index} has no string i")
            continue
        if i in seen_i:
            failures.append(f"duplicate people-index i {i}")
        seen_i.add(i)
        if not isinstance(h, str) or h not in ids:
            failures.append(f"{i} h does not resolve: {h}")
        elif h.startswith("person."):
            h_values.add(h)
        if i == h and i in tags and t != tags[i]:
            failures.append(f"{i} t={t!r} does not match row tag {tags[i]!r}")
        for ah in entry.get("ah", []):
            if not isinstance(ah, int) or not 1 <= ah <= 63:
                failures.append(f"{i} has invalid ah value {ah!r}")
                continue
            key = (a, ah)
            if key in seen_ah:
                failures.append(f"{a}-{ah} claimed by both {seen_ah[key]} and {i}")
            seen_ah[key] = i
        c = entry.get("c")
        if c is not None and c not in PLANNED_CASES:
            failures.append(f"{i} c is outside case.01-case.21: {c}")

    for person_id in sorted(tags):
        if person_id not in h_values:
            failures.append(f"{person_id} person row is missing from people-index h values")

    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        print(f"check_people_index: {len(failures)} failure(s)", file=sys.stderr)
        return 1
    print(f"check_people_index: {len(people)} entries cover {len(tags)} person rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
