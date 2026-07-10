#!/usr/bin/env python3
"""Validate the canonical case JSONL store (semantic checks only).

The public docket is a GENERATED projection of this store: byte-identity with
the render is enforced by `build_docket.py --check` in the gate, so this
validator no longer parses or drift-compares the HTML docket. It owns the
JSONL contract: field shape, id sequence, cross-store references, the
published-gap rules, and the search-frame closure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "research" / "cases" / "cases.jsonl"
PEOPLE = ROOT / "research" / "people" / "people.jsonl"
RELATIONSHIPS = ROOT / "research" / "people" / "relationships.jsonl"
ALLOWED_STATUS = frozenset({"open", "in_conflict", "needs_pull", "closed"})
ALLOWED_BRANCH = frozenset({"zimmerman", "mundell", "dible", "connelly"})
# Docket text fields are plain unicode: never raw HTML, never pasted entities.
ENTITY_RE = re.compile(r"&#?[a-zA-Z0-9]+;")
TRACE_FILE_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md\Z"
)
TRACE_ID_RE = re.compile(
    r"trace\.\d{4}-\d{2}-\d{2}\.[a-z0-9]+(?:-[a-z0-9]+)*\Z"
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _lint_text(case_id: str, field: str, value: str, failures: list[str], forbid_pipe: bool = False) -> None:
    if "<" in value:
        failures.append(f"{case_id} {field} must not contain raw HTML ('<')")
    if ENTITY_RE.search(value):
        failures.append(f"{case_id} {field} must hold plain unicode, not HTML entities")
    if forbid_pipe and "|" in value:
        failures.append(f"{case_id} {field} must not contain '|' (docket field separator)")


def canonical_person_ids(path: Path = PEOPLE) -> set[str]:
    """Return the only person-reference universe: canonical actual people."""

    return {
        record["id"]
        for record in read_jsonl(path)
        if record.get("node_type") == "person" and isinstance(record.get("id"), str)
    }


def canonical_gaps(path: Path = RELATIONSHIPS) -> list[dict]:
    """Return canonical unresolved-family records used by the public projection."""

    return [
        record
        for record in read_jsonl(path)
        if record.get("node_type") == "gap"
    ]


def evidence_case_index(root: Path = ROOT) -> dict[str, set[str]]:
    index = {}
    for path in sorted((root / "research" / "evidence").glob("*.jsonl")):
        for record in read_jsonl(path):
            index[record["id"]] = set(record.get("case_refs", []))
    return index


def canonical_trace_ids(trace_dir: Path | None = None) -> set[str]:
    """Return trace front-matter identities, never filename aliases."""

    directory = trace_dir or ROOT / "research" / "reasoning-traces"
    trace_ids: set[str] = set()
    for path in sorted(directory.glob("20*.md")):
        match = TRACE_FILE_RE.fullmatch(path.name)
        if match is None:
            continue
        expected = f"trace.{match.group('date')}.{match.group('slug')}"
        id_match = re.search(
            r"^id:\s*(trace\.[a-z0-9.-]+)\s*$",
            path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
        if id_match is not None and id_match.group(1) == expected:
            trace_ids.add(expected)
    return trace_ids


def core_failures(
    records: list[dict],
    gaps: list[dict],
    person_ids: set[str],
    evidence_cases: dict[str, set[str]],
    trace_ids: set[str],
) -> list[str]:
    failures = []
    seen = set()
    by_id = {}
    required = {
        "id", "node_type", "branch", "title", "status", "summary",
        "source_note", "person_refs", "evidence_refs", "trace_refs",
    }
    for line_number, record in enumerate(records, start=1):
        missing = required - set(record)
        if missing:
            failures.append(f"case line {line_number} missing fields: {sorted(missing)}")
            continue
        case_id = record["id"]
        if not re.fullmatch(r"case\.\d{2}", case_id):
            failures.append(f"invalid case id {case_id!r}")
        if case_id in seen:
            failures.append(f"duplicate case id {case_id}")
        seen.add(case_id)
        by_id[case_id] = record
        if record["node_type"] != "case":
            failures.append(f"{case_id} node_type must be case")
        if record["branch"] not in ALLOWED_BRANCH:
            failures.append(f"{case_id} invalid branch {record['branch']!r}")
        if record["status"] not in ALLOWED_STATUS:
            failures.append(f"{case_id} invalid status {record['status']!r}")
        if not record["title"] or not record["summary"]:
            failures.append(f"{case_id} title and summary are required")
        if not record["source_note"]:
            failures.append(f"{case_id} source_note is required")
        _lint_text(case_id, "title", record["title"], failures)
        _lint_text(case_id, "summary", record["summary"], failures)
        _lint_text(case_id, "source_note", record["source_note"], failures, forbid_pipe=True)
        if "display_prose" in record:
            if not record["display_prose"]:
                failures.append(
                    f"{case_id} display_prose must be non-empty when present (omit it to render summary)")
            else:
                _lint_text(case_id, "display_prose", record["display_prose"], failures)
        if not record["person_refs"]:
            failures.append(f"{case_id} person_refs must not be empty")
        for person_id in record["person_refs"]:
            if person_id not in person_ids:
                failures.append(f"{case_id} unresolved person ref {person_id}")
        for evidence_id in record["evidence_refs"]:
            if evidence_id not in evidence_cases:
                failures.append(f"{case_id} unresolved evidence ref {evidence_id}")
            elif case_id not in evidence_cases[evidence_id]:
                failures.append(
                    f"{case_id} evidence ref {evidence_id} does not reciprocally list the case")
        for trace_id in record["trace_refs"]:
            if not isinstance(trace_id, str) or TRACE_ID_RE.fullmatch(trace_id) is None:
                failures.append(
                    f"{case_id} trace ref must be a canonical trace id: {trace_id!r}"
                )
            elif trace_id not in trace_ids:
                failures.append(f"{case_id} missing trace id {trace_id}")

    expected = [f"case.{number:02d}" for number in range(1, len(seen) + 1)]
    actual = [record.get("id") for record in records]
    if actual != expected:
        failures.append(f"case ids must be append-only and sequential: {actual} != {expected}")

    for gap in gaps:
        gap_id = gap.get("id", "<gap without id>")
        case_refs = gap.get("case_refs")
        if not isinstance(case_refs, list):
            failures.append(f"{gap_id} case_refs must be a list")
            continue
        if gap.get("public_anchor") is not None and not case_refs:
            failures.append(f"published gap {gap_id} must cite an open case")
        for case_id in case_refs:
            if case_id not in by_id:
                failures.append(f"{gap_id} points to unknown {case_id}")
            elif (
                gap.get("public_anchor") is not None
                and by_id[case_id]["status"] == "closed"
            ):
                failures.append(f"published gap {gap_id} points to closed {case_id}")
    return failures


def main() -> int:
    records = read_jsonl(CASES)
    traces = canonical_trace_ids()
    failures = core_failures(
        records,
        canonical_gaps(),
        canonical_person_ids(),
        evidence_case_index(),
        traces,
    )
    frames_root = ROOT / "research" / "search-frames"
    uncased = sorted((frames_root / "uncased").glob("*.md"))
    for path in uncased:
        failures.append(f"uncased search frame remains after case cutover: {path.relative_to(ROOT)}")
    case_ids = {record["id"] for record in records}
    for path in sorted(frames_root.glob("case.*")):
        if path.is_dir() and path.name not in case_ids:
            failures.append(f"search-frame directory has no canonical case: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"check_cases: {len(failures)} failure(s)", file=sys.stderr)
        return 1
    print(
        f"check_cases: {len(records)} canonical cases satisfy the store "
        "and published-gap contract (docket bytes: build_docket --check)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
