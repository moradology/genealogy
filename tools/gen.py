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
    "plate-keys": "tools/build_plate_keys.py",
    "source-index": "tools/build_source_index.py",
}


def usage() -> str:
    lines = [
        "Usage: gen [--pretty] <command> [args]",
        "",
        "The researcher's cockpit: one JSON-first entry point for the genealogy",
        "toolchain. Every command prints exactly one JSON object to stdout",
        '(compact single line; --pretty for indented) carrying at least',
        '{"command", "ok"}. Exit code is 0 iff ok. Wrapped-tool output is in',
        'the "output" field, never raw on stdout.',
        "",
        "Repository commands:",
        "  gate                        Run the full gate (tools/check.sh)",
        "  build <target> [--check]    Rebuild, or verify with --check, one of:",
        "                              basemap fonts citation-backlinks",
        "                              plate-keys source-index",
        "  stamp [--write|--check|--deployed]",
        "                              Deploy fingerprint (tools/stamp.py)",
        "",
        "Ancestry commands (drive the already-running, logged-in Chrome; never",
        "launch a browser; all reads share a machine-global queue, human pacing,",
        "and the durable acquisition store in research/cache/ancestry - every",
        "page ever fetched is kept, so revisits are free and instant):",
        "  ancestry search --collection N --name Given_Surname",
        "                  [--birth YEAR] [--limit K] [--fresh]",
        "  ancestry record --collection N --id RECORD_ID [--fresh]",
        "  ancestry household --collection N --id RECORD_ID [--fresh]",
        "  ancestry goto <address> [--agent ID] [--fresh]",
        "  ancestry open [N] [--agent ID] [--fresh]",
        "  ancestry where | next | prev | back  [--agent ID]",
        "  ancestry cache stats|list|clear [--kind K] [--all]",
        "",
        "  Addresses:  record/COLL/ID",
        "              search/COLL?name=Given_Surname&birth=YEAR",
        "              collection/COLL",
        '  Result fields: "cached":true  = served from cache, Ancestry untouched;',
        '                 "navigated":false = logical location moved from cache',
        "                 without driving the browser tab.",
        "",
        "Help:  gen <command> --help   (ancestry forwards to the full subhelp;",
        "       try also: gen ancestry goto --help)",
        "",
        "Examples:",
        "  gen gate",
        "  gen build fonts --check",
        '  gen ancestry goto "search/6224?name=Marjorie_Clemans&birth=1912" --agent alice',
        "  gen ancestry next --agent alice",
        "  gen ancestry open 0 --agent alice",
    ]
    return "\n".join(lines)


COMMAND_HELP = {
    "gate": "\n".join([
        "Usage: gen gate",
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
        "Usage: gen build <target> [--check]",
        "",
        "Rebuild a generated artifact, or verify it byte-identical with --check.",
        "",
        "Targets:",
        "  basemap             Natural Earth projection/paths/routes regions",
        "  fonts               Subsetted woff2 data-URI block",
        "  citation-backlinks  'Cited by' backlinks in the Source Ledger",
        "  plate-keys          Plate marker keys, ledger, and numerals",
        "  source-index        research/sources/source-index.json",
        "",
        'JSON: {"command":"build","target":T,"check":bool,"ok":...,"returncode":N,"output":"..."}',
        "Note: a failing --check often just means index.html changed and the",
        "artifact needs a rebuild - read the output field.",
    ]),
    "stamp": "\n".join([
        "Usage: gen stamp [--write|--check|--deployed]",
        "",
        "Deploy fingerprint via tools/stamp.py.",
        "  (none)      report the current stamp state",
        "  --write     restamp index.html after content changes",
        "  --check     verify the stamp matches content (gate mode)",
        "  --deployed  compare against the live GitHub Pages deployment",
        "",
        'JSON: {"command":"stamp","ok":...,"returncode":N,"output":"..."}',
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

    cmd = ["uv", "run", BUILD_TARGETS[target]]
    if check:
        cmd.append("--check")
    result = run_captured(cmd)
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

    result = run_captured(["uv", "run", "tools/stamp.py", *modes])
    rc = result.returncode
    emit({"command": "stamp", "ok": rc == 0, "returncode": rc, "output": result.stdout or ""}, pretty)
    return rc


def handler_ancestry(argv: list[str], pretty: bool) -> int:
    if not argv:
        return json_error("ancestry", "missing subcommand", pretty, expected=["search", "record", "household"])
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
    }
    command = args[0]
    if command not in handlers:
        emit({"command": command, "ok": False, "error": "unknown command"}, pretty)
        return 1
    if any(arg in {"--help", "-h"} for arg in args[1:]):
        if command == "ancestry":
            # Forward to the subtool so argparse renders the real, always-current
            # help (works at any depth: `gen ancestry --help`, `... goto --help`).
            result = subprocess.run(
                ["uv", "run", "tools/gen_ancestry.py", *args[1:]],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            print(result.stdout, end="")
            return result.returncode
        print(COMMAND_HELP[command])
        return 0
    return handlers[command](args[1:], pretty)


def main() -> int:
    return dispatch(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
