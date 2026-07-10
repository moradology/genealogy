#!/usr/bin/env python3
"""Contract tests for tools/family_display.py (page-projection render seams).

Offline, stdlib only, no try/except. Pins the exact byte shapes the family
generators emit: token expansion (including the unquoted-attribute cite
anchors), escape-once semantics, both record-card variants, cameo figures,
alias spans, ahnen labels, and dom_stream equivalence.
Run: uv run tools/test_family_display.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import family_display  # noqa: E402

failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


CITE_MAP = {"src.test.alpha": "s1", "src.test.beta": "s2"}

# ---------- render_prose: tokens and escape-once ----------
check("plain text escapes ampersands",
      family_display.render_prose("Smith & Sons", CITE_MAP) == "Smith &amp; Sons")
check("unicode text passes through raw",
      family_display.render_prose("1880–1930 · Kansas", CITE_MAP) == "1880–1930 · Kansas")
check("cite token renders unquoted anchor bytes",
      family_display.render_prose("proof.{{cite:src.test.alpha}}", CITE_MAP)
      == "proof.<a class=cite href=#s1>s1</a>")
check("two cites resolve independently",
      family_display.render_prose("{{cite:src.test.alpha}}{{cite:src.test.beta}}", CITE_MAP)
      == "<a class=cite href=#s1>s1</a><a class=cite href=#s2>s2</a>")
check("case token renders a case chip",
      family_display.render_prose("See {{case:case.07}}.", CITE_MAP)
      == 'See <a class="case-chip" href="#case.07">case.07</a>.')
check("link token renders internal link with escaped label",
      family_display.render_prose("{{link:#person.a|Ann & Co}}", CITE_MAP)
      == '<a href="#person.a">Ann &amp; Co</a>')
check("url token renders external link",
      family_display.render_prose("{{url:https://example.org/x?a=1|the notice}}", CITE_MAP)
      == '<a href="https://example.org/x?a=1">the notice</a>')
check("vs token renders the span",
      family_display.render_prose("1922{{vs}}1923", CITE_MAP)
      == '1922<span class="vs">vs.</span>1923')
check("link token validates known anchors when given",
      family_display.render_prose("{{link:#person.a|Ann}}", CITE_MAP,
                                  known_anchors={"person.a"})
      == '<a href="#person.a">Ann</a>')

# Failure paths hard-fail: exercise through a subprocess so the no-try/except
# rule holds in this test too
snippet = (
    "import sys; sys.path.insert(0, 'tools'); import family_display; "
    "family_display.render_prose('{{cite:src.missing}}', {})"
)
result = subprocess.run([sys.executable, "-c", snippet],
                        cwd=Path(__file__).resolve().parents[1],
                        capture_output=True, text=True)
check("unresolvable cite hard-fails", result.returncode != 0, result.stdout)
snippet = (
    "import sys; sys.path.insert(0, 'tools'); import family_display; "
    "family_display.render_prose('{{link:#nowhere|X}}', {}, known_anchors=set())"
)
result = subprocess.run([sys.executable, "-c", snippet],
                        cwd=Path(__file__).resolve().parents[1],
                        capture_output=True, text=True)
check("unknown link anchor hard-fails", result.returncode != 0, result.stdout)

# ---------- page-context rendering (five-page split) ----------
ASSIGN = {"src.test.alpha": "index.html", "s1": "index.html",
          "case.07": "index.html", "person.a": "zimmerman.html",
          "person.m": "index.html"}
check("cite token qualifies to the landing from a person page",
      family_display.render_prose("proof.{{cite:src.test.alpha}}", CITE_MAP,
                                  page_context=(ASSIGN, "zimmerman.html"))
      == "proof.<a class=cite href=index.html#s1>s1</a>")
check("cite token stays bare on the landing",
      family_display.render_prose("proof.{{cite:src.test.alpha}}", CITE_MAP,
                                  page_context=(ASSIGN, "index.html"))
      == "proof.<a class=cite href=#s1>s1</a>")
check("case token qualifies cross-page",
      family_display.render_prose("See {{case:case.07}}.", CITE_MAP,
                                  page_context=(ASSIGN, "zimmerman.html"))
      == 'See <a class="case-chip" href="index.html#case.07">case.07</a>.')
check("link token qualifies cross-page",
      family_display.render_prose("{{link:#person.m|Mira}}", CITE_MAP,
                                  page_context=(ASSIGN, "zimmerman.html"))
      == '<a href="index.html#person.m">Mira</a>')
check("link token stays bare same-page",
      family_display.render_prose("{{link:#person.a|Ann}}", CITE_MAP,
                                  page_context=(ASSIGN, "zimmerman.html"))
      == '<a href="#person.a">Ann</a>')
check("no page context keeps today's bare behavior",
      family_display.render_prose("{{link:#person.a|Ann}}", CITE_MAP)
      == '<a href="#person.a">Ann</a>')

# ---------- cite map loader ----------
with tempfile.TemporaryDirectory(prefix="family-display-test-") as td:
    root = Path(td)
    (root / "research" / "sources").mkdir(parents=True)
    rows = [{"id": "src.one.aaaa1111", "html_id": "s1"},
            {"id": "src.two.bbbb2222", "html_id": "s2"}]
    (root / "research" / "sources" / "sources.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    loaded = family_display.cite_map(root)
    check("cite map loads id -> html_id",
          loaded == {"src.one.aaaa1111": "s1", "src.two.bbbb2222": "s2"}, loaded)
    rows[1]["html_id"] = "s9"
    (root / "research" / "sources" / "sources.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, 'tools'); import family_display; "
         f"family_display.cite_map(__import__('pathlib').Path('{td}'))"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    check("cite map rejects non-positional html_id", result.returncode != 0,
          result.stdout)

# ---------- ahnen labels ----------
check("single slot", family_display.ahnen_label("Z", [1]) == "Z-1")
check("couple slots use the interpunct",
      family_display.ahnen_label("M", [4, 5]) == "M-4·5")
check("non-contiguous slots stay itemized",
      family_display.ahnen_label("D", [16, 20]) == "D-16·20")
check("long contiguous runs compress to a range",
      family_display.ahnen_label("Z", [24, 25, 26, 27]) == "Z-24–27")
check("empty slots return None", family_display.ahnen_label("C", []) is None)

# ---------- record cards, both variants ----------
FIELDS_DISPLAY = {
    "variant": "fields",
    "head": "Colorado Divorce Index, 1851–1985",
    "fields": [{"dt": "Name", "dd": "Homer C. Mundell"},
               {"dt": "Spouse", "dd": "Marjorie Evelyn Mundell", "focal": True},
               {"dt": "Divorced", "dd": "26 Jun 1939"}],
    "cite": "The record that preserved her middle name · via Ancestry",
}
expected_fields_card = (
    '<figure class="record-card anchor-mundell" '
    'data-evidence-id="ev.test.divorce">'
    '<figcaption class="record-head">Colorado Divorce Index, 1851–1985</figcaption>'
    '<dl class="record-fields">'
    "<div><dt>Name</dt><dd>Homer C. Mundell</dd></div>"
    '<div class="focal"><dt>Spouse</dt><dd>Marjorie Evelyn Mundell</dd></div>'
    "<div><dt>Divorced</dt><dd>26 Jun 1939</dd></div>"
    "</dl>"
    '<p class="record-cite">The record that preserved her middle name '
    "· via Ancestry</p></figure>"
)
check("fields-variant card renders exact bytes",
      family_display.render_record_card("ev.test.divorce", FIELDS_DISPLAY, "mundell")
      == expected_fields_card,
      family_display.render_record_card("ev.test.divorce", FIELDS_DISPLAY, "mundell"))

ROLL_DISPLAY = {
    "variant": "roll",
    "head": "1910 U.S. Census · Martin Township",
    "roll": [{"cells": ["Etta Rust", "34", "Head, widowed"]},
             {"cells": ["Francis Rust", "15", "Daughter"], "focal": True}],
    "cite": "ED 0197, sheet 8A · via Ancestry",
}
expected_roll_card = (
    '<figure class="record-card anchor-mundell" data-evidence-id="ev.test.roll">'
    '<figcaption class="record-head">1910 U.S. Census · Martin Township</figcaption>'
    '<table class="record-roll"><tbody>'
    "<tr><td>Etta Rust</td><td>34</td><td>Head, widowed</td></tr>"
    '<tr class="focal"><td>Francis Rust</td><td>15</td><td>Daughter</td></tr>'
    "</tbody></table>"
    '<p class="record-cite">ED 0197, sheet 8A · via Ancestry</p></figure>'
)
check("roll-variant card renders exact bytes",
      family_display.render_record_card("ev.test.roll", ROLL_DISPLAY, "mundell")
      == expected_roll_card,
      family_display.render_record_card("ev.test.roll", ROLL_DISPLAY, "mundell"))

# ---------- person and gap cards ----------
person_display = {
    "identity": "Anchor of the test line; spouse of {{link:#person.b|Bea}}.",
    "details": "Documented at the county seat.{{cite:src.test.alpha}}",
    "vitals": "b. 1900 – d. 1980",
    "cameos": [{"src": "images/people/a.jpg", "alt": "Ann at the farm",
                "width": 137, "height": 157,
                "credit_url": "https://example.org/a",
                "credit_label": "Photo: archive"}],
}
rendered = family_display.render_person_card(
    row_id="person.a", title_html="Ann Alpha", ahnen_text="Z-1", tag="documented",
    display=person_display, cite_map=CITE_MAP, record_cards_html="")
expected_person = (
    '<div class="person" id="person.a"><div class="person-head">'
    '<span class="person-name">Ann Alpha</span> <span class="ahnen">Z-1</span> '
    '<span class="tag documented">Documented</span></div>'
    '<div class="vitals">b. 1900 – d. 1980</div>'
    '<p class="identity">Anchor of the test line; spouse of '
    '<a href="#person.b">Bea</a>.</p>'
    '<div class="person-details"><figure class="cameo">'
    '<img src="images/people/a.jpg" alt="Ann at the farm" width="137" '
    'height="157" loading="lazy"><figcaption>'
    '<a href="https://example.org/a">Photo: archive</a></figcaption></figure>'
    'Documented at the county seat.<a class=cite href=#s1>s1</a></div></div>'
)
check("person card renders exact bytes", rendered == expected_person, rendered)

gap_display = {
    "identity": "The open Gen 5 slot.",
    "details": "Not yet proven. Best target: the parish register.",
}
rendered = family_display.render_person_card(
    row_id="gap.a.parents", title_html="Parents of Ann", ahnen_text="Z-16·17",
    tag="open", display=gap_display, cite_map=CITE_MAP,
    record_cards_html="", alias_ids=("person.ghost.one", "person.ghost.two"))
check("gap card leads with alias spans",
      rendered.startswith('<div class="person" id="gap.a.parents">'
                          '<span id="person.ghost.one"></span>'
                          '<span id="person.ghost.two"></span>'
                          '<div class="person-head">'), rendered)
check("gap card omits vitals when absent",
      '<div class="vitals">' not in rendered, rendered)
check("record cards trail the details div",
      family_display.render_person_card(
          row_id="person.a", title_html="Ann", ahnen_text="Z-1", tag="documented",
          display={"identity": "x.", "details": "y."}, cite_map=CITE_MAP,
          record_cards_html=expected_roll_card,
      ).endswith("y.</div>" + expected_roll_card + "</div>"))

# person cards thread the page context through every prose field
rendered = family_display.render_person_card(
    row_id="person.a", title_html="Ann Alpha", ahnen_text="Z-1",
    tag="documented",
    display={"identity": "See {{case:case.07}}.",
             "details": "Proof.{{cite:src.test.alpha}}"},
    cite_map=CITE_MAP, page_context=(ASSIGN, "zimmerman.html"))
check("person card qualifies cross-page tokens",
      'href="index.html#case.07"' in rendered
      and "href=index.html#s1" in rendered, rendered)

# ---------- dom_stream ----------
check("entities and unicode stream identically",
      family_display.dom_stream("<div>a &ndash; b</div>")
      == family_display.dom_stream("<div>a – b</div>"))
check("attribute order is canonicalized",
      family_display.dom_stream('<a href="#x" class=cite>s1</a>')
      == family_display.dom_stream('<a class=cite href="#x">s1</a>'))
check("text differences are visible",
      family_display.dom_stream("<div>alpha</div>")
      != family_display.dom_stream("<div>beta</div>"))
check("structure differences are visible",
      family_display.dom_stream("<div><b>a</b></div>")
      != family_display.dom_stream("<div>a</div>"))

if failures:
    print("FAMILY DISPLAY TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("family_display: all contract checks passed")
