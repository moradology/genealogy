#!/usr/bin/env python3
"""Acceptance test for the `gen` cockpit CLI (tools/gen.py), chunk 1.

Stdlib only, no pytest, no try/except (a bad JSON parse should crash loudly =
a failure). Run: uv run tools/test_gen.py
Codex-runnable: exercises only the pure-Python wrappers, never the Playwright gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = [sys.executable, "tools/gen.py"]

failures: list[str] = []


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(GEN + args, cwd=ROOT, capture_output=True, text=True)


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}: {detail}")


# 1. --help lists every command, the nav verbs, and the address grammar; exits 0
r = run(["--help"])
check("help exit 0", r.returncode == 0, r.stderr[:200])
for word in ("gate", "build", "stamp", "ancestry", "goto", "record/COLL/ID", "cached"):
    check(f"help mentions {word}", word in r.stdout, r.stdout[:300])

# 1b. per-command help: gen build --help is plain text, exits 0, lists targets
r = run(["build", "--help"])
check("build help exit 0", r.returncode == 0, r.stderr[:200])
check("build help lists targets", "basemap" in r.stdout and "source-index" in r.stdout, r.stdout[:300])
check("build help is not json", not r.stdout.strip().startswith("{"), r.stdout[:80])

# 1c. ancestry help forwards to the subtool's argparse (works offline, no browser)
r = run(["ancestry", "--help"])
check("ancestry help exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
for word in ("goto", "addresses:", "navigated", "human-paced"):
    check(f"ancestry help mentions {word}", word in r.stdout, r.stdout[:400])
r = run(["ancestry", "goto", "--help"])
check("goto help exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
check("goto help shows grammar", "record/COLL/ID" in r.stdout, r.stdout[:300])

# 2. `build <target> --check` prints exactly one JSON object whose ok mirrors
#    the wrapped tool's exit code. Deliberately does NOT require ok==true:
#    concurrent edits to index.html legitimately make --check report stale, and
#    this test's contract is the JSON envelope, not repo cleanliness.
for target in ("source-index", "fonts", "basemap"):
    r = run(["build", target, "--check"])
    obj = json.loads(r.stdout)  # no try/except: invalid JSON crashes = failure
    check(f"build {target} ok is bool", isinstance(obj.get("ok"), bool), r.stdout[:200])
    check(f"build {target} ok mirrors rc", obj.get("ok") == (r.returncode == 0), f"ok={obj.get('ok')} rc={r.returncode}")
    check(f"build {target} target field", obj.get("target") == target, r.stdout[:200])
    check(f"build {target} command field", obj.get("command") == "build", r.stdout[:200])
    check(f"build {target} output is text", isinstance(obj.get("output"), str), r.stdout[:200])

# 3. default output is compact single-line JSON; --pretty is indented multi-line
r = run(["build", "source-index", "--check"])
check("default single-line json", r.stdout.strip().count("\n") == 0, repr(r.stdout[:120]))
rp = run(["build", "source-index", "--check", "--pretty"])
check("pretty is multi-line", rp.stdout.count("\n") > 1, repr(rp.stdout[:120]))
json.loads(rp.stdout)  # still valid JSON

# 4. gate is a registered command (not executed here — it needs Playwright)
check("gate registered in help", "gate" in run(["--help"]).stdout)

# 5. unknown command errors: nonzero exit AND a JSON error object on stdout
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
