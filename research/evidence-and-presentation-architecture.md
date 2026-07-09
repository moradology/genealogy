# Architecture: an evidence layer under an assembly (presentation) layer

Status: PROPOSAL / north star for owner review. Reframes the multi-page migration plan:
that plan is about the *presentation* layer; this doc is about the layer beneath it.

## The idea

Two layers, cleanly separated:

1. **Evidence / discovery layer — the source of truth.** Every fact traces to a piece of
   evidence; every non-obvious conclusion traces to a *thread* of reasoning (how we got
   there, what we ruled out). This layer is written for rigor, not for reading.
2. **Presentation (assembly) layer — the viz.** Its only job is to assemble the best
   honest story from the evidence layer and **point back to citations elegantly**. It is
   written for a family member, not a genealogist.

The presentation layer never *originates* a fact; it only *arranges* facts that exist in
the evidence layer, and every claim it makes can be clicked back to its proof.

## This is ~70% built already — it's just implicit and scattered

| Layer piece | Where it lives today |
|---|---|
| Evidence records (the actual pulls) | `research/pulls/**` (images gitignored) + per-pull `notes.md` |
| Source catalogue | `research/sources/source-index.json` (auto-extracted from the page's Source Ledger) |
| Structured event data + confidence + source_refs | `ancestry_geospatial.geojson` |
| Discovery threads (the reasoning) | `research/reasoning-traces/*.md` |
| Open threads / questions | the Docket (cases, negative register, corrigenda) in the page |
| Citations pointing back | superscripts → Source Ledger (with backlinks); the new **record cards** |

The gap isn't missing pieces — it's that the evidence pieces aren't a single addressable
store, and the presentation layer is hand-authored *beside* them rather than *citing* them
under a contract.

## The concrete shape (kept YAGNI — no ontology, no graph engine)

**Evidence records** — promote each pulled record from an ad-hoc `notes.md` to a small
structured entry (extend `source-index.json`, or one `evidence.json`). Fields:
`id`, `type` (census/marriage/divorce/death/obituary/grave/land), `title`,
`repository` (e.g. "NARA T627; via Ancestry — image local, ToS"), `citation` (the exact
archival string), `accessed`, `image` (path under `research/pulls/`, gitignored),
`transcription` (the fields, e.g. a household list), `confidence`, and `supports` (the
claim/person/case ids it backs). The **record cards** already render exactly this shape —
they are the evidence record made visible.

**Discovery threads** — keep the `reasoning-traces/*.md` as prose (this is a narrative
proof argument, not data). Add light front-matter: `case`, `people`, `evidence`,
`outcome`. The Docket case for a question links to its thread; the thread links to the
evidence records it weighs. This *is* the "thread of discovery," first-class.

**Claims (optional, only if it earns its keep)** — a fact a person card asserts. Minimal:
`id`, `statement`, `evidence: [...]`, `confidence`. Don't build this unless the gate below
needs it; the person card + its citations may be claim enough.

**The presentation layer** stays hand-authored (you do the frontend) but under a
**contract the gate enforces**: every "Documented/Strong" claim on a page cites at least
one evidence record; every cited record exists and carries a repository citation; every
citation link resolves; images referenced are present locally even though gitignored.
This is `check_refs` grown up — it already checks that `source_refs` URLs live in the
ledger; extend it to check that page claims resolve to evidence records.

## Pointing back "in an elegant fashion"

Three levels of pointing-back, cheapest first — all things the artifact already gestures at:
1. **Superscript → Source Ledger** (exists). Keep for external, linkable sources.
2. **Inline record card** (exists, new) — the evidence rendered where the claim is made.
   For Ancestry/ToS records this is the honest substitute for the image.
3. **Evidence view** (new, optional) — a per-record anchor (`#ev.1940-census-adolph`) that
   any claim can deep-link to, showing the transcription, the archival citation, the
   discovery thread it belongs to, and the local image when present. This is the elegant
   "click any fact, see its proof and how we found it."

## How this relates to the page split

Orthogonal but complementary. Build the **evidence layer first** — it's the backbone, and
it makes the presentation layer (single file *or* landing + four pages) a thin assembly on
top. If the evidence store is the source of truth, splitting the viz into pages is just
re-arranging the assembly; cross-page `check_refs` resolves against one evidence store, not
five copies. So: evidence layer → then presentation, in whatever page shape you choose.

## Suggested first step (small, reversible, high-signal)

Formalize **one cluster** end-to-end as the pattern: take the Mundell/Clemans work just
completed and turn its pulls into structured evidence records, link them from the Docket
cases and the person cards, and extend `check_refs` to enforce "these claims cite these
records." One vertical slice proves the contract; the rest is repetition.

## Decisions needed from you

1. Evidence store as an **extension of `source-index.json`**, or a **new `evidence.json`**
   (keeps sources vs. evidence-with-transcriptions separate)?
2. Do we add a lightweight **claims** layer, or treat the person card + its citations as
   the claim (simpler, YAGNI)?
3. Build the **`#ev.*` evidence view / deep-link** (level 3 pointing-back), or stop at
   inline record cards (level 2) for now?
4. Sequence: evidence layer **before** the page split (recommended), or interleave?
