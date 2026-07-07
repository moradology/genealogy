# Source Index

`source-index.json` is the machine-readable source listing for this project.

It is generated from the `index.html` Source Ledger:

```sh
python3 tools/build_source_index.py
```

Check whether it is current:

```sh
python3 tools/build_source_index.py --check
```

## Fields

- `id` - stable local source id used by reasoning traces. It is generated from source title, URL, and blurb so adding another source does not renumber existing entries.
- `title` - source title from the HTML Source Ledger.
- `url` - source URL.
- `source_type` - coarse type used for filtering.
- `lineage_tags` - inferred branch tags for retrieval.
- `evidence_role` - how the source is currently being used.
- `blurb` - short summary used for indexing.
- `search_text` - title plus blurb for simple full-text search.

## Source Types

Current broad source types include:

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
