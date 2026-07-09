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

## Do we need a relational database?

The data *is* relational (people ↔ evidence ↔ sources ↔ places ↔ cases, all many-to-many).
But "relational structure" and "a database management system" are different questions, and
they have different answers here.

**A database server (Postgres/MySQL): no.** It fights the artifact's entire reason for
being — static, offline, no server, no account, archival-for-decades. A server dies; this
record must outlive servers. It also can't be served from GitHub Pages, adds ops, and buys
nothing at this scale.

**Scale check.** The whole thing is ~85 people, ~170 sources, a few dozen evidence records,
~21 cases. That is a *spreadsheet*, not a database problem. It fits in memory as JSON with
room to spare and will grow by hand, slowly. Introducing a DBMS here is a forklift for a
book — and it violates YAGNI directly.

**The relational model belongs in plain text.** Express the relations as **id references
between git-tracked files** (evidence `supports: [ids]`, claims `evidence: [ids]`,
person `ah`/`h`, geojson `place_id`/`line_ids`). That *is* a relational model — normalized
tables as files, foreign keys as id strings — and the **gate is the constraint engine**:
`check_refs`, `check_people_index`, and `check_geo_sync` already enforce referential
integrity. This is less abstraction than a DBMS, not more, and it stays human-readable,
diffable, and archival. Plain text outlives every database format (this is why genealogy's
own interchange standard, GEDCOM, is flat text, and why archivists reach for plain files).

**The one legitimate middle path: SQLite — build-time only, if ever.** SQLite is a single
file, no server, and archival-grade (the Library of Congress lists it as a preferred
preservation format). If ad-hoc querying during research ever becomes a real pain ("every
unproven parent in Kansas born before 1880"), a SQLite file *generated from* the plain-text
records — used by the toolchain and by research, **never shipped to the browser** (that
would mean a ~1 MB WASM SQL engine and the end of self-containment) — is reasonable. But
only if the plain-text approach starts hurting. Today it doesn't. Don't build it yet.

**Recommendation:** no DBMS. Keep the plain-text relational store + the gate as its
integrity checker. Revisit SQLite as a build-time convenience only if querying becomes
painful — and even then the shipped artifact stays static files.

### What about a *graph* database specifically?

Sharper instinct: genealogy is natively a **graph** (people = nodes; parent-of /
married-to / child-of = typed edges; a pedigree is a graph traversal), and evidence,
sources, places, and cases hang off that same graph. Modeling it as a property graph —
nodes with types (`person`, `evidence`, `source`, `place`, `case`, `event`) and typed
edges (`parent_of`, `married_to`, `born_at`, `cites`, `supports`, `resolves`, `refutes`) —
is the truest picture of the data. So: **adopt the graph as the mental model.**

But, same split as before:

- **A graph DBMS (Neo4j and friends): no**, for the identical reasons — it's a server,
  which breaks static / offline / archival / no-ops, and it can't be served from GitHub
  Pages. Same forklift, same book.
- **You already have the graph, in plain text.** The geojson `family_link` features are
  literally a typed edge list (`from[]`, `to`, `kind: "parents to child" | "couple
  convergence" | "descendant path" | "parent evidence"`); the ahnentafel numbers encode
  the pedigree DAG (father of *n* = 2*n*); person `h`/`ah` and the `source_refs` are edges
  too. The evidence layer just extends this graph with `evidence`/`case` nodes and
  `supports`/`cites`/`resolves` edges. Storage = a **nodes file + a typed-edges file** (or
  edges embedded as id refs, as today). The gate becomes **graph-integrity**: every edge
  endpoint resolves to a real node.
- **Traversal is trivial at this scale.** "Ancestors of X", "everything a source touches",
  "shortest path between two people" are the graph queries that make a graph DB shine — at
  *millions* of nodes with deep walks. Here it's ~85 nodes, ~4 generations. Those walks are
  a 20-line Python function over the edge list, or an in-memory `networkx` graph built at
  build-time from the plain-text edges (never shipped). That's the right amount of tool.

So: **model it as a graph, store the graph as plain-text nodes + typed edges, run no graph
server.** If interactive graph *exploration* ever becomes a feature of the viz, build the
in-memory graph at build-time and emit exactly the static JSON the page needs — the browser
still loads plain data, not a database.

### The real prize: encoded opinions as a reasoning layer for automated search

The strongest argument for "graph" here isn't storage — it's that a graph with
**genealogical opinions encoded on it** would make *automated search* (me + Codex driving
Ancestry/web lookups) principled and cumulative instead of re-deriving judgment each
session. That's the valuable idea, and it's worth building. But note what's actually
valuable: the **encoded opinions**, not the query engine. You can have the opinions without
a graph DBMS — as predicates over the in-memory graph (built from the plain-text
nodes/edges; `networkx` at search-time, never shipped). At ~85 nodes the "query language"
is a handful of Python functions, and a DBMS buys nothing the ethos doesn't lose.

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
opinions dispose. That's the graph's genuine utility here — as a **reasoning substrate for
search**, realized as constraint code over a plain-text graph, not as a database server.

This is arguably the highest-leverage thing to build, and it pairs with the evidence layer:
the evidence graph is the data; the opinions are the rules that walk it.

### Storing paperwork and evidence — flexibility without a server

The appeal of a graph DB for evidence is the **schemaless flexibility**: a census node, a
gravestone node, and a divorce-index node have wildly different shapes, and you don't want
to declare rigid columns up front. That instinct is right. Two clarifications settle it:

- **The flexibility is the *model*, not the engine.** Schemaless property nodes + typed
  edges is a data model; **plain-text JSON/YAML already is exactly that.** A census evidence
  node carries `household[]`; a grave node carries `inscription` + `photo`; a divorce node
  carries `spouse` + `date` — each a different property bag, side by side, no migration to
  add a field to one and not the others. You get graph-DB flexibility with zero server,
  full git diffs, and archival durability. (This is why the **record cards** already render
  differently per record type — the model is flexible; the storage doesn't need to be a DB.)

- **The actual paperwork does NOT belong in any database — graph or relational.** Storing
  scans/PDFs/photos as blobs inside a DB is an anti-pattern: bloat, no dedup, no diffing,
  painful backup/restore, and it couples your images to a DB format that will rot. The
  durable pattern — and what this project already does — is **files on the filesystem,
  metadata + relationships in the record**: the evidence *node* holds the type, the exact
  citation, the transcription, and a `path` reference; the image lives under
  `research/pulls/**` (gitignored for Ancestry ToS), addressed by that path. The graph
  stores *about* the paperwork; the paperwork stays files. For preservation you want a file
  tree + a manifest, not a binary DB.

**When would a graph DBMS's flexibility actually earn its cost for evidence?** At
*thousands* of heterogeneous records where you want ad-hoc cross-queries over an evolving
shape without migrations, and emergent connection-discovery matters. At *dozens*, plain
JSON gives the same flexibility, and Python over the in-memory graph gives the same
queries — while keeping diffability, archival durability, and zero ops. So: **flexible
model, yes; graph server, no; binaries as files, always.**

### "Graph + SQLite"

This is the best "database" option on the table, and it dissolves my main objection: SQLite
is **serverless and a single file** (archival-grade — a Library of Congress preferred
format), and you can model a graph in it cleanly (a `nodes` table + an `edges` table +
`JSON` columns for the flexible per-node properties, with recursive CTEs for ancestor /
descendant / path traversal). No server, one file, SQL + graph traversal, schemaless-ish
via JSON columns. If we were going to adopt *a* database, this is it.

The deciding question at this scale isn't server-vs-serverless anymore — it's
**diffability and hand-editability**. This corpus is hand-curated, version-controlled, and
its *git history of reasoning* ("what changed, and why") is part of the value. A SQLite file
is binary: you can't see a meaningful PR diff, and you can't hand-edit a person the way you
edit a card or the geojson today — you need SQL or a tool. Those are real losses for a
small, single-author, forever archive, and SQLite's wins (SQL, traversal, scale) don't yet
pay for them.

**The synthesis that keeps both:** plain text stays the **source of truth** (diffable,
hand-editable, archival); SQLite becomes a **derived, build-time query index** — generated
from the text nodes/edges, used by the reasoning layer and automated search for
traversals/queries, and thrown away/regenerated at will. Text = truth; SQLite = a
materialized query cache; the viz still loads emitted static JSON, never the DB. You get the
graph-SQL query surface for the "encoded opinions" *and* keep git-native authoring. And it's
YAGNI-friendly: build the SQLite index only when the reasoning queries actually want more
than `networkx`-over-the-text gives — until then, don't.

(The coherent alternative is SQLite *as* the source of truth — defensible if you'd rather
have rich queryability than git-diffable hand-editing. Given how this project is actually
worked — hand-edited text, versioned reasoning, the gate as integrity — text-as-truth +
SQLite-as-derived-index is the better fit. But it's your call, and it's the one real fork.)

### A *dedicated* graph DB — the fair version

Worth splitting into two categories, because they get different answers:

- **Server graph DBs (Neo4j, Memgraph, ArangoDB).** Most powerful — Cypher, mature tooling,
  built-in graph *visualization/exploration*. But a server: breaks static/offline/archival/
  no-ops for anything shipped, and running a Neo4j instance to reason over ~85 nodes is
  overkill by three orders of magnitude. As the artifact's store: no. As a research-side
  toy for exploring the graph visually: possible, but heavy for what a notebook does.
- **Embedded graph DBs (KùzuDB; or Oxigraph for RDF/SPARQL).** This is the category I under-
  credited. Embeddable, in-process, **serverless**, single storage directory — "SQLite, but
  graph-native," with real Cypher and fast variable-length traversal. It removes the server
  objection *and* gives a proper graph query language, which SQLite's recursive CTEs only
  approximate. If the reasoning layer's queries are dominantly graph-shaped (ancestors,
  paths, subgraph patterns — for genealogy they are), an embedded graph DB is a *better*
  derived index than SQLite.

What a dedicated graph DB uniquely gives that `networkx`-over-text does not: a **declarative
query language** (`MATCH (p:Person)-[:CHILD_OF]->(x) WHERE x IS NULL AND p.birth < 1880`)
that's genuinely nicer for the automated-search "opinions" than ad-hoc Python, plus
exploration tooling. Those are real but modest wins at this scale.

So the honest position: **if you want a graph DB, have an *embedded* one as a derived
build-time reasoning index** (KùzuDB generated from the plain-text truth, queried by the
search agent, never shipped) — same materialized-view pattern as SQLite, just graph-native,
and the right pick if graph queries dominate. Keep text as the source of truth (diffable,
hand-editable, archival). Don't ship it to the browser; don't run a server; and — YAGNI —
don't build the index at all until `networkx`-over-text stops being enough at ~85 nodes.
The choice between a SQLite index and a Kùzu index is a small, reversible, build-time detail
you can defer until the reasoning layer actually exists and tells you which query shape it
wants.

## Decisions needed from you

1. Evidence store as an **extension of `source-index.json`**, or a **new `evidence.json`**
   (keeps sources vs. evidence-with-transcriptions separate)?
2. Do we add a lightweight **claims** layer, or treat the person card + its citations as
   the claim (simpler, YAGNI)?
3. Build the **`#ev.*` evidence view / deep-link** (level 3 pointing-back), or stop at
   inline record cards (level 2) for now?
4. Sequence: evidence layer **before** the page split (recommended), or interleave?
