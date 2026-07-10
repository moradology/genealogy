#!/usr/bin/env python3
"""Contract tests for tools/extract_family_display.py (one-shot migrator).

The extractor parses hand-authored person/gap rows out of index.html and
emits candidate display blocks, evidence display blocks, and layout rows as
JSON on stdout. It derives title/ahnen/tag by rule and emits overrides ONLY
where the rule misses; it REFUSES (nonzero exit, refusal list, no output
blocks) on any construct outside the display grammar or any tag that
disagrees with the store - escalation, never guessing.

Offline, stdlib only, no try/except. Run: uv run tools/test_extract_family_display.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXTRACTOR = REPO / "tools/extract_family_display.py"
sys.path.insert(0, str(REPO / "tools"))
import family_display  # noqa: E402

failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(EXTRACTOR), "--root", str(root), *args],
        capture_output=True, text=True)


def person(pid: str, name: str, confidence: str = "documented",
           anchor: str | None = None) -> dict:
    return {
        "id": pid, "node_type": "person", "display_name": name,
        "index_names": [name], "name_variants": [], "branches": ["zimmerman"],
        "role": "ancestor", "confidence": confidence,
        "privacy": "public_deceased", "public_anchor": anchor or pid,
    }


REGISTRY = {
    "v": 2,
    "people": [
        {"i": "person.solo", "n": "Sol Solo", "a": "Z", "k": "person",
         "ah": [1], "t": "documented", "h": "person.solo"},
        {"i": "person.hus", "n": "Hank Husband", "a": "Z", "k": "person",
         "ah": [4], "t": "strong", "h": "person.hus"},
        {"i": "person.wif", "n": "Wilma Wife", "a": "Z", "k": "person",
         "ah": [5], "t": "strong", "h": "person.hus"},
        {"i": "gap.solo.parents", "n": "Parents of Sol Solo", "a": "Z",
         "k": "gap", "ah": [16, 17], "t": "open", "h": "gap.solo.parents"},
    ],
}

SOLO_ROW = (
    '<div class="person" id="person.solo"><div class="person-head">'
    '<span class="person-name">Sol Solo</span> <span class="ahnen">Z-1</span> '
    '<span class="tag documented">Documented</span></div>'
    '<div class="vitals">b. 1900 &ndash; d. 1980</div>'
    '<p class="identity">The test anchor.</p>'
    '<div class="person-details"><figure class="cameo">'
    '<img src="images/people/solo.jpg" alt="Sol at home" width="100" '
    'height="120" loading="lazy"><figcaption>'
    '<a href="https://example.org/solo">Photo: archive</a></figcaption></figure>'
    'Documented 1900&ndash;1980, Kansas.<a class=cite href=#s1>s1</a> '
    'See <a class="case-chip" href="#case.01">case.01</a>.</div>'
    '<figure class="record-card anchor-zimmerman" '
    'data-evidence-id="ev.test.solo"><figcaption class="record-head">'
    '1910 Census &middot; Test County</figcaption><table class="record-roll">'
    "<tbody><tr><td>Head Person</td><td>40</td><td>Head</td></tr>"
    '<tr class="focal"><td>Sol Solo</td><td>10</td><td>Son</td></tr>'
    '</tbody></table><p class="record-cite">Sheet 1A &middot; via Test</p>'
    "</figure></div>"
)
COUPLE_ROW = (
    '<div class="person" id="person.hus"><div class="person-head">'
    '<span class="person-name">Hank Husband + Wilma Wife</span> '
    '<span class="ahnen">Z-4&middot;5</span> '
    '<span class="tag strong">Strong lead</span></div>'
    '<p class="identity">The test couple.</p>'
    '<div class="person-details">Married 1920.<a class=cite href=#s2>s2</a></div></div>'
)
GAP_ROW = (
    '<div class="person" id="gap.solo.parents"><span id="person.ghost"></span>'
    '<div class="person-head"><span class="person-name">Parents of Sol Solo</span> '
    '<span class="ahnen">Z-16&middot;17</span> '
    '<span class="tag open">Open edge</span></div>'
    '<p class="identity">The open slot.</p>'
    '<div class="person-details">Not yet proven.</div></div>'
)


def make_root(tmp: Path, rows_html: str, people_rows: list[dict],
              registry: dict = REGISTRY, second_branch_html: str = "") -> Path:
    root = tmp / "repo"
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "sources").mkdir(parents=True)
    (root / "research" / "people" / "people.jsonl").write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in people_rows),
        encoding="utf-8")
    (root / "research" / "sources" / "sources.jsonl").write_text(
        json.dumps({"id": "src.one.aaaa1111", "html_id": "s1"}) + "\n"
        + json.dumps({"id": "src.two.bbbb2222", "html_id": "s2"}) + "\n",
        encoding="utf-8")
    second = ""
    if second_branch_html:
        second = (
            '<div class="branch"><div class="branch-title"><h3>Second Line</h3></div>\n'
            '<div class="generations">\n'
            '<div class="generation"><div class="gen-label">Gen 2</div>'
            f'<div class="people">{second_branch_html}</div></div>\n'
            "</div></div>\n")
    (root / "index.html").write_text(
        "<html><body>\n"
        f'<script type="application/json" id="people-index">'
        f"{json.dumps(registry, separators=(',', ':'))}</script>\n"
        '<section class="sheet" id="branch-doyle"><h2>Test Branches</h2>\n'
        '<div class="branch"><div class="branch-title"><h3>Test Line</h3></div>\n'
        '<div class="generations">\n'
        '<div class="generation"><div class="gen-label">Gen 1</div>'
        f'<div class="people">{rows_html}</div></div>\n'
        f"</div></div>\n{second}</section>\n</body></html>\n",
        encoding="utf-8")
    return root


PEOPLE = [person("person.solo", "Sol Solo"),
          person("person.hus", "Hank Husband", confidence="strong"),
          person("person.wif", "Wilma Wife", confidence="strong",
                 anchor="person.hus"),
          person("person.ghost", "Ghost Alias", confidence="open",
                 anchor="person.ghost")]


with tempfile.TemporaryDirectory(prefix="extract-test-") as td:
    tmp = Path(td)

    # 1. Full extraction: prose, tokens, cameo, record card, gap aliases,
    #    one layout block PER div.branch (real sections hold up to three)
    root = make_root(tmp / "full", SOLO_ROW + COUPLE_ROW, PEOPLE,
                     second_branch_html=GAP_ROW)
    result = run(root, "--section", "branch-doyle")
    check("extraction exits 0", result.returncode == 0,
          result.stdout[-500:] + result.stderr[-500:])
    payload = json.loads(result.stdout)
    solo = payload["people"]["person.solo"]
    check("entities decode to unicode", solo["vitals"] == "b. 1900 – d. 1980", solo)
    check("cite anchors reverse-map to src tokens",
          "{{cite:src.one.aaaa1111}}" in solo["details"], solo["details"])
    check("case chips reverse-map to case tokens",
          "{{case:case.01}}" in solo["details"], solo["details"])
    check("cameos extract structurally",
          solo["cameos"] == [{"src": "images/people/solo.jpg",
                              "alt": "Sol at home", "width": 100, "height": 120,
                              "credit_url": "https://example.org/solo",
                              "credit_label": "Photo: archive"}], solo.get("cameos"))
    check("record card ref extracted",
          solo["record_cards"] == ["ev.test.solo"], solo.get("record_cards"))
    card = payload["evidence"]["ev.test.solo"]
    check("record card display extracted",
          card["variant"] == "roll"
          and card["head"] == "1910 Census · Test County"
          and card["roll"][1] == {"cells": ["Sol Solo", "10", "Son"],
                                  "focal": True}, card)
    check("derived couple title needs no override",
          "card_name" not in payload["people"]["person.hus"]
          and "title_override" not in payload["people"]["person.hus"],
          payload["people"]["person.hus"])
    gap = payload["gaps"]["gap.solo.parents"]
    check("gap alias anchors extracted",
          gap["alias_anchors"] == ["person.ghost"], gap)
    layout = payload["layout"]
    check("one layout block per branch", len(layout) == 2, layout)
    check("layout block extracted",
          layout[0]["section"] == "branch-doyle"
          and layout[0]["generations"][0]["label"] == "Gen 1"
          and layout[0]["generations"][0]["items"]
          == ["person.solo", "person.hus"], layout)
    check("second branch layout extracted",
          layout[1]["generations"][0]["label"] == "Gen 2"
          and layout[1]["generations"][0]["items"] == ["gap.solo.parents"],
          layout)

    # 2. Round trip: rendering the extracted block reproduces the source DOM
    cite_codes = {"src.one.aaaa1111": "s1", "src.two.bbbb2222": "s2"}
    rendered = family_display.render_person_card(
        row_id="person.solo", title_html="Sol Solo", ahnen_text="Z-1",
        tag="documented", display=solo, cite_map=cite_codes,
        record_cards_html=family_display.render_record_card(
            "ev.test.solo", card, "zimmerman"))
    check("extracted block round-trips to the source DOM",
          family_display.dom_stream(rendered) == family_display.dom_stream(SOLO_ROW),
          rendered)

    # 3. A title the rule cannot derive becomes an explicit override
    renamed = COUPLE_ROW.replace("Hank Husband + Wilma Wife",
                                 "Hank Husband/Harry + Wilma Wife")
    root = make_root(tmp / "override", renamed, PEOPLE,
                     registry={"v": 2, "people": REGISTRY["people"][:3]})
    result = run(root, "--section", "branch-doyle")
    check("override extraction exits 0", result.returncode == 0,
          result.stdout[-300:] + result.stderr[-300:])
    payload = json.loads(result.stdout)
    hus = payload["people"]["person.hus"]
    check("underivable title emits an override",
          hus.get("card_name") == "Hank Husband/Harry"
          or hus.get("title_override") == "Hank Husband/Harry + Wilma Wife", hus)

    # 4. A page tag disagreeing with the store REFUSES - data correction, not
    # a silent override
    wrong_tag = SOLO_ROW.replace('<span class="tag documented">Documented</span>',
                                 '<span class="tag strong">Strong lead</span>')
    root = make_root(tmp / "tagclash", wrong_tag,
                     [PEOPLE[0]], registry={"v": 2, "people": REGISTRY["people"][:1]})
    result = run(root, "--section", "branch-doyle")
    check("tag mismatch refuses", result.returncode != 0,
          result.stdout[-300:] + result.stderr[-300:])
    check("tag mismatch names the row", "person.solo" in result.stdout
          + result.stderr, result.stdout[-300:])

    # 5. Out-of-grammar markup REFUSES rather than guessing
    fancy = SOLO_ROW.replace("Kansas.", "<em>Kansas</em>.")
    root = make_root(tmp / "grammar", fancy,
                     [PEOPLE[0]], registry={"v": 2, "people": REGISTRY["people"][:1]})
    result = run(root, "--section", "branch-doyle")
    check("out-of-grammar markup refuses", result.returncode != 0,
          result.stdout[-300:] + result.stderr[-300:])

if failures:
    print("EXTRACT FAMILY DISPLAY TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("extract_family_display: all contract checks passed")
