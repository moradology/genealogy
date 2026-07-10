#!/usr/bin/env python3
"""JSON-first cockpit CLI for repository maintenance tools.

A thin, extensible dispatcher: each command wraps an existing tool, invokes it
the same way the gate does (`uv run tools/X.py`, so PEP 723 inline deps like
build_fonts.py's fonttools are resolved), and prints exactly one JSON object.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BUILD_TARGETS = {
    "basemap": "tools/build_basemap.py",
    "fonts": "tools/build_fonts.py",
    "citation-backlinks": "tools/build_citation_backlinks.py",
    "docket": "tools/build_docket.py",
    "plate-keys": "tools/build_plate_keys.py",
    "people-index": "tools/build_people_index.py",
    "source-index": "tools/build_source_index.py",
}
WRITE_FLAG_TARGETS = frozenset({"basemap", "fonts"})


def usage() -> str:
    lines = [
        "Usage: ./gen [--pretty] <command> [args]",
        "",
        "The researcher's cockpit: one JSON-first entry point for the genealogy",
        "toolchain. Every non-help command prints exactly one JSON object to stdout",
        '(compact single line; --pretty for indented) carrying at least',
        '{"command", "ok"}. Exit code is 0 iff ok. Wrapped-tool output is in',
        'the "output" field, never raw on stdout.',
        "",
        "Repository commands:",
        "  gate                        Run the full gate (tools/check.sh)",
        "  build <target> [--check]    Rebuild, or verify with --check, one of:",
        "                              basemap fonts citation-backlinks docket",
        "                              plate-keys people-index source-index",
        "  stamp [--write|--check|--deployed]",
        "                              Deploy fingerprint (tools/stamp.py)",
        "                              (no flag means --check)",
        "",
        "Ancestry commands (drive the already-running, logged-in Chrome; never",
        "launch a browser; all reads share a machine-global queue, human pacing,",
        "and the durable acquisition store in research/cache/ancestry - one",
        "latest validated snapshot is kept per page/query, so revisits are free):",
        "  ancestry search --collection N --name Given_Surname",
        "                  [--birth YEAR] [--place P] [--spouse Given_Surname]",
        "                  [--birthplace P] [--exact-name] [--agent ID]",
        "                  [--limit K] [--fresh|--cache-only]",
        "  ancestry record --collection N --id RECORD_ID [--agent ID] [--fresh|--cache-only]",
        "  ancestry household --collection N --id RECORD_ID [--agent ID] [--fresh|--cache-only]",
        "  ancestry goto <address> [--agent ID] [--fresh|--cache-only]",
        "  ancestry open [N] [--agent ID] [--fresh|--cache-only]",
        "  ancestry where | next | prev | back  [--agent ID]",
        "  ancestry session stats|reset --agent ID [--confirm RESET-ANCESTRY-SESSION]",
        "  ancestry cache stats|list [--kind K]",
        "  ancestry cache migrate [--kind K]",
        "  ancestry cache clear (--kind K|--all)",
        "                  [--include-records --confirm DELETE-DURABLE-ANCESTRY-RECORDS]",
        "",
        "  Addresses:  record/COLL/ID",
        "              search/COLL?name=Given_Surname&birth=YEAR&place=P&",
        "                  spouse=Given_Surname&birthplace=P&exact=true",
        "              collection/COLL",
        '  Result fields: "cached":true  = served from cache, Ancestry untouched;',
        '                 "navigated":false = logical location moved from cache',
        "                 without driving the browser tab.",
        "  Default reads: return a valid cache hit immediately; a miss joins the",
        "                 paced queue and fetches live after a lock-time recheck.",
        "  --cache-only: fail on a miss without probing Chrome or Ancestry; use",
        "                only when live access is forbidden, not as a preflight.",
        "",
        "Store commands (the canonical research truth stores; every write is",
        "validated against the repository contracts before it lands, under a",
        "store-wide lock, and never leaves a partial or unattested record):",
        "  evidence add --shard zimmerman|mundell|dible|connelly",
        "               [--validate-only]      (one evidence record as JSON on stdin;",
        "                                       privacy_review.status='passed' required;",
        "                                       acquisition.pull auto-assigned)",
        "  evidence draft --from-cache record/COLL/ID --id ev.ID",
        "               Build a review-required draft from one cached record;",
        "               cache-only, with citation and immutable provenance metadata",
        "  trace new --slug S --title T [--date D] [--case-refs a,b] [--person-refs ...]",
        "            [--evidence-refs ...] [--source-refs ...] [--geo-refs ...]",
        "            [--confidence C] [--outcome S] [--next-action S]",
        "  case update <case.id> [--status S] [--summary S] [--display-prose S]",
        "              [--source-note S] [--add-evidence-ref E] [--add-trace-ref T]",
        "              [--add-person-ref P] [--validate-only]",
        "                              Mutate one case; regenerates the docket",
        "                              region and restamps index.html atomically",
        "  case list [--status S[,S]] [--branch B[,B]]",
        "                              List canonical cases with optional filters",
        "  relationship update <relationship.id> [mutation/ref flags] [--validate-only]",
        "                              Validate and atomically update a family edge",
        "  gap resolve <gap.id> --parent person.id --role father|mother",
        "              --evidence-ref ev.id [resolution flags] [--validate-only]",
        "                              Resolve one parent slot and regenerate projection",
        "  show <id>                   Any case/evidence/source/trace/geo/person/",
        "                              relationship/gap id ->",
        "                              the record + everything referencing it",
        "  status                      Fast dashboard: validators, case histogram,",
        "                              family/evidence counts, latest trace (no Playwright)",
        "  ancestors <person.id>       Walk the family graph upward: generations,",
        "                              per-link confidence, and the gap frontier",
        "  path <a> <b>                Shortest relationship chain between two people",
        "  contradictions [--strict]   Deterministic rule sweep over the family graph:",
        "                              chronology, hygiene, and recorded conflicts",
        "",
        "Help:  ./gen <command> --help   (ancestry forwards to the full subhelp;",
        "       try also: ./gen ancestry goto --help)",
        "",
        "Examples:",
        "  ./gen gate",
        "  ./gen stamp",
        "  ./gen build fonts --check",
        '  ./gen ancestry goto "search/6224?name=Marjorie_Clemans&birth=1912" --agent alice',
        "  ./gen ancestry next --agent alice",
        "  ./gen ancestry open 0 --agent alice",
        "  ./gen show case.07",
        "  ./gen status",
    ]
    return "\n".join(lines)


COMMAND_HELP = {
    "gate": "\n".join([
        "Usage: ./gen gate",
        "",
        "Run the full repository gate (tools/check.sh): geojson + source-index",
        "validation, evidence/case/trace contracts, cross-reference closure,",
        "people index, geo sync, generated-region byte-identity, deploy stamp,",
        "and the Playwright acceptance spec.",
        "",
        'JSON: {"command":"gate","ok":<all passed>,"returncode":N,"output":"..."}',
        "Exit code mirrors check.sh. Requires Playwright locally (CI parity).",
    ]),
    "build": "\n".join([
        "Usage: ./gen build <target> [--check]",
        "",
        "Rebuild a generated artifact, or verify it byte-identical with --check.",
        "",
        "Targets:",
        "  basemap             Natural Earth projection/paths/routes regions",
        "  fonts               Subsetted woff2 data-URI block",
        "  citation-backlinks  'Cited by' backlinks in the Source Ledger",
        "  docket              The Docket case divs (from research/cases)",
        "  plate-keys          Plate marker keys, ledger, and numerals",
        "  people-index        Pedigree registry and static Index of Names",
        "  source-index        research/sources/source-index.json",
        "",
        'JSON: {"command":"build","target":T,"check":bool,"ok":...,"returncode":N,"output":"..."}',
        "Note: a failing --check often just means index.html changed and the",
        "artifact needs a rebuild - read the output field.",
    ]),
    "stamp": "\n".join([
        "Usage: ./gen stamp [--write|--check|--deployed]",
        "",
        "Deploy fingerprint via tools/stamp.py.",
        "  (none)      verify and report the current stamp (same as --check)",
        "  --write     restamp index.html after content changes",
        "  --check     verify the stamp matches content (gate mode)",
        "  --deployed  compare against the live GitHub Pages deployment",
        "",
        'JSON: {"command":"stamp","mode":M,"ok":...,"returncode":N,"output":"..."}',
    ]),
    "evidence": "\n".join([
        "Usage: ./gen evidence add --shard <zimmerman|mundell|dible|connelly> [--validate-only]",
        "       ./gen evidence draft --from-cache record/COLL/ID --id ev.ID [options]",
        "",
        "Append ONE evidence record (JSON object on stdin) to the canonical store.",
        "Safety contract: refuses without an explicit privacy attestation",
        "(privacy_review.status='passed'); refuses duplicate ids; auto-assigns the",
        "next two-digit acquisition.pull within the record's batch; validates the",
        "candidate store in a temp copy BEFORE touching the real shard; writes",
        "atomically under the store lock. --validate-only never writes.",
        "",
        'JSON: {"command":"evidence.add","ok":...,"written":bool,"id":...,"shard":...,"pull":...}',
        "",
        "draft reads one validated record cache entry and never probes Chrome or",
        "Ancestry. Required: --id ev.ID. Options: --record-type TYPE, --title TITLE,",
        "--batch BATCH, and repeatable --person-ref/--case-ref. It returns a",
        "canonical-shaped draft with cache_provenance, pending privacy review,",
        "review warnings, and no write. An unchanged draft is rejected by add.",
        'JSON: {"command":"evidence.draft","ok":...,"cache":{...},"draft":{...},"requires_review":[...]}',
        "Errors carry the repository validator's messages verbatim.",
    ]),
    "trace": "\n".join([
        "Usage: ./gen trace new --slug S --title T [--date YYYY-MM-DD]",
        "         [--case-refs a,b] [--person-refs ...] [--evidence-refs ...]",
        "         [--source-refs ...] [--geo-refs ...] [--confidence C]",
        "         [--outcome STR] [--next-action STR]",
        "",
        "Scaffold a reasoning trace from the canonical template: derived id",
        "(trace.<date>.<slug>), sorted refs, template body. Validated against the",
        "trace contract in a temp copy; the real file is only created after it",
        "passes, so a failure leaves nothing behind.",
        "",
        'JSON: {"command":"trace.new","ok":...,"path":...,"id":...}',
    ]),
    "case": "\n".join([
        "Usage: ./gen case list [--status S[,S]] [--branch B[,B]]",
        "       ./gen case update <case.id> [flags]",
        "",
        "list returns canonical case records, optionally filtered by one or more",
        "comma-separated statuses or branches.",
        "",
        "Mutate ONE canonical case record, truth-first and atomically:",
        "  --status S            open|in_conflict|needs_pull|closed",
        "  --summary S           the docket paragraph (unless display_prose set)",
        "  --display-prose S     richer docket paragraph override ('' clears it)",
        "  --source-note S       the docket's source shorthand (required field)",
        "  --add-evidence-ref E  idempotent append (repeatable)",
        "  --add-trace-ref T     canonical trace.* id; idempotent append (repeatable)",
        "  --add-person-ref P    idempotent append (repeatable)",
        "  --validate-only       full semantic + render validation, no writes",
        "",
        "Under the store lock: validates the candidate store, renders the docket",
        "region + fresh deploy stamp in memory, then writes cases.jsonl and",
        "index.html (both atomic). A no-op rerun self-repairs a stale docket",
        "(crash recovery). Evidence must already list the case in case_refs:",
        "run ./gen evidence add first, then case update --add-evidence-ref.",
        "",
        'JSON: {"command":"case.update","ok":...,"written":...,"changed":{...},',
        '       "added":{...},"already_present":{...},"docket":...,"stamp":...}',
    ]),
    "relationship": "\n".join([
        "Usage: ./gen relationship update <relationship.id> [flags]",
        "",
        "Atomically mutate one canonical family edge and regenerate/restamp the",
        "people projection. Flags:",
        "  --status accepted|hypothesis|rejected",
        "  --confidence documented|strong|lead|open",
        "  --provenance-note TEXT",
        "  --add-evidence-ref ev.ID   (repeatable)",
        "  --add-source-ref src.ID     (repeatable)",
        "  --add-case-ref case.NN      (repeatable)",
        "  --validate-only",
        "A status change requires a new provenance note. References are sorted,",
        "deduplicated, and validated before any write. Rejected edges retain",
        "their canonical ids, refs, and prior provenance, but graph traversal",
        "and pedigree projection ignore them.",
        "",
        'JSON: {"command":"relationship.update","ok":...,"written":...,"id":...,"projection":...}',
    ]),
    "gap": "\n".join([
        "Usage: ./gen gap resolve <gap.id> --parent person.ID --role father|mother",
        "         --evidence-ref ev.ID [--child person.ID] [--source-ref src.ID]",
        "         [--reject-relationship relationship.ID] [--confidence C]",
        "         [--provenance-note TEXT] [--validate-only]",
        "",
        "Resolve one role on a parentage/candidate-parentage gap. The command",
        "creates or promotes the accepted parent edge, requires every competing",
        "hypothesis to be rejected explicitly, narrows remaining roles/pedigree",
        "slots, retains rejected edges as inspectable canonical records, records",
        "durable resolution provenance, and regenerates the people projection and",
        "stamp. An identical replay is a no-op or repairs an interrupted projection.",
        "A fully resolved public gap remains a",
        "canonical resolved tombstone and reports owner_follow_up_required because",
        "person-card prose belongs to the owner.",
        "",
        'JSON: {"command":"gap.resolve","ok":...,"written":...,"relationship_id":...,"resolved":...,"remaining_open_roles":[...]}',
    ]),
    "ancestors": "\n".join([
        "Usage: ./gen ancestors <person.id>",
        "",
        "BFS up the parent links in research/people/relationships.jsonl: every",
        "reachable ancestor grouped by generation, each carrying the linking",
        "relationship id and its confidence. The frontier lists gap.* rows for",
        "walked people whose parents are explicitly unknown - the research edge.",
        "",
        'JSON: {"command":"ancestors","ok":...,"generations":[[...]],"count":N,"frontier":[...]}',
    ]),
    "path": "\n".join([
        "Usage: ./gen path <person.a> <person.b>",
        "",
        "Shortest chain of parent/spouse links between two people, each step",
        "naming the relationship, role, confidence, and relationship id.",
        "",
        'JSON: {"command":"path","ok":...,"length":N,"steps":[{from,to,relationship,...}]}',
    ]),
    "contradictions": "\n".join([
        "Usage: ./gen contradictions [--strict]",
        "",
        "Run the encoded-opinion rules (tools/family_rules.py) over the truth",
        "stores: parent ages, posthumous births, death-before-birth, marriage",
        "ages, confidence-vs-evidence hygiene, open gaps citing closed cases,",
        "and multiple-parent groupings. Vitals come from dated geojson life",
        "events; rejected relationship rows never enter any rule. Severities:",
        "violation = impossibility on accepted dated data (the only gating",
        "level), conflict = deliberately recorded unresolved state, advisory =",
        "the same impossibilities on hypothesis links plus hygiene notes.",
        "",
        'JSON: {"command":"contradictions","ok":...,"clean":...,"counts":{...},"coverage":{...},"findings":[...]}',
        "Exit 0 always; --strict exits 1 iff violations exist.",
    ]),
    "show": "\n".join([
        "Usage: ./gen show <id>",
        "",
        "Resolve any id across the truth stores - case.*, ev.*, src.*, trace ids",
        "or filenames, geojson feature/place ids, person.*, relationship.*, or",
        "gap.* - and return the canonical record plus reverse references.",
        "The orientation verb: start sessions here.",
        "",
        'JSON: {"command":"show","ok":...,"kind":...,"record":{...},"referenced_by":{...}}',
    ]),
    "status": "\n".join([
        "Usage: ./gen status",
        "",
        "Fast research dashboard - no Playwright, no network: store validators",
        "(family/evidence/cases/traces), canonical family counts, case-status",
        "histogram, evidence counts by shard, newest trace. Exit code mirrors health.",
        "",
        'JSON: {"command":"status","ok":...,"validators":{...},"family":{...},"cases":{...},"evidence":{...},"latest_trace":...}',
    ]),
}


def split_global_flags(argv: list[str]) -> tuple[list[str], bool]:
    return [arg for arg in argv if arg != "--pretty"], "--pretty" in argv


def dumps(obj: dict[str, object], pretty: bool) -> str:
    if pretty:
        return json.dumps(obj, indent=2)
    return json.dumps(obj, separators=(",", ":"))


def emit(obj: dict[str, object], pretty: bool) -> None:
    print(dumps(obj, pretty))


def run_captured(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def build_command(target: str, check: bool) -> list[str]:
    command = ["uv", "run", BUILD_TARGETS[target]]
    if check:
        command.append("--check")
    elif target in WRITE_FLAG_TARGETS:
        command.append("--write")
    return command


def json_error(command: str, error: str, pretty: bool, **extra: object) -> int:
    obj: dict[str, object] = {"command": command, "ok": False, "error": error}
    obj.update(extra)
    emit(obj, pretty)
    return 1


def handler_gate(argv: list[str], pretty: bool) -> int:
    if argv:
        return json_error("gate", "unexpected arguments", pretty, arguments=argv)
    result = run_captured(["sh", "tools/check.sh"])
    rc = result.returncode
    emit({"command": "gate", "ok": rc == 0, "returncode": rc, "output": result.stdout or ""}, pretty)
    return rc


def handler_build(argv: list[str], pretty: bool) -> int:
    check = False
    targets: list[str] = []
    unknown: list[str] = []
    for arg in argv:
        if arg == "--check":
            check = True
        elif arg.startswith("-"):
            unknown.append(arg)
        else:
            targets.append(arg)
    if unknown:
        return json_error("build", "unknown arguments", pretty, arguments=unknown)
    if not targets:
        return json_error("build", "missing target", pretty)
    if len(targets) > 1:
        return json_error("build", "unexpected arguments", pretty, arguments=targets[1:])
    target = targets[0]
    if target not in BUILD_TARGETS:
        return json_error("build", "unknown target", pretty, target=target)

    result = run_captured(build_command(target, check))
    rc = result.returncode
    emit(
        {
            "command": "build",
            "target": target,
            "check": check,
            "ok": rc == 0,
            "returncode": rc,
            "output": result.stdout or "",
        },
        pretty,
    )
    return rc


def handler_stamp(argv: list[str], pretty: bool) -> int:
    modes = [arg for arg in argv if arg in {"--write", "--check", "--deployed"}]
    unknown = [arg for arg in argv if arg not in {"--write", "--check", "--deployed"}]
    if unknown:
        return json_error("stamp", "unknown arguments", pretty, arguments=unknown)
    if len(modes) > 1:
        return json_error("stamp", "conflicting mode flags", pretty, arguments=modes)

    mode = modes[0] if modes else "--check"
    result = run_captured(["uv", "run", "tools/stamp.py", mode])
    rc = result.returncode
    emit(
        {
            "command": "stamp",
            "mode": mode.removeprefix("--"),
            "ok": rc == 0,
            "returncode": rc,
            "output": result.stdout or "",
        },
        pretty,
    )
    return rc


def handler_ancestry(argv: list[str], pretty: bool) -> int:
    if not argv:
        return json_error(
            "ancestry",
            "missing subcommand",
            pretty,
            expected=["search", "record", "household", "goto", "where", "next", "prev", "back", "open", "cache"],
        )
    result = subprocess.run(
        ["uv", "run", "tools/gen_ancestry.py", *argv],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out = (result.stdout or "").strip()
    if not out.startswith("{"):
        return json_error(
            "ancestry", "subtool produced no JSON", pretty,
            returncode=result.returncode, stderr=(result.stderr or "").strip()[-800:],
        )
    obj = json.loads(out)  # the subtool emits exactly one clean JSON object
    emit(obj, pretty)
    return 0 if obj.get("ok") else 1


def handler_store(command: str, argv: list[str], pretty: bool) -> int:
    """Forward a truth-store verb to tools/gen_store.py (stdlib-only, so this
    interpreter suffices) and re-emit its single JSON object, preserving the
    subtool's exit code (status mirrors store health)."""
    result = subprocess.run(
        [sys.executable, "tools/gen_store.py", command, *argv],
        cwd=ROOT,
        stdin=None if sys.stdin.isatty() else sys.stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out = (result.stdout or "").strip()
    if not out.startswith("{"):
        return json_error(
            command, "subtool produced no JSON", pretty,
            returncode=result.returncode, stderr=(result.stderr or "").strip()[-800:],
        )
    emit(json.loads(out), pretty)
    return result.returncode


def handler_evidence(argv: list[str], pretty: bool) -> int:
    if argv and argv[0] == "draft":
        result = subprocess.run(
            [sys.executable, "tools/gen_evidence_draft.py", *argv[1:]],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out = (result.stdout or "").strip()
        if not out.startswith("{"):
            return json_error(
                "evidence.draft",
                "subtool produced no JSON",
                pretty,
                returncode=result.returncode,
                stderr=(result.stderr or "").strip()[-800:],
            )
        emit(json.loads(out), pretty)
        return result.returncode
    return handler_store("evidence", argv, pretty)


def handler_trace(argv: list[str], pretty: bool) -> int:
    return handler_store("trace", argv, pretty)


def handler_show(argv: list[str], pretty: bool) -> int:
    return handler_store("show", argv, pretty)


def handler_status(argv: list[str], pretty: bool) -> int:
    return handler_store("status", argv, pretty)


def handler_case(argv: list[str], pretty: bool) -> int:
    return handler_store("case", argv, pretty)


def handler_relationship(argv: list[str], pretty: bool) -> int:
    return handler_store("relationship", argv, pretty)


def handler_gap(argv: list[str], pretty: bool) -> int:
    return handler_store("gap", argv, pretty)


def handler_ancestors(argv: list[str], pretty: bool) -> int:
    return handler_store("ancestors", argv, pretty)


def handler_path(argv: list[str], pretty: bool) -> int:
    return handler_store("path", argv, pretty)


def handler_contradictions(argv: list[str], pretty: bool) -> int:
    return handler_store("contradictions", argv, pretty)


def dispatch(argv: list[str]) -> int:
    args, pretty = split_global_flags(argv)
    if not args or args[0] in {"--help", "-h"}:
        print(usage())
        return 0

    handlers = {
        "gate": handler_gate,
        "build": handler_build,
        "stamp": handler_stamp,
        "ancestry": handler_ancestry,
        "evidence": handler_evidence,
        "trace": handler_trace,
        "case": handler_case,
        "relationship": handler_relationship,
        "gap": handler_gap,
        "ancestors": handler_ancestors,
        "path": handler_path,
        "contradictions": handler_contradictions,
        "show": handler_show,
        "status": handler_status,
    }
    command = args[0]
    if command not in handlers:
        emit({"command": command, "ok": False, "error": "unknown command"}, pretty)
        return 1
    if any(arg in {"--help", "-h"} for arg in args[1:]):
        if command == "ancestry":
            # Forward to the subtool so argparse renders the real, always-current
            # help (works at any depth: `./gen ancestry --help`,
            # `./gen ancestry goto --help`). Help imports no browser dependency,
            # so use this interpreter and remain offline on a cold uv cache.
            result = subprocess.run(
                [sys.executable, "tools/gen_ancestry.py", *args[1:]],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            # The implementation module uses argparse's conventional program
            # name; expose the repository's real, runnable entry point.
            print(
                result.stdout.replace("usage: gen ancestry", "usage: ./gen ancestry"),
                end="",
            )
            return result.returncode
        print(COMMAND_HELP[command])
        return 0
    return handlers[command](args[1:], pretty)


def main() -> int:
    return dispatch(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
