# Durable acquisition store

`ancestry/` here is the cockpit's durable structured-data store: one JSON file
holding the latest validated snapshot for each logical page or query fetched
through `./gen ancestry` (record fields + household rows, a search's full result
set, or a collection landing page). Each atomic file is a versioned
`{"schema":"gen.ancestry.cache","version":2,"meta":...,"data":...}` envelope.
A normal later read, by any agent in any session, is served from here without
touching Ancestry. `--fresh` atomically replaces that snapshot. Simultaneous
misses for the same page are rechecked inside the shared request lock, so only
one agent fetches and writes it. Cache inspection and deletion take that same
lock without triggering request pacing, so they cannot race an in-progress
acquisition.

The directory is **gitignored** (Ancestry ToS: index-derived data stays out of
the public repo) but lives in the repo tree so it travels with project backups.
Directories use private `0700` permissions and files use `0600`. Login pages,
challenge pages, wrong redirects, unrelated search results, unconfirmed empty
searches, and malformed parsed results are rejected before a file is written.

It is a durable latest-snapshot store, not a disposable performance cache.
`./gen ancestry cache clear` is normally used only with `--kind search` when an
index may have grown. Deleting record acquisitions requires both
`--include-records` and the exact confirmation phrase reported by a refused
clear; `--all` is held to the same rule. Inspect with
`./gen ancestry cache stats` / `cache list`.

If an entry is malformed or from an older schema, stats and list report it but
never treat its contents as valid. A filtered clear refuses to guess its kind.
Only the fully guarded `cache clear --all --include-records --confirm ...` path
can remove an unclassifiable entry, treating it as cautiously as record data.

Pass `--cache-only` to `search`, `record`, `household`, `goto`, or `open` when
live access is forbidden. A miss then returns a JSON error without probing the
browser or sending a request. It is mutually exclusive with `--fresh`.

This store is raw acquisition material. Durable *conclusions* belong in the
canonical evidence layer (`research/evidence/*.jsonl`), which is git-tracked
and privacy-reviewed.
