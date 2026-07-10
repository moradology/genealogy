#!/usr/bin/env python3
"""Mutation-style regression tests for the canonical case contract."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_cases", ROOT / "tools" / "check_cases.py")
assert SPEC is not None and SPEC.loader is not None
check_cases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_cases)

records = check_cases.read_jsonl(ROOT / "research" / "cases" / "cases.jsonl")
gaps = check_cases.canonical_gaps()
person_ids = check_cases.canonical_person_ids()
trace_names = {path.name for path in (ROOT / "research" / "reasoning-traces").glob("20*.md")}
evidence_cases = check_cases.evidence_case_index()


def failures(candidate, candidate_gaps=gaps, candidate_evidence=evidence_cases):
    return check_cases.core_failures(
        candidate, candidate_gaps, person_ids, candidate_evidence, trace_names)


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
published_case = next(record["id"] for record in records if record["status"] != "closed")
synthetic_gap = {
    "id": "gap.test.published",
    "node_type": "gap",
    "case_refs": [published_case],
    "public_anchor": "gap.test.published",
}
next(record for record in closed if record["id"] == published_case)["status"] = "closed"
if not any(
    "published gap" in failure
    for failure in failures(closed, candidate_gaps=gaps + [synthetic_gap])
):
    problems.append("published-gap-to-closed-case mutation survived")

unknown_gap_case = copy.deepcopy(synthetic_gap)
unknown_gap_case["case_refs"] = ["case.99"]
if not any(
    "points to unknown case.99" in failure
    for failure in failures(records, candidate_gaps=gaps + [unknown_gap_case])
):
    problems.append("unresolved canonical gap case mutation survived")

bad_person = copy.deepcopy(records)
bad_person[0]["person_refs"] = ["person.presentation_only"]
if not any("unresolved person ref" in failure for failure in failures(bad_person)):
    problems.append("noncanonical presentation-only person mutation survived")

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

no_note = copy.deepcopy(records)
no_note[0]["source_note"] = ""
if not any("source_note is required" in failure for failure in failures(no_note)):
    problems.append("empty source_note mutation survived")

piped_note = copy.deepcopy(records)
piped_note[0]["source_note"] = "census|shorthand"
if not any("must not contain '|'" in failure for failure in failures(piped_note)):
    problems.append("piped source_note mutation survived")

entity_prose = copy.deepcopy(records)
entity_prose[0]["display_prose"] = "prose with &mdash; entity"
if not any("plain unicode" in failure for failure in failures(entity_prose)):
    problems.append("entity display_prose mutation survived")

empty_prose = copy.deepcopy(records)
empty_prose[0]["display_prose"] = ""
if not any("display_prose must be non-empty" in failure for failure in failures(empty_prose)):
    problems.append("empty display_prose mutation survived")

if problems:
    for problem in problems:
        print(problem, file=sys.stderr)
    raise SystemExit(1)
print("test_check_cases: all 11 mutations rejected")
