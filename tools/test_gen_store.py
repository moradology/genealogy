#!/usr/bin/env python3
"""Acceptance test for tools/gen_store.py (cockpit write-side + orientation verbs).

Offline, stdlib only, no pytest, no try/except. Runs the CLI as a subprocess
against a FIXTURE COPY of the repo (GEN_STORE_ROOT override) so the real truth
stores are never written by tests. Run: uv run tools/test_gen_store.py
"""

from __future__ import annotations

import json
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
