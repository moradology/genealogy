#!/usr/bin/env python3
"""Contract tests for tools/page_map.py (the site's id -> page assignment).

Offline, stdlib only, no try/except. page_map is the single answer to "which
page does this id live on": person/gap ids via their branch, cases via their
branch, sN ledger codes always on the landing page. The split configuration is
EXISTENCE-DRIVEN: a branch is split out exactly when its page file exists, so
intermediate migration states need no code edits.
Run: uv run tools/test_page_map.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import page_map  # noqa: E402

failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def jl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)


def make_root(tmp: Path, pages: tuple = ()) -> Path:
    root = tmp / "repo"
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "cases").mkdir(parents=True)
    (root / "research" / "sources").mkdir(parents=True)
    (root / "research" / "people" / "people.jsonl").write_text(jl([
        {"id": "person.z-one", "branches": ["zimmerman"]},
        {"id": "person.m-one", "branches": ["mundell"]},
        {"id": "person.d-one", "branches": ["dible"]},
        {"id": "person.c-one", "branches": ["connelly"]},
    ]), encoding="utf-8")
    (root / "research" / "people" / "relationships.jsonl").write_text(jl([
        {"id": "gap.z-one.parents", "node_type": "gap", "branches": ["zimmerman"]},
        {"id": "relationship.parent.x-to-y", "node_type": "relationship",
         "branches": ["zimmerman"]},
    ]), encoding="utf-8")
    (root / "research" / "cases" / "cases.jsonl").write_text(jl([
        {"id": "case.01", "branch": "zimmerman"},
        {"id": "case.02", "branch": "mundell"},
    ]), encoding="utf-8")
    (root / "research" / "sources" / "sources.jsonl").write_text(jl([
        {"id": "src.one.aaaa1111", "html_id": "s1"},
        {"id": "src.two.bbbb2222", "html_id": "s2"},
    ]), encoding="utf-8")
    (root / "index.html").write_text("<html></html>", encoding="utf-8")
    for page in pages:
        (root / page).write_text("<html></html>", encoding="utf-8")
    return root


with tempfile.TemporaryDirectory(prefix="page-map-test-") as td:
    tmp = Path(td)

    # Nothing split: every id lives on the landing page
    root = make_root(tmp / "mono")
    check("split is empty with no page files",
          page_map.split_branches(root) == frozenset(), page_map.split_branches(root))
    assignments = page_map.page_assignments(root)
    check("all ids assigned", set(assignments) >= {
        "person.z-one", "person.m-one", "gap.z-one.parents",
        "case.01", "case.02", "s1", "s2"}, sorted(assignments))
    check("monolith maps everything to index",
          set(assignments.values()) == {"index.html"}, assignments)

    # Zimmerman split out: existence of the file drives the assignment
    root = make_root(tmp / "twopage", pages=("zimmerman.html",))
    check("split follows existing files",
          page_map.split_branches(root) == frozenset({"zimmerman"}),
          page_map.split_branches(root))
    assignments = page_map.page_assignments(root)
    check("zimmerman ids move to their page",
          assignments["person.z-one"] == "zimmerman.html"
          and assignments["gap.z-one.parents"] == "zimmerman.html"
          and assignments["case.01"] == "zimmerman.html", assignments)
    check("other branches stay on the landing",
          assignments["person.m-one"] == "index.html"
          and assignments["case.02"] == "index.html", assignments)
    check("ledger codes always land on the landing",
          assignments["s1"] == "index.html" and assignments["s2"] == "index.html",
          assignments)

    # href: bare iff same page, qualified otherwise
    check("same-page href is bare",
          page_map.href(assignments, "person.z-one", "zimmerman.html")
          == "#person.z-one")
    check("cross-page href is qualified",
          page_map.href(assignments, "person.z-one", "index.html")
          == "zimmerman.html#person.z-one")
    check("landing-bound href from a person page is qualified",
          page_map.href(assignments, "s1", "zimmerman.html") == "index.html#s1")
    check("landing-bound href on the landing is bare",
          page_map.href(assignments, "case.02", "index.html") == "#case.02")

    # Unknown ids hard-fail with ProjectionError
    snippet = (
        "import sys; sys.path.insert(0, 'tools'); import page_map; "
        f"a = page_map.page_assignments(__import__('pathlib').Path({str(root)!r})); "
        "page_map.href(a, 'person.nobody', 'index.html')"
    )
    result = subprocess.run([sys.executable, "-c", snippet], cwd=REPO,
                            capture_output=True, text=True)
    check("unknown id hard-fails", result.returncode != 0,
          result.stdout + result.stderr)
    check("unknown id failure is a ProjectionError",
          "ProjectionError" in result.stderr, result.stderr[-300:])

if failures:
    print("PAGE MAP TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("page_map: all contract checks passed")
