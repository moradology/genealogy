#!/usr/bin/env python3
"""Write-side and orientation verbs for the genealogy research stores."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

import build_docket  # noqa: E402
import build_people_index  # noqa: E402
import check_cases  # noqa: E402
import check_evidence  # noqa: E402
import check_family_core  # noqa: E402
import check_traces  # noqa: E402
import family_rules  # noqa: E402
import stamp as stamp_tool  # noqa: E402


SHARDS = ("zimmerman", "mundell", "dible", "connelly")
KINDS = (
    "case",
    "evidence",
    "source",
    "trace",
    "geo",
    "person",
    "relationship",
    "gap",
)
TRACE_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TRACE_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
TRACE_ID_RE = re.compile(
    r"trace\.\d{4}-\d{2}-\d{2}\.[a-z0-9]+(?:-[a-z0-9]+)*\Z"
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def stop(payload: dict[str, Any], code: int) -> int:
    emit(payload)
    return code


def root_path() -> Path:
    override = os.environ.get("GEN_STORE_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[1]


def today() -> str:
    return dt.date.today().isoformat()


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evidence_path(root: Path, shard: str) -> Path:
    return root / "research" / "evidence" / f"{shard}.jsonl"


def evidence_rows(root: Path) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for shard in SHARDS:
        for record in read_jsonl(evidence_path(root, shard)):
            rows.append((shard, record))
    return rows


def load_json_stdin() -> tuple[bool, Any]:
    raw = sys.stdin.read()
    completed = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        input=raw,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or "stdin is not valid JSON"
        return False, message
    return True, json.loads(completed.stdout)


def privacy_attested(record: dict[str, Any]) -> bool:
    review = record.get("privacy_review")
    return isinstance(review, dict) and review.get("status") == "passed"


def fill_evidence_defaults(
    record: dict[str, Any], rows: list[tuple[str, dict[str, Any]]]
) -> tuple[list[str], str | None]:
    if "accessed" not in record:
        record["accessed"] = today()
    if "opposes" not in record:
        record["opposes"] = []
    if "local_assets" not in record:
        record["local_assets"] = []

    acquisition = record.get("acquisition")
    if not isinstance(acquisition, dict):
        return [], None

    pull = acquisition.get("pull")
    if pull is not None and pull != "auto":
        return [], pull if isinstance(pull, str) else None

    batch = acquisition.get("batch")
    if not isinstance(batch, str) or not batch:
        return ["acquisition.batch is required to auto-assign acquisition.pull"], None

    maximum = 0
    for _shard, existing in rows:
        existing_acquisition = existing.get("acquisition")
        if not isinstance(existing_acquisition, dict):
            continue
        if existing_acquisition.get("batch") != batch:
            continue
        existing_pull = existing_acquisition.get("pull")
        if (
            isinstance(existing_pull, str)
            and len(existing_pull) == 2
            and existing_pull.isdigit()
        ):
            maximum = max(maximum, int(existing_pull))

    next_pull = maximum + 1
    if next_pull > 99:
        return [f"acquisition.pull for batch {batch!r} would exceed 99"], None
    acquisition["pull"] = f"{next_pull:02d}"
    return [], acquisition["pull"]


def append_record_bytes(original: bytes, record: dict[str, Any]) -> bytes:
    separator = b"" if not original or original.endswith(b"\n") else b"\n"
    return original + separator + compact_json(record).encode("utf-8") + b"\n"


def store_lock_path(root: Path) -> Path:
    return root / "research" / ".store.lock"


def atomic_replace(path: Path, data: bytes) -> None:
    """Write-temp-then-rename in the same directory: readers see the old or the
    new complete file, never a partial write. Concurrent cockpit writers are
    already serialized by the store flock."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def atomic_create(path: Path, data: bytes) -> None:
    """Publish a complete new file without ever replacing an existing path.

    The payload is written and synced under a unique, exclusively-created
    temporary name in the destination directory. Linking that inode into its
    final name is atomic and fails with ``FileExistsError`` if anything already
    owns the destination, including a writer that does not honor our flock.
    """
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def validate_candidate_evidence(root: Path, shard: str, candidate: bytes):
    """Validate the WOULD-BE store in a temp directory: the real shards are
    never dirtied by unvalidated or unattested records (no revert window)."""
    evidence_dir = root / "research" / "evidence"
    with tempfile.TemporaryDirectory(prefix="gen-store-validate-") as td:
        tdir = Path(td)
        for entry in evidence_dir.iterdir():
            if entry.is_file():
                (tdir / entry.name).write_bytes(entry.read_bytes())
        (tdir / f"{shard}.jsonl").write_bytes(candidate)
        return check_evidence.validate_repository(root=root, evidence_dir=tdir)


def validate_candidate_trace(root: Path, filename: str, content: str):
    """Same pattern for traces: validate the would-be trace dir in a temp copy
    before the real file is ever created."""
    trace_dir = root / "research" / "reasoning-traces"
    with tempfile.TemporaryDirectory(prefix="gen-store-validate-") as td:
        tdir = Path(td)
        for entry in trace_dir.iterdir():
            if entry.is_file():
                (tdir / entry.name).write_bytes(entry.read_bytes())
        (tdir / filename).write_text(content, encoding="utf-8")
        return check_traces.validate_repository(root=root, trace_dir=tdir)


def command_evidence_add(args: argparse.Namespace, root: Path) -> int:
    if args.shard not in SHARDS:
        return stop(
            {
                "command": "evidence.add",
                "ok": False,
                "errors": [f"unknown evidence shard {args.shard!r}"],
            },
            1,
        )

    parsed, value = load_json_stdin()
    if not parsed:
        return stop(
            {"command": "evidence.add", "ok": False, "errors": [str(value)]},
            1,
        )
    if not isinstance(value, dict):
        return stop(
            {
                "command": "evidence.add",
                "ok": False,
                "errors": ["stdin must be one JSON object"],
            },
            1,
        )

    record = value
    if not privacy_attested(record):
        return stop(
            {
                "command": "evidence.add",
                "ok": False,
                "errors": [
                    "privacy attestation is required: privacy_review.status must be 'passed'"
                ],
            },
            1,
        )

    # The store flock serializes every cockpit writer across the whole
    # read -> assign-pull -> validate -> write sequence: no lost writes, no
    # duplicate auto-assigned pulls. Released on close, including on crash.
    with open(store_lock_path(root), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        rows = evidence_rows(root)
        record_id = record.get("id")
        if any(existing.get("id") == record_id for _shard, existing in rows):
            return stop(
                {
                    "command": "evidence.add",
                    "ok": False,
                    "errors": [f"evidence id already exists: {record_id!r}"],
                },
                1,
            )

        fill_errors, pull = fill_evidence_defaults(record, rows)
        if fill_errors:
            return stop(
                {"command": "evidence.add", "ok": False, "errors": fill_errors},
                1,
            )

        path = evidence_path(root, args.shard)
        original = path.read_bytes()
        candidate = append_record_bytes(original, record)
        result = validate_candidate_evidence(root, args.shard, candidate)

        if not result.ok:
            return stop(
                {
                    "command": "evidence.add",
                    "ok": False,
                    "written": False,
                    "errors": list(result.errors),
                },
                1,
            )
        if args.validate_only:
            return stop(
                {
                    "command": "evidence.add",
                    "ok": True,
                    "written": False,
                    "id": record_id,
                    "shard": args.shard,
                    "pull": pull,
                },
                0,
            )

        atomic_replace(path, candidate)
        return stop(
            {
                "command": "evidence.add",
                "ok": True,
                "written": True,
                "id": record_id,
                "shard": args.shard,
                "pull": pull,
            },
            0,
        )


def csv_refs(raw: str | None) -> list[str]:
    if raw is None or not raw.strip():
        return []
    return sorted(part.strip() for part in raw.split(",") if part.strip())


def trace_list(raw: str | None) -> str:
    return json.dumps(csv_refs(raw), ensure_ascii=False)


def trace_body_from_template(root: Path, title: str) -> str:
    template = (
        root / "research" / "reasoning-traces" / "template.md"
    ).read_text(encoding="utf-8")
    lines = template.splitlines()
    closing = lines.index("---", 1)
    body_lines = lines[closing + 1 :]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    return "\n".join(body_lines).replace("Short Trace Title", title).rstrip() + "\n"


def command_trace_new(args: argparse.Namespace, root: Path) -> int:
    if not TRACE_SLUG_RE.fullmatch(args.slug):
        return stop(
            {
                "command": "trace.new",
                "ok": False,
                "errors": ["slug must be lowercase words separated by hyphens"],
            },
            1,
        )
    if not TRACE_DATE_RE.fullmatch(args.date):
        return stop(
            {
                "command": "trace.new",
                "ok": False,
                "errors": ["date must use YYYY-MM-DD"],
            },
            1,
        )

    trace_dir = root / "research" / "reasoning-traces"
    filename = f"{args.date}-{args.slug}.md"
    path = trace_dir / filename
    trace_id = f"trace.{args.date}.{args.slug}"
    outcome = args.outcome or "Current result, including what remains unproved."
    next_action = args.next_action or "One concrete next research action."
    fields = [
        "---",
        f"id: {trace_id}",
        f"title: {json.dumps(args.title, ensure_ascii=False)}",
        f"date: {args.date}",
        "status: active",
        f"confidence: {args.confidence}",
        f"case_refs: {trace_list(args.case_refs)}",
        f"person_refs: {trace_list(args.person_refs)}",
        f"evidence_refs: {trace_list(args.evidence_refs)}",
        f"source_refs: {trace_list(args.source_refs)}",
        f"geo_refs: {trace_list(args.geo_refs)}",
        f"outcome: {json.dumps(outcome, ensure_ascii=False)}",
        f"next_action: {json.dumps(next_action, ensure_ascii=False)}",
        "---",
        "",
    ]
    if args.body_file is not None:
        body_path = Path(args.body_file)
        if not body_path.is_file():
            return stop(
                {"command": "trace.new", "ok": False,
                 "errors": [f"body file not found: {args.body_file}"]},
                1,
            )
        body = body_path.read_text(encoding="utf-8")
        if not body.strip():
            return stop(
                {"command": "trace.new", "ok": False, "errors": ["body file is empty"]},
                1,
            )
        body = body.rstrip() + "\n"
    else:
        body = trace_body_from_template(root, args.title)
    content = "\n".join(fields) + body

    # Existence check, validation, and creation all happen under the store
    # flock, and the validation runs against a temp copy of the trace dir: the
    # real file is only ever created AFTER it validates, so a failure leaves
    # nothing behind and a concurrent same-slug create cannot overwrite or
    # unlink another process's file.
    with open(store_lock_path(root), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        if path.exists():
            return stop(
                {
                    "command": "trace.new",
                    "ok": False,
                    "errors": [f"trace already exists: {filename}"],
                },
                1,
            )

        result = validate_candidate_trace(root, filename, content)
        if not result.ok:
            return stop(
                {"command": "trace.new", "ok": False, "errors": list(result.errors)},
                1,
            )

        try:
            atomic_create(path, content.encode("utf-8"))
        except FileExistsError:
            return stop(
                {
                    "command": "trace.new",
                    "ok": False,
                    "errors": [f"trace already exists: {filename}"],
                },
                1,
            )
        return stop(
            {
                "command": "trace.new",
                "ok": True,
                "path": str(path.relative_to(root)),
                "id": trace_id,
            },
            0,
        )


def trace_documents(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    documents: list[tuple[Path, dict[str, Any]]] = []
    trace_dir = root / "research" / "reasoning-traces"
    for path in sorted(trace_dir.glob("*.md")):
        if path.name in check_traces.SKIPPED_NAMES:
            continue
        errors: list[str] = []
        parsed = check_traces.parse_trace(path.read_text(encoding="utf-8"), path.name, errors)
        if parsed is not None:
            fields = dict(parsed.fields)
            fields["path"] = str(path.relative_to(root))
            fields["filename"] = path.name
            documents.append((path, fields))
    return documents


def trace_id_index(root: Path) -> dict[str, str]:
    """Map each canonical trace identity to its on-disk document name."""

    return {
        fields["id"]: path.name
        for path, fields in trace_documents(root)
        if isinstance(fields.get("id"), str)
    }


def canonical_trace_refs(
    root: Path, refs: list[str]
) -> tuple[list[str], list[str]]:
    """Validate canonical trace ids without accepting filename aliases."""

    index = trace_id_index(root)
    resolved: list[str] = []
    errors: list[str] = []
    for ref in refs:
        if not TRACE_ID_RE.fullmatch(ref):
            errors.append(
                f"trace ref must be a canonical trace.<date>.<slug> id: {ref!r}"
            )
        elif ref not in index:
            errors.append(f"unknown trace id {ref!r}")
        else:
            resolved.append(ref)
    return resolved, errors


def people_records(root: Path) -> list[dict[str, Any]]:
    return read_jsonl(root / "research" / "people" / "people.jsonl")


def family_records(root: Path) -> list[dict[str, Any]]:
    return read_jsonl(root / "research" / "people" / "relationships.jsonl")


def geo_records(root: Path) -> list[tuple[str, dict[str, Any]]]:
    geo = json.loads((root / "ancestry_geospatial.geojson").read_text(encoding="utf-8"))
    records: list[tuple[str, dict[str, Any]]] = []
    for feature in geo.get("features", []):
        if isinstance(feature, dict) and isinstance(feature.get("id"), str):
            records.append((feature["id"], feature))
    registry = geo.get("place_registry") or {}
    if isinstance(registry, dict):
        for key, value in registry.items():
            if isinstance(value, dict):
                record = {"id": key, **value}
            else:
                record = {"id": key, "value": value}
            records.append((key, record))
    return records


def resolve_id(root: Path, wanted: str) -> tuple[str | None, dict[str, Any] | None, set[str]]:
    for record in read_jsonl(root / "research" / "cases" / "cases.jsonl"):
        if record.get("id") == wanted:
            return "case", record, {wanted}

    for shard, record in evidence_rows(root):
        if record.get("id") == wanted:
            return "evidence", record, {wanted}

    for record in read_jsonl(root / "research" / "sources" / "sources.jsonl"):
        if record.get("id") == wanted:
            return "source", record, {wanted}

    for path, fields in trace_documents(root):
        aliases = {fields["id"], path.name, str(path.relative_to(root))}
        if wanted in aliases:
            return "trace", fields, aliases

    for geo_id, record in geo_records(root):
        if geo_id == wanted:
            return "geo", record, {wanted}

    for record in people_records(root):
        if record.get("id") == wanted:
            return "person", record, {wanted}

    for record in family_records(root):
        if record.get("id") == wanted:
            kind = "gap" if record.get("node_type") == "gap" else "relationship"
            return kind, record, {wanted}

    return None, None, {wanted}


def record_refs(record: dict[str, Any], fields: tuple[str, ...]) -> set[str]:
    refs: set[str] = set()
    for field in fields:
        value = record.get(field)
        if isinstance(value, list):
            refs.update(item for item in value if isinstance(item, str))
    return refs


def nested_strings(value: Any):
    """Yield exact string values from a JSON-shaped record."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from nested_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from nested_strings(nested)


def referenced_by(root: Path, aliases: set[str]) -> dict[str, list[str]]:
    cases: list[str] = []
    for record in read_jsonl(root / "research" / "cases" / "cases.jsonl"):
        refs = record_refs(record, ("evidence_refs", "person_refs", "trace_refs"))
        if refs & aliases and isinstance(record.get("id"), str):
            cases.append(record["id"])

    evidence: list[str] = []
    for _shard, record in evidence_rows(root):
        refs = record_refs(record, ("supports", "opposes", "person_refs", "case_refs"))
        if refs & aliases and isinstance(record.get("id"), str):
            evidence.append(record["id"])

    traces: list[str] = []
    for _path, fields in trace_documents(root):
        refs = record_refs(
            fields,
            ("case_refs", "person_refs", "evidence_refs", "source_refs", "geo_refs"),
        )
        if refs & aliases and isinstance(fields.get("id"), str):
            traces.append(fields["id"])

    relationships: list[str] = []
    for record in family_records(root):
        refs = record_refs(
            record,
            (
                "evidence_refs",
                "source_refs",
                "case_refs",
                "subject_persons",
                "candidate_persons",
            ),
        )
        for field in ("person_a", "person_b"):
            value = record.get(field)
            if isinstance(value, str):
                refs.add(value)
        if refs & aliases and isinstance(record.get("id"), str):
            relationships.append(record["id"])

    geo: list[str] = []
    for geo_id, record in geo_records(root):
        # Feature ids are definitions; only their content can refer to another
        # record. Exact-value matching avoids treating names or URLs as ids.
        content = record.get("properties", record)
        if set(nested_strings(content)) & aliases:
            geo.append(geo_id)

    return {
        "cases": sorted(cases),
        "evidence": sorted(evidence),
        "traces": sorted(traces),
        "relationships": sorted(relationships),
        "geo": sorted(set(geo)),
    }


def family_core(root: Path) -> tuple[dict[str, dict], list[dict], list[dict]]:
    """People by id, parent/spouse relationship links, and gap rows."""
    people = {
        r["id"]: r
        for r in read_jsonl(root / "research" / "people" / "people.jsonl")
        if r.get("node_type") == "person"
    }
    rows = read_jsonl(root / "research" / "people" / "relationships.jsonl")
    links = [
        r
        for r in rows
        if r.get("node_type") == "relationship"
        and r.get("status") != "rejected"
    ]
    gaps = [r for r in rows if r.get("node_type") == "gap"]
    return people, links, gaps


def parents_of_index(links: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for link in links:
        if link.get("relationship_type") == "parent_of":
            index.setdefault(link["person_b"], []).append(link)
    return index


def gaps_for(gaps: list[dict], person_id: str) -> list[dict]:
    return [
        {"id": g["id"], "label": g.get("label"), "open_roles": g.get("open_roles", []),
         "case_refs": g.get("case_refs", [])}
        for g in gaps
        if person_id in (g.get("subject_persons") or [])
    ]


def command_ancestors(args: argparse.Namespace, root: Path) -> int:
    people, links, gaps = family_core(root)
    if args.person_id not in people:
        return stop({"command": "ancestors", "ok": False,
                     "errors": [f"unknown person id {args.person_id!r}"]}, 1)
    parents = parents_of_index(links)
    generations: list[list[dict]] = []
    frontier: list[dict] = []
    seen = {args.person_id}
    current = [args.person_id]
    while current:
        layer: list[dict] = []
        next_ids: list[str] = []
        for person_id in current:
            for link in parents.get(person_id, []):
                parent_id = link["person_a"]
                if parent_id in seen:
                    continue
                seen.add(parent_id)
                next_ids.append(parent_id)
                layer.append({
                    "id": parent_id,
                    "name": people.get(parent_id, {}).get("display_name"),
                    "child": person_id,
                    "role": link.get("parent_role"),
                    "confidence": link.get("confidence"),
                    "via": link["id"],
                })
            for gap in gaps_for(gaps, person_id):
                if (
                    set(gap["open_roles"]) & {"father", "mother", "parents"}
                    and gap not in frontier
                ):
                    frontier.append(gap)
        if layer:
            generations.append(layer)
        current = next_ids
    return stop({
        "command": "ancestors", "ok": True, "id": args.person_id,
        "name": people[args.person_id].get("display_name"),
        "generations": generations,
        "count": sum(len(layer) for layer in generations),
        "frontier": frontier,
    }, 0)


def command_path(args: argparse.Namespace, root: Path) -> int:
    people, links, _gaps = family_core(root)
    for pid in (args.person_a, args.person_b):
        if pid not in people:
            return stop({"command": "path", "ok": False,
                         "errors": [f"unknown person id {pid!r}"]}, 1)
    neighbors: dict[str, list[tuple[str, dict]]] = {}
    for link in links:
        a, b = link.get("person_a"), link.get("person_b")
        if not isinstance(a, str) or not isinstance(b, str):
            continue
        neighbors.setdefault(a, []).append((b, link))
        neighbors.setdefault(b, []).append((a, link))
    origin, goal = args.person_a, args.person_b
    if origin == goal:
        return stop({"command": "path", "ok": True, "steps": [], "length": 0}, 0)
    came: dict[str, tuple[str, dict]] = {}
    queue = [origin]
    seen = {origin}
    while queue and goal not in seen:
        person_id = queue.pop(0)
        for other, link in neighbors.get(person_id, []):
            if other in seen:
                continue
            seen.add(other)
            came[other] = (person_id, link)
            queue.append(other)
    if goal not in came:
        return stop({"command": "path", "ok": False,
                     "errors": [f"no relationship path between {origin} and {goal}"]}, 1)
    steps: list[dict] = []
    cursor = goal
    while cursor != origin:
        previous, link = came[cursor]
        steps.append({
            "from": previous, "to": cursor,
            "from_name": people.get(previous, {}).get("display_name"),
            "to_name": people.get(cursor, {}).get("display_name"),
            "relationship": link.get("relationship_type"),
            "role": link.get("parent_role"),
            "confidence": link.get("confidence"),
            "via": link.get("id"),
        })
        cursor = previous
    steps.reverse()
    return stop({"command": "path", "ok": True, "from": origin, "to": goal,
                 "length": len(steps), "steps": steps}, 0)


def command_contradictions(args: argparse.Namespace, root: Path) -> int:
    report = family_rules.contradictions(root)
    code = 1 if args.strict and report["counts"]["violation"] else 0
    return stop({"command": "contradictions", "ok": code == 0, **report}, code)


def command_adjudicate(args: argparse.Namespace, root: Path) -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return stop({"command": "adjudicate", "ok": False,
                     "errors": ["expected a claim JSON object on stdin"]}, 1)
    report = family_rules.adjudicate(root, json.loads(raw))
    if report.get("errors"):
        return stop({"command": "adjudicate", "ok": False, **report}, 1)
    return stop({"command": "adjudicate", "ok": True, **report}, 0)


def command_show(args: argparse.Namespace, root: Path) -> int:
    kind, record, aliases = resolve_id(root, args.id)
    if kind is None or record is None:
        return stop(
            {
                "command": "show",
                "ok": False,
                "id": args.id,
                "searched": list(KINDS),
            },
            1,
        )

    return stop(
        {
            "command": "show",
            "ok": True,
            "id": args.id,
            "kind": kind,
            "record": record,
            "referenced_by": referenced_by(root, aliases),
        },
        0,
    )


def validate_case_records(root: Path, records: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Semantic validation of a CANDIDATE case list against the real repo
    context — the docket byte contract is guaranteed separately, by rendering
    through the same build_docket.render path the gate checks."""
    trace_ids = check_cases.canonical_trace_ids(
        root / "research" / "reasoning-traces"
    )
    failures = check_cases.core_failures(
        records,
        check_cases.canonical_gaps(
            root / "research" / "people" / "relationships.jsonl"
        ),
        check_cases.canonical_person_ids(
            root / "research" / "people" / "people.jsonl"
        ),
        check_cases.evidence_case_index(root),
        trace_ids,
    )
    frames_root = root / "research" / "search-frames"
    for path in sorted((frames_root / "uncased").glob("*.md")):
        failures.append(
            f"uncased search frame remains after case cutover: {path.relative_to(root)}"
        )
    case_ids = {record["id"] for record in records}
    for path in sorted(frames_root.glob("case.*")):
        if path.is_dir() and path.name not in case_ids:
            failures.append(
                f"search-frame directory has no canonical case: {path.relative_to(root)}"
            )
    return not failures, failures


def validate_cases(root: Path) -> tuple[bool, list[str]]:
    return validate_case_records(root, read_jsonl(root / "research" / "cases" / "cases.jsonl"))


CASE_SCALAR_FLAGS = ("status", "summary", "display_prose", "source_note")
CASE_ADD_FLAGS = ("evidence_refs", "trace_refs", "person_refs")
CASE_STATUSES = ("open", "in_conflict", "needs_pull", "closed")
CASE_BRANCHES = SHARDS


def csv_filter_values(raw: str | None) -> list[str]:
    if raw is None:
        return []
    return sorted(set(part.strip() for part in raw.split(",") if part.strip()))


def command_case_list(args: argparse.Namespace, root: Path) -> int:
    statuses = csv_filter_values(args.status)
    branches = csv_filter_values(args.branch)
    errors: list[str] = []
    unknown_statuses = sorted(set(statuses) - set(CASE_STATUSES))
    unknown_branches = sorted(set(branches) - set(CASE_BRANCHES))
    if unknown_statuses:
        errors.append(f"unknown case statuses: {unknown_statuses}")
    if unknown_branches:
        errors.append(f"unknown case branches: {unknown_branches}")
    if errors:
        return stop({"command": "case.list", "ok": False, "errors": errors}, 1)

    records = read_jsonl(root / "research" / "cases" / "cases.jsonl")
    selected = [
        dict(record)
        for record in records
        if (not statuses or record.get("status") in statuses)
        and (not branches or record.get("branch") in branches)
    ]
    return stop(
        {
            "command": "case.list",
            "ok": True,
            "filters": {"status": statuses, "branch": branches},
            "count": len(selected),
            "cases": selected,
        },
        0,
    )


def render_docket_html(root: Path, records: list[dict[str, Any]]) -> tuple[str, str]:
    """Compose the two index.html mutations in memory: regenerated docket
    region + fresh deploy stamp. Pure; hard-fails (SystemExit) on missing
    markers/anchors or unknown person refs, BEFORE any file is written."""
    source = (root / "index.html").read_text(encoding="utf-8")
    people = build_docket.people_index(source)
    markup = build_docket.render_cases(records, people)
    spliced = build_docket.splice_cases(source, markup)
    return stamp_tool.stamped_html(spliced)


def command_case_update(args: argparse.Namespace, root: Path) -> int:
    mutations = [name for name in CASE_SCALAR_FLAGS if getattr(args, name) is not None]
    requested_additions = {
        name: getattr(args, f"add_{name[:-1]}") or [] for name in CASE_ADD_FLAGS
    }
    if not mutations and not any(requested_additions.values()):
        return stop({"command": "case.update", "ok": False, "errors": ["nothing to update"]}, 1)
    if args.status is not None and args.status not in CASE_STATUSES:
        return stop({"command": "case.update", "ok": False,
                     "errors": [f"invalid status {args.status!r}"]}, 1)
    if args.source_note == "":
        return stop({"command": "case.update", "ok": False,
                     "errors": ["source_note is required and cannot be cleared"]}, 1)

    cases_path = root / "research" / "cases" / "cases.jsonl"
    with open(store_lock_path(root), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        trace_refs, trace_errors = canonical_trace_refs(
            root, requested_additions["trace_refs"]
        )
        if trace_errors:
            return stop(
                {
                    "command": "case.update",
                    "ok": False,
                    "written": False,
                    "errors": trace_errors,
                },
                1,
            )
        additions = dict(requested_additions)
        additions["trace_refs"] = trace_refs

        records = read_jsonl(cases_path)
        target = next((r for r in records if r.get("id") == args.case_id), None)
        if target is None:
            return stop({"command": "case.update", "ok": False,
                         "errors": [f"unknown case id {args.case_id!r}"]}, 1)

        changed: dict[str, Any] = {}
        for name in CASE_SCALAR_FLAGS:
            value = getattr(args, name)
            if value is None:
                continue
            if name == "display_prose" and value == "":
                # documented spelling for "clear the override, render summary"
                changed[name] = target.pop(name, None) is not None
                continue
            if name == "status":
                changed[name] = [target.get(name), value]
            else:
                changed[name] = target.get(name) != value
            target[name] = value
        added: dict[str, list[str]] = {}
        already: dict[str, list[str]] = {}
        for name, values in additions.items():
            existing = target.setdefault(name, [])
            added[name], already[name] = [], []
            for value in values:
                if value in existing:
                    already[name].append(value)
                else:
                    existing.append(value)
                    added[name].append(value)

        candidate = "".join(compact_json(r) + "\n" for r in records).encode("utf-8")
        original = cases_path.read_bytes()
        noop = candidate == original

        ok, errors = validate_case_records(root, records)
        if not ok:
            return stop({"command": "case.update", "ok": False, "written": False,
                         "errors": errors}, 1)
        final_html, stamp_value = render_docket_html(root, records)
        html_path = root / "index.html"
        html_current = html_path.read_text(encoding="utf-8") == final_html

        if noop and html_current:
            return stop({"command": "case.update", "ok": True, "written": False,
                         "noop": True, "repaired": None, "id": args.case_id}, 0)
        if args.validate_only:
            return stop({"command": "case.update", "ok": True, "written": False,
                         "validate_only": True, "id": args.case_id,
                         "changed": changed, "added": added,
                         "already_present": already}, 0)

        if not noop:
            atomic_replace(cases_path, candidate)
        atomic_replace(html_path, final_html.encode("utf-8"))
        return stop({
            "command": "case.update", "ok": True, "written": True, "id": args.case_id,
            "changed": changed, "added": added, "already_present": already,
            "repaired": "docket" if noop else None,
            "docket": "regenerated", "stamp": stamp_value,
        }, 0)


def relationships_path(root: Path) -> Path:
    return root / "research" / "people" / "relationships.jsonl"


def family_candidate_bytes(records: list[dict[str, Any]]) -> bytes:
    return "".join(compact_json(record) + "\n" for record in records).encode(
        "utf-8"
    )


def validate_candidate_family(root: Path, candidate: bytes):
    """Validate would-be family rows without exposing partial real state."""

    with tempfile.TemporaryDirectory(prefix="gen-family-validate-") as td:
        candidate_path = Path(td) / "relationships.jsonl"
        candidate_path.write_bytes(candidate)
        return check_family_core.validate_repository(
            root=root, relationships_path=candidate_path
        )


def render_candidate_family_html(
    root: Path, candidate: bytes
) -> tuple[str, str, int]:
    """Render and stamp the family projection from candidate relationships.

    ``build_people_index`` deliberately reads a root-shaped tree.  A minimal
    temporary root lets it enforce its complete projection contract before
    either the canonical JSONL or ``index.html`` is changed.
    """

    with tempfile.TemporaryDirectory(prefix="gen-family-render-") as td:
        candidate_root = Path(td)
        people_dir = candidate_root / "research" / "people"
        people_dir.mkdir(parents=True)
        (people_dir / "people.jsonl").write_bytes(
            (root / "research" / "people" / "people.jsonl").read_bytes()
        )
        (people_dir / "relationships.jsonl").write_bytes(candidate)
        (candidate_root / "index.html").write_bytes(
            (root / "index.html").read_bytes()
        )
        _original, rendered, payload = build_people_index.build(candidate_root)
    stamped, stamp_value = stamp_tool.stamped_html(rendered)
    return stamped, stamp_value, len(payload["people"])


RELATIONSHIP_SCALAR_FLAGS = ("status", "confidence", "provenance_note")
RELATIONSHIP_ADD_FLAGS = ("evidence_refs", "source_refs", "case_refs")


def command_relationship_update(args: argparse.Namespace, root: Path) -> int:
    mutations = [
        name
        for name in RELATIONSHIP_SCALAR_FLAGS
        if getattr(args, name) is not None
    ]
    additions = {
        name: getattr(args, f"add_{name[:-1]}") or []
        for name in RELATIONSHIP_ADD_FLAGS
    }
    if not mutations and not any(additions.values()):
        return stop(
            {
                "command": "relationship.update",
                "ok": False,
                "errors": ["nothing to update"],
            },
            1,
        )
    if args.status is not None and args.status not in (
        "accepted",
        "hypothesis",
        "rejected",
    ):
        return stop(
            {
                "command": "relationship.update",
                "ok": False,
                "errors": [f"invalid relationship status {args.status!r}"],
            },
            1,
        )
    if args.confidence is not None and args.confidence not in (
        "documented",
        "strong",
        "lead",
        "open",
    ):
        return stop(
            {
                "command": "relationship.update",
                "ok": False,
                "errors": [f"invalid relationship confidence {args.confidence!r}"],
            },
            1,
        )
    if args.provenance_note == "":
        return stop(
            {
                "command": "relationship.update",
                "ok": False,
                "errors": ["provenance_note cannot be empty"],
            },
            1,
        )

    path = relationships_path(root)
    with open(store_lock_path(root), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        records = read_jsonl(path)
        target = next(
            (
                record
                for record in records
                if record.get("id") == args.relationship_id
                and record.get("node_type") == "relationship"
            ),
            None,
        )
        if target is None:
            return stop(
                {
                    "command": "relationship.update",
                    "ok": False,
                    "errors": [
                        f"unknown relationship id {args.relationship_id!r}"
                    ],
                },
                1,
            )
        if (
            args.status is not None
            and args.status != target.get("status")
            and args.provenance_note is None
        ):
            return stop(
                {
                    "command": "relationship.update",
                    "ok": False,
                    "written": False,
                    "errors": [
                        "--provenance-note is required when relationship status changes"
                    ],
                },
                1,
            )

        scalar_values = {
            name: getattr(args, name) for name in RELATIONSHIP_SCALAR_FLAGS
        }
        if args.status == "rejected" and target.get("status") != "rejected":
            scalar_values["provenance_note"] = (
                f"{target['provenance_note'].rstrip()} Rejected on {today()}: "
                f"{args.provenance_note}"
            )
        elif args.status == "rejected" and args.provenance_note is not None:
            replay_suffix = re.compile(
                r" Rejected on \d{4}-\d{2}-\d{2}: "
                + re.escape(args.provenance_note)
                + r"\Z"
            )
            if replay_suffix.search(target["provenance_note"]):
                scalar_values["provenance_note"] = target["provenance_note"]
            else:
                scalar_values["provenance_note"] = (
                    f"{target['provenance_note'].rstrip()} Rejection note updated "
                    f"on {today()}: {args.provenance_note}"
                )
        elif (
            target.get("status") == "rejected"
            and args.status is not None
            and args.status != "rejected"
        ):
            scalar_values["provenance_note"] = (
                f"{target['provenance_note'].rstrip()} Status changed to "
                f"{args.status} on {today()}: {args.provenance_note}"
            )

        changed: dict[str, bool] = {}
        for name in RELATIONSHIP_SCALAR_FLAGS:
            value = scalar_values[name]
            if value is None:
                continue
            changed[name] = target.get(name) != value
            target[name] = value

        added: dict[str, list[str]] = {}
        already: dict[str, list[str]] = {}
        for name, values in additions.items():
            existing = target[name]
            added[name] = sorted(set(values) - set(existing))
            already[name] = sorted(set(values) & set(existing))
            target[name] = sorted(set(existing) | set(values))

        candidate = family_candidate_bytes(records)
        validation = validate_candidate_family(root, candidate)
        if not validation.ok:
            return stop(
                {
                    "command": "relationship.update",
                    "ok": False,
                    "written": False,
                    "errors": list(validation.errors),
                },
                1,
            )
        try:
            final_html, stamp_value, projection_count = render_candidate_family_html(
                root, candidate
            )
        except build_people_index.ProjectionError as exc:
            return stop(
                {
                    "command": "relationship.update",
                    "ok": False,
                    "written": False,
                    "errors": [f"family projection failed: {exc}"],
                },
                1,
            )

        original = path.read_bytes()
        html_path = root / "index.html"
        html_current = html_path.read_text(encoding="utf-8") == final_html
        noop = candidate == original
        result_fields = {
            "id": args.relationship_id,
            "changed": changed,
            "added": added,
            "already_present": already,
        }
        if args.validate_only:
            return stop(
                {
                    "command": "relationship.update",
                    "ok": True,
                    "written": False,
                    "validate_only": True,
                    **result_fields,
                },
                0,
            )
        if noop and html_current:
            return stop(
                {
                    "command": "relationship.update",
                    "ok": True,
                    "written": False,
                    "noop": True,
                    "repaired": None,
                    **result_fields,
                },
                0,
            )

        if not noop:
            atomic_replace(path, candidate)
        atomic_replace(html_path, final_html.encode("utf-8"))
        return stop(
            {
                "command": "relationship.update",
                "ok": True,
                "written": True,
                "repaired": "people-index" if noop else None,
                "projection": "regenerated",
                "projection_count": projection_count,
                "stamp": stamp_value,
                **result_fields,
            },
            0,
        )


def relationship_id_for_parent(parent_id: str, child_id: str) -> str:
    parent_key = parent_id.removeprefix("person.").replace(".", "_")
    child_key = child_id.removeprefix("person.").replace(".", "_")
    return f"relationship.parent.{parent_key}-to-{child_key}"


def remaining_parent_roles(open_roles: list[str], resolved_role: str) -> list[str]:
    if "parents" in open_roles:
        return ["mother" if resolved_role == "father" else "father"]
    return sorted(role for role in open_roles if role != resolved_role)


def remaining_pedigree(
    pedigree: dict[str, list[int]], roles: list[str]
) -> dict[str, list[int]]:
    keep_father = "father" in roles or "parents" in roles
    keep_mother = "mother" in roles or "parents" in roles
    return {
        code: [
            slot
            for slot in slots
            if (slot % 2 == 0 and keep_father)
            or (slot % 2 == 1 and keep_mother)
        ]
        for code, slots in pedigree.items()
    }


def gap_resolution_note(
    args: argparse.Namespace,
    child_id: str,
    relationship_id: str,
    evidence_refs: list[str],
    source_refs: list[str],
    case_refs: list[str],
    rejected_ids: set[str],
) -> str:
    """Persist both human reasoning and an exact replay signature."""

    resolution_refs = [*evidence_refs, *source_refs, *case_refs]
    base = args.provenance_note or (
        f"Resolved {args.role} of {child_id} as {args.parent} through "
        f"{relationship_id}, citing {', '.join(resolution_refs)}."
    )
    action = {
        "parent": args.parent,
        "child": child_id,
        "role": args.role,
        "relationship_id": relationship_id,
        "confidence": args.confidence,
        "evidence_refs": sorted(set(args.evidence_ref)),
        "source_refs": sorted(set(args.source_ref or [])),
        "rejected_relationship_ids": sorted(rejected_ids),
    }
    return f"{base.rstrip()} Resolution action: {compact_json(action)}"


def exact_gap_resolution_replay(
    *,
    gap: dict[str, Any],
    selected: dict[str, Any] | None,
    role: str,
    confidence: str,
    resolution_note: str,
    evidence_refs: list[str],
    source_refs: list[str],
    case_refs: list[str],
    rejected_rows: list[dict[str, Any]],
    rejected_ids: set[str],
) -> bool:
    """Recognize only the exact, fully-landed action encoded in truth."""

    if selected is None:
        return False
    if (
        selected.get("status") != "accepted"
        or selected.get("parent_role") != role
        or selected.get("confidence") != confidence
        or selected.get("provenance_note") != resolution_note
    ):
        return False
    if not set(evidence_refs).issubset(selected.get("evidence_refs") or []):
        return False
    if not set(source_refs).issubset(selected.get("source_refs") or []):
        return False
    if not set(case_refs).issubset(selected.get("case_refs") or []):
        return False
    if (
        gap.get("resolution_note") != resolution_note
        or gap.get("evidence_refs") != evidence_refs
        or gap.get("source_refs") != source_refs
        or gap.get("status") not in {"open", "resolved"}
    ):
        return False
    open_roles = gap.get("open_roles") or []
    if role in open_roles or "parents" in open_roles:
        return False
    if gap.get("status") == "resolved" and (
        open_roles
        or gap.get("candidate_persons")
        or any(gap.get("pedigree", {}).values())
        or not gap.get("resolved_on")
    ):
        return False
    if gap.get("status") == "open" and gap.get("resolved_on") is not None:
        return False
    if {row.get("id") for row in rejected_rows} != rejected_ids:
        return False
    for row in rejected_rows:
        if (
            row.get("status") != "rejected"
            or resolution_note not in (row.get("provenance_note") or "")
            or not set(evidence_refs).issubset(row.get("evidence_refs") or [])
            or not set(source_refs).issubset(row.get("source_refs") or [])
            or not set(case_refs).issubset(row.get("case_refs") or [])
        ):
            return False
    return True


def finish_gap_replay(
    args: argparse.Namespace,
    root: Path,
    records: list[dict[str, Any]],
    result_fields: dict[str, Any],
) -> int:
    """Validate landed truth, then no-op or repair its generated projection."""

    candidate = family_candidate_bytes(sorted(records, key=lambda record: record["id"]))
    validation = validate_candidate_family(root, candidate)
    if not validation.ok:
        return stop(
            {
                "command": "gap.resolve",
                "ok": False,
                "written": False,
                "errors": list(validation.errors),
            },
            1,
        )
    try:
        final_html, stamp_value, projection_count = render_candidate_family_html(
            root, candidate
        )
    except build_people_index.ProjectionError as exc:
        return stop(
            {
                "command": "gap.resolve",
                "ok": False,
                "written": False,
                "errors": [f"family projection failed: {exc}"],
            },
            1,
        )

    if args.validate_only:
        return stop(
            {
                "command": "gap.resolve",
                "ok": True,
                "written": False,
                "validate_only": True,
                "replay": True,
                **result_fields,
            },
            0,
        )
    html_path = root / "index.html"
    if html_path.read_text(encoding="utf-8") == final_html:
        return stop(
            {
                "command": "gap.resolve",
                "ok": True,
                "written": False,
                "noop": True,
                "replay": True,
                "repaired": None,
                **result_fields,
            },
            0,
        )
    atomic_replace(html_path, final_html.encode("utf-8"))
    return stop(
        {
            "command": "gap.resolve",
            "ok": True,
            "written": True,
            "noop": False,
            "replay": True,
            "repaired": "people-index",
            "projection": "regenerated",
            "projection_count": projection_count,
            "stamp": stamp_value,
            **result_fields,
        },
        0,
    )


def command_gap_resolve(args: argparse.Namespace, root: Path) -> int:
    if args.role not in ("father", "mother"):
        return stop(
            {
                "command": "gap.resolve",
                "ok": False,
                "errors": ["role must be 'father' or 'mother'"],
            },
            1,
        )
    if args.confidence not in ("documented", "strong", "lead", "open"):
        return stop(
            {
                "command": "gap.resolve",
                "ok": False,
                "errors": [f"invalid relationship confidence {args.confidence!r}"],
            },
            1,
        )
    if args.provenance_note == "":
        return stop(
            {
                "command": "gap.resolve",
                "ok": False,
                "errors": ["provenance_note cannot be empty"],
            },
            1,
        )

    path = relationships_path(root)
    with open(store_lock_path(root), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        records = read_jsonl(path)
        gap = next(
            (
                record
                for record in records
                if record.get("id") == args.gap_id
                and record.get("node_type") == "gap"
            ),
            None,
        )
        if gap is None:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [f"unknown gap id {args.gap_id!r}"],
                },
                1,
            )
        if gap.get("gap_type") not in ("parentage", "candidate_parentage"):
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        "gap resolve only supports parentage and "
                        "candidate_parentage gaps"
                    ],
                },
                1,
            )
        subjects = gap.get("subject_persons") or []
        child_id = args.child
        if child_id is None:
            if len(subjects) != 1:
                return stop(
                    {
                        "command": "gap.resolve",
                        "ok": False,
                        "errors": [
                            "--child is required when a gap has multiple subjects"
                        ],
                    },
                    1,
                )
            child_id = subjects[0]
        if child_id not in subjects:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [f"child {child_id!r} is not a subject of {args.gap_id}"],
                },
                1,
            )

        people = {record["id"] for record in people_records(root)}
        if args.parent not in people:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [f"unknown parent person id {args.parent!r}"],
                },
                1,
            )
        selected = next(
            (
                record
                for record in records
                if record.get("node_type") == "relationship"
                and record.get("relationship_type") == "parent_of"
                and record.get("person_a") == args.parent
                and record.get("person_b") == child_id
            ),
            None,
        )
        if selected is not None and selected.get("parent_role") != args.role:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        f"existing relationship {selected['id']} has role "
                        f"{selected.get('parent_role')!r}, not {args.role!r}"
                    ],
                },
                1,
            )

        rejected_ids = set(args.reject_relationship or [])
        if rejected_ids and args.provenance_note is None:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "written": False,
                    "errors": [
                        "--provenance-note is required when competing "
                        "relationships are rejected"
                    ],
                },
                1,
            )
        rejected_rows = [
            record
            for record in records
            if record.get("id") in rejected_ids
            and record.get("node_type") == "relationship"
        ]
        evidence_refs = sorted(
            set(gap.get("evidence_refs") or []) | set(args.evidence_ref)
        )
        source_refs = sorted(
            set(gap.get("source_refs") or []) | set(args.source_ref or [])
        )
        case_refs = sorted(set(gap.get("case_refs") or []))
        if selected is None:
            relationship_id = relationship_id_for_parent(args.parent, child_id)
        else:
            relationship_id = selected["id"]

        resolution_note = gap_resolution_note(
            args,
            child_id,
            relationship_id,
            evidence_refs,
            source_refs,
            case_refs,
            rejected_ids,
        )
        replay_fields = {
            "gap_id": args.gap_id,
            "relationship_id": relationship_id,
            "parent": args.parent,
            "child": child_id,
            "role": args.role,
            "resolved": gap.get("status") == "resolved",
            "canonical_gap_state": (
                "resolved_tombstone"
                if gap.get("status") == "resolved"
                else "open"
            ),
            "remaining_open_roles": gap.get("open_roles") or [],
            "rejected_relationship_ids": sorted(rejected_ids),
            "owner_follow_up_required": gap.get("owner_follow_up_required"),
            "owner_anchor": (
                gap.get("public_anchor")
                if gap.get("owner_follow_up_required")
                else None
            ),
        }
        if exact_gap_resolution_replay(
            gap=gap,
            selected=selected,
            role=args.role,
            confidence=args.confidence,
            resolution_note=resolution_note,
            evidence_refs=evidence_refs,
            source_refs=source_refs,
            case_refs=case_refs,
            rejected_rows=rejected_rows,
            rejected_ids=rejected_ids,
        ):
            return finish_gap_replay(args, root, records, replay_fields)

        if gap.get("status") != "open":
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        f"gap {args.gap_id} is already {gap.get('status')!r}"
                    ],
                },
                1,
            )
        open_roles = gap.get("open_roles") or []
        if args.role not in open_roles and "parents" not in open_roles:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        f"{args.role} is not open on {args.gap_id}; "
                        f"open roles are {open_roles}"
                    ],
                },
                1,
            )
        if selected is not None and selected.get("status") == "rejected":
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        f"selected relationship {selected['id']} is rejected"
                    ],
                },
                1,
            )

        competitors = [
            record
            for record in records
            if record.get("node_type") == "relationship"
            and record.get("relationship_type") == "parent_of"
            and record.get("status") != "rejected"
            and record.get("person_b") == child_id
            and record.get("parent_role") == args.role
            and record.get("person_a") != args.parent
        ]
        accepted_competitors = [
            record["id"]
            for record in competitors
            if record.get("status") == "accepted"
        ]
        if accepted_competitors:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        "cannot replace accepted competing relationships: "
                        + ", ".join(sorted(accepted_competitors))
                    ],
                },
                1,
            )
        competitor_ids = {record["id"] for record in competitors}
        if rejected_ids != competitor_ids:
            missing = sorted(competitor_ids - rejected_ids)
            extra = sorted(rejected_ids - competitor_ids)
            details = []
            if missing:
                details.append(
                    "explicit --reject-relationship required for " + ", ".join(missing)
                )
            if extra:
                details.append(
                    "not competing hypothesis relationships: " + ", ".join(extra)
                )
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "written": False,
                    "errors": details,
                },
                1,
            )
        if selected is None and any(
            record.get("id") == relationship_id for record in records
        ):
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "errors": [
                        f"derived relationship id already exists: {relationship_id}"
                    ],
                },
                1,
            )

        if selected is None:
            selected = {
                "id": relationship_id,
                "node_type": "relationship",
                "relationship_type": "parent_of",
                "person_a": args.parent,
                "person_b": child_id,
                "parent_role": args.role,
                "status": "accepted",
                "confidence": args.confidence,
                "branches": sorted(gap["branches"]),
                "evidence_refs": evidence_refs,
                "source_refs": source_refs,
                "case_refs": case_refs,
                "provenance_note": resolution_note,
            }
            records.append(selected)
        else:
            selected["status"] = "accepted"
            selected["confidence"] = args.confidence
            selected["branches"] = sorted(
                set(selected["branches"]) | set(gap["branches"])
            )
            selected["evidence_refs"] = sorted(
                set(selected["evidence_refs"]) | set(evidence_refs)
            )
            selected["source_refs"] = sorted(
                set(selected["source_refs"]) | set(source_refs)
            )
            selected["case_refs"] = sorted(
                set(selected["case_refs"]) | set(case_refs)
            )
            selected["provenance_note"] = resolution_note

        for competitor in competitors:
            if competitor["id"] not in rejected_ids:
                continue
            competitor["status"] = "rejected"
            competitor["evidence_refs"] = sorted(
                set(competitor["evidence_refs"]) | set(evidence_refs)
            )
            competitor["source_refs"] = sorted(
                set(competitor["source_refs"]) | set(source_refs)
            )
            competitor["case_refs"] = sorted(
                set(competitor["case_refs"]) | set(case_refs)
            )
            competitor["provenance_note"] = (
                f"{competitor['provenance_note'].rstrip()} Rejected on {today()} "
                f"while resolving {args.gap_id} in favor of {relationship_id}. "
                f"{resolution_note}"
            )
        roles = remaining_parent_roles(open_roles, args.role)
        resolved_people = {args.parent} | {
            record.get("person_a") for record in competitors
        }
        gap["candidate_persons"] = sorted(
            set(gap.get("candidate_persons") or []) - resolved_people
        )
        gap["open_roles"] = roles
        gap["pedigree"] = remaining_pedigree(gap["pedigree"], roles)
        gap["evidence_refs"] = evidence_refs
        gap["source_refs"] = source_refs
        owner_anchor = gap.get("public_anchor")
        owner_follow_up_required = owner_anchor is not None
        gap["resolution_note"] = resolution_note
        gap["owner_follow_up_required"] = owner_follow_up_required
        gap["status"] = "open"
        gap["resolved_on"] = None
        if not roles:
            gap["candidate_persons"] = []
            gap["pedigree"] = {code: [] for code in ("Z", "M", "D", "C")}
            gap["status"] = "resolved"
            gap["resolved_on"] = today()

        records.sort(key=lambda record: record["id"])
        candidate = family_candidate_bytes(records)
        validation = validate_candidate_family(root, candidate)
        if not validation.ok:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "written": False,
                    "errors": list(validation.errors),
                },
                1,
            )
        try:
            final_html, stamp_value, projection_count = render_candidate_family_html(
                root, candidate
            )
        except build_people_index.ProjectionError as exc:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": False,
                    "written": False,
                    "errors": [f"family projection failed: {exc}"],
                },
                1,
            )

        result_fields = {
            "gap_id": args.gap_id,
            "relationship_id": relationship_id,
            "parent": args.parent,
            "child": child_id,
            "role": args.role,
            "resolved": not roles,
            "canonical_gap_state": "resolved_tombstone" if not roles else "open",
            "remaining_open_roles": roles,
            "rejected_relationship_ids": sorted(rejected_ids),
            "owner_follow_up_required": owner_follow_up_required,
            "owner_anchor": owner_anchor if owner_follow_up_required else None,
        }
        if args.validate_only:
            return stop(
                {
                    "command": "gap.resolve",
                    "ok": True,
                    "written": False,
                    "validate_only": True,
                    **result_fields,
                },
                0,
            )

        atomic_replace(path, candidate)
        atomic_replace(root / "index.html", final_html.encode("utf-8"))
        return stop(
            {
                "command": "gap.resolve",
                "ok": True,
                "written": True,
                "noop": False,
                "replay": False,
                "repaired": None,
                "projection": "regenerated",
                "projection_count": projection_count,
                "stamp": stamp_value,
                **result_fields,
            },
            0,
        )


def latest_trace(root: Path) -> str:
    paths = sorted((root / "research" / "reasoning-traces").glob("20*.md"))
    if not paths:
        return ""
    return max(paths, key=lambda path: (path.name[:10], path.name)).name


def command_status(_args: argparse.Namespace, root: Path) -> int:
    family_result = check_family_core.validate_repository(root=root)
    evidence_result = check_evidence.validate_repository(root=root)
    cases_ok, _case_errors = validate_cases(root)
    traces_result = check_traces.validate_repository(root=root)

    case_records = read_jsonl(root / "research" / "cases" / "cases.jsonl")
    cases: dict[str, int] = {"open": 0}
    for record in case_records:
        status = record.get("status")
        if isinstance(status, str):
            cases[status] = cases.get(status, 0) + 1
    cases["total"] = len(case_records)

    by_shard = {
        shard: len(read_jsonl(evidence_path(root, shard)))
        for shard in SHARDS
    }
    validators = {
        "family": family_result.ok,
        "evidence": evidence_result.ok,
        "cases": cases_ok,
        "traces": traces_result.ok,
    }
    gap_rows = [
        row
        for row in family_records(root)
        if row.get("node_type") == "gap"
    ]
    gap_statuses = {
        status: sum(row.get("status") == status for row in gap_rows)
        for status in ("open", "resolved")
    }
    healthy = all(validators.values())
    return stop(
        {
            "command": "status",
            "ok": healthy,
            "validators": validators,
            "family": {
                "people": family_result.person_count,
                "relationships": family_result.relationship_count,
                "gaps": family_result.gap_count,
                "gaps_by_status": gap_statuses,
            },
            "cases": cases,
            "evidence": {"total": sum(by_shard.values()), "by_shard": by_shard},
            "latest_trace": latest_trace(root),
        },
        0 if healthy else 1,
    )


def parser_error(message: str) -> None:
    emit({"ok": False, "errors": [message]})
    raise SystemExit(1)


def attach_error(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.error = parser_error
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = attach_error(argparse.ArgumentParser(add_help=False))
    sub = parser.add_subparsers(dest="command", required=True)

    evidence = attach_error(sub.add_parser("evidence", add_help=False))
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_add = attach_error(evidence_sub.add_parser("add", add_help=False))
    evidence_add.add_argument("--shard", required=True)
    evidence_add.add_argument("--validate-only", action="store_true")
    evidence_add.set_defaults(handler=command_evidence_add)

    trace = attach_error(sub.add_parser("trace", add_help=False))
    trace_sub = trace.add_subparsers(dest="trace_command", required=True)
    trace_new = attach_error(trace_sub.add_parser("new", add_help=False))
    trace_new.add_argument("--slug", required=True)
    trace_new.add_argument("--title", required=True)
    trace_new.add_argument("--date", default=today())
    trace_new.add_argument("--confidence", default="working")
    trace_new.add_argument("--case-refs")
    trace_new.add_argument("--person-refs")
    trace_new.add_argument("--evidence-refs")
    trace_new.add_argument("--source-refs")
    trace_new.add_argument("--geo-refs")
    trace_new.add_argument("--outcome")
    trace_new.add_argument("--next-action")
    trace_new.add_argument("--body-file", dest="body_file")
    trace_new.set_defaults(handler=command_trace_new)

    case = attach_error(sub.add_parser("case", add_help=False))
    case_sub = case.add_subparsers(dest="case_command", required=True)
    case_list = attach_error(case_sub.add_parser("list", add_help=False))
    case_list.add_argument("--status")
    case_list.add_argument("--branch")
    case_list.set_defaults(handler=command_case_list)
    case_update = attach_error(case_sub.add_parser("update", add_help=False))
    case_update.add_argument("case_id")
    case_update.add_argument("--status")
    case_update.add_argument("--summary")
    case_update.add_argument("--display-prose", dest="display_prose")
    case_update.add_argument("--source-note", dest="source_note")
    case_update.add_argument("--add-evidence-ref", dest="add_evidence_ref", action="append")
    case_update.add_argument("--add-trace-ref", dest="add_trace_ref", action="append")
    case_update.add_argument("--add-person-ref", dest="add_person_ref", action="append")
    case_update.add_argument("--validate-only", action="store_true")
    case_update.set_defaults(handler=command_case_update)

    relationship = attach_error(sub.add_parser("relationship", add_help=False))
    relationship_sub = relationship.add_subparsers(
        dest="relationship_command", required=True
    )
    relationship_update = attach_error(
        relationship_sub.add_parser("update", add_help=False)
    )
    relationship_update.add_argument("relationship_id")
    relationship_update.add_argument("--status")
    relationship_update.add_argument("--confidence")
    relationship_update.add_argument("--provenance-note", dest="provenance_note")
    relationship_update.add_argument(
        "--add-evidence-ref", dest="add_evidence_ref", action="append"
    )
    relationship_update.add_argument(
        "--add-source-ref", dest="add_source_ref", action="append"
    )
    relationship_update.add_argument(
        "--add-case-ref", dest="add_case_ref", action="append"
    )
    relationship_update.add_argument("--validate-only", action="store_true")
    relationship_update.set_defaults(handler=command_relationship_update)

    gap = attach_error(sub.add_parser("gap", add_help=False))
    gap_sub = gap.add_subparsers(dest="gap_command", required=True)
    gap_resolve = attach_error(gap_sub.add_parser("resolve", add_help=False))
    gap_resolve.add_argument("gap_id")
    gap_resolve.add_argument("--parent", required=True)
    gap_resolve.add_argument("--child")
    gap_resolve.add_argument("--role", required=True)
    gap_resolve.add_argument(
        "--evidence-ref", dest="evidence_ref", action="append", required=True
    )
    gap_resolve.add_argument("--source-ref", dest="source_ref", action="append")
    gap_resolve.add_argument(
        "--reject-relationship", dest="reject_relationship", action="append"
    )
    gap_resolve.add_argument("--confidence", default="strong")
    gap_resolve.add_argument("--provenance-note", dest="provenance_note")
    gap_resolve.add_argument("--validate-only", action="store_true")
    gap_resolve.set_defaults(handler=command_gap_resolve)

    show = attach_error(sub.add_parser("show", add_help=False))
    show.add_argument("id")
    show.set_defaults(handler=command_show)

    ancestors = attach_error(sub.add_parser("ancestors", add_help=False))
    ancestors.add_argument("person_id")
    ancestors.set_defaults(handler=command_ancestors)

    path_cmd = attach_error(sub.add_parser("path", add_help=False))
    path_cmd.add_argument("person_a")
    path_cmd.add_argument("person_b")
    path_cmd.set_defaults(handler=command_path)

    contradictions = attach_error(sub.add_parser("contradictions", add_help=False))
    contradictions.add_argument("--strict", action="store_true")
    contradictions.set_defaults(handler=command_contradictions)

    adjudicate = attach_error(sub.add_parser("adjudicate", add_help=False))
    adjudicate.set_defaults(handler=command_adjudicate)

    status = attach_error(sub.add_parser("status", add_help=False))
    status.set_defaults(handler=command_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args, root_path())


if __name__ == "__main__":
    raise SystemExit(main())
