# The Reasoning Layer: adjudicate, frontier, contradictions

Status: PROPOSAL for owner review. The "encoded opinions" program — turning the
judgment applied by hand this week (the four-Marjorie eliminations, the offline-records
ranking, the weakest-step honesty) into rules any agent session runs through the cockpit.

Substrate already in place: the family core (117 people, 155 typed links with
per-link confidence and evidence refs, 18 gap nodes), cases/evidence/trace stores,
`gen ancestors`/`gen path` BFS walks, and the geojson life events (the only dated
records — people.jsonl deliberately carries no dates). Everything below is stdlib,
functions-only, no try/except, tests-first, per-phase gate-green commits. Codex builds
new files against my authored contract tests; I hand-wire hot files.

---

## Phase 0 — Vitals resolver + honest coverage report

The chronology rules need birth/death/marriage YEARS. Those live only in
`ancestry_geospatial.geojson` life events (person_id + date fields), covering a
fraction of the 117 people. Build the join once, and be honest about its reach.

- New `tools/family_rules.py`: `vitals(root) -> {person_id: {birth_year?, death_year?,
  marriage_years[], provenance: [event ids]}}` joining the family core to geojson
  events; tolerant of year-only dates; UNKNOWN stays unknown (rules must skip, never
  guess).
- `gen vitals-coverage` (or fold into `gen status`): how many people have dated
  births/deaths; which direct-line people are undated (those are themselves research
  leads — a Phase 3 input).
- Contract test with synthetic fixtures; wire nothing into the gate yet.
- Exit criterion: coverage numbers eyeballed by owner; rules' blind spots documented.

## Phase 1 — Contradiction engine: `gen contradictions`

Store-wide constraint sweep over EXISTING data. Independent rule functions, each
returning findings `{rule, severity, persons, links, evidence, detail}`:

- parent 12–55 at child's birth (both dated); mother not dead before birth; father
  not dead >9 months before birth
- death after birth; marriage at ≥14; child born after parent's marriage-age floor
- generation-gap sanity along `ancestors` chains
- cross-store: relationship confidence "documented/strong" with zero evidence_refs
  (a claim stronger than its support); closed cases still cited by open gaps

Adoption is two-stage ON PURPOSE: report-only first (JSON list, `clean: bool`,
exit 0 even when findings exist), because legacy data may legitimately trip rules;
after the store is swept clean, promote to a gate line (`--strict` exits 1 on
findings). Mutation tests: a 10-year-old parent, a posthumous mother, an undated
person (must be skipped silently).

## Phase 2 — Candidate adjudication: `gen adjudicate`

The four-Marjorie logic as a verb. Input: one candidate JSON on stdin — a proposed
identity or relationship (`{"claim": "same_person"|"parent_of", "target":
"person.x", "candidate": {names[], birth_year?, death_year?, places[], spouse?,
discriminators{}}}`). Output: `{verdict: reject|weak|plausible|strong, reasons[],
mismatches[], missing: [what linking evidence would settle it]}`.

Rules, in order:
1. **Chronology feasibility** vs Phase-0 vitals (hard reject on impossibility —
   this alone would have killed the Barron-County Marjorie instantly).
2. **Name compatibility**: stdlib-only variant matching (normalized comparison,
   initial/diminutive tables seeded from this family's observed variants —
   Zodrow/Farrow, Mundell/Mandell/Mondel, Clemans/Clemens/Clemons/Clements —
   plus plain edit distance). Middle-name/initial conflicts are independent
   mismatches.
3. **Geo-temporal plausibility**: candidate places vs the person's geojson event
   places (county/state-level, era-aware; no distance math — YAGNI).
4. **Two-independent-mismatches ⇒ reject** (the codified house rule).
5. **Negative memory**: consult evidence `opposes` edges and trace outcomes that
   already touch the target — a previously refuted candidate is rejected with a
   pointer to the prior refutation, never re-litigated silently.
6. Verdict `strong` is CAPPED at `plausible` unless a linking document is cited:
   the verb can encourage, but only evidence promotes.

OWNER DECISION NEEDED: where rejected candidates live canonically. Options:
(a) evidence records with `opposes` (exists today; the four Marjories are already
recorded this way) — my recommendation, zero schema change; (b) a `rejected_persons`
field on gap nodes (family-core schema change, owner's store); (c) a new
rejections.jsonl (more machinery than the data warrants — YAGNI).

## Phase 3 — Frontier ranking: `gen frontier`

The offline-records ranking generalized. Score every open lead — the 18 gap nodes,
sub-strong links on direct-line `path` chains, undated direct-line people from
Phase 0, and open/needs_pull cases — on:

- **Tractability**: known anchors (dated subject? known spouse? known county?) ×
  record availability (a small static coverage table: census decades, SSDI range,
  state vital-index spans, the Ancestry collection ids already in the pilot prompt).
  Offline-only paths (parish registers, county packets) rank separately, never
  interleaved with online-chaseable items.
- **Value**: direct-line pedigree position beats collateral; closes a case > feeds
  a gap > corroborates; weakest-link upgrades on the four anchor chains weighted
  highest (computed from `path` confidences, not asserted).
- **Cost/negative memory**: expected live hits; penalty when a trace already
  registered a negative for the same record class (don't re-run dead searches).

Output: ranked JSON with per-item WHY + the exact suggested next record (collection,
name, year) — directly consumable by the pilot-agent prompt, replacing its manual
topic-picking rubric with `./gen frontier` + human approval.

## Phase 4 — Integration and adoption

- Pilot prompt updated: topic selection starts from `gen frontier`; identity claims
  run `gen adjudicate` BEFORE `evidence add` of identity-asserting records.
- `gen status` gains `contradictions` and `frontier_top` summary fields.
- Gate: promote `gen contradictions --strict` once Phase 1's sweep is clean.
- Decide (owner): does `case update --status closed` require a clean adjudication/
  contradiction pass for the case's people? (Recommendation: yes, cheap and safe.)
- Docs: researcher-cockpit.md built-list; a reasoning-traces entry documenting the
  first real frontier run and whether its ranking matches researcher intuition —
  the acceptance test for the whole layer is "does `frontier` independently
  reproduce the Marjorie offline-records ordering and the case.06 pick?"

## Phase 5 (deferred, explicit triggers) — CozoDB + recall

Not built until a trigger fires: (a) rules need recursive joins the BFS walks make
awkward, (b) the store grows past ~500 people, or (c) trace-corpus search by grep
demonstrably misses recalls. Then: CozoDB as the derived Datalog index generated
from the text stores (never authored, never shipped), Phase 1–3 rules mirrored as
Datalog for ergonomics comparison, and `gen recall` via its vector search over
trace/evidence text with a local embedding step. Text stays truth throughout.

---

## Sequencing and effort

0 → 1 → 2 → 3 are strictly ordered (each consumes the previous); 4 rides alongside;
5 waits for its triggers. Phases 0+1 are one Codex-buildable chunk against my tests;
Phase 2 is the subtlest (name matching + verdict calculus — I'd build the rule core
by hand and let Codex scaffold the fixtures); Phase 3 is mostly scoring plumbing.
Each phase lands as one gate-green commit with contract tests in check.sh.

The acceptance bar for the program, stated once: **an agent session that has never
seen this repo should be able to run `gen frontier`, pick its top item, adjudicate
its candidates, and be blocked from landing anything the house rules would have
rejected by hand.**
