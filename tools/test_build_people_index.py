#!/usr/bin/env python3
"""Acceptance checks for the canonical family-core projection builder."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "tools/build_people_index.py"
failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def person(
    person_id: str,
    display_name: str,
    index_name: str,
    branch: str,
    *,
    role: str = "ancestor",
) -> dict[str, object]:
    return {
        "id": person_id,
        "node_type": "person",
        "display_name": display_name,
        "index_names": [index_name],
        "name_variants": [],
        "branches": [branch],
        "role": role,
        "confidence": "lead",
        "privacy": "public_deceased",
        "public_anchor": person_id,
    }


def parent(
    relationship_id: str,
    parent_id: str,
    child_id: str,
    parent_role: str,
    branch: str,
    *,
    status: str = "accepted",
) -> dict[str, object]:
    return {
        "id": relationship_id,
        "node_type": "relationship",
        "relationship_type": "parent_of",
        "parent_role": parent_role,
        "person_a": parent_id,
        "person_b": child_id,
        "status": status,
        "confidence": "lead",
        "branches": [branch],
        "evidence_refs": [],
        "source_refs": [],
        "case_refs": ["case.01"],
        "provenance_note": "Synthetic projection fixture.",
    }


def gap() -> dict[str, object]:
    return {
        "id": "gap.c.father",
        "node_type": "gap",
        "gap_type": "candidate_parentage",
        "label": "Competing father candidates",
        "subject_persons": ["person.c.root"],
        "candidate_persons": ["person.c.father_one", "person.c.father_two"],
        "open_roles": ["father"],
        "branches": ["connelly"],
        "case_refs": ["case.01"],
        "evidence_refs": [],
        "source_refs": [],
        "public_anchor": "gap.c.father",
        "status": "open",
        "resolution_note": "",
        "resolved_on": None,
        "owner_follow_up_required": False,
        "pedigree": {"Z": [], "M": [], "D": [], "C": [2]},
    }


def write_fixture(root: Path) -> None:
    people = [
        person("person.z.root", "Zed Root", "Root, Zed", "zimmerman", role="anchor"),
        person("person.z.father", "Zed Father", "Father, Zed", "zimmerman"),
        person("person.z.mother", "Zed Mother", "Mother, Zed", "zimmerman"),
        person("person.z.shared", "Shared Ancestor", "Ancestor, Shared", "zimmerman"),
        person("person.m.root", "Mina Root", "Root, Mina", "mundell", role="anchor"),
        person("person.d.root", "Dara Root", "Root, Dara", "dible", role="anchor"),
        person("person.c.root", "Cora Root", "Root, Cora", "connelly", role="anchor"),
        person(
            "person.c.father_one",
            "First Candidate",
            "Candidate, First",
            "connelly",
            role="candidate",
        ),
        person(
            "person.c.father_two",
            "Second Candidate",
            "Candidate, Second",
            "connelly",
            role="candidate",
        ),
    ]
    relationships = [
        parent(
            "relationship.z.father",
            "person.z.father",
            "person.z.root",
            "father",
            "zimmerman",
        ),
        parent(
            "relationship.z.mother",
            "person.z.mother",
            "person.z.root",
            "mother",
            "zimmerman",
            status="hypothesis",
        ),
        parent(
            "relationship.z.shared_to_father",
            "person.z.shared",
            "person.z.father",
            "father",
            "zimmerman",
        ),
        parent(
            "relationship.z.shared_to_mother",
            "person.z.shared",
            "person.z.mother",
            "father",
            "zimmerman",
        ),
        parent(
            "relationship.c.father_one",
            "person.c.father_one",
            "person.c.root",
            "father",
            "connelly",
            status="hypothesis",
        ),
        parent(
            "relationship.c.father_two",
            "person.c.father_two",
            "person.c.root",
            "father",
            "connelly",
            status="hypothesis",
        ),
        gap(),
    ]

    people_dir = root / "research/people"
    people_dir.mkdir(parents=True, exist_ok=True)
    (people_dir / "people.jsonl").write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in people),
        encoding="utf-8",
    )
    (people_dir / "relationships.jsonl").write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in relationships),
        encoding="utf-8",
    )
    ids = [str(row["public_anchor"]) for row in people] + ["gap.c.father"]
    target_html = "\n".join(f'<div id="{identifier}"></div>' for identifier in ids)
    (root / "index.html").write_text(
        "<!doctype html><html><body>\n"
        + target_html
        + '\n<script type="application/json" id="people-index">{"v":2,"people":[]}</script>\n'
        + '<section class="sheet" id="index-of-names"><h2>old</h2></section>\n'
        + "</body></html>\n",
        encoding="utf-8",
    )


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER), "--root", str(root), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def payload(source: str) -> dict[str, object]:
    match = re.search(
        r'<script type="application/json" id="people-index">(.*?)</script>',
        source,
        re.S,
    )
    assert match is not None
    return json.loads(match.group(1))


with tempfile.TemporaryDirectory(prefix="people-projection-test-") as td:
    root = Path(td) / "repo"
    root.mkdir()
    write_fixture(root)

    # A stale projection is reported without modifying the fixture.
    stale = (root / "index.html").read_bytes()
    result = run(root, "--check")
    check("stale check fails", result.returncode != 0, result.stderr)
    check("check is read only", (root / "index.html").read_bytes() == stale)

    result = run(root)
    check("build succeeds", result.returncode == 0, result.stderr)
    rendered = (root / "index.html").read_text(encoding="utf-8")
    data = payload(rendered)
    entries = data.get("people", [])
    check("payload v2", data.get("v") == 2, data)

    by_key = {(entry["i"], entry["a"]): entry for entry in entries}
    check(
        "accepted father traversal",
        by_key[("person.z.father", "Z")]["ah"] == [2],
        by_key[("person.z.father", "Z")],
    )
    check(
        "hypothesis traversal",
        by_key[("person.z.mother", "Z")]["ah"] == [3],
        by_key[("person.z.mother", "Z")],
    )
    check(
        "pedigree collapse retained",
        by_key[("person.z.shared", "Z")]["ah"] == [4, 6],
        by_key[("person.z.shared", "Z")],
    )
    check(
        "conflict gap owns slot",
        by_key[("gap.c.father", "C")]["ah"] == [2],
        by_key[("gap.c.father", "C")],
    )
    check(
        "conflicting people do not own slot",
        by_key[("person.c.father_one", "C")]["ah"] == []
        and by_key[("person.c.father_two", "C")]["ah"] == [],
        (by_key[("person.c.father_one", "C")], by_key[("person.c.father_two", "C")]),
    )
    check(
        "one individual per person entry",
        all(" + " not in entry["n"] for entry in entries if entry["k"] == "person"),
    )
    index_section = re.search(
        r'<section class="sheet" id="index-of-names">.*?</section>', rendered, re.S
    )
    check("name index rendered", index_section is not None)
    index_text = index_section.group(0) if index_section else ""
    check(
        "name index excludes gaps",
        "Competing father candidates" not in index_text,
        index_text,
    )
    check("name index has individual", "Candidate, First" in index_text, index_text)

    built = (root / "index.html").read_bytes()
    result = run(root, "--check")
    check("current check passes", result.returncode == 0, result.stderr)
    result = run(root)
    check("repeat build succeeds", result.returncode == 0, result.stderr)
    check("repeat build byte stable", (root / "index.html").read_bytes() == built)

    # Competing parent hypotheses without an explicit slot owner must fail.
    relationships_path = root / "research/people/relationships.jsonl"
    rows = [json.loads(line) for line in relationships_path.read_text().splitlines()]
    relationships_path.write_text(
        "".join(
            json.dumps(row, separators=(",", ":")) + "\n"
            for row in rows
            if row["node_type"] != "gap"
        ),
        encoding="utf-8",
    )
    result = run(root)
    check(
        "unowned conflict fails",
        result.returncode != 0 and "explicit gap" in result.stderr,
        result.stderr,
    )

    # A retained rejected edge is not a live pedigree candidate.
    write_fixture(root)
    rows = [json.loads(line) for line in relationships_path.read_text().splitlines()]
    retained = []
    for row in rows:
        if row["node_type"] == "gap":
            continue
        if row["id"] == "relationship.c.father_two":
            row["status"] = "rejected"
            row["provenance_note"] += " Rejected on 2026-07-09: fixture adjudication."
        retained.append(row)
    relationships_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in retained),
        encoding="utf-8",
    )
    result = run(root)
    check("rejected candidate projection succeeds", result.returncode == 0, result.stderr)
    retained_payload = payload((root / "index.html").read_text())
    retained_by_id = {entry["i"]: entry for entry in retained_payload["people"]}
    check(
        "active candidate receives slot",
        retained_by_id["person.c.father_one"]["ah"] == [2],
        retained_by_id,
    )
    check(
        "rejected candidate has no slot",
        retained_by_id["person.c.father_two"]["ah"] == [],
        retained_by_id,
    )

    # Even an unplaced hypothesis cycle is unsafe for graph consumers.
    write_fixture(root)
    relationships_path = root / "research/people/relationships.jsonl"
    rows = [json.loads(line) for line in relationships_path.read_text().splitlines()]
    rows.extend(
        [
            parent(
                "relationship.c.loop_one",
                "person.c.father_one",
                "person.c.father_two",
                "father",
                "connelly",
                status="hypothesis",
            ),
            parent(
                "relationship.c.loop_two",
                "person.c.father_two",
                "person.c.father_one",
                "father",
                "connelly",
                status="hypothesis",
            ),
        ]
    )
    relationships_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    result = run(root)
    check(
        "unplaced hypothesis cycle fails",
        result.returncode != 0 and "cycles" in result.stderr,
        result.stderr,
    )

    # A legacy combined-couple label is rejected instead of leaking into v2.
    write_fixture(root)
    people_path = root / "research/people/people.jsonl"
    people = [json.loads(line) for line in people_path.read_text().splitlines()]
    people[0]["display_name"] = "Zed Root + Someone Else"
    people_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in people),
        encoding="utf-8",
    )
    result = run(root)
    check(
        "combined person label rejected",
        result.returncode != 0 and "one individual" in result.stderr,
        result.stderr,
    )

    # Generated links never survive a missing or misspelled presentation id.
    write_fixture(root)
    html_path = root / "index.html"
    source = html_path.read_text(encoding="utf-8")
    html_path.write_text(
        source.replace('<div id="person.z.father"></div>\n', ""),
        encoding="utf-8",
    )
    result = run(root)
    check(
        "missing target rejected",
        result.returncode != 0 and "person.z.father (0 matches)" in result.stderr,
        result.stderr,
    )

# Lock the migration's historically significant corrections to the real projection.
# These are deliberately exact: a later edit must not silently reintroduce the
# combined people, pedigree-collapse loss, or disputed Ford parents that prompted
# the canonical-family cutover.
real_data = payload((REPO / "index.html").read_text(encoding="utf-8"))
real_entries = real_data.get("people", [])
real_by_key = {(entry["i"], entry["a"]): entry for entry in real_entries}
check(
    "real Rust father slot",
    real_by_key[("person.rust.john_aissen", "M")]["ah"] == [20],
    real_by_key[("person.rust.john_aissen", "M")],
)
check(
    "real Rust mother slot",
    real_by_key[("person.rust.frauke_folkerts_everwyn", "M")]["ah"] == [21],
    real_by_key[("person.rust.frauke_folkerts_everwyn", "M")],
)
check(
    "older Rust generation remains unplaced",
    real_by_key[("person.rust.aisse_jansen", "M")]["ah"] == []
    and real_by_key[("person.rust.jan_aissen", "M")]["ah"] == [],
    (
        real_by_key[("person.rust.aisse_jansen", "M")],
        real_by_key[("person.rust.jan_aissen", "M")],
    ),
)
check(
    "Nomdje remains an unplaced second wife",
    real_by_key[("person.nomdje_n_rust", "M")]["ah"] == [],
    real_by_key[("person.nomdje_n_rust", "M")],
)
check(
    "real Dible paternal collapse",
    real_by_key[("person.dible.john_albert", "D")]["ah"] == [16, 20]
    and real_by_key[("person.heckman.catherine", "D")]["ah"] == [17, 21],
    (
        real_by_key[("person.dible.john_albert", "D")],
        real_by_key[("person.heckman.catherine", "D")],
    ),
)
check(
    "real Ford gap owns disputed slots",
    real_by_key[("gap.ford.john_laborn.parentage", "C")]["ah"] == [44, 45],
    real_by_key[("gap.ford.john_laborn.parentage", "C")],
)
check(
    "real Ford candidates remain unplaced",
    all(
        real_by_key[(person_id, "C")]["ah"] == []
        for person_id in (
            "person.davis.aritta",
            "person.ford.john_laborn_sr",
            "person.ford.levi",
        )
    ),
)

# The map is another public projection of the same people. Keep the four
# corrected identities/roles from drifting independently of the family core.
geo = json.loads((REPO / "ancestry_geospatial.geojson").read_text(encoding="utf-8"))
geo_by_id = {feature["id"]: feature for feature in geo["features"]}
check(
    "Ernestina death uses Ernestina identity",
    geo_by_id["event.zodrow.ernestina_death.1940-05-14"]["properties"][
        "person_id"
    ]
    == "person.baier.ernestina",
)
check(
    "1841 Rust origin uses Aisse identity",
    geo_by_id["event.rust.east_frisian_origin.1841"]["properties"]["person_id"]
    == "person.rust.aisse_jansen",
)
claar_origin = geo_by_id["event.claar.swiss_origin.1700"]["properties"]
check(
    "Claar origin is lineage context",
    claar_origin["feature_kind"] == "lineage_context"
    and claar_origin["event_type"] == "european_origin_hypothesis"
    and "person_id" not in claar_origin,
    claar_origin,
)
check(
    "Long marriage names both participants",
    geo_by_id["event.long.jf_marriage.1826-02-23"]["properties"]["participants"]
    == ["person.long.john_franklin", "person.patton.sally"],
)
check(
    "resolved Rust target is cut over upstream",
    "target.rust.smith_county_parentage" not in geo_by_id
    and "target.rust.john_f_ethel_rupert_reamsville_cluster" not in geo_by_id
    and geo_by_id["target.rust.john_f_upstream_parentage"]["properties"][
        "subject_person"
    ]
    == "person.rust.john_f"
    and geo_by_id["target.rust.john_f_upstream_reamsville_cluster"]["properties"][
        "candidate_people"
    ]
    == [
        "person.rust.john_aissen",
        "person.rust.frauke_folkerts_everwyn",
    ],
)
rust_path_note = geo_by_id["path.rust_upstream_and_frances_identity"]["properties"][
    "evidence_note"
]
check(
    "Rust path states settled parentage",
    "are established as Mary Frances's parents" in rust_path_note
    and "remain candidate parents" not in rust_path_note,
    rust_path_note,
)
rust_trace = (
    REPO / "research/reasoning-traces/2026-07-07-mundell-rust-frances-adolph.md"
).read_text(encoding="utf-8")
check(
    "active Rust trace states settled parentage",
    "only candidate parents" not in rust_trace
    and "case_refs: [\"case.05\", \"case.06\"]" in rust_trace,
)
source_rows = [
    json.loads(line)
    for line in (REPO / "research/sources/sources.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line
]
john_aissen_source = next(
    row
    for row in source_rows
    if row["id"] == "src.john-aissen-rust-find-a-grave.23615b78"
)
check(
    "John Aissen source scopes the open edge",
    "still-open upstream link" in john_aissen_source["blurb"]
    and "prove Mary Frances Rust's parents" not in john_aissen_source["blurb"],
    john_aissen_source["blurb"],
)

if failures:
    print("PEOPLE PROJECTION TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    raise SystemExit(1)
print("people projection: all contract checks passed")
