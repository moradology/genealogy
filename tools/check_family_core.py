#!/usr/bin/env python3
"""Validate the canonical people and family-relationship JSONL stores.

The family core deliberately has one hard-cutover shape.  People are actual
historical individuals.  Unidentified parents, research frontiers, and other
open work belong in explicit gap rows, never in synthetic person rows.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PEOPLE_PATH = Path("research/people/people.jsonl")
RELATIONSHIPS_PATH = Path("research/people/relationships.jsonl")

PERSON_FIELDS = frozenset(
    {
        "id",
        "node_type",
        "display_name",
        "index_names",
        "name_variants",
        "branches",
        "role",
        "confidence",
        "privacy",
        "public_anchor",
    }
)
RELATIONSHIP_FIELDS = frozenset(
    {
        "id",
        "node_type",
        "relationship_type",
        "parent_role",
        "person_a",
        "person_b",
        "status",
        "confidence",
        "branches",
        "evidence_refs",
        "source_refs",
        "case_refs",
        "provenance_note",
    }
)
GAP_FIELDS = frozenset(
    {
        "id",
        "node_type",
        "gap_type",
        "label",
        "subject_persons",
        "candidate_persons",
        "open_roles",
        "branches",
        "case_refs",
        "evidence_refs",
        "source_refs",
        "public_anchor",
        "pedigree",
    }
)

BRANCHES = frozenset({"zimmerman", "mundell", "dible", "connelly"})
ROLES = frozenset({"anchor", "ancestor", "collateral", "candidate"})
CONFIDENCES = frozenset({"documented", "strong", "lead", "open"})
RELATIONSHIP_TYPES = frozenset({"parent_of", "spouse_of"})
RELATIONSHIP_STATUSES = frozenset({"accepted", "hypothesis"})
GAP_TYPES = frozenset(
    {"parentage", "frontier", "candidate_parentage", "research_cluster"}
)
OPEN_ROLES = frozenset(
    {"father", "mother", "parents", "earlier_ancestors", "origin"}
)
PEDIGREE_KEYS = frozenset({"Z", "M", "D", "C"})

PERSON_ID_RE = re.compile(r"person\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
RELATIONSHIP_ID_RE = re.compile(
    r"relationship\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z"
)
GAP_ID_RE = re.compile(r"gap\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
EVIDENCE_ID_RE = re.compile(r"ev\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
SOURCE_ID_RE = re.compile(r"src\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
CASE_ID_RE = re.compile(r"case\.\d{2}\Z")
FAKE_ID_PARTS = frozenset(
    {"parent", "parents", "frontier", "unknown", "group", "cluster", "collaterals"}
)
FAKE_LABEL_RE = re.compile(
    r"\b(?:parents?|unknown|frontier|group|cluster|collaterals)\b",
    re.IGNORECASE,
)
COMBINED_LABEL_RE = re.compile(r"\s(?:\+|&|and)\s", re.IGNORECASE)


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    person_count: int
    relationship_count: int
    gap_count: int

    @property
    def ok(self) -> bool:
        return not self.errors


class _DuplicateKeyError(ValueError):
    pass


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _parse_json(line: str, where: str, errors: list[str]) -> Any | None:
    try:
        return json.loads(line, object_pairs_hook=_object_without_duplicate_keys)
    except json.JSONDecodeError as exc:
        errors.append(f"{where}: invalid JSON: {exc.msg} at column {exc.colno}")
    except _DuplicateKeyError as exc:
        errors.append(f"{where}: invalid JSON: {exc}")
    return None


def _read_jsonl(path: Path, root: Path, errors: list[str]) -> list[tuple[str, Any]]:
    relative = path.relative_to(root) if path.is_relative_to(root) else path
    if not path.is_file():
        errors.append(f"{relative} is missing")
        return []
    rows: list[tuple[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        where = f"{relative}:{line_number}"
        if not line.strip():
            errors.append(f"{where}: blank lines are not allowed in JSONL")
            continue
        value = _parse_json(line, where, errors)
        if value is not None:
            rows.append((where, value))
    return rows


class _ProjectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        anchor = values.get("id")
        if anchor:
            self.ids.add(anchor)


def _projection_ids(root: Path) -> set[str] | None:
    """Return public HTML ids solely to validate canonical link targets."""

    html_path = root / "index.html"
    if not html_path.is_file():
        return None
    parser = _ProjectionParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    return parser.ids


def _exact_fields(
    row: dict[str, Any], expected: frozenset[str], where: str, errors: list[str]
) -> bool:
    actual = set(row)
    if actual == expected:
        return True
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{where}: missing fields: {missing}")
    if unknown:
        errors.append(f"{where}: unknown fields: {unknown}")
    return False


def _nonempty_string(
    row: dict[str, Any], field: str, where: str, errors: list[str]
) -> str | None:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: {field} must be a non-empty string")
        return None
    return value


def _enum(
    row: dict[str, Any],
    field: str,
    allowed: frozenset[str],
    where: str,
    errors: list[str],
) -> str | None:
    value = row.get(field)
    if value not in allowed:
        errors.append(f"{where}: {field} must be one of {sorted(allowed)}")
        return None
    return value


def _sorted_unique_strings(
    row: dict[str, Any],
    field: str,
    where: str,
    errors: list[str],
    *,
    nonempty: bool = False,
) -> list[str]:
    value = row.get(field)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"{where}: {field} must be a list of non-empty strings")
        return []
    if nonempty and not value:
        errors.append(f"{where}: {field} must not be empty")
    if len(value) != len(set(value)):
        errors.append(f"{where}: {field} contains duplicate values")
    if value != sorted(value):
        errors.append(f"{where}: {field} must be sorted")
    return value


def _validate_branches(
    row: dict[str, Any], where: str, errors: list[str]
) -> list[str]:
    branches = _sorted_unique_strings(
        row, "branches", where, errors, nonempty=True
    )
    for branch in branches:
        if branch not in BRANCHES:
            errors.append(f"{where}: branches contains unknown branch {branch!r}")
    return branches


def _validate_ref_list(
    row: dict[str, Any],
    field: str,
    universe: set[str],
    grammar: re.Pattern[str],
    where: str,
    errors: list[str],
    *,
    nonempty: bool = False,
) -> list[str]:
    refs = _sorted_unique_strings(
        row, field, where, errors, nonempty=nonempty
    )
    for ref in refs:
        if not grammar.fullmatch(ref):
            errors.append(f"{where}: {field} contains invalid id {ref!r}")
        elif ref not in universe:
            errors.append(f"{where}: {field} contains unresolved ref {ref!r}")
    return refs


def _validate_public_anchor(
    value: Any,
    grammar: re.Pattern[str],
    html_ids: set[str] | None,
    where: str,
    errors: list[str],
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not grammar.fullmatch(value):
        errors.append(
            f"{where}: public_anchor must be null or an id matching {grammar.pattern!r}"
        )
        return None
    if html_ids is not None and value not in html_ids:
        errors.append(f"{where}: public_anchor {value!r} is absent from index.html")
    return value


def _fake_person_reason(person_id: str, names: Iterable[str]) -> str | None:
    id_parts = set(re.split(r"[._-]", person_id.removeprefix("person.")))
    fake_parts = sorted(id_parts & FAKE_ID_PARTS)
    if fake_parts:
        return f"id uses synthetic label part {fake_parts[0]!r}"
    for name in names:
        if "+" in name or COMBINED_LABEL_RE.search(name):
            return f"name {name!r} describes more than one person"
        if FAKE_LABEL_RE.search(name):
            return f"name {name!r} describes a gap or group"
    return None


def _collect_registry_ids(
    paths: Iterable[Path],
    root: Path,
    label: str,
    errors: list[str],
) -> set[str]:
    ids: set[str] = set()
    seen_at: dict[str, str] = {}
    for path in sorted(paths):
        if not path.is_file():
            continue
        relative = path.relative_to(root) if path.is_relative_to(root) else path
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            where = f"{relative}:{line_number}"
            value = _parse_json(line, where, errors)
            if not isinstance(value, dict):
                errors.append(f"{where}: {label} registry row must be an object")
                continue
            identifier = value.get("id")
            if not isinstance(identifier, str) or not identifier:
                errors.append(f"{where}: {label} registry row has no id")
                continue
            if identifier in seen_at:
                errors.append(
                    f"{where}: duplicate {label} registry id {identifier!r}; "
                    f"first seen at {seen_at[identifier]}"
                )
            else:
                seen_at[identifier] = where
                ids.add(identifier)
    return ids


def _register_global_id(
    identifier: str | None,
    where: str,
    seen_ids: dict[str, str],
    errors: list[str],
) -> None:
    if identifier is None:
        return
    if identifier in seen_ids:
        errors.append(
            f"{where}: duplicate global id {identifier!r}; first seen at {seen_ids[identifier]}"
        )
    else:
        seen_ids[identifier] = where


def _validate_person(
    row: Any,
    where: str,
    html_ids: set[str] | None,
    errors: list[str],
) -> str | None:
    if not isinstance(row, dict):
        errors.append(f"{where}: person row must be an object")
        return None
    _exact_fields(row, PERSON_FIELDS, where, errors)
    person_id = _nonempty_string(row, "id", where, errors)
    if person_id is not None and not PERSON_ID_RE.fullmatch(person_id):
        errors.append(f"{where}: invalid person id {person_id!r}")
    if row.get("node_type") != "person":
        errors.append(f"{where}: node_type must be 'person'")
    display_name = _nonempty_string(row, "display_name", where, errors)
    index_names = _sorted_unique_strings(
        row, "index_names", where, errors, nonempty=True
    )
    variants = _sorted_unique_strings(row, "name_variants", where, errors)
    _validate_branches(row, where, errors)
    _enum(row, "role", ROLES, where, errors)
    _enum(row, "confidence", CONFIDENCES, where, errors)
    if row.get("privacy") != "public_deceased":
        errors.append(f"{where}: privacy must be 'public_deceased'")
    _validate_public_anchor(row.get("public_anchor"), PERSON_ID_RE, html_ids, where, errors)

    if person_id is not None:
        names = [name for name in [display_name, *index_names, *variants] if name]
        reason = _fake_person_reason(person_id, names)
        if reason:
            errors.append(
                f"{where}: person rows must represent one actual individual; {reason}"
            )
    return person_id if person_id and PERSON_ID_RE.fullmatch(person_id) else None


def _validate_relationship(
    row: dict[str, Any],
    where: str,
    person_ids: set[str],
    evidence_ids: set[str],
    source_ids: set[str],
    case_ids: set[str],
    errors: list[str],
) -> tuple[
    str | None,
    tuple[str, str, str] | None,
    tuple[str, str] | None,
    tuple[str, str] | None,
]:
    _exact_fields(row, RELATIONSHIP_FIELDS, where, errors)
    relationship_id = _nonempty_string(row, "id", where, errors)
    if relationship_id is not None and not RELATIONSHIP_ID_RE.fullmatch(relationship_id):
        errors.append(f"{where}: invalid relationship id {relationship_id!r}")
    if row.get("node_type") != "relationship":
        errors.append(f"{where}: node_type must be 'relationship'")
    relationship_type = _enum(
        row, "relationship_type", RELATIONSHIP_TYPES, where, errors
    )
    parent_role = row.get("parent_role")
    if relationship_type == "parent_of":
        if parent_role not in {"father", "mother"}:
            errors.append(
                f"{where}: parent_role must be 'father' or 'mother' for parent_of"
            )
    elif relationship_type == "spouse_of" and parent_role is not None:
        errors.append(f"{where}: parent_role must be null for spouse_of")
    person_a = _nonempty_string(row, "person_a", where, errors)
    person_b = _nonempty_string(row, "person_b", where, errors)
    for field, endpoint in (("person_a", person_a), ("person_b", person_b)):
        if endpoint is not None and endpoint not in person_ids:
            errors.append(f"{where}: {field} has unresolved person endpoint {endpoint!r}")
    if person_a is not None and person_a == person_b:
        errors.append(f"{where}: relationship endpoints must be distinct")
    status = _enum(row, "status", RELATIONSHIP_STATUSES, where, errors)
    confidence = _enum(row, "confidence", CONFIDENCES, where, errors)
    _validate_branches(row, where, errors)
    evidence_refs = _validate_ref_list(
        row, "evidence_refs", evidence_ids, EVIDENCE_ID_RE, where, errors
    )
    source_refs = _validate_ref_list(
        row, "source_refs", source_ids, SOURCE_ID_RE, where, errors
    )
    case_refs = _validate_ref_list(
        row, "case_refs", case_ids, CASE_ID_RE, where, errors
    )
    _nonempty_string(row, "provenance_note", where, errors)
    if not (evidence_refs or source_refs or case_refs):
        errors.append(
            f"{where}: every relationship must cite evidence, source, or case refs"
        )

    pair_key: tuple[str, str, str] | None = None
    parent_edge: tuple[str, str] | None = None
    accepted_parent_role: tuple[str, str] | None = None
    if relationship_type and person_a and person_b and person_a != person_b:
        if relationship_type == "spouse_of":
            first, second = sorted((person_a, person_b))
            pair_key = (relationship_type, first, second)
        else:
            pair_key = (relationship_type, person_a, person_b)
            if person_a in person_ids and person_b in person_ids:
                parent_edge = (person_a, person_b)
                if status == "accepted" and parent_role in {"father", "mother"}:
                    accepted_parent_role = (person_b, parent_role)
    valid_id = (
        relationship_id
        if relationship_id and RELATIONSHIP_ID_RE.fullmatch(relationship_id)
        else None
    )
    return valid_id, pair_key, parent_edge, accepted_parent_role


def _validate_gap(
    row: dict[str, Any],
    where: str,
    person_ids: set[str],
    evidence_ids: set[str],
    source_ids: set[str],
    case_ids: set[str],
    html_ids: set[str] | None,
    occupied_slots: dict[tuple[str, int], str],
    errors: list[str],
) -> str | None:
    _exact_fields(row, GAP_FIELDS, where, errors)
    gap_id = _nonempty_string(row, "id", where, errors)
    if gap_id is not None and not GAP_ID_RE.fullmatch(gap_id):
        errors.append(f"{where}: invalid gap id {gap_id!r}")
    if row.get("node_type") != "gap":
        errors.append(f"{where}: node_type must be 'gap'")
    _enum(row, "gap_type", GAP_TYPES, where, errors)
    _nonempty_string(row, "label", where, errors)
    subjects = _validate_ref_list(
        row,
        "subject_persons",
        person_ids,
        PERSON_ID_RE,
        where,
        errors,
        nonempty=True,
    )
    candidates = _validate_ref_list(
        row, "candidate_persons", person_ids, PERSON_ID_RE, where, errors
    )
    overlap = sorted(set(subjects) & set(candidates))
    if overlap:
        errors.append(
            f"{where}: subject_persons and candidate_persons must be disjoint: {overlap}"
        )
    roles = _sorted_unique_strings(row, "open_roles", where, errors)
    for role in roles:
        if role not in OPEN_ROLES:
            errors.append(f"{where}: open_roles contains unknown role {role!r}")
    _validate_branches(row, where, errors)
    _validate_ref_list(
        row,
        "case_refs",
        case_ids,
        CASE_ID_RE,
        where,
        errors,
        nonempty=True,
    )
    _validate_ref_list(
        row, "evidence_refs", evidence_ids, EVIDENCE_ID_RE, where, errors
    )
    _validate_ref_list(
        row, "source_refs", source_ids, SOURCE_ID_RE, where, errors
    )
    _validate_public_anchor(
        row.get("public_anchor"), GAP_ID_RE, html_ids, where, errors
    )

    pedigree = row.get("pedigree")
    if not isinstance(pedigree, dict):
        errors.append(f"{where}: pedigree must be an object")
    elif set(pedigree) != PEDIGREE_KEYS:
        errors.append(
            f"{where}: pedigree fields must be exactly {sorted(PEDIGREE_KEYS)}"
        )
    else:
        for branch_code in sorted(PEDIGREE_KEYS):
            slots = pedigree[branch_code]
            if not isinstance(slots, list) or any(type(slot) is not int for slot in slots):
                errors.append(
                    f"{where}: pedigree.{branch_code} must be a list of integers"
                )
                continue
            if len(slots) != len(set(slots)):
                errors.append(
                    f"{where}: pedigree.{branch_code} contains duplicate values"
                )
            if slots != sorted(slots):
                errors.append(f"{where}: pedigree.{branch_code} must be sorted")
            for slot in slots:
                if not 1 <= slot <= 63:
                    errors.append(
                        f"{where}: pedigree.{branch_code} slot {slot!r} must be 1..63"
                    )
                    continue
                key = (branch_code, slot)
                if key in occupied_slots:
                    errors.append(
                        f"{where}: pedigree slot {branch_code}-{slot} is also claimed by "
                        f"{occupied_slots[key]}"
                    )
                else:
                    occupied_slots[key] = gap_id or where
    return gap_id if gap_id and GAP_ID_RE.fullmatch(gap_id) else None


def _validate_parent_acyclic(
    person_ids: set[str], edges: list[tuple[str, str]], errors: list[str]
) -> None:
    children: dict[str, list[str]] = {person_id: [] for person_id in person_ids}
    for parent, child in edges:
        children[parent].append(child)
    state: dict[str, int] = {}
    stack: list[str] = []
    reported: set[frozenset[str]] = set()

    def visit(person_id: str) -> None:
        state[person_id] = 1
        stack.append(person_id)
        for child in children[person_id]:
            if state.get(child, 0) == 0:
                visit(child)
            elif state.get(child) == 1:
                start = stack.index(child)
                cycle = stack[start:] + [child]
                key = frozenset(cycle)
                if key not in reported:
                    reported.add(key)
                    errors.append(
                        "parent_of graph contains a cycle: "
                        + " -> ".join(cycle)
                    )
        stack.pop()
        state[person_id] = 2

    for person_id in sorted(person_ids):
        if state.get(person_id, 0) == 0:
            visit(person_id)


def validate_repository(
    root: Path = ROOT,
    people_path: Path = PEOPLE_PATH,
    relationships_path: Path = RELATIONSHIPS_PATH,
) -> ValidationResult:
    root = Path(root)
    people_file = people_path if people_path.is_absolute() else root / people_path
    relationships_file = (
        relationships_path
        if relationships_path.is_absolute()
        else root / relationships_path
    )
    errors: list[str] = []
    html_ids = _projection_ids(root)

    evidence_dir = root / "research/evidence"
    evidence_ids = _collect_registry_ids(
        evidence_dir.glob("*.jsonl") if evidence_dir.is_dir() else [],
        root,
        "evidence",
        errors,
    )
    source_path = root / "research/sources/sources.jsonl"
    source_ids = _collect_registry_ids(
        [source_path] if source_path.is_file() else [], root, "source", errors
    )
    case_path = root / "research/cases/cases.jsonl"
    case_ids = _collect_registry_ids(
        [case_path] if case_path.is_file() else [], root, "case", errors
    )

    seen_ids: dict[str, str] = {}
    person_ids: set[str] = set()
    branch_anchors: dict[str, list[str]] = {branch: [] for branch in BRANCHES}
    person_count = 0
    for where, row in _read_jsonl(people_file, root, errors):
        person_count += 1
        person_id = _validate_person(row, where, html_ids, errors)
        _register_global_id(person_id, where, seen_ids, errors)
        if person_id is not None:
            person_ids.add(person_id)
            if isinstance(row, dict) and row.get("role") == "anchor":
                branches = row.get("branches")
                if isinstance(branches, list):
                    for branch in branches:
                        if branch in branch_anchors:
                            branch_anchors[branch].append(person_id)

    anchors = {person_id for values in branch_anchors.values() for person_id in values}
    if len(anchors) != 4:
        errors.append(f"family core must have exactly four anchor people; found {len(anchors)}")
    for branch in sorted(BRANCHES):
        if len(branch_anchors[branch]) != 1:
            errors.append(
                f"branch {branch!r} must have exactly one anchor; "
                f"found {branch_anchors[branch]}"
            )

    relationship_count = 0
    gap_count = 0
    seen_pairs: dict[tuple[str, str, str], str] = {}
    parent_edges: list[tuple[str, str]] = []
    accepted_parent_roles: dict[tuple[str, str], str] = {}
    occupied_slots: dict[tuple[str, int], str] = {}
    for where, row in _read_jsonl(relationships_file, root, errors):
        if not isinstance(row, dict):
            errors.append(f"{where}: relationship/gap row must be an object")
            continue
        node_type = row.get("node_type")
        if node_type == "relationship":
            relationship_count += 1
            identifier, pair_key, parent_edge, accepted_parent_role = _validate_relationship(
                row,
                where,
                person_ids,
                evidence_ids,
                source_ids,
                case_ids,
                errors,
            )
            _register_global_id(identifier, where, seen_ids, errors)
            if pair_key is not None:
                if pair_key in seen_pairs:
                    errors.append(
                        f"{where}: duplicate {pair_key[0]} pair; first seen at "
                        f"{seen_pairs[pair_key]}"
                    )
                else:
                    seen_pairs[pair_key] = where
            if parent_edge is not None:
                parent_edges.append(parent_edge)
            if accepted_parent_role is not None:
                if accepted_parent_role in accepted_parent_roles:
                    child, role = accepted_parent_role
                    errors.append(
                        f"{where}: child {child!r} has more than one accepted {role}; "
                        f"first seen at {accepted_parent_roles[accepted_parent_role]}"
                    )
                else:
                    accepted_parent_roles[accepted_parent_role] = where
        elif node_type == "gap":
            gap_count += 1
            identifier = _validate_gap(
                row,
                where,
                person_ids,
                evidence_ids,
                source_ids,
                case_ids,
                html_ids,
                occupied_slots,
                errors,
            )
            _register_global_id(identifier, where, seen_ids, errors)
        else:
            errors.append(
                f"{where}: node_type must discriminate 'relationship' or 'gap'"
            )

    _validate_parent_acyclic(person_ids, parent_edges, errors)
    return ValidationResult(
        tuple(errors), person_count, relationship_count, gap_count
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = validate_repository(root=args.root)
    if not result.ok:
        print("family-core validation failed:", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        "family core ok: "
        f"{result.person_count} people, "
        f"{result.relationship_count} relationships, "
        f"{result.gap_count} gaps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
