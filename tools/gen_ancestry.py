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
  search  --collection N --name Given_Surname [filters] [--limit K]
  record  --collection N --id RECORD_ID
  household --collection N --id RECORD_ID   (record, household members only)
  goto/where/next/prev/open/back --agent ID  (private logical navigation)
  cache stats|list|migrate|clear             (durable-store administration)
  session stats|reset --agent ID             (per-agent hit accounting)

Live-capable commands are cache-first by default and automatically join the
paced live queue on a miss. They accept --cache-only for the narrower case where
a miss must return as JSON without probing Chrome or sending a request.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import random
import re
import secrets
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlparse

CDP_URL = "http://localhost:9222"
CDP_HOST, CDP_PORT = "localhost", 9222

# Two kinds of state, deliberately in two places:
# - MACHINE-GLOBAL (guards the one Ancestry account + the one browser, across
#   every clone/session): the queue lock, pacing timestamp, tabs, agent cursors.
#   Lives in ~/.gen-cockpit; GEN_COCKPIT_DIR overrides (tests only, gated).
# - PROJECT-DURABLE (the acquisition store): the latest validated structured
#   snapshot for each logical page or query. Normal revisits are free; --fresh
#   atomically replaces that snapshot. Lives IN the repo tree but gitignored
#   (Ancestry ToS: index-derived data stays out of the public repo). Backed up
#   with the project. GEN_ANCESTRY_CACHE_DIR overrides (tests only, gated).
ROOT = Path(__file__).resolve().parents[1]
# Relocating the machine-global state or the acquisition store via environment
# variables is TEST-ONLY and requires the explicit unsafe flag: without it a
# stray env var could split the account flock into per-process locks and defeat
# the global queue (adversarial-review finding, 2026-07-09).
UNSAFE_TEST = os.environ.get("GEN_ANCESTRY_UNSAFE_TEST") == "1"


def _test_override(name: str) -> str | None:
    value = os.environ.get(name)
    if value and UNSAFE_TEST:
        return value
    return None


STATE_DIR = Path(_test_override("GEN_COCKPIT_DIR") or str(Path.home() / ".gen-cockpit")) / "ancestry"
CACHE_DIR = Path(_test_override("GEN_ANCESTRY_CACHE_DIR") or str(ROOT / "research" / "cache" / "ancestry"))
LOCK_PATH = STATE_DIR / "queue.lock"
LAST_PATH = STATE_DIR / "last_request"
AGENTS_DIR = STATE_DIR / "agents"       # per-agent cursor + history, one file each
SESSIONS_DIR = STATE_DIR / "sessions"   # per-agent live/cache hit accounting
TABS_PATH = STATE_DIR / "tabs.json"     # hashed agent id -> CDP targetId
# Minimum seconds between REAL Ancestry hits, across all agents (human pace).
# Configuration may make pacing slower, never faster than the safety floor.
MIN_INTERVAL_FLOOR = 5.0
MIN_INTERVAL = max(MIN_INTERVAL_FLOOR, float(os.environ.get("GEN_ANCESTRY_MIN_INTERVAL", "5.0")))
JITTER_MAX = max(0.0, float(os.environ.get("GEN_ANCESTRY_JITTER", "2.5")))

CACHE_SCHEMA = "gen.ancestry.cache"
CACHE_VERSION = 3
AGENT_STATE_SCHEMA = "gen.ancestry.agent-state"
TABS_STATE_SCHEMA = "gen.ancestry.tabs-state"
SESSION_STATE_SCHEMA = "gen.ancestry.session-state"
AGENT_STATE_VERSION = 2
TABS_STATE_VERSION = 1
REQUEST_STATE_VERSION = 1
SESSION_VERSION = 1
REQUEST_STATE_SCHEMA = "gen.ancestry.request-state"
RECORD_DELETE_CONFIRMATION = "DELETE-DURABLE-ANCESTRY-RECORDS"
SESSION_RESET_CONFIRMATION = "RESET-ANCESTRY-SESSION"
AGENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
CACHE_KINDS = ("collection", "record", "search")
SEARCH_TEXT_FILTERS = ("birth", "place", "spouse", "birthplace")
CENSUS_COLLECTION_YEARS = {
    "8054": 1850,
    "7667": 1860,
    "7163": 1870,
    "6742": 1880,
    "7602": 1900,
    "7884": 1910,
    "6061": 1920,
    "6224": 1930,
    "2442": 1940,
    "62308": 1950,
}


class CockpitError(Exception):
    """Expected, user-actionable failure that must be returned as JSON."""

    def __init__(self, error: str, **details):
        super().__init__(error)
        self.error = error
        self.details = details


def emit(obj: dict) -> None:
    print(json.dumps(obj, separators=(",", ":")))


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


def ensure_state() -> None:
    ensure_private_dir(STATE_DIR)
    ensure_private_dir(AGENTS_DIR)
    ensure_private_dir(SESSIONS_DIR)
    ensure_private_dir(CACHE_DIR)


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Replace one private file atomically, never exposing a partial write."""
    ensure_private_dir(path.parent)
    tmp = path.parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(6)}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
        path.chmod(0o600)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        tmp.unlink(missing_ok=True)


def atomic_write_json(path: Path, obj) -> None:
    atomic_write_bytes(path, json.dumps(obj, separators=(",", ":")).encode())


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CockpitError("invalid JSON state", path=str(path), detail=str(exc)) from exc


def agent_id(raw: str | None) -> str:
    value = raw or "default"
    if not AGENT_RE.fullmatch(value):
        raise CockpitError(
            "invalid agent id; use 1-64 letters, digits, dots, underscores, or hyphens and start with a letter or digit",
            agent=value,
        )
    return value


def agent_disk_key(agent: str) -> str:
    """Keep user-provided ids out of filenames and persistent map keys."""
    agent_id(agent)
    return hashlib.sha256(agent.encode()).hexdigest()[:32]


def cache_key(kind: str, parts: dict) -> str:
    raw = kind + "|" + "|".join(f"{k}={parts[k]}" for k in sorted(parts))
    return kind + "-" + hashlib.sha1(raw.encode()).hexdigest()[:16]


def cache_location(key: str, meta: dict) -> dict:
    """Reconstruct and validate the logical location named by cache metadata."""
    kind = meta.get("kind")
    collection = meta.get("collection")
    if kind not in CACHE_KINDS or not isinstance(collection, str) or not collection.isdigit():
        raise CockpitError("malformed ancestry cache metadata", key=key)
    if kind == "record":
        record_id = meta.get("id")
        if not isinstance(record_id, str) or not record_id.isdigit():
            raise CockpitError("malformed ancestry record cache metadata", key=key)
        loc = {"type": "record", "collection": collection, "id": record_id}
    elif kind == "search":
        name = meta.get("name")
        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            raise CockpitError("malformed ancestry search cache metadata", key=key)
        loc = {
            "type": "search",
            "collection": collection,
            "name": name,
            **{field: meta.get(field) for field in SEARCH_TEXT_FILTERS},
            "exact_name": meta.get("exact_name"),
        }
        validate_search_location(loc, context="cache metadata")
    else:
        loc = {"type": "collection", "collection": collection}
    if location_key(loc) != key:
        raise CockpitError("ancestry cache key does not match its metadata", key=key)
    return loc


def validate_cache_envelope(key: str, obj: object) -> tuple[dict, dict]:
    """Validate schema, key, metadata, and payload as one indivisible contract."""
    if not isinstance(obj, dict) or obj.get("schema") != CACHE_SCHEMA or obj.get("version") != CACHE_VERSION:
        raise CockpitError(
            "unsupported ancestry cache format; run `gen ancestry cache migrate` before continuing",
            key=key,
            found_version=obj.get("version") if isinstance(obj, dict) else None,
            expected_version=CACHE_VERSION,
        )
    meta = obj.get("meta")
    data = obj.get("data")
    if not isinstance(meta, dict) or not isinstance(data, dict):
        raise CockpitError("malformed ancestry cache envelope", key=key)
    fetched_at = meta.get("fetched_at")
    if not isinstance(fetched_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fetched_at):
        raise CockpitError("malformed ancestry cache timestamp", key=key)
    data_sha256 = meta.get("data_sha256")
    expected_sha256 = hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if not isinstance(data_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", data_sha256):
        raise CockpitError("malformed ancestry cache payload digest", key=key)
    if data_sha256 != expected_sha256:
        raise CockpitError("ancestry cache payload digest mismatch", key=key)
    loc = cache_location(key, meta)
    validate_location_data(loc, data)
    return meta, data


def cache_read_envelope(key: str) -> tuple[dict, dict] | None:
    """Return validated acquisition metadata and data, or None.

    This is the public read boundary for consumers that need citation and cache
    provenance as well as parsed data. Callers never need to open cache JSON.
    """
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    obj = read_json(path)
    return validate_cache_envelope(key, obj)


def cache_read_location(loc: dict) -> tuple[dict, dict] | None:
    """Read one validated cache envelope by its canonical logical location."""
    key = location_key(loc)
    envelope = cache_read_envelope(key)
    if envelope is not None:
        _meta, data = envelope
        validate_location_data(loc, data)
    return envelope


def cache_read(key: str) -> dict | None:
    """Return a current-version cached payload, or None."""
    envelope = cache_read_envelope(key)
    return envelope[1] if envelope is not None else None


def cache_write(key: str, obj: dict, meta: dict | None = None) -> None:
    ensure_state()
    envelope = {
        "schema": CACHE_SCHEMA,
        "version": CACHE_VERSION,
        "meta": {
            **(meta or {}),
            "fetched_at": utc_timestamp(),
            "data_sha256": hashlib.sha256(
                json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        },
        "data": obj,
    }
    validate_cache_envelope(key, envelope)
    atomic_write_json(CACHE_DIR / f"{key}.json", envelope)


def cache_entries():
    """Yield (key, meta_or_None, bytes) for every cache entry."""
    if not CACHE_DIR.exists():
        return
    for path in sorted(CACHE_DIR.glob("*.json")):
        obj = read_json(path)
        meta, _data = validate_cache_envelope(path.stem, obj)
        yield path.stem, meta, path.stat().st_size


def cache_inventory() -> tuple[list[tuple[str, dict, int]], list[dict]]:
    """Inspect all top-level entries without letting one bad file hide the rest."""
    valid: list[tuple[str, dict, int]] = []
    invalid: list[dict] = []
    if not CACHE_DIR.exists():
        return valid, invalid
    for path in sorted(CACHE_DIR.glob("*.json")):
        try:
            size = path.stat().st_size
            obj = read_json(path)
            meta, _data = validate_cache_envelope(path.stem, obj)
        except CockpitError as exc:
            invalid.append({"key": path.stem, "error": exc.error, **exc.details})
        except OSError as exc:
            invalid.append({"key": path.stem, "error": f"unreadable cache entry: {exc}"})
        else:
            valid.append((path.stem, meta, size))
    return valid, invalid


def legacy_primary_name(row: dict) -> str:
    cells = row.get("cells")
    if not isinstance(cells, list) or not all(isinstance(cell, str) for cell in cells):
        raise CockpitError("legacy Ancestry search row has malformed cells")
    candidates = [cell.strip() for cell in cells if cell.strip() and cell.strip() != "View Record"]
    if not candidates:
        raise CockpitError("legacy Ancestry search row has no recoverable subject name")
    return candidates[0]


def migrate_v2_envelope(key: str, obj: object) -> tuple[str, dict, str]:
    """Losslessly reshape one explicit v2 acquisition into the v3 contract."""
    if (
        not isinstance(obj, dict)
        or obj.get("schema") != CACHE_SCHEMA
        or obj.get("version") != 2
        or not isinstance(obj.get("meta"), dict)
        or not isinstance(obj.get("data"), dict)
    ):
        raise CockpitError("entry is not a migratable ancestry cache v2 envelope", key=key)
    old_meta = obj["meta"]
    old_data = obj["data"]
    kind = old_meta.get("kind")
    collection = old_meta.get("collection")
    fetched_at = old_meta.get("fetched_at")
    if kind not in CACHE_KINDS or not isinstance(collection, str) or not collection.isdigit():
        raise CockpitError("legacy ancestry cache metadata is malformed", key=key)
    if not isinstance(fetched_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fetched_at):
        raise CockpitError("legacy ancestry cache timestamp is malformed", key=key)

    data = dict(old_data)
    if kind == "search":
        name = old_meta.get("name")
        birth = old_meta.get("birth")
        if not isinstance(name, str) or not name.strip() or not isinstance(birth, str):
            raise CockpitError("legacy ancestry search metadata is malformed", key=key)
        old_key = cache_key("search", {"collection": collection, "name": name, "birth": birth})
        if old_key != key:
            raise CockpitError("legacy ancestry search key does not match its metadata", key=key)
        loc = search_location(collection, name, birth=birth)
        legacy_rows = data.get("results")
        if not isinstance(legacy_rows, list):
            raise CockpitError("legacy ancestry search results are malformed", key=key)
        rows = []
        for legacy_row in legacy_rows:
            if not isinstance(legacy_row, dict):
                raise CockpitError("legacy ancestry search row is malformed", key=key)
            rows.append({**legacy_row, "primary_name": legacy_primary_name(legacy_row)})
        validate_search_rows(rows, collection)
        if rows:
            outcome = validate_search_outcome(loc, None, rows)
        elif data.get("outcome") == "no-results":
            outcome = "no-results"
        else:
            raise CockpitError("legacy empty ancestry search lacks a validated no-results outcome", key=key)
        data = {
            **data,
            **search_filters(loc),
            "count": len(rows),
            "outcome": outcome,
            "result_set": search_result_set_metadata(outcome),
            "results": rows,
        }
        new_key = location_key(loc)
        canonical_meta = {"kind": "search", "collection": collection, **search_filters(loc), "outcome": outcome}
    elif kind == "record":
        record_id = old_meta.get("id")
        if not isinstance(record_id, str) or not record_id.isdigit():
            raise CockpitError("legacy ancestry record metadata is malformed", key=key)
        loc = {"type": "record", "collection": collection, "id": record_id}
        if location_key(loc) != key:
            raise CockpitError("legacy ancestry record key does not match its metadata", key=key)
        household = data.get("household")
        data = {
            **data,
            "household_extraction": {
                "present": bool(household),
                "complete": False,
                "dwelling_complete": None,
                "method": "inner_text" if household else "none",
                "columns": ["name", "age", "relation"] if household else [],
                "warnings": ["legacy extraction untrusted; refresh required"],
            },
            "citation_metadata": {
                "complete": False,
                "fields": {},
                "warnings": ["legacy cache did not retain citation text; refresh required"],
            },
        }
        new_key = key
        canonical_meta = {"kind": "record", "collection": collection, "id": record_id}
    else:
        loc = {"type": "collection", "collection": collection}
        if location_key(loc) != key:
            raise CockpitError("legacy ancestry collection key does not match its metadata", key=key)
        new_key = key
        canonical_meta = {"kind": "collection", "collection": collection}

    new_meta = {
        **old_meta,
        **canonical_meta,
        "fetched_at": fetched_at,
        "migrated_from_version": 2,
        "migrated_at": utc_timestamp(),
        "data_sha256": hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    envelope = {"schema": CACHE_SCHEMA, "version": CACHE_VERSION, "meta": new_meta, "data": data}
    validate_cache_envelope(new_key, envelope)
    return new_key, envelope, kind


def migrate_cache_locked(kind_filter: str | None) -> dict:
    migrated = already_current = superseded = 0
    failures: list[dict] = []
    if not CACHE_DIR.exists():
        return {"migrated": 0, "already_current": 0, "superseded": 0, "failed": 0, "failures": []}
    for path in sorted(CACHE_DIR.glob("*.json")):
        try:
            obj = read_json(path)
            if isinstance(obj, dict) and obj.get("schema") == CACHE_SCHEMA and obj.get("version") == CACHE_VERSION:
                meta, _data = validate_cache_envelope(path.stem, obj)
                if kind_filter is None or meta["kind"] == kind_filter:
                    already_current += 1
                continue
            legacy_kind = obj.get("meta", {}).get("kind") if isinstance(obj, dict) else None
            if kind_filter is not None and legacy_kind != kind_filter:
                continue
            new_key, envelope, _kind = migrate_v2_envelope(path.stem, obj)
            target = CACHE_DIR / f"{new_key}.json"
            if target != path and target.exists():
                current = read_json(target)
                validate_cache_envelope(new_key, current)
                path.unlink()
                superseded += 1
                continue
            atomic_write_json(target, envelope)
            if target != path:
                path.unlink()
            migrated += 1
        except (CockpitError, OSError) as exc:
            failures.append({
                "key": path.stem,
                "error": exc.error if isinstance(exc, CockpitError) else str(exc),
            })
    return {
        "migrated": migrated,
        "already_current": already_current,
        "superseded": superseded,
        "failed": len(failures),
        "failures": failures,
    }


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_session_state() -> dict:
    return {
        "schema": SESSION_STATE_SCHEMA,
        "version": SESSION_VERSION,
        "session_id": secrets.token_hex(8),
        "started_at": utc_timestamp(),
        "live_hits": 0,
        "cache_hits": 0,
        "by_kind": {kind: {"live": 0, "cached": 0} for kind in CACHE_KINDS},
    }


def validate_session_state(state: object) -> dict:
    if (
        not isinstance(state, dict)
        or state.get("schema") != SESSION_STATE_SCHEMA
        or state.get("version") != SESSION_VERSION
    ):
        raise CockpitError("unsupported ancestry session accounting state; reset the agent session")
    if not isinstance(state.get("started_at"), str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", state["started_at"]
    ):
        raise CockpitError("malformed ancestry session accounting state")
    if not isinstance(state.get("session_id"), str) or not re.fullmatch(r"[0-9a-f]{16}", state["session_id"]):
        raise CockpitError("malformed ancestry session accounting state")
    if not isinstance(state.get("live_hits"), int) or state["live_hits"] < 0:
        raise CockpitError("malformed ancestry session accounting state")
    if not isinstance(state.get("cache_hits"), int) or state["cache_hits"] < 0:
        raise CockpitError("malformed ancestry session accounting state")
    by_kind = state.get("by_kind")
    if not isinstance(by_kind, dict) or set(by_kind) != set(CACHE_KINDS):
        raise CockpitError("malformed ancestry session accounting state")
    for counts in by_kind.values():
        if (
            not isinstance(counts, dict)
            or set(counts) != {"live", "cached"}
            or not all(isinstance(value, int) and value >= 0 for value in counts.values())
        ):
            raise CockpitError("malformed ancestry session accounting state")
    return state


def session_path(agent: str) -> Path:
    return SESSIONS_DIR / f"{agent_disk_key(agent)}.json"


def load_session(agent: str) -> dict:
    path = session_path(agent)
    if path.exists():
        return validate_session_state(read_json(path))
    state = new_session_state()
    save_session(agent, state)
    return state


def save_session(agent: str, state: dict) -> None:
    save_json(session_path(agent), validate_session_state(state))


def record_session_access(agent: str, kind: str, *, cached: bool) -> dict:
    """Record one acquisition-store read or one real Ancestry request.

    The caller holds cache_lock, which also serializes these per-agent counters.
    A live hit is charged immediately before browser I/O because failed HTTP or
    parsing attempts still consume the paid-account request budget.
    """
    agent = agent_id(agent)
    if kind not in CACHE_KINDS:
        raise CockpitError("cannot account for unknown Ancestry request kind", kind=kind)
    state = load_session(agent)
    counter = "cache_hits" if cached else "live_hits"
    state[counter] += 1
    state["by_kind"][kind]["cached" if cached else "live"] += 1
    save_session(agent, state)
    return state


def public_session_state(state: dict) -> dict:
    validated = validate_session_state(state)
    return {
        "session_id": validated["session_id"],
        "started_at": validated["started_at"],
        "live_hits": validated["live_hits"],
        "cache_hits": validated["cache_hits"],
        "by_kind": validated["by_kind"],
    }


def session_summary(agent: str) -> dict:
    return public_session_state(load_session(agent_id(agent)))


def throttle() -> None:
    """Human-pace real hits: wait out MIN_INTERVAL since the last global request."""
    if LAST_PATH.exists():
        state = read_json(LAST_PATH)
        if (
            not isinstance(state, dict)
            or state.get("schema") != REQUEST_STATE_SCHEMA
            or state.get("version") != REQUEST_STATE_VERSION
        ):
            raise CockpitError("unsupported request pacing state; reset the private ancestry cockpit state")
        last = float(state.get("last_request_epoch", 0))
        wait = MIN_INTERVAL - (time.time() - last)
        if wait > 0:
            time.sleep(wait + random.uniform(0, JITTER_MAX))
    atomic_write_json(
        LAST_PATH,
        {"schema": REQUEST_STATE_SCHEMA, "version": REQUEST_STATE_VERSION, "last_request_epoch": time.time()},
    )


@contextmanager
def cache_lock():
    """Serialize durable-store reads, writes, and administration without pacing."""
    ensure_state()
    fd = os.open(LOCK_PATH, os.O_RDWR | os.O_CREAT, 0o600)
    os.chmod(LOCK_PATH, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def cached_or_fetch(
    key: str,
    *,
    agent: str,
    fresh: bool,
    cache_only: bool,
    fetch,
    meta: dict,
    validate,
) -> tuple[dict, bool]:
    """Read once, then recheck/fetch/write while holding the global lock.

    The second read prevents two agents that observed the same miss from both
    hitting Ancestry. A successful acquisition is durable before the lock is
    released, so the next waiter always sees it.
    """
    agent = agent_id(agent)
    kind = meta.get("kind")
    if kind not in CACHE_KINDS:
        raise CockpitError("cannot acquire unknown Ancestry location kind", kind=kind)
    if not fresh:
        with cache_lock():
            hit = cache_read(key)
            if hit is not None:
                validate(hit)
                record_session_access(agent, kind, cached=True)
                return hit, True
    if cache_only:
        raise CockpitError("cache miss in --cache-only mode; no live request was made", key=key)

    with cache_lock():
        if not fresh:
            hit = cache_read(key)
            if hit is not None:
                validate(hit)
                record_session_access(agent, kind, cached=True)
                return hit, True
        if not cdp_up():
            raise CockpitError("cdp browser not reachable on :9222")
        throttle()
        record_session_access(agent, kind, cached=False)
        data, fetched_meta = fetch()
        validate(data)
        cache_write(key, data, {**meta, **fetched_meta})
        return data, False


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


def parse_citation_metadata(text: str) -> dict:
    """Capture literal citation/source prose exposed by the record detail page."""
    lines = [line.strip() for line in text.splitlines()]
    headings = {
        "Source Citation": "source_citation",
        "Source Information": "source_information",
    }
    fields: dict[str, str] = {}
    stop_lines = {
        "Original data:",
        "Description",
        "Learn more about this database",
        "Browse Individual Records",
        "Suggested records",
        "Save this record?",
    }
    for heading, key in headings.items():
        try:
            start = lines.index(heading) + 1
        except ValueError:
            continue
        values: list[str] = []
        for line in lines[start:]:
            if line in headings or line in stop_lines:
                break
            if line and line != "Source":
                values.append(line)
        if values:
            fields[key] = " ".join(values)

    warnings = []
    if "source_citation" not in fields:
        warnings.append("Source Citation text was not available in the parsed record page")
    if "source_information" not in fields:
        warnings.append("Source Information text was not available in the parsed record page")
    return {"complete": not warnings, "fields": fields, "warnings": warnings}


def census_expects_relationship(collection: str) -> bool | None:
    year = CENSUS_COLLECTION_YEARS.get(str(collection))
    return None if year is None else year >= 1880


def household_column_indexes(headers: list[str], collection: str) -> tuple[dict[str, int | None], list[str]]:
    normalized = [" ".join(normalized_words(header)) for header in headers]

    def first_index(predicate) -> int | None:
        return next((index for index, header in enumerate(normalized) if predicate(header)), None)

    name_index = first_index(lambda value: "household member" in value or value == "name" or value.endswith(" name"))
    age_index = first_index(lambda value: value == "age" or value.startswith("age ") or value.endswith(" age"))
    relation_index = first_index(lambda value: "relationship" in value or "relation" in value)
    warnings: list[str] = []
    if name_index is None:
        name_index = 0
        warnings.append("household name column was inferred from position")
    if age_index is None:
        age_index = 1
        warnings.append("household age column was inferred from position")

    expects_relation = census_expects_relationship(collection)
    if relation_index is None and expects_relation is True:
        relation_index = 2
        warnings.append("household relationship column was inferred from census year and position")
    elif relation_index is None and expects_relation is None and len(headers) >= 3:
        relation_index = 2
        warnings.append("household relationship column was inferred from position")
    return {"name": name_index, "age": age_index, "relation": relation_index}, warnings


def normalize_household_rows(
    headers: list[str],
    rows: list[list[str]],
    collection: str,
    *,
    method: str,
    extra_warnings: list[str] | None = None,
) -> tuple[list[dict[str, str | None]], dict]:
    indexes, parser_warnings = household_column_indexes(headers, collection)
    parser_warnings.extend(extra_warnings or [])
    members: list[dict[str, str | None]] = []
    required_index = max(index for index in (indexes["name"], indexes["age"]) if index is not None)
    relation_index = indexes["relation"]

    for row_number, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, list) or not all(isinstance(cell, str) for cell in raw_row):
            parser_warnings.append(f"household row {row_number} had a malformed cell shape and was skipped")
            continue
        cells = [" ".join(cell.split()) for cell in raw_row]
        if len(cells) <= required_index:
            parser_warnings.append(f"household row {row_number} had fewer cells than the detected columns and was skipped")
            continue
        name = cells[indexes["name"]].strip()  # type: ignore[index]
        if not name:
            parser_warnings.append(f"household row {row_number} had no name and was skipped")
            continue
        if relation_index is not None and relation_index >= len(cells):
            parser_warnings.append(f"household row {row_number} had no relationship cell")
            relation = ""
        else:
            relation = cells[relation_index].strip() if relation_index is not None else None
        members.append({
            "name": name,
            "age": cells[indexes["age"]].strip(),  # type: ignore[index]
            "relation": relation,
        })

    parser_warnings = list(dict.fromkeys(parser_warnings))
    warning_list = list(parser_warnings)
    if census_expects_relationship(collection) is False:
        warning_list.append(
            "pre-1880 record-associated rows are not proof of a complete census dwelling; "
            "compare dwelling and family numbers across records"
        )
    columns = ["name", "age"] + (["relation"] if indexes["relation"] is not None else [])
    extraction = {
        "present": True,
        "complete": not parser_warnings,
        "dwelling_complete": None,
        "method": method,
        "columns": columns,
        "warnings": warning_list,
    }
    return members, extraction


def parse_household_table(table: object, collection: str) -> tuple[list[dict[str, str | None]], dict] | None:
    """Normalize a semantic household table extracted directly from the DOM."""
    if table is None:
        return None
    if not isinstance(table, dict) or not isinstance(table.get("headers"), list) or not isinstance(table.get("rows"), list):
        raise CockpitError("Ancestry household table parser returned a malformed shape; page was not cached")
    headers = table["headers"]
    rows = table["rows"]
    if not all(isinstance(header, str) for header in headers):
        raise CockpitError("Ancestry household table parser returned malformed headers; page was not cached")
    warnings = [] if rows else ["household table contained no member rows"]
    return normalize_household_rows(headers, rows, collection, method="table", extra_warnings=warnings)


def parse_household(text: str, collection: str) -> tuple[list[dict[str, str | None]], dict]:
    """Parse the flattened-text fallback without shifting census columns.

    Household tables are normally read semantically from the DOM. This fallback
    preserves the table's detected column count, so 1850-1870 two-column rows
    cannot be mistaken for later name/age/relationship triples.
    """
    header_start = text.find("Household Members")
    if header_start < 0:
        expected = str(collection) in CENSUS_COLLECTION_YEARS
        warnings = ["expected census household section was not found"] if expected else []
        return [], {
            "present": False,
            "complete": not expected,
            "dwelling_complete": None,
            "method": "none",
            "columns": [],
            "warnings": warnings,
        }

    section = text[header_start:]
    for marker in ("\nSource\n", "Save this record", "Listen and explore", "Suggested records"):
        cut = section.find(marker)
        if cut > 0:
            section = section[:cut]
    header_line, separator, body = section.partition("\n")
    if not separator:
        return [], {
            "present": True,
            "complete": False,
            "dwelling_complete": None,
            "method": "inner_text",
            "columns": [],
            "warnings": ["household section had no member rows"],
        }

    headers = [part.strip() for part in header_line.split("\t") if part.strip()]
    if len(headers) < 2:
        expects_relation = census_expects_relationship(collection)
        headers = ["Household Members (Name)", "Age"]
        if expects_relation is not False:
            headers.append("Relationship")
    column_count = len(headers)
    rows: list[list[str]] = []
    scalar_cells: list[str] = []
    fallback_warnings = ["semantic household table unavailable; parsed flattened text"]

    def flush_scalars() -> None:
        complete_count = len(scalar_cells) // column_count
        for offset in range(0, complete_count * column_count, column_count):
            rows.append(scalar_cells[offset:offset + column_count])
        leftovers = len(scalar_cells) % column_count
        if leftovers:
            fallback_warnings.append(f"{leftovers} trailing household cell(s) could not be assigned to a row")
        scalar_cells.clear()

    for line in body.splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            cells = [cell.strip() for cell in line.split("\t")]
            if sum(bool(cell) for cell in cells) >= 2:
                flush_scalars()
                if len(cells) < column_count:
                    cells.extend([""] * (column_count - len(cells)))
                rows.append(cells)
                continue
        scalar_cells.append(line.strip())
    flush_scalars()
    return normalize_household_rows(
        headers,
        rows,
        collection,
        method="inner_text",
        extra_warnings=fallback_warnings,
    )


def _ancestry_url(url: str) -> tuple[str, str]:
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise CockpitError("Ancestry returned an invalid final URL") from exc
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "ancestry.com" or host.endswith(".ancestry.com")):
        raise CockpitError("Ancestry navigation left the ancestry.com HTTPS origin", final_url=url)
    return host, parsed.path.rstrip("/")


def validate_page(loc: dict, final_url: str, title: str, body: str) -> None:
    """Reject redirects, login walls, challenges, and empty/skeleton pages."""
    _host, path = _ancestry_url(final_url)
    path_lower = path.lower()
    title_lower = (title or "").strip().lower()
    body_lower = (body or "")[:12000].lower()
    login_paths = ("/account/signin", "/account/login", "/secure/login", "/auth/")
    challenge_phrases = (
        "verify you are human",
        "unusual activity",
        "complete the security check",
        "access denied",
        "captcha",
        "sign in to ancestry",
    )
    if any(marker in path_lower for marker in login_paths):
        raise CockpitError("Ancestry redirected to login; page was not cached", final_url=final_url)
    if "sign in" in title_lower or "login" in title_lower:
        raise CockpitError("Ancestry returned a login page; page was not cached", final_url=final_url)
    if any(marker in title_lower or marker in body_lower for marker in challenge_phrases):
        raise CockpitError("Ancestry returned a login or challenge page; page was not cached", final_url=final_url)
    if not isinstance(body, str) or len(body.strip()) < 20:
        raise CockpitError("Ancestry returned an empty or incomplete page; page was not cached", final_url=final_url)

    collection = re.escape(str(loc["collection"]))
    collection_path = re.fullmatch(rf"/search/collections/{collection}", path, re.IGNORECASE)
    if loc["type"] in {"search", "collection"} and not collection_path:
        raise CockpitError("Ancestry returned the wrong collection page; page was not cached", final_url=final_url)
    if loc["type"] == "record":
        record = re.escape(str(loc["id"]))
        classic = re.fullmatch(rf"/search/collections/{collection}/records/{record}", path, re.IGNORECASE)
        discovery = re.fullmatch(rf"/discoveryui-content/view/{record}:{collection}", path, re.IGNORECASE)
        if not (classic or discovery):
            raise CockpitError("Ancestry returned the wrong record page; page was not cached", final_url=final_url)


def ancestry_search_params(loc: dict) -> dict[str, str]:
    validate_search_location(loc)
    params = {"name": loc["name"]}
    birth_parts = [value for value in (loc["birth"], loc["birthplace"]) if value]
    if birth_parts:
        params["birth"] = "_".join(birth_parts)
    if loc["place"]:
        params["residence"] = loc["place"]
    if loc["spouse"]:
        params["spouse"] = loc["spouse"]
    if loc["exact_name"]:
        params["name_x"] = "1_1"
    return params


def validate_final_search_query(loc: dict, final_url: str) -> None:
    """Prove Ancestry retained every requested filter before caching results."""
    try:
        pairs = parse_qsl(urlparse(final_url).query, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise CockpitError("Ancestry returned a malformed final search query; page was not cached") from exc
    if len({key for key, _value in pairs}) != len(pairs):
        raise CockpitError("Ancestry returned duplicate final search filters; page was not cached")
    actual = dict(pairs)
    dropped = {
        key: {"requested": value, "returned": actual.get(key)}
        for key, value in ancestry_search_params(loc).items()
        if actual.get(key) != value
    }
    if dropped:
        raise CockpitError(
            "Ancestry dropped or changed requested search filters; page was not cached",
            filters=dropped,
            final_url=final_url,
        )


def validate_response(response) -> None:
    status = getattr(response, "status", None)
    if not isinstance(status, int):
        raise CockpitError("Ancestry navigation returned no HTTP response; page was not cached")
    if status < 200 or status >= 400:
        raise CockpitError("Ancestry returned an unsuccessful HTTP response; page was not cached", status=status)


def validate_search_rows(rows, collection: str) -> list[dict]:
    if not isinstance(rows, list):
        raise CockpitError("Ancestry search parser returned a malformed result set; page was not cached")
    for row in rows:
        if not isinstance(row, dict):
            raise CockpitError("Ancestry search parser returned a malformed result; page was not cached")
        record_id = row.get("record_id")
        cells = row.get("cells")
        primary_name = row.get("primary_name")
        text = row.get("text")
        url = row.get("url")
        if not isinstance(record_id, str) or not record_id.isdigit():
            raise CockpitError("Ancestry search result has an invalid record id; page was not cached")
        if (
            not isinstance(cells, list)
            or not all(isinstance(cell, str) for cell in cells)
            or not isinstance(primary_name, str)
            or not primary_name.strip()
            or not isinstance(text, str)
        ):
            raise CockpitError("Ancestry search result has an invalid parsed shape; page was not cached")
        if not isinstance(url, str):
            raise CockpitError("Ancestry search result has no record URL; page was not cached")
        _host, path = _ancestry_url(url)
        expected = rf"/search/collections/{re.escape(str(collection))}/records/{re.escape(record_id)}"
        if not re.fullmatch(expected, path, re.IGNORECASE):
            raise CockpitError("Ancestry search result belongs to another collection; page was not cached")
    return rows


def normalized_words(value: str) -> list[str]:
    """Case-fold text into Unicode-aware alphanumeric words."""
    folded = value.casefold()
    return [word for word in re.split(r"[^\w]+", folded, flags=re.UNICODE) if word]


def edit_distance_within(left: str, right: str, limit: int) -> bool:
    """Return whether two short words are within a bounded edit distance."""
    if abs(len(left) - len(right)) > limit:
        return False
    previous = list(range(len(right) + 1))
    for row_index, left_char in enumerate(left, start=1):
        current = [row_index]
        for column_index, right_char in enumerate(right, start=1):
            current.append(min(
                current[-1] + 1,
                previous[column_index] + 1,
                previous[column_index - 1] + (left_char != right_char),
            ))
        if min(current) > limit:
            return False
        previous = current
    return previous[-1] <= limit


def name_word_matches(expected: str, actual: str) -> bool:
    """Allow the small spelling variants Ancestry commonly returns."""
    if expected == actual:
        return True
    if len(expected) < 4 or not actual or expected[0] != actual[0]:
        return False
    limit = min(2, max(1, len(expected) // 5))
    return edit_distance_within(expected, actual, limit)


def validate_search_location(loc: object, *, context: str = "search") -> dict:
    if not isinstance(loc, dict) or loc.get("type") != "search":
        raise CockpitError(f"malformed Ancestry {context}")
    collection = loc.get("collection")
    name = loc.get("name")
    if not isinstance(collection, str) or not collection.isdigit() or not isinstance(name, str) or not name.strip():
        raise CockpitError(f"malformed Ancestry {context}")
    for field in SEARCH_TEXT_FILTERS:
        value = loc.get(field)
        if not isinstance(value, str) or (value and not value.strip()):
            raise CockpitError(f"malformed Ancestry {context} filter", filter=field)
    if loc["birth"] and not re.fullmatch(r"\d{3,4}", loc["birth"]):
        raise CockpitError("birth must be a 3- or 4-digit year")
    if not isinstance(loc.get("exact_name"), bool):
        raise CockpitError(f"malformed Ancestry {context} exact-name filter")
    return loc


def search_location(
    collection: str,
    name: str,
    *,
    birth: str = "",
    place: str = "",
    spouse: str = "",
    birthplace: str = "",
    exact_name: bool = False,
) -> dict:
    loc = {
        "type": "search",
        "collection": collection,
        "name": name,
        "birth": birth,
        "place": place,
        "spouse": spouse,
        "birthplace": birthplace,
        "exact_name": exact_name,
    }
    return validate_search_location(loc)


def search_filters(loc: dict) -> dict:
    validate_search_location(loc)
    return {
        "name": loc["name"],
        **{field: loc[field] for field in SEARCH_TEXT_FILTERS},
        "exact_name": loc["exact_name"],
    }


def validate_search_outcome(loc: dict, body: str | None, rows: list[dict]) -> str:
    """Prove that a search reached results for the requested name, or no results."""
    query_words = normalized_words(str(loc.get("name", "")).replace("_", " "))
    if not query_words:
        raise CockpitError("Ancestry search has no usable name to validate; page was not cached")

    if rows:
        exact = loc.get("exact_name") is True
        required = query_words if exact else ([query_words[0]] if len(query_words) == 1 else [query_words[0], query_words[-1]])
        for row in rows:
            row_words = normalized_words(row["primary_name"])
            matches = (
                (lambda wanted, found: wanted == found)
                if exact
                else name_word_matches
            )
            if all(any(matches(wanted, found) for found in row_words) for wanted in required):
                return "results"
        return "no-matching-results-on-page"

    if body is None:
        raise CockpitError("cached empty Ancestry search lacks a validated no-results outcome")
    body_text = " ".join(normalized_words(body))
    no_result_phrases = (
        "0 results",
        "no results",
        "no matching records",
        "there are no records",
        "we couldn t find",
        "we could not find",
        "we didn t find",
        "we did not find",
    )
    if any(phrase in body_text for phrase in no_result_phrases):
        return "no-results"
    raise CockpitError("Ancestry search did not reach a stable result state; page was not cached")


def search_result_set_metadata(outcome: str) -> dict:
    if outcome == "no-results":
        return {"complete": True, "pages_read": 1, "more_results_possible": False, "warnings": []}
    if outcome not in {"results", "no-matching-results-on-page"}:
        raise CockpitError("Ancestry search has an unknown outcome; page was not cached", outcome=outcome)
    return {
        "complete": False,
        "pages_read": 1,
        "more_results_possible": True,
        "warnings": ["only the first results page was read; more results may exist"],
    }


def validate_result_set_metadata(value: object, outcome: str) -> dict:
    expected = search_result_set_metadata(outcome)
    if value != expected:
        raise CockpitError("cached Ancestry search has invalid result-set completeness metadata")
    return expected


def validate_record_data(fields, household, household_extraction, citation_metadata) -> tuple[dict, list, dict, dict]:
    if not isinstance(fields, dict) or not fields:
        raise CockpitError("Ancestry record parser found no detail fields; page was not cached")
    if not all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip() for k, v in fields.items()):
        raise CockpitError("Ancestry record parser returned malformed detail fields; page was not cached")
    if not isinstance(household, list):
        raise CockpitError("Ancestry record parser returned a malformed household; page was not cached")
    for member in household:
        if (
            not isinstance(member, dict)
            or set(member) != {"name", "age", "relation"}
            or not isinstance(member["name"], str)
            or not member["name"].strip()
            or not isinstance(member["age"], str)
            or (member["relation"] is not None and not isinstance(member["relation"], str))
        ):
            raise CockpitError("Ancestry record parser returned a malformed household member; page was not cached")
    if (
        not isinstance(household_extraction, dict)
        or set(household_extraction) != {
            "present", "complete", "dwelling_complete", "method", "columns", "warnings"
        }
        or not isinstance(household_extraction["present"], bool)
        or not isinstance(household_extraction["complete"], bool)
        or household_extraction["dwelling_complete"] is not None
        or household_extraction["method"] not in {"table", "inner_text", "none"}
        or not isinstance(household_extraction["columns"], list)
        or not all(column in {"name", "age", "relation"} for column in household_extraction["columns"])
        or not isinstance(household_extraction["warnings"], list)
        or not all(isinstance(warning, str) and warning for warning in household_extraction["warnings"])
    ):
        raise CockpitError("Ancestry record parser returned malformed household extraction metadata; page was not cached")
    if household and not household_extraction["present"]:
        raise CockpitError("Ancestry household rows conflict with extraction metadata; page was not cached")
    if (
        not isinstance(citation_metadata, dict)
        or set(citation_metadata) != {"complete", "fields", "warnings"}
        or not isinstance(citation_metadata["complete"], bool)
        or not isinstance(citation_metadata["fields"], dict)
        or not all(
            key in {"source_citation", "source_information"}
            and isinstance(value, str)
            and value.strip()
            for key, value in citation_metadata["fields"].items()
        )
        or not isinstance(citation_metadata["warnings"], list)
        or not all(isinstance(warning, str) and warning for warning in citation_metadata["warnings"])
        or (citation_metadata["complete"] and citation_metadata["warnings"])
    ):
        raise CockpitError("Ancestry record parser returned malformed citation metadata; page was not cached")
    return fields, household, household_extraction, citation_metadata


def validate_location_data(loc: dict, data: object) -> dict:
    """Validate both newly parsed and durable cached structured data."""
    if not isinstance(data, dict) or data.get("ok") is not True or data.get("collection") != loc["collection"]:
        raise CockpitError("cached or parsed Ancestry data does not match the requested location")
    if loc["type"] == "search":
        validate_search_location(loc)
        if data.get("command") != "ancestry.search" or any(
            data.get(field) != value for field, value in search_filters(loc).items()
        ):
            raise CockpitError("cached Ancestry search does not match the requested query")
        rows = validate_search_rows(data.get("results"), loc["collection"])
        if data.get("count") != len(rows):
            raise CockpitError("cached Ancestry search has an invalid result count")
        expected_outcome = validate_search_outcome(loc, None, rows) if rows else "no-results"
        if data.get("outcome") != expected_outcome:
            raise CockpitError("cached Ancestry search lacks a validated outcome; refresh it")
        validate_result_set_metadata(data.get("result_set"), expected_outcome)
    elif loc["type"] == "record":
        if data.get("command") != "ancestry.record" or data.get("record_id") != loc["id"]:
            raise CockpitError("cached Ancestry record does not match the requested record")
        validate_record_data(
            data.get("fields"),
            data.get("household"),
            data.get("household_extraction"),
            data.get("citation_metadata"),
        )
    elif data.get("command") != "ancestry.collection":
        raise CockpitError("parsed Ancestry collection does not match the requested collection")
    return data


# ---- browser-driven commands ----

def load_json(path: Path, default):
    if path.exists():
        return read_json(path)
    return default


def save_json(path: Path, obj) -> None:
    ensure_state()
    atomic_write_json(path, obj)


def new_agent_state() -> dict:
    return {
        "schema": AGENT_STATE_SCHEMA,
        "version": AGENT_STATE_VERSION,
        "location": None,
        "results": [],
        "cursor": 0,
        "history": [],
        "last_search": None,
    }


def validate_agent_state(state: object) -> dict:
    if (
        not isinstance(state, dict)
        or state.get("schema") != AGENT_STATE_SCHEMA
        or state.get("version") != AGENT_STATE_VERSION
    ):
        raise CockpitError("unsupported agent state format; remove the stale agent state and start a new session")
    if not isinstance(state.get("results"), list) or not isinstance(state.get("history"), list):
        raise CockpitError("malformed agent state")
    if not isinstance(state.get("cursor"), int):
        raise CockpitError("malformed agent cursor")
    return state


def load_agent(agent: str) -> dict:
    key = agent_disk_key(agent)
    return validate_agent_state(load_json(AGENTS_DIR / f"{key}.json", new_agent_state()))


def save_agent(agent: str, state: dict) -> None:
    key = agent_disk_key(agent)
    save_json(AGENTS_DIR / f"{key}.json", validate_agent_state(state))


def new_tabs_state() -> dict:
    return {"schema": TABS_STATE_SCHEMA, "version": TABS_STATE_VERSION, "tabs": {}}


def load_tabs() -> dict:
    state = load_json(TABS_PATH, new_tabs_state())
    if (
        not isinstance(state, dict)
        or state.get("schema") != TABS_STATE_SCHEMA
        or state.get("version") != TABS_STATE_VERSION
    ):
        raise CockpitError("unsupported browser-tab state format; remove tabs.json and retry")
    if not isinstance(state.get("tabs"), dict):
        raise CockpitError("malformed browser-tab state")
    return state


def target_id(context, page) -> str:
    session = context.new_cdp_session(page)
    return session.send("Target.getTargetInfo")["targetInfo"]["targetId"]


def get_agent_page(context, agent: str):
    """The agent's own tab, matched by CDP targetId across CLI invocations."""
    tabs_state = load_tabs()
    tabs = tabs_state["tabs"]
    disk_key = agent_disk_key(agent)
    want = tabs.get(disk_key)
    if want:
        for page in context.pages:
            if target_id(context, page) == want:
                return page
    page = context.new_page()
    tabs[disk_key] = target_id(context, page)
    save_json(TABS_PATH, tabs_state)
    return page


def run_on_page(fn, agent="default"):
    """Every command drives its agent's OWN tab (stateless commands share the
    reserved "default" agent tab). The human's logged-in tab is never touched."""
    from playwright.sync_api import sync_playwright

    agent = agent_id(agent)
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
    const rawCells = [...tr.querySelectorAll('td')].map(td => td.innerText.replace(/\s+/g, ' ').trim());
    const cells = rawCells.filter(Boolean);
    const table = tr.closest('table');
    const headers = table ? [...table.querySelectorAll('thead th')].map(th => th.innerText.replace(/\s+/g, ' ').trim().toLowerCase()) : [];
    const nameIndex = headers.findIndex(header => header === 'name' || header.endsWith(' name'));
    const primaryName = nameIndex >= 0 ? rawCells[nameIndex] : (cells[0] === 'View Record' ? cells[1] : cells[0]);
    const m = a.href.match(/records\/(\d+)/);
    out.push({
      record_id: m ? m[1] : null,
      url: a.href.split('?')[0],
      primary_name: primaryName || '',
      cells,
      text: tr.innerText.replace(/\s+/g, ' ').trim().slice(0, 220),
    });
  });
  const seen = new Set();
  return out.filter(o => o.record_id && !seen.has(o.record_id) && seen.add(o.record_id));
}"""


HOUSEHOLD_JS = r"""() => {
  const clean = value => (value || '').replace(/\s+/g, ' ').trim();
  const tables = [...document.querySelectorAll('table')];
  const table = tables.find(candidate => /household members/i.test(clean(candidate.innerText).slice(0, 300)));
  if (!table) return null;
  let headers = [...table.querySelectorAll('thead th')].map(cell => clean(cell.innerText));
  let rowElements = [...table.querySelectorAll('tbody tr')];
  if (!headers.length) {
    const first = table.querySelector('tr');
    if (first) headers = [...first.querySelectorAll('th')].map(cell => clean(cell.innerText));
    rowElements = [...table.querySelectorAll('tr')].filter(row => row !== first);
  }
  const rows = rowElements
    .map(row => [...row.querySelectorAll('td')].map(cell => clean(cell.innerText)))
    .filter(cells => cells.some(Boolean));
  return {headers, rows};
}"""


def browser_fetch_location(agent: str, loc: dict) -> tuple[dict, dict]:
    """Fetch, validate, and parse one logical page. Caller owns the lock."""
    requested_url = url_for(loc)

    def go(page):
        response = page.goto(requested_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000 if loc["type"] == "record" else 3200)
        validate_response(response)
        body = page.evaluate("() => document.body.innerText")
        final_url = page.url
        title = page.title()
        validate_page(loc, final_url, title, body)
        if loc["type"] == "search":
            validate_final_search_query(loc, final_url)
            rows = validate_search_rows(page.evaluate(SEARCH_JS), loc["collection"])
            outcome = validate_search_outcome(loc, body, rows)
            data = {
                "command": "ancestry.search",
                "ok": True,
                "collection": loc["collection"],
                **search_filters(loc),
                "count": len(rows),
                "outcome": outcome,
                "result_set": search_result_set_metadata(outcome),
                "results": rows,
            }
        elif loc["type"] == "record":
            parsed_table = parse_household_table(page.evaluate(HOUSEHOLD_JS), loc["collection"])
            household, household_extraction = parsed_table or parse_household(body, loc["collection"])
            fields = parse_detail_fields(body)
            citation_metadata = parse_citation_metadata(body)
            validate_record_data(fields, household, household_extraction, citation_metadata)
            data = {
                "command": "ancestry.record",
                "ok": True,
                "collection": loc["collection"],
                "record_id": loc["id"],
                "household": household,
                "household_extraction": household_extraction,
                "fields": fields,
                "citation_metadata": citation_metadata,
            }
        else:
            data = {"command": "ancestry.collection", "ok": True, "collection": loc["collection"]}
        meta = {"requested_url": requested_url, "final_url": final_url}
        if loc["type"] == "search":
            meta["outcome"] = data["outcome"]
        return data, meta

    return run_on_page(go, agent=agent)


def cmd_search(args) -> int:
    # Cache key is limit-free and the FULL result set is cached; --limit only
    # trims the emitted view. Normal reads reuse one validated snapshot;
    # --fresh atomically replaces it.
    if args.limit < 0:
        raise CockpitError("limit must be zero or greater")
    agent = agent_id(args.agent)
    loc = search_location(
        args.collection,
        args.name,
        birth=args.birth or "",
        place=args.place or "",
        spouse=args.spouse or "",
        birthplace=args.birthplace or "",
        exact_name=args.exact_name,
    )
    key = location_key(loc)
    obj, cached = cached_or_fetch(
        key,
        agent=agent,
        fresh=args.fresh,
        cache_only=args.cache_only,
        fetch=lambda: browser_fetch_location(agent, loc),
        meta={"kind": "search", "collection": args.collection, **search_filters(loc)},
        validate=lambda data: validate_location_data(loc, data),
    )
    emit({
        **obj,
        "results": obj["results"][: args.limit],
        "cached": cached,
        "agent": agent,
        "session": session_summary(agent),
    })
    return 0


def _read_record(args, household_only: bool) -> int:
    # household is a VIEW of the record: both share one "record" cache entry
    # (same page, same fetch), so reading one never re-fetches for the other.
    cmd = "ancestry.household" if household_only else "ancestry.record"
    if not args.collection.isdigit() or not args.id.isdigit():
        raise CockpitError("collection and record id must be numeric")
    agent = agent_id(args.agent)
    loc = {"type": "record", "collection": args.collection, "id": args.id}
    key = location_key(loc)
    obj, cached = cached_or_fetch(
        key,
        agent=agent,
        fresh=args.fresh,
        cache_only=args.cache_only,
        fetch=lambda: browser_fetch_location(agent, loc),
        meta={"kind": "record", "collection": args.collection, "id": args.id},
        validate=lambda data: validate_location_data(loc, data),
    )
    view = {**obj, "command": cmd, "cached": cached, "agent": agent, "session": session_summary(agent)}
    if household_only:
        view.pop("fields", None)
    emit(view)
    return 0


def cmd_record(args) -> int:
    return _read_record(args, household_only=False)


def cmd_household(args) -> int:
    return _read_record(args, household_only=True)


# ---- relative navigation: an agent moves through Ancestry by address ----

def parse_address(addr: str) -> dict | None:
    m = re.fullmatch(r"record/(\d+)/(\d+)", addr)
    if m:
        return {"type": "record", "collection": m.group(1), "id": m.group(2)}
    m = re.fullmatch(r"collection/(\d+)", addr)
    if m:
        return {"type": "collection", "collection": m.group(1)}
    m = re.fullmatch(r"search/(\d+)(?:\?(.*))?", addr)
    if m:
        try:
            pairs = parse_qsl(m.group(2) or "", keep_blank_values=True, strict_parsing=True)
        except ValueError:
            return None
        allowed = {"name", *SEARCH_TEXT_FILTERS, "exact"}
        if any(k not in allowed for k, _v in pairs) or len({k for k, _v in pairs}) != len(pairs):
            return None
        params = dict(pairs)
        if not params.get("name"):
            return None
        if params.get("birth") and not re.fullmatch(r"\d{3,4}", params["birth"]):
            return None
        if "exact" in params and params["exact"] != "true":
            return None
        try:
            return search_location(
                m.group(1),
                params["name"],
                birth=params.get("birth", ""),
                place=params.get("place", ""),
                spouse=params.get("spouse", ""),
                birthplace=params.get("birthplace", ""),
                exact_name=params.get("exact") == "true",
            )
        except CockpitError:
            return None
    return None


def url_for(loc: dict) -> str:
    collection = quote(str(loc["collection"]), safe="")
    base = f"https://www.ancestry.com/search/collections/{collection}"
    if loc["type"] == "record":
        return f"{base}/records/{quote(str(loc['id']), safe='')}"
    if loc["type"] == "collection":
        return f"{base}/"
    return f"{base}/?{urlencode(ancestry_search_params(loc))}"


def location_key(loc: dict) -> str:
    if loc["type"] == "record":
        return cache_key("record", {"collection": loc["collection"], "id": loc["id"]})
    if loc["type"] == "search":
        # Same limit-free key as cmd_search: one query, one cache entry, shared
        # by the stateless and navigational paths.
        return cache_key("search", {"collection": loc["collection"], **search_filters(loc)})
    if loc["type"] == "collection":
        return cache_key("collection", {"collection": loc["collection"]})
    raise CockpitError("unsupported Ancestry location type", location_type=loc.get("type"))


def state_snapshot(state: dict) -> dict:
    return {
        "location": state.get("location"),
        "results": state.get("results", []),
        "cursor": state.get("cursor", 0),
    }


def go_to_location(
    agent: str,
    loc: dict,
    push: bool,
    fresh: bool,
    cache_only: bool,
    command: str = "ancestry.goto",
) -> int:
    """Move an agent to loc. Serve from cache without a hit when possible; only
    the actual browser navigation is a real (queued, paced) hit."""
    agent = agent_id(agent)
    state = load_agent(agent)
    key = location_key(loc)
    data, cached = cached_or_fetch(
        key,
        agent=agent,
        fresh=fresh,
        cache_only=cache_only,
        fetch=lambda: browser_fetch_location(agent, loc),
        meta={"kind": loc["type"], **{k: v for k, v in loc.items() if k != "type"}},
        validate=lambda value: validate_location_data(loc, value),
    )
    if push and state.get("location") is not None and state["location"] != loc:
        state["history"].append(state_snapshot(state))
    state["location"] = loc
    if loc["type"] == "search":
        state["results"] = data.get("results", [])
        state["cursor"] = 0
        # The iteration context outlives the current location: next/prev/open
        # keep working after this agent moves onto a record.
        state["last_search"] = {"location": loc, "results": state["results"], "cursor": 0}
    else:
        state["results"] = []
        state["cursor"] = 0
    save_agent(agent, state)
    emit({
        "command": command,
        "ok": True,
        "agent": agent,
        "location": loc,
        "navigated": not cached,
        "data": data,
        "session": session_summary(agent),
    })
    return 0


def cmd_goto(args) -> int:
    loc = parse_address(args.address)
    if loc is None:
        emit({"command": "ancestry.goto", "ok": False, "error": "unparseable address", "address": args.address})
        return 1
    return go_to_location(agent_id(args.agent), loc, push=True, fresh=args.fresh, cache_only=args.cache_only)


def cmd_where(args) -> int:
    agent = agent_id(args.agent)
    state = load_agent(agent)
    loc = state.get("location")
    cursor_at = None
    search = active_search(state)
    if search is not None:
        res, cur = search["results"], search["cursor"]
        cursor_at = {"cursor": cur, "count": len(res), "result": res[cur] if 0 <= cur < len(res) else None,
                     "search": search["location"], "live": search["live"]}
    emit({"command": "ancestry.where", "ok": True, "agent": agent, "location": loc,
          "history_depth": len(state.get("history", [])), "cursor_at": cursor_at})
    return 0


def active_search(state: dict) -> dict | None:
    """The agent's live iteration context: the current search when standing on
    one, else the persisted last_search (so opening a record never consumes
    the ability to keep stepping/opening results)."""
    loc = state.get("location")
    if isinstance(loc, dict) and loc.get("type") == "search" and state.get("results"):
        return {"location": loc, "results": state["results"], "cursor": state.get("cursor", 0), "live": True}
    last = state.get("last_search")
    if isinstance(last, dict) and last.get("results"):
        return {"location": last.get("location"), "results": last["results"], "cursor": last.get("cursor", 0), "live": False}
    return None


def step(agent: str, delta: int, command: str) -> int:
    state = load_agent(agent)
    search = active_search(state)
    if search is None:
        emit({"command": command, "ok": False, "error": "no active search; goto a search first", "agent": agent})
        return 1
    res = search["results"]
    cur = max(0, min(len(res) - 1, search["cursor"] + delta))
    if search["live"]:
        state["cursor"] = cur
        if isinstance(state.get("last_search"), dict):
            state["last_search"]["cursor"] = cur
    else:
        state["last_search"]["cursor"] = cur
    save_agent(agent, state)
    emit({"command": command, "ok": True, "agent": agent, "cursor": cur, "count": len(res), "result": res[cur]})
    return 0


def cmd_next(args) -> int:
    return step(agent_id(args.agent), 1, "ancestry.next")


def cmd_prev(args) -> int:
    return step(agent_id(args.agent), -1, "ancestry.prev")


def cmd_open(args) -> int:
    agent = agent_id(args.agent)
    state = load_agent(agent)
    search = active_search(state)
    if search is None:
        emit({"command": "ancestry.open", "ok": False, "error": "no active search; goto a search first", "agent": agent})
        return 1
    loc = search["location"]
    if not isinstance(loc, dict) or loc.get("type") != "search":
        emit({"command": "ancestry.open", "ok": False, "error": "no active search; goto a search first", "agent": agent})
        return 1
    res = search["results"]
    n = args.n if args.n is not None else search["cursor"]
    if not (0 <= n < len(res)):
        emit({"command": "ancestry.open", "ok": False, "error": "index out of range", "n": n, "count": len(res)})
        return 1
    validate_search_rows(res, loc["collection"])
    row = res[n]
    _host, row_path = _ancestry_url(row["url"])
    expected = rf"/search/collections/{re.escape(loc['collection'])}/records/{re.escape(row['record_id'])}"
    if not re.fullmatch(expected, row_path, re.IGNORECASE):
        emit({"command": "ancestry.open", "ok": False, "error": "active result does not belong to the active collection", "agent": agent})
        return 1
    record = {"type": "record", "collection": loc["collection"], "id": row["record_id"]}
    if isinstance(state.get("last_search"), dict):
        state["last_search"]["cursor"] = n
        save_agent(agent, state)
    return go_to_location(
        agent,
        record,
        push=True,
        fresh=args.fresh,
        cache_only=args.cache_only,
        command="ancestry.open",
    )


def cmd_back(args) -> int:
    agent = agent_id(args.agent)
    state = load_agent(agent)
    history = state.get("history", [])
    if not history:
        emit({"command": "ancestry.back", "ok": False, "error": "no history", "agent": agent})
        return 1
    previous = history.pop()
    if (
        not isinstance(previous, dict)
        or not {"location", "results", "cursor"}.issubset(previous)
        or (previous["location"] is not None and not isinstance(previous["location"], dict))
        or not isinstance(previous["results"], list)
        or not isinstance(previous["cursor"], int)
    ):
        raise CockpitError("malformed navigation history")
    state["history"] = history
    state["location"] = previous["location"]
    state["results"] = previous["results"]
    state["cursor"] = previous["cursor"]
    save_agent(agent, state)
    emit({
        "command": "ancestry.back",
        "ok": True,
        "agent": agent,
        "location": state["location"],
        "history_depth": len(history),
        "cursor": state["cursor"],
        "navigated": False,
    })
    return 0


def cmd_session(args) -> int:
    agent = agent_id(args.agent)
    if args.action == "stats":
        if args.confirm is not None:
            emit({
                "command": "ancestry.session.stats",
                "ok": False,
                "error": "--confirm is only valid with session reset",
                "agent": agent,
            })
            return 1
        with cache_lock():
            state = load_session(agent)
        emit({
            "command": "ancestry.session.stats",
            "ok": True,
            "agent": agent,
            "session": public_session_state(state),
        })
        return 0
    if args.confirm != SESSION_RESET_CONFIRMATION:
        emit({
            "command": "ancestry.session.reset",
            "ok": False,
            "error": f"refusing to reset accounting without --confirm {SESSION_RESET_CONFIRMATION}",
            "agent": agent,
        })
        return 1
    with cache_lock():
        state = new_session_state()
        save_session(agent, state)
    emit({
        "command": "ancestry.session.reset",
        "ok": True,
        "agent": agent,
        "session": public_session_state(state),
    })
    return 0


# ---- cache management (no browser, no hits) ----

def entry_kind(key: str, meta: dict | None) -> str:
    kind = meta.get("kind") if isinstance(meta, dict) else None
    if kind not in {"search", "record", "collection"}:
        raise CockpitError("malformed ancestry cache metadata", key=key)
    return kind


def cmd_cache(args) -> int:
    if args.kind is not None and args.kind not in CACHE_KINDS:
        emit({
            "command": f"ancestry.cache.{args.action}",
            "ok": False,
            "error": "unknown cache kind",
            "kind": args.kind,
            "expected": list(CACHE_KINDS),
        })
        return 1
    clear_only_used = bool(
        getattr(args, "all", False)
        or getattr(args, "include_records", False)
        or getattr(args, "confirm", None)
    )
    if args.action not in {"clear"} and clear_only_used:
        emit({
            "command": f"ancestry.cache.{args.action}",
            "ok": False,
            "error": "--all, --include-records, and --confirm are only valid with cache clear",
        })
        return 1
    if args.action == "clear" and args.kind and getattr(args, "all", False):
        emit({
            "command": "ancestry.cache.clear",
            "ok": False,
            "error": "choose exactly one cache clear scope: --kind or --all",
        })
        return 1
    with cache_lock():
        if args.action == "migrate":
            result = migrate_cache_locked(args.kind)
            ok = result["failed"] == 0
            emit({"command": "ancestry.cache.migrate", "ok": ok, "kind": args.kind or "all", **result})
            return 0 if ok else 1
        return _cmd_cache_locked(args)


def _cmd_cache_locked(args) -> int:
    valid_entries, invalid = cache_inventory()
    if args.action == "stats":
        by_kind: dict[str, int] = {}
        total = count = 0
        fetched = []
        for key, meta, size in valid_entries:
            kind = entry_kind(key, meta)
            if args.kind and kind != args.kind:
                continue
            by_kind[kind] = by_kind.get(kind, 0) + 1
            total += size
            count += 1
            if meta and meta.get("fetched_at"):
                fetched.append(meta["fetched_at"])
        result = {"command": "ancestry.cache.stats", "ok": not invalid, "kind": args.kind or "all",
                  "entries": count, "by_kind": by_kind,
                  "bytes": total, "oldest": min(fetched) if fetched else None,
                  "newest": max(fetched) if fetched else None, "dir": str(CACHE_DIR),
                  "invalid_entries": len(invalid), "invalid": invalid}
        if invalid:
            result["error"] = "invalid cache entries require `gen ancestry cache migrate`, repair, or a guarded clear --all"
        emit(result)
        return 0 if not invalid else 1
    if args.action == "list":
        rows = []
        for key, meta, size in valid_entries:
            kind = entry_kind(key, meta)
            if args.kind and kind != args.kind:
                continue
            row = {"key": key, "kind": kind, "bytes": size}
            if meta:
                row["fetched_at"] = meta.get("fetched_at")
                row["what"] = {k: v for k, v in meta.items() if k not in {"kind", "fetched_at", "url"}}
            rows.append(row)
        result = {"command": "ancestry.cache.list", "ok": not invalid, "count": len(rows),
                  "entries": rows, "invalid_entries": len(invalid), "invalid": invalid}
        if invalid:
            result["error"] = "invalid cache entries require `gen ancestry cache migrate`, repair, or a guarded clear --all"
        emit(result)
        return 0 if not invalid else 1
    # clear
    if not args.kind and not getattr(args, "all", False):
        emit({"command": "ancestry.cache.clear", "ok": False,
              "error": "refusing to clear everything without --all (or narrow with --kind)"})
        return 1
    if invalid and not args.all:
        emit({
            "command": "ancestry.cache.clear",
            "ok": False,
            "error": "cannot safely classify invalid cache entries; use guarded --all to remove them",
            "invalid_entries": len(invalid),
            "invalid": invalid,
            "removed": 0,
        })
        return 1
    targets = []
    for key, meta, _size in valid_entries:
        if args.kind and entry_kind(key, meta) != args.kind:
            continue
        targets.append((key, entry_kind(key, meta)))
    record_targets = [key for key, kind in targets if kind == "record"]
    protected_targets = len(record_targets) + (len(invalid) if args.all else 0)
    if protected_targets and (
        not getattr(args, "include_records", False)
        or getattr(args, "confirm", None) != RECORD_DELETE_CONFIRMATION
    ):
        emit({
            "command": "ancestry.cache.clear",
            "ok": False,
            "error": (
                "refusing to delete durable record acquisitions; pass --include-records and "
                f"--confirm {RECORD_DELETE_CONFIRMATION} to authorize deletion"
            ),
            "record_entries": len(record_targets),
            "invalid_entries": len(invalid) if args.all else 0,
        })
        return 1
    removed = 0
    for key, _kind in targets:
        try:
            (CACHE_DIR / f"{key}.json").unlink()
        except FileNotFoundError:
            continue
        else:
            removed += 1
    invalid_removed = 0
    if args.all:
        for row in invalid:
            try:
                (CACHE_DIR / f"{row['key']}.json").unlink()
            except FileNotFoundError:
                continue
            else:
                removed += 1
                invalid_removed += 1
    emit({"command": "ancestry.cache.clear", "ok": True, "removed": removed,
          "kind": args.kind or "all", "invalid_removed": invalid_removed})
    return 0


EPILOG = """\
addresses:
  record/COLL/ID                           one record's detail page
  search/COLL?name=Given_Surname&...       a collection search; optional birth,
                                            place, spouse, birthplace, exact=true
  collection/COLL                          a collection's landing page

semantics (what an agent must know):
  - Never launches a browser: connects to the already-running, logged-in Chrome
    (CDP :9222). If it is down, you get {"ok":false,"error":"cdp browser not
    reachable on :9222"} - ask the human to start it.
  - Every real Ancestry hit is serialized through a machine-global queue and
    human-paced (>= GEN_ANCESTRY_MIN_INTERVAL seconds apart, default 5, plus
    jitter) across ALL agents. You never need to rate-limit yourself.
    `session stats --agent ID` reports live hits charged just before browser I/O
    (including failed HTTP/parsing attempts), plus cache reads, since that
    agent's last guarded session reset.
  - DURABLE acquisition store, not an eviction cache: one latest validated
    snapshot per logical page or query lives in research/cache/ancestry
    (gitignored, backed up with the project). A normal revisit by any agent,
    any session, returns instantly with "cached":true and never touches
    Ancestry. A normal miss automatically joins the paced queue, rechecks the
    store under the lock, and fetches live; no --cache-only preflight is needed.
    record and household share one entry (same page). --fresh atomically
    replaces a snapshot (mainly for searches, which can gain rows as indexes
    grow). Inspect with `cache stats` / `cache list`; `cache clear` is guarded.
  - --cache-only guarantees a cache read or a JSON cache-miss error. It never
    probes CDP or sends a live request, is intended only when live access is
    forbidden, and cannot be combined with --fresh.
  - --agent ID gives you your own browser tab plus your own cursor, history, and
    accounting (state in ~/.gen-cockpit/ancestry/). Commands without --agent
    use the reserved "default" agent. The human's own tab is never driven. Use
    one process per agent id at a time.
  - Your location is LOGICAL: a cache-served goto updates state without moving
    the tab. back always restores the prior location, result set, and cursor
    entirely from private state. The "navigated" field reports whether the
    browser moved.
  - next/prev/where/back are pure local state: zero Ancestry hits.
  - Search reads page 1 only (up to ~20 rows); result_set.complete and warnings
    make that scope explicit, and next stops at the page edge.
  - Census household extraction reports parser completeness separately from
    dwelling coverage. In particular, pre-1880 record-associated rows may omit
    people who share the same dwelling/family number; follow the warning.

typical session:
  goto "search/6224?name=Marjorie_Clemans&birth=1912" --agent alice
  next --agent alice          # step the cursor through results, free
  open --agent alice          # open the record under the cursor (one hit)
  where --agent alice         # {location, history_depth, cursor_at}
  back --agent alice          # restored locally: "navigated":false
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

    # one-shot data commands (default agent unless --agent is supplied)
    p_search = sub.add_parser(
        "search", help="run a collection search -> {outcome, result_set, results:[{record_id, primary_name, cells}]}",
        description="Search one collection. Full result set is cached; --limit trims only the emitted view.")
    p_search.add_argument("--collection", required=True, metavar="N", help="Ancestry collection id (e.g. 6224 = 1930 census)")
    p_search.add_argument("--name", required=True, metavar="GIVEN_SURNAME", help="underscore-joined, e.g. Marjorie_Clemans")
    p_search.add_argument("--birth", metavar="YEAR", help="approximate birth year filter")
    p_search.add_argument("--place", metavar="PLACE", help="residence/event place filter, e.g. Smith_Kansas")
    p_search.add_argument("--spouse", metavar="GIVEN_SURNAME", help="spouse-name filter")
    p_search.add_argument("--birthplace", metavar="PLACE", help="birthplace filter")
    p_search.add_argument("--exact-name", action="store_true", help="require exact given and surname words")
    p_search.add_argument("--agent", metavar="ID", help="agent id for tab ownership and session accounting; default: 'default'")
    p_search.add_argument("--limit", type=int, default=25, metavar="K", help="max results to emit (default 25)")
    search_policy = p_search.add_mutually_exclusive_group()
    search_policy.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
    search_policy.add_argument("--cache-only", action="store_true", help="read cache only; never probe CDP or fetch live")
    p_search.set_defaults(func=cmd_search)

    for name, desc in (
        ("record", "read one record -> {fields, household, household_extraction, citation_metadata}"),
        ("household", "read one record, household members only"),
    ):
        p = sub.add_parser(name, help=desc, description=desc + ". Records use a durable validated snapshot.")
        p.add_argument("--collection", required=True, metavar="N", help="Ancestry collection id")
        p.add_argument("--id", required=True, metavar="RECORD_ID", help="record id within the collection")
        p.add_argument("--agent", metavar="ID", help="agent id for tab ownership and session accounting; default: 'default'")
        policy = p.add_mutually_exclusive_group()
        policy.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
        policy.add_argument("--cache-only", action="store_true", help="read cache only; never probe CDP or fetch live")
        p.set_defaults(func=cmd_record if name == "record" else cmd_household)

    # stateful navigation (per-agent tab + cursor + history)
    p_goto = sub.add_parser(
        "goto", help="move your agent to an address -> {location, navigated, data}",
        description="Move to an address (see epilog for the grammar). Pushes the previous location onto your history.")
    p_goto.add_argument("address", help="record/COLL/ID | search/COLL?name=..&birth=.. | collection/COLL")
    p_goto.add_argument("--agent", metavar="ID", help="your agent id (own tab, cursor, history); default: 'default'")
    goto_policy = p_goto.add_mutually_exclusive_group()
    goto_policy.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
    goto_policy.add_argument("--cache-only", action="store_true", help="read cache only; never probe CDP or fetch live")
    p_goto.set_defaults(func=cmd_goto)

    for name, func, desc in (
        ("where", cmd_where, "report your logical location, history depth, and cursor -> no Ancestry hit"),
        ("next", cmd_next, "step the search cursor forward -> {cursor, result}; no Ancestry hit"),
        ("prev", cmd_prev, "step the search cursor back -> {cursor, result}; no Ancestry hit"),
        ("back", cmd_back, "pop history and restore it locally; no Ancestry hit"),
    ):
        p = sub.add_parser(name, help=desc, description=desc + ".")
        p.add_argument("--agent", metavar="ID", help="your agent id; default: 'default'")
        p.set_defaults(func=func)

    p_open = sub.add_parser(
        "open", help="open search result N, or the one under your cursor -> a record",
        description="Open result N of your current search (0-based); with no N, opens the result under your cursor.")
    p_open.add_argument("n", nargs="?", type=int, default=None, metavar="N", help="0-based result index (default: cursor)")
    p_open.add_argument("--agent", metavar="ID", help="your agent id; default: 'default'")
    open_policy = p_open.add_mutually_exclusive_group()
    open_policy.add_argument("--fresh", action="store_true", help="bypass the cache; force a live fetch")
    open_policy.add_argument("--cache-only", action="store_true", help="read cache only; never probe CDP or fetch live")
    p_open.set_defaults(func=cmd_open)

    p_session = sub.add_parser(
        "session",
        help="inspect or reset per-agent live-hit accounting -> stats | reset; no Ancestry hit",
        description="Accounting begins at the first access after a guarded reset and persists across CLI processes.",
    )
    p_session.add_argument("action", choices=["stats", "reset"], help="inspect counters or begin a new accounting session")
    p_session.add_argument("--agent", required=True, metavar="ID", help="agent id whose accounting session to inspect/reset")
    p_session.add_argument("--confirm", metavar="PHRASE", help="required reset phrase shown by a refused reset")
    p_session.set_defaults(func=cmd_session)

    p_cache = sub.add_parser(
        "cache", help="manage the shared cache -> stats | list | migrate | clear; no Ancestry hits",
        description="Manage the private acquisition store. migrate performs the explicit v2-to-v3 hard cutover; no action touches Ancestry.")
    p_cache.add_argument("action", choices=["stats", "list", "migrate", "clear"], help="what to do")
    p_cache.add_argument(
        "--kind",
        metavar="KIND",
        help="filter/narrow to one kind: collection, record, or search",
    )
    p_cache.add_argument("--all", action="store_true", help="required to clear without a --kind filter")
    p_cache.add_argument("--include-records", action="store_true", help="permit durable record deletion when paired with --confirm")
    p_cache.add_argument("--confirm", metavar="PHRASE", help="record deletion confirmation phrase shown by a refused clear")
    p_cache.set_defaults(func=cmd_cache)

    args = parser.parse_args()
    try:
        return args.func(args)
    except CockpitError as exc:
        command = f"ancestry.cache.{args.action}" if args.cmd == "cache" else f"ancestry.{args.cmd}"
        emit({"command": command, "ok": False, "error": exc.error, **exc.details})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
