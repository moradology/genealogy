# The researcher's cockpit

Status: PARTIALLY BUILT. This document separates the commands that work today
from ideas that still need design or implementation.

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
./gen build source-index --check
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

## BUILT command surface

### Repository maintenance

- `./gen gate` runs the same complete gate as CI.
- `./gen build <target> [--check]` builds or verifies one generated artifact.
  Targets are `basemap`, `fonts`, `citation-backlinks`, `plate-keys`, and
  `source-index`.
- `./gen stamp [--write|--check|--deployed]` manages the public-page content
  fingerprint. With no flag it checks the local stamp.

### Ancestry acquisition

These commands use the already-running, logged-in Chrome session; they never
launch a browser. A live read is shared, queued, and human-paced across agents.
Cached reads and the `where`, `next`, `prev`, and `back` commands do not contact
Ancestry. Add `--cache-only` when even a cache miss must remain offline;
`--cache-only` and `--fresh` cannot be combined.

```text
./gen ancestry search --collection N --name Given_Surname [--birth YEAR] [--limit K] [--fresh | --cache-only]
./gen ancestry record --collection N --id RECORD_ID [--fresh | --cache-only]
./gen ancestry household --collection N --id RECORD_ID [--fresh | --cache-only]

./gen ancestry goto <address> [--agent ID] [--fresh | --cache-only]
./gen ancestry open [N] [--agent ID] [--fresh | --cache-only]
./gen ancestry where [--agent ID]
./gen ancestry next [--agent ID]
./gen ancestry prev [--agent ID]
./gen ancestry back [--agent ID]

./gen ancestry cache stats [--kind K]
./gen ancestry cache list [--kind K]
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
- `search/COLL?name=Given_Surname&birth=YEAR`
- `collection/COLL`

Use `./gen ancestry --help` or, for example,
`./gen ancestry goto --help` for the full current contract.

## Ancestry safety and state — built now

The account is one shared, rate-sensitive resource. Agents should use only
`./gen ancestry` for these reads.

1. The machine-global queue and pacing state live under
   `~/.gen-cockpit/ancestry/`. Real requests take one inter-process lock, and a
   shared timestamp spaces requests across every agent.
2. Structured results live under `research/cache/ancestry/`. This directory is
   ignored by Git because the acquired material is restricted. Record and
   household views share the same stored record. `--fresh` intentionally
   bypasses a stored result; `--cache-only` turns a miss into an offline error.
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
   Searches must also contain a result matching the requested name or an
   explicit no-results message. One latest validated snapshot is kept per
   logical page or query; `--fresh` atomically replaces it.

Current limits are deliberate and visible: searches read only the first page,
and there are no `up`, household-member navigation, or tab-cleanup commands.
Search-page validation checks that at least one result resembles the requested
name, or that the page explicitly reports no results. The current page markup
does not let the tool independently prove that a birth-year filter remained
applied, so uncertain pages fail without being stored and birth-filtered results
still require researcher review.

## FUTURE ideas — not CLI commands

The names below are planning vocabulary only. `./gen` rejects them today, and
scripts or agent prompts must not depend on them.

### Canonical people and relationships

- Decide where people, names, parent-child links, unions, and identity claims
  are authored.
- Remove the remaining split between the public HTML and Python-held lists.
- Define the privacy and evidence rules for every relationship.

This decision comes before treating graph-backed cockpit answers as part of the
research workflow. It is intentionally still open for discussion; work on a
rebuildable graph index can proceed in parallel without settling it by accident.

### Possible truth and reasoning commands

- `add-evidence`, `add-node`, and `add-edge`
- `show` and `validate`
- `adjudicate`, `frontier`, and `contradictions`
- `ancestors`, `descendants`, and `path`
- `recall`

### Possible projection and session commands

- `project`
- `status`
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

Next, before expanding the command surface:

1. Agree on the canonical people-and-relationships model.
2. Only then expose the smallest graph-backed reasoning commands worth
   maintaining.
