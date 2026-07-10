# Canonical evidence store

These JSONL files are the source of truth for acquired evidence. The store is
sharded by family branch so researchers can add records on separate branches
without editing the same file:

- `zimmerman.jsonl`
- `mundell.jsonl`
- `dible.jsonl`
- `connelly.jsonl`

Each nonblank line is exactly one JSON object and one logical acquisition. The
initial July 2026 migration therefore has 23 records, not 24: the two local
directories beginning with `01-` are duplicate captures of the same 1910 census
record and are represented by the single id `ev.ancestry.1910-zodrow`. New pulls
may append to that batch without changing the first 23 logical acquisitions.

The old pull notes and the HTML Source Ledger are not alternate evidence formats.
They may explain where migrated data came from, but tools must read this JSONL
shape only. A format change is a hard migration of every record and validator in
one change; do not add fallback readers.

## Record contract

Every record has these fields:

| Field | Contract |
|---|---|
| `id` | Stable `ev.*` id. Never recycle an id for a different acquisition. |
| `record_type` | One of `census`, `church_register`, `death_index`, `divorce`, `marriage`, `obituary_index`, `probate`, `record_bundle`, or `search_log`. |
| `title` | Short human-readable title. |
| `repository` | Archival custodian or index publisher, plus access platform where relevant. |
| `citation` | Exact archival citation when preserved; otherwise the most exact collection, record id, or negative-search citation available. |
| `citation_gap` | Optional, required by practice whenever page-, roll-, or repository-level detail is known to be missing. |
| `accessed` | ISO date of acquisition. |
| `status` | `found`, `partial`, or `not_found`. |
| `confidence` | `high`, `medium`, `low`, or `not_applicable`; confidence in what was captured, not in an unproved identity theory. |
| `supports`, `opposes` | Edge-ready `person.*` or `case.*` ids. Keep empty when a record merely informs a question and does not support or oppose the whole referenced node. |
| `person_refs`, `case_refs` | Complete current subject/case index for the record. Every support/oppose endpoint must also appear here. |
| `privacy_review` | Required attestation that possibly living people and sensitive identifiers were excluded from tracked text. |
| `acquisition` | Provider, batch, unique two-digit logical pull number, and zero or more ignored local pull directories. Open-web records use an empty list when no local artifact was retained. |
| `cache_provenance` | Optional structured provenance for a record drafted from the private Ancestry acquisition store: canonical `record/COLL/ID` address, validated cache key/schema/version, immutable payload SHA-256, fetch timestamp, and requested/final URLs. The key locates a mutable latest snapshot; the digest identifies the exact parsed payload used. URL-less legacy acquisitions retain null URLs plus an explicit `url_gap`; URLs are never reconstructed or guessed. |
| `source_urls` | Original record URLs when available. URLs are leads, never substitutes for citations. |
| `transcription` | Concise, privacy-safe transcription or abstract of the material facts and conflicts. |
| `local_assets` | Optional ignored files under `research/pulls/`, each with a role and optional SHA-256 checksum. |

`supports` and `opposes` deliberately target only current person and case ids. A
future claim layer may add claim edges through a deliberate schema cutover; unknown
id types are rejected today rather than silently retained.

## Privacy and local files

Tracked evidence must not contain a full Social Security number or the name of a
person who may still be living. Use a neutral description such as “younger sibling”
or “surviving relative.” A record may name someone only when the project has
evidence that the person is deceased or the date makes survival impossible.

Raw subscription images remain ignored by Git. `local_assets` provides a stable
inventory without publishing the images. The normal check validates paths and
verifies checksums for files that are present. Run the stronger local audit when
the subscription pulls are mounted:

```sh
uv run tools/check_evidence.py --require-local-assets
```

That mode requires every listed directory and asset to exist. A fresh clone can
run the normal gate without access to private images.

## Known citation gaps in the migrated batch

The source notes did not preserve enough metadata to make every citation complete:

- Pulls 03 and 15 are documented searches with no located record, so their
  citations describe the exact collections and searches rather than an archival
  item.
- Pulls 13 and 14 captured obituary index entries only. The full newspaper pages
  were behind an additional subscription, and survivor names were intentionally
  not retained.
- Pulls 17, 18, and 20 lack the census enumeration district and NARA roll in the
  notes. Collection record ids, places, sheets, and households were retained where
  known.
- Pull 21 did not preserve a fuller Social Security Administration source-file
  citation. Its full identifier is intentionally excluded even though a private
  local screenshot still exists.
- Pulls 22 and 23 lack page-level census citations for their candidate bundles.
  The collection and record ids are retained, and the bundles remain negative
  memory rather than lineage proof.
- Pull 12 did not locate the sought original 1895 marriage. Its record contains the
  exact 1900 census and 1917 derivative marriage citations that were actually
  captured.

Close a gap by editing the canonical record and removing or narrowing its
`citation_gap`; do not reconstruct missing details by guessing.

## Drafting from the Ancestry acquisition store

`./gen evidence draft --from-cache record/COLL/ID --id ev.ID` reads one already-cached,
validated record and emits a canonical-shaped evidence draft with citation
fields and `cache_provenance`. It never falls back to a live request. The draft
deliberately carries a pending privacy review and placeholder transcription, so
passing it unchanged to `evidence add` fails. Review the record, exclude living
people and sensitive identifiers, correct the citation and interpretation, set
canonical subject/case refs, and only then attest `privacy_review.status` as
`passed`. A migrated legacy record that never retained acquisition URLs still
produces a draft: its provenance contains the canonical record address, null URL
fields, and an explicit `url_gap`/refresh warning rather than a fabricated URL.

## Validation

`tools/check_evidence.py` uses only the Python standard library. It rejects schema
drift, bad or duplicate ids, duplicate logical pulls, unresolved person/case refs,
privacy-attestation failures, Social Security number patterns, unsafe local paths,
and checksum mismatches. Its regression suite is `tools/test_check_evidence.py`.
