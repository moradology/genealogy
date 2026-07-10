#!/usr/bin/env python3
"""Generate .generations blocks in index.html from the family truth stores.

A layout block (research/people/layout.jsonl) names one branch block's
generation structure: labels and the exact order of person cards, gap cards,
and inline stems. Card content comes from display blocks on people.jsonl /
relationships.jsonl rows, record cards from evidence display blocks, titles
and ahnen labels from the shared derive-by-rule model (family_display) with
store overrides where the rule misses, and stem tags from the live
relationship chain. One keyed marker pair per block:
<!-- BEGIN family-block:ID --> ... <!-- END -->.

Bootstrap bar is CONTENT-FAITHFUL, not identical: every visible word and
every link target of the hand-authored region must survive into the
generated region; presentation may improve. Words change only through store
edits - a hand region carrying words the store does not is a refusal, never
a silent replacement. Zero writes on any validation failure.

Run: uv run tools/build_family.py [--root PATH] [--check]
"""

from __future__ import annotations

import argparse
import html as html_module
import json
import re
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_docket  # noqa: E402
import family_display  # noqa: E402
from build_people_index import ProjectionError  # noqa: E402

LAYOUT_PATH = "research/people/layout.jsonl"
PEOPLE_PATH = "research/people/people.jsonl"
RELATIONSHIPS_PATH = "research/people/relationships.jsonl"
STEMS_PATH = "research/people/stems.jsonl"
EVIDENCE_DIR = "research/evidence"
LAYOUT_FIELDS = ("id", "node_type", "section", "anchor_class", "generations")
ANCHOR_CLASSES = ("zimmerman", "mundell", "dible", "connelly")
GEN_LABEL_RE = re.compile(r"Gen \d(?:-\d)?")
LAYOUT_ID_RE = re.compile(r"layout\.[a-z0-9][a-z0-9._-]*")
HREF_RE = re.compile(r'href="?([^"\s>]+)"?')
MARKER_KEY_RE = re.compile(r"<!-- BEGIN family-block:([^ ]+) -->")
DIV_EDGE_RE = re.compile(r"<div\b|</div>")


def fail(message: str) -> NoReturn:
    raise ProjectionError(message)


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_layout(root: Path) -> list[dict]:
    blocks = read_jsonl(root / LAYOUT_PATH)
    seen_ids: set[str] = set()
    seen_items: set[str] = set()
    for block in blocks:
        where = f"layout.jsonl {block.get('id')!r}"
        block_id = block.get("id")
        if not isinstance(block_id, str) or not LAYOUT_ID_RE.fullmatch(block_id):
            fail(f"{where}: id must match layout.[a-z0-9][a-z0-9._-]*")
        if block_id in seen_ids:
            fail(f"{where}: duplicate layout id")
        seen_ids.add(block_id)
        if block.get("node_type") != "layout_block":
            fail(f"{where}: node_type must be 'layout_block'")
        if set(block) != set(LAYOUT_FIELDS):
            fail(f"{where}: fields must be exactly {sorted(LAYOUT_FIELDS)}")
        if block.get("anchor_class") not in ANCHOR_CLASSES:
            fail(f"{where}: anchor_class must be one of {list(ANCHOR_CLASSES)}")
        generations = block.get("generations")
        if not isinstance(generations, list) or not generations:
            fail(f"{where}: generations must be a non-empty list")
        for generation in generations:
            if (not isinstance(generation, dict)
                    or set(generation) != {"label", "items"}):
                fail(f"{where}: each generation is {{label, items}}")
            if not isinstance(generation.get("label"), str) \
                    or not GEN_LABEL_RE.fullmatch(generation["label"]):
                fail(f"{where}: generation label {generation.get('label')!r} "
                     "must match 'Gen N' or 'Gen N-M'")
            items = generation.get("items")
            if not isinstance(items, list) or not items:
                fail(f"{where}: generation items must be a non-empty list")
            for item in items:
                if not isinstance(item, str) or not item:
                    fail(f"{where}: layout items must be non-empty strings")
                if item in seen_items:
                    fail(f"{where}: item {item!r} appears in more than one "
                         "layout position")
                seen_items.add(item)
    return blocks


def load_evidence_displays(root: Path) -> dict[str, dict]:
    displays: dict[str, dict] = {}
    for path in sorted((root / EVIDENCE_DIR).glob("*.jsonl")):
        for row in read_jsonl(path):
            display = row.get("display")
            evidence_id = row.get("id")
            if isinstance(evidence_id, str) and isinstance(display, dict):
                displays[evidence_id] = display
    return displays


def substituted_members(members: list[dict], row_id: str,
                        card_name: str | None) -> list[dict]:
    if not card_name:
        return members
    return [{**member, "n": card_name} if member.get("i") == row_id else member
            for member in members]


def render_card(item: str, *, groups: dict[str, list[dict]],
                people: dict[str, dict], gaps: dict[str, dict],
                evidence_displays: dict[str, dict], anchor_class: str,
                cite_codes: dict[str, str]) -> str:
    is_gap = item.startswith("gap.")
    row = gaps.get(item) if is_gap else people.get(item)
    if row is None:
        fail(f"layout item {item!r} has no store row")
    display = row.get("display")
    if not isinstance(display, dict):
        fail(f"layout item {item!r} has no display block")
    members = groups.get(item)
    if not members:
        fail(f"layout item {item!r} has no people-index registry group")
    title_override = display.get("title_override")
    if isinstance(title_override, str) and title_override:
        title_html = family_display.render_prose(title_override, cite_codes)
    else:
        derived = family_display.derived_title(
            substituted_members(members, item, display.get("card_name")))
        if not derived:
            fail(f"layout item {item!r}: title is underivable and no "
                 "title_override is set")
        title_html = html_module.escape(derived, quote=False)
    ahnen_text = display.get("ahnen_override")
    if not ahnen_text:
        ahnen_text = family_display.derived_ahnen(members)
    if not ahnen_text:
        # Slotless cards degrade gracefully: a rejected link that vacates a
        # pedigree slot must not strand the card or block the write path.
        ahnen_text = "frontier" if is_gap else "(collateral)"
    tag = "open" if is_gap else row.get("confidence")
    record_cards_html = ""
    for ref in display.get("record_cards") or []:
        card_display = evidence_displays.get(ref)
        if card_display is None:
            fail(f"layout item {item!r}: record card {ref!r} has no evidence "
                 "display block")
        record_cards_html += family_display.render_record_card(
            ref, card_display, anchor_class)
    return family_display.render_person_card(
        row_id=item, title_html=title_html,
        ahnen_text=html_module.escape(ahnen_text, quote=False), tag=tag,
        display=display, cite_map=cite_codes,
        record_cards_html=record_cards_html,
        alias_ids=tuple(display.get("alias_anchors") or []))


def render_block(block: dict, context: dict) -> str:
    generations: list[str] = []
    for generation in block["generations"]:
        items_html: list[str] = []
        for item in generation["items"]:
            if item.startswith("stem."):
                stem_row = context["stems"].get(item)
                if stem_row is None:
                    fail(f"layout item {item!r} has no stems.jsonl row")
                items_html.append(family_display.render_stem(
                    stem_row, context["people"], context["links"]))
            else:
                items_html.append(render_card(
                    item, groups=context["groups"], people=context["people"],
                    gaps=context["gaps"],
                    evidence_displays=context["evidence_displays"],
                    anchor_class=block["anchor_class"],
                    cite_codes=context["cite_codes"]))
        generations.append(
            '<div class="generation"><div class="gen-label">'
            f'{html_module.escape(generation["label"], quote=False)}</div>'
            f'<div class="people">{"".join(items_html)}</div></div>')
    return "\n".join(generations)


def div_span(source: str, open_index: int) -> int:
    """Index just past the </div> closing the div that opens at open_index."""
    depth = 0
    for match in DIV_EDGE_RE.finditer(source, open_index):
        if match.group(0) == "<div":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return source.index(">", match.start()) + 1
    fail("index.html: unbalanced <div> nesting while locating a generations block")


def region_hrefs(fragment: str) -> list[str]:
    return sorted(HREF_RE.findall(fragment))


def splice(source: str, blocks: list[dict], rendered: dict[str, str]) -> str:
    if source.count("<!-- BEGIN ") != source.count("<!-- END -->"):
        fail("index.html BEGIN/END marker counts diverge; a marker was added "
             "or removed by hand - refusing to splice anything")
    marker_keys = MARKER_KEY_RE.findall(source)
    marked = {block["id"] for block in blocks if block["id"] in set(marker_keys)}
    orphans = [key for key in marker_keys
               if key not in {block["id"] for block in blocks}]
    if orphans:
        fail(f"index.html carries family-block markers with no layout row: {orphans}")
    updated = source
    for block in blocks:
        if block["id"] not in marked:
            continue
        pattern = re.compile(
            rf"(<!-- BEGIN family-block:{re.escape(block['id'])} -->).*?"
            r"(<!-- END -->)", re.S)
        matches = list(pattern.finditer(updated))
        if len(matches) != 1:
            fail(f"index.html has {len(matches)} marker pairs for "
                 f"{block['id']!r}; markers and store have diverged")
        match = matches[0]
        interior = updated[match.end(1): match.start(2)]
        if "<!--" in interior:
            fail(f"index.html family-block region for {block['id']!r} is "
                 "malformed (a marker was edited or removed); refusing to splice")
        updated = (updated[: match.end(1)] + "\n" + rendered[block["id"]]
                   + "\n" + updated[match.start(2):])
    # Bootstrap the unmarked blocks, per section, in reverse document order.
    pending = [block for block in blocks if block["id"] not in marked]
    by_section: dict[str, list[dict]] = {}
    for block in pending:
        by_section.setdefault(block["section"], []).append(block)
    for section_id, section_blocks in by_section.items():
        section_open = updated.find(f'id="{section_id}"')
        if section_open == -1:
            fail(f"index.html has no section {section_id!r}")
        section_end = updated.find("</section>", section_open)
        spans: list[tuple[int, int]] = []
        cursor = section_open
        while True:
            open_index = updated.find('<div class="generations">', cursor,
                                      section_end)
            if open_index == -1:
                break
            close_index = div_span(updated, open_index)
            spans.append((open_index, close_index))
            cursor = close_index
        if len(spans) < len(section_blocks):
            fail(f"{section_id}: {len(section_blocks)} layout blocks but only "
                 f"{len(spans)} .generations blocks on the page")
        for block, (open_index, close_index) in reversed(
                list(zip(section_blocks, spans))):
            open_end = updated.index(">", open_index) + 1
            close_start = updated.rindex("</div>", open_end, close_index)
            old_interior = updated[open_end:close_start]
            new_interior = rendered[block["id"]]
            old_text = family_display.visible_text(old_interior)
            new_text = family_display.visible_text(new_interior)
            if old_text != new_text:
                fail(f"bootstrap {block['id']}: the hand region's words differ "
                     "from the store render; refusing to replace words the "
                     "store does not carry")
            if region_hrefs(old_interior) != region_hrefs(new_interior):
                fail(f"bootstrap {block['id']}: the hand region's link targets "
                     "differ from the store render; refusing")
            replacement = (f"<!-- BEGIN family-block:{block['id']} -->\n"
                           f"{new_interior}\n<!-- END -->")
            updated = (updated[:open_end] + replacement
                       + updated[close_start:])
    return updated


def build(root: Path) -> tuple[str, str, int]:
    blocks = load_layout(root)
    people = {row["id"]: row for row in read_jsonl(root / PEOPLE_PATH)}
    family_rows = read_jsonl(root / RELATIONSHIPS_PATH)
    gaps = {row["id"]: row for row in family_rows
            if row.get("node_type") == "gap"}
    links = [row for row in family_rows
             if row.get("node_type") == "relationship"]
    stems_rows = {row["id"]: row for row in read_jsonl(root / STEMS_PATH)}
    source = (root / "index.html").read_text(encoding="utf-8")
    registry = build_docket.people_index(source)
    context = {
        "people": people,
        "gaps": gaps,
        "links": links,
        "stems": stems_rows,
        "groups": family_display.registry_groups(list(registry.values())),
        "evidence_displays": load_evidence_displays(root),
        "cite_codes": family_display.cite_map(root),
    }
    rendered = {block["id"]: render_block(block, context) for block in blocks}
    return source, splice(source, blocks, rendered), len(blocks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    original, updated, count = build(args.root)
    html_path = args.root / "index.html"
    if args.check:
        if original != updated:
            print(f"{html_path} family projection is out of date; "
                  "run ./gen build family")
            return 1
        print(f"family projection current: {count} blocks")
        return 0
    if original != updated:
        html_path.write_text(updated, encoding="utf-8")
        print(f"family projection written: {count} blocks")
    else:
        print(f"family projection unchanged: {count} blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
