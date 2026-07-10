#!/usr/bin/env python3
"""Acceptance checks for the docket projection builder (tools/build_docket.py).

Offline, stdlib only, no try/except. Exercises write, --check, and
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


# Hand-authored docket in the CURRENT page style: entities, a two-segment refs
# div, and one MALFORMED div (trace id embedded in the middle segment,
# no third pipe) mirroring the real case.07.
HAND_DOCKET = (
    '<div id="case.01"><div><b>case.01</b><h3>Alpha &amp; entities</h3><b>OPEN</b></div>'
    "<p>Q: alpha &mdash; with an entity dash.</p>"
    '<div><a href="#person.alpha">Z-4/5</a>|1885 KS census; notes|trace.2026-01-01.alpha-trace</div></div>\n'
    '<div id="case.02"><div><b>case.02</b><h3>Beta-&gt;arrow</h3><b>IN CONFLICT</b></div>'
    "<p>Q: beta.</p>"
    '<div><a href="#person.beta">M-3</a>|Beta memorials trace.2026-01-02.beta-trace</div></div>\n'
)

HTML_TEMPLATE = (
    "<html><head></head><body>\n"
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


def person(pid: str, name: str, branches: list[str], role: str = "ancestor",
           confidence: str = "documented", anchor: str | None = None) -> dict:
    return {
        "id": pid,
        "node_type": "person",
        "display_name": name,
        "index_names": [name],
        "name_variants": [],
        "branches": branches,
        "role": role,
        "confidence": confidence,
        "privacy": "public_deceased",
        "public_anchor": anchor or pid,
    }


def plink(parent: str, child: str, branch: str,
          parent_role: str = "father") -> dict:
    return {
        "id": f"relationship.parent.{parent.split('.')[-1]}-to-{child.split('.')[-1]}",
        "node_type": "relationship",
        "relationship_type": "parent_of",
        "parent_role": parent_role,
        "person_a": parent,
        "person_b": child,
        "status": "accepted",
        "confidence": "documented",
        "branches": [branch],
        "evidence_refs": [],
        "source_refs": ["src.test.relationship"],
        "case_refs": [],
        "provenance_note": "test",
    }


def people_rows() -> list[dict]:
    return [
        person("person.z_anchor", "Zara Zimmerman", ["zimmerman"],
               role="anchor"),
        person("person.z_parent", "Zane Zimmerman", ["zimmerman"]),
        person("person.alpha", "Alpha, Ada", ["zimmerman"],
               confidence="strong"),
        person("person.alpha_wife", "Alpha, Win", ["zimmerman"],
               confidence="strong", anchor="person.alpha"),
        person("person.gamma_collateral", "Gamma, Gil collateral",
               ["zimmerman"], role="collateral", confidence="lead"),
        person("person.m_anchor", "Mona Mundell", ["mundell"],
               role="anchor"),
        person("person.beta", "Beta, Bo", ["mundell"]),
        person("person.d_anchor", "Dina Dible", ["dible"], role="anchor"),
        person("person.c_anchor", "Cora Connelly", ["connelly"],
               role="anchor"),
    ]


def relationship_rows() -> list[dict]:
    return [
        plink("person.z_parent", "person.z_anchor", "zimmerman"),
        plink("person.alpha", "person.z_parent", "zimmerman"),
        plink("person.alpha_wife", "person.z_parent", "zimmerman",
              parent_role="mother"),
        plink("person.beta", "person.m_anchor", "mundell",
              parent_role="mother"),
    ]


def case_record(case_id: str, title: str, summary: str, status: str, person_refs: list[str],
                trace_refs: list[str], source_note: str = "test sources", **extra) -> dict:
    rec = {
        "id": case_id,
        "node_type": "case",
        "branch": "zimmerman",
        "title": title,
        "status": status,
        "summary": summary,
        "source_note": source_note,
        "person_refs": person_refs,
        "evidence_refs": [],
        "trace_refs": trace_refs,
    }
    rec.update(extra)
    return rec


def make_fixture(tmp: Path) -> Path:
    root = tmp / "repo"
    (root / "research" / "cases").mkdir(parents=True)
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "reasoning-traces").mkdir(parents=True)
    for name in ("2026-01-01-alpha-trace.md", "2026-01-02-beta-trace.md"):
        (root / "research" / "reasoning-traces" / name).write_text("---\n---\n")
    records = [
        case_record("case.01", "Alpha & entities", "Q: alpha — with an entity dash.", "open",
                    ["person.alpha", "person.alpha_wife"], ["trace.2026-01-01.alpha-trace"],
                    source_note="1885 KS census; notes"),
        case_record("case.02", "Beta->arrow", "Q: beta.", "in_conflict",
                    ["person.beta"], [], source_note="Beta memorials"),
    ]
    lines = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records)
    (root / "research" / "cases" / "cases.jsonl").write_text(lines)
    people_lines = "".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n"
        for r in people_rows()
    )
    (root / "research" / "people" / "people.jsonl").write_text(people_lines)
    relationship_lines = "".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n"
        for r in relationship_rows()
    )
    (root / "research" / "people" / "relationships.jsonl").write_text(
        relationship_lines)
    (root / "index.html").write_text(
        HTML_TEMPLATE.format(docket=HAND_DOCKET))
    return root


def read_cases(root: Path) -> list[dict]:
    return [json.loads(x) for x in (root / "research/cases/cases.jsonl").read_text().splitlines() if x.strip()]


with tempfile.TemporaryDirectory(prefix="build-docket-test-") as td:
    root = make_fixture(Path(td))
    html_path = root / "index.html"

    # ---- 2. write mode: markers inserted, canonical render, region-contained ----
    r = run(root)
    check("write exit 0", r.returncode == 0, r.stderr[:300])
    html = html_path.read_text()
    check("markers present", "<!-- BEGIN docket-cases -->" in html and "<!-- END -->" in html, html[:200])
    check("markers inside docket section", html.index('id="docket"') < html.index("<!-- BEGIN docket-cases -->") < html.index("<h3>Corrigenda</h3>"))
    check("entity normalized to unicode", "— with an entity dash" in html)
    check("arrow escaped roundtrip", "Beta-&gt;arrow" in html)
    check("label derived from stores", '<a href="#person.alpha">Z-4/5</a>' in html)
    check("status label mapped", "<b>IN CONFLICT</b>" in html)
    check("trace ref rendered", "|trace.2026-01-01.alpha-trace</div>" in html)
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
