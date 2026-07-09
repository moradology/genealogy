# Migration plan: one file → landing + four focused pages

Status: PROPOSAL for owner approval. Nothing here is executed yet. The current
`index.html` remains the single source of truth until this is approved and done.

## Goal

Split the single `index.html` into **five pages**:
- `index.html` — landing / front door
- `zimmerman.html` — Doyle Julius Zimmerman's ancestry (Zimmerman / Zodrow / Nauer / Fleckenstein)
- `mundell.html` — Evelyn Delores Mundell's ancestry (Mundell / Rust / Cantwell / Clemans)
- `dible.html` — William J. "Bill" Dible's ancestry (Dible / Long / Sleight / McClelland)
- `connelly.html` — Donna Lea Connelly's ancestry (Connelly / Durham / Claar / White)

Motivation is **focus and page length**, not size — images already cost the byte
budget nothing, and the HTML has headroom. Each branch page becomes short enough to
read top-to-bottom; the landing page becomes a true front door.

Alternative considered: **two "couple" pages** (Doyle+Evelyn on one, Bill+Donna on the
other) + landing = 3 pages. That keeps each married couple together and shares the
convergence map more naturally, but the four-page split gives each grandparent line its
own clean home. Recommendation: four pages as you proposed, unless you want the couples
kept together.

## What lives where

| Section | Destination |
|---|---|
| Hero, "How to read this", start-here ramp | Landing |
| Story cards | Landing (each links into its branch page) |
| Convergence map (Plate I, Kansas window) | Landing |
| The four anchor cards + jump links to branch pages | Landing |
| 2076 letter, colophon, WANTED / mailto | Landing |
| Each branch's generations + person cards + record cards | Its branch page |
| Each branch's line plate (III–VI) + marker key | Its branch page |
| Each branch's pedigree chart | Its branch page |
| Docket cases | Split by branch onto branch pages; a combined docket stays on Landing OR a `docket.html` |
| Source Ledger | Split by branch group onto branch pages; shared/cross-branch sources on Landing |
| Index of Names | Landing (or a `people.html`); links resolve cross-page |
| Pedigree "Table of Removes" | Landing |

Open question for you: do the **Docket** and **Index of Names** stay as combined pages
(one docket, one index, linking across branches), or get split per branch? Combined is
better for cross-branch discovery; split is shorter per page. Recommendation: keep a
combined Docket and Index on the landing page (they are the cross-cutting spine).

## Shared assets — the central decision

Today everything (CSS, ~42 KB of embedded fonts, the map/interaction JS) is inlined in
one file. Across five pages that inline block would be duplicated 5×. Two options:

- **A. Shared linked assets (recommended).** Extract into `assets/app.css`,
  `assets/fonts.css` (the woff2 data-URIs), and `assets/app.js`, linked by every page
  with relative paths. Same-origin requests only — still zero *external* requests, still
  works offline over `file://` as a folder. Downside: a page is no longer a single file
  you can email by itself.
- **B. Fully inline every page.** Each page self-contained (email-able alone), fonts
  duplicated 5× (~210 KB total). Simpler mental model, larger repo, and edits to shared
  CSS must be applied five times (or via a build step).

Recommendation: **A**, plus a **keepsake build** (below) that regenerates a single
inlined file for print/archival. That keeps day-to-day maintainability and preserves the
"one file, no server, no network" promise as an export rather than the working format.

## Preserving the archival promise

The colophon's whole ethos is "this whole record is one file… keep the file itself."
To keep that guarantee under a multi-page structure, add `tools/build_keepsake.py`: it
inlines all shared assets and concatenates the five pages into one `keepsake.html`
(print-styled, all anchors rewritten to in-document). The colophon changes from "this is
one file" to "the keepsake edition is one file; the working site is a small folder."

## Navigation

A shared masthead nav on every page: `Home · Zimmerman · Mundell · Dible · Connelly`,
plus the existing within-page jump links. The current jump nav (`ANCHORS · MAP · …`)
becomes per-page section jumps.

## Tooling / gate rework (the real cost)

The gate is the artifact's backbone and assumes one file. Changes:

1. **Byte budget (S9/S10/S11):** per-page HTML ceiling; shared fonts counted once
   against a shared-asset budget, not per page.
2. **Page height (L2):** measured per page (each is shorter, so this gets *easier*).
3. **check_refs:** today it resolves person/case/source refs within one file. It must
   become **cross-file**: build the union of all ids across the five pages + the geojson,
   then resolve `page.html#anchor` links across files. This is the biggest tooling change.
4. **check_geo_sync:** the geojson stays one data file; each branch page carries its own
   `verifiedEventData` subset; sync-check runs per page against the shared geojson.
5. **check_people_index:** the people-index JSON either becomes shared (one file, linked)
   or is split per page; the index of names must link cross-page.
6. **build_plate_keys / build_citation_backlinks / stamp:** run per page.
7. **Source ledger checks (C2/C3/C4):** per-page ledger counts; cross-page citation
   superscripts must resolve to whichever page hosts the source.
8. **acceptance_spec.js:** parameterize by page; run the Playwright suite against each of
   the five pages (themes, responsive, plate rendering, interactions).
9. **CI + check.sh:** loop the whole gate over five pages + validate the keepsake build.

## Cross-page integrity — the new failure mode

Person cards link to spouses/parents/descent stems that may live on another branch page
(e.g., a stem from Evelyn references the Mundell line; the convergence links cross
branches). Every such link becomes `otherpage.html#anchor`. check_refs must verify these
resolve, and a broken cross-page link is a new class of gate failure to guard against.

## Suggested order of work

1. Extract shared assets (A) behind the current single page; confirm the one page still
   passes the full gate unchanged. (Reversible checkpoint.)
2. Add `tools/build_keepsake.py` and a `keepsake.html` gate check.
3. Stand up the five-page skeleton with shared nav and empty branch pages.
4. Move one branch (say Zimmerman) to its page end-to-end; make `check_refs` cross-file;
   get that page green. This is the proof-of-concept; the hard tooling is done here.
5. Move the remaining three branches.
6. Split/relocate Docket, Source Ledger, Index of Names; fix cross-page citations.
7. Rework `check.sh` / CI to run the whole suite across pages + keepsake.
8. Screenshot matrix (light/dark × 320/768/1440) for all five pages + keepsake print.

## Honest tradeoffs

- **Gain:** shorter, focused, faster pages; a real landing page; room per branch; a
  cleaner mental model for readers and for adding evidence.
- **Cost:** substantial one-time tooling rework (cross-file check_refs is the crux); a
  new cross-page-link failure mode; the working artifact is a folder, not a file
  (mitigated by the keepsake export); five pages to keep visually in sync.
- **Not a reason to do it:** size/images — those are free today.

## Decisions needed from you before executing

1. Four branch pages (as proposed) or two couple pages (Doyle+Evelyn, Bill+Donna)?
2. Shared linked assets (A) or fully-inline pages (B)?
3. Combined Docket + Index on the landing page, or split per branch?
4. Keepsake single-file export — yes (recommended) or not needed?
