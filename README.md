# Zimmerman-Dible Genealogy

Static working artifact for the Zimmerman-Dible ancestry research.

Live site: https://moradology.github.io/genealogy/

Repository: https://github.com/moradology/genealogy

## What This Is

This repo holds a shareable public-record research artifact for four grandparent anchors:

- Doyle Jule Zimmerman
- Evelyn Delores Mundell Zimmerman
- William J. "Bill" Dible
- Donna Lea Connelly Dible

The goal is breadth plus honesty. The public page presents the current working tree, confidence labels, map events, family-link geography, and next record targets. It is not a final proof tree. Open edges and compiled leads are intentionally marked as such.

## Main Files

- `index.html` - the hosted static artifact.
- `ancestry_geospatial.geojson` - machine-readable geography for verified events, temporal paths, research targets, and family links.
- `research/` - durable research memory, reasoning traces, and source indexes.
- `tools/build_source_index.py` - extracts the HTML Source Ledger into a searchable JSON source index.

## Research Memory

Research notes live under `research/` so useful reasoning does not get buried in chat history.

- `research/reasoning-traces/` captures fruitful chains of reasoning: question, hypothesis, evidence used, why the inference is plausible, why it is not proved, and the next record pull.
- `research/sources/source-index.json` lists every source currently in the artifact Source Ledger with a stable local id, URL, type, lineage tags, evidence role, blurb, and searchable text.
- `research/sources/README.md` documents the source-index fields and search patterns.

Use reasoning traces for memory when a path is worth preserving even if it is not yet proof. Use the source index for retrieval and cross-link traces to source ids.

## Evidence Language

The artifact uses these broad confidence labels:

- `documented` - supported by an obituary, cemetery profile, indexed record, or specific record collection.
- `strong` - repeated public tree/index/cemetery evidence with consistent people, places, and dates.
- `lead` - specific compiled or indexed evidence worth pursuing, but still awaiting original-record confirmation.
- `working` - useful compiled lead or indirect evidence; needs original proof.
- `possible` - hypothesis that must stay visually distinct from stronger evidence.
- `target` - record-search location rather than a proven life event.
- `open` - known gap or research edge.

## Data Model

`ancestry_geospatial.geojson` is a GeoJSON `FeatureCollection`.

Feature kinds currently include:

- `verified_event` - a mapped event asserted strongly enough to display.
- `record_target` - a place or repository target where a record pull could move the tree.
- `temporal_path` - a sequence of places through time for one branch or hypothesis.
- `family_link` - a relationship edge used by the map to show people converging into unions and unions carrying forward to descendants.

Important conventions:

- Coordinates are WGS84 longitude/latitude.
- Dates use ISO format when known; otherwise year or year-month plus `date_sort`.
- Preserve existing ids unless correcting an error.
- Keep speculative paths visually and structurally distinct from documented/strong paths.

## Source Index

Rebuild the source index after editing the Source Ledger in `index.html`:

```sh
python3 tools/build_source_index.py
```

Useful source searches:

```sh
rg -n "Mainhardt|Archion|Zinkle" research/sources/source-index.json
rg -n "Sabanka|Lebehnke|Zodrow" research/sources/source-index.json
rg -n "Frances Adolph|Rust|Winona" research/sources/source-index.json
```

## Local Checks

Run the single gate before committing:

```sh
sh tools/check.sh
```

It validates both JSON data files, regenerates and freshness-checks the source index,
verifies every cross-reference id resolves, syntax-checks the inline JavaScript, and runs
the full Playwright acceptance spec. CI runs the same script on every push.

## Publishing

The site is served by GitHub Pages from `main` at repository root.

Normal update flow:

```sh
git status -sb
python3 tools/build_source_index.py
python3 -m json.tool ancestry_geospatial.geojson >/dev/null
python3 -m json.tool research/sources/source-index.json >/dev/null
git add index.html ancestry_geospatial.geojson research tools README.md
git commit -m "Describe the genealogy update"
git push
```

GitHub Pages rebuilds automatically after push.

## Privacy

The artifact is public. Do not add private information about living people. Keep living descendants intentionally omitted unless explicit permission and a clear reason exist.
