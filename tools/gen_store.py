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
import check_cases  # noqa: E402
import check_evidence  # noqa: E402
import check_family_core  # noqa: E402
import check_traces  # noqa: E402
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
    links = [r for r in rows if r.get("node_type") == "relationship"]
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
                if "parents" in gap["open_roles"] and gap not in frontier:
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
    trace_dir = root / "research" / "reasoning-traces"
    trace_names = {path.name for path in trace_dir.glob("20*.md")}
    failures = check_cases.core_failures(
        records,
        check_cases.canonical_gaps(
            root / "research" / "people" / "relationships.jsonl"
        ),
        check_cases.canonical_person_ids(
            root / "research" / "people" / "people.jsonl"
        ),
        check_cases.evidence_case_index(root),
        trace_names,
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
    additions = {name: getattr(args, f"add_{name[:-1]}") or [] for name in CASE_ADD_FLAGS}
    if not mutations and not any(additions.values()):
        return stop({"command": "case.update", "ok": False, "errors": ["nothing to update"]}, 1)
    if args.status is not None and args.status not in ("open", "in_conflict", "needs_pull", "closed"):
        return stop({"command": "case.update", "ok": False,
                     "errors": [f"invalid status {args.status!r}"]}, 1)
    if args.source_note == "":
        return stop({"command": "case.update", "ok": False,
                     "errors": ["source_note is required and cannot be cleared"]}, 1)

    cases_path = root / "research" / "cases" / "cases.jsonl"
    with open(store_lock_path(root), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

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
                         "changed": changed, "added": added, "already_present": already}, 0)

        if not noop:
            atomic_replace(cases_path, candidate)
        atomic_replace(html_path, final_html.encode("utf-8"))
        return stop({
            "command": "case.update", "ok": True, "written": True, "id": args.case_id,
            "changed": changed, "added": added, "already_present": already,
            "repaired": "docket" if noop else None,
            "docket": "regenerated", "stamp": stamp_value,
        }, 0)


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

    status = attach_error(sub.add_parser("status", add_help=False))
    status.set_defaults(handler=command_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args, root_path())


if __name__ == "__main__":
    raise SystemExit(main())
