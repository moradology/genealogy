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

import check_cases  # noqa: E402
import check_evidence  # noqa: E402
import check_traces  # noqa: E402


SHARDS = ("zimmerman", "mundell", "dible", "connelly")
KINDS = ("case", "evidence", "source", "trace", "geo", "person")
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
    content = "\n".join(fields) + trace_body_from_template(root, args.title)

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

        path.write_text(content, encoding="utf-8")
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
    html = (root / "index.html").read_text(encoding="utf-8")
    return check_cases.people_index(html)


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
        if record.get("i") == wanted:
            return "person", record, {wanted}

    return None, None, {wanted}


def record_refs(record: dict[str, Any], fields: tuple[str, ...]) -> set[str]:
    refs: set[str] = set()
    for field in fields:
        value = record.get(field)
        if isinstance(value, list):
            refs.update(item for item in value if isinstance(item, str))
    return refs


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

    return {
        "cases": sorted(cases),
        "evidence": sorted(evidence),
        "traces": sorted(traces),
    }


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


def validate_cases(root: Path) -> tuple[bool, list[str]]:
    html = (root / "index.html").read_text(encoding="utf-8")
    records = read_jsonl(root / "research" / "cases" / "cases.jsonl")
    person_ids = set(re.findall(r'id="(person\.[A-Za-z0-9_.-]+)"', html))
    trace_dir = root / "research" / "reasoning-traces"
    trace_names = {path.name for path in trace_dir.glob("20*.md")}
    failures = check_cases.core_failures(
        records,
        check_cases.docket_records(html),
        check_cases.people_index(html),
        person_ids,
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


def latest_trace(root: Path) -> str:
    paths = sorted((root / "research" / "reasoning-traces").glob("20*.md"))
    if not paths:
        return ""
    return max(paths, key=lambda path: (path.name[:10], path.name)).name


def command_status(_args: argparse.Namespace, root: Path) -> int:
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
    trace_new.set_defaults(handler=command_trace_new)

    show = attach_error(sub.add_parser("show", add_help=False))
    show.add_argument("id")
    show.set_defaults(handler=command_show)

    status = attach_error(sub.add_parser("status", add_help=False))
    status.set_defaults(handler=command_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args, root_path())


if __name__ == "__main__":
    raise SystemExit(main())
