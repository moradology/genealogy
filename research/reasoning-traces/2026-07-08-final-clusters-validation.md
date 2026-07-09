---
id: trace.2026-07-08.final-clusters-validation
title: "Final Clusters Validation"
date: 2026-07-08
status: resolved
confidence: strong
case_refs: ["case.04", "case.06", "case.17"]
person_refs: ["person.catherina_marie_koeberger", "person.claar.samuel_dove", "person.nauer.thomas", "person.rust.john_aissen", "person.rust.john_f"]
evidence_refs: ["ev.ancestry.1830-1841-rust-parish", "ev.ancestry.1861-nauer-marriage-negative", "ev.ancestry.1895-claar-marriage-search", "ev.ancestry.1900-rust", "ev.ancestry.1905-rust"]
source_refs: ["src.catherina-koeberger-nauer-find-a-grave.33248488", "src.john-aissen-rust-find-a-grave.23615b78", "src.lula-claar-thieler-obituary-page-oberlin-herald-nwkansas-pdf.7597fac2", "src.motherbedford-klar-claar-genealogy-page.ebad933d", "src.new-prussia-ontario-locality-context.912a8779", "src.samuel-dove-claar-familysearch.55d8177a", "src.thomas-a-nauer-wikitree.4b5b94d5"]
geo_refs: ["event.claar.samuel_mary_marriage_conflict.1895-10-05", "event.claar.swiss_origin.1700", "event.nauer.catherina_koeberger_death.1906-02-01", "event.nauer.thomas_catharine_waterloo_residence.1871", "event.rust.east_frisian_origin.1841", "target.nauer.st_clements_registers", "target.rust.john_f_ethel_rupert_reamsville_cluster"]
outcome: "The checked Hawkeye, Claar, Nauer, and Rust claims were graded and retained with source limits; the original Claar marriage, Ontario parish, and direct Rust parent link remain open."
next_action: "Pull the original Claar marriage, browse the Ontario Catholic collection by parish, and obtain direct proof connecting Mary Frances Rust to her parents."
---

# Final clusters: Hawkeye/Claar, Koeberger/Nauer, Rust (2026-07-08)

Closing validation for the last three frontier clusters (research/archive/program-board-2026-07-08.md 3.1, 3.20,
3.17, 3.18, 3.10). 8 verified, 1 unreachable-as-text, 3 flags. Method note
worth keeping: WikiTree quote-matching REQUIRES a real-Chrome render — the
reader proxy returns body prose only and silently misses the structured
vitals fields.

## Verified

1. **Hawkeye post office** 17 Nov 1879 - 30 Nov 1896, Cook Township
   (dccoks.org, verbatim).
2. **Both Hawkeye memoirs** in the KSHS bibliography with call numbers —
   Claar-Rezner "Settled by Pioneer Group from Iowa" and Lark Oren Claar
   (kansashistory.gov, verbatim).
3. **Mary Myrtle Claar b. 4 Jun 1880 "in Hawkeye, Decatur, Kansas"**, daughter
   of Henry Claar + Electra Alice White (WikiTree Claar-283, real-Chrome
   structured vitals) — the Claar-at-Hawkeye anchor.
4. **Balthasar Hans Clar 1647 - 26 Feb 1703, parents unidentified** (WikiTree
   Clar-6) — the honest documentary end of the direct Clar line holds.
   PLACE ATTRIBUTION SPLIT: Clar-6 places him in Canton Bern; "d. Mimbach"
   is the motherbedford compiled genealogy's claim only. Present both with
   their sources; never cite Mimbach to WikiTree.
5. **FamilySearch collection 1927566** "Canada, Ontario Roman Catholic Church
   Records, 1760-1923" exists, free, 126,534 images — case.04's next pull.
   CAVEAT: the collection does NOT enumerate parishes; St. Agatha /
   St. Clements coverage is UNCONFIRMED until checked via Browse waypoints.
6. **Waterloo Region Generations**: Koeberger 0 hits; "Coberger" exactly one —
   Katharina Christiane "Catherine" Coberger (b. 1833), spouse-linked to
   Thomas Nauer, no blood kin linked.
7. **F. John Rust's 1909 obituary** (memorial 53803179, real Chrome, full
   text): m. Etta Rupert 24 Oct 1893; "To this union three children were
   born, two boys and one girl"; Smith County resident since 1896. The
   3-vs-4-children tension with the memorial's four linked children is real;
   plausible reconciliation (Nina Frances d. before Oct 1909 or mis-linked)
   needs a census/mortality check — carry open at case.06.
8. **East Frisian Rust chain endpoints** (tote-punkte-ostfriesland.de,
   verified-index): Jan Aissen Rust *12.2.1842 Wybelsum, son of Aisse
   Janssen Rust (OSB Larrelt); Eise Janssen Rust *5.3.1754 +19.1.1826.
   Endpoints verified-index; the intermediate patronymic links remain
   COMPILED — grade the chain accordingly.

## Unreachable as text — and a grade-integrity flag

The 1991 Claar biography (motherbedford PDF) is a 160-page scanned-image
document: zero machine-extractable text, 59MB. The original wave's
[verified-primary] grade for its died-at-sea-years debunking list and the
York County Klee will was OVERSTATED — no automated fetch could have
quote-matched it. The Klee/Hanover/York marriage is independently
corroborated at compiled tier (frontierpatriots.com); the ship-years list
exists on no fetchable source. Treat both as "scanned image, not
machine-verified" pending OCR or a human read of the scan.

## Case absorptions queued (small index.html edits, next write window)

- case.17 body: the Hawkeye-Claar anchors (items 1-3) may promote; Balthasar
  place split-attributed; the scanned-PDF grade footnote.
- case.04 body: reword the next pull to "collection 1927566; St. Agatha /
  St. Clements coverage unconfirmed — verify via Browse waypoints."
- case.06 body: the 3-vs-4 children tension; East Frisian endpoints at
  verified-index, middle compiled.

With this trace, every TODO section-3 digest cluster is validated: the
frontier corpus's artifact-relevant claims have all been independently
re-fetched, landed, corrected, or registered as negatives.
