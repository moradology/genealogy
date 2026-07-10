#!/usr/bin/env python3
"""Acceptance checks for the family-card projection builder (tools/build_family.py).

Offline, stdlib only, no try/except. The builder renders whole .generations
blocks (person cards, gap cards, inline stems) from layout.jsonl + display
blocks. Bootstrap bar is CONTENT-FAITHFUL, not byte- or DOM-identical: every
visible word and every link target of the hand region must survive into the
generated region; presentation is free to improve. Words change only through
store edits. Run: uv run tools/test_build_family.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "tools/build_family.py"
failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BUILDER), "--root", str(root), *args],
        capture_output=True, text=True)


def person(pid: str, name: str, confidence: str = "documented",
           anchor: str | None = None, display: dict | None = None) -> dict:
    row = {
        "id": pid, "node_type": "person", "display_name": name,
        "index_names": [name], "name_variants": [], "branches": ["zimmerman"],
        "role": "ancestor", "confidence": confidence,
        "privacy": "public_deceased", "public_anchor": anchor or pid,
    }
    if display is not None:
        row["display"] = display
    return row


def plink(parent: str, child: str, confidence: str = "documented") -> dict:
    return {
        "id": f"relationship.parent.{parent.split('.')[-1]}-to-{child.split('.')[-1]}",
        "node_type": "relationship", "relationship_type": "parent_of",
        "person_a": parent, "person_b": child, "parent_role": "mother",
        "status": "accepted", "confidence": confidence, "branches": ["zimmerman"],
        "evidence_refs": [], "source_refs": ["src.test.x"], "case_refs": [],
        "provenance_note": "test",
    }


GAP_ROW = {
    "id": "gap.solo.parents", "node_type": "gap", "gap_type": "parentage",
    "label": "Parents of Sol Solo", "subject_persons": ["person.solo"],
    "candidate_persons": [], "open_roles": ["parents"], "branches": ["zimmerman"],
    "case_refs": [], "evidence_refs": [], "source_refs": [],
    "public_anchor": "gap.solo.parents", "status": "open",
    "resolution_note": "", "resolved_on": None, "owner_follow_up_required": False,
    "pedigree": {"Z": [16, 17], "M": [], "D": [], "C": []},
    "display": {"identity": "The open Gen 5 slot.",
                "details": "Not yet proven. Best target: the parish register."},
}
STEM_ROW = {
    "id": "stem.test.one", "node_type": "stem", "anchor": "person.anchor",
    "target": "person.target", "from_label": "Anna A. Anchor",
    "via_prose": "mother", "link_text": "Tessa Target",
    "line_label": "the Target line",
}
REGISTRY = {
    "v": 2,
    "people": [
        {"i": "person.anchor", "n": "Anna Anchor", "a": "Z", "k": "person",
         "ah": [1], "t": "documented", "h": "person.anchor"},
        {"i": "person.solo", "n": "Sol Solo", "a": "Z", "k": "person",
         "ah": [4], "t": "documented", "h": "person.solo"},
        {"i": "person.target", "n": "Tessa Target", "a": "Z", "k": "person",
         "ah": [2], "t": "documented", "h": "person.target"},
        {"i": "gap.solo.parents", "n": "Parents of Sol Solo", "a": "Z",
         "k": "gap", "ah": [16, 17], "t": "open", "h": "gap.solo.parents"},
    ],
}
LAYOUT = {
    "id": "layout.branch-test.1", "node_type": "layout_block",
    "section": "branch-test", "anchor_class": "zimmerman",
    "generations": [
        {"label": "Gen 1", "items": ["person.anchor"]},
        {"label": "Gen 2", "items": ["person.solo", "stem.test.one",
                                     "gap.solo.parents"]},
    ],
}
EVIDENCE_DISPLAY = {
    "variant": "roll", "head": "1910 Census · Test County",
    "roll": [{"cells": ["Sol Solo", "10", "Son"], "focal": True}],
    "cite": "Sheet 1A · via Test",
}
ANCHOR_DISPLAY = {"identity": "The test anchor.",
                  "details": "Documented at the seat.{{cite:src.one.aaaa1111}}"}
SOLO_DISPLAY = {"identity": "Anna’s son.",
                "details": "Counted in 1910.{{cite:src.two.bbbb2222}}",
                "vitals": "b. 1900 – d. 1980",
                "record_cards": ["ev.test.card"]}

# Hand-authored region in the CURRENT page style: entities, stem markers.
HAND_REGION = (
    '<div class="generation"><div class="gen-label">Gen 1</div>'
    '<div class="people"><div class="person" id="person.anchor">'
    '<div class="person-head"><span class="person-name">Anna Anchor</span> '
    '<span class="ahnen">Z-1</span> '
    '<span class="tag documented">Documented</span></div>'
    '<p class="identity">The test anchor.</p>'
    '<div class="person-details">Documented at the seat.'
    "<a class=cite href=#s1>s1</a></div></div></div></div>\n"
    '<div class="generation"><div class="gen-label">Gen 2</div>'
    '<div class="people"><div class="person" id="person.solo">'
    '<div class="person-head"><span class="person-name">Sol Solo</span> '
    '<span class="ahnen">Z-4</span> '
    '<span class="tag documented">Documented</span></div>'
    '<div class="vitals">b. 1900 &ndash; d. 1980</div>'
    '<p class="identity">Anna&rsquo;s son.</p>'
    '<div class="person-details">Counted in 1910.'
    "<a class=cite href=#s2>s2</a></div>"
    '<figure class="record-card anchor-zimmerman" '
    'data-evidence-id="ev.test.card"><figcaption class="record-head">'
    '1910 Census &middot; Test County</figcaption>'
    '<table class="record-roll"><tbody><tr class="focal"><td>Sol Solo</td>'
    "<td>10</td><td>Son</td></tr></tbody></table>"
    '<p class="record-cite">Sheet 1A &middot; via Test</p></figure></div>'
    "<!-- BEGIN stem:stem.test.one -->"
    '<div class="stem"><span class="stem-label">descent</span> Anna A. Anchor '
    '<span class="stem-arrow">→</span> mother '
    '<a href="#person.target">Tessa Target</a> '
    '<span class="stem-arrow">→</span> the Target line '
    '<span class="tag documented">Documented</span> '
    '<span class="stem-note">weakest step: Anna–Tessa</span></div>'
    "<!-- END -->"
    '<div class="person" id="gap.solo.parents"><div class="person-head">'
    '<span class="person-name">Parents of Sol Solo</span> '
    '<span class="ahnen">Z-16&middot;17</span> '
    '<span class="tag open">Open edge</span></div>'
    '<p class="identity">The open Gen 5 slot.</p>'
    '<div class="person-details">Not yet proven. Best target: the parish '
    "register.</div></div></div></div>"
)


def jl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)


def make_root(tmp: Path, *, layout: dict = LAYOUT, hand: str = HAND_REGION,
              solo_display: dict = SOLO_DISPLAY,
              evidence_display: dict | None = EVIDENCE_DISPLAY,
              stem_confidence: str = "documented") -> Path:
    root = tmp / "repo"
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "sources").mkdir(parents=True)
    (root / "research" / "evidence").mkdir(parents=True)
    people = [
        person("person.anchor", "Anna Anchor", display=ANCHOR_DISPLAY),
        person("person.solo", "Sol Solo",
               display=dict(solo_display) if solo_display else None),
        person("person.target", "Tessa Target"),
    ]
    (root / "research" / "people" / "people.jsonl").write_text(
        jl(people), encoding="utf-8")
    (root / "research" / "people" / "relationships.jsonl").write_text(
        jl([plink("person.target", "person.anchor",
                  confidence=stem_confidence), GAP_ROW]), encoding="utf-8")
    (root / "research" / "people" / "stems.jsonl").write_text(
        jl([STEM_ROW]), encoding="utf-8")
    (root / "research" / "people" / "layout.jsonl").write_text(
        jl([layout]), encoding="utf-8")
    evidence_row = {"id": "ev.test.card"}
    if evidence_display is not None:
        evidence_row["display"] = evidence_display
    (root / "research" / "evidence" / "zimmerman.jsonl").write_text(
        jl([evidence_row]), encoding="utf-8")
    (root / "research" / "sources" / "sources.jsonl").write_text(
        jl([{"id": "src.one.aaaa1111", "html_id": "s1"},
            {"id": "src.two.bbbb2222", "html_id": "s2"}]), encoding="utf-8")
    (root / "index.html").write_text(
        "<html><body>\n"
        f'<script type="application/json" id="people-index">'
        f"{json.dumps(REGISTRY, separators=(',', ':'))}</script>\n"
        '<section class="sheet" id="branch-test"><h2>Test Branches</h2>\n'
        '<div class="branch"><div class="branch-title"><h3>Test Line</h3></div>\n'
        f'<div class="generations">\n{hand}\n</div></div></section>\n'
        "</body></html>\n", encoding="utf-8")
    return root


with tempfile.TemporaryDirectory(prefix="build-family-test-") as td:
    tmp = Path(td)

    # 1. Bootstrap: content-faithful cutover, stem markers absorbed
    root = make_root(tmp / "boot")
    result = run(root)
    html = (root / "index.html").read_text(encoding="utf-8")
    check("bootstrap exits 0", result.returncode == 0,
          result.stdout + result.stderr)
    check("family-block marker present",
          html.count("<!-- BEGIN family-block:layout.branch-test.1 -->") == 1, html)
    check("stem markers absorbed into the block",
          "<!-- BEGIN stem:" not in html, html)
    check("stem still renders inside the block",
          "weakest step: Anna–Tessa" in html, html)
    check("record card rides the person card",
          'data-evidence-id="ev.test.card"' in html, html)
    check("entities normalized to unicode", "&ndash;" not in html, html)

    # 2. Idempotence and --check
    before = (root / "index.html").read_bytes()
    result = run(root)
    check("second write is a no-op",
          result.returncode == 0 and (root / "index.html").read_bytes() == before,
          result.stdout)
    result = run(root, "--check")
    check("check green after write", result.returncode == 0,
          result.stdout + result.stderr)

    # 3. Content edits flow store -> page; --check catches drift
    solo = dict(SOLO_DISPLAY)
    solo["details"] = "Counted in the 1910 census.{{cite:src.two.bbbb2222}}"
    (root / "research" / "people" / "people.jsonl").write_text(
        jl([person("person.anchor", "Anna Anchor", display=ANCHOR_DISPLAY),
            person("person.solo", "Sol Solo", display=solo),
            person("person.target", "Tessa Target")]), encoding="utf-8")
    result = run(root, "--check")
    check("display edit reddens check", result.returncode == 1, result.stdout)
    check("check names the remediation", "./gen build family" in result.stdout,
          result.stdout)
    result = run(root)
    check("rebuild renders the store edit", result.returncode == 0
          and "Counted in the 1910 census." in
          (root / "index.html").read_text(encoding="utf-8"), result.stdout)

    # 4. A relationship confidence edit re-renders the inline stem
    (root / "research" / "people" / "relationships.jsonl").write_text(
        jl([plink("person.target", "person.anchor", confidence="lead"),
            GAP_ROW]), encoding="utf-8")
    result = run(root, "--check")
    check("stem chain edit reddens check", result.returncode == 1, result.stdout)
    result = run(root)
    check("stem tag regenerates inside the family block",
          '<span class="tag lead">Working lead</span>' in
          (root / "index.html").read_text(encoding="utf-8"), result.stdout)

    # 5. build_stems skips layout-claimed stems entirely
    result = subprocess.run(
        [sys.executable, str(REPO / "tools/build_stems.py"),
         "--root", str(root), "--check"],
        capture_output=True, text=True)
    check("build_stems skips claimed stems",
          result.returncode == 0 and "0 stems" in result.stdout,
          result.stdout + result.stderr)

    # 6. Bootstrap refuses when the hand region carries words the store lacks
    tampered = HAND_REGION.replace("Documented at the seat.",
                                   "Documented at the seat, they say.")
    root = make_root(tmp / "tamper", hand=tampered)
    before = (root / "index.html").read_bytes()
    result = run(root)
    check("content mismatch refuses", result.returncode == 1,
          result.stdout + result.stderr)
    check("content mismatch writes nothing",
          (root / "index.html").read_bytes() == before)

    # 7. Error paths: zero writes
    bad_layout = dict(LAYOUT)
    bad_layout["generations"] = [{"label": "Gen 1",
                                  "items": ["person.nobody"]}]
    root = make_root(tmp / "bad-item", layout=bad_layout)
    before = (root / "index.html").read_bytes()
    result = run(root)
    check("unknown layout item exits 1", result.returncode == 1,
          result.stdout + result.stderr)
    check("unknown layout item writes nothing",
          (root / "index.html").read_bytes() == before)

    root = make_root(tmp / "no-display", solo_display=None)
    result = run(root)
    check("card item without display exits 1", result.returncode == 1,
          result.stdout + result.stderr)

    root = make_root(tmp / "no-card-display", evidence_display=None)
    result = run(root)
    check("record card without evidence display exits 1",
          result.returncode == 1, result.stdout + result.stderr)

    dup_layout = dict(LAYOUT)
    dup_layout["generations"] = [
        {"label": "Gen 1", "items": ["person.anchor", "person.anchor"]}]
    root = make_root(tmp / "dup-item", layout=dup_layout)
    result = run(root)
    check("duplicate layout item exits 1", result.returncode == 1,
          result.stdout + result.stderr)

if failures:
    print("BUILD FAMILY TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("build_family: all contract checks passed")
