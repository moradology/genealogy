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

if failures:
    print("GEN ANCESTRY PARSE TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("gen_ancestry parse: all checks passed")
