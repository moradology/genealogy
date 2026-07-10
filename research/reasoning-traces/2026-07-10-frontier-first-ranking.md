---
id: trace.2026-07-10.frontier-first-ranking
title: "First frontier ranking of the open research edge"
date: 2026-07-10
status: active
confidence: documented
case_refs: ["case.07"]
person_refs: ["person.clemans.marjorie"]
evidence_refs: ["ev.ancestry.marjorie-census-sweep-negative", "ev.ancestry.marjorie-vital-index-sweep-negative"]
source_refs: []
geo_refs: []
outcome: "The integer rubric's first ranking reproduces the manual ordering: dated county-anchored parentage gaps lead online, and the exhausted Marjorie search moves to the offline records-to-order channel."
next_action: "Owner sanity-checks the ranking against researcher intuition; --strict promotion decision still pending."
---
# First frontier ranking, for owner sanity-check (2026-07-10)

`./gen frontier` (reasoning layer phase 3) produced its first ranking of the
open research edge. The rubric is deterministic integers: value from pedigree
depth, item kind, and open-case bonuses; tractability from dated subjects,
accepted spouses, known places, and the static record-coverage table; penalty
from recorded negative searches. Offline-only leads are channelled separately
and never interleaved.

## Online top ten

1. 62 - gap.zimmerman.john_paul.parents (parentage)
2. 62 - gap.durham.david.parents (parentage)
3. 56 - gap.zodrow.frontier (frontier)
4. 54 - relationship.parent.elmore_deborah-to-mundell_harvey (weak link)
5. 54 - relationship.parent.james_hannah_ann-to-lovina_parker_love (weak link)
6. 54 - relationship.parent.love_thomas-to-lovina_parker_love (weak link)
7. 54 - relationship.parent.mcclelland_alexander-to-mcclelland_dorsey (weak link)
8. 54 - relationship.parent.mundell_harvey-to-mundell_john_pryor (weak link)
9. 54 - relationship.parent.mundell_john-to-mundell_harvey (weak link)
10. 54 - relationship.parent.sarah_hoge-to-mcclelland_dorsey (weak link)

Dated, county-anchored parentage gaps with sole open cases lead; the band of
lead-confidence direct links follows. This matches the weakest-step-first
instinct the rubric was built to encode.

## Offline channel

- 52 - gap.clemans.marjorie.parents -> Colorado county vital records and
  court case files
- 16 - person.clemans.marjorie (undated) -> the same county records

The engine reproduces the manual conclusion of the July 8 session: the
target's online coverage is exhausted, so her parentage moves to the
records-to-order channel. This became true only after the session's negative
census and vital-index sweeps were recorded as structured search_log
evidence (ev.ancestry.marjorie-census-sweep-negative and
ev.ancestry.marjorie-vital-index-sweep-negative) - with only prose memory of
those sweeps, frontier had ranked her as the top online target. Negative
results recorded as evidence are load-bearing.

## Method note

Acceptance for the phase: the ranking reproduces the Marjorie offline/online
ordering and places dated, county-anchored leads above deeper undated
material, both satisfied above. The trace-negative penalty from the original
plan was folded into the search_log evidence penalty to avoid counting one
negative twice.
