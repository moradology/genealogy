#!/usr/bin/env python3
"""Contract tests for tools/family_rules.py (reasoning layer, phases 0-3).

Offline, stdlib only, no pytest, no try/except. Builds tiny synthetic roots per
scenario and calls family_rules functions directly, then smoke-tests the
gen_store CLI envelope against the same fixtures via GEN_STORE_ROOT.
Run: uv run tools/test_family_rules.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import family_rules  # noqa: E402

failures: list[str] = []


def check(name: str, cond: bool, detail: object = "") -> None:
    if not cond:
        failures.append(f"{name}: {detail}")


# ---------- fixture builders ----------

def person(pid: str, name: str = "Test Person") -> dict:
    return {
        "id": pid, "node_type": "person", "display_name": name,
        "index_names": [name], "name_variants": [], "branches": ["mundell"],
        "role": "ancestor", "confidence": "strong", "privacy": "public_deceased",
        "public_anchor": pid,
    }


def plink(parent: str, child: str, role: str, status: str = "accepted",
          confidence: str = "strong", ev: list | None = None, src: list | None = None,
          cases: list | None = None) -> dict:
    return {
        "id": f"relationship.parent.{parent.split('.')[-1]}-to-{child.split('.')[-1]}",
        "node_type": "relationship", "relationship_type": "parent_of",
        "person_a": parent, "person_b": child, "parent_role": role,
        "status": status, "confidence": confidence, "branches": ["mundell"],
        "evidence_refs": ev or [], "source_refs": src if src is not None else ["src.test.x"],
        "case_refs": cases or [], "provenance_note": "test",
    }


def gap_row(gid: str, subjects: list, cases: list, status: str = "open",
            gap_type: str = "parentage", pedigree: dict | None = None) -> dict:
    return {
        "id": gid, "node_type": "gap", "gap_type": gap_type, "label": gid,
        "subject_persons": subjects, "candidate_persons": [], "open_roles": ["parents"],
        "branches": ["mundell"], "case_refs": cases, "evidence_refs": [],
        "source_refs": [], "public_anchor": gid, "status": status,
        "resolution_note": None, "resolved_on": None, "owner_follow_up_required": False,
        "pedigree": pedigree if pedigree is not None
        else {"Z": [], "M": [6, 7], "D": [], "C": []},
    }


def case_row(cid: str, status: str = "open", persons: list | None = None) -> dict:
    return {
        "id": cid, "node_type": "case", "branch": "mundell", "title": cid,
        "status": status, "summary": "Q: test.", "source_note": "test",
        "person_refs": persons or ["person.a"], "evidence_refs": [], "trace_refs": [],
    }


def event(pid: str, etype: str, date: str, date_sort: str,
          place: str = "Martin, Smith, Kansas") -> dict:
    return {
        "type": "Feature",
        "id": f"event.{pid.split('.')[-1]}.{etype}.{date_sort}",
        "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
        "properties": {
            "feature_kind": "life_event", "event_type": etype, "person_id": pid,
            "person_name": pid, "anchor": "x", "line_ids": [], "generation": 1,
            "date": date, "date_sort": date_sort, "place_id": "place.test",
            "place_label": place, "confidence": "strong",
            "source_refs": [],
        },
    }


def make_root(tmp: Path, people: list, links_and_gaps: list, events: list,
              cases: list | None = None, evidence: list | None = None) -> Path:
    root = tmp / "repo"
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "cases").mkdir(parents=True)
    (root / "research" / "evidence").mkdir(parents=True)
    (root / "research" / "reasoning-traces").mkdir(parents=True)
    jl = lambda rows: "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)  # noqa: E731
    (root / "research" / "people" / "people.jsonl").write_text(jl(people))
    (root / "research" / "people" / "relationships.jsonl").write_text(jl(links_and_gaps))
    (root / "research" / "cases" / "cases.jsonl").write_text(jl(cases or []))
    (root / "research" / "evidence" / "mundell.jsonl").write_text(jl(evidence or []))
    (root / "ancestry_geospatial.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": events}))
    return root


def slink(a: str, b: str, status: str = "accepted") -> dict:
    return {
        "id": f"relationship.spouse.{a.split('.')[-1]}-to-{b.split('.')[-1]}",
        "node_type": "relationship", "relationship_type": "spouse_of",
        "person_a": a, "person_b": b, "parent_role": None,
        "status": status, "confidence": "documented", "branches": ["mundell"],
        "evidence_refs": [], "source_refs": ["src.test.x"], "case_refs": [],
        "provenance_note": "test",
    }


def marriage_event(pid: str, date_sort: str, participants: list) -> dict:
    feature = event(pid, "marriage", date_sort, date_sort)
    feature["properties"]["participants"] = participants
    return feature


def exclusion_feature(target_pid: str, candidate_pid: str | None,
                      date_start: str, place_label: str, note: str) -> dict:
    return {
        "type": "Feature",
        "id": f"target.test.exclusion.{date_start}",
        "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
        "properties": {
            "feature_kind": "exclusion_target", "event_type": "same_name_collision",
            "label": f"exclusion {date_start}", "anchor": "x", "line_ids": [],
            "date_start": date_start, "date_sort": date_start,
            "place_label": place_label, "confidence": "lead",
            "candidate_person": candidate_pid, "ancestor_person": target_pid,
            "exclusion_note": note, "source_refs": [],
        },
    }


def negative_evidence(ev_id: str, pid: str) -> dict:
    return {
        "id": ev_id, "record_type": "search_log", "title": f"negative search {ev_id}",
        "repository": "test", "citation": "test", "accessed": "2026-01-01",
        "status": "not_found", "confidence": "medium", "supports": [], "opposes": [],
        "person_refs": [pid], "case_refs": [],
        "privacy_review": {"status": "passed", "reviewed": "2026-01-01",
                           "living_people": "excluded", "sensitive_identifiers": "excluded"},
        "acquisition": {"provider": "Ancestry", "batch": "t", "pull": "01", "local_dirs": []},
        "source_urls": [], "transcription": "nothing found", "local_assets": [],
    }


def same_person_claim(target: str, names: list, **kw) -> dict:
    candidate = {"names": names, "birth_year": kw.get("birth_year"),
                 "birth_approx": kw.get("birth_approx", False),
                 "death_year": kw.get("death_year"), "places": kw.get("places", []),
                 "spouse": kw.get("spouse"),
                 "discriminators": kw.get("discriminators", {})}
    return {"claim": "same_person", "target": target, "candidate": candidate}


def find(findings: list, rule: str) -> list:
    return [f for f in findings if f["rule"] == rule]


with tempfile.TemporaryDirectory(prefix="family-rules-test-") as td:
    tmp = Path(td)

    # ============ Phase 0: vitals ============
    root = make_root(tmp / "v", [person("person.a"), person("person.b"), person("person.c"),
                                 person("person.d"), person("person.e")], [], [
        event("person.a", "birth", "1900-05-01", "1900-05-01"),
        event("person.a", "death", "1960", "1960-01-01"),
        event("person.b", "birth", "about 1851", "1851-01-01"),
        event("person.c", "birth", "1880", "1880-01-01"),
        event("person.c", "birth", "1882", "1882-01-01"),          # conflicting years
        event("person.c", "death_or_burial", "1930", "1930-01-01"),
        event("person.a", "marriage", "1922-06-14", "1922-06-14"),
        event("person.e", "death", "1930", "1930-01-01"),
        event("person.e", "death", "1935", "1935-01-01"),          # conflicting deaths
    ])
    v = family_rules.vitals(root)
    check("vitals full date", v["person.a"]["birth_year"] == 1900 and v["person.a"]["birth_approx"] is False, v.get("person.a"))
    check("vitals death year", v["person.a"]["death_year"] == 1960, v.get("person.a"))
    check("vitals marriage list", v["person.a"]["marriage_years"] == [1922], v.get("person.a"))
    check("vitals about approx", v["person.b"]["birth_year"] == 1851 and v["person.b"]["birth_approx"] is True, v.get("person.b"))
    check("vitals conflict keeps earliest", v["person.c"]["birth_year"] == 1880, v.get("person.c"))
    check("vitals conflict recorded", bool(v["person.c"]["conflicts"]), v.get("person.c"))
    check("vitals death_or_burial maps", v["person.c"]["death_year"] == 1930, v.get("person.c"))
    check("vitals conflict keeps latest death", v["person.e"]["death_year"] == 1935, v.get("person.e"))
    check("vitals death conflict recorded", bool(v["person.e"]["conflicts"]), v.get("person.e"))
    check("vitals undated absent", "person.d" not in v, sorted(v))

    # ============ Phase 1: contradictions ============
    # R1 violation: accepted father born 1900, child born 1910 (father age 10)
    root = make_root(tmp / "r1", [person("person.f"), person("person.k")],
                     [plink("person.f", "person.k", "father")],
                     [event("person.f", "birth", "1900", "1900-01-01"),
                      event("person.k", "birth", "1910", "1910-01-01")])
    out = family_rules.contradictions(root)
    r1 = find(out["findings"], "parent-age")
    check("R1 fires", len(r1) == 1, out["findings"])
    check("R1 is violation", bool(r1) and r1[0]["severity"] == "violation", r1)
    check("R1 makes unclean", out["clean"] is False, out["counts"])

    # Same impossibility on a HYPOTHESIS link -> advisory, clean stays true
    root = make_root(tmp / "r1h", [person("person.f"), person("person.k")],
                     [plink("person.f", "person.k", "father", status="hypothesis")],
                     [event("person.f", "birth", "1900", "1900-01-01"),
                      event("person.k", "birth", "1910", "1910-01-01")])
    out = family_rules.contradictions(root)
    r1 = find(out["findings"], "parent-age")
    check("R1 hypothesis advisory", bool(r1) and r1[0]["severity"] == "advisory", r1)
    check("R1 hypothesis keeps clean", out["clean"] is True, out["counts"])

    # REJECTED link: same impossibility must produce NO finding at all
    root = make_root(tmp / "r1x", [person("person.f"), person("person.k")],
                     [plink("person.f", "person.k", "father", status="rejected")],
                     [event("person.f", "birth", "1900", "1900-01-01"),
                      event("person.k", "birth", "1910", "1910-01-01")])
    out = family_rules.contradictions(root)
    check("rejected link never enters rules", not out["findings"], out["findings"])
    check("rejected link excluded from coverage",
          out["coverage"]["checkable"]["parent_age"] == 0, out["coverage"])

    # R1 exact boundaries (accepted, no approx): limits are 12 <= age, mother <= 55, father <= 65
    def parent_age_root(name: str, role: str, parent_birth: int, child_birth: int,
                        approx: bool = False) -> Path:
        raw = f"about {parent_birth}" if approx else str(parent_birth)
        return make_root(tmp / name, [person("person.p"), person("person.k")],
                         [plink("person.p", "person.k", role)],
                         [event("person.p", "birth", raw, f"{parent_birth}-01-01"),
                          event("person.k", "birth", str(child_birth), f"{child_birth}-01-01")])

    out = family_rules.contradictions(parent_age_root("b1", "father", 1800, 1865))
    check("R1 father 65 ok", not find(out["findings"], "parent-age"), out["findings"])
    out = family_rules.contradictions(parent_age_root("b2", "father", 1800, 1866))
    r1 = find(out["findings"], "parent-age")
    check("R1 father 66 violation", bool(r1) and r1[0]["severity"] == "violation", out["findings"])
    out = family_rules.contradictions(parent_age_root("b3", "mother", 1800, 1855))
    check("R1 mother 55 ok", not find(out["findings"], "parent-age"), out["findings"])
    out = family_rules.contradictions(parent_age_root("b4", "mother", 1800, 1856))
    check("R1 mother 56 violation", bool(find(out["findings"], "parent-age")), out["findings"])
    out = family_rules.contradictions(parent_age_root("b5", "father", 1800, 1812))
    check("R1 age 12 ok", not find(out["findings"], "parent-age"), out["findings"])
    out = family_rules.contradictions(parent_age_root("b6", "father", 1800, 1811))
    check("R1 age 11 violation", bool(find(out["findings"], "parent-age")), out["findings"])
    out = family_rules.contradictions(parent_age_root("b7", "father", 1800, 1811, approx=True))
    check("R1 age 11 approx widened ok", not find(out["findings"], "parent-age"), out["findings"])
    out = family_rules.contradictions(parent_age_root("b8", "father", 1800, 1866, approx=True))
    check("R1 father 66 approx widened ok", not find(out["findings"], "parent-age"), out["findings"])

    # R3 father-death gap policy: 0 ok, 1 strained advisory, 2 violation, 2+approx strained
    def father_death_root(name: str, death: int, birth: int, approx: bool = False) -> Path:
        raw = f"about {death}" if approx else str(death)
        return make_root(tmp / name, [person("person.p"), person("person.k")],
                         [plink("person.p", "person.k", "father")],
                         [event("person.p", "death", raw, f"{death}-01-01"),
                          event("person.k", "birth", str(birth), f"{birth}-01-01")])

    out = family_rules.contradictions(father_death_root("fd0", 1900, 1900))
    check("R3 same year ok", not find(out["findings"], "father-dead-before-birth"), out["findings"])
    out = family_rules.contradictions(father_death_root("fd1", 1900, 1901))
    fd = find(out["findings"], "father-dead-before-birth")
    check("R3 gap 1 advisory strained", bool(fd) and fd[0]["severity"] == "advisory"
          and fd[0].get("subtype") == "strained", fd)
    out = family_rules.contradictions(father_death_root("fd2", 1900, 1902))
    fd = find(out["findings"], "father-dead-before-birth")
    check("R3 gap 2 violation", bool(fd) and fd[0]["severity"] == "violation", fd)
    out = family_rules.contradictions(father_death_root("fd3", 1900, 1902, approx=True))
    fd = find(out["findings"], "father-dead-before-birth")
    check("R3 gap 2 approx advisory strained", bool(fd) and fd[0]["severity"] == "advisory"
          and fd[0].get("subtype") == "strained", fd)

    # R2 violation: accepted mother died 1905, child born 1910
    root = make_root(tmp / "r2", [person("person.m"), person("person.k")],
                     [plink("person.m", "person.k", "mother")],
                     [event("person.m", "death", "1905", "1905-01-01"),
                      event("person.k", "birth", "1910", "1910-01-01")])
    out = family_rules.contradictions(root)
    check("R2 posthumous mother violation",
          any(f["severity"] == "violation" for f in find(out["findings"], "mother-dead-before-birth")),
          out["findings"])

    # R4 death-before-birth (single person)
    root = make_root(tmp / "r4", [person("person.a")], [],
                     [event("person.a", "birth", "1900", "1900-01-01"),
                      event("person.a", "death", "1890", "1890-01-01")])
    out = family_rules.contradictions(root)
    check("R4 death before birth", bool(find(out["findings"], "death-before-birth")), out["findings"])

    # Undated pair: silent, and excluded from checkable counts
    root = make_root(tmp / "und", [person("person.f"), person("person.k")],
                     [plink("person.f", "person.k", "father")], [])
    out = family_rules.contradictions(root)
    check("undated silent", not out["findings"], out["findings"])
    check("undated excluded from checkable", out["coverage"]["checkable"]["parent_age"] == 0, out["coverage"])

    # R9: two ACCEPTED fathers -> violation; hypotheses sharing a case -> conflict
    root = make_root(tmp / "r9a", [person("person.f1"), person("person.f2"), person("person.k")],
                     [plink("person.f1", "person.k", "father"),
                      plink("person.f2", "person.k", "father")], [])
    out = family_rules.contradictions(root)
    r9 = find(out["findings"], "multiple-parent")
    check("R9 accepted violation", bool(r9) and r9[0]["severity"] == "violation", out["findings"])

    root = make_root(tmp / "r9h", [person("person.f1"), person("person.f2"), person("person.k")],
                     [plink("person.f1", "person.k", "father", status="hypothesis", confidence="open", cases=["case.16"]),
                      plink("person.f2", "person.k", "father", status="hypothesis", confidence="open", cases=["case.16"])],
                     [], cases=[case_row("case.16", "in_conflict")])
    out = family_rules.contradictions(root)
    r9 = find(out["findings"], "multiple-parent")
    check("R9 shared-case conflict", bool(r9) and r9[0]["severity"] == "conflict"
          and r9[0].get("subtype") == "recorded_conflict", r9)
    check("R9 conflict keeps clean", out["clean"] is True, out["counts"])

    # R9 hypotheses with NO shared case ref -> advisory unlinked_parent_hypotheses
    root = make_root(tmp / "r9u", [person("person.f1"), person("person.f2"), person("person.k")],
                     [plink("person.f1", "person.k", "father", status="hypothesis", confidence="open", cases=["case.01"]),
                      plink("person.f2", "person.k", "father", status="hypothesis", confidence="open", cases=["case.02"])], [])
    out = family_rules.contradictions(root)
    r9 = find(out["findings"], "multiple-parent")
    check("R9 unlinked hypotheses advisory", bool(r9) and r9[0]["severity"] == "advisory"
          and r9[0].get("subtype") == "unlinked_parent_hypotheses", r9)

    # R7 predicate: both ref lists empty fires; source_refs-backed does not
    root = make_root(tmp / "r7", [person("person.f"), person("person.k"), person("person.g")],
                     [plink("person.f", "person.k", "father", confidence="strong", src=[]),
                      plink("person.g", "person.k", "mother", confidence="strong", src=["src.ok"])], [])
    out = family_rules.contradictions(root)
    r7 = find(out["findings"], "confidence-vs-evidence")
    check("R7 fires only on both-empty", len(r7) == 1, r7)
    check("R7 links are pure relationship ids", bool(r7)
          and r7[0]["links"] == ["relationship.parent.f-to-k"], r7)
    check("R7 persons carry the link endpoints", bool(r7)
          and r7[0]["persons"] == ["person.f", "person.k"], r7)

    # R8: OPEN gap citing a closed case -> advisory; resolved gap ignored;
    # a legacy gap row with NO status field counts as open
    legacy_gap = gap_row("gap.test.legacy", ["person.a"], ["case.01"])
    del legacy_gap["status"]
    root = make_root(tmp / "r8", [person("person.a")],
                     [gap_row("gap.test.open", ["person.a"], ["case.01"]),
                      gap_row("gap.test.resolved", ["person.a"], ["case.01"], status="resolved"),
                      legacy_gap],
                     [], cases=[case_row("case.01", "closed")])
    out = family_rules.contradictions(root)
    r8 = find(out["findings"], "gap-cites-closed-case")
    check("R8 open + legacy gaps advisory, resolved ignored",
          len(r8) == 2 and all(f["severity"] == "advisory" for f in r8), r8)

    # Determinism: identical runs, identical JSON
    a = json.dumps(family_rules.contradictions(root), sort_keys=False)
    b = json.dumps(family_rules.contradictions(root), sort_keys=False)
    check("deterministic output", a == b)

    # Total sort: findings that tie on (severity, rule, first person) must come out
    # in the same order regardless of input row order
    tie_people = [person("person.f"), person("person.k1"), person("person.k2")]
    tie_rows = [plink("person.f", "person.k1", "father", confidence="strong", src=[]),
                plink("person.f", "person.k2", "father", confidence="strong", src=[])]
    out_fwd = family_rules.contradictions(
        make_root(tmp / "sortA", tie_people, tie_rows, []))
    out_rev = family_rules.contradictions(
        make_root(tmp / "sortB", tie_people, list(reversed(tie_rows)), []))
    check("sort is total across input order",
          json.dumps(out_fwd["findings"]) == json.dumps(out_rev["findings"]),
          (out_fwd["findings"], out_rev["findings"]))

    # Coverage block shape
    check("coverage people count", out["coverage"]["people"] == 1, out["coverage"])
    check("counts shape", set(out["counts"]) == {"violation", "conflict", "advisory"}, out["counts"])

    # ============ Phase 2: adjudicate ============
    check("NAME_EQUIVALENCE covers clemans variants",
          any({"clemans", "clemens", "clemons", "clements"} <= s
              for s in family_rules.NAME_EQUIVALENCE), family_rules.NAME_EQUIVALENCE)

    marjorie = person("person.t.marjorie", "Marjorie Evelyn Clemans")
    homer = person("person.t.homer", "Homer Clair Mundell")
    adjudicate_people = [marjorie, homer]
    adjudicate_links = [slink("person.t.marjorie", "person.t.homer")]
    marriage = marriage_event("person.t.homer", "1933-06-19",
                              ["person.t.homer", "person.t.marjorie"])

    def adjudicate_root(name: str, extra_events: list | None = None,
                        extra_links: list | None = None, evidence: list | None = None,
                        extra_people: list | None = None) -> Path:
        return make_root(tmp / name, adjudicate_people + (extra_people or []),
                         adjudicate_links + (extra_links or []),
                         [marriage] + (extra_events or []), evidence=evidence)

    # Vitals: marriage years credit every participant, not just person_id
    root = adjudicate_root("vp")
    v = family_rules.vitals(root)
    check("vitals credits marriage to participants",
          v.get("person.t.marjorie", {}).get("marriage_years") == [1933],
          v.get("person.t.marjorie"))
    check("vitals credits marriage to person_id too",
          v.get("person.t.homer", {}).get("marriage_years") == [1933],
          v.get("person.t.homer"))

    # Chronology: birth drift 10 -> impossible -> reject alone
    root = adjudicate_root("adj-b", extra_events=[
        event("person.t.marjorie", "birth", "1912", "1912-01-01")])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], birth_year=1922))
    check("adjudicate drift-10 impossible reject", out["verdict"] == "reject", out)
    check("adjudicate impossible axis chronology",
          any(m["axis"] == "chronology" and m["kind"] == "impossible"
              for m in out["mismatches"]), out["mismatches"])

    # The Barron shape: target birth UNKNOWN but marriage 1933 documented;
    # candidate b1922 would be 11 at that marriage -> impossible -> reject
    root = adjudicate_root("adj-c")
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], birth_year=1922))
    check("adjudicate marriage-age floor reject", out["verdict"] == "reject", out)

    # Drift 3 -> strained -> one mismatch -> weak, never reject alone
    root = adjudicate_root("adj-d", extra_events=[
        event("person.t.marjorie", "birth", "1912", "1912-01-01")])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], birth_year=1915))
    check("adjudicate strained drift weak", out["verdict"] == "weak", out)
    check("adjudicate strained is one mismatch",
          out["score"]["independent_mismatches"] == 1, out["score"])

    # Approx widening: about-1912 target vs 1914 candidate -> compatible support
    root = adjudicate_root("adj-e", extra_events=[
        event("person.t.marjorie", "birth", "about 1912", "1912-01-01")])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], birth_year=1914))
    check("adjudicate approx drift-2 plausible", out["verdict"] == "plausible"
          and any(s["axis"] == "chronology" for s in out["supports"]), out)

    # NAME_EQUIVALENCE: Clemens~Clemans -> compatible -> weak, NOT reject
    root = adjudicate_root("adj-f")
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemens"]))
    check("adjudicate Clemens equivalence weak not reject",
          out["verdict"] == "weak" and out["score"]["mismatches"] == 0, out)

    # Incompatible surname + wrong geography -> two independent axes -> reject
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Smith"], places=["Liberty Mills, Indiana"]))
    check("adjudicate name+geo two-axis reject", out["verdict"] == "reject"
          and out["score"]["independent_mismatches"] >= 2, out)

    # The Opal shape: middle conflict + spouse conflict -> reject
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Opal Clemans"], spouse="Clay V. Stamper",
        discriminators={"middle": "Opal"}))
    check("adjudicate middle+spouse reject", out["verdict"] == "reject", out)
    check("adjudicate middle and spouse axes",
          {"middle", "spouse"} <= {m["axis"] for m in out["mismatches"]},
          out["mismatches"])

    # Middle INITIAL is compatible with the recorded middle; geo overlap supports
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie E Clemans"],
        places=["Smith County, Kansas"], discriminators={"initial": "E"}))
    check("adjudicate initial+geo plausible", out["verdict"] == "plausible", out)
    check("adjudicate middle initial support",
          any(s["axis"] == "middle" for s in out["supports"]), out["supports"])

    # Strong requires a cited linking document that RESOLVES in the tracked
    # stores; an unresolvable string never promotes
    link_root = adjudicate_root("adj-k", evidence=[
        negative_evidence("ev.test.link", "person.t.homer")])
    out = family_rules.adjudicate(link_root, same_person_claim(
        "person.t.marjorie", ["Marjorie Evelyn Clemans"], places=["Smith County, Kansas"]))
    check("adjudicate caps at plausible without linking document",
          out["verdict"] == "plausible", out)
    out = family_rules.adjudicate(link_root, same_person_claim(
        "person.t.marjorie", ["Marjorie Evelyn Clemans"], places=["Smith County, Kansas"],
        discriminators={"linking_document": "ev.test.link"}))
    check("adjudicate resolvable linking document promotes to strong",
          out["verdict"] == "strong", out)
    out = family_rules.adjudicate(link_root, same_person_claim(
        "person.t.marjorie", ["Marjorie Evelyn Clemans"], places=["Smith County, Kansas"],
        discriminators={"linking_document": "ev.fake.nope"}))
    check("adjudicate fake linking document stays plausible",
          out["verdict"] == "plausible", out)
    check("adjudicate fake linking document called out",
          any("does not resolve" in reason for reason in out["reasons"]), out["reasons"])

    # Spouse axis matches surname-first with a given-name check, not any-word
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], spouse="Clay Clair"))
    check("adjudicate spouse middle-word does not support",
          any(m["axis"] == "spouse" for m in out["mismatches"]), out)
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], spouse="Clay Mundell"))
    check("adjudicate spouse wrong given name does not support",
          any(m["axis"] == "spouse" for m in out["mismatches"]), out)
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"], spouse="Homer"))
    check("adjudicate spouse given-name-only supports",
          any(s["axis"] == "spouse" for s in out["supports"]), out)

    # A partial two-word name whose tail IS the middle discriminator counts once
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Opal"], discriminators={"middle": "Opal"}))
    check("adjudicate partial name counts middle once",
          out["verdict"] == "weak"
          and {m["axis"] for m in out["mismatches"]} == {"middle"}, out)

    # All-unknown with a compatible name -> weak; missing axes reported
    root = adjudicate_root("adj-p")
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"]))
    check("adjudicate all-unknown compatible weak", out["verdict"] == "weak", out)
    check("adjudicate missing axes listed",
          set(out["missing"]) == {"chronology", "geo", "middle", "spouse"}, out["missing"])

    # parent_of: candidate born 1900 cannot father a child born 1905
    kid = person("person.t.kid", "Kid Clemans")
    root = adjudicate_root("adj-l", extra_people=[kid], extra_events=[
        event("person.t.kid", "birth", "1905", "1905-01-01")])
    out = family_rules.adjudicate(root, {
        "claim": "parent_of", "child": "person.t.kid", "role": "father",
        "candidate": {"names": ["Robert Clemans"], "birth_year": 1900,
                      "places": [], "discriminators": {}}})
    check("adjudicate parent_of age-5 reject", out["verdict"] == "reject", out)

    # parent_of: a REJECTED relationship row is a tombstone -> direct refutation
    smith = person("person.t.smith", "John Smith")
    root = adjudicate_root("adj-m", extra_people=[kid, smith],
                           extra_links=[plink("person.t.smith", "person.t.kid",
                                              "father", status="rejected")],
                           extra_events=[event("person.t.kid", "birth", "1905", "1905-01-01")])
    out = family_rules.adjudicate(root, {
        "claim": "parent_of", "child": "person.t.kid", "role": "father",
        "candidate": {"names": ["John Smith"], "birth_year": 1880,
                      "places": [], "discriminators": {}}})
    check("adjudicate rejected tombstone reject", out["verdict"] == "reject", out)
    check("adjudicate tombstone pointer",
          any(n["kind"] == "rejected_relationship" and n.get("refutes")
              for n in out["negative_memory"]), out["negative_memory"])

    # exclusion_target with candidate_person: recorded same-name collision refutes
    opal = person("person.t.opal", "Marjorie Opal Clemans")
    root = adjudicate_root("adj-n", extra_people=[opal], extra_events=[
        exclusion_feature("person.t.marjorie", "person.t.opal", "1914-03-01",
                          "Liberty Mills, Indiana", "recorded exclusion")])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Opal Clemans"], birth_year=1914))
    check("adjudicate exclusion_target refutation", out["verdict"] == "reject"
          and any(n["kind"] == "exclusion_target" and n.get("refutes")
                  for n in out["negative_memory"]), out)

    # exclusion_target without candidate_person: birth year + place overlap match
    root = adjudicate_root("adj-n2", extra_events=[
        exclusion_feature("person.t.marjorie", None, "1918-01-01",
                          "Kit Carson County, Colorado", "too young")])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie E Clemans"], birth_year=1918,
        places=["Kit Carson County, Colorado"]))
    check("adjudicate exclusion matches on year+place", out["verdict"] == "reject", out)

    # A county-precise tombstone must not swallow a merely same-state candidate,
    # whether the state rides with a city or stands alone
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie E Clemans"], birth_year=1918,
        places=["Denver, Colorado"]))
    check("adjudicate state-only overlap does not refute",
          not any(n.get("refutes") for n in out["negative_memory"]),
          out["negative_memory"])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie E Clemans"], birth_year=1918,
        places=["Colorado"]))
    check("adjudicate bare-state candidate does not refute",
          not any(n.get("refutes") for n in out["negative_memory"]),
          out["negative_memory"])

    # parent_of against an OCCUPIED slot is an identity claim on the occupant:
    # the occupant's tombstones and vitals apply
    mother_link = plink("person.t.marjorie", "person.t.kid", "mother")
    occupied = adjudicate_root("adj-q", extra_people=[kid, opal],
                               extra_links=[mother_link],
                               extra_events=[
        event("person.t.kid", "birth", "1935", "1935-01-01"),
        exclusion_feature("person.t.marjorie", "person.t.opal", "1914-03-01",
                          "Liberty Mills, Indiana", "recorded exclusion")])
    out = family_rules.adjudicate(occupied, {
        "claim": "parent_of", "child": "person.t.kid", "role": "mother",
        "candidate": {"names": ["Marjorie Opal Clemans"], "birth_year": 1914,
                      "places": [], "discriminators": {}}})
    check("adjudicate parent_of consults occupant tombstones",
          out["verdict"] == "reject"
          and any(n["kind"] == "exclusion_target" and n.get("refutes")
                  for n in out["negative_memory"]), out)
    check("adjudicate surfaces occupied slot",
          any(n["kind"] == "occupied_slot" for n in out["negative_memory"]),
          out["negative_memory"])
    # Barron shape via parent_of: candidate b1922 matching the occupant's name
    # is judged against the occupant's documented 1933 marriage -> impossible
    out = family_rules.adjudicate(occupied, {
        "claim": "parent_of", "child": "person.t.kid", "role": "mother",
        "candidate": {"names": ["Marjorie Clemans"], "birth_year": 1922,
                      "places": [], "discriminators": {}}})
    check("adjudicate parent_of occupant chronology rejects",
          out["verdict"] == "reject"
          and any(m["axis"] == "chronology" and m["kind"] == "impossible"
                  for m in out["mismatches"]), out)

    # Rejected-row tombstones need year corroboration when both sides are dated
    dated_smith_root = adjudicate_root(
        "adj-m2", extra_people=[kid, smith],
        extra_links=[plink("person.t.smith", "person.t.kid", "father", status="rejected")],
        extra_events=[event("person.t.kid", "birth", "1905", "1905-01-01"),
                      event("person.t.smith", "birth", "1880", "1880-01-01")])
    out = family_rules.adjudicate(dated_smith_root, {
        "claim": "parent_of", "child": "person.t.kid", "role": "father",
        "candidate": {"names": ["John Smith"], "birth_year": 1850,
                      "places": [], "discriminators": {}}})
    check("adjudicate same-name different-birth is not refuted",
          not any(n.get("refutes") for n in out["negative_memory"]),
          out["negative_memory"])

    # Padded father-death gap of 2 mirrors R3: strained, never silent
    out = family_rules.adjudicate(
        adjudicate_root("adj-r", extra_people=[kid], extra_events=[
            event("person.t.kid", "birth", "about 1905", "1905-01-01")]),
        {"claim": "parent_of", "child": "person.t.kid", "role": "father",
         "candidate": {"names": ["Robert Clemans"], "death_year": 1903,
                       "places": [], "discriminators": {}}})
    check("adjudicate padded father gap 2 strained",
          any(m["axis"] == "chronology" and m["kind"] == "mismatch"
              and "strained" in m["detail"] for m in out["mismatches"]), out)

    # not_found evidence surfaces as a pointer but never forces the verdict
    root = adjudicate_root("adj-o", evidence=[
        negative_evidence("ev.test.neg", "person.t.marjorie")])
    out = family_rules.adjudicate(root, same_person_claim(
        "person.t.marjorie", ["Marjorie Clemans"]))
    check("adjudicate surfaces negative evidence",
          any(n["kind"] == "evidence" for n in out["negative_memory"]),
          out["negative_memory"])
    check("adjudicate pointer does not force reject", out["verdict"] == "weak", out)

    # Malformed claims error instead of guessing
    out = family_rules.adjudicate(root, same_person_claim("person.t.nobody", ["X Y"]))
    check("adjudicate unknown target errors", bool(out.get("errors")), out)

    # Determinism
    claim = same_person_claim("person.t.marjorie", ["Marjorie Opal Clemans"],
                              spouse="Clay V. Stamper", discriminators={"middle": "Opal"})
    a = json.dumps(family_rules.adjudicate(root, claim))
    b = json.dumps(family_rules.adjudicate(root, claim))
    check("adjudicate deterministic", a == b)

    # ============ Phase 3: frontier ============
    def ped(pos: list) -> dict:
        return {"Z": [], "M": pos, "D": [], "C": []}

    # Depth: pedigree position 2 outranks position 20; value formula pinned
    root = make_root(tmp / "fr-depth",
                     [person("person.fa", "Frank Alpha"), person("person.fb", "Frank Beta")],
                     [gap_row("gap.a.parents", ["person.fa"], [], pedigree=ped([2, 3])),
                      gap_row("gap.b.parents", ["person.fb"], [], pedigree=ped([20, 21]))],
                     [])
    out = family_rules.frontier(root)
    check("frontier envelope channels", set(out) >= {"online", "offline"}, sorted(out))
    ids = [item["target"] for item in out["online"]]
    check("frontier depth-2 outranks depth-20",
          ids.index("gap.a.parents") < ids.index("gap.b.parents"), ids)
    fa = [i for i in out["online"] if i["target"] == "gap.a.parents"][0]
    fb = [i for i in out["online"] if i["target"] == "gap.b.parents"][0]
    check("frontier depth value formula",
          fa["value"] - fb["value"] == (40 - 6 * 1) - (40 - 6 * 4),
          (fa["value"], fb["value"]))
    check("frontier item shape",
          set(fa) >= {"target", "kind", "subjects", "score", "value", "tractability",
                      "penalty", "why", "suggested_next_record", "case_refs"}, sorted(fa))
    check("frontier score arithmetic",
          fa["score"] == fa["value"] + fa["tractability"] - fa["penalty"], fa)

    # Tractability: dated + county-anchored subject outranks unanchored at equal depth
    root = make_root(tmp / "fr-anchor",
                     [person("person.da", "Dora Dated"), person("person.ua", "Una Undated")],
                     [gap_row("gap.da.parents", ["person.da"], [], pedigree=ped([4, 5])),
                      gap_row("gap.ua.parents", ["person.ua"], [], pedigree=ped([4, 5]))],
                     [event("person.da", "birth", "1880", "1880-01-01")])
    out = family_rules.frontier(root)
    by = {i["target"]: i for i in out["online"] + out["offline"]}
    check("frontier dated subject adds tractability",
          by["gap.da.parents"]["score"] > by["gap.ua.parents"]["score"], by)

    # Penalty: one not_found is exactly -10; three cap at -20
    root = make_root(tmp / "fr-pen",
                     [person("person.p1", "Pia One"), person("person.p2", "Pia Two"),
                      person("person.p3", "Pia Three")],
                     [gap_row("gap.p1.parents", ["person.p1"], [], pedigree=ped([4, 5])),
                      gap_row("gap.p2.parents", ["person.p2"], [], pedigree=ped([4, 5])),
                      gap_row("gap.p3.parents", ["person.p3"], [], pedigree=ped([4, 5]))],
                     [],
                     evidence=[negative_evidence("ev.t.n1", "person.p2"),
                               negative_evidence("ev.t.n2", "person.p3"),
                               negative_evidence("ev.t.n3", "person.p3"),
                               negative_evidence("ev.t.n4", "person.p3")])
    out = family_rules.frontier(root)
    by = {i["target"]: i for i in out["online"] + out["offline"]}
    check("frontier single not_found is -10",
          by["gap.p1.parents"]["score"] - by["gap.p2.parents"]["score"] == 10,
          {k: v["score"] for k, v in by.items()})
    check("frontier penalty caps at -20",
          by["gap.p1.parents"]["score"] - by["gap.p3.parents"]["score"] == 20,
          {k: v["score"] for k, v in by.items()})

    # Kind weights: a weak (lead/open) direct link outranks a floor-depth
    # parentage gap; strong links never become items; undated ancestors do
    root = make_root(tmp / "fr-kind",
                     [person("person.k1", "Kay One"), person("person.k2", "Kay Two"),
                      person("person.k3", "Kay Three")],
                     [gap_row("gap.k1.parents", ["person.k1"], [], pedigree=ped([])),
                      plink("person.k2", "person.k3", "father", confidence="lead")],
                     [])
    out = family_rules.frontier(root)
    ids = [i["target"] for i in out["online"]]
    weak = [i for i in out["online"] if i["kind"] == "weak_link"]
    check("frontier weak link is an item", len(weak) == 1, ids)
    check("frontier weak link outranks floor parentage gap",
          ids.index(weak[0]["target"]) < ids.index("gap.k1.parents"), ids)
    check("frontier undated ancestors are items",
          any(i["kind"] == "undated_person" for i in out["online"]), ids)

    # Case bonus: the sole item citing an open case gets +8; shared items +4
    root = make_root(tmp / "fr-case",
                     [person("person.c1", "Cee One"), person("person.c2", "Cee Two"),
                      person("person.c3", "Cee Three")],
                     [gap_row("gap.c1.parents", ["person.c1"], ["case.31"], pedigree=ped([4, 5])),
                      gap_row("gap.c2.parents", ["person.c2"], ["case.32"], pedigree=ped([4, 5])),
                      gap_row("gap.c3.parents", ["person.c3"], ["case.32"], pedigree=ped([4, 5]))],
                     [], cases=[case_row("case.31"), case_row("case.32")])
    out = family_rules.frontier(root)
    by = {i["target"]: i for i in out["online"]}
    check("frontier sole open-case item beats shared",
          by["gap.c1.parents"]["value"] - by["gap.c2.parents"]["value"] == 4,
          {k: v["value"] for k, v in by.items()})

    # Channel: offline-only coverage lands in offline[], never interleaved
    root = make_root(tmp / "fr-off", [person("person.g1", "Georg Alt")],
                     [gap_row("gap.g1.parents", ["person.g1"], [], pedigree=ped([16, 17]))],
                     [event("person.g1", "birth", "1700", "1700-01-01",
                            place="Dorf, Bayern")])
    out = family_rules.frontier(root)
    check("frontier offline-only lead in offline channel",
          any(i["target"] == "gap.g1.parents" for i in out["offline"])
          and not any(i["target"] == "gap.g1.parents" for i in out["online"]), out)
    georg = [i for i in out["offline"] if i["target"] == "gap.g1.parents"][0]
    check("frontier offline suggestion names the offline class",
          georg["suggested_next_record"]
          and "parish" in georg["suggested_next_record"]["collection"].lower(), georg)

    # Exhausted online coverage (penalty at cap) + matching offline coverage
    # moves the item to the offline channel - the Marjorie shape
    root = make_root(tmp / "fr-exh", [person("person.x1", "Xena Ex")],
                     [gap_row("gap.x1.parents", ["person.x1"], [], pedigree=ped([6, 7]))],
                     [event("person.x1", "marriage", "1933-06-19", "1933-06-19",
                            place="Akron, Washington County, Colorado")],
                     evidence=[negative_evidence("ev.t.x1", "person.x1"),
                               negative_evidence("ev.t.x2", "person.x1")])
    out = family_rules.frontier(root)
    check("frontier exhausted online moves offline",
          any(i["target"] == "gap.x1.parents" for i in out["offline"]), out)
    exhausted = [i for i in out["offline"] if i["target"] == "gap.x1.parents"][0]
    check("frontier marriage-only subject counts as dated",
          any("dated subject" in why for why in exhausted["why"]), exhausted["why"])

    # One evidence row touching multiple subjects is one penalty, not two
    root = make_root(tmp / "fr-multi",
                     [person("person.m1", "Multi One"), person("person.m2", "Multi Two")],
                     [gap_row("gap.m.parents", ["person.m1", "person.m2"], [],
                              pedigree=ped([4, 5]))],
                     [], evidence=[{**negative_evidence("ev.t.m1", "person.m1"),
                                    "person_refs": ["person.m1", "person.m2"]}])
    out = family_rules.frontier(root)
    multi = [i for i in out["online"] + out["offline"]
             if i["target"] == "gap.m.parents"][0]
    check("frontier shared evidence row penalized once", multi["penalty"] == 10, multi)

    # A weak link and a gap citing the same open case both take the shared +4
    root = make_root(tmp / "fr-share",
                     [person("person.s1", "Share One"), person("person.s2", "Share Two"),
                      person("person.s3", "Share Three")],
                     [gap_row("gap.s1.parents", ["person.s1"], ["case.41"],
                              pedigree=ped([4, 5])),
                      plink("person.s2", "person.s3", "father", confidence="lead",
                            cases=["case.41"])],
                     [], cases=[case_row("case.41")])
    out = family_rules.frontier(root)
    shared = {i["target"]: i for i in out["online"]}
    check("frontier cross-kind shared case is +4 for both",
          any("open case reference: +4" in why for why in shared["gap.s1.parents"]["why"])
          and any("open case reference: +4" in why
                  for why in shared[plink("person.s2", "person.s3", "father")["id"]]["why"]),
          shared)

    # Mixed US + German places with a census-era subject stays online
    root = make_root(tmp / "fr-mix", [person("person.mx", "Mixed Mover")],
                     [gap_row("gap.mx.parents", ["person.mx"], [], pedigree=ped([8, 9]))],
                     [event("person.mx", "birth", "1860", "1860-01-01",
                            place="Dorf, Bayern"),
                      event("person.mx", "death", "1930", "1930-01-01",
                            place="Martin, Smith, Kansas")])
    out = family_rules.frontier(root)
    check("frontier mixed-place census-era subject stays online",
          any(i["target"] == "gap.mx.parents" for i in out["online"])
          and not any(i["target"] == "gap.mx.parents" for i in out["offline"]), out)

    # Ties break by id ascending; byte-deterministic output; resolved gaps excluded
    root = make_root(tmp / "fr-tie",
                     [person("person.t1", "Tie One"), person("person.t2", "Tie Two")],
                     [gap_row("gap.zz.parents", ["person.t2"], [], pedigree=ped([4, 5])),
                      gap_row("gap.aa.parents", ["person.t1"], [], pedigree=ped([4, 5]))],
                     [])
    out = family_rules.frontier(root)
    ids = [i["target"] for i in out["online"] if i["kind"] == "parentage"]
    check("frontier tie breaks by id", ids == ["gap.aa.parents", "gap.zz.parents"], ids)
    check("frontier deterministic",
          json.dumps(family_rules.frontier(root)) == json.dumps(family_rules.frontier(root)))
    root = make_root(tmp / "fr-res", [person("person.t1", "Tie One")],
                     [gap_row("gap.rz.parents", ["person.t1"], [], status="resolved")], [])
    out = family_rules.frontier(root)
    check("frontier resolved gap excluded",
          not any(i["target"] == "gap.rz.parents"
                  for i in out["online"] + out["offline"]), out)

    # ============ CLI smoke: ./gen contradictions envelope ============
    repo = Path(__file__).resolve().parent.parent

    def cli(root: Path, *extra: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "GEN_STORE_ROOT": str(root)}
        return subprocess.run(
            [sys.executable, "tools/gen_store.py", "contradictions", *extra],
            cwd=repo, capture_output=True, text=True, env=env,
        )

    bad = make_root(tmp / "cli-bad", [person("person.f"), person("person.k")],
                    [plink("person.f", "person.k", "father")],
                    [event("person.f", "birth", "1900", "1900-01-01"),
                     event("person.k", "birth", "1910", "1910-01-01")])
    r = cli(bad)
    check("cli default exit 0 on violation", r.returncode == 0, r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli envelope shape", payload["command"] == "contradictions"
          and payload["ok"] is True and payload["clean"] is False
          and payload["counts"]["violation"] == 1, payload)
    r = cli(bad, "--strict")
    check("cli strict exit 1 on violation", r.returncode == 1, r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli strict ok mirrors exit", payload["ok"] is False, payload)

    good = make_root(tmp / "cli-clean", [person("person.a")], [],
                     [event("person.a", "birth", "1900", "1900-01-01")])
    r = cli(good, "--strict")
    check("cli strict exit 0 when clean", r.returncode == 0, r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli clean envelope", payload["ok"] is True and payload["clean"] is True, payload)

    # ============ CLI smoke: ./gen adjudicate envelope ============
    adj_cli_root = adjudicate_root("cli-adj")
    env = {**os.environ, "GEN_STORE_ROOT": str(adj_cli_root)}
    claim_json = json.dumps(same_person_claim(
        "person.t.marjorie", ["Marjorie Opal Clemans"], spouse="Clay V. Stamper",
        discriminators={"middle": "Opal"}))
    r = subprocess.run([sys.executable, "tools/gen_store.py", "adjudicate"],
                       cwd=repo, capture_output=True, text=True, env=env, input=claim_json)
    check("cli adjudicate exit 0", r.returncode == 0, r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli adjudicate envelope", payload["command"] == "adjudicate"
          and payload["ok"] is True and payload["verdict"] == "reject", payload)
    r = subprocess.run([sys.executable, "tools/gen_store.py", "adjudicate"],
                       cwd=repo, capture_output=True, text=True, env=env,
                       input=json.dumps({"claim": "same_person"}))
    check("cli adjudicate malformed claim exits 1", r.returncode == 1, r.stdout + r.stderr)

    # ============ CLI smoke: ./gen frontier envelope ============
    fr_root = make_root(tmp / "cli-fr", [person("person.fa", "Frank Alpha")],
                        [gap_row("gap.a.parents", ["person.fa"], [],
                                 pedigree=ped([2, 3]))], [])
    env = {**os.environ, "GEN_STORE_ROOT": str(fr_root)}
    r = subprocess.run([sys.executable, "tools/gen_store.py", "frontier", "--top", "1"],
                       cwd=repo, capture_output=True, text=True, env=env)
    check("cli frontier exit 0", r.returncode == 0, r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli frontier envelope", payload["command"] == "frontier"
          and payload["ok"] is True and len(payload["online"]) == 1, payload)

    # ============ CLI smoke: case close gate refuses on violation ============
    gate_root = make_root(tmp / "cli-gate", [person("person.f"), person("person.k")],
                          [plink("person.f", "person.k", "father")],
                          [event("person.f", "birth", "1900", "1900-01-01"),
                           event("person.k", "birth", "1910", "1910-01-01")],
                          cases=[case_row("case.90", persons=["person.f"])])
    env = {**os.environ, "GEN_STORE_ROOT": str(gate_root)}
    r = subprocess.run([sys.executable, "tools/gen_store.py", "case", "update",
                        "case.90", "--status", "closed"],
                       cwd=repo, capture_output=True, text=True, env=env)
    check("cli case close refused on violation", r.returncode == 1,
          r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli case close names the violation",
          any("parent-age" in error for error in payload.get("errors", [])), payload)

    # The gate must also see people ADDED in the same command - no bypass via
    # close + add-person-ref when the case previously referenced clean people
    bypass_root = make_root(tmp / "cli-gate2",
                            [person("person.x"), person("person.f"), person("person.k")],
                            [plink("person.f", "person.k", "father")],
                            [event("person.f", "birth", "1900", "1900-01-01"),
                             event("person.k", "birth", "1910", "1910-01-01")],
                            cases=[case_row("case.91", persons=["person.x"])])
    env = {**os.environ, "GEN_STORE_ROOT": str(bypass_root)}
    r = subprocess.run([sys.executable, "tools/gen_store.py", "case", "update",
                        "case.91", "--status", "closed",
                        "--add-person-ref", "person.f"],
                       cwd=repo, capture_output=True, text=True, env=env)
    check("cli case close gate sees added person refs", r.returncode == 1,
          r.stdout + r.stderr)
    payload = json.loads(r.stdout)
    check("cli case close bypass names the violation",
          any("parent-age" in error for error in payload.get("errors", [])), payload)

if failures:
    print("FAMILY RULES TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("family_rules (phases 0-3): all contract checks passed")
