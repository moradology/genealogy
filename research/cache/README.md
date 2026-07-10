# Durable acquisition store

`ancestry/` here is the cockpit's durable structured-data store: one JSON file
holding the latest validated snapshot for each logical page or query fetched
through `./gen ancestry` (record fields + household rows, a search's full result
set, or a collection landing page). Each atomic file is a versioned
`{"schema":"gen.ancestry.cache","version":3,"meta":...,"data":...}` envelope.
Metadata includes a SHA-256 of the canonical parsed payload, so the cache key
and fetch timestamp are backed by an immutable identity for the exact data used.
A normal later read, by any agent in any session, is served from here without
touching Ancestry. On a normal cache miss, the command automatically joins the
shared paced queue, rechecks the store inside the request lock, and then fetches
and stores the live result. No separate cache preflight is needed. `--fresh`
atomically replaces an existing snapshot. Simultaneous misses for the same page
are rechecked inside the shared request lock, so only one agent fetches and
writes it. Cache inspection and deletion take that same lock without triggering
request pacing, so they cannot race an in-progress acquisition.

Version 3 is a hard schema cutover. Run `./gen ancestry cache migrate` once to
convert version-2 entries explicitly; runtime reads never silently accept the
old shape. Search filters and validated negative outcomes are preserved.
Legacy record fields remain available, while their old household extraction is
marked incomplete and refresh-required rather than trusted. Migration never
contacts Ancestry.

The directory is **gitignored** (Ancestry ToS: index-derived data stays out of
the public repo) but lives in the repo tree so it travels with project backups.
Directories use private `0700` permissions and files use `0600`. Login pages,
challenge pages, wrong redirects, unconfirmed empty searches, and malformed
parsed results are rejected before a file is written. A valid results page whose
first page contains only unrelated names is cached explicitly as
`no-matching-results-on-page`, with incomplete-result warnings.

It is a durable latest-snapshot store, not a disposable performance cache.
`./gen ancestry cache clear` is normally used only with `--kind search` when an
index may have grown. Deleting record acquisitions requires both
`--include-records` and the exact confirmation phrase reported by a refused
clear; `--all` is held to the same rule. Inspect with
`./gen ancestry cache stats` / `cache list`.

Search snapshots carry an explicit outcome and result-set completeness:
`results`, `no-results`, or `no-matching-results-on-page`. The last outcome is
durable negative memory but remains incomplete because only page one was read.
Record snapshots carry `household_extraction` metadata (presence, parse
completeness, columns, method, dwelling-scope knowledge, and warnings) plus
literal `citation_metadata` when Ancestry exposed Source Citation or Source
Information text.

If an entry is malformed or from an older schema, stats and list report it but
never treat its contents as valid. A filtered clear refuses to guess its kind.
Only the fully guarded `cache clear --all --include-records --confirm ...` path
can remove an unclassifiable entry, treating it as cautiously as record data.

Pass `--cache-only` to `search`, `record`, `household`, `goto`, or `open` when
live access is forbidden. A miss then returns a JSON error without probing the
browser or sending a request. Do not use it as a routine preflight for normal
reads, which are already cache-first. It is mutually exclusive with `--fresh`.

This store is raw acquisition material. Durable *conclusions* belong in the
canonical evidence layer (`research/evidence/*.jsonl`), which is git-tracked
and privacy-reviewed.
