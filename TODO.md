# Current Work — Zimmerman–Dible Genealogy

Last updated: 2026-07-09.

The completed 2026-07-08 program board and its validated-findings digest are
archived at `research/archive/program-board-2026-07-08.md`. Do not use that
archive as a current task list.

## Working contract

- Git-tracked JSONL and Markdown are the research truth.
- `research/sources/sources.jsonl` is the canonical source registry.
- `research/evidence/*.jsonl` contains privacy-reviewed pulled-record metadata.
- `research/cases/cases.jsonl` is the append-only Docket.
- `index.html`, `source-index.json`, and the derived graph database are projections.
- Raw subscription images stay local under ignored `research/pulls/` paths.
- No living people or sensitive personal identifiers enter tracked/public content.
- Run `sh tools/check.sh` before landing a change.

## Completed in the 2026-07-09 integrity and research pass

- [x] Finish the evidence hard cutover: migrate all 23 logical subscription pulls,
  validate their references, and link landed findings to stable `ev.*` ids.
- [x] Normalize every reasoning trace to the current front-matter contract.
- [x] Reconcile the Rust/Adolph resolved identity across the GeoJSON, traces, and
  residual-person registry while leaving the still-open Strawn step explicit.
- [x] Complete one evidence-reviewed advancement or durable negative for each
  branch research lane:
  - Zimmerman: the 1851 Nauer/Wand household is documented; Thomas's parentage stays open.
  - Mundell: James-to-John is named in the 1837 probate index; Harvey-to-John stays open.
  - Dible: Catherine Moore is documented about 1839; death, burial, and parents stay open.
  - Connelly: the 1895 marriage is fixed at Oberlin; the bride's spelling stays open.
- [x] Make the Source Ledger and case presentation fully checked projections of
  their canonical JSONL records.

## Owner decision required

- [ ] The sensitive identifier has been removed from the current tree, but it
  remains in published Git history. Rewriting and force-pushing history requires
  explicit approval because it will disrupt existing clones.

## Later

- [ ] Split the reader into focused pages only after the evidence contract is
  complete and the graph/cockpit tools consume the same JSONL truth.
- [ ] Optional family-paper scans: the 1911 Ford letter, wedding materials, and
  photographs named in the public “Wanted” section.

## Done when

- Every retained pull has tracked, sanitized metadata.
- Every open pedigree slot points to a non-closed case.
- No case, trace, GeoJSON target, or search frame contradicts a settled verdict.
- The full gate passes, including privacy, evidence, case, and browser checks.
