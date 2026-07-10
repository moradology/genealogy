# Canonical family core

This directory is the single reviewed source for people and family connections.

- `people.jsonl` contains one real, deceased historical person per line. A person
  has a stable id, searchable names, family branch, research role, confidence,
  privacy state, and public-page anchor.
- `relationships.jsonl` contains 155 typed parent or spouse links and 18 explicit
  family gaps. Links carry their confidence and supporting evidence, source, or
  case references. Gaps describe unknown or disputed relatives without inventing
  placeholder people.

Life events and places do not belong here; they remain in
`ancestry_geospatial.geojson`.

After an edit, rebuild and verify the public projection:

```sh
./gen build people-index
./gen gate
```

`tools/check_family_core.py` checks the two files, their references, duplicate and
impossible links, parent cycles, privacy rules, and the generated public projection.
`./gen show` can inspect any `person.*`, `relationship.*`, or `gap.*` id and list
reverse references. `./gen status` reports validator health and family counts.

CozoDB is reserved for a possible future disposable search index. No loader or
database index exists yet, and such an index may never become research truth.
