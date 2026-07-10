#!/usr/bin/env python3
"""Contract tests for tools/check_pages.py (cross-file link integrity).

Offline, stdlib only, no try/except. check_pages parses every site page once
and validates: bare #x hrefs resolve on their own page; qualified page.html#x
hrefs resolve on that page; canonical anchors (person/gap public anchors,
cases, sN ledger codes) occur exactly once site-wide AND on the page
page_map assigns; no duplicate ids within a page. It is the cross-file
replacement for the single-DOM C9 class. Run: uv run tools/test_check_pages.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "tools/check_pages.py"
failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True, text=True)


def jl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)


def write_stores(root: Path) -> None:
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "cases").mkdir(parents=True)
    (root / "research" / "sources").mkdir(parents=True)
    (root / "research" / "people" / "people.jsonl").write_text(jl([
        {"id": "person.z-one", "branches": ["zimmerman"],
         "public_anchor": "person.z-one"},
        {"id": "person.m-one", "branches": ["mundell"],
         "public_anchor": "person.m-one"},
    ]), encoding="utf-8")
    (root / "research" / "people" / "relationships.jsonl").write_text(jl([
        {"id": "gap.z-one.parents", "node_type": "gap",
         "branches": ["zimmerman"], "public_anchor": "gap.z-one.parents"},
    ]), encoding="utf-8")
    (root / "research" / "cases" / "cases.jsonl").write_text(jl([
        {"id": "case.01", "branch": "zimmerman"},
    ]), encoding="utf-8")
    (root / "research" / "sources" / "sources.jsonl").write_text(jl([
        {"id": "src.one.aaaa1111", "html_id": "s1"},
    ]), encoding="utf-8")


INDEX_OK = (
    '<html><body>'
    '<a href="#s1">s1</a>'
    '<a href="zimmerman.html#person.z-one">Z One</a>'
    '<a href="zimmerman.html#case.01">case.01</a>'
    '<li id=s1>ledger row</li>'
    '<div id="person.m-one">M One card</div>'
    "</body></html>"
)
ZIMMERMAN_OK = (
    '<html><body>'
    '<a href="#person.z-one">self link</a>'
    '<a href="index.html#s1">s1</a>'
    '<a href="index.html#person.m-one">M One</a>'
    '<div id="person.z-one">card</div>'
    '<div id="gap.z-one.parents">gap card</div>'
    '<div id="case.01">case</div>'
    "</body></html>"
)


def make_site(tmp: Path, index_html: str = INDEX_OK,
              zimmerman_html: str | None = ZIMMERMAN_OK) -> Path:
    root = tmp / "site"
    root.mkdir(parents=True)
    write_stores(root)
    (root / "index.html").write_text(index_html, encoding="utf-8")
    if zimmerman_html is not None:
        (root / "zimmerman.html").write_text(zimmerman_html, encoding="utf-8")
    return root


with tempfile.TemporaryDirectory(prefix="check-pages-test-") as td:
    tmp = Path(td)

    # 1. A coherent two-page site passes
    result = run(make_site(tmp / "ok"))
    check("coherent site passes", result.returncode == 0,
          result.stdout + result.stderr)

    # 2. A broken bare anchor fails and is named
    result = run(make_site(tmp / "bare",
                           index_html=INDEX_OK.replace('href="#s1"',
                                                       'href="#s99"')))
    check("broken bare anchor fails", result.returncode == 1, result.stdout)
    check("broken bare anchor named", "s99" in result.stdout, result.stdout)

    # 3. A qualified href to a missing anchor fails
    result = run(make_site(
        tmp / "qual",
        index_html=INDEX_OK.replace("zimmerman.html#person.z-one",
                                    "zimmerman.html#person.gone")))
    check("broken qualified href fails", result.returncode == 1, result.stdout)

    # 4. A qualified href to a page that does not exist fails
    result = run(make_site(
        tmp / "nopage",
        index_html=INDEX_OK.replace("zimmerman.html#case.01",
                                    "dible.html#case.01")))
    check("href to absent page fails", result.returncode == 1, result.stdout)

    # 5. A canonical anchor on the WRONG page per page_map fails
    result = run(make_site(
        tmp / "misplaced",
        index_html=INDEX_OK + '<div id="person.z-one">stray copy</div>'))
    check("misplaced canonical anchor fails", result.returncode == 1,
          result.stdout)

    # 6. A duplicate id within one page fails
    result = run(make_site(
        tmp / "dupe",
        zimmerman_html=ZIMMERMAN_OK + '<div id="case.01">again</div>'))
    check("duplicate id within a page fails", result.returncode == 1,
          result.stdout)

    # 7. A canonical anchor missing from the whole site fails
    result = run(make_site(
        tmp / "absent",
        zimmerman_html=ZIMMERMAN_OK.replace(
            '<div id="gap.z-one.parents">gap card</div>', "")))
    check("missing canonical anchor fails", result.returncode == 1,
          result.stdout)

if failures:
    print("CHECK PAGES TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("check_pages: all contract checks passed")
