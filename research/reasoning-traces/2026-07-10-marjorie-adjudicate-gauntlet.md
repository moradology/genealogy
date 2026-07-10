---
id: trace.2026-07-10.marjorie-adjudicate-gauntlet
title: "The adjudicate gauntlet: four Marjorie candidates re-tried by machine"
date: 2026-07-10
status: active
confidence: documented
case_refs: ["case.07"]
person_refs: ["person.clemans.marjorie"]
evidence_refs: ["ev.ancestry.1910-clemans-barron", "ev.ancestry.1933-mundell-clemans-marriage", "ev.ancestry.marjorie-clemans-candidates"]
source_refs: []
geo_refs: ["target.clemans.barron_same_name_collision", "target.clemans.kit_carson_same_name_collision", "target.clemans.marjorie_opal_same_name_collision", "target.clemans.waynoka_same_name_collision"]
outcome: "All four historical same-name candidates reject deterministically, three by live axes and all four by recorded exclusion tombstones; a control candidate matching the target profile stays open."
next_action: "Owner eyeballs the gauntlet and the first contradictions sweep, then decides on promoting contradictions --strict into the gate."
---
# The adjudicate gauntlet: four historical Marjorie candidates re-tried by machine (2026-07-10)

`./gen adjudicate` (reasoning layer phase 2, commit b1198d2) re-adjudicated the four
same-name Marjorie Clemans candidates that were eliminated by hand during the case.07
research. The engine judges claims from tracked structure only: vitals from dated
geojson life events (marriage events now credit both participants, giving the target
her documented 1933 marriage year), name variants through the NAME_EQUIVALENCE
classes, accepted spouse links, geo token overlap, and four negative-memory sources.

## Verdicts

1. **Barron County WI daughter (b~1922)** — REJECT, refuted by
   `target.clemans.barron_same_name_collision`. Without the tombstone the engine
   independently rejects on chronology: a b~1922 candidate would be 11 at the
   documented 19 June 1933 marriage, below the 14-year floor.
2. **Liberty Mills IN, Marjorie Opal (b 1914, m. Stamper)** — REJECT, refuted by the
   pre-existing `target.clemans.marjorie_opal_same_name_collision`. Live axes agree:
   middle Opal vs recorded Evelyn, spouse Stamper vs documented Homer Mundell, and
   Indiana geography are three independent mismatches.
3. **Kit Carson County CO, Marjorie E. (b~1918)** — REJECT, refuted by the new
   `target.clemans.kit_carson_same_name_collision`. This is the one candidate the
   live axes alone cannot kill: her middle initial E is compatible with Evelyn and
   Colorado geography overlaps, and the decisive fact (bride age 21 in 1933, so the
   target was born about 1912, six years earlier) lives in the marriage record's
   prose, not in structured vitals. The recorded tombstone is what carries the
   exclusion deterministically.
4. **Waynoka OK, Marjorie Emily (b 1915, m. Weaver)** — REJECT, refuted by
   `target.clemans.waynoka_same_name_collision`. Live axes agree: middle Emily,
   spouse Weaver, Oklahoma geography — three independent mismatches.

## Control

A hypothetical candidate matching the target's actual profile — Marjorie Clemans,
born about 1912, Kansas — returns WEAK with zero refutations: the tombstones do not
swallow genuinely new candidates (the county-precise features require birth-year
equality plus at least two place-token overlaps to refute). The correct next move
for such a record remains evidence pull plus owner review, exactly as before.

## Method note

Severity discipline holds end to end: hypotheses stay advisable, only accepted
impossibilities gate, and a rejection here never re-litigates — the envelope points
at the recorded exclusion so an agent can read why in one hop.
