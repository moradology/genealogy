# The researcher's cockpit

Status: PROPOSAL. A single, ergonomic tool surface an AI researcher (Claude or Codex)
operates the whole project through — instead of ad-hoc scripts and a dozen remembered
invocations. It sits *on top of* the evidence layer (see
`evidence-and-presentation-architecture.md`): the graph is the data, the cockpit is the
controls.

## Why

Today the AI researcher: hand-writes a Playwright/CDP script per Ancestry lookup (~20 this
session), remembers `bash tools/check.sh` / `uv run tools/check_*.py` / the build scripts
separately, hand-edits `index.html`/geojson surgically, and tracks state in prose. It works,
but it's high-friction and easy to get subtly wrong. The cockpit makes the common research
loop — **propose candidate → test against the opinions → pull the record → add evidence →
validate → update the frontier** — a short sequence of clean, composable commands.

## Design principles (the important part)

- **One entry point, verb-first.** A `gen` CLI (uv). `gen <action> [args]`. Discoverable via
  `gen --help` and `gen ask --list`.
- **JSON-first I/O.** Every command emits structured JSON by default (agents parse it
  reliably); `--pretty` for humans. Inputs are flags or JSON on stdin. This is the single
  biggest ergonomics lever for an AI operator.
- **Composable.** One command's output feeds the next: `gen frontier` → pick a target →
  `gen ancestry household` → `gen add-evidence` → `gen validate`.
- **Idempotent + safe.** Writes to the text truth are validated before commit; the paid
  Ancestry session keeps its single-session / human-paced guardrail with a `--dry-run`;
  destructive ops confirm.
- **Self-describing.** `--help` everywhere, `gen ask --list` for the canned reasoning
  queries, schemas printable — a fresh agent orients in one command.
- **Functions, not a framework.** A thin dispatcher (argparse or typer) over small Python
  functions that mostly *wrap tools we already have*. No OO framework, no daemon, no hidden
  state — the JSONL files are the state. (YAGNI; functions over classes.)

## The command surface (grouped)

**TRUTH — the evidence store**
- `gen add-evidence <pull-dir>` — ingest a pull into an evidence node (type, exact citation,
  transcription, local image `path`, `supports`).
- `gen add-node` / `gen add-edge` — people/places/cases; typed edges.
- `gen show <id>` — a node and its graph neighborhood.
- `gen validate` — referential + schema + citation-contract integrity (the gate for the graph).

**REASON — the opinions + graph queries** (NetworkX now, CozoDB later)
- `gen adjudicate <candidate.json>` — run a proposed identity through chronology + same-name
  rules → verdict + reasons. (This is the four-Marjorie logic, automated.)
- `gen frontier` — ranked open edges: what to research next, with why + tractability.
- `gen ancestors <person>` / `gen descendants <person>` / `gen path <a> <b>` — traversals.
- `gen contradictions` — scan the graph for constraint violations.
- `gen recall "<query>"` — semantic retrieval over traces/evidence (Cozo vectors; later).

**FIELD — acquisition**
- `gen ancestry search --collection N --name "..." [--birth --residence ...]` → JSON results.
  (Wraps the CDP/Playwright driving hand-scripted all session.)
- `gen ancestry record <id>` / `gen ancestry household <id>` → structured household JSON.
- `gen web "<query>"` → dispatch a Codex web search, return findings.

**VIZ — the presentation projection**
- `gen project` — regenerate/validate `index.html` (and future pages) from the truth.
- `gen gate` — the full `check.sh`, wrapped.
- `gen build <basemap|fonts|keys|backlinks|source-index> [--check]` — wrap the existing build
  tools under one consistent UX.

**SESSION**
- `gen status` — dashboard: gate state, open cases, recent evidence, frontier top-5.
- `gen log <case> "<note>"` — append to a discovery thread.

## The Ancestry session manager (shared account, polite agents)

The account is one shared, ban-risky resource. The rule: **agents never touch Ancestry
directly — only through `gen ancestry`, which enforces safety for them.** Three layers:

1. **Global queue + human pace (BUILT).** State lives machine-globally under
   `~/.gen-cockpit/ancestry/` (outside the repo). Real hits take a single `flock` — one
   agent at a time, the rest queue; the lock frees on close *and* on crash (the OS frees the
   fd). A shared `last_request` timestamp enforces `MIN_INTERVAL` (default 5s + jitter)
   between real hits across *all* agents. So no matter how many agents run, Ancestry sees one
   paced, human-like stream.
2. **Durable acquisition store (BUILT; upgraded from a cache 2026-07-09).** The structured
   data from every page ever fetched is kept forever in `research/cache/ancestry/` (in the
   repo tree, gitignored per Ancestry ToS, backed up with the project). Revisits by any
   agent, any session, return instantly (`"cached":true`) and never touch Ancestry.
   Entries are `{meta, data}` envelopes (fetch timestamp + source URL); `record` and
   `household` share one entry (same page). `--fresh` forces a re-fetch (mainly searches,
   which can gain rows). Managed via `gen ancestry cache stats|list|clear` (clear is
   guarded). Machine-global concerns (queue lock, pacing, tabs, agent cursors) stay in
   `~/.gen-cockpit`.
3. **Per-agent tabs + relative addressing (BUILT).** Verbs: `goto <address>`, `where`,
   `next`, `prev`, `open [N]`, `back` — all `--agent <id>`-scoped. Semantics decided at
   review: (a) an agent's location is **logical** — a cache-served `goto` updates state
   without moving the tab; the `navigated` field reports whether a real fetch happened;
   (b) records are cached forever (immutable), searches until `--fresh`; search cache is
   limit-free and stores the full result set, so one query costs at most one real hit ever;
   (c) **one process per agent-id at a time** (the flock serializes Ancestry hits, not
   per-agent state writes); (d) the human's own tab is never driven — stateless commands
   use the reserved `default` agent tab. Known gaps, deliberate: no pagination past page 1,
   no `up`/`household <N>` verbs yet, no tab-cleanup verb.

### Per-agent tabs on a shared Chrome (as built)

One Chrome/CDP process, one login; each agent gets its **own tab** so navigation state
doesn't stomp others. Each `gen` invocation is a fresh process, so "the agent's tab" is made
durable by mapping `agent-id -> CDP targetId` in `~/.gen-cockpit/tabs.json`: on
`gen ancestry --agent A ...`, find A's target among the browser's pages (via a CDP session's
`Target.getTargetInfo`); if gone, open a new tab and record it. The global lock still
serializes the actual *requests* (the account limit is global), so tabs buy **navigation
isolation**, not request parallelism — agent A can sit on a search while B reads a record,
each driving only its own tab.

### Local / relative addressing (designed)

A compact address scheme + per-tab cursor state so agents "move around" Ancestry without
juggling URLs:
- **Absolute:** `record/2442/58087568`, `search/6224?name=Marjorie_Clemans&birth=1912`,
  `collection/6224`.
- **Relative (needs per-tab state — current location, current result set + cursor, a small
  history stack, stored per agent):** `next` / `prev` (walk search results), `open <n>`
  (open result N), `back` (history), `up` (record -> its search/collection),
  `household <n>` (open a household member's own record).
So: `gen ancestry --agent A goto record/2442/58087568`, then `... A up`, `... A next`,
`... A open 3`. This turns the browser into a stateful, addressable surface per agent.

Build note: layer 3 is a real build (per-tab state machine + address parser + history) and is
optional — layers 1-2 already make the shared account safe for many agents. Do tabs first
(navigation isolation), addressing second.

## Build order (pain-first, YAGNI)

1. **`gen ancestry …`** — the highest-friction thing today. Turn the ad-hoc CDP scripting into
   stable `search` / `record` / `household` commands returning JSON. Immediately useful, even
   before the evidence layer exists. (Keeps the single-session guardrail.)
2. **`gen gate` / `gen build …`** — wrap the tools we already have under one entry point. Cheap
   tidy-up, removes a dozen remembered invocations.
3. **Evidence store + `gen validate`** — the JSONL truth + graph integrity (delivered with the
   Mundell/Clemans vertical slice).
4. **`gen adjudicate` / `gen frontier` / `gen contradictions`** — the reasoning over NetworkX;
   must re-derive the four-Marjorie rejection and the offline-records ranking from the graph.
5. **`gen recall`** — Cozo + vectors, once the corpus makes semantic retrieval beat `grep`.

## How it fits everything else

The cockpit is the *interface*; the evidence graph (text truth) is the *data*; CozoDB/NetworkX
is the *reasoning index*; the viz is a *projection*. The cockpit is also the natural seam for
driving Codex: Claude specs a command + its gate, Codex implements the plumbing, Claude reviews
and keeps the gate green — while all family-facing page work stays hand-done.

The dogfooding test: once `gen` exists, the next real research session should run almost entirely
through it, and re-derive a result we already trust (the Marjorie adjudication) with a handful of
commands instead of twenty hand-written scripts.
