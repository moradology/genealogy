#!/usr/bin/env python3
"""Build static marker keys for the map plates in index.html."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"

PLATE_RE = re.compile(
    r'\{\s*key: "([^"]+)", svgId: "([^"]+)", detailId: "([^"]+)", '
    r'base: "([^"]+)", anchor: (null|"[^"]+")(?:,|\s*\})'
)
LINK_RE = re.compile(
    r'\{\s*id: "([^"]+)",\s*anchor: "([^"]+)",\s*from: \[([^\]]*)\],'
    r'\s*to: "([^"]+)",\s*kind: "([^"]+)",\s*label: "([^"]+)"',
    re.S,
)

ANCHOR_SLUG = {
    "Doyle Julius Zimmerman": "zimmerman",
    "Evelyn Delores Mundell Zimmerman": "mundell",
    "William J. Dible": "dible",
    "Donna Lea Connelly Dible": "connelly",
}
ANCHOR_SHORT = {
    "Doyle Julius Zimmerman": "Zimmerman",
    "Evelyn Delores Mundell Zimmerman": "Mundell",
    "William J. Dible": "Dible",
    "Donna Lea Connelly Dible": "Connelly",
}
PLATE_ROMANS = ["II", "III", "IV", "V", "VI"]
LEDGER_ROWS = [
    ("Zimmerman", "zimmerman", 5, "8,158", "", "1869-1954", False),
    ("Nauer", "zimmerman", 6, "1,735", "", "1871-1930", False),
    ("Mundell/Rust", "mundell", 8, "4,547", "", "1837-2023", False),
    ("Dible/Heckman", "dible", 5, "10,779", "~9,100", "1896-2022", False),
    ("Long/Sleight", "dible", 5, "8,096", "~1,300", "1805-1933", False),
    ("Connelly/Durham", "connelly", 10, "5,029", "", "1782-2022", False),
    ("Claar", "connelly", 5, "2,771", "~600", "1838-1935", False),
    ("Nauer parentage", "zimmerman", 4, "1,718", "1,718", "1851-1880", True),
    ("Rust identity", "mundell", 5, "593", "593", "1894-1910", True),
    ("McClelland/Love", "dible", 8, "2,635", "2,635", "1801-1933", True),
    ("Clemans/Flaherty", "mundell", 4, "2,216", "2,216", "1921-2023", True),
]


def extract_between(text: str, start: str, end: str) -> str:
    start_i = text.index(start) + len(start)
    end_i = text.index(end, start_i)
    return text[start_i:end_i]


def parse_events(source: str) -> list[dict[str, object]]:
    block = extract_between(source, "const verifiedEventData = [", "\n    ];")
    events = []
    for line in block.splitlines():
        stripped = line.strip().rstrip(",")
        if stripped.startswith('{"id":"event.'):
            events.append(json.loads(stripped))
    if not events:
        print("build_plate_keys: no verifiedEventData rows parsed", file=sys.stderr)
        raise SystemExit(1)
    return events


def quoted_items(raw: str) -> list[str]:
    return re.findall(r'"([^"]+)"', raw)


def parse_links(source: str) -> list[dict[str, object]]:
    block = extract_between(source, "const familyLinkData = [", "\n    ];")
    links = []
    for match in LINK_RE.finditer(block):
        links.append({
            "id": match.group(1),
            "anchor": match.group(2),
            "from": quoted_items(match.group(3)),
            "to": match.group(4),
            "kind": match.group(5),
            "label": match.group(6),
        })
    if not links:
        print("build_plate_keys: no familyLinkData rows parsed", file=sys.stderr)
        raise SystemExit(1)
    return links


def parse_plates(source: str) -> list[dict[str, str | None]]:
    block = extract_between(source, "const PLATES = [", "\n    ];")
    plates = []
    for match in PLATE_RE.finditer(block):
        raw_anchor = match.group(5)
        anchor = None if raw_anchor == "null" else raw_anchor.strip('"')
        plates.append({
            "key": match.group(1),
            "svgId": match.group(2),
            "detailId": match.group(3),
            "base": match.group(4),
            "anchor": anchor,
        })
    if len(plates) != 5:
        print(f"build_plate_keys: parsed {len(plates)} plate configs, expected 5", file=sys.stderr)
        raise SystemExit(1)
    return plates


def parse_js_object_numbers(source: str, const_name: str) -> dict[str, float]:
    match = re.search(rf"const {const_name} = \{{([^}}]+)\}};", source)
    if not match:
        print(f"build_plate_keys: {const_name} not found", file=sys.stderr)
        raise SystemExit(1)
    values: dict[str, float] = {}
    for key, value in re.findall(r"(\w+): (-?\d+(?:\.\d+)?)", match.group(1)):
        values[key] = float(value)
    return values


def in_kansas(event: dict[str, object], ks_proj: dict[str, float]) -> bool:
    lon, lat = event["coords"]
    return (
        lon >= ks_proj["lonMin"] and lon <= ks_proj["lonMax"]
        and lat >= ks_proj["latMin"] and lat <= ks_proj["latMax"]
    )


def compare_key(event: dict[str, object]) -> tuple[str, str]:
    return str(event["sort"]), str(event["id"])


def plate_data(
    cfg: dict[str, str | None],
    events: list[dict[str, object]],
    links: list[dict[str, object]],
    ks_proj: dict[str, float],
) -> tuple[list[dict[str, object]], set[str]]:
    anchor = cfg["anchor"]
    if anchor is None:
        return sorted([event for event in events if in_kansas(event, ks_proj)], key=compare_key), set()

    own = [event for event in events if event["anchor"] == anchor]
    own_ids = {str(event["id"]) for event in own}
    linked = [
        link for link in links
        if link["anchor"] == anchor
        or any(event_id in own_ids for event_id in link["from"])
        or link["to"] in own_ids
    ]
    wanted = set(own_ids)
    for link in linked:
        wanted.update(str(event_id) for event_id in link["from"])
        wanted.add(str(link["to"]))
    selected = sorted([event for event in events if event["id"] in wanted], key=compare_key)
    return selected, {str(event["id"]) for event in selected if event["id"] not in own_ids}


def text(value: object) -> str:
    return html.escape(str(value), quote=False)


def confidence_label(event: dict[str, object]) -> str:
    if event["confidence"] == "documented":
        return "documented"
    return "strong lead"


def type_label(event: dict[str, object]) -> str:
    return str(event["type"]).replace("_", " ")


def line_suffix(event: dict[str, object], cfg: dict[str, str | None], guest_ids: set[str]) -> str:
    event_id = str(event["id"])
    if cfg["anchor"] is None or event_id not in guest_ids:
        return ""
    anchor = str(event["anchor"])
    slug = ANCHOR_SLUG[anchor]
    label = ANCHOR_SHORT[anchor]
    return f' · <span class=anchor-text-{slug}>{label} line</span>'


def key_markup(cfg: dict[str, str | None], rows: list[dict[str, object]], guest_ids: set[str]) -> str:
    label = text(f"{cfg['key']} marker key")
    parts = [f'        <ol class=plate-key aria-label="{label}">']
    for index, event in enumerate(rows, start=1):
        parts.append(
            f'<li data-e={text(event["id"])}>'
            f'<b>{index}</b>'
            f'<time>{text(event["date"])}</time> '
            f'{text(type_label(event))} · {text(event["person"])} · '
            f'{text(event["place"])} · <i>{confidence_label(event)}</i>'
            f'{line_suffix(event, cfg, guest_ids)}</li>'
        )
    parts.append("</ol>")
    return "".join(parts)


def replace_existing_block(source: str, key: str, markup: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"(        <!-- BEGIN plate-key:{re.escape(key)} -->\n)"
        rf".*?"
        rf"(\n        <!-- END -->)",
        re.S,
    )
    replaced, count = pattern.subn(rf"\1{markup}\2", source)
    return replaced, count > 0


def insert_new_block(source: str, detail_id: str, key: str, markup: str) -> str:
    needle = f'        <div class="plate-detail" id="{detail_id}"></div>'
    block = (
        f'{needle}\n'
        f'        <!-- BEGIN plate-key:{key} -->\n'
        f'{markup}\n'
        f'        <!-- END -->'
    )
    if needle not in source:
        print(f"build_plate_keys: detail region {detail_id} not found", file=sys.stderr)
        raise SystemExit(1)
    return source.replace(needle, block, 1)


def stamp_plate_numbers(source: str) -> str:
    index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal index
        if index >= len(PLATE_ROMANS):
            print("build_plate_keys: more plate-no spans than known plate numerals", file=sys.stderr)
            raise SystemExit(1)
        roman = PLATE_ROMANS[index]
        index += 1
        return f"{match.group(1)}Plate {roman}.{match.group(2)}"

    rendered = re.sub(r'(<span class="plate-no">).*?(</span>)', replace, source)
    if index != len(PLATE_ROMANS):
        print(f"build_plate_keys: stamped {index} plate numerals, expected {len(PLATE_ROMANS)}", file=sys.stderr)
        raise SystemExit(1)
    return rendered


def ledger_markup() -> str:
    rows = []
    for name, slug, waypoints, km, conj, years, maybe in LEDGER_ROWS:
        prefix = "? " if maybe else ""
        row_class = " class=conjectural" if maybe else ""
        rows.append(
            f"<tr{row_class}><td>{prefix}<span class=anchor-text-{slug}>{name}</span></td>"
            f"<td>{waypoints}</td><td>{km}</td><td>{conj}</td><td>{years}</td></tr>"
        )
    return (
        '<figure class=ledger-table><figcaption>Table of Removes · leg distances are great-circle '
        'kilometres between recorded waypoints</figcaption><div class=table-scroll><table><thead><tr>'
        '<th>Route</th><th>Wp</th><th>Km</th><th>Conj. km</th><th>Years</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div></figure>"
    )


def replace_or_insert_ledger(source: str) -> str:
    markup = ledger_markup()
    pattern = re.compile(r"(      <!-- BEGIN miles-ledger -->\n).*?(\n      <!-- END -->)", re.S)
    rendered, count = pattern.subn(rf"\1{markup}\2", source)
    if count:
        return rendered
    needle = '      <p class="small">Full coordinates, confidence labels, open targets, and geospatial records live in <a href="ancestry_geospatial.geojson">ancestry_geospatial.geojson</a>.</p>'
    block = f"      <!-- BEGIN miles-ledger -->\n{markup}\n      <!-- END -->\n{needle}"
    if needle not in source:
        print("build_plate_keys: map coordinates paragraph not found for miles ledger", file=sys.stderr)
        raise SystemExit(1)
    return source.replace(needle, block, 1)


def render(source: str) -> str:
    events = parse_events(source)
    links = parse_links(source)
    plates = parse_plates(source)
    ks_proj = parse_js_object_numbers(source, "KS_PROJ")
    rendered = source
    for cfg in plates:
        rows, guest_ids = plate_data(cfg, events, links, ks_proj)
        markup = key_markup(cfg, rows, guest_ids)
        rendered, found = replace_existing_block(rendered, str(cfg["key"]), markup)
        if not found:
            rendered = insert_new_block(rendered, str(cfg["detailId"]), str(cfg["key"]), markup)
    rendered = replace_or_insert_ledger(rendered)
    return stamp_plate_numbers(rendered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if plate keys are out of date")
    args = parser.parse_args()

    original = HTML_PATH.read_text()
    rendered = render(original)
    if args.check:
        if original != rendered:
            print(f"{HTML_PATH} plate keys, ledger, or numerals are out of date; run uv run tools/build_plate_keys.py", file=sys.stderr)
            return 1
        print(f"{HTML_PATH} plate keys, ledger, and numerals are current")
        return 0

    HTML_PATH.write_text(rendered)
    print(f"updated {HTML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
