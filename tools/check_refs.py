#!/usr/bin/env python3
"""Verify the cross-reference id universe is closed.

Definitions and references are kept strictly apart, so a typo in a
reference can no longer define itself (the flaw in the previous version
of this checker). Definitions: verifiedEventData ids and person./case.
anchors in index.html, geojson feature-level ids, the geojson top-level
place_registry (top level, not metadata -- the old path silently read
nothing), the frozen RESIDUAL_PERSONS set (union spouses/collaterals with
no HTML card), and the source ledger. References: research markdown
(reasoning traces and search frames), geojson link endpoints and route
sequences, every geojson person.* token (must resolve to an HTML anchor
or a residual), and the familyLinkData block in index.html.

Also enforced: geojson feature ids unique; familyLinkData ids match
geojson link_id set exactly; familyLinkData endpoints resolve to
verifiedEventData (the map runtime draws only those); every geojson
source_refs URL is in the ledger; ledger URLs unique; id grammar for
person.* and case.*; RESIDUAL_PERSONS is exactly the set of geojson
person.* tokens with no HTML anchor -- no stale entries, no entries
that have quietly gained a card; RETIRED_ALIASES (ids renamed away from
in past slates) may never resurface in a geojson token or a trace/frame
reference, and can't be laundered back in through RESIDUAL_PERSONS;
case.* refs must name a case in the bounded PLANNED_CASES manifest, so
an unopened docket can't be typo'd into silent dormancy.

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

# Geojson person.* tokens (person_id, participants, candidate_people,
# candidate_person, ancestor_person, collateral_persons, or a person.*
# mention anywhere else in a feature's properties) that resolve to no
# index.html person.* anchor: union spouses and collaterals named only
# inside a combined "Person + Spouse" card that belongs to their
# partner's id, so they never got a card of their own, plus candidate
# identities still under research. Shrinks when the people-index (W4)
# gives them entries; new geojson person ids must either match an HTML
# anchor or be added here deliberately.
RESIDUAL_PERSONS = frozenset({
    "person.ann_ghent_sleight",
    "person.antonette_grams",
    "person.betsy_wasson",
    "person.catherina_marie_koeberger",
    "person.catherine_zinkle",
    "person.clarence_aison_rust",
    "person.cora_mcclellan",
    "person.dorothea_meyer",
    "person.edward_j_flaherty",
    "person.edwin_reid",
    "person.elizabeth_j_haden",
    "person.elizabeth_jane_brown",
    "person.ethel_b_rupert",
    # candidate identity of person.mary_frances_rust pending case.05 --
    # deliberately distinct id while the identity question is open.
    "person.frances_adolph",
    "person.genevieve_clemans",
    "person.julia_dible",
    "person.kate_flaherty",
    "person.lovina_parker_love",
    "person.lyle_strawn",
    "person.margaret_ellen_flaherty",
    # EXCLUDED same-name individual, referenced by the exclusion target.
    "person.marjorie_opal_clemans",
    "person.mary_frances_rust",
    "person.mary_viola_beach",
    "person.nancy_ann_turner",
    "person.nomdje_n_rust",
    "person.paul_michael_zimmerman",
    "person.rev_robert_long",
    "person.robert_reid",
    "person.sarah_hoge",
    "person.sarah_sally_lewis_tompkins",
    "person.sophia_reid",
    "person.virginia_ann_ford",
    "person.william_bryan_rust",
})

# Old person.* ids retired by past renames (Slate 1 W1's grammar cutover,
# 26 ids; plus six ids folded together by later data repairs). A retired
# id must never resurface as a walked geojson token or a trace/frame
# reference -- that would silently reintroduce a split identity under an
# id nothing else points to. RETIRED_TO_CANONICAL names the replacement
# for the failure message; RESIDUAL_PERSONS and RETIRED_ALIASES must stay
# disjoint (asserted below) so a stale alias can't be laundered back in
# by adding it to the residual set instead of fixing the reference.
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
}
RETIRED_ALIASES = frozenset(RETIRED_TO_CANONICAL)

_retired_residual_overlap = RESIDUAL_PERSONS & RETIRED_ALIASES
assert not _retired_residual_overlap, (
    f"RESIDUAL_PERSONS and RETIRED_ALIASES overlap: {sorted(_retired_residual_overlap)}")

# Append-only Docket registry: extend this set in the same change that
# opens a new case. Bounds how far a case ref can pend before the Docket
# lands -- an id outside this manifest is a typo, not a future case.
# 2026-07-08: case.21 opened for Cecilia's corrected Leonard Ferdinand parentage.
PLANNED_CASES = frozenset({f"case.{n:02d}" for n in range(1, 22)})


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
    ids.update(seen_fids)
    ids.update(k for k in geo.get("place_registry") or {} if isinstance(k, str))
    ids.update(RESIDUAL_PERSONS)
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
            failures.append(f"person id violates grammar person.[a-z0-9_]+: {value}")
        if value.startswith("case.") and CASE_GRAMMAR.fullmatch(value) is None:
            failures.append(f"case id violates grammar case.NN: {value}")


def check_residuals(html: str, geo: dict, failures: list[str]) -> None:
    """RESIDUAL_PERSONS must track reality in both directions, so it can't
    drift into a second, unreviewed identity list: every entry must still
    be cited somewhere in the geojson, and none may have gained an
    index.html card (that's a forced cutover, not an addition -- the
    residual entry is removed the same change the card lands)."""
    geo_person_tokens: set[str] = set()
    for feature in geo["features"]:
        geo_person_tokens.update(iter_person_tokens(feature.get("properties") or {}))
    html_anchors = set(re.findall(r'id="(person\.[A-Za-z0-9_.-]+)"', html))
    for value in sorted(RESIDUAL_PERSONS):
        if value not in geo_person_tokens:
            failures.append(f"RESIDUAL_PERSONS {value} no longer occurs in geojson; delete it")
        if value in html_anchors:
            failures.append(f"RESIDUAL_PERSONS {value} now has an index.html anchor; remove it from RESIDUAL_PERSONS")


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
    # Dormancy is bounded by PLANNED_CASES either way: a case ref outside
    # that manifest is a typo, not a future case, and fails immediately.
    docket_live = any(k.startswith("case.") for k in known)
    pending_cases = set()
    for origin, ref in references:
        if ref in known:
            continue
        if ref in RETIRED_ALIASES:
            failures.append(
                f"retired alias {ref} referenced from {origin}; use {RETIRED_TO_CANONICAL[ref]} instead")
            continue
        if ref.startswith("case."):
            if ref not in PLANNED_CASES:
                failures.append(f"UNRESOLVED {ref} referenced from {origin}: unknown case id (not in PLANNED_CASES)")
                continue
            if not docket_live:
                pending_cases.add(ref)
                continue
        failures.append(f"UNRESOLVED {ref} referenced from {origin}")
    if pending_cases:
        print(f"check_refs: {len(pending_cases)} case refs pending the Docket "
              f"({', '.join(sorted(pending_cases))})")
    check_links(html, geo, failures)
    check_source_urls(geo, ledger, failures)
    check_grammar(known | {ref for _, ref in references}, failures)
    check_residuals(html, geo, failures)

    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        print(f"check_refs: {len(failures)} failure(s)", file=sys.stderr)
        return 1
    print(f"check_refs: {len(references)} references resolve against {len(known)} defined ids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
