#!/usr/bin/env python3
"""Acceptance test for tools/gen_store.py (cockpit write-side + orientation verbs).

Offline, stdlib only, no pytest, no try/except. Runs the CLI as a subprocess
against a FIXTURE COPY of the repo (GEN_STORE_ROOT override) so the real truth
stores are never written by tests. Run: uv run tools/test_gen_store.py
"""

from __future__ import annotations

import json
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

failures: list[str] = []


def check(name: str, cond: bool, detail: object = "") -> None:
    if not cond:
        failures.append(f"{name}: {detail}")


def make_fixture(tmp: Path) -> Path:
    root = tmp / "repo"
    root.mkdir()
    for rel in (
        "research/cases",
        "research/evidence",
        "research/people",
        "research/sources",
        "research/reasoning-traces",
    ):
        shutil.copytree(REPO / rel, root / rel)
    for rel in ("index.html", "ancestry_geospatial.geojson"):
        shutil.copy(REPO / rel, root / rel)
    return root


def store(root: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "GEN_STORE_ROOT": str(root)}
    return subprocess.run(
        [sys.executable, "tools/gen_store.py", *args],
        cwd=REPO, capture_output=True, text=True, env=env, input=stdin,
    )


def valid_record(rec_id: str, pull: str | None = "auto") -> dict:
    rec = {
        "id": rec_id,
        "record_type": "census",
        "title": "Test census household",
        "repository": "National Archives and Records Administration; accessed through Ancestry",
        "citation": "Test citation; Ancestry collection 62308, record 99999999.",
        "citation_gap": "Enumeration district and sheet not captured.",
        "status": "found",
        "confidence": "high",
        "supports": [],
        "opposes": [],
        "person_refs": ["person.evelyn_mundell"],
        "case_refs": ["case.08"],
        "privacy_review": {"status": "passed", "reviewed": "2026-07-09",
                           "living_people": "excluded", "sensitive_identifiers": "excluded"},
        "acquisition": {"provider": "Ancestry", "batch": "ancestry-2026-07", "local_dirs": []},
        "source_urls": ["https://www.ancestry.com/search/collections/62308/records/99999999"],
        "transcription": "A test transcription naming no living people.",
        "local_assets": [],
    }
    if pull is not None:
        rec["acquisition"]["pull"] = pull
    return rec


with tempfile.TemporaryDirectory(prefix="gen-store-test-") as td:
    root = make_fixture(Path(td))
    shard_path = root / "research/evidence/mundell.jsonl"
    original = shard_path.read_bytes()

    # ---- evidence add: happy path with pull auto-assignment ----
    r = store(root, "evidence", "add", "--shard", "mundell", stdin=json.dumps(valid_record("ev.test.alpha")))
    o = json.loads(r.stdout)
    check("add ok", o.get("ok") is True and r.returncode == 0, r.stdout[:300] + r.stderr[:300])
    check("add reports id", o.get("id") == "ev.test.alpha", o)
    check("add auto pull is 2-digit", isinstance(o.get("pull"), str) and len(o["pull"]) == 2 and o["pull"].isdigit(), o)
    first_pull = o.get("pull")
    lines = [json.loads(x) for x in shard_path.read_text().splitlines() if x.strip()]
    added = [x for x in lines if x["id"] == "ev.test.alpha"]
    check("added line present", len(added) == 1, len(added))
    check("added line carries accessed date", bool(added[0].get("accessed")), added[0].get("accessed"))
    pulls = [x["acquisition"]["pull"] for x in lines if x["acquisition"]["batch"] == "ancestry-2026-07"]
    check("auto pull unique in batch", pulls.count(added[0]["acquisition"]["pull"]) == 1, pulls)

    # ---- evidence add: duplicate id refused, store untouched ----
    before = shard_path.read_bytes()
    r = store(root, "evidence", "add", "--shard", "mundell", stdin=json.dumps(valid_record("ev.test.alpha")))
    check("dup id refused", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])
    check("dup id no write", shard_path.read_bytes() == before)

    # ---- evidence add: missing privacy attestation refused, store untouched ----
    rec = valid_record("ev.test.beta")
    del rec["privacy_review"]
    r = store(root, "evidence", "add", "--shard", "mundell", stdin=json.dumps(rec))
    o = json.loads(r.stdout)
    check("no-privacy refused", r.returncode != 0 and o["ok"] is False, r.stdout[:200])
    check("no-privacy error names attestation", "privacy" in json.dumps(o).lower(), o)
    check("no-privacy no write", shard_path.read_bytes() == before)

    # ---- evidence add: validator-invalid record is reverted byte-identically ----
    rec = valid_record("ev.test.gamma")
    rec["record_type"] = "not_a_real_type"
    r = store(root, "evidence", "add", "--shard", "mundell", stdin=json.dumps(rec))
    o = json.loads(r.stdout)
    check("invalid refused", r.returncode != 0 and o["ok"] is False, r.stdout[:300])
    check("invalid reverted byte-identical", shard_path.read_bytes() == before)

    # ---- evidence add: --validate-only never writes ----
    r = store(root, "evidence", "add", "--shard", "mundell", "--validate-only",
              stdin=json.dumps(valid_record("ev.test.delta")))
    o = json.loads(r.stdout)
    check("validate-only ok", o.get("ok") is True and o.get("written") is False, r.stdout[:300])
    check("validate-only no write", shard_path.read_bytes() == before)

    # ---- trace new: scaffold passes check_traces, refs sorted ----
    r = store(root, "trace", "new", "--slug", "test-thread", "--title", "A Test Thread",
              "--date", "2026-07-09",
              "--case-refs", "case.08,case.05",
              "--evidence-refs", "ev.ancestry.1950-homer-mundell",
              "--person-refs", "person.mundell.homer,person.evelyn_mundell")
    o = json.loads(r.stdout)
    check("trace new ok", o.get("ok") is True and r.returncode == 0, r.stdout[:300] + r.stderr[:300])
    tpath = root / "research/reasoning-traces/2026-07-09-test-thread.md"
    check("trace file exists", tpath.exists())
    text = tpath.read_text()
    trace_original = tpath.read_bytes()
    check("trace id derived", "id: trace.2026-07-09.test-thread" in text, text[:200])
    check("trace case refs sorted", text.find('"case.05"') < text.find('"case.08"'), text[:400])
    check("trace person refs sorted",
          text.find('"person.evelyn_mundell"') < text.find('"person.mundell.homer"'), text[:600])

    # ---- trace new: refusing to overwrite ----
    r = store(root, "trace", "new", "--slug", "test-thread", "--title", "Again", "--date", "2026-07-09")
    check("trace overwrite refused", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])
    check("trace overwrite preserves original bytes", tpath.read_bytes() == trace_original)

    # ---- trace new: bad ref fails validation and the file is not left behind ----
    r = store(root, "trace", "new", "--slug", "bad-refs", "--title", "Bad", "--date", "2026-07-09",
              "--evidence-refs", "ev.does.not.exist")
    check("trace bad ref refused", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:300])
    check("trace bad ref cleaned up", not (root / "research/reasoning-traces/2026-07-09-bad-refs.md").exists())

    # ---- trace new --body-file: authored body instead of template ----
    body_md = Path(td) / "body.md"
    body_md.write_text("# Authored Body\n\nReal prose instead of placeholders.\n")
    r = store(root, "trace", "new", "--slug", "authored-body", "--title", "Authored", "--date", "2026-07-09",
              "--body-file", str(body_md))
    o = json.loads(r.stdout)
    check("body-file trace ok", o.get("ok") is True, r.stdout[:300])
    authored = (root / "research/reasoning-traces/2026-07-09-authored-body.md").read_text()
    check("body-file content used", "Real prose instead of placeholders." in authored)
    check("body-file no template placeholders", "State the current best hypothesis" not in authored)
    r = store(root, "trace", "new", "--slug", "missing-body", "--title", "X", "--date", "2026-07-09",
              "--body-file", str(Path(td) / "nope.md"))
    check("missing body file refused", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])

    # ---- show: a case, with reverse references ----
    r = store(root, "show", "case.05")
    o = json.loads(r.stdout)
    check("show case ok", o.get("ok") is True and o.get("kind") == "case", r.stdout[:200])
    check("show case record", o.get("record", {}).get("id") == "case.05", str(o)[:200])
    refby = o.get("referenced_by", {})
    check("show case reverse traces", any("mundell" in t for t in refby.get("traces", [])), refby)
    check("show case reverse evidence", "ev.ancestry.1950-adolph-mundell" in refby.get("evidence", []), refby)

    # ---- show: an evidence id ----
    r = store(root, "show", "ev.ancestry.1950-homer-mundell")
    o = json.loads(r.stdout)
    check("show evidence ok", o.get("ok") is True and o.get("kind") == "evidence", r.stdout[:200])

    # ---- show: canonical people and family-core rows (never HTML scraping) ----
    r = store(root, "show", "person.doyle_zimmerman")
    o = json.loads(r.stdout)
    check("show person ok", o.get("ok") is True and o.get("kind") == "person", r.stdout[:200])
    check(
        "show person canonical shape",
        o.get("record", {}).get("display_name") == "Doyle Julius Zimmerman",
        o.get("record"),
    )
    check(
        "show person reverse relationships",
        "relationship.parent.zimmerman_leonard-to-doyle_zimmerman"
        in o.get("referenced_by", {}).get("relationships", []),
        o.get("referenced_by"),
    )
    check(
        "show person reverse geo events",
        "event.doyle_zimmerman.birth.1930-04-12"
        in o.get("referenced_by", {}).get("geo", []),
        o.get("referenced_by"),
    )

    r = store(root, "show", "relationship.parent.zimmerman_leonard-to-doyle_zimmerman")
    o = json.loads(r.stdout)
    check(
        "show relationship ok",
        o.get("ok") is True and o.get("kind") == "relationship",
        r.stdout[:200],
    )

    r = store(root, "show", "gap.fleckenstein.catherine.parents")
    o = json.loads(r.stdout)
    check("show gap ok", o.get("ok") is True and o.get("kind") == "gap", r.stdout[:200])

    # ---- show: unknown id ----
    r = store(root, "show", "nope.nothing")
    check("show unknown rc", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])

    # ---- case list: structured filtering, canonical trace ids only ----
    r = store(root, "case", "list", "--status", "open,in_conflict", "--branch", "mundell")
    o = json.loads(r.stdout)
    check("case list ok", r.returncode == 0 and o.get("ok") is True, r.stdout[:300])
    check("case list filtered", o.get("count") == 6, o.get("cases"))
    check("case list statuses", all(
        case.get("status") in {"open", "in_conflict"}
        and case.get("branch") == "mundell"
        for case in o.get("cases", [])), o.get("cases"))
    check("case list canonical traces", all(
        trace.startswith("trace.")
        for case in o.get("cases", []) for trace in case.get("trace_refs", [])),
        o.get("cases"))
    r = store(root, "case", "list", "--status", "bogus")
    check("case list invalid filter refused",
          r.returncode != 0 and json.loads(r.stdout).get("ok") is False, r.stdout[:200])

    # ---- a second auto-pull add gets a DISTINCT pull number ----
    r = store(root, "evidence", "add", "--shard", "mundell", stdin=json.dumps(valid_record("ev.test.epsilon")))
    o2 = json.loads(r.stdout)
    check("second add ok", o2.get("ok") is True, r.stdout[:300])
    check("second pull distinct", o2.get("pull") != first_pull, (first_pull, o2.get("pull")))

    # ---- no temp-file litter in the evidence dir after adds/refusals ----
    litter = list((root / "research/evidence").glob("*.tmp"))
    check("no tmp litter", not litter, litter)
    trace_litter = list((root / "research/reasoning-traces").glob("*.tmp"))
    check("no trace tmp litter", not trace_litter, trace_litter)

    # ---- case update: truth-first chained write (cases.jsonl + docket + stamp) ----
    html_path = root / "index.html"
    cases_store = root / "research/cases/cases.jsonl"
    html_before = html_path.read_bytes()

    # Canonical trace ids are the only accepted write shape. Filenames are a
    # read-side alias, never persisted back into a truth store.
    r = store(root, "case", "update", "case.08",
              "--add-trace-ref", "trace.2026-07-09.test-thread")
    o = json.loads(r.stdout)
    check("case canonical trace add ok", o.get("ok") is True, r.stdout[:300])
    case08 = next(json.loads(line) for line in cases_store.read_text().splitlines()
                  if json.loads(line).get("id") == "case.08")
    check("case stores canonical trace id",
          "trace.2026-07-09.test-thread" in case08["trace_refs"], case08["trace_refs"])
    canonical_case_bytes = cases_store.read_bytes()
    r = store(root, "case", "update", "case.08",
              "--add-trace-ref", "2026-07-09-test-thread.md")
    o = json.loads(r.stdout)
    check("case trace filename refused", r.returncode != 0 and o.get("ok") is False, o)
    check("case trace filename no write", cases_store.read_bytes() == canonical_case_bytes)

    sentinel = "Q: explain Leora/William Rogers. UPDATED-BY-TEST sentinel summary."
    r = store(root, "case", "update", "case.08",
              "--summary", sentinel,
              "--add-person-ref", "person.clemans.marjorie")
    o = json.loads(r.stdout)
    check("case update ok", o.get("ok") is True and o.get("written") is True, r.stdout[:400] + r.stderr[:200])
    check("case update changed summary", o.get("changed", {}).get("summary") is True, o.get("changed"))
    check("case update added person ref", o.get("added", {}).get("person_refs") == ["person.clemans.marjorie"], o.get("added"))
    check("case update reports stamp", bool(o.get("stamp")), o.get("stamp"))
    check("docket regenerated with new summary", sentinel in html_path.read_text())
    check("index.html actually rewritten", html_path.read_bytes() != html_before)
    updated = [json.loads(x) for x in cases_store.read_text().splitlines() if x.strip() and json.loads(x)["id"] == "case.08"][0]
    check("cases.jsonl carries new summary", "UPDATED-BY-TEST" in updated["summary"])

    # ---- identical rerun: pure no-op ----
    r = store(root, "case", "update", "case.08", "--summary", sentinel,
              "--add-person-ref", "person.clemans.marjorie")
    o = json.loads(r.stdout)
    check("case update noop", o.get("noop") is True and o.get("written") is False, r.stdout[:300])

    # ---- crash recovery: stale docket region self-repairs on a no-op rerun ----
    html_path.write_text(html_path.read_text().replace(sentinel, "STALE DOCKET BYTES."))
    r = store(root, "case", "update", "case.08", "--summary", sentinel,
              "--add-person-ref", "person.clemans.marjorie")
    o = json.loads(r.stdout)
    check("repair reported", o.get("repaired") == "docket", r.stdout[:300])
    check("repair restored region", sentinel in html_path.read_text())

    # ---- validate-only: no writes ----
    before_pair = (html_path.read_bytes(), cases_store.read_bytes())
    r = store(root, "case", "update", "case.08", "--summary", "another candidate", "--validate-only")
    o = json.loads(r.stdout)
    check("case validate-only ok", o.get("ok") is True and o.get("validate_only") is True, r.stdout[:300])
    check("case validate-only no writes",
          (html_path.read_bytes(), cases_store.read_bytes()) == before_pair)

    # ---- refusals: unknown id; closing a case a published gap points to ----
    r = store(root, "case", "update", "case.99", "--summary", "x")
    check("unknown case refused", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])
    r = store(root, "case", "update", "case.14", "--status", "closed")
    o = json.loads(r.stdout)
    check("published-gap close refused", r.returncode != 0 and o["ok"] is False, r.stdout[:300])
    check("refusal names the gap rule", "gap" in " ".join(o.get("errors", [])).lower(), o.get("errors"))

    # ---- relationship update: whole-store validation + projection/stamp ----
    relationships_store = root / "research/people/relationships.jsonl"
    relationship_id = "relationship.parent.cantwell_barnabas-to-cantwell_sarah_alice"
    before_family = (relationships_store.read_bytes(), html_path.read_bytes())
    r = store(root, "relationship", "update", relationship_id,
              "--status", "accepted")
    o = json.loads(r.stdout)
    check("relationship status requires provenance",
          r.returncode != 0 and "provenance" in json.dumps(o).lower(), o)
    check("relationship missing provenance no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_family)

    r = store(root, "relationship", "update", relationship_id,
              "--status", "accepted", "--confidence", "strong",
              "--provenance-note", "Direct test evidence replaces the working hypothesis.",
              "--add-evidence-ref", "ev.test.alpha", "--validate-only")
    o = json.loads(r.stdout)
    check("relationship validate-only ok",
          r.returncode == 0 and o.get("validate_only") is True, r.stdout[:400])
    check("relationship validate-only no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_family)

    r = store(root, "relationship", "update", relationship_id,
              "--status", "accepted", "--confidence", "strong",
              "--provenance-note", "Direct test evidence replaces the working hypothesis.",
              "--add-evidence-ref", "ev.test.alpha")
    o = json.loads(r.stdout)
    check("relationship update ok",
          r.returncode == 0 and o.get("written") is True
          and o.get("projection") == "regenerated", r.stdout[:400])
    family_rows = [json.loads(line) for line in relationships_store.read_text().splitlines()]
    relationship = next(row for row in family_rows if row.get("id") == relationship_id)
    check("relationship scalars updated",
          relationship["status"] == "accepted" and relationship["confidence"] == "strong",
          relationship)
    check("relationship evidence sorted",
          relationship["evidence_refs"] == sorted(relationship["evidence_refs"])
          and "ev.test.alpha" in relationship["evidence_refs"], relationship["evidence_refs"])
    r = store(root, "relationship", "update", relationship_id,
              "--status", "accepted", "--confidence", "strong",
              "--provenance-note", "Direct test evidence replaces the working hypothesis.",
              "--add-evidence-ref", "ev.test.alpha")
    o = json.loads(r.stdout)
    check("relationship update idempotent", o.get("noop") is True, r.stdout[:300])

    prior_provenance = relationship["provenance_note"]
    r = store(root, "relationship", "update", relationship_id,
              "--status", "rejected",
              "--provenance-note", "A later direct record rejects this edge.")
    o = json.loads(r.stdout)
    check("relationship rejection update ok",
          r.returncode == 0 and o.get("written") is True, o)
    family_rows = [json.loads(line) for line in relationships_store.read_text().splitlines()]
    rejected_relationship = next(
        row for row in family_rows if row.get("id") == relationship_id)
    check("relationship rejection retains provenance",
          rejected_relationship["status"] == "rejected"
          and rejected_relationship["provenance_note"].startswith(prior_provenance)
          and "Rejected on" in rejected_relationship["provenance_note"],
          rejected_relationship)
    rejected_bytes = relationships_store.read_bytes()
    r = store(root, "relationship", "update", relationship_id,
              "--status", "rejected",
              "--provenance-note", "A later direct record rejects this edge.")
    o = json.loads(r.stdout)
    check("relationship rejection replay noops",
          r.returncode == 0 and o.get("noop") is True, o)
    check("relationship rejection replay retains bytes",
          relationships_store.read_bytes() == rejected_bytes)
    r = store(root, "show", relationship_id)
    o = json.loads(r.stdout)
    check("directly rejected relationship remains showable",
          r.returncode == 0 and o.get("record", {}).get("status") == "rejected", o)

    before_family = (relationships_store.read_bytes(), html_path.read_bytes())
    r = store(root, "relationship", "update", relationship_id,
              "--add-evidence-ref", "ev.does.not.exist")
    o = json.loads(r.stdout)
    check("relationship bad ref refused", r.returncode != 0 and o.get("ok") is False, o)
    check("relationship bad ref no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_family)

    # ---- gap resolve: explicit conflict adjudication, partial then full ----
    gap_id = "gap.ford.john_laborn.parentage"
    john_sr = "relationship.parent.ford_john_laborn_sr-to-ford_john_laborn"
    levi = "relationship.parent.ford_levi-to-ford_john_laborn"
    family_rows = [json.loads(line) for line in relationships_store.read_text().splitlines()]
    levi_original_provenance = next(
        row for row in family_rows if row.get("id") == levi
    )["provenance_note"]
    next(row for row in family_rows if row.get("id") == gap_id)["evidence_refs"] = [
        "ev.test.epsilon"
    ]
    relationships_store.write_text("".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in family_rows))
    before_family = (relationships_store.read_bytes(), html_path.read_bytes())
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha")
    o = json.loads(r.stdout)
    check("gap conflict requires explicit rejection",
          r.returncode != 0 and levi in json.dumps(o), o)
    check("gap conflict no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_family)

    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha",
              "--reject-relationship", levi)
    o = json.loads(r.stdout)
    check("gap rejection requires provenance",
          r.returncode != 0 and "provenance" in json.dumps(o).lower(), o)
    check("gap missing provenance no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_family)

    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha",
              "--reject-relationship", levi,
              "--provenance-note", "Direct test evidence selects John Sr. and rejects Levi.",
              "--validate-only")
    o = json.loads(r.stdout)
    check("gap partial validate-only ok",
          r.returncode == 0 and o.get("validate_only") is True, r.stdout[:500])
    check("gap partial validate-only no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_family)

    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha",
              "--reject-relationship", levi,
              "--provenance-note", "Direct test evidence selects John Sr. and rejects Levi.")
    o = json.loads(r.stdout)
    check("gap partial resolve ok",
          r.returncode == 0 and o.get("resolved") is False
          and o.get("remaining_open_roles") == ["mother"], r.stdout[:500])
    check("gap partial owner warning",
          o.get("owner_follow_up_required") is True
          and o.get("owner_anchor") == gap_id, o)
    family_rows = [json.loads(line) for line in relationships_store.read_text().splitlines()]
    ford_gap = next(row for row in family_rows if row.get("id") == gap_id)
    selected_father = next(row for row in family_rows if row.get("id") == john_sr)
    check("gap partial shrinks role and slot",
          ford_gap["open_roles"] == ["mother"]
          and ford_gap["pedigree"]["C"] == [45]
          and ford_gap["status"] == "open"
          and ford_gap["owner_follow_up_required"] is True
          and ford_gap["resolved_on"] is None, ford_gap)
    check("gap partial prunes typed candidates",
          ford_gap["candidate_persons"] == ["person.davis.aritta"],
          ford_gap["candidate_persons"])
    check("gap selected parent accepted",
          selected_father["status"] == "accepted"
          and {"ev.test.alpha", "ev.test.epsilon"}
          <= set(selected_father["evidence_refs"]), selected_father)
    check("gap evidence retained on tombstone",
          {"ev.test.alpha", "ev.test.epsilon"} <= set(ford_gap["evidence_refs"]),
          ford_gap["evidence_refs"])
    check("gap rejection persisted in provenance",
          levi in selected_father["provenance_note"], selected_father["provenance_note"])
    rejected_levi = next(row for row in family_rows if row.get("id") == levi)
    check("gap rejected relationship retained",
          rejected_levi["status"] == "rejected"
          and rejected_levi["provenance_note"].startswith(levi_original_provenance)
          and "Rejected on" in rejected_levi["provenance_note"]
          and "ev.test.alpha" in rejected_levi["evidence_refs"]
          and "src.muhlenberg-county-heritage-vol-5-no-1.3ab8ae71"
          in rejected_levi["source_refs"], rejected_levi)

    r = store(root, "show", levi)
    o = json.loads(r.stdout)
    check("rejected relationship remains showable",
          r.returncode == 0 and o.get("record", {}).get("status") == "rejected", o)

    # Simulate a crash after truth landed but before its generated projection:
    # restore the pre-write HTML and replay the exact same action.
    partial_relationships = relationships_store.read_bytes()
    partial_html = html_path.read_bytes()
    html_path.write_bytes(before_family[1])
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha",
              "--reject-relationship", levi,
              "--provenance-note", "Direct test evidence selects John Sr. and rejects Levi.")
    o = json.loads(r.stdout)
    check("partial gap replay repairs projection",
          r.returncode == 0 and o.get("replay") is True
          and o.get("repaired") == "people-index" and o.get("written") is True, o)
    check("partial gap replay preserves truth",
          relationships_store.read_bytes() == partial_relationships, o)
    check("partial gap replay restores exact html", html_path.read_bytes() == partial_html)
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha",
              "--reject-relationship", levi,
              "--provenance-note", "Direct test evidence selects John Sr. and rejects Levi.")
    o = json.loads(r.stdout)
    check("partial gap replay noops when current",
          r.returncode == 0 and o.get("replay") is True
          and o.get("noop") is True and o.get("written") is False, o)

    before_nonidentical = (relationships_store.read_bytes(), html_path.read_bytes())
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.ford.john_laborn_sr", "--role", "father",
              "--evidence-ref", "ev.test.alpha", "--evidence-ref", "ev.test.epsilon",
              "--reject-relationship", levi,
              "--provenance-note", "Direct test evidence selects John Sr. and rejects Levi.")
    o = json.loads(r.stdout)
    check("nonidentical partial replay refused", r.returncode != 0 and o.get("ok") is False, o)
    check("nonidentical partial replay no writes",
          (relationships_store.read_bytes(), html_path.read_bytes()) == before_nonidentical)

    r = store(root, "ancestors", "person.donna_connelly")
    o = json.loads(r.stdout)
    check("partial parent gap remains on frontier",
          any(gap.get("id") == gap_id and gap.get("open_roles") == ["mother"]
              for gap in o.get("frontier", [])), o.get("frontier"))
    check("rejected parent excluded from traversal",
          all(person.get("id") != "person.ford.levi"
              for layer in o.get("generations", []) for person in layer),
          o.get("generations"))

    pre_full_html = html_path.read_bytes()
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.davis.aritta", "--role", "mother",
              "--evidence-ref", "ev.test.alpha")
    o = json.loads(r.stdout)
    check("gap full resolve ok",
          r.returncode == 0 and o.get("resolved") is True
          and o.get("owner_follow_up_required") is True, r.stdout[:500])
    family_rows = [json.loads(line) for line in relationships_store.read_text().splitlines()]
    ford_gap = next(row for row in family_rows if row.get("id") == gap_id)
    check("resolved gap retained as canonical tombstone",
          ford_gap["open_roles"] == [] and ford_gap["candidate_persons"] == []
          and ford_gap["public_anchor"] == gap_id
          and ford_gap["status"] == "resolved"
          and ford_gap["resolved_on"] == dt.date.today().isoformat()
          and ford_gap["owner_follow_up_required"] is True
          and "mother of person.ford.john_laborn as person.davis.aritta"
          in ford_gap["resolution_note"]
          and "ev.test.alpha" in ford_gap["resolution_note"]
          and all(not slots for slots in ford_gap["pedigree"].values()), ford_gap)
    full_relationships = relationships_store.read_bytes()
    full_html = html_path.read_bytes()
    html_path.write_bytes(pre_full_html)
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.davis.aritta", "--role", "mother",
              "--evidence-ref", "ev.test.alpha")
    o = json.loads(r.stdout)
    check("full gap replay repairs projection",
          r.returncode == 0 and o.get("replay") is True
          and o.get("repaired") == "people-index" and o.get("written") is True, o)
    check("full gap replay preserves truth",
          relationships_store.read_bytes() == full_relationships, o)
    check("full gap replay restores exact html", html_path.read_bytes() == full_html)
    r = store(root, "gap", "resolve", gap_id,
              "--parent", "person.davis.aritta", "--role", "mother",
              "--evidence-ref", "ev.test.alpha")
    o = json.loads(r.stdout)
    check("full gap replay noops when current",
          r.returncode == 0 and o.get("replay") is True
          and o.get("noop") is True and o.get("written") is False, o)
    r = store(root, "ancestors", "person.donna_connelly")
    o = json.loads(r.stdout)
    check("resolved tombstone leaves frontier",
          all(gap.get("id") != gap_id for gap in o.get("frontier", [])),
          o.get("frontier"))

    # ---- traversal verbs over the family core ----
    r = store(root, "ancestors", "person.evelyn_mundell")
    o = json.loads(r.stdout)
    check("ancestors ok", o.get("ok") is True and r.returncode == 0, r.stdout[:300])
    gen1 = {x["id"] for x in o.get("generations", [[]])[0]}
    check("ancestors gen1 parents", {"person.mundell.homer", "person.clemans.marjorie"} <= gen1, gen1)
    check("ancestors reach rust", any(
        x["id"] == "person.rust.john_f" for layer in o.get("generations", []) for x in layer), o.get("count"))
    check("ancestors frontier has marjorie gap", any(
        "case.07" in (g.get("case_refs") or []) for g in o.get("frontier", [])), o.get("frontier"))
    r = store(root, "path", "person.rust.john_f", "person.evelyn_mundell")
    o = json.loads(r.stdout)
    check("path ok", o.get("ok") is True and o.get("length") == 3, r.stdout[:300])
    check("path steps carry confidence", all(st.get("confidence") for st in o.get("steps", [])), o.get("steps"))
    r = store(root, "ancestors", "person.nobody")
    check("ancestors unknown refused", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])

    # ---- status: fast dashboard, no Playwright; ok mirrors exit code ----
    r = store(root, "status")
    o = json.loads(r.stdout)
    check("status ok field", isinstance(o.get("ok"), bool), r.stdout[:200])
    check("status ok mirrors rc", o.get("ok") == (r.returncode == 0), f"ok={o.get('ok')} rc={r.returncode}")
    check("status cases histogram", isinstance(o.get("cases", {}).get("open"), int), o.get("cases"))
    check("status evidence counts", isinstance(o.get("evidence", {}).get("total"), int), o.get("evidence"))
    check("status validators subfield", isinstance(o.get("validators"), dict) and o["validators"], o.get("validators"))
    check("status family validator", o.get("validators", {}).get("family") is True, o.get("validators"))
    check("status family counts", o.get("family", {}).get("people") == 117, o.get("family"))
    check("status gap lifecycle counts",
          o.get("family", {}).get("gaps_by_status") == {"open": 17, "resolved": 1},
          o.get("family"))
    check("status names latest trace", bool(o.get("latest_trace")), o.get("latest_trace"))

    # ---- status on an UNHEALTHY store: ok false AND nonzero exit ----
    cases_path = root / "research/cases/cases.jsonl"
    cases_original = cases_path.read_bytes()
    cases_path.write_bytes(cases_original + b'{"id":"case.99","node_type":"case"}\n')
    r = store(root, "status")
    o = json.loads(r.stdout)
    check("unhealthy status ok false", o.get("ok") is False, r.stdout[:200])
    check("unhealthy status rc nonzero", r.returncode != 0, r.returncode)
    cases_path.write_bytes(cases_original)

if failures:
    print("GEN STORE TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("gen_store: all contract checks passed")
