#!/usr/bin/env python3
"""Verify that every cross-reference resolves to a canonical definition.

Person identity has one source: research/people/people.jsonl. HTML and
GeoJSON person tokens are references to that store and can never define a
person. Canonical gaps come from relationships.jsonl; case/event anchors remain
public projections; feature/place/source definitions retain their existing
stores. Retired person ids are forbidden even if they appear in a projection.

The checker also enforces unique GeoJSON feature ids, parity between map link
records and familyLinkData, valid map endpoints, and source-ledger URL closure.

Run: uv run tools/check_refs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ID_RE = re.compile(r"\b(src|event|person|place|case|gap)\.[A-Za-z0-9_.-]+\b")
# Keep this identical to the canonical family-core grammar. Projections do not
# get to retain a narrower legacy spelling rule.
PERSON_GRAMMAR = re.compile(r"person\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
CASE_GRAMMAR = re.compile(r"case\.\d{2}\Z")
GAP_GRAMMAR = re.compile(r"gap\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
# Person tokens can appear inside prose fields (evidence_note,
# research_question, exclusion_note, ...), not just id-typed fields, so
# this is matched against every string value rather than plucked by key.
PERSON_TOKEN_RE = re.compile(r"\bperson\.[A-Za-z0-9_.-]+\b")
# Strips URL spans before the person-token scan, so a source_refs URL like
# ".../person.php?..." stays inert (the whole value is one URL span, so
# nothing is left to match) while prose combining a URL and a person
# mention -- "see https://x/y and person.ghost" -- still surfaces the
# person token. \S* is bounded by whitespace rather than "://", so it
# consumes the full URL (path, query, fragment) without reaching into
# separate words on either side.
URL_SPAN_RE = re.compile(r"\S*://\S*")

# Old person.* ids retired by past renames (Slate 1 W1's grammar cutover,
# 26 ids; plus six ids folded together by later data repairs). A retired
# id must never resurface in canonical data or a projection. The mapping names
# the replacement for a useful failure message; it is not an alias resolver.
RETIRED_TO_CANONICAL = {
    "person.doyle_jule_zimmerman": "person.doyle_zimmerman",
    "person.evelyn_delores_mundell": "person.evelyn_mundell",
    "person.william_j_dible": "person.bill_dible",
    "person.donna_lea_connelly": "person.donna_connelly",
    "person.michael_john_zimmerman_sr": "person.zimmerman.michael",
    "person.elizabeth_catherine_nauer": "person.nauer.elizabeth",
    "person.john_paul_zimmerman": "person.zimmerman.john_paul",
    "person.john_zodrow": "person.zodrow.john",
    "person.zodrow.julius": "person.zodrow.julius_collateral",
    "person.thomas_a_nauer": "person.nauer.thomas",
    "person.lorenz_nauer": "person.nauer.lorenz",
    "person.walter_william_mundell": "person.mundell.walter",
    "person.harvey_william_mundell": "person.mundell.harvey",
    "person.talmadge_dewitt_clemans": "person.clemans.talmadge",
    "person.martin_flaherty": "person.flaherty.martin",
    "person.harry_h_dible": "person.dible.harry",
    "person.ray_hershel_dible": "person.dible.ray",
    "person.almeda_ora_long": "person.long.almeda",
    "person.robert_nelson_long": "person.long.robert_nelson",
    "person.dorsey_overturf_mcclelland": "person.mcclelland.dorsey",
    "person.david_monroe_durham": "person.durham.david",
    "person.john_laborn_ford": "person.ford.john_laborn",
    "person.john_burton_staples": "person.staples.john_burton",
    "person.henry_claar": "person.claar.henry",
    "person.samuel_dove_claar": "person.claar.samuel_dove",
    "person.richard_d_haden": "person.haden.richard",
    "person.alexander_m_mcclelland": "person.mcclelland.alexander",
    "person.john_f_rust": "person.rust.john_f",
    "person.john_aissen_rust": "person.rust.john_aissen",
    "person.andrew_jackson_haden": "person.haden.andrew",
    "person.homer_clair_mundell": "person.mundell.homer",
    "person.marjorie_clemans": "person.clemans.marjorie",
    "person.marjorie_clemans_mundell": "person.clemans.marjorie",
    "person.frances_adolph": "person.mary_frances_rust",
    "person.catherine_zinkle": "person.zinkle.catherine",
    "person.rev_robert_long": "person.long.robert_rev",
    "person.betsy_wasson": "person.wasson.betsy",
}
RETIRED_ALIASES = frozenset(RETIRED_TO_CANONICAL)

def canonical_case_ids() -> frozenset[str]:
    """Load the append-only case universe from the canonical JSONL truth."""
    path = ROOT / "research" / "cases" / "cases.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return frozenset(record["id"] for record in records)


# One authoritative Docket registry. New cases land in cases.jsonl first; the
# page, frames, and checkers are projections validated by check_cases.py.
PLANNED_CASES = canonical_case_ids()


def canonical_family_ids(
    root: Path, failures: list[str]
) -> tuple[set[str], set[str]]:
    """Load actual people and gaps from the canonical family JSONL stores."""

    people: set[str] = set()
    gaps: set[str] = set()
    people_path = root / "research/people/people.jsonl"
    relationships_path = root / "research/people/relationships.jsonl"

    if not people_path.is_file():
        failures.append(f"missing canonical person store: {people_path}")
    else:
        for line_number, line in enumerate(
            people_path.read_text(encoding="utf-8").splitlines(), 1
        ):
            where = f"{people_path}:{line_number}"
            if not line.strip():
                failures.append(f"{where}: blank lines are not allowed in JSONL")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"{where}: invalid person JSON: {exc}")
                continue
            if not isinstance(record, dict) or record.get("node_type") != "person":
                failures.append(f"{where}: canonical person record must have node_type 'person'")
                continue
            value = record.get("id")
            if not isinstance(value, str):
                failures.append(f"{where}: canonical person record has no string id")
            elif value in people:
                failures.append(f"{where}: duplicate canonical person id {value}")
            elif value in RETIRED_ALIASES:
                failures.append(
                    f"{where}: retired person id {value} is forbidden; "
                    f"use {RETIRED_TO_CANONICAL[value]} instead"
                )
            else:
                people.add(value)

    if not relationships_path.is_file():
        failures.append(f"missing canonical relationship store: {relationships_path}")
    else:
        for line_number, line in enumerate(
            relationships_path.read_text(encoding="utf-8").splitlines(), 1
        ):
            where = f"{relationships_path}:{line_number}"
            if not line.strip():
                failures.append(f"{where}: blank lines are not allowed in JSONL")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"{where}: invalid relationship JSON: {exc}")
                continue
            if not isinstance(record, dict) or record.get("node_type") != "gap":
                continue
            value = record.get("id")
            if not isinstance(value, str):
                failures.append(f"{where}: canonical gap record has no string id")
            elif value in gaps:
                failures.append(f"{where}: duplicate canonical gap id {value}")
            else:
                gaps.add(value)
    return people, gaps


def iter_person_tokens(value):
    """Recursively yield every person.* token found in string values.

    Walks dicts/lists to reach nested strings (e.g. sequence steps,
    candidate_people arrays). URL spans are stripped from each string
    first (see URL_SPAN_RE) so a URL like ".../person.php?..." (a real
    getperson.php-style pattern seen on genealogy sites) can't be
    mistaken for a person.* id, while a person token elsewhere in the
    same string still surfaces.
    """
    if isinstance(value, str):
        for match in PERSON_TOKEN_RE.finditer(URL_SPAN_RE.sub(" ", value)):
            yield match.group(0).rstrip(".")
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_person_tokens(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_person_tokens(item)


def family_link_block(html: str) -> str:
    start = html.index("const familyLinkData")
    return html[start:html.index("];", start)]


def collect_definitions(
    html: str,
    geo: dict,
    ledger: dict,
    failures: list[str],
    root: Path = ROOT,
) -> set[str]:
    ids: set[str] = set()
    people, gaps = canonical_family_ids(root, failures)
    ids.update(people)
    ids.update(gaps)
    for record in ledger["sources"]:
        ids.add(record["id"])
    for match in re.finditer(r'"id":"(event\.[^"]+)"', html):
        ids.add(match.group(1))
    for match in re.finditer(r'id="(case\.[A-Za-z0-9_.-]+)"', html):
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
    for fid in seen_fids:
        if fid.startswith(("person.", "gap.")):
            failures.append(
                f"geojson feature id {fid} cannot define canonical family identity"
            )
        else:
            ids.add(fid)
    for key in geo.get("place_registry") or {}:
        if not isinstance(key, str):
            continue
        if key.startswith(("person.", "gap.")):
            failures.append(
                f"geojson place_registry key {key} cannot define canonical family identity"
            )
        else:
            ids.add(key)
    return ids


def collect_references(
    html: str, geo: dict, root: Path = ROOT
) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for match in re.finditer(r'id="((?:person|gap)\.[A-Za-z0-9_.-]+)"', html):
        refs.append(("index.html anchor", match.group(1)))
    paths = sorted((root / "research" / "reasoning-traces").glob("*.md"))
    frames_dir = root / "research" / "search-frames"
    if frames_dir.exists():
        paths.extend(sorted(frames_dir.rglob("*.md")))
    for path in paths:
        origin = str(path.relative_to(root))
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
        for token in iter_person_tokens(props):
            refs.append((origin, token))
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
            failures.append(f"person id violates canonical grammar: {value}")
        if value.startswith("case.") and CASE_GRAMMAR.fullmatch(value) is None:
            failures.append(f"case id violates grammar case.NN: {value}")
        if value.startswith("gap.") and GAP_GRAMMAR.fullmatch(value) is None:
            failures.append(f"gap id violates canonical grammar: {value}")


def main() -> int:
    html = (ROOT / "index.html").read_text()
    geo = json.loads((ROOT / "ancestry_geospatial.geojson").read_text())
    ledger = json.loads((ROOT / "research" / "sources" / "source-index.json").read_text())

    failures: list[str] = []
    known = collect_definitions(html, geo, ledger, failures)
    references = collect_references(html, geo)
    for origin, ref in references:
        if ref in RETIRED_ALIASES:
            failures.append(
                f"retired alias {ref} referenced from {origin}; use {RETIRED_TO_CANONICAL[ref]} instead")
            continue
        if ref in known:
            continue
        if ref.startswith("case."):
            if ref not in PLANNED_CASES:
                failures.append(f"UNRESOLVED {ref} referenced from {origin}: unknown case id (not in PLANNED_CASES)")
                continue
        failures.append(f"UNRESOLVED {ref} referenced from {origin}")
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
