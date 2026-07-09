#!/usr/bin/env python3
"""Validate canonical case JSONL and its presentation/search projections."""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "research" / "cases" / "cases.jsonl"
ALLOWED_STATUS = frozenset({"open", "in_conflict", "needs_pull", "closed"})
ALLOWED_BRANCH = frozenset({"zimmerman", "mundell", "dible", "connelly"})
CASE_RE = re.compile(
    r'<div id="(?P<id>case\.\d{2})"><div><b>[^<]+</b><h3>(?P<title>.*?)</h3>'
    r'<b>(?P<status>.*?)</b></div><p>(?P<summary>.*?)</p><div>.*?</div></div>',
    re.S,
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def plain(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html_lib.unescape(value)).strip()


def docket_records(html: str) -> dict[str, dict[str, str]]:
    start = html.index('<section class="sheet" id="docket">')
    end = html.index('<section class="sheet" id="wanted">')
    records = {}
    for match in CASE_RE.finditer(html[start:end]):
        records[match.group("id")] = {
            "title": plain(match.group("title")),
            "status": match.group("status").lower().replace(" ", "_"),
            "summary": plain(match.group("summary")),
        }
    return records


def people_index(html: str) -> list[dict]:
    match = re.search(
        r'<script[^>]*type="application/json"[^>]*id="people-index"[^>]*>(.*?)</script>',
        html,
        re.S | re.I,
    )
    assert match is not None
    return json.loads(match.group(1))["people"]


def evidence_case_index(root: Path = ROOT) -> dict[str, set[str]]:
    index = {}
    for path in sorted((root / "research" / "evidence").glob("*.jsonl")):
        for record in read_jsonl(path):
            index[record["id"]] = set(record.get("case_refs", []))
    return index


def core_failures(
    records: list[dict],
    docket: dict[str, dict[str, str]],
    people: list[dict],
    person_ids: set[str],
    evidence_cases: dict[str, set[str]],
    trace_names: set[str],
) -> list[str]:
    failures = []
    seen = set()
    by_id = {}
    required = {
        "id", "node_type", "branch", "title", "status", "summary",
        "person_refs", "evidence_refs", "trace_refs",
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
        for person_id in record["person_refs"]:
            if person_id not in person_ids:
                failures.append(f"{case_id} unresolved person ref {person_id}")
        for evidence_id in record["evidence_refs"]:
            if evidence_id not in evidence_cases:
                failures.append(f"{case_id} unresolved evidence ref {evidence_id}")
            elif case_id not in evidence_cases[evidence_id]:
                failures.append(
                    f"{case_id} evidence ref {evidence_id} does not reciprocally list the case")
        for trace_name in record["trace_refs"]:
            if trace_name not in trace_names:
                failures.append(f"{case_id} missing trace {trace_name}")

    expected = [f"case.{number:02d}" for number in range(1, len(seen) + 1)]
    actual = [record.get("id") for record in records]
    if actual != expected:
        failures.append(f"case ids must be append-only and sequential: {actual} != {expected}")
    if set(docket) != seen:
        failures.append(
            f"Docket ids differ from canonical cases: missing={sorted(seen - set(docket))} "
            f"extra={sorted(set(docket) - seen)}")
    for case_id in sorted(seen & set(docket)):
        canonical = by_id[case_id]
        projected = docket[case_id]
        for field in ("title", "status", "summary"):
            if canonical[field] != projected[field]:
                failures.append(
                    f"{case_id} Docket {field} drift: {projected[field]!r} != {canonical[field]!r}")

    for person in people:
        case_id = person.get("c")
        if not case_id:
            continue
        if case_id not in by_id:
            failures.append(f"{person.get('i')} points to unknown {case_id}")
        elif person.get("t") == "open" and by_id[case_id]["status"] == "closed":
            failures.append(f"open slot {person.get('i')} points to closed {case_id}")
    return failures


def main() -> int:
    html = (ROOT / "index.html").read_text()
    records = read_jsonl(CASES)
    person_ids = set(re.findall(r'id="(person\.[A-Za-z0-9_.-]+)"', html))
    trace_dir = ROOT / "research" / "reasoning-traces"
    traces = {path.name for path in trace_dir.glob("20*.md")}
    failures = core_failures(
        records,
        docket_records(html),
        people_index(html),
        person_ids,
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
    print(f"check_cases: {len(records)} canonical cases match the Docket and open-slot contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
