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
        "Commands:",
        "  gate                         Run the full repository gate",
        "  build <target> [--check]     Build or check a generated artifact",
        "  stamp [--write|--check|--deployed]",
        "  ancestry <search|record|household> ...   Read the live CDP session as JSON",
        "",
        "Build targets:",
        "  basemap  fonts  citation-backlinks  plate-keys  source-index",
    ]
    return "\n".join(lines)


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
    if not args or any(arg in {"--help", "-h"} for arg in args):
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
    return handlers[command](args[1:], pretty)


def main() -> int:
    return dispatch(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
