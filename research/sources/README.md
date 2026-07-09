# Source Index

`sources.jsonl` is the canonical, Git-tracked source registry. One explicit
source record lives on each line so parallel research work produces small,
reviewable diffs. `source-index.json` is its generated search projection.

Rebuild the search projection after editing `sources.jsonl`:

```sh
./gen build source-index
```

Check whether it is current:

```sh
./gen build source-index --check
```

The check also compares the public Source Ledger in `index.html` with the
canonical JSONL records. The presentation may never silently change source
titles, URLs, groups, or blurbs. The old HTML-to-JSON extraction path was
removed in the schema-2 hard cutover.

## Fields

- `id` - stable local source id used by reasoning traces; the readable slug comes from the title and the digest hashes the URL only.
- `html_id` - append-only public ledger code (`s1`, `s2`, ...), present in canonical JSONL but omitted from the generated search index.
- `group` - public Source Ledger section, present in canonical JSONL but omitted from the generated search index.
- `title` - source title from the HTML Source Ledger.
- `url` - source URL.
- `source_type` - explicitly reviewed coarse type used for filtering.
- `lineage_tags` - explicitly reviewed branch tags for retrieval.
- `evidence_role` - explicitly reviewed statement of how the source is used.
- `blurb` - short summary used for indexing.
- `search_text` - title plus blurb for simple full-text search.

## Source Types

Current broad source types include:

- `archival_record`
- `obituary`
- `cemetery_memorial`
- `public_tree_index`
- `church_record_target`
- `newspaper`
- `local_transcription`
- `compiled_pdf_or_journal`
- `compiled_tree_or_profile`
- `gazetteer_or_registry_context`
- `web_reference`

## Evidence Roles

- `evidence` - source directly states or lists a fact currently used in the artifact.
- `lead` - useful pointer, usually compiled or indexed.
- `research_target` - source points to a record set or next pull.
- `conflict_or_disambiguation` - source helps resolve a conflict or same-name problem.
- `context_not_proof` - source provides locality or background context only.
- `reference` - general reference.

## Search Examples

```sh
rg -n "Mainhardt|Zinkle|Archion" research/sources/source-index.json
rg -n "Sabanka|Lebehnke|Deutsch Krone" research/sources/source-index.json
rg -n "Frances Adolph|Rust|Winona|Strawn" research/sources/source-index.json
rg -n "\"lineage_tags\": \\[" research/sources/source-index.json
```

With `jq`:

```sh
jq -r '.sources[] | select(.lineage_tags[] == "zimmerman") | [.id, .title, .evidence_role] | @tsv' research/sources/source-index.json
jq -r '.sources[] | select(.evidence_role == "research_target") | [.id, .title, .blurb] | @tsv' research/sources/source-index.json
```

## Id stability

Source ids hash the URL only (the readable slug derives from the title). Blurb
edits never change ids; a title or URL change moves the id, and the migration
pattern in `id-migration-2026-07.json` should be repeated.
