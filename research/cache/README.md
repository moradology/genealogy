# Durable acquisition store

`ancestry/` here is the cockpit's durable structured-data store: one JSON file
per page ever fetched through `gen ancestry` (record fields + household rows,
or a search's full result set), wrapped in a `{"meta": ..., "data": ...}`
envelope with the fetch timestamp and source URL. The first hit is the last
hit — any later read, by any agent in any session, is served from here without
touching Ancestry.

The directory is **gitignored** (Ancestry ToS: index-derived data stays out of
the public repo) but lives in the repo tree so it travels with project backups.
It is an acquisitions log, not a cache to evict: `gen ancestry cache clear` is
guarded and normally only used with `--kind search` when an index may have
grown. Inspect with `gen ancestry cache stats` / `cache list`.

This store is raw acquisition material. Durable *conclusions* belong in the
canonical evidence layer (`research/evidence/*.jsonl`), which is git-tracked
and privacy-reviewed.
