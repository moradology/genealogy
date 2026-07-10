# Canonical family core

This directory is the single reviewed source for people and family connections.

- `people.jsonl` contains one real, deceased historical person per line. A person
  has a stable id, searchable names, family branch, research role, confidence,
  privacy state, and public-page anchor.
- `relationships.jsonl` contains 155 typed parent or spouse links and 18 explicit
  family gaps. Links carry their confidence and supporting evidence, source, or
  case references. Gaps describe unknown or disputed relatives without inventing
  placeholder people.

Relationship `status` is `accepted`, `hypothesis`, or `rejected`. Rejected
relationships remain canonical and inspectable: resolution evidence is unioned
into their typed refs and a dated rejection is appended to the original
provenance note. Graph traversal and pedigree projection ignore them.

Every gap has an explicit lifecycle. `status` is `open` or `resolved`;
`resolution_note` records the durable adjudication, `resolved_on` is an ISO date
or null, and `owner_follow_up_required` says whether the hand-authored public
card still needs revision. Evidence, source, and case support remains in the
typed `*_refs` fields. A resolved public gap remains as a canonical tombstone:
it keeps its stable id and `public_anchor`, but has no open roles, candidates,
or pedigree slots. This prevents stale page anchors and historical references
from becoming dangling ids while keeping it off the active ancestor frontier.

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
