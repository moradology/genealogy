#!/usr/bin/env python3
"""Project canonical research cases into the public docket section."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = Path("index.html")
CASES_PATH = Path("research/cases/cases.jsonl")

STATUS_LABELS = {
    "open": "OPEN",
    "in_conflict": "IN CONFLICT",
    "needs_pull": "NEEDS PULL",
    "closed": "CLOSED",
}

SCRIPT_RE = re.compile(r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.I | re.S)
ATTR_RE = re.compile(
    r"(?P<name>[A-Za-z_:][\w:.-]*)"
    r"(?:\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\s>]+)))?"
)
MARKER_RE = re.compile(
    r"(<!-- BEGIN docket-cases -->\n).*?(\n<!-- END -->)",
    re.S,
)
CASE_RE = re.compile(
    r'<div id="(case\.\d+)"><div>.*?</div><p>.*?</p><div>(.*?)</div></div>',
    re.S,
)
LEADING_LINKS_RE = re.compile(r"\A(?:\s*<a\b[^>]*>.*?</a>\s*(?:,\s*)?)+", re.I | re.S)
TRACE_TOKEN_RE = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md")


def fail(message: str) -> NoReturn:
    print(f"build_docket: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        fail(f"missing canonical store: {path}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            fail(f"{path}:{line_number}: blank JSONL lines are not allowed")
        record = json.loads(line)
        if not isinstance(record, dict):
            fail(f"{path}:{line_number}: row must be a JSON object")
        records.append(record)
    return records


def attrs(raw: str) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for match in ATTR_RE.finditer(raw):
        value = match.group("double")
        if value is None:
            value = match.group("single")
        if value is None:
            value = match.group("bare")
        values[match.group("name").lower()] = value
    return values


def people_index(source: str) -> dict[str, dict[str, Any]]:
    matches = []
    for match in SCRIPT_RE.finditer(source):
        if attrs(match.group("attrs")).get("id") == "people-index":
            matches.append(match)
    if len(matches) != 1:
        fail(f"expected exactly one #people-index script; found {len(matches)}")
    payload = json.loads(matches[0].group("body"))
    if not isinstance(payload, dict) or not isinstance(payload.get("people"), list):
        fail("#people-index JSON must contain a people list")
    by_id: dict[str, dict[str, Any]] = {}
    for entry in payload["people"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("i"), str):
            fail("#people-index contains an entry without string i")
        entry_id = entry["i"]
        if entry_id in by_id:
            fail(f"#people-index has duplicate entry {entry_id}")
        by_id[entry_id] = entry
    return by_id


def text(value: Any) -> str:
    if not isinstance(value, str):
        fail(f"expected string value, found {value!r}")
    return html.escape(value, quote=False)


def string_list(value: Any, where: str) -> list[str]:
    if not isinstance(value, list):
        fail(f"{where} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            fail(f"{where} must contain only strings")
        result.append(item)
    return result


def case_links(person_refs: list[str], people: dict[str, dict[str, Any]]) -> str:
    """One link per TARGET CARD: person_refs sharing an anchor (a couple on one
    card, e.g. Z-8 + Z-9) merge into a single couple-style link (Z-8/9), in
    first-appearance order. Refs without ahnentafel numbers fall back to the
    entry's display name and never merge numbers."""
    groups: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for ref in person_refs:
        entry = people.get(ref)
        if entry is None:
            fail(f"unknown person_ref {ref}")
        anchor = entry.get("h")
        if not isinstance(anchor, str):
            fail(f"#people-index entry {ref} has no string h")
        if anchor not in groups:
            groups[anchor] = {"branch": entry.get("a"), "numbers": [], "fallback": entry.get("n")}
            order.append(anchor)
        slots = entry.get("ah")
        if isinstance(slots, list):
            for slot in slots:
                if slot not in groups[anchor]["numbers"]:
                    groups[anchor]["numbers"].append(slot)
    links = []
    for anchor in order:
        group = groups[anchor]
        if group["numbers"]:
            label = f"{group['branch']}-" + "/".join(str(n) for n in sorted(group["numbers"]))
        else:
            label = str(group["fallback"])
        links.append(f'<a href="#{anchor}">{label}</a>')
    return ", ".join(links)


def render_case(record: dict[str, Any], people: dict[str, dict[str, Any]]) -> str:
    case_id = text(record.get("id"))
    title = text(record.get("title"))
    status = record.get("status")
    if status not in STATUS_LABELS:
        fail(f"{record.get('id')}: unknown status {status!r}")
    prose = record.get("display_prose") or record.get("summary")
    body = text(prose)
    person_refs = string_list(record.get("person_refs"), f"{record.get('id')}.person_refs")
    links = case_links(person_refs, people)
    source_note = text(record.get("source_note", ""))
    trace_refs = string_list(record.get("trace_refs", []), f"{record.get('id')}.trace_refs")
    traces = "" if not trace_refs else "|" + " ".join(trace_refs)
    return (
        f'<div id="{case_id}"><div><b>{case_id}</b><h3>{title}</h3>'
        f"<b>{STATUS_LABELS[status]}</b></div><p>{body}</p>"
        f"<div>{links}|{source_note}{traces}</div></div>"
    )


def render_cases(records: list[dict[str, Any]], people: dict[str, dict[str, Any]]) -> str:
    lines = [render_case(record, people) for record in sorted(records, key=lambda row: str(row.get("id")))]
    return "\n".join(lines)


def section_bounds(source: str) -> tuple[int, int]:
    start = source.find('<section class="sheet" id="docket">')
    if start == -1:
        fail("docket section not found")
    end = source.find('<section class="sheet" id="wanted"', start)
    if end == -1:
        fail("wanted section after docket not found")
    return start, end


def splice_cases(source: str, cases_markup: str) -> str:
    docket_start, docket_end = section_bounds(source)
    corr_i = source.find("\n<h3>Corrigenda", docket_start, docket_end)
    if corr_i == -1:
        fail("docket Corrigenda anchor not found")

    marker_matches = list(MARKER_RE.finditer(source))
    if marker_matches:
        if len(marker_matches) != 1:
            fail(f"expected one docket marker block; found {len(marker_matches)}")
        match = marker_matches[0]
        if not (docket_start < match.start() and match.end() <= corr_i):
            fail("docket marker block is not inside the docket cases region")
        return source[: match.end(1)] + cases_markup + source[match.start(2) :]

    case_i = source.find('<div id="case.01">', docket_start, corr_i)
    if case_i == -1:
        fail("docket case.01 start not found")
    block = f"<!-- BEGIN docket-cases -->\n{cases_markup}\n<!-- END -->"
    return source[:case_i] + block + source[corr_i:]


def build(root: Path) -> tuple[str, str, int]:
    html_path = root / HTML_PATH
    if not html_path.is_file():
        fail(f"missing presentation file: {html_path}")
    source = html_path.read_text(encoding="utf-8")
    cases = read_jsonl(root / CASES_PATH)
    rendered_cases = render_cases(cases, people_index(source))
    return source, splice_cases(source, rendered_cases), len(cases)


def docket_section(source: str) -> str:
    start, end = section_bounds(source)
    return source[start:end]


def note_from_refs(raw_refs: str) -> str:
    tail = LEADING_LINKS_RE.sub("", raw_refs.strip(), count=1)
    for segment in tail.split("|"):
        note = html.unescape(segment).strip()
        if note:
            return note
    return ""


def strip_trace_tokens(note: str) -> tuple[str, list[str]]:
    tokens = TRACE_TOKEN_RE.findall(note)
    cleaned_segments: list[str] = []
    for segment in note.split(";"):
        cleaned = TRACE_TOKEN_RE.sub("", segment)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ;")
        if cleaned:
            cleaned_segments.append(cleaned)
    return "; ".join(cleaned_segments), tokens


def ordered_case(record: dict[str, Any], source_note: str) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in ("id", "node_type", "branch", "title", "status", "summary"):
        if key in record:
            ordered[key] = record[key]
    ordered["source_note"] = source_note
    for key, value in record.items():
        if key not in ordered and key != "source_note":
            ordered[key] = value
    return ordered


def write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    payload = "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    )
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, path)


def migrate(root: Path) -> int:
    html_path = root / HTML_PATH
    if not html_path.is_file():
        fail(f"missing presentation file: {html_path}")
    source = html_path.read_text(encoding="utf-8")
    notes: dict[str, str] = {}
    token_updates: dict[str, list[str]] = {}
    for match in CASE_RE.finditer(docket_section(source)):
        case_id = match.group(1)
        raw_note = note_from_refs(match.group(2))
        cleaned_note, tokens = strip_trace_tokens(raw_note)
        notes[case_id] = cleaned_note
        token_updates[case_id] = tokens

    records = read_jsonl(root / CASES_PATH)
    migrated: list[dict[str, Any]] = []
    reports: list[str] = []
    for record in records:
        case_id = record.get("id")
        if not isinstance(case_id, str):
            fail("case record without string id")
        source_note = notes.get(case_id, "")
        trace_refs = string_list(record.get("trace_refs", []), f"{case_id}.trace_refs")
        for token in token_updates.get(case_id, []):
            if token not in trace_refs:
                trace_refs.append(token)
                reports.append(f"build_docket: {case_id} merged trace_ref {token}")
            reports.append(f"build_docket: {case_id} stripped trace token {token}")
        updated = dict(record)
        updated["trace_refs"] = trace_refs
        migrated.append(ordered_case(updated, source_note))
        if source_note:
            reports.append(f"build_docket: {case_id} source_note extracted: {source_note}")

    write_jsonl_atomic(root / CASES_PATH, migrated)
    for report in reports:
        print(report)
    print(f"updated {root / CASES_PATH}: {len(migrated)} cases migrated")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="fail if docket projection has drifted")
    parser.add_argument("--migrate", action="store_true", help="extract source_note values from the current hand docket")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.migrate:
        return migrate(root)

    original, rendered, count = build(root)
    html_path = root / HTML_PATH
    if args.check:
        if original != rendered:
            print(
                f"{html_path} docket projection is out of date; run ./gen build docket",
                file=sys.stderr,
            )
            return 1
        print(f"docket projection current: {count} cases")
        return 0

    if original != rendered:
        html_path.write_text(rendered, encoding="utf-8")
    print(f"updated {html_path}: {count} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
