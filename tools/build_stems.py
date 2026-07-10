#!/usr/bin/env python3
"""Generate the descent-stem divs in index.html from research/people/stems.jsonl.

A stem is curated presentation of a descent chain. The editorial words (from
label, via prose, link text, line label, note suffix, short-name overrides)
are store data; the confidence tag and the weakest-step pair are COMPUTED from
the family core via family_rules.parent_chains/weakest_parent_step, so a
relationship edit that weakens a chain reddens --check and regenerates the tag
and note. If that moves a value pinned by acceptance C10, the gate goes red
for a conscious owner ratchet - never silent drift.

First run bootstraps: it finds the hand-authored <div class="stem"> elements
in document order, refuses unless the store rows match them one-to-one on
target anchors, then wraps each in keyed markers
<!-- BEGIN stem:ID -->...<!-- END -->. Later runs splice by key. Once a stem
is claimed by a layout block in research/people/layout.jsonl it is skipped
here (build_family renders it) until this builder retires.

Store text is plain unicode (no raw '<', no HTML entities); escaping happens
once at render. Run: uv run tools/build_stems.py [--root PATH] [--check]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import family_rules  # noqa: E402

STEMS_PATH = "research/people/stems.jsonl"
PEOPLE_PATH = "research/people/people.jsonl"
RELATIONSHIPS_PATH = "research/people/relationships.jsonl"
LAYOUT_PATH = "research/people/layout.jsonl"
TAG_LABELS = {"documented": "Documented", "strong": "Strong lead",
              "lead": "Working lead", "open": "Open edge"}
REQUIRED_FIELDS = ("id", "node_type", "anchor", "target", "from_label",
                   "via_prose", "link_text", "line_label")
OPTIONAL_FIELDS = ("note_suffix", "short_names")
TEXT_FIELDS = ("from_label", "via_prose", "link_text", "line_label", "note_suffix")
ENTITY_RE = re.compile(r"&#?[a-zA-Z0-9]+;")
HAND_STEM_RE = re.compile(r'<div class="stem">.*?</div>')
MARKER_KEY_RE = re.compile(r"<!-- BEGIN stem:([^ ]+) -->")
HREF_RE = re.compile(r'href="#([^"]+)"')
STEM_ID_RE = re.compile(r"stem\.[a-z0-9][a-z0-9._-]*")
TAG_STRIP_RE = re.compile(r"<[^>]+>")


def visible_text(fragment: str) -> str:
    """Collapse a fragment to its space-normalized, entity-decoded text."""
    return " ".join(html.unescape(TAG_STRIP_RE.sub(" ", fragment)).split())


def fail(message: str) -> NoReturn:
    print(message)
    raise SystemExit(1)


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def text(value: str) -> str:
    return html.escape(value, quote=False)


def validate_rows(rows: list[dict], people: dict[str, dict]) -> None:
    seen: set[str] = set()
    for row in rows:
        where = f"stems.jsonl {row.get('id')!r}"
        row_id = row.get("id")
        if not isinstance(row_id, str) or not STEM_ID_RE.fullmatch(row_id):
            fail(f"{where}: id must match stem.[a-z0-9][a-z0-9._-]*")
        if row_id in seen:
            fail(f"{where}: duplicate stem id")
        seen.add(row_id)
        if row.get("node_type") != "stem":
            fail(f"{where}: node_type must be 'stem'")
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        unknown = [field for field in row
                   if field not in REQUIRED_FIELDS and field not in OPTIONAL_FIELDS]
        if missing:
            fail(f"{where}: missing fields {missing}")
        if unknown:
            fail(f"{where}: unknown fields {unknown}")
        for field in TEXT_FIELDS:
            value = row.get(field)
            if value is None and field in OPTIONAL_FIELDS:
                continue
            if not isinstance(value, str) or not value:
                fail(f"{where}: {field} must be a non-empty string")
            if "<" in value:
                fail(f"{where}: {field} must not contain raw HTML ('<')")
            if ENTITY_RE.search(value):
                fail(f"{where}: {field} must hold plain unicode, not HTML entities")
        for field in ("anchor", "target"):
            value = row.get(field)
            if value not in people:
                fail(f"{where}: {field} {value!r} is not a known person id")
        short_names = row.get("short_names")
        if short_names is not None:
            if not isinstance(short_names, dict) or not short_names:
                fail(f"{where}: short_names must be a non-empty object when present")
            for pid, label in short_names.items():
                if pid not in people:
                    fail(f"{where}: short_names key {pid!r} is not a known person id")
                if not isinstance(label, str) or not label:
                    fail(f"{where}: short_names[{pid!r}] must be a non-empty string")


def short_name(row: dict, people: dict[str, dict], person_id: str) -> str:
    override = (row.get("short_names") or {}).get(person_id)
    if isinstance(override, str) and override:
        return override
    return people[person_id]["display_name"].split()[0]


def render_stem(row: dict, people: dict[str, dict], links: list[dict]) -> str:
    where = f"stems.jsonl {row['id']!r}"
    chains = family_rules.parent_chains(links, row["anchor"], row["target"])
    if not chains:
        fail(f"{where}: no upward parent chain from {row['anchor']} to {row['target']}")
    if len(chains) > 1:
        fail(f"{where}: {len(chains)} distinct chains from {row['anchor']} to "
             f"{row['target']}; stems require exactly one")
    for link in chains[0]:
        if link.get("status") != "accepted":
            fail(f"{where}: chain link {link.get('id')!r} has status "
                 f"{link.get('status')!r}; a descent stem may only claim a "
                 "fully accepted chain")
    weakest = family_rules.weakest_parent_step(chains[0])
    confidence = weakest.get("confidence")
    if confidence not in TAG_LABELS:
        fail(f"{where}: weakest link {weakest.get('id')!r} has unknown "
             f"confidence {confidence!r}")
    pair = (f"{text(short_name(row, people, weakest['person_b']))}"
            f"–{text(short_name(row, people, weakest['person_a']))}")
    note = f"weakest step: {pair}"
    suffix = row.get("note_suffix")
    if suffix:
        note += f", {text(suffix)}"
    href = "#" + people[row["target"]]["public_anchor"]
    return (
        '<div class="stem"><span class="stem-label">descent</span> '
        f'{text(row["from_label"])} <span class="stem-arrow">→</span> '
        f'{text(row["via_prose"])} <a href="{href}">{text(row["link_text"])}</a> '
        f'<span class="stem-arrow">→</span> {text(row["line_label"])} '
        f'<span class="tag {confidence}">{TAG_LABELS[confidence]}</span> '
        f'<span class="stem-note">{note}</span></div>'
    )


def splice(source: str, rows: list[dict], rendered: dict[str, str],
           people: dict[str, dict]) -> str:
    marker_keys = MARKER_KEY_RE.findall(source)
    if marker_keys:
        store_ids = {row["id"] for row in rows}
        orphans = [key for key in marker_keys if key not in store_ids]
        if orphans:
            fail(f"index.html carries stem markers with no store row: {orphans}")
        updated = source
        for row in rows:
            pattern = re.compile(
                rf"(<!-- BEGIN stem:{re.escape(row['id'])} -->).*?(<!-- END -->)",
                re.S)
            matches = list(pattern.finditer(updated))
            if len(matches) != 1:
                fail(f"index.html has {len(matches)} marker pairs for {row['id']!r}; "
                     "markers and store have diverged")
            match = matches[0]
            interior = updated[match.end(1): match.start(2)]
            if ("<!--" in interior
                    or not interior.startswith('<div class="stem">')
                    or not interior.endswith("</div>")):
                fail(f"index.html stem region for {row['id']!r} is malformed "
                     "(a marker was edited or removed by hand); refusing to splice")
            updated = (updated[: match.end(1)] + rendered[row["id"]]
                       + updated[match.start(2):])
        return updated
    if not rows:
        # Every stem is claimed by a layout block (build_family renders them
        # inline); nothing here to manage and no markers to bootstrap.
        return source
    hand = list(HAND_STEM_RE.finditer(source))
    if len(hand) != len(rows):
        fail(f"bootstrap: index.html has {len(hand)} hand stems but stems.jsonl "
             f"has {len(rows)} rows; they must match one-to-one in order")
    for position, (match, row) in enumerate(zip(hand, rows), start=1):
        href_match = HREF_RE.search(match.group(0))
        expected = people[row["target"]]["public_anchor"]
        if not href_match or href_match.group(1) != expected:
            fail(f"bootstrap: hand stem {position} targets "
                 f"#{href_match.group(1) if href_match else '?'} but store row "
                 f"{row['id']!r} resolves to #{expected}")
        hand_text = visible_text(match.group(0))
        rendered_text = visible_text(rendered[row["id"]])
        if hand_text != rendered_text:
            fail(f"bootstrap: hand stem {position} reads {hand_text!r} but store "
                 f"row {row['id']!r} renders {rendered_text!r}; refusing to "
                 "replace words the store does not carry")
    updated = source
    for match, row in reversed(list(zip(hand, rows))):
        block = (f"<!-- BEGIN stem:{row['id']} -->{rendered[row['id']]}"
                 "<!-- END -->")
        updated = updated[: match.start()] + block + updated[match.end():]
    return updated


def claimed_by_layout(root: Path) -> set[str]:
    layout_path = root / LAYOUT_PATH
    if not layout_path.exists():
        return set()
    claimed: set[str] = set()
    for block in read_jsonl(layout_path):
        for generation in block.get("generations") or []:
            for item in generation.get("items") or []:
                if isinstance(item, str) and item.startswith("stem."):
                    claimed.add(item)
    return claimed


def build(root: Path) -> tuple[str, str, int]:
    people = {row["id"]: row for row in read_jsonl(root / PEOPLE_PATH)}
    links = [row for row in read_jsonl(root / RELATIONSHIPS_PATH)
             if row.get("node_type") == "relationship"]
    rows = read_jsonl(root / STEMS_PATH)
    validate_rows(rows, people)
    claimed = claimed_by_layout(root)
    rows = [row for row in rows if row["id"] not in claimed]
    rendered = {row["id"]: render_stem(row, people, links) for row in rows}
    source = (root / "index.html").read_text(encoding="utf-8")
    return source, splice(source, rows, rendered, people), len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    original, updated, count = build(args.root)
    html_path = args.root / "index.html"
    if args.check:
        if original != updated:
            print(f"{html_path} stems projection is out of date; run ./gen build stems")
            return 1
        print(f"stems projection current: {count} stems")
        return 0
    if original != updated:
        html_path.write_text(updated, encoding="utf-8")
        print(f"stems projection written: {count} stems")
    else:
        print(f"stems projection unchanged: {count} stems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
