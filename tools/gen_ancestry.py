#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright"]
# ///
"""Read Ancestry records as JSON by driving an ALREADY-RUNNING Chrome CDP session.

Never launches a browser: it connects over CDP (http://localhost:9222) to the
single, human-paced session the researcher already opened and logged in. That
honors the Ancestry ToS posture (one human-paced session, no automation of
login/settings) and keeps raw pages out of the repo — this only emits parsed
JSON to stdout; the raw image capture stays a manual "Save to your computer".

JSON-first. No try/except: the common failure (browser not up) is detected by a
plain socket probe and returned as a clean JSON error; genuinely unexpected
errors fail fast.

Commands:
  search  --collection N --name Given_Surname [--birth YEAR] [--limit K]
  record  --collection N --id RECORD_ID
  household --collection N --id RECORD_ID   (record, household members only)
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import random
import socket
import time
from pathlib import Path

CDP_URL = "http://localhost:9222"
CDP_HOST, CDP_PORT = "localhost", 9222

# Machine-global state, shared by EVERY agent that uses this CLI (not repo-
# relative, so it serializes across sessions/clones and stays out of git). One
# Ancestry account, one global queue + one cache.
STATE_DIR = Path.home() / ".gen-cockpit" / "ancestry"
CACHE_DIR = STATE_DIR / "cache"
LOCK_PATH = STATE_DIR / "queue.lock"
LAST_PATH = STATE_DIR / "last_request"
# Minimum seconds between REAL Ancestry hits, across all agents (human pace).
MIN_INTERVAL = float(os.environ.get("GEN_ANCESTRY_MIN_INTERVAL", "5.0"))
JITTER_MAX = float(os.environ.get("GEN_ANCESTRY_JITTER", "2.5"))


def emit(obj: dict) -> None:
    print(json.dumps(obj, separators=(",", ":")))


def ensure_state() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def cache_key(kind: str, parts: dict) -> str:
    raw = kind + "|" + "|".join(f"{k}={parts[k]}" for k in sorted(parts))
    return kind + "-" + hashlib.sha1(raw.encode()).hexdigest()[:16]


def cache_read(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def cache_write(key: str, obj: dict) -> None:
    ensure_state()
    (CACHE_DIR / f"{key}.json").write_text(json.dumps(obj, separators=(",", ":")))


def throttle() -> None:
    """Human-pace real hits: wait out MIN_INTERVAL since the last global request."""
    if LAST_PATH.exists():
        last = float(LAST_PATH.read_text().strip() or "0")
        wait = MIN_INTERVAL - (time.time() - last)
        if wait > 0:
            time.sleep(wait + random.uniform(0, JITTER_MAX))
    LAST_PATH.write_text(str(time.time()))


def locked_fetch(fetch):
    """Serialize + pace a real Ancestry hit across ALL agents via a global flock.

    LOCK_EX blocks until this process is next in line (that is the queue). The
    lock is released when the file closes at the end of the `with` -- including
    on crash, because the OS frees the fd -- so a dead agent never wedges it.
    No try/except: `with open` guarantees the release.
    """
    ensure_state()
    with open(LOCK_PATH, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        throttle()
        return fetch()


def cdp_up() -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.5)
    code = sock.connect_ex((CDP_HOST, CDP_PORT))
    sock.close()
    return code == 0


# ---- innerText parsing (pure functions, unit-testable without a browser) ----

def parse_detail_fields(text: str) -> dict[str, str]:
    """Label\\tValue pairs in the record's Detail section (before the household)."""
    fields: dict[str, str] = {}
    start = text.find("Detail")
    if start < 0:
        return fields
    stop_markers = ["Household Members", "\nSource\n", "Save this record"]
    stops = [text.find(m, start) for m in stop_markers if text.find(m, start) > 0]
    end = min(stops) if stops else len(text)
    for line in text[start:end].splitlines():
        if "\t" in line:
            label, _, value = line.partition("\t")
            label, value = label.strip(), value.strip()
            if label and value and label not in fields:
                fields[label] = value
    return fields


def parse_household(text: str) -> list[dict[str, str]]:
    """Household members below the 'Household Members' header.

    Ancestry interleaves blank lines, so rows arrive either tab-joined
    ('Name\\tAge\\tRelation') or as a name line followed by an age line and a
    relationship line. Both shapes are folded into {name, age, relation}.
    """
    header = text.find("Household Members")
    if header < 0:
        return []
    body = text[header:]
    for marker in ("\nSource\n", "Save this record", "Listen and explore", "Suggested records"):
        cut = body.find(marker)
        if cut > 0:
            body = body[:cut]
    # drop the header line itself
    body = body.split("\n", 1)[1] if "\n" in body else ""
    tokens = [ln.strip() for ln in body.splitlines() if ln.strip()]

    members: list[dict[str, str]] = []
    pending_name: str | None = None
    pending_age: str | None = None
    for tok in tokens:
        if "\t" in tok:
            parts = [p.strip() for p in tok.split("\t") if p.strip()]
            if len(parts) >= 3:
                members.append({"name": parts[0], "age": parts[1], "relation": parts[2]})
            elif len(parts) == 2:
                members.append({"name": parts[0], "age": "", "relation": parts[1]})
            pending_name = pending_age = None
            continue
        if pending_name is None:
            pending_name = tok
        elif pending_age is None and tok.isdigit():
            pending_age = tok
        else:
            members.append({"name": pending_name, "age": pending_age or "", "relation": tok})
            pending_name = pending_age = None
    if pending_name is not None:
        members.append({"name": pending_name, "age": pending_age or "", "relation": ""})
    return members


# ---- browser-driven commands ----

def get_ancestry_page(context):
    pages = context.pages
    for page in pages:
        if "ancestry." in page.url:
            return page
    return pages[0] if pages else context.new_page()


def run_on_page(fn):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = get_ancestry_page(context)
        page.bring_to_front()
        return fn(page)


SEARCH_JS = r"""() => {
  const out = [];
  document.querySelectorAll('a[href*="/records/"]').forEach(a => {
    const tr = a.closest('tr'); if (!tr) return;
    const cells = [...tr.querySelectorAll('td')].map(td => td.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean);
    const m = a.href.match(/records\/(\d+)/);
    out.push({
      record_id: m ? m[1] : null,
      url: a.href.split('?')[0],
      cells,
      text: tr.innerText.replace(/\s+/g, ' ').trim().slice(0, 220),
    });
  });
  const seen = new Set();
  return out.filter(o => o.record_id && !seen.has(o.record_id) && seen.add(o.record_id));
}"""


def cmd_search(args) -> int:
    key = cache_key("search", {"collection": args.collection, "name": args.name, "birth": args.birth or "", "limit": args.limit})
    if not args.fresh:
        hit = cache_read(key)
        if hit is not None:
            emit({**hit, "cached": True})
            return 0
    if not cdp_up():
        emit({"command": "ancestry.search", "ok": False, "error": "cdp browser not reachable on :9222"})
        return 1
    url = f"https://www.ancestry.com/search/collections/{args.collection}/?name={args.name}"
    if args.birth:
        url += f"&birth={args.birth}"

    def fetch():
        def go(page):
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3200)
            return page.evaluate(SEARCH_JS)
        return run_on_page(go)

    rows = locked_fetch(fetch)
    obj = {
        "command": "ancestry.search",
        "ok": True,
        "collection": args.collection,
        "name": args.name,
        "count": len(rows),
        "results": rows[: args.limit],
    }
    cache_write(key, obj)
    emit({**obj, "cached": False})
    return 0


def _read_record(args, household_only: bool) -> int:
    kind = "household" if household_only else "record"
    cmd = f"ancestry.{kind}"
    key = cache_key(kind, {"collection": args.collection, "id": args.id})
    if not args.fresh:
        hit = cache_read(key)
        if hit is not None:
            emit({**hit, "cached": True})
            return 0
    if not cdp_up():
        emit({"command": cmd, "ok": False, "error": "cdp browser not reachable on :9222"})
        return 1
    url = f"https://www.ancestry.com/search/collections/{args.collection}/records/{args.id}"

    def fetch():
        def go(page):
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            return page.evaluate("() => document.body.innerText")
        return run_on_page(go)

    text = locked_fetch(fetch)
    household = parse_household(text)
    obj: dict = {"command": cmd, "ok": True, "collection": args.collection, "record_id": args.id, "household": household}
    if not household_only:
        obj["fields"] = parse_detail_fields(text)
    cache_write(key, obj)
    emit({**obj, "cached": False})
    return 0


def cmd_record(args) -> int:
    return _read_record(args, household_only=False)


def cmd_household(args) -> int:
    return _read_record(args, household_only=True)


def main() -> int:
    parser = argparse.ArgumentParser(prog="gen_ancestry", add_help=True)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("--collection", required=True)
    p_search.add_argument("--name", required=True, help="Given_Surname (Ancestry format)")
    p_search.add_argument("--birth")
    p_search.add_argument("--limit", type=int, default=25)
    p_search.add_argument("--fresh", action="store_true", help="bypass cache, force a live fetch")
    p_search.set_defaults(func=cmd_search)

    for name in ("record", "household"):
        p = sub.add_parser(name)
        p.add_argument("--collection", required=True)
        p.add_argument("--id", required=True)
        p.add_argument("--fresh", action="store_true", help="bypass cache, force a live fetch")
        p.set_defaults(func=cmd_record if name == "record" else cmd_household)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
