#!/usr/bin/env python3
"""Deterministic family reasoning rules, phases 0-1."""

from __future__ import annotations

import json
from pathlib import Path


VITAL_FEATURE_KINDS = {"life_event", "candidate_life_event", "life_context"}
SEVERITY_RANK = {"violation": 0, "conflict": 1, "advisory": 2}


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _family_core(root: Path) -> tuple[dict[str, dict], list[dict], list[dict], list[dict]]:
    people = _read_jsonl(root / "research" / "people" / "people.jsonl")
    rows = _read_jsonl(root / "research" / "people" / "relationships.jsonl")
    people_by_id = {row["id"]: row for row in people}
    all_links = [row for row in rows if row.get("node_type") == "relationship"]
    active_links = [row for row in all_links if row.get("status") != "rejected"]
    gaps = [row for row in rows if row.get("node_type") == "gap"]
    return people_by_id, active_links, all_links, gaps


def _cases(root: Path) -> dict[str, dict]:
    rows = _read_jsonl(root / "research" / "cases" / "cases.jsonl")
    return {row["id"]: row for row in rows}


def _geo_events(root: Path) -> list[dict]:
    data = json.loads((root / "ancestry_geospatial.geojson").read_text())
    return [
        feature
        for feature in data.get("features", [])
        if feature.get("properties", {}).get("feature_kind") in VITAL_FEATURE_KINDS
    ]


def _year_from_date_sort(value: object) -> int | None:
    if not isinstance(value, str) or not value:
        return None
    year = value[:4]
    if len(year) != 4 or not year.isdigit():
        return None
    return int(year)


def _blank_vital() -> dict:
    return {
        "marriage_years": [],
        "birth_approx": False,
        "death_approx": False,
        "provenance": [],
        "conflicts": [],
    }


def _is_approx(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return "about " in value.lower() or "/" in value


def vitals(root: Path) -> dict[str, dict]:
    people: dict[str, dict] = {}
    for feature in _geo_events(root):
        props = feature.get("properties", {})
        event_type = props.get("event_type")
        if event_type not in {
            "birth",
            "death",
            "death_or_burial",
            "marriage",
            "marriage_with_name_conflict",
        }:
            continue
        year = _year_from_date_sort(props.get("date_sort"))
        if year is None:
            continue
        person_id = props.get("person_id")
        if not isinstance(person_id, str) or not person_id:
            continue
        vital = people.setdefault(person_id, _blank_vital())
        event_id = feature.get("id")
        if isinstance(event_id, str) and event_id:
            vital["provenance"].append(event_id)
        approx = _is_approx(props.get("date"))
        if event_type == "birth":
            if "birth_year" in vital and vital["birth_year"] != year:
                vital["conflicts"].append(
                    f"{person_id} birth_year conflict: {vital['birth_year']} vs {year}"
                )
                vital["birth_year"] = min(vital["birth_year"], year)
            else:
                vital["birth_year"] = year
            vital["birth_approx"] = vital["birth_approx"] or approx
        elif event_type in {"death", "death_or_burial"}:
            if "death_year" in vital and vital["death_year"] != year:
                vital["conflicts"].append(
                    f"{person_id} death_year conflict: {vital['death_year']} vs {year}"
                )
                vital["death_year"] = max(vital["death_year"], year)
            else:
                vital["death_year"] = year
            vital["death_approx"] = vital["death_approx"] or approx
        else:
            vital["marriage_years"].append(year)
    for vital in people.values():
        vital["marriage_years"] = sorted(set(vital["marriage_years"]))
        vital["provenance"] = sorted(set(vital["provenance"]))
    return dict(sorted(people.items()))


def _link_id(link: dict) -> str:
    value = link.get("id")
    if isinstance(value, str):
        return value
    return ""


def _link_case_refs(link: dict) -> list[str]:
    refs = link.get("case_refs")
    if not isinstance(refs, list):
        return []
    return sorted(ref for ref in refs if isinstance(ref, str))


def _link_severity(links: list[dict]) -> str:
    if links and all(link.get("status") == "accepted" for link in links):
        return "violation"
    return "advisory"


def _finding(
    rule: str,
    severity: str,
    persons: list[str],
    links: list[str],
    case_refs: list[str],
    detail: str,
    subtype: str | None = None,
) -> dict:
    finding = {
        "rule": rule,
        "severity": severity,
        "persons": persons,
        "links": links,
        "case_refs": case_refs,
        "detail": detail,
    }
    if subtype is not None:
        finding["subtype"] = subtype
    return finding


def _birth_year(vital_map: dict[str, dict], person_id: str) -> int | None:
    value = vital_map.get(person_id, {}).get("birth_year")
    if isinstance(value, int):
        return value
    return None


def _death_year(vital_map: dict[str, dict], person_id: str) -> int | None:
    value = vital_map.get(person_id, {}).get("death_year")
    if isinstance(value, int):
        return value
    return None


def _birth_approx(vital_map: dict[str, dict], person_id: str) -> bool:
    return bool(vital_map.get(person_id, {}).get("birth_approx"))


def _death_approx(vital_map: dict[str, dict], person_id: str) -> bool:
    return bool(vital_map.get(person_id, {}).get("death_approx"))


def _pad(*flags: bool) -> int:
    if any(flags):
        return 1
    return 0


def _person_pair(link: dict) -> list[str]:
    people: list[str] = []
    for key in ("person_a", "person_b"):
        value = link.get(key)
        if isinstance(value, str) and value:
            people.append(value)
    return people


def _parent_age_findings(
    active_links: list[dict], vital_map: dict[str, dict]
) -> tuple[list[dict], int]:
    findings: list[dict] = []
    checkable = 0
    for link in active_links:
        if link.get("relationship_type") != "parent_of":
            continue
        parent_id = link.get("person_a")
        child_id = link.get("person_b")
        if not isinstance(parent_id, str) or not isinstance(child_id, str):
            continue
        parent_birth = _birth_year(vital_map, parent_id)
        child_birth = _birth_year(vital_map, child_id)
        if parent_birth is None or child_birth is None:
            continue
        checkable += 1
        age = child_birth - parent_birth
        padding = _pad(
            _birth_approx(vital_map, parent_id), _birth_approx(vital_map, child_id)
        )
        role = link.get("parent_role")
        too_young = age < 12 - padding
        too_old = (
            (role == "mother" and age > 55 + padding)
            or (role == "father" and age > 65 + padding)
        )
        if too_young or too_old:
            findings.append(
                _finding(
                    "parent-age",
                    _link_severity([link]),
                    [parent_id, child_id],
                    [_link_id(link)],
                    _link_case_refs(link),
                    f"{parent_id} would be {age} at {child_id}'s birth",
                )
            )
    return findings, checkable


def _parent_death_findings(active_links: list[dict], vital_map: dict[str, dict]) -> list[dict]:
    findings: list[dict] = []
    for link in active_links:
        if link.get("relationship_type") != "parent_of":
            continue
        parent_id = link.get("person_a")
        child_id = link.get("person_b")
        if not isinstance(parent_id, str) or not isinstance(child_id, str):
            continue
        parent_death = _death_year(vital_map, parent_id)
        child_birth = _birth_year(vital_map, child_id)
        if parent_death is None or child_birth is None:
            continue
        role = link.get("parent_role")
        padding = _pad(
            _death_approx(vital_map, parent_id), _birth_approx(vital_map, child_id)
        )
        if role == "mother" and parent_death < child_birth - padding:
            findings.append(
                _finding(
                    "mother-dead-before-birth",
                    _link_severity([link]),
                    [parent_id, child_id],
                    [_link_id(link)],
                    _link_case_refs(link),
                    f"{parent_id} death year {parent_death} precedes {child_id} birth year {child_birth}",
                )
            )
        if role == "father":
            gap = child_birth - parent_death
            if gap > 1 + padding:
                findings.append(
                    _finding(
                        "father-dead-before-birth",
                        _link_severity([link]),
                        [parent_id, child_id],
                        [_link_id(link)],
                        _link_case_refs(link),
                        f"{parent_id} death year {parent_death} is {gap} years before {child_id} birth year {child_birth}",
                    )
                )
            elif gap == 1 or (padding == 1 and gap == 2):
                findings.append(
                    _finding(
                        "father-dead-before-birth",
                        "advisory",
                        [parent_id, child_id],
                        [_link_id(link)],
                        _link_case_refs(link),
                        f"{parent_id} death year {parent_death} is strained against {child_id} birth year {child_birth}",
                        "strained",
                    )
                )
    return findings


def _person_vital_findings(
    people_by_id: dict[str, dict], vital_map: dict[str, dict]
) -> tuple[list[dict], int, int]:
    findings: list[dict] = []
    death_before_birth_checkable = 0
    marriage_age_checkable = 0
    for person_id in sorted(people_by_id):
        vital = vital_map.get(person_id, {})
        birth = _birth_year(vital_map, person_id)
        death = _death_year(vital_map, person_id)
        if birth is not None and death is not None:
            death_before_birth_checkable += 1
            padding = _pad(
                bool(vital.get("birth_approx")), bool(vital.get("death_approx"))
            )
            if death < birth - padding:
                findings.append(
                    _finding(
                        "death-before-birth",
                        "violation",
                        [person_id],
                        [],
                        [],
                        f"{person_id} death year {death} precedes birth year {birth}",
                    )
                )
        marriage_years = vital.get("marriage_years", [])
        if birth is not None and marriage_years:
            marriage_age_checkable += 1
            padding = _pad(bool(vital.get("birth_approx")))
            for marriage_year in marriage_years:
                age = marriage_year - birth
                if age < 14 - padding:
                    findings.append(
                        _finding(
                            "marriage-age",
                            "violation",
                            [person_id],
                            [],
                            [],
                            f"{person_id} would be {age} at marriage year {marriage_year}",
                        )
                    )
    return findings, death_before_birth_checkable, marriage_age_checkable


def _confidence_findings(active_links: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for link in active_links:
        if link.get("status") != "accepted":
            continue
        if link.get("confidence") not in {"documented", "strong"}:
            continue
        if link.get("evidence_refs", []) != [] or link.get("source_refs", []) != []:
            continue
        link_ref = _link_id(link)
        person_a = link.get("person_a")
        if isinstance(person_a, str) and person_a not in link_ref:
            link_ref = f"{link_ref} {person_a}"
        findings.append(
            _finding(
                "confidence-vs-evidence",
                "advisory",
                _person_pair(link),
                [link_ref],
                _link_case_refs(link),
                f"{_link_id(link)} is {link.get('confidence')} with no evidence_refs or source_refs",
            )
        )
    return findings


def _gap_case_findings(gaps: list[dict], cases_by_id: dict[str, dict]) -> list[dict]:
    findings: list[dict] = []
    for gap in gaps:
        if gap.get("status", "open") != "open":
            continue
        refs = gap.get("case_refs", [])
        if not isinstance(refs, list):
            refs = []
        closed_refs = sorted(
            ref
            for ref in refs
            if isinstance(ref, str) and cases_by_id.get(ref, {}).get("status") == "closed"
        )
        if not closed_refs:
            continue
        persons: list[str] = []
        for key in ("subject_persons", "candidate_persons"):
            values = gap.get(key, [])
            if isinstance(values, list):
                persons.extend(value for value in values if isinstance(value, str))
        findings.append(
            _finding(
                "gap-cites-closed-case",
                "advisory",
                sorted(set(persons)),
                [],
                closed_refs,
                f"{gap.get('id')} is open while citing closed case(s) {', '.join(closed_refs)}",
            )
        )
    return findings


def _multiple_parent_findings(active_links: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = {}
    for link in active_links:
        if link.get("relationship_type") != "parent_of":
            continue
        child_id = link.get("person_b")
        role = link.get("parent_role")
        if not isinstance(child_id, str) or role not in {"father", "mother"}:
            continue
        groups.setdefault((child_id, role), []).append(link)
    findings: list[dict] = []
    for (child_id, role), links in sorted(groups.items()):
        if len(links) < 2:
            continue
        sorted_links = sorted(links, key=_link_id)
        statuses = [link.get("status") for link in sorted_links]
        case_counts: dict[str, int] = {}
        for link in sorted_links:
            for ref in _link_case_refs(link):
                case_counts[ref] = case_counts.get(ref, 0) + 1
        shared_case_refs = sorted(ref for ref, count in case_counts.items() if count >= 2)
        all_case_refs = sorted(case_counts)
        parents = sorted(
            value
            for value in (link.get("person_a") for link in sorted_links)
            if isinstance(value, str)
        )
        link_ids = [_link_id(link) for link in sorted_links]
        if all(status == "accepted" for status in statuses):
            findings.append(
                _finding(
                    "multiple-parent",
                    "violation",
                    [child_id] + parents,
                    link_ids,
                    all_case_refs,
                    f"{child_id} has multiple accepted {role} links",
                )
            )
        elif "hypothesis" in statuses and shared_case_refs:
            findings.append(
                _finding(
                    "multiple-parent",
                    "conflict",
                    [child_id] + parents,
                    link_ids,
                    shared_case_refs,
                    f"{child_id} has multiple {role} hypotheses recorded in shared case(s)",
                    "recorded_conflict",
                )
            )
        else:
            findings.append(
                _finding(
                    "multiple-parent",
                    "advisory",
                    [child_id] + parents,
                    link_ids,
                    all_case_refs,
                    f"{child_id} has multiple unlinked {role} hypotheses",
                    "unlinked_parent_hypotheses",
                )
            )
    return findings


def _generation_gap_findings(active_links: list[dict], vital_map: dict[str, dict]) -> list[dict]:
    parents_by_child: dict[str, list[dict]] = {}
    for link in active_links:
        if link.get("relationship_type") != "parent_of":
            continue
        if link.get("status") != "accepted":
            continue
        child_id = link.get("person_b")
        if not isinstance(child_id, str):
            continue
        parents_by_child.setdefault(child_id, []).append(link)
    for links in parents_by_child.values():
        links.sort(key=_link_id)

    findings: list[dict] = []
    for descendant_id in sorted(vital_map):
        descendant_birth = _birth_year(vital_map, descendant_id)
        if descendant_birth is None:
            continue
        stack: list[tuple[str, list[dict], set[str]]] = [
            (descendant_id, [], {descendant_id})
        ]
        while stack:
            current_id, path, seen = stack.pop()
            for link in reversed(parents_by_child.get(current_id, [])):
                parent_id = link.get("person_a")
                if not isinstance(parent_id, str) or parent_id in seen:
                    continue
                next_path = path + [link]
                parent_birth = _birth_year(vital_map, parent_id)
                if parent_birth is not None and len(next_path) >= 2:
                    average_gap = (descendant_birth - parent_birth) / len(next_path)
                    padding = _pad(
                        _birth_approx(vital_map, descendant_id),
                        _birth_approx(vital_map, parent_id),
                    )
                    if average_gap < 14 - padding or average_gap > 60 + padding:
                        findings.append(
                            _finding(
                                "generation-gap",
                                "advisory",
                                [parent_id, descendant_id],
                                [_link_id(path_link) for path_link in next_path],
                                sorted(
                                    {
                                        ref
                                        for path_link in next_path
                                        for ref in _link_case_refs(path_link)
                                    }
                                ),
                                f"{parent_id} to {descendant_id} averages {average_gap:.1f} years over {len(next_path)} generations",
                            )
                        )
                stack.append((parent_id, next_path, seen | {parent_id}))
    return findings


def _coverage(
    people_by_id: dict[str, dict],
    vital_map: dict[str, dict],
    parent_age_checkable: int,
    death_before_birth_checkable: int,
    marriage_age_checkable: int,
) -> dict:
    dated_birth = 0
    dated_death = 0
    dated_both = 0
    for person_id in people_by_id:
        has_birth = _birth_year(vital_map, person_id) is not None
        has_death = _death_year(vital_map, person_id) is not None
        if has_birth:
            dated_birth += 1
        if has_death:
            dated_death += 1
        if has_birth and has_death:
            dated_both += 1
    return {
        "people": len(people_by_id),
        "dated_birth": dated_birth,
        "dated_death": dated_death,
        "dated_both": dated_both,
        "checkable": {
            "parent_age": parent_age_checkable,
            "death_before_birth": death_before_birth_checkable,
            "marriage_age": marriage_age_checkable,
        },
    }


def _sort_findings(findings: list[dict]) -> list[dict]:
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_RANK[finding["severity"]],
            finding["rule"],
            finding["persons"][0] if finding["persons"] else "",
        ),
    )


def contradictions(root: Path) -> dict:
    people_by_id, active_links, _all_links, gaps = _family_core(root)
    cases_by_id = _cases(root)
    vital_map = vitals(root)

    findings: list[dict] = []
    parent_age_findings, parent_age_checkable = _parent_age_findings(
        active_links, vital_map
    )
    findings.extend(parent_age_findings)
    findings.extend(_parent_death_findings(active_links, vital_map))
    (
        person_findings,
        death_before_birth_checkable,
        marriage_age_checkable,
    ) = _person_vital_findings(people_by_id, vital_map)
    findings.extend(person_findings)
    findings.extend(_generation_gap_findings(active_links, vital_map))
    findings.extend(_confidence_findings(active_links))
    findings.extend(_gap_case_findings(gaps, cases_by_id))
    findings.extend(_multiple_parent_findings(active_links))

    sorted_findings = _sort_findings(findings)
    counts = {"violation": 0, "conflict": 0, "advisory": 0}
    for finding in sorted_findings:
        counts[finding["severity"]] += 1
    return {
        "clean": counts["violation"] == 0,
        "counts": counts,
        "coverage": _coverage(
            people_by_id,
            vital_map,
            parent_age_checkable,
            death_before_birth_checkable,
            marriage_age_checkable,
        ),
        "findings": sorted_findings,
    }
