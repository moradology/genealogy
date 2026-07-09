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
import re
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
AGENTS_DIR = STATE_DIR / "agents"       # per-agent cursor + history, one file each
TABS_PATH = STATE_DIR / "tabs.json"     # agent-id -> CDP targetId (its own tab)
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

def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, obj) -> None:
    ensure_state()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, separators=(",", ":")))


def new_agent_state() -> dict:
    return {"location": None, "results": [], "cursor": 0, "history": []}


def load_agent(agent: str) -> dict:
    return load_json(AGENTS_DIR / f"{agent}.json", new_agent_state())


def save_agent(agent: str, state: dict) -> None:
    save_json(AGENTS_DIR / f"{agent}.json", state)


def target_id(context, page) -> str:
    session = context.new_cdp_session(page)
    return session.send("Target.getTargetInfo")["targetInfo"]["targetId"]


def get_agent_page(context, agent: str):
    """The agent's own tab, matched by CDP targetId across CLI invocations."""
    tabs = load_json(TABS_PATH, {})
    want = tabs.get(agent)
    if want:
        for page in context.pages:
            if target_id(context, page) == want:
                return page
    page = context.new_page()
    tabs[agent] = target_id(context, page)
    save_json(TABS_PATH, tabs)
    return page


def run_on_page(fn, agent="default"):
    """Every command drives its agent's OWN tab (stateless commands share the
    reserved "default" agent tab). The human's logged-in tab is never touched."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = get_agent_page(context, agent)
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
    # Cache key is limit-free and the FULL result set is cached; --limit only
    # trims the emitted view. One query = at most one real hit, ever.
    key = cache_key("search", {"collection": args.collection, "name": args.name, "birth": args.birth or ""})
    if not args.fresh:
        hit = cache_read(key)
        if hit is not None:
            emit({**hit, "results": hit["results"][: args.limit], "cached": True})
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
        return run_on_page(go, agent="default")

    rows = locked_fetch(fetch)
    obj = {
        "command": "ancestry.search",
        "ok": True,
        "collection": args.collection,
        "name": args.name,
        "count": len(rows),
        "results": rows,
    }
    cache_write(key, obj)
    emit({**obj, "results": rows[: args.limit], "cached": False})
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
        return run_on_page(go, agent="default")

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


# ---- relative navigation: an agent moves through Ancestry by address ----

def parse_address(addr: str) -> dict | None:
    m = re.fullmatch(r"record/([^/]+)/([^/]+)", addr)
    if m:
        return {"type": "record", "collection": m.group(1), "id": m.group(2)}
    m = re.fullmatch(r"collection/([^/?]+)", addr)
    if m:
        return {"type": "collection", "collection": m.group(1)}
    m = re.fullmatch(r"search/([^/?]+)(?:\?(.*))?", addr)
    if m:
        params = dict(p.split("=", 1) for p in (m.group(2) or "").split("&") if "=" in p)
        return {"type": "search", "collection": m.group(1), "name": params.get("name", ""), "birth": params.get("birth", "")}
    return None


def url_for(loc: dict) -> str:
    base = f"https://www.ancestry.com/search/collections/{loc['collection']}"
    if loc["type"] == "record":
        return f"{base}/records/{loc['id']}"
    if loc["type"] == "collection":
        return f"{base}/"
    url = f"{base}/?name={loc['name']}"
    if loc.get("birth"):
        url += f"&birth={loc['birth']}"
    return url


def location_key(loc: dict) -> str | None:
    if loc["type"] == "record":
        return cache_key("record", {"collection": loc["collection"], "id": loc["id"]})
    if loc["type"] == "search":
        # Same limit-free key as cmd_search: one query, one cache entry, shared
        # by the stateless and navigational paths.
        return cache_key("search", {"collection": loc["collection"], "name": loc["name"], "birth": loc.get("birth", "")})
    return None


def fetch_location(agent: str, loc: dict) -> dict:
    """Drive the agent's tab to loc (a real hit, queued + paced) -> structured data."""
    def fetch():
        def go(page):
            page.goto(url_for(loc), wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000 if loc["type"] == "record" else 3200)
            if loc["type"] == "search":
                return {"results": page.evaluate(SEARCH_JS)}
            if loc["type"] == "record":
                return {"text": page.evaluate("() => document.body.innerText")}
            return {}
        return run_on_page(go, agent=agent)

    got = locked_fetch(fetch)
    if loc["type"] == "search":
        rows = got["results"]
        return {"command": "ancestry.search", "ok": True, "collection": loc["collection"], "name": loc["name"], "count": len(rows), "results": rows}
    if loc["type"] == "record":
        text = got["text"]
        return {"command": "ancestry.record", "ok": True, "collection": loc["collection"], "record_id": loc["id"], "household": parse_household(text), "fields": parse_detail_fields(text)}
    return {"command": "ancestry.collection", "ok": True, "collection": loc["collection"]}


def go_to_location(agent: str, loc: dict, push: bool, fresh: bool) -> int:
    """Move an agent to loc. Serve from cache without a hit when possible; only
    the actual browser navigation is a real (queued, paced) hit."""
    state = load_agent(agent)
    key = location_key(loc)
    data = cache_read(key) if (key and not fresh) else None
    navigated = False
    if data is None:
        if not cdp_up():
            emit({"command": "ancestry.goto", "ok": False, "error": "cdp browser not reachable on :9222"})
            return 1
        data = fetch_location(agent, loc)
        navigated = True
        if key:
            cache_write(key, data)
    if push and state.get("location") is not None and state["location"] != loc:
        state["history"].append(state["location"])
    state["location"] = loc
    if loc["type"] == "search":
        state["results"] = data.get("results", [])
        state["cursor"] = 0
    save_agent(agent, state)
    emit({"command": "ancestry.goto", "ok": True, "agent": agent, "location": loc, "navigated": navigated, "data": data})
    return 0


def cmd_goto(args) -> int:
    loc = parse_address(args.address)
    if loc is None:
        emit({"command": "ancestry.goto", "ok": False, "error": "unparseable address", "address": args.address})
        return 1
    return go_to_location(args.agent or "default", loc, push=True, fresh=args.fresh)


def cmd_where(args) -> int:
    agent = args.agent or "default"
    state = load_agent(agent)
    loc = state.get("location")
    cursor_at = None
    if loc and loc.get("type") == "search":
        res, cur = state.get("results", []), state.get("cursor", 0)
        cursor_at = {"cursor": cur, "count": len(res), "result": res[cur] if 0 <= cur < len(res) else None}
    emit({"command": "ancestry.where", "ok": True, "agent": agent, "location": loc,
          "history_depth": len(state.get("history", [])), "cursor_at": cursor_at})
    return 0


def step(agent: str, delta: int) -> int:
    state = load_agent(agent)
    res = state.get("results", [])
    if not res:
        emit({"command": "ancestry.step", "ok": False, "error": "no active search; goto a search first", "agent": agent})
        return 1
    cur = max(0, min(len(res) - 1, state.get("cursor", 0) + delta))
    state["cursor"] = cur
    save_agent(agent, state)
    emit({"command": "ancestry.step", "ok": True, "agent": agent, "cursor": cur, "count": len(res), "result": res[cur]})
    return 0


def cmd_next(args) -> int:
    return step(args.agent or "default", 1)


def cmd_prev(args) -> int:
    return step(args.agent or "default", -1)


def cmd_open(args) -> int:
    agent = args.agent or "default"
    state = load_agent(agent)
    res = state.get("results", [])
    if not res:
        emit({"command": "ancestry.open", "ok": False, "error": "no active search results", "agent": agent})
        return 1
    n = args.n if args.n is not None else state.get("cursor", 0)
    if not (0 <= n < len(res)):
        emit({"command": "ancestry.open", "ok": False, "error": "index out of range", "n": n, "count": len(res)})
        return 1
    loc = state.get("location") or {}
    record = {"type": "record", "collection": loc.get("collection"), "id": res[n]["record_id"]}
    return go_to_location(agent, record, push=True, fresh=args.fresh)


def cmd_back(args) -> int:
    agent = args.agent or "default"
    state = load_agent(agent)
    history = state.get("history", [])
    if not history:
        emit({"command": "ancestry.back", "ok": False, "error": "no history", "agent": agent})
        return 1
    previous = history.pop()
    state["history"] = history
    save_agent(agent, state)
    return go_to_location(agent, previous, push=False, fresh=False)


EPILOG = """\
addresses:
  record/COLL/ID                          one record's detail page
  search/COLL?name=Given_Surname&birth=Y  a collection search (birth optional)
  collection/COLL                         a collection's landing page

semantics (what an agent must know):
  - Never launches a browser: connects to the already-running, logged-in Chrome
    (CDP :9222). If it is down, you get {"ok":false,"error":"cdp browser not
    reachable on :9222"} - ask the human to start it.
  - Every real Ancestry hit is serialized through a machine-global queue and
    human-paced (>= GEN_ANCESTRY_MIN_INTERVAL seconds apart, default 5, plus
    jitter) across ALL agents. You never need to rate-limit yourself.
  - Cache-first: repeat reads return instantly with "cached":true and never
    touch Ancestry (records cache forever; searches until --fresh).
  - --agent ID gives you your own browser tab plus your own cursor and history
    (state in ~/.gen-cockpit/ancestry/). Stateless commands share the reserved
    "default" tab. The human's own tab is never driven. Use one process per
    agent id at a time.
  - Your location is LOGICAL: a cache-served goto/back updates state without
    moving the tab; the "navigated" field reports whether the browser moved.
  - next/prev/where are pure local state: zero Ancestry hits.
  - Search reads page 1 only (up to ~20 rows); next stops at the page edge.

typical session:
  goto "search/6224?name=Marjorie_Clemans&birth=1912" --agent alice
  next --agent alice          # step the cursor through results, free
  open --agent alice          # open the record under the cursor (one hit)
  where --agent alice         # {location, history_depth, cursor_at}
  back --agent alice          # usually cache-served: "navigated":false
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gen ancestry",
        description=(
            "Read Ancestry as structured JSON through the shared, human-paced "
            "browser session. Emits exactly one JSON object per invocation; "
            "no HTML or DOM ever reaches the caller."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="<command>")

    # stateless data commands (one-shot JSON, reserved "default" tab)
    p_search = sub.add_parser(
        "search", help="run a collection search -> {count, results:[{record_id, cells, text}]}",
        description="Search one collection. Full result set is cached; --limit trims only the emitted view.")
    p_search.add_argument("--collection", required=True, metavar="N", help="Ancestry collection id (e.g. 6224 = 1930 census)")
    p_search.add_argument("--name", required=True, metavar="GIVEN_SURNAME", help="underscore-joined, e.g. Marjorie_Clemans")
    p_search.add_argument("--birth", metavar="YEAR", help="approximate birth year filter")
    p_search.add_argument("--limit", type=int, default=25, metavar="K", help="max results to emit (default 25)")
    p_search.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
    p_search.set_defaults(func=cmd_search)

    for name, desc in (
        ("record", "read one record -> {fields:{label:value}, household:[{name,age,relation}]}"),
        ("household", "read one record, household members only"),
    ):
        p = sub.add_parser(name, help=desc, description=desc + ". Records are immutable; cached forever.")
        p.add_argument("--collection", required=True, metavar="N", help="Ancestry collection id")
        p.add_argument("--id", required=True, metavar="RECORD_ID", help="record id within the collection")
        p.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
        p.set_defaults(func=cmd_record if name == "record" else cmd_household)

    # stateful navigation (per-agent tab + cursor + history)
    p_goto = sub.add_parser(
        "goto", help="move your agent to an address -> {location, navigated, data}",
        description="Move to an address (see epilog for the grammar). Pushes the previous location onto your history.")
    p_goto.add_argument("address", help="record/COLL/ID | search/COLL?name=..&birth=.. | collection/COLL")
    p_goto.add_argument("--agent", metavar="ID", help="your agent id (own tab, cursor, history); default: 'default'")
    p_goto.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
    p_goto.set_defaults(func=cmd_goto)

    for name, func, desc in (
        ("where", cmd_where, "report your logical location, history depth, and cursor -> no Ancestry hit"),
        ("next", cmd_next, "step the search cursor forward -> {cursor, result}; no Ancestry hit"),
        ("prev", cmd_prev, "step the search cursor back -> {cursor, result}; no Ancestry hit"),
        ("back", cmd_back, "pop history and return there (usually cache-served)"),
    ):
        p = sub.add_parser(name, help=desc, description=desc + ".")
        p.add_argument("--agent", metavar="ID", help="your agent id; default: 'default'")
        p.set_defaults(func=func)

    p_open = sub.add_parser(
        "open", help="open search result N, or the one under your cursor -> a record",
        description="Open result N of your current search (0-based); with no N, opens the result under your cursor.")
    p_open.add_argument("n", nargs="?", type=int, default=None, metavar="N", help="0-based result index (default: cursor)")
    p_open.add_argument("--agent", metavar="ID", help="your agent id; default: 'default'")
    p_open.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
    p_open.set_defaults(func=cmd_open)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
