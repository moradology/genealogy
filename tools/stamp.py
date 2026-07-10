#!/usr/bin/env python3
"""Deploy stamp: a content fingerprint committed into index.html.

The stamp is sha256 of index.html with the stamp line itself placeholdered,
truncated to 12 hex chars, plus the stamp date. GitHub Pages has no build
step, so this committed fingerprint is what lets `--deployed` prove the live
site serves the pushed content (no more cache guessing).

  ./gen stamp --write      refresh the stamp after edits
  ./gen stamp --check      fail if content changed since stamping
  ./gen stamp --deployed   compare the live site's stamp digest
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
LIVE_URL = "https://moradology.github.io/genealogy/"
STAMP_RE = re.compile(r'<meta name="deploy-stamp" content="[^"]*">')
PLACEHOLDER = '<meta name="deploy-stamp" content="STAMP">'


def digest_of(html: str) -> str:
    canonical = STAMP_RE.sub(PLACEHOLDER, html)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def current_stamp(html: str) -> str | None:
    match = STAMP_RE.search(html)
    if match is None:
        return None
    return match.group(0).split('content="')[1].rstrip('">')


def stamped_html(html: str) -> tuple[str, str]:
    """Pure restamp: return (html with a current stamp, the stamp string).

    The single source of truth for the stamp format; the CLI write() and the
    cockpit's chained case-update write both go through it. Requires the stamp
    meta (or its placeholder position) to already exist in the document.
    """
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if STAMP_RE.search(html) is None:
        anchor = "</title>\n"
        if anchor not in html:
            raise SystemExit("stamp: no </title> anchor found")
        html = html.replace(anchor, anchor + "  " + PLACEHOLDER + "\n", 1)
    stamp = f"{digest_of(html)} {date}"
    return STAMP_RE.sub(f'<meta name="deploy-stamp" content="{stamp}">', html), stamp


def write() -> int:
    html, stamp = stamped_html(HTML.read_text())
    HTML.write_text(html)
    print(f"stamped: {stamp}")
    return 0


def check() -> int:
    html = HTML.read_text()
    stamp = current_stamp(html)
    if stamp is None:
        print("no deploy stamp present; run ./gen stamp --write", file=sys.stderr)
        return 1
    recorded = stamp.split()[0]
    actual = digest_of(html)
    if recorded != actual:
        print(f"stale stamp: recorded {recorded}, content is {actual}; run ./gen stamp --write", file=sys.stderr)
        return 1
    print(f"stamp current: {stamp}")
    return 0


def deployed() -> int:
    local = current_stamp(HTML.read_text())
    if local is None:
        print("no local stamp; run ./gen stamp --write first", file=sys.stderr)
        return 1
    result = subprocess.run(
        ["curl", "-s", "--max-time", "20", LIVE_URL],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"curl failed with exit {result.returncode}", file=sys.stderr)
        return 1
    remote = current_stamp(result.stdout)
    if remote is None:
        print("live site has no deploy stamp (older build still cached?)", file=sys.stderr)
        return 1
    if remote.split()[0] != local.split()[0]:
        print(f"live {remote} != local {local} (Pages cache max-age is 600s)", file=sys.stderr)
        return 1
    print(f"live site matches local stamp: {local}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--deployed", action="store_true")
    args = parser.parse_args()
    if args.write:
        return write()
    if args.check:
        return check()
    return deployed()


if __name__ == "__main__":
    raise SystemExit(main())
