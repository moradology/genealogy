# Architecture: an evidence layer under an assembly (presentation) layer

Status: FOUNDATION IMPLEMENTED 2026-07-09. The evidence, case, source, and trace
contracts described here are live. The graph database is a derived CozoDB reasoning
index, never an authoring source; see `embedded-graph-db-options.md`.

## The source-of-truth story (decisive)

**The source of truth is git-tracked plain text. Not SQLite, not any database.** Here is the
whole reasoning, because it's the capstone decision everything else hangs on.

Pick the store by the properties that define *this* project, and three dominate:
- **Diffability = the reasoning history.** In genealogy the *argument* matters as much as the
  fact. `git diff` + commit messages already are that log: "changed Cecilia's parents to
  Leonard Zodrow because the 1910 census, here's the trace." A binary DB throws that away —
  you can't see in a PR what fact changed or why. This alone is close to decisive.
- **Hand-editability.** The owner authors the data directly (cards, geojson, notes). Text
  supports that with any editor; a DB needs SQL or a bespoke UI, changing the whole workflow.
- **Archival durability.** Plain text is readable in thirty years with `cat`; every DB format
  eventually needs a migration. This record must outlive its tools.

SQLite-as-truth would buy enforced constraints, transactions, and SQL queries. But note **we
don't lose integrity by choosing text** — we move it from *storage-engine enforcement* to a
*validation step*: the gate (`check_refs`, `check_people_index`, `check_geo_sync`, extended to
the evidence graph) plays the role foreign keys would, in pre-commit/CI. You *can* commit a
broken state; the gate stops it from shipping. That's "constraints as a check" instead of
"constraints as an engine" — the right trade when diffable, hand-editable text is the goal.

So: **text is truth; the gate is its integrity; CozoDB is a derived reasoning index; the
viz is a derived projection; binaries are files referenced by path.** Nothing authoritative
is binary.

**Format of the truth** (text, but which text):
- **Research data → JSONL** (one case, source, or evidence record per line). Line-delimited records give
  *clean line-level git diffs*, are appendable and greppable, and dodge JSON's noisy
  whitespace/reordering diffs. Current truth lives in `cases.jsonl`, `sources.jsonl`,
  and branch-sharded `evidence/*.jsonl`; graph nodes and edges are derived from them.
- **Discovery threads → Markdown + front-matter** (prose reasoning; the `reasoning-traces/`
  already are this).
- **Geo → keep `ancestry_geospatial.geojson`** (already the geo truth; it's line-editable text).
- **Binaries → filesystem**, referenced by `path`.

**Current cutover.** Cases, evidence, and sources now have canonical Git-tracked stores.
`index.html` is checked against the case and source registries, visible record cards name
canonical `ev.*` records, and `source-index.json` is generated from `sources.jsonl`.
Reasoning traces use one strict frontmatter contract. Person prose remains hand-authored,
but every Documented or Strong row must cite the Source Ledger.

**The one honest exception.** If this were multi-user, write-heavy, and integrity-critical
operationally, storage-engine-enforced constraints + transactions would outweigh diffability,
and SQLite-*as-truth* (with a Dolt-style diff export) would be worth it. This project is
single-author, low-write, and archival — so text wins clearly. Revisit only if that changes.

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

## Implemented addresses

| Layer piece | Where it lives today |
|---|---|
| Evidence records | `research/evidence/*.jsonl`; private images remain under ignored `research/pulls/**` |
| Source catalogue | `research/sources/sources.jsonl`; `source-index.json` is generated |
| Structured event data + confidence + source_refs | `ancestry_geospatial.geojson` |
| Discovery threads | strict `research/reasoning-traces/*.md` frontmatter plus prose |
| Open threads / questions | `research/cases/cases.jsonl`, checked against the public Docket |
| Citations pointing back | superscripts → Source Ledger; record cards → canonical evidence ids |

Every piece now has a stable address and a checked relationship to the others. The graph
loader consumes those addresses; it does not introduce a second record format.

## The concrete shape

**Evidence records** live in branch-sharded JSONL. Each record carries a stable id, record
type, exact citation, privacy review, acquisition identity, subject and case references,
safe transcription, and optional checksummed paths to ignored local assets. The complete
contract is in `research/evidence/README.md`. Visible record cards point to these ids.

**Discovery threads** remain Markdown narrative proofs with strict frontmatter for cases,
people, evidence, sources, places, outcome, and next action. The Docket links the live
question; the trace explains how the evidence was weighed.

**Claims (optional, only if it earns its keep)** — a fact a person card asserts. Minimal:
`id`, `statement`, `evidence: [...]`, `confidence`. Don't build this unless the gate below
needs it; the person card + its citations may be claim enough.

**The presentation layer** stays hand-authored under a gate-enforced contract: every
Documented or Strong person row cites the Source Ledger, every visible record card resolves
to canonical evidence, every Docket entry matches its canonical case, and all references
resolve. Local private assets receive checksum validation when mounted but are never
required in a public clone.

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

Orthogonal but complementary. The **evidence layer is now the backbone**, so a future page
split is only a rearrangement of the presentation. Every page must continue to resolve
against the same cases, evidence, sources, traces, and GeoJSON rather than copy their facts.

## First vertical slice — completed

Thirty evidence records — the initial subscription migration, later subscription pulls,
and four open-web findings — are linked to canonical cases and traces and guarded by strict
validators and mutation tests. The same contract spans all four family branches.

## Database boundary

Genealogy is natively a graph: people, events, places, evidence, sources, cases, and
reasoning traces are nodes joined by typed relationships. The project now uses **CozoDB as
an embedded, derived reasoning index** for that graph.

The boundary is strict:

- Researchers author only the Git-tracked JSONL, Markdown, GeoJSON, and presentation text.
- Validators reject unresolved or one-sided references before data can land.
- The Cozo loader rebuilds the index from those files; graph rows are disposable.
- Cozo may traverse, rank, and help plan searches, but it may not originate or overwrite a
  canonical fact.
- The public artifact stays static and offline. It never ships the database or depends on a
  database service.

This gives the search tooling a graph query surface without sacrificing readable diffs,
hand editing, or long-term archival files.

### The real prize: encoded opinions as a reasoning layer for automated search

The graph earns its place by making **genealogical opinions explicit** so automated search
can be principled and cumulative instead of re-deriving judgment each session. Cozo is the
query surface; the durable value remains the rules and decisions expressed against ids from
the canonical text.

**The opinions worth encoding** (several already exist, informally — this makes them
repeatable rather than living in my head each session):

- **Chronology constraints.** parent 12–55 at a child's birth; death after birth; marriage
  after ~14; no children after death; sane generation gaps. This is exactly what rejected
  the Barron-County Marjorie (mother would have been ~13) — as a *rule*, automated search
  flags it without me.
- **Same-name adjudication.** A candidate for an open edge must match on a discriminator
  (middle name, a linking record) and be geographically/temporally plausible; "two
  independent mismatches ⇒ reject." This is the exact logic that cleared all four Marjorie
  Clemans candidates by hand.
- **Confidence propagation.** A claim is only as strong as its weakest supporting edge; a
  descent chain is as strong as its weakest link. The stems already display "weakest step"
  — encode it so it's computed, not asserted.
- **Lead tractability ranking.** Score open edges by the anchors available (known death
  place/date ⇒ orderable certificate; known spouse ⇒ findable household; cold frontier ⇒
  low). This is what produced the offline-records order for Marjorie; as a heuristic it
  ranks *every* open edge and tells automated search where to spend next.
- **Negative memory.** Rejected candidates as `refutes` edges with reasons, so search never
  re-proposes a ruled-out same-name. The Negative-Evidence Register is this, unstructured.

**How it serves automated search.** Before landing a candidate, the search agent runs it
through the constraints (contradiction check); when a name search returns N same-names, it
scores each against the graph; between sessions it reads the frontier ranking to pick the
next target and the negative memory to skip dead ends. The agent proposes; the encoded
opinions dispose. That's the graph's genuine utility here: a **reasoning substrate for
search**, realized as constraints and queries over the derived Cozo graph.

This is arguably the highest-leverage thing to build, and it pairs with the evidence layer:
the evidence graph is the data; the opinions are the rules that walk it.

### Storing paperwork and evidence

Different record types share one deliberate JSONL envelope. Their record-specific detail
lives in the privacy-safe transcription; adding a new canonical field or record type is a
hard schema migration with validator and test changes, not an untracked property added only
inside Cozo.

Scans, PDFs, and photographs remain filesystem assets. Canonical evidence stores their
paths, roles, and optional checksums; subscription captures stay ignored under
`research/pulls/**`. Cozo indexes metadata and relationships only. It does not store the
paperwork as blobs.

### Chosen derived index

CozoDB is embedded, serverless, rebuildable, and suited to ancestry paths and relationship
patterns. Research tools may use it for graph traversal, candidate ranking, negative memory,
and search planning. The index is never shipped in the public artifact, edited as research
truth, or accepted as evidence without a canonical record and normal review.

## Decisions made

1. Evidence is separate, branch-sharded JSONL; it is not folded into the source index.
2. No claims layer yet; case/person references plus citations carry the current assertions.
3. Inline record cards point to canonical evidence ids; a separate evidence view is deferred.
4. The evidence contract landed before any page split.
5. CozoDB is the sole graph index and remains a derived consumer of canonical text.
