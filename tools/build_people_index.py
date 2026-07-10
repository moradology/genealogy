#!/usr/bin/env python3
"""Project the canonical family core into the public people indexes.

The two JSONL files under ``research/people`` are the only family-structure
input.  ``index.html`` is read solely to replace the two generated blocks and
to prove that every generated link has a real target.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html as html_lib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PEOPLE_PATH = Path("research/people/people.jsonl")
RELATIONSHIPS_PATH = Path("research/people/relationships.jsonl")

BRANCH_CODES = {
    "zimmerman": "Z",
    "mundell": "M",
    "dible": "D",
    "connelly": "C",
}
BRANCH_ORDER = tuple(BRANCH_CODES)
BRANCHES = frozenset(BRANCH_CODES)
CONFIDENCES = frozenset({"documented", "strong", "lead", "open"})
ROLES = frozenset({"anchor", "ancestor", "collateral", "candidate"})
OPEN_ROLES = frozenset({"father", "mother", "parents", "earlier_ancestors", "origin"})
COMBINED_NAME_RE = re.compile(r"\s(?:\+|&|and)\s", re.I)

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
        "status",
        "resolution_note",
        "resolved_on",
        "owner_follow_up_required",
        "pedigree",
    }
)

PERSON_ID_RE = re.compile(r"person\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
RELATIONSHIP_ID_RE = re.compile(r"relationship\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
GAP_ID_RE = re.compile(r"gap\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")

SCRIPT_RE = re.compile(r"<script\b(?P<attrs>[^>]*)>.*?</script\s*>", re.I | re.S)
INDEX_SECTION_RE = re.compile(
    r"<section\b(?P<attrs>[^>]*)>.*?</section\s*>", re.I | re.S
)
ATTR_RE = re.compile(
    r"(?P<name>[A-Za-z_:][\w:.-]*)"
    r"(?:\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\s>]+)))?"
)


class ProjectionError(ValueError):
    """The canonical core cannot be projected without guessing."""


class _DuplicateKeyError(ValueError):
    pass


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ProjectionError(f"missing canonical store: {path}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        where = f"{path}:{line_number}"
        if not line.strip():
            raise ProjectionError(f"{where}: blank JSONL lines are not allowed")
        try:
            record = json.loads(line, object_pairs_hook=_object_without_duplicate_keys)
        except (json.JSONDecodeError, _DuplicateKeyError) as exc:
            raise ProjectionError(f"{where}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise ProjectionError(f"{where}: row must be a JSON object")
        records.append(record)
    return records


def _require_exact_fields(
    row: dict[str, Any], expected: frozenset[str], where: str
) -> None:
    if set(row) == expected:
        return
    missing = sorted(expected - set(row))
    unknown = sorted(set(row) - expected)
    details = []
    if missing:
        details.append(f"missing {missing}")
    if unknown:
        details.append(f"unknown {unknown}")
    raise ProjectionError(
        f"{where}: fields do not match the hard-cutover contract ({'; '.join(details)})"
    )


def _require_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectionError(f"{where} must be a non-empty string")
    return value


def _require_sorted_strings(
    value: Any, where: str, *, nonempty: bool = False
) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ProjectionError(f"{where} must be a list of non-empty strings")
    if nonempty and not value:
        raise ProjectionError(f"{where} must not be empty")
    if value != sorted(set(value)):
        raise ProjectionError(f"{where} must be sorted and unique")
    return value


def _require_branches(value: Any, where: str) -> list[str]:
    branches = _require_sorted_strings(value, where, nonempty=True)
    unknown = sorted(set(branches) - BRANCHES)
    if unknown:
        raise ProjectionError(f"{where} contains unknown branches {unknown}")
    return branches


def _optional_anchor(value: Any, grammar: re.Pattern[str], where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not grammar.fullmatch(value):
        raise ProjectionError(f"{where} has an invalid public anchor {value!r}")
    return value


def load_family_core(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Load the one supported canonical shape, rejecting all legacy variants."""

    people = _load_jsonl(root / PEOPLE_PATH)
    person_by_id: dict[str, dict[str, Any]] = {}
    anchors: dict[str, list[str]] = {branch: [] for branch in BRANCH_ORDER}
    for line_number, person in enumerate(people, 1):
        where = f"{PEOPLE_PATH}:{line_number}"
        _require_exact_fields(person, PERSON_FIELDS, where)
        person_id = _require_string(person["id"], f"{where}.id")
        if not PERSON_ID_RE.fullmatch(person_id):
            raise ProjectionError(
                f"{where}.id is not a canonical person id: {person_id!r}"
            )
        if person["node_type"] != "person":
            raise ProjectionError(f"{where}.node_type must be 'person'")
        display_name = _require_string(person["display_name"], f"{where}.display_name")
        index_names = _require_sorted_strings(
            person["index_names"], f"{where}.index_names", nonempty=True
        )
        name_variants = _require_sorted_strings(
            person["name_variants"], f"{where}.name_variants"
        )
        for name in (display_name, *index_names, *name_variants):
            if COMBINED_NAME_RE.search(name):
                raise ProjectionError(
                    f"{where}: person names must describe one individual, not {name!r}"
                )
        branches = _require_branches(person["branches"], f"{where}.branches")
        if person["role"] not in ROLES:
            raise ProjectionError(f"{where}.role is invalid: {person['role']!r}")
        if person["confidence"] not in CONFIDENCES:
            raise ProjectionError(
                f"{where}.confidence is invalid: {person['confidence']!r}"
            )
        if person["privacy"] != "public_deceased":
            raise ProjectionError(f"{where}.privacy must be 'public_deceased'")
        _optional_anchor(
            person["public_anchor"], PERSON_ID_RE, f"{where}.public_anchor"
        )
        if person_id in person_by_id:
            raise ProjectionError(f"{where}: duplicate person id {person_id!r}")
        person_by_id[person_id] = person
        if person["role"] == "anchor":
            for branch in branches:
                anchors[branch].append(person_id)

    for branch, branch_anchors in anchors.items():
        if len(branch_anchors) != 1:
            raise ProjectionError(
                f"branch {branch!r} must have exactly one anchor person; found {branch_anchors}"
            )
    if len({values[0] for values in anchors.values()}) != 4:
        raise ProjectionError("the four branches must have four distinct anchor people")

    rows = _load_jsonl(root / RELATIONSHIPS_PATH)
    relationships: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    seen_ids = set(person_by_id)
    seen_pairs: set[tuple[str, str, str]] = set()
    accepted_parent_roles: set[tuple[str, str]] = set()
    occupied_gap_slots: dict[tuple[str, int], str] = {}
    for line_number, row in enumerate(rows, 1):
        where = f"{RELATIONSHIPS_PATH}:{line_number}"
        node_type = row.get("node_type")
        if node_type == "relationship":
            _require_exact_fields(row, RELATIONSHIP_FIELDS, where)
            relationship_id = _require_string(row["id"], f"{where}.id")
            if not RELATIONSHIP_ID_RE.fullmatch(relationship_id):
                raise ProjectionError(
                    f"{where}.id is not a relationship id: {relationship_id!r}"
                )
            if row["relationship_type"] not in {"parent_of", "spouse_of"}:
                raise ProjectionError(f"{where}.relationship_type is invalid")
            if row["relationship_type"] == "parent_of":
                if row["parent_role"] not in {"father", "mother"}:
                    raise ProjectionError(
                        f"{where}.parent_role must be father or mother for parent_of"
                    )
            elif row["parent_role"] is not None:
                raise ProjectionError(f"{where}.parent_role must be null for spouse_of")
            for field in ("person_a", "person_b"):
                endpoint = _require_string(row[field], f"{where}.{field}")
                if endpoint not in person_by_id:
                    raise ProjectionError(
                        f"{where}.{field} is unresolved: {endpoint!r}"
                    )
            if row["person_a"] == row["person_b"]:
                raise ProjectionError(
                    f"{where}: relationship endpoints must be distinct"
                )
            if row["status"] not in {"accepted", "hypothesis", "rejected"}:
                raise ProjectionError(f"{where}.status is invalid")
            if row["confidence"] not in CONFIDENCES:
                raise ProjectionError(f"{where}.confidence is invalid")
            branches = _require_branches(row["branches"], f"{where}.branches")
            if row["relationship_type"] == "parent_of":
                for branch in branches:
                    for endpoint in (row["person_a"], row["person_b"]):
                        if branch not in person_by_id[endpoint]["branches"]:
                            raise ProjectionError(
                                f"{where}: parent endpoint {endpoint} does not declare "
                                f"branch {branch!r}"
                            )
            relationship_refs = [
                _require_sorted_strings(row[field], f"{where}.{field}")
                for field in ("evidence_refs", "source_refs", "case_refs")
            ]
            if not any(relationship_refs):
                raise ProjectionError(
                    f"{where}: every relationship must cite evidence, source, or case refs"
                )
            _require_string(row["provenance_note"], f"{where}.provenance_note")
            if row["relationship_type"] == "spouse_of":
                first, second = sorted((row["person_a"], row["person_b"]))
                pair_key = ("spouse_of", first, second)
            else:
                pair_key = ("parent_of", row["person_a"], row["person_b"])
            if pair_key in seen_pairs:
                raise ProjectionError(
                    f"{where}: duplicate relationship pair {pair_key}"
                )
            seen_pairs.add(pair_key)
            if row["relationship_type"] == "parent_of" and row["status"] == "accepted":
                role_key = (row["person_b"], row["parent_role"])
                if role_key in accepted_parent_roles:
                    raise ProjectionError(
                        f"{where}: more than one accepted {row['parent_role']} "
                        f"for {row['person_b']}"
                    )
                accepted_parent_roles.add(role_key)
            identifier = relationship_id
            relationships.append(row)
        elif node_type == "gap":
            _require_exact_fields(row, GAP_FIELDS, where)
            gap_id = _require_string(row["id"], f"{where}.id")
            if not GAP_ID_RE.fullmatch(gap_id):
                raise ProjectionError(f"{where}.id is not a gap id: {gap_id!r}")
            if row["gap_type"] not in {
                "parentage",
                "frontier",
                "candidate_parentage",
                "research_cluster",
            }:
                raise ProjectionError(f"{where}.gap_type is invalid")
            _require_string(row["label"], f"{where}.label")
            subjects = _require_sorted_strings(
                row["subject_persons"], f"{where}.subject_persons", nonempty=True
            )
            candidates = _require_sorted_strings(
                row["candidate_persons"], f"{where}.candidate_persons"
            )
            for field, values in (
                ("subject_persons", subjects),
                ("candidate_persons", candidates),
            ):
                unresolved = sorted(set(values) - set(person_by_id))
                if unresolved:
                    raise ProjectionError(
                        f"{where}.{field} has unresolved people {unresolved}"
                    )
            if set(subjects) & set(candidates):
                raise ProjectionError(f"{where}: gap subjects and candidates overlap")
            open_roles = _require_sorted_strings(
                row["open_roles"], f"{where}.open_roles"
            )
            invalid_roles = sorted(set(open_roles) - OPEN_ROLES)
            if invalid_roles:
                raise ProjectionError(
                    f"{where}.open_roles contains invalid roles {invalid_roles}"
                )
            gap_branches = _require_branches(row["branches"], f"{where}.branches")
            _require_sorted_strings(
                row["case_refs"], f"{where}.case_refs", nonempty=True
            )
            for field in ("evidence_refs", "source_refs"):
                _require_sorted_strings(row[field], f"{where}.{field}")
            _optional_anchor(row["public_anchor"], GAP_ID_RE, f"{where}.public_anchor")
            if row["status"] not in {"open", "resolved"}:
                raise ProjectionError(f"{where}.status is invalid")
            if not isinstance(row["resolution_note"], str):
                raise ProjectionError(f"{where}.resolution_note must be a string")
            if row["resolved_on"] is not None:
                if not isinstance(row["resolved_on"], str):
                    raise ProjectionError(
                        f"{where}.resolved_on must be null or an ISO date"
                    )
                try:
                    parsed_date = dt.date.fromisoformat(row["resolved_on"])
                except ValueError as exc:
                    raise ProjectionError(
                        f"{where}.resolved_on must be null or an ISO date"
                    ) from exc
                if parsed_date.isoformat() != row["resolved_on"]:
                    raise ProjectionError(
                        f"{where}.resolved_on must use YYYY-MM-DD"
                    )
            if type(row["owner_follow_up_required"]) is not bool:
                raise ProjectionError(
                    f"{where}.owner_follow_up_required must be boolean"
                )
            if row["status"] == "open" and row["resolved_on"] is not None:
                raise ProjectionError(f"{where}: open gap resolved_on must be null")
            if row["status"] == "resolved":
                if open_roles:
                    raise ProjectionError(
                        f"{where}: resolved gap open_roles must be empty"
                    )
                if candidates:
                    raise ProjectionError(
                        f"{where}: resolved gap candidate_persons must be empty"
                    )
                if not row["resolution_note"].strip():
                    raise ProjectionError(
                        f"{where}: resolved gap resolution_note must not be empty"
                    )
                if row["resolved_on"] is None:
                    raise ProjectionError(
                        f"{where}: resolved gap resolved_on is required"
                    )
                if (
                    row["public_anchor"] is not None
                    and row["owner_follow_up_required"] is not True
                ):
                    raise ProjectionError(
                        f"{where}: resolved public gap must require owner follow-up"
                    )
            if (
                row["owner_follow_up_required"]
                and not row["resolution_note"].strip()
            ):
                raise ProjectionError(
                    f"{where}: owner follow-up requires a resolution note"
                )
            pedigree = row["pedigree"]
            if not isinstance(pedigree, dict) or set(pedigree) != set(
                BRANCH_CODES.values()
            ):
                raise ProjectionError(
                    f"{where}.pedigree must have exactly Z, M, D, and C lists"
                )
            for code in BRANCH_CODES.values():
                slots = pedigree[code]
                if (
                    not isinstance(slots, list)
                    or any(type(slot) is not int for slot in slots)
                    or slots != sorted(set(slots))
                    or any(not 1 <= slot <= 63 for slot in slots)
                ):
                    raise ProjectionError(
                        f"{where}.pedigree.{code} must be sorted unique integers from 1 to 63"
                    )
                branch = next(
                    name
                    for name, branch_code in BRANCH_CODES.items()
                    if branch_code == code
                )
                if slots and branch not in gap_branches:
                    raise ProjectionError(
                        f"{where}.pedigree.{code} has slots but branches omits {branch!r}"
                    )
                for slot in slots:
                    key = (code, slot)
                    if key in occupied_gap_slots:
                        raise ProjectionError(
                            f"pedigree slot {code}-{slot} is claimed by both "
                            f"{occupied_gap_slots[key]} and {gap_id}"
                        )
                    occupied_gap_slots[key] = gap_id
            if row["status"] == "resolved" and any(
                pedigree[code] for code in BRANCH_CODES.values()
            ):
                raise ProjectionError(
                    f"{where}: resolved gap pedigree slots must be empty"
                )
            identifier = gap_id
            gaps.append(row)
        else:
            raise ProjectionError(
                f"{where}.node_type must discriminate 'relationship' or 'gap'"
            )
        if identifier in seen_ids:
            raise ProjectionError(f"{where}: duplicate global id {identifier!r}")
        seen_ids.add(identifier)

    return people, relationships, gaps


def _parent_map(
    relationships: Iterable[dict[str, Any]], branch: str
) -> dict[tuple[str, str], list[tuple[str, str]]]:
    parents: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for relationship in relationships:
        if (
            relationship["relationship_type"] == "parent_of"
            and relationship["status"] != "rejected"
            and branch in relationship["branches"]
        ):
            key = (relationship["person_b"], relationship["parent_role"])
            parents[key].add((relationship["person_a"], relationship["status"]))
    return {key: sorted(values) for key, values in parents.items()}


def _require_parent_acyclic(
    people: list[dict[str, Any]], relationships: list[dict[str, Any]]
) -> None:
    """Reject cycles anywhere in the family core, including unplaced leads."""

    children: dict[str, list[str]] = {person["id"]: [] for person in people}
    for relationship in relationships:
        if (
            relationship["relationship_type"] == "parent_of"
            and relationship["status"] != "rejected"
        ):
            children[relationship["person_a"]].append(relationship["person_b"])

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(person_id: str) -> None:
        state[person_id] = 1
        stack.append(person_id)
        for child in children[person_id]:
            if state.get(child, 0) == 0:
                visit(child)
            elif state.get(child) == 1:
                start = stack.index(child)
                cycle = " -> ".join((*stack[start:], child))
                raise ProjectionError(f"parent_of graph cycles: {cycle}")
        stack.pop()
        state[person_id] = 2

    for person_id in sorted(children):
        if state.get(person_id, 0) == 0:
            visit(person_id)


def project_slots(
    people: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], list[int]], dict[tuple[str, str], list[int]]]:
    """Return actual-person and gap slots, refusing ambiguous ancestry."""

    _require_parent_acyclic(people, relationships)
    person_by_id = {person["id"]: person for person in people}
    anchor_by_branch = {
        branch: next(
            person["id"]
            for person in people
            if person["role"] == "anchor" and branch in person["branches"]
        )
        for branch in BRANCH_ORDER
    }
    gap_by_slot: dict[tuple[str, int], dict[str, Any]] = {}
    gap_slots: dict[tuple[str, str], list[int]] = defaultdict(list)
    for gap in gaps:
        for branch, code in BRANCH_CODES.items():
            for slot in gap["pedigree"][code]:
                gap_by_slot[(code, slot)] = gap
                gap_slots[(gap["id"], branch)].append(slot)

    person_slots: dict[tuple[str, str], list[int]] = defaultdict(list)
    slot_owners: dict[tuple[str, int], str] = {}

    for branch in BRANCH_ORDER:
        code = BRANCH_CODES[branch]
        parents = _parent_map(relationships, branch)

        def visit(person_id: str, slot: int, path: tuple[str, ...]) -> None:
            if person_id in path:
                cycle = " -> ".join((*path, person_id))
                raise ProjectionError(
                    f"{branch} parent graph cycles inside six generations: {cycle}"
                )
            person = person_by_id[person_id]
            if branch not in person["branches"]:
                raise ProjectionError(
                    f"{person_id} reaches {code}-{slot} but does not declare branch {branch!r}"
                )
            gap = gap_by_slot.get((code, slot))
            if gap is not None:
                raise ProjectionError(
                    f"pedigree slot {code}-{slot} is claimed by both {gap['id']} and {person_id}"
                )
            prior = slot_owners.get((code, slot))
            if prior is not None and prior != person_id:
                raise ProjectionError(
                    f"pedigree slot {code}-{slot} resolves to both {prior} and {person_id}"
                )
            slot_owners[(code, slot)] = person_id
            key = (person_id, branch)
            if slot not in person_slots[key]:
                person_slots[key].append(slot)
            next_path = (*path, person_id)
            for parent_role, parent_slot in (
                ("father", slot * 2),
                ("mother", slot * 2 + 1),
            ):
                if parent_slot > 63:
                    continue
                parent_edges = parents.get((person_id, parent_role), [])
                candidates = [parent_id for parent_id, _status in parent_edges]
                explicit_gap = gap_by_slot.get((code, parent_slot))
                if explicit_gap is not None:
                    if person_id not in explicit_gap["subject_persons"]:
                        raise ProjectionError(
                            f"{explicit_gap['id']} owns parent slot {code}-{parent_slot} "
                            f"but does not name subject {person_id}"
                        )
                    missing = sorted(
                        set(candidates) - set(explicit_gap["candidate_persons"])
                    )
                    if missing:
                        raise ProjectionError(
                            f"{explicit_gap['id']} owns parent slot {code}-{parent_slot} "
                            f"but omits candidates {missing}"
                        )
                    accepted = sorted(
                        parent_id
                        for parent_id, status in parent_edges
                        if status == "accepted"
                    )
                    if accepted:
                        raise ProjectionError(
                            f"{explicit_gap['id']} owns parent slot {code}-{parent_slot} "
                            f"but accepted parent edges name {accepted}"
                        )
                    continue
                if len(candidates) > 1:
                    raise ProjectionError(
                        f"{code}-{parent_slot} has competing {parent_role} candidates "
                        f"for {person_id}: {candidates}; an explicit gap must own the slot"
                    )
                if len(candidates) == 1:
                    visit(candidates[0], parent_slot, next_path)

        visit(anchor_by_branch[branch], 1, ())

    for slots in person_slots.values():
        slots.sort()
    for slots in gap_slots.values():
        slots.sort()
    return dict(person_slots), dict(gap_slots)


def build_payload(
    people: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    person_slots: dict[tuple[str, str], list[int]],
    gap_slots: dict[tuple[str, str], list[int]],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for branch in BRANCH_ORDER:
        code = BRANCH_CODES[branch]
        branch_entries: list[dict[str, Any]] = []
        for person in people:
            if branch not in person["branches"] or person["public_anchor"] is None:
                continue
            slots = person_slots.get((person["id"], branch), [])
            branch_entries.append(
                {
                    "i": person["id"],
                    "n": person["display_name"],
                    "a": code,
                    "k": "person",
                    "ah": slots,
                    "t": person["confidence"],
                    "h": person["public_anchor"],
                }
            )
        for gap in gaps:
            if branch not in gap["branches"] or gap["public_anchor"] is None:
                continue
            slots = gap_slots.get((gap["id"], branch), [])
            entry: dict[str, Any] = {
                "i": gap["id"],
                "n": gap["label"],
                "a": code,
                "k": "gap",
                "ah": slots,
                "t": "documented" if gap["status"] == "resolved" else "open",
                "h": gap["public_anchor"],
            }
            if gap["case_refs"]:
                entry["c"] = gap["case_refs"][0]
            branch_entries.append(entry)
        branch_entries.sort(
            key=lambda entry: (
                min(entry["ah"], default=64),
                0 if entry["k"] == "person" else 1,
                _sort_text(entry["n"]),
                entry["i"],
            )
        )
        entries.extend(branch_entries)
    return {"v": 2, "people": entries}


def _sort_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in decomposed if not unicodedata.combining(char)
    ).casefold()


def build_name_index(people: list[dict[str, Any]]) -> str:
    names: list[tuple[str, str, str]] = []
    for person in people:
        anchor = person["public_anchor"]
        if anchor is None:
            continue
        names.extend((name, anchor, person["id"]) for name in person["index_names"])
    names.sort(key=lambda item: (_sort_text(item[0]), item[0], item[2]))

    lines = [
        '<section class="sheet" id="index-of-names">',
        "  <h2>Index of Names</h2>",
        '  <ul class="sources name-index">',
    ]
    prior_letter = ""
    for name, anchor, _person_id in names:
        first = name.lstrip()[:1]
        letter = first.upper() if first.isalpha() else "#"
        if letter != prior_letter:
            lines.append(f'    <li class="index-letter">{html_lib.escape(letter)}</li>')
            prior_letter = letter
        lines.append(
            f'    <li><a href="#{html_lib.escape(anchor, quote=True)}">'
            f"{html_lib.escape(name)}</a></li>"
        )
    lines.extend(["  </ul>", "</section>"])
    return "\n".join(lines)


def _attrs(raw: str) -> dict[str, str | None]:
    attrs: dict[str, str | None] = {}
    for match in ATTR_RE.finditer(raw):
        value = match.group("double")
        if value is None:
            value = match.group("single")
        if value is None:
            value = match.group("bare")
        attrs[match.group("name").lower()] = value
    return attrs


class _IdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: Counter[str] = Counter()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        identifier = dict(attrs).get("id")
        if identifier:
            self.ids[identifier] += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _one_people_script(source: str) -> re.Match[str]:
    matches = []
    for match in SCRIPT_RE.finditer(source):
        attrs = _attrs(match.group("attrs"))
        if attrs.get("id") == "people-index":
            if (attrs.get("type") or "").lower() != "application/json":
                raise ProjectionError(
                    "#people-index must be a script with type application/json"
                )
            matches.append(match)
    if len(matches) != 1:
        raise ProjectionError(
            f"expected exactly one #people-index script; found {len(matches)}"
        )
    return matches[0]


def _one_name_section(source: str) -> re.Match[str]:
    matches = [
        match
        for match in INDEX_SECTION_RE.finditer(source)
        if _attrs(match.group("attrs")).get("id") == "index-of-names"
    ]
    if len(matches) != 1:
        raise ProjectionError(
            f"expected exactly one #index-of-names section; found {len(matches)}"
        )
    return matches[0]


def render_html(
    source: str,
    payload: dict[str, Any],
    people: list[dict[str, Any]],
) -> str:
    parser = _IdParser()
    parser.feed(source)
    targets = {
        entry["h"] for entry in payload["people"] if isinstance(entry.get("h"), str)
    }
    targets.update(
        person["public_anchor"]
        for person in people
        if person["public_anchor"] is not None
    )
    bad_targets = [
        f"{target} ({parser.ids[target]} matches)"
        for target in sorted(targets)
        if parser.ids[target] != 1
    ]
    if bad_targets:
        raise ProjectionError(
            "projected link targets must occur exactly once in index.html: "
            + ", ".join(bad_targets)
        )

    json_text = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    json_text = (
        json_text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    script = f'<script type="application/json" id="people-index">{json_text}</script>'
    section = build_name_index(people)
    replacements = [
        (_one_people_script(source).span(), script),
        (_one_name_section(source).span(), section),
    ]
    rendered = source
    for (start, end), replacement in sorted(replacements, reverse=True):
        rendered = rendered[:start] + replacement + rendered[end:]
    return rendered


def build(root: Path) -> tuple[str, str, dict[str, Any]]:
    people, relationships, gaps = load_family_core(root)
    person_slots, gap_slots = project_slots(people, relationships, gaps)
    payload = build_payload(people, gaps, person_slots, gap_slots)

    reached = {person_id for person_id, _branch in person_slots}
    missing_public = sorted(
        person_id
        for person_id in reached
        if next(person for person in people if person["id"] == person_id)[
            "public_anchor"
        ]
        is None
    )
    if missing_public:
        raise ProjectionError(
            "pedigree people need public_anchor values: " + ", ".join(missing_public)
        )
    slotted_gaps = {gap_id for gap_id, _branch in gap_slots}
    missing_gap_public = sorted(
        gap["id"]
        for gap in gaps
        if gap["id"] in slotted_gaps and gap["public_anchor"] is None
    )
    if missing_gap_public:
        raise ProjectionError(
            "pedigree gaps need public_anchor values: " + ", ".join(missing_gap_public)
        )

    html_path = root / "index.html"
    if not html_path.is_file():
        raise ProjectionError(f"missing presentation file: {html_path}")
    original = html_path.read_text(encoding="utf-8")
    return original, render_html(original, payload, people), payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if either generated block has drifted",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        original, rendered, payload = build(root)
    except ProjectionError as exc:
        print(f"build_people_index: {exc}", file=sys.stderr)
        return 1

    html_path = root / "index.html"
    if args.check:
        if original != rendered:
            print(
                f"{html_path} people projection is out of date; "
                "run uv run tools/build_people_index.py",
                file=sys.stderr,
            )
            return 1
        print(f"people projection current: {len(payload['people'])} entries")
        return 0

    if original != rendered:
        html_path.write_text(rendered, encoding="utf-8")
    print(f"updated {html_path}: {len(payload['people'])} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
