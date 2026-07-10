#!/usr/bin/env python3
"""Offline acceptance test for the repository's `./gen` cockpit CLI.

Stdlib only, no pytest, no try/except (a bad JSON parse should crash loudly =
a failure). Run: uv run tools/test_gen.py
Codex-runnable: exercises only the pure-Python wrappers, never the Playwright gate.
"""

from __future__ import annotations

import json
import importlib.util
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
GEN = [str(ROOT / "gen")]
SPEC = importlib.util.spec_from_file_location("gen_cli", ROOT / "tools" / "gen.py")
assert SPEC is not None and SPEC.loader is not None
gen_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_cli)

failures: list[str] = []


def run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(GEN + args, cwd=ROOT, capture_output=True, text=True, env=env)


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}: {detail}")


# 0. The documented repository-local entry point exists and is executable.
check("root entry point exists", (ROOT / "gen").is_file())
check("root entry point executable", bool((ROOT / "gen").stat().st_mode & 0o111))

# 1. --help lists every built command, the nav verbs, and the address grammar;
# exits 0 and uses the actual repository-local invocation.
r = run(["--help"])
check("help exit 0", r.returncode == 0, r.stderr[:200])
check("help uses runnable entry point", "Usage: ./gen" in r.stdout, r.stdout[:200])
for word in (
    "gate",
    "build",
    "stamp",
    "ancestry",
    "goto",
    "record/COLL/ID",
    "cached",
    "--cache-only",
    "DELETE-DURABLE-ANCESTRY-RECORDS",
    "a miss joins the",
    "evidence draft",
    "case list",
    "relationship update",
    "gap resolve",
    "session stats",
    "cache migrate",
    "--exact-name",
):
    check(f"help mentions {word}", word in r.stdout, r.stdout[:300])

# 1b. per-command help: ./gen build --help is plain text, exits 0, lists targets
r = run(["build", "--help"])
check("build help exit 0", r.returncode == 0, r.stderr[:200])
check(
    "build help lists targets",
    "basemap" in r.stdout and "people-index" in r.stdout and "source-index" in r.stdout,
    r.stdout[:300],
)
check("build help is not json", not r.stdout.strip().startswith("{"), r.stdout[:80])

# 1c. ancestry help forwards to the subtool's argparse (works offline, no browser)
r = run(["ancestry", "--help"])
check("ancestry help exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
for word in ("goto", "addresses:", "navigated", "human-paced", "no --cache-only preflight is needed"):
    check(f"ancestry help mentions {word}", word in r.stdout, r.stdout[:400])
r = run(["ancestry", "goto", "--help"])
check("goto help exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
check("goto help shows grammar", "record/COLL/ID" in r.stdout, r.stdout[:300])
check("forwarded help uses runnable entry point", "usage: ./gen ancestry goto" in r.stdout, r.stdout[:300])
check("goto help exposes offline mode", "--cache-only" in r.stdout, r.stdout[:300])
r = run(["ancestry", "cache", "--help"])
check("cache help exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
check(
    "cache help exposes durable-record guard",
    "--include-records" in r.stdout and "--confirm" in r.stdout,
    r.stdout[:400],
)

# 1d. Canonical store verbs are wired through the repository entry point and
# expose plain-text help without touching any truth store.
for command, expected in (
    ("evidence", "evidence draft"),
    ("case", "case list"),
    ("relationship", "relationship update"),
    ("gap", "gap resolve"),
    ("ancestors", "frontier lists"),
    ("path", "Shortest chain"),
):
    r = run([command, "--help"])
    check(f"{command} help exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
    check(f"{command} help describes command", expected in r.stdout, r.stdout[:400])
    check(f"{command} help is not json", not r.stdout.strip().startswith("{"), r.stdout[:80])

with patch.object(gen_cli, "handler_store", return_value=0) as store_handler:
    check(
        "relationship wrapper returns store result",
        gen_cli.handler_relationship(["update", "relationship.example", "--validate-only"], False) == 0,
    )
    store_handler.assert_called_once_with(
        "relationship", ["update", "relationship.example", "--validate-only"], False
    )
with patch.object(gen_cli, "handler_store", return_value=0) as store_handler:
    check(
        "gap wrapper returns store result",
        gen_cli.handler_gap(
            ["resolve", "gap.example", "--parent", "person.example", "--role", "father"],
            False,
        ) == 0,
    )
    store_handler.assert_called_once_with(
        "gap",
        ["resolve", "gap.example", "--parent", "person.example", "--role", "father"],
        False,
    )

# 2. `build <target> --check` prints exactly one JSON object whose ok mirrors
#    the wrapped tool's exit code. Deliberately does NOT require ok==true:
#    concurrent edits to index.html legitimately make --check report stale, and
#    this test's contract is the JSON envelope, not repo cleanliness.
for target in ("source-index", "people-index"):
    r = run(["build", target, "--check"])
    obj = json.loads(r.stdout)  # no try/except: invalid JSON crashes = failure
    check(f"build {target} ok is bool", isinstance(obj.get("ok"), bool), r.stdout[:200])
    check(f"build {target} ok mirrors rc", obj.get("ok") == (r.returncode == 0), f"ok={obj.get('ok')} rc={r.returncode}")
    check(f"build {target} target field", obj.get("target") == target, r.stdout[:200])
    check(f"build {target} command field", obj.get("command") == "build", r.stdout[:200])
    check(f"build {target} output is text", isinstance(obj.get("output"), str), r.stdout[:200])

# Default builds really mean writes. The two generators with required mode
# flags must receive --write; the legacy default-write generators must not.
check(
    "default basemap build passes write mode",
    gen_cli.build_command("basemap", False)[-1] == "--write",
    str(gen_cli.build_command("basemap", False)),
)
check(
    "default fonts build passes write mode",
    gen_cli.build_command("fonts", False)[-1] == "--write",
    str(gen_cli.build_command("fonts", False)),
)
check(
    "default source-index build keeps native write mode",
    "--write" not in gen_cli.build_command("source-index", False),
    str(gen_cli.build_command("source-index", False)),
)
for target in gen_cli.BUILD_TARGETS:
    command = gen_cli.build_command(target, True)
    check(
        f"check command for {target} is explicit and offline to construct",
        command[-1] == "--check" and command[2] == gen_cli.BUILD_TARGETS[target],
        str(command),
    )

# 3. default output is compact single-line JSON; --pretty is indented multi-line
r = run(["build", "source-index", "--check"])
check("default single-line json", r.stdout.strip().count("\n") == 0, repr(r.stdout[:120]))
rp = run(["build", "source-index", "--check", "--pretty"])
check("pretty is multi-line", rp.stdout.count("\n") > 1, repr(rp.stdout[:120]))
json.loads(rp.stdout)  # still valid JSON

# 4. A bare stamp means a local check. This is safe offline and must never
# forward an empty mode list to tools/stamp.py's required argument group.
r = run(["stamp"])
obj = json.loads(r.stdout)
check("bare stamp command field", obj.get("command") == "stamp", r.stdout[:200])
check("bare stamp defaults to check", obj.get("mode") == "check", r.stdout[:200])
check("bare stamp ok mirrors rc", obj.get("ok") == (r.returncode == 0), r.stdout[:200])
check("bare stamp avoids argparse mode error", "one of the arguments" not in obj.get("output", ""), r.stdout[:200])

r = run(["stamp", "--write", "--check"])
obj = json.loads(r.stdout)
check("stamp rejects conflicting modes", r.returncode != 0 and obj.get("ok") is False, r.stdout[:200])

# 5. gate is a registered command (not executed here — it needs Playwright)
check("gate registered in help", "gate" in run(["--help"]).stdout)

# 6. Ancestry JSON forwarding is unit-tested without asking uv to resolve the
# Playwright dependency. The ancestry module's own suite exercises real cache
# administration against temporary directories.
fake = subprocess.CompletedProcess(
    args=["uv", "run", "tools/gen_ancestry.py", "cache", "stats"],
    returncode=0,
    stdout='{"command":"ancestry.cache.stats","ok":true,"entries":0}\n',
    stderr="",
)
stream = io.StringIO()
with patch.object(gen_cli.subprocess, "run", return_value=fake) as ancestry_run, redirect_stdout(stream):
    code = gen_cli.handler_ancestry(["cache", "stats"], False)
obj = json.loads(stream.getvalue())
check("ancestry wrapper exits cleanly", code == 0, stream.getvalue()[:200])
check(
    "ancestry wrapper forwards JSON",
    obj.get("command") == "ancestry.cache.stats" and obj.get("ok") is True and obj.get("entries") == 0,
    stream.getvalue()[:300],
)
forwarded = ancestry_run.call_args.args[0]
check(
    "ancestry wrapper forwards arguments",
    forwarded[-2:] == ["cache", "stats"],
    str(forwarded),
)

# 7. unknown command errors: nonzero exit AND a JSON error object on stdout
r = run(["frobnicate"])
check("unknown command nonzero exit", r.returncode != 0, f"rc={r.returncode}")
obj = json.loads(r.stdout) if r.stdout.strip() else {}
check("unknown command json error", obj.get("ok") is False and "error" in obj, r.stdout[:200])

if failures:
    print("GEN COCKPIT TEST FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("gen cockpit chunk 1: all contract checks passed")
