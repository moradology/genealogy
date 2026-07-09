#!/usr/bin/env python3
"""Mutation-style regression tests for strict reasoning-trace frontmatter."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import check_traces


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "research/reasoning-traces"

universes, universe_errors = check_traces.load_universes(ROOT)
documents = {
    path.name: path.read_text(encoding="utf-8")
    for path in sorted(TRACE_DIR.glob("*.md"))
    if path.name not in check_traces.SKIPPED_NAMES
}


def failures(candidate: dict[str, str]) -> list[str]:
    return check_traces.validate_documents(candidate, universes)


problems: list[str] = []
if universe_errors:
    problems.append(f"canonical universes fail: {universe_errors}")
if failures(documents):
    problems.append(f"baseline reasoning traces fail: {failures(documents)}")

missing_frontmatter = copy.deepcopy(documents)
name = "2026-07-08-slate3-evidence-gates.md"
missing_frontmatter[name] = missing_frontmatter[name].split("---", 2)[2].lstrip()
if not any("missing strict frontmatter" in error for error in failures(missing_frontmatter)):
    problems.append("missing-frontmatter mutation survived")

legacy_frontmatter = copy.deepcopy(documents)
name = "2026-07-07-zimmerman-mainhardt-archion.md"
legacy_frontmatter[name] = legacy_frontmatter[name].replace(
    "date: 2026-07-07", "date_created: 2026-07-07", 1
)
if not any("must be 'date'" in error for error in failures(legacy_frontmatter)):
    problems.append("legacy-frontmatter mutation survived")

bad_evidence = copy.deepcopy(documents)
name = "2026-07-08-ancestry-pull-adjudication.md"
bad_evidence[name] = bad_evidence[name].replace(
    "ev.ancestry.1830-1841-rust-parish", "ev.missing", 1
)
if not any("unresolved evidence ref" in error for error in failures(bad_evidence)):
    problems.append("unresolved-evidence mutation survived")

undeclared_body_ref = copy.deepcopy(documents)
name = "2026-07-08-ancestry-pull-adjudication.md"
undeclared_body_ref[name] = undeclared_body_ref[name].replace(
    ', "case.21"]', "]", 1
)
if not any(
    "body ref case.21 is missing from case_refs" in error
    for error in failures(undeclared_body_ref)
):
    problems.append("undeclared-body-reference mutation survived")

duplicate_id = copy.deepcopy(documents)
name = "2026-07-07-zodrow-sabanka-lebehnke.md"
duplicate_id[name] = duplicate_id[name].replace(
    "trace.2026-07-07.zodrow-sabanka-lebehnke",
    "trace.2026-07-07.mundell-rust-frances-adolph",
    1,
)
if not any("duplicate trace id" in error for error in failures(duplicate_id)):
    problems.append("duplicate-trace-id mutation survived")

unsorted_refs = copy.deepcopy(documents)
name = "2026-07-08-mundell-patents-validation.md"
unsorted_refs[name] = unsorted_refs[name].replace(
    '["case.22"]', '["case.22", "case.01"]', 1
)
if not any("case_refs must be sorted" in error for error in failures(unsorted_refs)):
    problems.append("unsorted-reference mutation survived")

bad_geo = copy.deepcopy(documents)
name = "2026-07-08-slate3-evidence-gates.md"
bad_geo[name] = bad_geo[name].replace(
    "event.donna_connelly.birth.1935-04-24", "event.missing", 1
)
if not any("unresolved geo ref" in error for error in failures(bad_geo)):
    problems.append("unresolved-geo mutation survived")

if problems:
    for problem in problems:
        print(problem, file=sys.stderr)
    raise SystemExit(1)
print("test_check_traces: all 7 mutations rejected")
