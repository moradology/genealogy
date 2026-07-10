# The researcher's cockpit

Status: FOUNDATION BUILT. This document separates the commands that work today
from graph-based research ideas that still need design or implementation.

The canonical local entry point is `./gen`, run from the repository root. It is
not installed as a machine-wide `gen` command. `tools/gen.py` and the smaller
scripts under `tools/` are implementation details behind that entry point.

The cockpit sits over the durable research files described in
`evidence-and-presentation-architecture.md`. Those reviewed text files remain
the source of truth. A graph database can index them for searching
and reasoning, but it must stay rebuildable and must not become another place
where researchers author facts.

## Quick start — built now

```sh
./gen --help
./gen build people-index --check
./gen build source-index --check
./gen show person.doyle_zimmerman
./gen case list --status open,in_conflict,needs_pull
./gen ancestors person.evelyn_mundell
./gen status
./gen stamp
./gen ancestry cache stats
./gen gate
```

Command results are one JSON object on standard output; add `--pretty` anywhere
for indented JSON. Help is ordinary text. A result has at least `command` and
`ok`, and the process exits successfully exactly when `ok` is true. Wrapped
tool output is carried in the JSON `output` field.

`./gen stamp` is a local check, equivalent to `./gen stamp --check`. Use
`--write` after an intentional `index.html` change. `--deployed` is the only
stamp mode that contacts the published site.

### Research stores and orientation

- `./gen evidence add --shard <branch>` reads one evidence record as JSON from
  standard input, validates the whole store, and writes only if every check passes.
  Add `--validate-only` to test without writing.
- `./gen trace new --slug <slug> --title <title> ...` creates a validated reasoning
  trace with its case, person, evidence, source, and place references.
- `./gen show <id>` resolves any case, evidence, source, trace, GeoJSON, person,
  relationship, or gap id and reports everything that refers to it.
- `./gen status` runs the fast family, evidence, case, and trace checks and reports
  family counts, case status, evidence totals, and the newest trace. It is offline
  and does not run the browser acceptance test.

People and family links are authored in `research/people/people.jsonl` and
`research/people/relationships.jsonl`. The public registry, pedigree, and Index of
Names are generated with `./gen build people-index` and checked by the gate.

## BUILT command surface

### Repository maintenance

- `./gen gate` runs the same complete gate as CI.
- `./gen build <target> [--check]` builds or verifies one generated artifact.
  Targets are `basemap`, `fonts`, `citation-backlinks`, `docket`,
  `plate-keys`, `people-index`, `source-index`, and `family` - the last
  regenerates every person card, gap card, inline stem, and record card
  from the display blocks and layout in the truth stores.
- `./gen stamp [--write|--check|--deployed]` manages the public-page content
  fingerprint. With no flag it checks the local stamp.

### Canonical research workflow

- `./gen evidence draft --from-cache record/COLL/ID --id ev.ID` produces a
  review-required evidence draft from a validated cached record. It is strictly
  offline and carries citation fields, cache provenance, and explicit review
  warnings; it does not write the draft.
- `./gen evidence add --shard BRANCH [--validate-only]` validates and appends a
  reviewed evidence object supplied on standard input.
- `./gen trace new ...` creates a canonical reasoning trace, and `./gen case
  update case.NN ...` links reviewed evidence and traces into a case.
- `./gen case list [--status CSV] [--branch CSV]` returns canonical case records
  with optional filters.
- `./gen relationship update relationship.ID ... [--validate-only]` updates a
  family edge and atomically regenerates the people projection. Status changes
  require a provenance note. Rejected edges retain their stable ids, structured
  refs, and prior provenance but are excluded from traversal and pedigree output.
- `./gen gap resolve gap.ID --parent person.ID --role father|mother
  --evidence-ref ev.ID ... [--validate-only]` resolves one parent role. Every
  competing same-role hypothesis must be rejected explicitly; a partial
  resolution remains on the ancestor frontier. Rejected hypotheses remain
  inspectable canonical rows. Replaying the exact landed action is idempotent
  and repairs a stale projection after an interrupted two-file write.
- `./gen ancestors person.ID` reports the upward graph and unresolved frontier.
  `./gen path person.A person.B` reports the shortest parent/spouse chain.

### Reasoning layer

- `./gen contradictions [--strict]` sweeps the family graph with the encoded
  rules: parent ages, posthumous births, marriage ages, evidence hygiene, and
  multiple-parent groupings. Violations are impossibilities on accepted dated
  data; recorded conflicts and advisories never gate anything. `--strict`
  exits 1 only on violations.
- `echo '<claim json>' | ./gen adjudicate` judges a same_person or parent_of
  claim across chronology, name (with the recorded variant classes), middle,
  geography, and spouse axes, and surfaces recorded negative memory: not_found
  search logs, rejected relationship tombstones, resolved gaps, and
  exclusion_target features. The verdict is advisory - the envelope travels
  with a proposal; it never blocks a write.
- `./gen frontier [--top N]` ranks the open research edge (open gaps, weak
  lead/open parent links, undated direct-line ancestors) with a deterministic
  integer rubric, splitting online work from offline-only leads. Start
  research sessions here.
- `./gen status` includes the contradiction counts and top frontier targets.
  `./gen case update --status closed` refuses while a violation touches the
  case's people; demote the offending link to hypothesis or fix the data.

Each reasoning verb reproduced an existing trusted conclusion before first
use on new ones: the contradictions sweep classifies the recorded dual-Ford
conflict without gating it, adjudicate re-derives all four Marjorie Clemans
same-name eliminations, and frontier reproduces the Marjorie offline
records-to-order ranking.

Use each command's `--help` for its full flags and output contract. Write
commands accept canonical IDs only; filename aliases are not a write format.

### Ancestry acquisition

These commands use the already-running, logged-in Chrome session; they never
launch a browser. A live read is shared, queued, and human-paced across agents.
Live-capable reads are cache-first by default: a valid stored result returns
immediately, while a miss automatically joins the shared paced queue, is
rechecked under the lock, and then fetches live. Do not preflight ordinary
reads with `--cache-only`. Use `--cache-only` only when a miss must remain
offline, such as before live research is approved. `where`, `next`, `prev`, and
`back` never contact Ancestry. `--cache-only` and `--fresh` cannot be combined.

```text
./gen ancestry search --collection N --name Given_Surname
    [--birth YEAR] [--place PLACE] [--spouse Given_Surname]
    [--birthplace PLACE] [--exact-name] [--agent ID] [--limit K]
    [--fresh | --cache-only]
./gen ancestry record --collection N --id RECORD_ID [--agent ID] [--fresh | --cache-only]
./gen ancestry household --collection N --id RECORD_ID [--agent ID] [--fresh | --cache-only]

./gen ancestry goto <address> [--agent ID] [--fresh | --cache-only]
./gen ancestry open [N] [--agent ID] [--fresh | --cache-only]
./gen ancestry where [--agent ID]
./gen ancestry next [--agent ID]
./gen ancestry prev [--agent ID]
./gen ancestry back [--agent ID]

./gen ancestry session stats --agent ID
./gen ancestry session reset --agent ID --confirm RESET-ANCESTRY-SESSION

./gen ancestry cache stats [--kind K]
./gen ancestry cache list [--kind K]
./gen ancestry cache migrate [--kind K]
./gen ancestry cache clear (--kind K | --all)
    [--include-records --confirm DELETE-DURABLE-ANCESTRY-RECORDS]
```

Options belong after their Ancestry subcommand. For example:

```sh
./gen ancestry goto "search/6224?name=Marjorie_Clemans&birth=1912" --agent alice
./gen ancestry next --agent alice
./gen ancestry open 0 --agent alice
./gen ancestry back --agent alice
```

Supported addresses are:

- `record/COLL/ID`
- `search/COLL?name=Given_Surname&birth=YEAR&place=PLACE&spouse=Given_Surname&birthplace=PLACE&exact=true`
- `collection/COLL`

Use `./gen ancestry --help` or, for example,
`./gen ancestry goto --help` for the full current contract.

## Ancestry safety and state — built now

The account is one shared, rate-sensitive resource. Agents should use only
`./gen ancestry` for these reads.

1. The machine-global queue and pacing state live under
   `~/.gen-cockpit/ancestry/`. Real requests take one inter-process lock, and a
   shared timestamp spaces requests across every agent. Each agent also has a
   guarded, resettable accounting session that counts cache reads and real hits;
   failed live HTTP or parse attempts count because they consume account budget.
2. Structured results live under `research/cache/ancestry/`. This directory is
   ignored by Git because the acquired material is restricted. Record and
   household views share the same stored record. A normal command reads this
   store first and automatically queues a live fetch on a miss. `--fresh`
   intentionally bypasses a stored result; `--cache-only` turns a miss into an
   offline error and should not be used as a routine preflight.
   Version-2 entries require the explicit offline `cache migrate` hard cutover;
   version-3 payloads include an integrity digest.
   Removing durable record entries requires both `--include-records` and the
   displayed confirmation phrase, including when `--all` is used.
3. Each `--agent ID` has its own logical location, result cursor, history, and
   Chrome tab. The mapping is stored under `~/.gen-cockpit/ancestry/`. Use one
   process at a time for a given agent id.
4. A stored `goto` can update logical state without moving Chrome. `back`
   always restores the previous logical state locally. The JSON `navigated`
   field reports whether the browser actually moved.
5. Stored results and agent state are versioned, written atomically, and kept
   in private files and directories. Older layouts are rejected rather than
   read through a compatibility path.
6. Before a live response is stored, the tool verifies the expected Ancestry
   address, rejects login and challenge pages, and validates the parsed shape.
   Searches durably distinguish matching results, explicit no-results pages,
   and a first page containing only unrelated names; completeness warnings make
   page-one negatives explicit. One latest validated snapshot is kept per
   logical page or query; `--fresh` atomically replaces it.

Current limits are deliberate and visible: searches read only the first page,
and there are no `up`, household-member navigation, or tab-cleanup commands.
Search-page validation distinguishes matching, explicit-empty, and unrelated
page-one outcomes. It also proves that Ancestry retained every requested filter
in the final URL. That verifies request retention, not the index's internal
matching semantics, so filtered results still require researcher review.

## FUTURE ideas — not CLI commands

The names below are planning vocabulary only. `./gen` rejects them today, and
scripts or agent prompts must not depend on them.

### Possible truth and reasoning commands

- `descendants`
- `recall`

### Possible projection and session commands

- `project`
- `log`
- `web`

If these are built, they should remain thin functions over canonical files and
rebuildable indexes. A useful first slice would have to reproduce an existing,
trusted conclusion—such as the Marjorie identity decision—before the system is
used for new conclusions.

## Design rules

- One honest entry point: `./gen <action> [args]`.
- JSON for command results, plain text for help.
- Offline inspection must be clearly distinguishable from a live paid-site
  request.
- Repository writes must pass the same validators and gate used by CI.
- Restricted source material stays outside tracked public files.
- The reviewed text records are authoritative; any graph is a disposable index.
- Prefer small functions over a framework, daemon, or hidden database state.

## Delivery order

Completed foundation:

1. Guarded Ancestry search, record, household, cache, and navigation commands.
2. Gate, build, and deploy-stamp wrappers.
3. Canonical evidence, source, case, and reasoning-trace files with validators.
4. Race-safe, versioned private acquisitions; offline-only mode; validated
   page parsing; and cursor-preserving navigation.
5. Canonical people and relationship files, strict family validation, and the
   generated public people registry, pedigree, and Index of Names.
6. Validated evidence and trace writes plus cross-store `show` and fast `status`
   commands.
7. Canonical case listing, family-edge updates, parent-gap resolution, ancestor
   frontiers and relationship paths.
8. Review-required evidence drafts from validated Ancestry record cache entries,
   including literal citation metadata and immutable cache provenance.

Next, if graph-backed searching proves useful:

1. Build a disposable CozoDB index from the canonical files. No loader or index
   exists yet.
2. Reproduce a trusted conclusion, such as the Marjorie identity decision.
3. Expose only the smallest graph-backed reasoning commands worth maintaining.
