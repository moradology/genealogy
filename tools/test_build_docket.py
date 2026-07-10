#!/usr/bin/env python3
"""Acceptance checks for the docket projection builder (tools/build_docket.py).

Offline, stdlib only, no try/except. Exercises --migrate, write, --check, and
error paths against a synthetic fixture repo via --root, in the same style as
test_build_people_index.py. Run: uv run tools/test_build_docket.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "tools/build_docket.py"
failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BUILDER), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


PEOPLE_INDEX = {
    "v": 1,
    "people": [
        # alpha + alpha_wife share one card anchor: refs to both must merge into
        # a single couple-style link Z-12/13.
        {"i": "person.alpha", "n": "Alpha, Ada", "a": "Z", "k": "person", "ah": [12], "t": "strong", "h": "person.alpha"},
        {"i": "person.alpha_wife", "n": "Alpha, Win", "a": "Z", "k": "person", "ah": [13], "t": "strong", "h": "person.alpha"},
        {"i": "person.beta", "n": "Beta, Bo", "a": "M", "k": "person", "ah": [3], "t": "documented", "h": "person.beta"},
        {"i": "person.gamma_collateral", "n": "Gamma, Gil collateral", "a": "Z", "k": "collateral", "t": "lead", "h": "person.gamma_collateral"},
    ],
}

# Hand-authored docket in the CURRENT page style: entities, a two-segment refs
# div, and one MALFORMED div (trace filename embedded in the middle segment,
# no third pipe) mirroring the real case.07.
HAND_DOCKET = (
    '<div id="case.01"><div><b>case.01</b><h3>Alpha &amp; entities</h3><b>OPEN</b></div>'
    "<p>Q: alpha &mdash; with an entity dash.</p>"
    '<div><a href="#person.alpha">Z-12/13</a>|1885 KS census; notes|2026-01-01-alpha-trace.md</div></div>\n'
    '<div id="case.02"><div><b>case.02</b><h3>Beta-&gt;arrow</h3><b>IN CONFLICT</b></div>'
    "<p>Q: beta.</p>"
    '<div><a href="#person.beta">M-3</a>|Beta memorials 2026-01-02-beta-trace.md</div></div>\n'
)

HTML_TEMPLATE = (
    "<html><head></head><body>\n"
    '<script type="application/json" id="people-index">{blob}</script>\n'
    '<section class="sheet" id="docket">\n'
    "<h2>The Docket</h2>\n"
    "<p class=section-note>Append-only cases.</p>\n"
    "{docket}"
    "<h3>Corrigenda</h3>\n"
    "<ul>\n<li>hand-authored corrigendum stays untouched</li>\n</ul>\n"
    "</section>\n"
    '<section class="sheet" id="wanted"><h2>Wanted</h2></section>\n'
    "</body></html>\n"
)


def case_record(case_id: str, title: str, summary: str, status: str, person_refs: list[str],
                trace_refs: list[str], **extra) -> dict:
    rec = {
        "id": case_id,
        "node_type": "case",
        "branch": "zimmerman",
        "title": title,
        "status": status,
        "summary": summary,
        "person_refs": person_refs,
        "evidence_refs": [],
        "trace_refs": trace_refs,
    }
    rec.update(extra)
    return rec


def make_fixture(tmp: Path) -> Path:
    root = tmp / "repo"
    (root / "research" / "cases").mkdir(parents=True)
    (root / "research" / "reasoning-traces").mkdir(parents=True)
    for name in ("2026-01-01-alpha-trace.md", "2026-01-02-beta-trace.md"):
        (root / "research" / "reasoning-traces" / name).write_text("---\n---\n")
    records = [
        case_record("case.01", "Alpha & entities", "Q: alpha — with an entity dash.", "open",
                    ["person.alpha", "person.alpha_wife"], ["2026-01-01-alpha-trace.md"]),
        case_record("case.02", "Beta->arrow", "Q: beta.", "in_conflict",
                    ["person.beta"], []),
    ]
    lines = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records)
    (root / "research" / "cases" / "cases.jsonl").write_text(lines)
    (root / "index.html").write_text(
        HTML_TEMPLATE.format(blob=json.dumps(PEOPLE_INDEX, separators=(",", ":")), docket=HAND_DOCKET))
    return root


def read_cases(root: Path) -> list[dict]:
    return [json.loads(x) for x in (root / "research/cases/cases.jsonl").read_text().splitlines() if x.strip()]


with tempfile.TemporaryDirectory(prefix="build-docket-test-") as td:
    root = make_fixture(Path(td))
    html_path = root / "index.html"

    # ---- 1. --migrate extracts source_note; strips embedded trace token ----
    r = run(root, "--migrate")
    check("migrate exit 0", r.returncode == 0, r.stderr[:300])
    recs = {c["id"]: c for c in read_cases(root)}
    check("migrate source_note case.01", recs["case.01"].get("source_note") == "1885 KS census; notes", recs["case.01"].get("source_note"))
    check("migrate strips trace token from note",
          recs["case.02"].get("source_note") == "Beta memorials", recs["case.02"].get("source_note"))
    check("migrate merged stripped trace into trace_refs",
          recs["case.02"].get("trace_refs") == ["2026-01-02-beta-trace.md"], recs["case.02"].get("trace_refs"))
    check("migrate report mentions case.02", "case.02" in (r.stdout + r.stderr), r.stdout[:400])
    check("migrate never touches html", '<div id="case.01"><div><b>case.01</b><h3>Alpha &amp; entities</h3>' in html_path.read_text())

    # ---- 2. write mode: markers inserted, canonical render, region-contained ----
    r = run(root)
    check("write exit 0", r.returncode == 0, r.stderr[:300])
    html = html_path.read_text()
    check("markers present", "<!-- BEGIN docket-cases -->" in html and "<!-- END -->" in html, html[:200])
    check("markers inside docket section", html.index('id="docket"') < html.index("<!-- BEGIN docket-cases -->") < html.index("<h3>Corrigenda</h3>"))
    check("entity normalized to unicode", "— with an entity dash" in html)
    check("arrow escaped roundtrip", "Beta-&gt;arrow" in html)
    check("label derived from blob", '<a href="#person.alpha">Z-12/13</a>' in html)
    check("status label mapped", "<b>IN CONFLICT</b>" in html)
    check("trace ref rendered", "|2026-01-01-alpha-trace.md</div>" in html)
    check("corrigenda untouched", "hand-authored corrigendum stays untouched" in html)

    # ---- 3. idempotence + --check green, then stale after a JSONL edit ----
    before = html_path.read_bytes()
    r = run(root)
    check("second write idempotent", html_path.read_bytes() == before)
    r = run(root, "--check")
    check("check green", r.returncode == 0, r.stderr[:300])
    recs = read_cases(root)
    recs[0]["summary"] = "Q: alpha, edited."
    (root / "research/cases/cases.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in recs))
    r = run(root, "--check")
    check("check stale exit 1", r.returncode == 1, r.returncode)
    check("check remediation names ./gen", "./gen build docket" in (r.stdout + r.stderr), (r.stdout + r.stderr)[:300])

    # ---- 4. display_prose renders instead of summary ----
    recs = read_cases(root)
    recs[0]["display_prose"] = "A richer, hand-written docket paragraph."
    (root / "research/cases/cases.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in recs))
    r = run(root)
    check("prose write ok", r.returncode == 0, r.stderr[:300])
    html = html_path.read_text()
    check("display_prose rendered", "<p>A richer, hand-written docket paragraph.</p>" in html)
    check("summary not rendered when prose present", "<p>Q: alpha, edited.</p>" not in html)

    # ---- 5. collateral label fallback (no ah) ----
    recs = read_cases(root)
    recs[1]["person_refs"] = ["person.gamma_collateral"]
    (root / "research/cases/cases.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in recs))
    r = run(root)
    check("fallback write ok", r.returncode == 0, r.stderr[:300])
    check("fallback label is display name", ">Gamma, Gil collateral</a>" in html_path.read_text())

    # ---- 6. unknown person_ref: hard error, zero writes ----
    before = html_path.read_bytes()
    recs = read_cases(root)
    recs[1]["person_refs"] = ["person.does_not_exist"]
    (root / "research/cases/cases.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in recs))
    r = run(root)
    check("unknown ref nonzero exit", r.returncode != 0, r.returncode)
    check("unknown ref no write", html_path.read_bytes() == before)

if failures:
    print("BUILD DOCKET TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("build_docket: all contract checks passed")
