#!/usr/bin/env python3
"""Offline parse tests for tools/gen_ancestry.py — no browser, no playwright.

Imports the pure parsing functions (playwright is only imported lazily inside
the browser path, so this runs on plain stdlib). Run: uv run tools/test_gen_ancestry.py
No try/except: a bad parse asserts loudly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_ancestry as ga  # noqa: E402

failures: list[str] = []


def check(name: str, cond: bool, detail: object = "") -> None:
    if not cond:
        failures.append(f"{name}: {detail}")


# Real Ancestry record innerText: detail fields are Label\tValue, and household
# rows come BOTH tab-joined and interleaved with blank lines (the messy shape).
FIXTURE = (
    "View\nHomer Mandell\n1940 United States Federal Census \n"
    "Detail \nHow to evaluate details\n"
    "Name\tHomer Mandell\n[Homer Mundell]\n"
    "Age\t29\nEstimated Birth Year\tabt 1911\nBirthplace\tKansas\n"
    "Marital Status\tMarried\nHome in 1940\tColby, Thomas, Kansas\n"
    "Occupation\tMechanic\nNeighbors\tView others on page\n"
    "Household Members (Name)\tAge\tRelationship\n"
    "Lon A Adolph\n\t\n58\n\t\nHead\n"            # interleaved shape
    "Frances Adolph\t45\tWife\n"                   # tab-joined shape
    "Derane Adolph\n\t\n10\n\t\nSon\n"             # interleaved shape
    "Save this record?\nSource\nSource Citation\n"
)

fields = ga.parse_detail_fields(FIXTURE)
check("field Name", fields.get("Name") == "Homer Mandell", fields.get("Name"))
check("field Occupation", fields.get("Occupation") == "Mechanic", fields.get("Occupation"))
check("field Home", fields.get("Home in 1940") == "Colby, Thomas, Kansas", fields.get("Home in 1940"))
check("fields stop before household", "Lon A Adolph" not in " ".join(fields.values()), fields)

hh = ga.parse_household(FIXTURE)
triples = [(m["name"], m["age"], m["relation"]) for m in hh]
check("household head (interleaved)", ("Lon A Adolph", "58", "Head") in triples, triples)
check("household wife (tab-joined)", ("Frances Adolph", "45", "Wife") in triples, triples)
check("household son (interleaved)", ("Derane Adolph", "10", "Son") in triples, triples)
check("household count == 3", len(hh) == 3, triples)

# cdp_up returns a bool without raising when nothing is listening on some port
check("cdp_up returns bool", isinstance(ga.cdp_up(), bool))

# ---- address grammar (relative-navigation layer) ----
rec = ga.parse_address("record/2442/58087568")
check("addr record", rec == {"type": "record", "collection": "2442", "id": "58087568"}, rec)
srch = ga.parse_address("search/6224?name=Marjorie_Clemans&birth=1912")
check("addr search", srch == {"type": "search", "collection": "6224", "name": "Marjorie_Clemans", "birth": "1912"}, srch)
srch_nb = ga.parse_address("search/6224?name=Only_Name")
check("addr search no birth", srch_nb is not None and srch_nb["birth"] == "", srch_nb)
coll = ga.parse_address("collection/6224")
check("addr collection", coll == {"type": "collection", "collection": "6224"}, coll)
check("addr garbage rejected", ga.parse_address("frob/nicate/x/y") is None)

check("url record", ga.url_for(rec) == "https://www.ancestry.com/search/collections/2442/records/58087568", ga.url_for(rec))
check("url search", ga.url_for(srch) == "https://www.ancestry.com/search/collections/6224/?name=Marjorie_Clemans&birth=1912", ga.url_for(srch))

check("location_key record stable", ga.location_key(rec) == ga.cache_key("record", {"collection": "2442", "id": "58087568"}))
check("location_key collection none", ga.location_key(coll) is None)

# ---- cache verbs against a throwaway GEN_COCKPIT_DIR (subprocess; offline) ----
import json
import os
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix="gen-cache-test-") as tmp:
    env = {**os.environ, "GEN_ANCESTRY_CACHE_DIR": tmp, "GEN_COCKPIT_DIR": tmp + "/state"}

    def cache_cmd(*args):
        return subprocess.run(
            [sys.executable, "tools/gen_ancestry.py", "cache", *args],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, env=env)

    r = cache_cmd("stats")
    o = json.loads(r.stdout)
    check("cache stats empty", o["ok"] is True and o["entries"] == 0, r.stdout[:200])

    # seed one enveloped entry and one legacy (pre-envelope) entry
    cdir = Path(tmp)
    (cdir / "record-aaaa.json").write_text(json.dumps(
        {"meta": {"kind": "record", "collection": "2442", "id": "1", "fetched_at": "2026-07-09T12:00:00"},
         "data": {"ok": True}}))
    (cdir / "search-bbbb.json").write_text(json.dumps({"ok": True, "results": []}))  # legacy shape

    o = json.loads(cache_cmd("stats").stdout)
    check("cache stats counts", o["entries"] == 2 and o["by_kind"] == {"record": 1, "search": 1}, o)
    check("cache stats newest", o["newest"] == "2026-07-09T12:00:00", o)

    o = json.loads(cache_cmd("list", "--kind", "record").stdout)
    check("cache list filtered", o["count"] == 1 and o["entries"][0]["kind"] == "record", o)

    r = cache_cmd("clear")
    check("cache clear refuses bare", r.returncode != 0 and json.loads(r.stdout)["ok"] is False, r.stdout[:200])
    o = json.loads(cache_cmd("clear", "--kind", "search").stdout)
    check("cache clear by kind", o["removed"] == 1, o)
    o = json.loads(cache_cmd("clear", "--all").stdout)
    check("cache clear all", o["removed"] == 1, o)
    o = json.loads(cache_cmd("stats").stdout)
    check("cache empty after clear", o["entries"] == 0, o)

# ---- per-agent state round-trip (uses the real state dir; unique agent name) ----
AGENT = "test-agent-selfcheck"
state = ga.new_agent_state()
state["location"] = rec
state["history"] = [srch]
state["cursor"] = 2
ga.save_agent(AGENT, state)
back = ga.load_agent(AGENT)
check("agent state round-trip", back == state, back)
(ga.AGENTS_DIR / f"{AGENT}.json").unlink()

if failures:
    print("GEN ANCESTRY PARSE TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("gen_ancestry parse: all checks passed")
