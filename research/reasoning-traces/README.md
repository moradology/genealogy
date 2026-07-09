# Reasoning Traces

Reasoning traces preserve both active research paths and completed proof arguments.

Use `template.md` for new traces. Every dated trace uses the same strict, single-line
frontmatter contract and is checked by `tools/check_traces.py`:

- `id`, `title`, `date`, `status`, and `confidence`
- `case_refs`, `person_refs`, `evidence_refs`, `source_refs`, and `geo_refs`
- `outcome` and one concrete `next_action`

Reference arrays use canonical ids only. Cases, evidence, and sources resolve through
their JSONL stores; people resolve through the HTML/GeoJSON person universe; geographic
events, targets, paths, and links resolve through `ancestry_geospatial.geojson`. Keep
arrays sorted and use JSON array/string syntax on one line. Do not restore the legacy
`date_created`, `people`, `places`, `source_ids`, or `geojson_ids` fields.

## Status Values

- `active` - current high-value path.
- `parked` - useful but not next in line.
- `resolved` - proved or disproved and incorporated into the main artifact.
- `rejected` - plausible path that was ruled out.

## Confidence Values

- `documented`
- `strong`
- `lead`
- `working`
- `possible`
- `open`

## Current Traces

All date-prefixed Markdown files in this directory are canonical traces. The validator
rejects undated trace filenames and missing or legacy frontmatter.
