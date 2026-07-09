#!/usr/bin/env python3
"""Mutation-style regression tests for the canonical case contract."""

from __future__ import annotations

import copy
import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_cases", ROOT / "tools" / "check_cases.py")
assert SPEC is not None and SPEC.loader is not None
check_cases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_cases)

html = (ROOT / "index.html").read_text()
records = check_cases.read_jsonl(ROOT / "research" / "cases" / "cases.jsonl")
docket = check_cases.docket_records(html)
people = check_cases.people_index(html)
person_ids = set(re.findall(r'id="(person\.[A-Za-z0-9_.-]+)"', html))
trace_names = {path.name for path in (ROOT / "research" / "reasoning-traces").glob("20*.md")}
evidence_cases = check_cases.evidence_case_index()


def failures(candidate, candidate_people=people, candidate_evidence=evidence_cases):
    return check_cases.core_failures(
        candidate, docket, candidate_people, person_ids, candidate_evidence, trace_names)


problems = []
if failures(records):
    problems.append("baseline canonical cases fail")

duplicate = copy.deepcopy(records)
duplicate.append(copy.deepcopy(duplicate[-1]))
if not any("duplicate case id" in failure for failure in failures(duplicate)):
    problems.append("duplicate case mutation survived")

gap = copy.deepcopy(records)
del gap[1]
if not any("append-only and sequential" in failure for failure in failures(gap)):
    problems.append("case sequence gap mutation survived")

closed = copy.deepcopy(records)
next(record for record in closed if record["id"] == "case.23")["status"] = "closed"
if not any("open slot" in failure for failure in failures(closed)):
    problems.append("open-slot-to-closed-case mutation survived")

bad_ref = copy.deepcopy(records)
bad_ref[0]["evidence_refs"] = ["ev.missing"]
if not any("unresolved evidence ref" in failure for failure in failures(bad_ref)):
    problems.append("unresolved evidence mutation survived")

missing_reciprocal = copy.deepcopy(evidence_cases)
first_case = records[0]
first_evidence = first_case["evidence_refs"][0]
missing_reciprocal[first_evidence].discard(first_case["id"])
if not any(
    "does not reciprocally list the case" in failure
    for failure in failures(records, candidate_evidence=missing_reciprocal)
):
    problems.append("missing reciprocal case ref mutation survived")

if problems:
    for problem in problems:
        print(problem, file=sys.stderr)
    raise SystemExit(1)
print("test_check_cases: all 5 mutations rejected")
