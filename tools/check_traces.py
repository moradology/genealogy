#!/usr/bin/env python3
"""Validate strict reasoning-trace frontmatter and canonical references."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = Path("research/reasoning-traces")
SKIPPED_NAMES = frozenset({"README.md", "template.md"})

FIELD_ORDER = (
    "id",
    "title",
    "date",
    "status",
    "confidence",
    "case_refs",
    "person_refs",
    "evidence_refs",
    "source_refs",
    "geo_refs",
    "outcome",
    "next_action",
)
LIST_FIELDS = frozenset(
    {"case_refs", "person_refs", "evidence_refs", "source_refs", "geo_refs"}
)
QUOTED_FIELDS = frozenset({"title", "outcome", "next_action"})
STATUSES = frozenset({"active", "parked", "rejected", "resolved"})
CONFIDENCES = frozenset({"documented", "strong", "lead", "working", "possible", "open"})

TRACE_FILE_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md\Z"
)
TRACE_ID_RE = re.compile(r"trace\.\d{4}-\d{2}-\d{2}\.[a-z0-9]+(?:-[a-z0-9]+)*\Z")
CASE_ID_RE = re.compile(r"case\.\d{2}\Z")
PERSON_ID_RE = re.compile(r"person\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\Z")
EVIDENCE_ID_RE = re.compile(r"ev\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
SOURCE_ID_RE = re.compile(r"src\.[a-z0-9][A-Za-z0-9_.-]*\Z")

BODY_CASE_RE = re.compile(r"\bcase\.\d{2}\b")
BODY_PERSON_RE = re.compile(r"\bperson\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\b")
BODY_EVIDENCE_RE = re.compile(r"\bev\.[a-z0-9]+(?:[._-][a-z0-9]+)*\b")
BODY_SOURCE_RE = re.compile(r"\bsrc\.[a-z0-9][A-Za-z0-9_.-]*[A-Za-z0-9]\b")


@dataclass(frozen=True)
class Universes:
    cases: frozenset[str]
    people: frozenset[str]
    evidence: frozenset[str]
    sources: frozenset[str]
    geo: frozenset[str]


@dataclass(frozen=True)
class ParsedTrace:
    fields: dict[str, Any]
    body: str


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    trace_count: int

    @property
    def ok(self) -> bool:
        return not self.errors


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings(nested)


def _read_jsonl_ids(path: Path, label: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    if not path.is_file():
        errors.append(f"missing canonical {label} store: {path}")
        return ids
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid {label} JSON: {exc}")
            continue
        value = record.get("id") if isinstance(record, dict) else None
        if not isinstance(value, str):
            errors.append(f"{path}:{line_number}: canonical {label} record has no string id")
        elif value in ids:
            errors.append(f"{path}:{line_number}: duplicate canonical {label} id {value}")
        else:
            ids.add(value)
    return ids


def load_universes(root: Path = ROOT) -> tuple[Universes, list[str]]:
    root = root.resolve()
    errors: list[str] = []
    cases = _read_jsonl_ids(root / "research/cases/cases.jsonl", "case", errors)
    sources = _read_jsonl_ids(root / "research/sources/sources.jsonl", "source", errors)
    evidence: set[str] = set()
    evidence_paths = sorted((root / "research/evidence").glob("*.jsonl"))
    if not evidence_paths:
        errors.append("no canonical evidence shards found under research/evidence")
    for path in evidence_paths:
        for evidence_id in _read_jsonl_ids(path, "evidence", errors):
            if evidence_id in evidence:
                errors.append(f"duplicate canonical evidence id across shards: {evidence_id}")
            evidence.add(evidence_id)

    people: set[str] = set()
    html_path = root / "index.html"
    if not html_path.is_file():
        errors.append("missing index.html; cannot resolve trace person refs")
    else:
        people.update(
            re.findall(
                r"\bid\s*=\s*['\"](person\.[A-Za-z0-9_.-]+)['\"]",
                html_path.read_text(encoding="utf-8"),
            )
        )

    geo: set[str] = set()
    geo_path = root / "ancestry_geospatial.geojson"
    if not geo_path.is_file():
        errors.append("missing ancestry_geospatial.geojson; cannot resolve trace refs")
    else:
        try:
            geojson = json.loads(geo_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid ancestry_geospatial.geojson: {exc}")
        else:
            for feature in geojson.get("features", []):
                feature_id = feature.get("id") if isinstance(feature, dict) else None
                if isinstance(feature_id, str):
                    if feature_id in geo:
                        errors.append(f"duplicate GeoJSON feature id {feature_id}")
                    geo.add(feature_id)
            registry = geojson.get("place_registry") or {}
            if isinstance(registry, dict):
                geo.update(key for key in registry if isinstance(key, str))
            for value in _strings(geojson):
                if PERSON_ID_RE.fullmatch(value):
                    people.add(value)

    return (
        Universes(
            cases=frozenset(cases),
            people=frozenset(people),
            evidence=frozenset(evidence),
            sources=frozenset(sources),
            geo=frozenset(geo),
        ),
        errors,
    )


def parse_trace(text: str, name: str, errors: list[str]) -> ParsedTrace | None:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{name}: missing strict frontmatter opening delimiter")
        return None
    try:
        closing = lines.index("---", 1)
    except ValueError:
        errors.append(f"{name}: missing strict frontmatter closing delimiter")
        return None
    raw_fields = lines[1:closing]
    if len(raw_fields) != len(FIELD_ORDER):
        errors.append(
            f"{name}: frontmatter must contain exactly {len(FIELD_ORDER)} fields; "
            f"found {len(raw_fields)}"
        )
        return None

    fields: dict[str, Any] = {}
    for position, (line, expected) in enumerate(zip(raw_fields, FIELD_ORDER), 1):
        if ": " not in line:
            errors.append(f"{name}: frontmatter field {position} must use 'key: value'")
            continue
        key, raw = line.split(": ", 1)
        if key != expected:
            errors.append(
                f"{name}: frontmatter field {position} must be {expected!r}, found {key!r}"
            )
            continue
        if expected in LIST_FIELDS:
            if not raw.startswith("["):
                errors.append(f"{name}: {expected} must be a one-line JSON array")
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{name}: {expected} is not valid JSON: {exc.msg}")
                continue
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                errors.append(f"{name}: {expected} must be a JSON array of strings")
                continue
            if len(value) != len(set(value)):
                errors.append(f"{name}: {expected} contains duplicate refs")
            if value != sorted(value):
                errors.append(f"{name}: {expected} must be sorted")
            fields[expected] = value
        elif expected in QUOTED_FIELDS:
            if not raw.startswith('"'):
                errors.append(f"{name}: {expected} must be a JSON-quoted string")
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{name}: {expected} is not a valid JSON string: {exc.msg}")
                continue
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name}: {expected} must be a non-empty string")
                continue
            fields[expected] = value
        else:
            if not raw or raw != raw.strip() or any(char.isspace() for char in raw):
                errors.append(f"{name}: {expected} must be one unquoted token")
                continue
            fields[expected] = raw

    body_lines = lines[closing + 1 :]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    body = "\n".join(body_lines)
    if not body.startswith("# "):
        errors.append(f"{name}: trace body must begin with an H1 heading")
    if len(fields) != len(FIELD_ORDER):
        return None
    return ParsedTrace(fields=fields, body=body)


def _check_declared_body_refs(
    parsed: ParsedTrace, name: str, universes: Universes, errors: list[str]
) -> None:
    patterns = {
        "case_refs": BODY_CASE_RE,
        "person_refs": BODY_PERSON_RE,
        "evidence_refs": BODY_EVIDENCE_RE,
        "source_refs": BODY_SOURCE_RE,
    }
    for field, pattern in patterns.items():
        declared = set(parsed.fields[field])
        for ref in sorted(set(pattern.findall(parsed.body))):
            if ref not in declared:
                errors.append(f"{name}: body ref {ref} is missing from {field}")
    declared_geo = set(parsed.fields["geo_refs"])
    for ref in sorted(universes.geo):
        if re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(ref)}(?![A-Za-z0-9_.-])", parsed.body):
            if ref not in declared_geo:
                errors.append(f"{name}: body ref {ref} is missing from geo_refs")


def validate_documents(
    documents: dict[str, str], universes: Universes
) -> list[str]:
    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    ref_specs = {
        "case_refs": (CASE_ID_RE, universes.cases, "case"),
        "person_refs": (PERSON_ID_RE, universes.people, "person"),
        "evidence_refs": (EVIDENCE_ID_RE, universes.evidence, "evidence"),
        "source_refs": (SOURCE_ID_RE, universes.sources, "source"),
    }

    for name in sorted(documents):
        match = TRACE_FILE_RE.fullmatch(name)
        if match is None:
            errors.append(f"{name}: trace filename must be YYYY-MM-DD-lowercase-slug.md")
            continue
        parsed = parse_trace(documents[name], name, errors)
        if parsed is None:
            continue
        fields = parsed.fields
        expected_id = f"trace.{match.group('date')}.{match.group('slug')}"
        trace_id = fields["id"]
        if not TRACE_ID_RE.fullmatch(trace_id):
            errors.append(f"{name}: invalid trace id {trace_id!r}")
        if trace_id != expected_id:
            errors.append(f"{name}: trace id must be {expected_id!r}, found {trace_id!r}")
        if trace_id in seen_ids:
            errors.append(f"{name}: duplicate trace id {trace_id}; first seen in {seen_ids[trace_id]}")
        else:
            seen_ids[trace_id] = name
        try:
            dt.date.fromisoformat(fields["date"])
        except ValueError:
            errors.append(f"{name}: date must be a real ISO date")
        if fields["date"] != match.group("date"):
            errors.append(f"{name}: date must match the filename date")
        if fields["status"] not in STATUSES:
            errors.append(f"{name}: status must be one of {sorted(STATUSES)}")
        if fields["confidence"] not in CONFIDENCES:
            errors.append(f"{name}: confidence must be one of {sorted(CONFIDENCES)}")

        for field, (grammar, universe, label) in ref_specs.items():
            for ref in fields[field]:
                if not grammar.fullmatch(ref):
                    errors.append(f"{name}: invalid {label} ref {ref!r} in {field}")
                elif ref not in universe:
                    errors.append(f"{name}: unresolved {label} ref {ref!r}")
        for ref in fields["geo_refs"]:
            if ref not in universes.geo:
                errors.append(f"{name}: unresolved geo ref {ref!r}")
        _check_declared_body_refs(parsed, name, universes, errors)
    return errors


def validate_repository(
    root: Path = ROOT, trace_dir: Path = TRACE_DIR
) -> ValidationResult:
    root = root.resolve()
    directory = trace_dir if trace_dir.is_absolute() else root / trace_dir
    universes, errors = load_universes(root)
    if not directory.is_dir():
        errors.append(f"missing reasoning-traces directory: {directory}")
        return ValidationResult(tuple(errors), 0)
    documents = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(directory.glob("*.md"))
        if path.name not in SKIPPED_NAMES
    }
    errors.extend(validate_documents(documents, universes))
    return ValidationResult(tuple(errors), len(documents))


def main() -> int:
    result = validate_repository()
    if not result.ok:
        print("trace validation failed:", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"traces ok: {result.trace_count} strict frontmatter records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
