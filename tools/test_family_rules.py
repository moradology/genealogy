#!/usr/bin/env python3
"""Contract tests for tools/family_rules.py (reasoning layer, phases 0-1).

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


def gap_row(gid: str, subjects: list, cases: list, status: str = "open") -> dict:
    return {
        "id": gid, "node_type": "gap", "gap_type": "parentage", "label": gid,
        "subject_persons": subjects, "candidate_persons": [], "open_roles": ["parents"],
        "branches": ["mundell"], "case_refs": cases, "evidence_refs": [],
        "source_refs": [], "public_anchor": gid, "status": status,
        "resolution_note": None, "resolved_on": None, "owner_follow_up_required": False,
        "pedigree": {"Z": [], "M": [6, 7], "D": [], "C": []},
    }


def case_row(cid: str, status: str = "open") -> dict:
    return {
        "id": cid, "node_type": "case", "branch": "mundell", "title": cid,
        "status": status, "summary": "Q: test.", "source_note": "test",
        "person_refs": ["person.a"], "evidence_refs": [], "trace_refs": [],
    }


def event(pid: str, etype: str, date: str, date_sort: str) -> dict:
    return {
        "type": "Feature",
        "id": f"event.{pid.split('.')[-1]}.{etype}.{date_sort}",
        "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
        "properties": {
            "feature_kind": "life_event", "event_type": etype, "person_id": pid,
            "person_name": pid, "anchor": "x", "line_ids": [], "generation": 1,
            "date": date, "date_sort": date_sort, "place_id": "place.test",
            "place_label": "Martin, Smith, Kansas", "confidence": "strong",
            "source_refs": [],
        },
    }


def make_root(tmp: Path, people: list, links_and_gaps: list, events: list,
              cases: list | None = None) -> Path:
    root = tmp / "repo"
    (root / "research" / "people").mkdir(parents=True)
    (root / "research" / "cases").mkdir(parents=True)
    (root / "research" / "evidence").mkdir(parents=True)
    (root / "research" / "reasoning-traces").mkdir(parents=True)
    jl = lambda rows: "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)  # noqa: E731
    (root / "research" / "people" / "people.jsonl").write_text(jl(people))
    (root / "research" / "people" / "relationships.jsonl").write_text(jl(links_and_gaps))
    (root / "research" / "cases" / "cases.jsonl").write_text(jl(cases or []))
    (root / "research" / "evidence" / "mundell.jsonl").write_text("")
    (root / "ancestry_geospatial.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": events}))
    return root


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

if failures:
    print("FAMILY RULES TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("family_rules (phases 0-1): all contract checks passed")
