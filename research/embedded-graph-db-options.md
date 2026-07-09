# Embedded graph-store options for the reasoning index

Scope: candidates for the **derived, build-time reasoning/query index** described in
`evidence-and-presentation-architecture.md` — generated from the plain-text truth, queried
by the toolchain + automated search, **never shipped to the browser, never a server**.
Constraints that matter here: embeddable/in-process, good **Python (uv)** story, and a good
fit for **recursive genealogical rules + graph traversal** at small-but-growing scale
(~85 nodes today). Because it's a *derived* index regenerable from text, the pick is
low-stakes and swappable — that de-risks choosing a younger tool.

## At-a-glance

| Option | Kind | Query language | Embedded | Python pkg | Maturity | Sweet spot |
|---|---|---|---|---|---|---|
| NetworkX | in-mem graph lib | Python (imperative) | n/a (in-proc) | `networkx` | mature | just build it in memory |
| python-igraph | in-mem graph lib | Python/C | n/a | `igraph` | mature | same, faster |
| **KùzuDB** | property graph DB | **Cypher** | yes | `kuzu` | young, active | property-graph + Cypher, analytics |
| **CozoDB** | graph+relational+vector | **Datalog** | yes | `pycozo` | young | recursive *rules* / inference |
| Oxigraph | RDF triplestore | **SPARQL** | yes | `pyoxigraph` | maturing | RDF standards / interop |
| RDFLib | RDF lib | SPARQL | yes (pure-py) | `rdflib` | mature | small RDF, zero native deps |
| DuckDB | analytical SQL | SQL (+ recursive CTE, PGQ ext) | yes | `duckdb` | mature/active | reads your JSON directly, SQL analytics |
| SQLite | relational | SQL (+ recursive CTE) | yes | stdlib | ubiquitous | ubiquitous, archival baseline |

Explicitly **not embedded** (servers/distributed — excluded for the ethos, listed so we're
complete): Neo4j server, Memgraph, Dgraph, NebulaGraph, JanusGraph, OrientDB, TigerGraph,
ArangoDB. RedisGraph is **discontinued** (Redis dropped it in 2023) — do not use. Neo4j has
an *embedded* mode but it's JVM/Java-only — impractical from Python. TerminusDB and Dolt are
covered under "versioned data" below.

## The in-memory libraries (not databases — the YAGNI baseline)

### NetworkX
- **Pros:** pure Python, one `pip`/`uv add`, no native deps, huge algorithm library
  (ancestors/descendants/shortest path/components), trivial to build from the text nodes+edges
  each run. Zero persistence to manage — perfect for a *derived* index.
- **Cons:** no persistence (rebuild each run — fine here), no declarative query language (you
  write Python), slow at large scale (irrelevant at ~85 nodes).
- **Verdict:** the correct *first* answer. At this scale it does everything the reasoning
  layer needs with zero infrastructure.

### python-igraph
- **Pros:** C-backed, much faster than NetworkX, solid algorithms.
- **Cons:** clunkier API, still imperative (no query language), native build. Speed is moot here.
- **Verdict:** only if NetworkX ever gets slow (it won't at this scale).

## Embedded property-graph databases

### KùzuDB  ★ top DB pick if you want a property graph + Cypher
- **Pros:** purpose-built "embedded graph DB" ("DuckDB/SQLite for graphs"); real **Cypher**;
  columnar + fast multi-hop traversal and pattern matching; clean `pip install kuzu` Python
  API; ingests CSV/Parquet/Pandas/Arrow directly (easy to load from generated text); MIT;
  actively developed. Cypher is familiar (Neo4j-like) and reads well for the search rules
  (`MATCH (p:Person)-[:CHILD_OF]->(x) WHERE x IS NULL`).
- **Cons:** young project (API still evolving; smaller community than SQLite/Neo4j); storage
  is a Kùzu-specific directory (opaque, not diffable — fine for a *derived* index, not for truth);
  Cypher is great for patterns/traversal but is not a full recursive *rule* language.
- **Verdict:** the natural choice if you think in property-graph + Cypher terms. Best mainstream
  embedded graph DB today.

### Neo4j (embedded)
- **Pros:** the most mature graph engine, richest Cypher + tooling/visualization.
- **Cons:** embedded mode is **JVM/Java only** — a bad fit for a Python/uv toolchain; heavyweight.
  The server is out on ethos grounds.
- **Verdict:** no, for this stack.

## Embedded Datalog / graph-relational

### CozoDB  ★ top pick for the *reasoning* ("opinions") layer specifically
- **Pros:** embeddable, serverless; **Datalog** query language — which is *purpose-built for
  recursive declarative rules*, exactly the shape of genealogical "opinions" (ancestry
  closure, cousin detection, constraint propagation, same-name adjudication all read as a
  handful of rules); pluggable backends incl. an on-disk **SQLite** file and RocksDB (so it can
  be a single file); `pip install pycozo`; also does graph algorithms and vector search.
- **Cons:** young, smaller community than the others (bus-factor/API-churn risk); Datalog has a
  learning curve if you've never used it; docs thinner than Kùzu/DuckDB.
- **Verdict:** the most *intellectually* fitting option for encoding rules — if the reasoning
  layer becomes central, Datalog is the elegant language for it. Slightly more of a bet.

## Embedded RDF / triplestores (SPARQL)

### Oxigraph
- **Pros:** embeddable Rust RDF store with **SPARQL 1.1**; `pip install pyoxigraph`; in-memory or
  RocksDB-backed; standards-based, so it interoperates with genealogy RDF vocabularies
  (GEDCOM X, the BIO vocab, `schema.org/Person`). Triples are the ultimate flexible/schemaless
  graph.
- **Cons:** RDF/SPARQL has real conceptual overhead (reification for statements-about-statements,
  IRIs everywhere); tooling is niche; heavier mental model than a property graph.
- **Verdict:** compelling *only* if standards/interop or publishing linked-data is a goal. For a
  private reasoning index it's more ceremony than payoff.

### RDFLib
- **Pros:** pure-Python RDF, no native deps, SPARQL, mature; in-memory or SQLite-backed store.
- **Cons:** slow at scale (fine here); same RDF conceptual overhead.
- **Verdict:** the zero-friction way to try the RDF path in Python before committing to Oxigraph.

## Embedded relational used as a graph

### DuckDB
- **Pros:** embedded analytical SQL, extremely fast; **reads your generated JSON/CSV/Parquet
  directly** (could query the text store almost without an import step); recursive CTEs for
  traversal; an experimental **DuckPGQ** extension adds SQL/PGQ property-graph pattern syntax;
  great Python API; very active. Excellent as a general analytical index.
- **Cons:** not graph-native (recursive CTEs are more verbose than Cypher/Datalog for deep
  walks); DuckPGQ still experimental.
- **Verdict:** the pragmatic "I like SQL and want it to just read my files" option; strong middle
  ground, especially for tabular/analytical questions mixed with light traversal.

### SQLite
- **Pros:** ubiquitous, zero-install (Python stdlib), single file, archival-grade, recursive
  CTEs + JSON1.
- **Cons:** graph queries via recursive CTEs are the most verbose of the bunch; no graph niceties.
- **Verdict:** the boring, safe baseline if you want *a* persisted index and value ubiquity over
  ergonomics.

## Aside: versioned-data stores (they target the diffability concern, not traversal)
- **TerminusDB** — graph/document DB with **git-like data versioning** (branch/diff/merge of
  data). Directly addresses "I want diffable history." But it's server-oriented (Rust core),
  Datalog-ish (WOQL), niche. Interesting philosophically; heavy for this.
- **Dolt** — "Git for data": a **versioned SQL** database with branch/diff/merge. Relational, not
  graph, and CLI/server-oriented. Only relevant if you ever wanted DB-*as-truth* without losing
  diffs. Not needed while text is the truth.

## Top suggestions (with reasoning)

1. **Start with NetworkX — no DB.** At ~85 nodes, build the graph in memory from the text
   nodes/edges and encode the "opinions" as Python predicates + NetworkX traversals. Zero
   infrastructure, and it proves the reasoning layer on real data. This is the YAGNI-correct
   first move and likely enough for a long time.
2. **If/when you want a persisted, declarative index, the two real contenders:**
   - **CozoDB (Datalog)** — pick this if the *rules* are the point. Genealogical constraints and
     inference are recursive declarative rules, and Datalog expresses them more elegantly than
     anything else here. Best conceptual fit for "encoded opinions"; slightly bigger bet.
   - **KùzuDB (Cypher)** — pick this if you'd rather think in a property graph with a familiar,
     mainstream query language and want the smoothest traversal/pattern ergonomics. Safer,
     more conventional.
3. **DuckDB** is the strong pragmatic alternative if you're most comfortable in SQL and love that
   it can query your generated JSON directly — good for mixed tabular+graph questions.
4. **Oxigraph/RDFLib (RDF/SPARQL)** only if standards/interoperability or publishing linked
   genealogy data becomes a goal; otherwise the RDF overhead isn't worth it for a private index.

**My overall recommendation:** NetworkX now; and when it stops being enough, **CozoDB** if you
lean into rule-based reasoning (my pick given the "encoded opinions" goal), or **KùzuDB** if you
prefer property-graph + Cypher. Either is generated from the plain-text truth and thrown away/
regenerated freely — so you can even prototype both cheaply and keep the winner. Never a server;
never shipped to the browser.

## DECISION (2026-07-09): CozoDB

Owner chose **CozoDB** as the derived reasoning/query index. Rationale: Datalog is the natural
language for the encoded "opinions" (recursive rules), it's embeddable + single-file (SQLite
backend), and it bundles vector search so we don't need a second store. It remains a *derived*
index generated from the plain-text truth (`pip install pycozo`, build/search-time only, never
shipped). The young-project risk is real but mitigated by the derived-index design — if Cozo
ever fell over, regenerate the same graph into Kùzu/SQLite from the unchanged text truth.

### Where the vector search actually earns its keep here (honest read)

Bundled vectors are a genuine bonus, but they help in specific places — and *not* the one people
assume first:

- **Semantic retrieval over the evidence/thread corpus — the strongest fit.** As the
  `reasoning-traces/`, evidence notes, and obituary/record text grow, embed them so automated
  search can ask "have we already investigated an institutional death in this family?" or "what
  did we find on the Rust East Frisian origin?" This is RAG over the evidence layer — the agent's
  cross-session memory of its own prior work. Value grows with the corpus.
- **A *signal* in entity resolution / same-name candidate scoring — secondary.** Embed a
  candidate record's full context (name + dates + places + associated names) and find the nearest
  existing person node to suggest identity / flag collisions. Useful as one input, not the whole
  decision.
- **NOT the right tool for name-spelling variants.** "Zodrow→Farrow", "Mundell→Mandell→Mondel",
  "Clemans/Clemens/Clemons/Clements" are *orthographic/phonetic* problems, and the proven, lighter
  tools are **Soundex / Double Metaphone / Jaro-Winkler / Levenshtein** — encode those as Datalog/
  Python predicates. Vectors complement them for *semantic* text, they don't replace them for
  spelling.

Cost to be aware of: vectors need an **embedding model** at build/search-time (a local
sentence-transformer or an API call) — a real moving part. It's YAGNI until the corpus is big
enough that semantic retrieval beats `grep`; at a few dozen traces, full-text search is often
enough. So: adopt Cozo for the Datalog rules first; turn on its vector search when the corpus
makes it worth an embedding step.
