#!/usr/bin/env python3
"""Deterministic family reasoning rules, phases 0-2.

Phase 0: vitals resolved from dated geojson life events.
Phase 1: contradictions - encoded-opinion rules over the truth stores.
Phase 2: adjudicate - candidate-identity verdicts from tracked structure only.
"""

from __future__ import annotations

import json
from pathlib import Path

from gen_ancestry import name_word_matches, normalized_words


VITAL_FEATURE_KINDS = {"life_event", "candidate_life_event", "life_context"}
SEVERITY_RANK = {"violation": 0, "conflict": 1, "advisory": 2}
NAME_EQUIVALENCE = (
    frozenset({"zodrow", "farrow"}),
    frozenset({"mundell", "mandell", "mondel"}),
    frozenset({"clemans", "clemens", "clemons", "clements"}),
)
PLACE_STOPWORDS = {"and", "city", "co", "county", "of", "states", "the", "town",
                   "township", "twp", "united", "us", "usa"}
SAME_PERSON_AXES = ("chronology", "geo", "middle", "name-core", "spouse")
PARENT_OF_AXES = ("chronology", "geo", "name-core")
MARRIAGE_AGE_FLOOR = 14
PARENT_AGE_MIN = 12
MOTHER_AGE_MAX = 55
FATHER_AGE_MAX = 65
PARENT_AGE_STRAIN_BAND = 10


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
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
    data = json.loads((root / "ancestry_geospatial.geojson").read_text(encoding="utf-8"))
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
        event_id = feature.get("id")
        approx = _is_approx(props.get("date"))
        credited = [person_id]
        if event_type in {"marriage", "marriage_with_name_conflict"}:
            for participant in props.get("participants") or []:
                if isinstance(participant, str) and participant and participant not in credited:
                    credited.append(participant)
        for credited_id in credited:
            vital = people.setdefault(credited_id, _blank_vital())
            if isinstance(event_id, str) and event_id:
                vital["provenance"].append(event_id)
            if event_type == "birth":
                if "birth_year" in vital and vital["birth_year"] != year:
                    vital["conflicts"].append(
                        f"{credited_id} birth_year conflict: {vital['birth_year']} vs {year}"
                    )
                    vital["birth_year"] = min(vital["birth_year"], year)
                else:
                    vital["birth_year"] = year
                vital["birth_approx"] = vital["birth_approx"] or approx
            elif event_type in {"death", "death_or_burial"}:
                if "death_year" in vital and vital["death_year"] != year:
                    vital["conflicts"].append(
                        f"{credited_id} death_year conflict: {vital['death_year']} vs {year}"
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
        findings.append(
            _finding(
                "confidence-vs-evidence",
                "advisory",
                _person_pair(link),
                [_link_id(link)],
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
            tuple(finding["persons"]),
            tuple(finding["links"]),
            tuple(finding["case_refs"]),
            finding.get("subtype", ""),
            finding["detail"],
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


def _evidence_rows(root: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted((root / "research" / "evidence").glob("*.jsonl")):
        rows.extend(_read_jsonl(path))
    return rows


def _exclusion_targets(root: Path) -> list[dict]:
    data = json.loads((root / "ancestry_geospatial.geojson").read_text(encoding="utf-8"))
    return [
        feature
        for feature in data.get("features", [])
        if feature.get("properties", {}).get("feature_kind") == "exclusion_target"
    ]


def _citable_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for row in _evidence_rows(root):
        value = row.get("id")
        if isinstance(value, str):
            ids.add(value)
    sources = root / "research" / "sources" / "sources.jsonl"
    if sources.exists():
        for row in _read_jsonl(sources):
            value = row.get("id")
            if isinstance(value, str):
                ids.add(value)
    return ids


def _equivalence_compatible(word_a: str, word_b: str) -> bool:
    if word_a == word_b:
        return True
    for family in NAME_EQUIVALENCE:
        if word_a in family and word_b in family:
            return True
    return False


def _word_compatible(word_a: str, word_b: str) -> bool:
    return (
        _equivalence_compatible(word_a, word_b)
        or name_word_matches(word_a, word_b)
        or name_word_matches(word_b, word_a)
    )


def _initial_compatible(term: str, word: str) -> bool:
    if len(term) == 1 and word:
        return term[0] == word[0]
    if len(word) == 1 and term:
        return word[0] == term[0]
    return False


def _person_name_strings(row: dict) -> list[str]:
    strings: list[str] = []
    display = row.get("display_name")
    if isinstance(display, str) and display:
        strings.append(display)
    for key in ("index_names", "name_variants"):
        for value in row.get(key) or []:
            if isinstance(value, str) and value:
                strings.append(value)
    return strings


def _display_style_strings(row: dict) -> list[str]:
    strings: list[str] = []
    display = row.get("display_name")
    if isinstance(display, str) and display:
        strings.append(display)
    for value in row.get("name_variants") or []:
        if isinstance(value, str) and value:
            strings.append(value)
    return strings


def _candidate_names(candidate: dict) -> list[list[str]]:
    names = candidate.get("names")
    if not isinstance(names, list):
        return []
    parsed: list[list[str]] = []
    for name in names:
        if isinstance(name, str):
            words = normalized_words(name)
            if words:
                parsed.append(words)
    return parsed


def _target_word_pools(row: dict) -> tuple[set[str], set[str], set[str]]:
    """Return (surname pool, all-words pool, recorded middles).

    Surnames take the first AND last word of every recorded name string so both
    display order and 'Last, First Middle' index order contribute. Middles come
    only from display-style strings, where word position is meaningful.
    """
    surnames: set[str] = set()
    all_words: set[str] = set()
    for value in _person_name_strings(row):
        words = normalized_words(value)
        if not words:
            continue
        all_words.update(words)
        surnames.add(words[0])
        surnames.add(words[-1])
    middles: set[str] = set()
    for value in _display_style_strings(row):
        words = normalized_words(value)
        if len(words) >= 3:
            middles.update(words[1:-1])
    return surnames, all_words, middles


def _name_core_compatible(cand_names: list[list[str]],
                          surnames: set[str], all_words: set[str]) -> bool:
    for words in cand_names:
        surname = words[-1]
        surname_ok = any(_word_compatible(surname, target) for target in sorted(surnames))
        if len(words) == 1:
            given_ok = True
        else:
            given = words[0]
            given_ok = any(
                _word_compatible(given, target) or _initial_compatible(given, target)
                for target in sorted(all_words)
            )
        if surname_ok and given_ok:
            return True
    return False


def _full_name_match(cand_names: list[list[str]], row: dict) -> bool:
    """Bidirectional cover: every word on each side has a compatible counterpart."""
    row_names = [normalized_words(value) for value in _display_style_strings(row)]
    for cand in cand_names:
        for words in row_names:
            if words and _words_cover(cand, words) and _words_cover(words, cand):
                return True
    return False


def _words_cover(covered: list[str], covering: list[str]) -> bool:
    for word in covered:
        if not any(_word_compatible(word, other) or _initial_compatible(word, other)
                   for other in covering):
            return False
    return True


def _strip_trailing_middle(cand_names: list[list[str]], discriminators: dict) -> list[list[str]]:
    """Drop a name's tail word when it IS the declared middle - a partial
    'Given Middle' extraction must not read as given + surname."""
    middle = discriminators.get("middle")
    if not isinstance(middle, str):
        return cand_names
    middle_words = set(normalized_words(middle))
    if not middle_words:
        return cand_names
    trimmed: list[list[str]] = []
    for words in cand_names:
        if len(words) >= 2 and words[-1] in middle_words:
            trimmed.append(words[:-1])
        else:
            trimmed.append(words)
    return trimmed


def _candidate_middle_terms(candidate: dict, cand_names: list[list[str]]) -> list[str]:
    terms: list[str] = []
    discriminators = candidate.get("discriminators") or {}
    for key in ("middle", "initial"):
        value = discriminators.get(key)
        if isinstance(value, str):
            for word in normalized_words(value):
                if word not in terms:
                    terms.append(word)
    if not terms:
        for words in cand_names:
            for word in words[1:-1]:
                if word not in terms:
                    terms.append(word)
    return terms


def _middle_axis(terms: list[str], middles: set[str]) -> str | None:
    if not terms or not middles:
        return None
    for term in terms:
        for middle in sorted(middles):
            if _word_compatible(term, middle) or _initial_compatible(term, middle):
                return "support"
    return "mismatch"


def _place_tokens(labels: list[str]) -> set[str]:
    tokens: set[str] = set()
    for label in labels:
        for word in normalized_words(label):
            if word not in PLACE_STOPWORDS and not word.isdigit():
                tokens.add(word)
    return tokens


def _target_place_labels(root: Path, person_id: str) -> list[str]:
    labels: list[str] = []
    for feature in _geo_events(root):
        props = feature.get("properties", {})
        participants = props.get("participants") or []
        if props.get("person_id") != person_id and person_id not in participants:
            continue
        label = props.get("place_label")
        if isinstance(label, str) and label and label not in labels:
            labels.append(label)
    return labels


def _geo_axis(target_labels: list[str], candidate_places: list) -> tuple[str | None, str]:
    target_tokens = _place_tokens(target_labels)
    candidate_tokens = _place_tokens(
        [place for place in candidate_places if isinstance(place, str)])
    if not target_tokens or not candidate_tokens:
        return None, ""
    overlap = sorted(target_tokens & candidate_tokens)
    if overlap:
        return "support", "shared place words: " + ", ".join(overlap)
    return "mismatch", (
        f"no place overlap between candidate {sorted(candidate_tokens)} "
        f"and recorded {sorted(target_tokens)}")


def _spouse_axis(people_by_id: dict[str, dict], active_links: list[dict],
                 target_id: str, spouse_value: object) -> tuple[str | None, str]:
    if not isinstance(spouse_value, str):
        return None, ""
    words = normalized_words(spouse_value)
    if not words:
        return None, ""
    spouse_surnames: set[str] = set()
    spouse_words: set[str] = set()
    spouse_names: list[str] = []
    for link in active_links:
        if link.get("relationship_type") != "spouse_of" or link.get("status") != "accepted":
            continue
        other = None
        if link.get("person_a") == target_id:
            other = link.get("person_b")
        elif link.get("person_b") == target_id:
            other = link.get("person_a")
        if not isinstance(other, str):
            continue
        row = people_by_id.get(other)
        if not row:
            continue
        display = row.get("display_name")
        if isinstance(display, str):
            spouse_names.append(display)
        row_surnames, row_words, _middles = _target_word_pools(row)
        spouse_surnames.update(row_surnames)
        spouse_words.update(row_words)
    if not spouse_words:
        return None, ""
    surname = words[-1]
    surname_ok = any(_word_compatible(surname, target_word)
                     for target_word in sorted(spouse_surnames))
    given_ok = True
    if len(words) >= 2:
        given = words[0]
        given_ok = any(
            _word_compatible(given, target_word)
            or _initial_compatible(given, target_word)
            for target_word in sorted(spouse_words))
    if surname_ok and given_ok:
        return "support", f"spouse {spouse_value!r} matches a documented spouse"
    return "mismatch", (
        f"spouse {spouse_value!r} matches no documented spouse "
        f"({', '.join(sorted(spouse_names))})")


def _year_band(known: int, offered: int, pad: int) -> str:
    drift = abs(known - offered)
    if drift <= 1 + pad:
        return "compatible"
    if drift <= 4 + pad:
        return "strained"
    return "impossible"


def _chronology_entry(impossible: list[str], strained: list[str],
                      compatible: list[str], evaluated: bool,
                      ) -> tuple[bool, dict | None, dict | None]:
    if impossible:
        return True, {"axis": "chronology", "kind": "impossible",
                      "detail": "; ".join(impossible)}, None
    if strained:
        return True, {"axis": "chronology", "kind": "mismatch",
                      "detail": "strained: " + "; ".join(strained)}, None
    if compatible:
        return True, None, {"axis": "chronology", "detail": "; ".join(compatible)}
    return evaluated, None, None


def _same_person_chronology(target_vital: dict, candidate: dict,
                            ) -> tuple[bool, dict | None, dict | None]:
    birth = candidate.get("birth_year")
    death = candidate.get("death_year")
    impossible: list[str] = []
    strained: list[str] = []
    compatible: list[str] = []
    evaluated = False
    birth_pad = 1 if (target_vital.get("birth_approx")
                      or candidate.get("birth_approx")) else 0
    death_pad = 1 if target_vital.get("death_approx") else 0
    target_birth = target_vital.get("birth_year")
    target_death = target_vital.get("death_year")
    marriage_years = target_vital.get("marriage_years") or []
    if isinstance(birth, int) and isinstance(target_birth, int):
        evaluated = True
        band = _year_band(target_birth, birth, birth_pad)
        detail = f"candidate birth {birth} vs recorded birth {target_birth}"
        {"compatible": compatible, "strained": strained,
         "impossible": impossible}[band].append(detail)
    if isinstance(death, int) and isinstance(target_death, int):
        evaluated = True
        band = _year_band(target_death, death, death_pad)
        detail = f"candidate death {death} vs recorded death {target_death}"
        {"compatible": compatible, "strained": strained,
         "impossible": impossible}[band].append(detail)
    if isinstance(birth, int):
        for year in marriage_years:
            evaluated = True
            age = year - birth
            if age < MARRIAGE_AGE_FLOOR - birth_pad:
                impossible.append(
                    f"candidate would be {age} at the documented {year} marriage")
    if isinstance(death, int):
        for year in marriage_years:
            evaluated = True
            if death < year:
                impossible.append(
                    f"candidate died {death} before the documented {year} marriage")
    return _chronology_entry(impossible, strained, compatible, evaluated)


def _parent_of_chronology(child_vital: dict, candidate: dict, role: str,
                          ) -> tuple[bool, dict | None, dict | None]:
    birth = candidate.get("birth_year")
    death = candidate.get("death_year")
    child_birth = child_vital.get("birth_year")
    if not isinstance(child_birth, int):
        return False, None, None
    pad = 1 if (child_vital.get("birth_approx")
                or candidate.get("birth_approx")) else 0
    impossible: list[str] = []
    strained: list[str] = []
    compatible: list[str] = []
    evaluated = False
    if isinstance(birth, int):
        evaluated = True
        age = child_birth - birth
        role_max = MOTHER_AGE_MAX if role == "mother" else FATHER_AGE_MAX
        if age < PARENT_AGE_MIN - pad:
            impossible.append(
                f"candidate would be {age} at the child's {child_birth} birth")
        elif age > role_max + PARENT_AGE_STRAIN_BAND + pad:
            impossible.append(
                f"candidate would be {age} at the child's birth, "
                f"beyond any plausible {role}")
        elif age > role_max + pad:
            strained.append(
                f"candidate would be {age} at the child's birth")
        else:
            compatible.append(
                f"age {age} at the child's {child_birth} birth is plausible "
                f"for a {role}")
    if isinstance(death, int):
        evaluated = True
        if role == "mother" and death < child_birth - pad:
            impossible.append(
                f"candidate died {death} before the child's {child_birth} birth")
        if role == "father":
            gap = child_birth - death
            if gap > 1 + pad:
                impossible.append(
                    f"candidate died {death}, {gap} years before the child's birth")
            elif gap == 1 or (pad == 1 and gap == 2):
                strained.append(
                    f"candidate died {death}, just before the child's birth")
    return _chronology_entry(impossible, strained, compatible, evaluated)


def _negative_memory(root: Path, people_by_id: dict[str, dict], all_links: list[dict],
                     gaps: list[dict], vital_map: dict[str, dict], claim_type: str,
                     target_id: str | None, child_id: str | None, role: str | None,
                     candidate: dict, cand_names: list[list[str]],
                     tombstone_anchors: list[str], occupants: list[dict]) -> list[dict]:
    entries: list[dict] = []
    focus_ids = {value for value in (target_id, child_id) if value}
    for row in _evidence_rows(root):
        person_refs = set(row.get("person_refs") or []) | set(row.get("opposes") or [])
        if not (focus_ids & person_refs):
            continue
        negative = (
            row.get("status") == "not_found"
            or row.get("record_type") == "search_log"
            or bool(set(row.get("opposes") or []) & focus_ids)
        )
        if negative:
            entries.append({"kind": "evidence", "ref": str(row.get("id") or ""),
                            "refutes": False, "note": str(row.get("title") or "")})
    if claim_type == "parent_of":
        for link in all_links:
            if (link.get("relationship_type") != "parent_of"
                    or link.get("status") != "rejected"
                    or link.get("person_b") != child_id
                    or link.get("parent_role") != role):
                continue
            row = people_by_id.get(link.get("person_a", ""))
            refutes = False
            if row:
                refutes = _full_name_match(cand_names, row)
                birth = candidate.get("birth_year")
                row_birth = vital_map.get(
                    link.get("person_a", ""), {}).get("birth_year")
                if refutes and isinstance(birth, int) and isinstance(row_birth, int):
                    refutes = abs(birth - row_birth) <= 1
            entries.append({"kind": "rejected_relationship", "ref": _link_id(link),
                            "refutes": refutes,
                            "note": str(link.get("provenance_note") or "")})
        for link in occupants:
            entries.append({
                "kind": "occupied_slot", "ref": _link_id(link), "refutes": False,
                "note": (f"{link.get('person_a')} already holds the accepted "
                         f"{role} slot; a second accepted parent would be a "
                         "violation")})
    for gap in gaps:
        if gap.get("status", "open") != "resolved":
            continue
        if focus_ids & set(gap.get("subject_persons") or []):
            entries.append({"kind": "resolved_gap", "ref": str(gap.get("id") or ""),
                            "refutes": False,
                            "note": str(gap.get("resolution_note") or "")})
    if tombstone_anchors:
        birth = candidate.get("birth_year")
        candidate_tokens = _place_tokens(
            [place for place in (candidate.get("places") or [])
             if isinstance(place, str)])
        for feature in _exclusion_targets(root):
            props = feature.get("properties", {})
            if props.get("ancestor_person") not in tombstone_anchors:
                continue
            start_year = _year_from_date_sort(
                props.get("date_start") or props.get("date_sort"))
            refutes = False
            candidate_pid = props.get("candidate_person")
            if isinstance(candidate_pid, str) and candidate_pid in people_by_id:
                years_ok = True
                if isinstance(birth, int) and isinstance(start_year, int):
                    years_ok = abs(start_year - birth) <= 1
                refutes = years_ok and _full_name_match(
                    cand_names, people_by_id[candidate_pid])
            else:
                place_label = props.get("place_label")
                feature_tokens = _place_tokens(
                    [place_label] if isinstance(place_label, str) else [])
                overlap = feature_tokens & candidate_tokens
                needed = min(2, len(feature_tokens))
                refutes = (isinstance(birth, int) and start_year == birth
                           and needed > 0 and len(overlap) >= needed)
            entries.append({"kind": "exclusion_target",
                            "ref": str(feature.get("id") or ""),
                            "refutes": refutes,
                            "note": str(props.get("exclusion_note") or "")})
    entries.sort(key=lambda entry: (entry["kind"], entry["ref"]))
    return entries


def adjudicate(root: Path, claim: dict) -> dict:
    if not isinstance(claim, dict):
        return {"errors": ["claim must be a JSON object"]}
    claim_type = claim.get("claim")
    candidate = claim.get("candidate")
    errors: list[str] = []
    if claim_type not in {"same_person", "parent_of"}:
        errors.append("claim must be 'same_person' or 'parent_of'")
    if not isinstance(candidate, dict):
        errors.append("candidate must be an object")
        candidate = {}
    cand_names = _candidate_names(candidate)
    if not cand_names:
        errors.append("candidate.names must contain at least one non-empty name")
    people_by_id, active_links, all_links, gaps = _family_core(root)
    target_id = claim.get("target")
    child_id = claim.get("child")
    role = claim.get("role")
    if claim_type == "same_person":
        if not isinstance(target_id, str) or target_id not in people_by_id:
            errors.append(f"unknown target person {target_id!r}")
    if claim_type == "parent_of":
        if not isinstance(child_id, str) or child_id not in people_by_id:
            errors.append(f"unknown child person {child_id!r}")
        if role not in {"father", "mother"}:
            errors.append("role must be 'father' or 'mother' for parent_of claims")
    if errors:
        return {"errors": errors}

    vital_map = vitals(root)
    subject_id = target_id if claim_type == "same_person" else child_id
    subject_row = people_by_id[subject_id]
    subject_vital = vital_map.get(subject_id, {})
    axes = SAME_PERSON_AXES if claim_type == "same_person" else PARENT_OF_AXES
    mismatches: list[dict] = []
    supports: list[dict] = []
    evaluated: set[str] = set()

    if claim_type == "same_person":
        chron_eval, chron_mismatch, chron_support = _same_person_chronology(
            subject_vital, candidate)
    else:
        chron_eval, chron_mismatch, chron_support = _parent_of_chronology(
            subject_vital, candidate, role)
    if chron_eval:
        evaluated.add("chronology")
    if chron_mismatch:
        mismatches.append(chron_mismatch)
    elif chron_support:
        supports.append(chron_support)

    trimmed_names = _strip_trailing_middle(
        cand_names, candidate.get("discriminators") or {})
    occupants: list[dict] = []
    matched_occupants: list[str] = []
    if claim_type == "parent_of":
        for link in active_links:
            if (link.get("relationship_type") != "parent_of"
                    or link.get("status") != "accepted"
                    or link.get("person_b") != child_id
                    or link.get("parent_role") != role):
                continue
            occupants.append(link)
            occupant_id = link.get("person_a")
            if not isinstance(occupant_id, str):
                continue
            occupant_row = people_by_id.get(occupant_id)
            if not occupant_row:
                continue
            occupant_surnames, occupant_words, _o = _target_word_pools(occupant_row)
            if _name_core_compatible(trimmed_names, occupant_surnames, occupant_words):
                matched_occupants.append(occupant_id)
        # A claim into an occupied slot whose name matches the occupant is an
        # identity claim about the occupant: their vitals apply too.
        for occupant_id in matched_occupants:
            occupant_eval, occupant_mismatch, occupant_support = (
                _same_person_chronology(vital_map.get(occupant_id, {}), candidate))
            if occupant_eval:
                evaluated.add("chronology")
            if occupant_mismatch:
                mismatches.append(occupant_mismatch)
            elif occupant_support:
                supports.append(occupant_support)

    surnames, all_words, middles = _target_word_pools(subject_row)
    if claim_type == "same_person":
        evaluated.add("name-core")
        if not _name_core_compatible(trimmed_names, surnames, all_words):
            mismatches.append({
                "axis": "name-core", "kind": "mismatch",
                "detail": "candidate name is not compatible with any recorded name"})
    elif role == "father":
        evaluated.add("name-core")
        cand_surnames = sorted({words[-1] for words in trimmed_names})
        if not any(_word_compatible(cand_surname, target_surname)
                   for cand_surname in cand_surnames
                   for target_surname in sorted(surnames)):
            mismatches.append({
                "axis": "name-core", "kind": "mismatch",
                "detail": "candidate surname does not match the child's recorded surname"})

    if claim_type == "same_person":
        terms = _candidate_middle_terms(candidate, cand_names)
        state = _middle_axis(terms, middles)
        if state is not None:
            evaluated.add("middle")
            if state == "support":
                supports.append({
                    "axis": "middle",
                    "detail": "middle name or initial matches the recorded middle name"})
            else:
                mismatches.append({
                    "axis": "middle", "kind": "mismatch",
                    "detail": (f"candidate middle {terms} conflicts with recorded "
                               f"middle {sorted(middles)}")})

    state, detail = _geo_axis(_target_place_labels(root, subject_id),
                              candidate.get("places") or [])
    if state is not None:
        evaluated.add("geo")
        if state == "support":
            supports.append({"axis": "geo", "detail": detail})
        else:
            mismatches.append({"axis": "geo", "kind": "mismatch", "detail": detail})

    if claim_type == "same_person":
        state, detail = _spouse_axis(people_by_id, active_links, subject_id,
                                     candidate.get("spouse"))
        if state is not None:
            evaluated.add("spouse")
            if state == "support":
                supports.append({"axis": "spouse", "detail": detail})
            else:
                mismatches.append({"axis": "spouse", "kind": "mismatch",
                                   "detail": detail})

    if claim_type == "same_person":
        tombstone_anchors = [target_id] if isinstance(target_id, str) else []
    else:
        tombstone_anchors = matched_occupants
    negative = _negative_memory(root, people_by_id, all_links, gaps, vital_map,
                                claim_type, target_id, child_id, role, candidate,
                                cand_names, tombstone_anchors, occupants)
    refutations = [entry for entry in negative if entry["refutes"]]
    impossible = [entry for entry in mismatches if entry["kind"] == "impossible"]
    independent = len({entry["axis"] for entry in mismatches})
    reasons: list[str] = []
    if refutations:
        verdict = "reject"
        for entry in refutations:
            reasons.append(
                f"directly refuted by recorded negative memory: {entry['ref']}")
    elif impossible:
        verdict = "reject"
        for entry in impossible:
            reasons.append(f"chronologically impossible: {entry['detail']}")
    elif independent >= 2:
        verdict = "reject"
        reasons.append(f"{independent} independent mismatch axes: "
                       + ", ".join(sorted({entry["axis"] for entry in mismatches})))
    elif independent == 1:
        verdict = "weak"
        reasons.append("one mismatch axis: " + mismatches[0]["axis"])
    elif supports:
        linking = (candidate.get("discriminators") or {}).get("linking_document")
        if isinstance(linking, str) and linking and linking in _citable_ids(root):
            verdict = "strong"
            reasons.append(f"no mismatches, {len(supports)} supporting axes, "
                           f"linking document cited: {linking}")
        elif isinstance(linking, str) and linking:
            verdict = "plausible"
            reasons.append(f"linking document {linking!r} does not resolve to a "
                           "tracked evidence or source record; capped at plausible")
        else:
            verdict = "plausible"
            reasons.append(f"no mismatches with {len(supports)} supporting axes; "
                           "strong requires a cited linking document")
    else:
        verdict = "weak"
        reasons.append("name compatibility only; every other axis is unknown")

    mismatches.sort(key=lambda entry: (entry["axis"], entry["kind"], entry["detail"]))
    supports.sort(key=lambda entry: (entry["axis"], entry["detail"]))
    envelope = {
        "claim": claim_type,
        "target": target_id,
        "verdict": verdict,
        "score": {"mismatches": len(mismatches),
                  "independent_mismatches": independent,
                  "supports": len(supports)},
        "mismatches": mismatches,
        "supports": supports,
        "reasons": reasons,
        "negative_memory": negative,
        "missing": sorted(set(axes) - evaluated),
    }
    if claim_type == "parent_of":
        envelope["child"] = child_id
        envelope["role"] = role
    return envelope
