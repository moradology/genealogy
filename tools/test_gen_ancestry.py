#!/usr/bin/env python3
"""Offline tests for tools/gen_ancestry.py.

Every filesystem write uses a temporary directory and every browser/network
boundary is mocked. Run: uv run tools/test_gen_ancestry.py
"""

from __future__ import annotations

import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_ancestry as ga  # noqa: E402


FIXTURE = (
    "View\nExample Person\n1940 United States Federal Census \n"
    "Detail \nHow to evaluate details\n"
    "Name\tExample Person\nAge\t29\nEstimated Birth Year\tabt 1911\n"
    "Birthplace\tKansas\nOccupation\tMechanic\n"
    "Household Members (Name)\tAge\tRelationship\n"
    "Example Head\n\t\n58\n\t\nHead\n"
    "Example Wife\t45\tWife\n"
    "Example Son\n\t\n10\n\t\nSon\n"
    "Save this record?\nSource\nSource Citation\n"
)


def row(collection: str = "6224", record_id: str = "100") -> dict:
    return {
        "record_id": record_id,
        "url": f"https://www.ancestry.com/search/collections/{collection}/records/{record_id}",
        "cells": ["Example Person", "1911"],
        "text": "Example Person 1911 Kansas",
    }


def search_loc(collection: str = "6224") -> dict:
    return {"type": "search", "collection": collection, "name": "Example_Person", "birth": "1911"}


def search_data(collection: str = "6224") -> dict:
    rows = [row(collection)]
    return {
        "command": "ancestry.search",
        "ok": True,
        "collection": collection,
        "name": "Example_Person",
        "birth": "1911",
        "count": len(rows),
        "outcome": "results",
        "results": rows,
    }


def record_loc(collection: str = "6224", record_id: str = "100") -> dict:
    return {"type": "record", "collection": collection, "id": record_id}


def record_data(collection: str = "6224", record_id: str = "100") -> dict:
    return {
        "command": "ancestry.record",
        "ok": True,
        "collection": collection,
        "record_id": record_id,
        "fields": {"Name": "Example Person", "Age": "29"},
        "household": [{"name": "Example Head", "age": "58", "relation": "Head"}],
    }


@contextmanager
def temporary_runtime():
    with tempfile.TemporaryDirectory(prefix="gen-ancestry-test-") as tmp:
        root = Path(tmp)
        state = root / "state" / "ancestry"
        values = {
            "STATE_DIR": state,
            "CACHE_DIR": root / "cache",
            "LOCK_PATH": state / "queue.lock",
            "LAST_PATH": state / "last_request",
            "AGENTS_DIR": state / "agents",
            "TABS_PATH": state / "tabs.json",
        }
        with patch.multiple(ga, **values):
            yield root


def captured(callable_, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        code = callable_(*args)
    return code, json.loads(out.getvalue())


class ParsingTests(unittest.TestCase):
    def test_detail_and_household_shapes(self):
        fields = ga.parse_detail_fields(FIXTURE)
        self.assertEqual(fields["Name"], "Example Person")
        self.assertEqual(fields["Occupation"], "Mechanic")
        self.assertNotIn("Example Head", " ".join(fields.values()))
        triples = [(m["name"], m["age"], m["relation"]) for m in ga.parse_household(FIXTURE)]
        self.assertEqual(
            triples,
            [("Example Head", "58", "Head"), ("Example Wife", "45", "Wife"), ("Example Son", "10", "Son")],
        )

    def test_address_grammar_and_urls(self):
        rec = ga.parse_address("record/2442/58087568")
        self.assertEqual(rec, {"type": "record", "collection": "2442", "id": "58087568"})
        search = ga.parse_address("search/6224?name=Example_Person&birth=1912")
        self.assertEqual(search, {"type": "search", "collection": "6224", "name": "Example_Person", "birth": "1912"})
        self.assertEqual(ga.parse_address("collection/6224"), {"type": "collection", "collection": "6224"})
        self.assertIsNone(ga.parse_address("record/not-numeric/1"))
        self.assertIsNone(ga.parse_address("search/6224?name=&other=x"))
        self.assertEqual(
            ga.url_for(rec),
            "https://www.ancestry.com/search/collections/2442/records/58087568",
        )
        self.assertEqual(
            ga.url_for(search),
            "https://www.ancestry.com/search/collections/6224/?name=Example_Person&birth=1912",
        )
        collection = {"type": "collection", "collection": "6224"}
        self.assertEqual(
            ga.location_key(collection),
            ga.cache_key("collection", {"collection": "6224"}),
        )

    def test_agent_ids_are_validated_and_hashed(self):
        self.assertEqual(ga.agent_id("alice-2"), "alice-2")
        self.assertEqual(len(ga.agent_disk_key("alice-2")), 32)
        self.assertNotIn("alice", ga.agent_disk_key("alice-2"))
        for bad in ("../escape", "/absolute", ".", "space name", "x" * 65):
            with self.assertRaises(ga.CockpitError):
                ga.agent_id(bad)


class ValidationTests(unittest.TestCase):
    def test_page_accepts_expected_url_and_rejects_redirects_and_challenges(self):
        loc = search_loc()
        good = "https://www.ancestry.com/search/collections/6224/?name=Example_Person"
        ga.validate_page(loc, good, "Search results", "Search results with enough page content to be complete")
        with self.assertRaisesRegex(ga.CockpitError, "wrong collection"):
            ga.validate_page(loc, "https://www.ancestry.com/search/collections/9999/", "Results", "Enough normal page content to validate")
        with self.assertRaisesRegex(ga.CockpitError, "login"):
            ga.validate_page(loc, "https://www.ancestry.com/account/signin", "Sign in", "Sign in to Ancestry to continue")
        with self.assertRaisesRegex(ga.CockpitError, "challenge"):
            ga.validate_page(loc, good, "Security check", "Please verify you are human before continuing")
        with self.assertRaisesRegex(ga.CockpitError, "origin"):
            ga.validate_page(loc, "https://example.org/search/collections/6224/", "Results", "Enough normal page content to validate")

    def test_parsed_shapes_are_strict(self):
        ga.validate_search_rows([row()], "6224")
        ga.validate_record_data({"Name": "Example Person"}, [])
        with self.assertRaisesRegex(ga.CockpitError, "another collection"):
            ga.validate_search_rows([row("9999")], "6224")
        with self.assertRaisesRegex(ga.CockpitError, "no detail fields"):
            ga.validate_record_data({}, [])
        malformed = {"name": "Example", "age": "1"}
        with self.assertRaisesRegex(ga.CockpitError, "household member"):
            ga.validate_record_data({"Name": "Example"}, [malformed])
        ga.validate_response(SimpleNamespace(status=200))
        with self.assertRaisesRegex(ga.CockpitError, "unsuccessful HTTP"):
            ga.validate_response(SimpleNamespace(status=429))
        with self.assertRaisesRegex(ga.CockpitError, "no HTTP response"):
            ga.validate_response(None)

    def test_search_outcome_requires_name_match_or_explicit_no_results(self):
        self.assertEqual(
            ga.validate_search_outcome(search_loc(), "Search results", [row()]),
            "results",
        )
        fuzzy_loc = {**search_loc(), "name": "Leora_Mundell"}
        fuzzy = {**row(), "cells": ["Leora Mendell"], "text": "Leora Mendell 1937 Denver"}
        self.assertEqual(ga.validate_search_outcome(fuzzy_loc, "Search results", [fuzzy]), "results")

        unrelated = {**row(), "cells": ["Someone Else"], "text": "Someone Else 1911 Kansas"}
        with self.assertRaisesRegex(ga.CockpitError, "unrelated"):
            ga.validate_search_outcome(search_loc(), "Search results", [unrelated])
        with self.assertRaisesRegex(ga.CockpitError, "stable result state"):
            ga.validate_search_outcome(search_loc(), "Search page still loading", [])
        self.assertEqual(
            ga.validate_search_outcome(search_loc(), "We couldn't find any matching records", []),
            "no-results",
        )

    def test_cached_search_requires_current_validated_outcome(self):
        stale = search_data()
        stale.pop("outcome")
        with self.assertRaisesRegex(ga.CockpitError, "validated outcome"):
            ga.validate_location_data(search_loc(), stale)

    def test_cached_search_requires_exact_birth_query(self):
        wrong_birth = search_data()
        wrong_birth["birth"] = "1912"
        with self.assertRaisesRegex(ga.CockpitError, "requested query"):
            ga.validate_location_data(search_loc(), wrong_birth)

    def test_browser_boundary_is_mocked_and_validated(self):
        class Page:
            url = "https://www.ancestry.com/search/collections/6224/?name=Example_Person"

            def goto(self, *_args, **_kwargs):
                return SimpleNamespace(status=200)

            def wait_for_timeout(self, _milliseconds):
                return None

            def title(self):
                return "Search results"

            def evaluate(self, script):
                return [row()] if script == ga.SEARCH_JS else "Search results with enough complete page content"

        with patch.object(ga, "run_on_page", side_effect=lambda fn, agent: fn(Page())):
            data, meta = ga.browser_fetch_location("alice", search_loc())
        self.assertEqual(data, search_data())
        self.assertEqual(meta["final_url"], Page.url)


class DurableStoreTests(unittest.TestCase):
    def test_cache_and_state_writes_are_versioned_atomic_and_private(self):
        with temporary_runtime():
            loc = record_loc()
            key = ga.location_key(loc)
            ga.cache_write(key, record_data(), {"kind": "record", "collection": "6224", "id": "100"})
            cache_path = ga.CACHE_DIR / f"{key}.json"
            envelope = json.loads(cache_path.read_text())
            self.assertEqual((envelope["schema"], envelope["version"]), (ga.CACHE_SCHEMA, ga.CACHE_VERSION))
            self.assertEqual(stat.S_IMODE(cache_path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(ga.CACHE_DIR.stat().st_mode), 0o700)
            self.assertEqual(list(ga.CACHE_DIR.glob(".*.tmp")), [])

            state = ga.new_agent_state()
            ga.save_agent("alice", state)
            path = ga.AGENTS_DIR / f"{ga.agent_disk_key('alice')}.json"
            self.assertTrue(path.exists())
            self.assertFalse((ga.AGENTS_DIR / "alice.json").exists())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(ga.AGENTS_DIR.stat().st_mode), 0o700)
            self.assertEqual(ga.load_agent("alice"), state)

            tabs = ga.new_tabs_state()
            ga.save_json(ga.TABS_PATH, tabs)
            self.assertEqual(ga.load_tabs(), tabs)
            with patch.object(ga.time, "time", return_value=1234.5):
                ga.throttle()
            pacing = json.loads(ga.LAST_PATH.read_text())
            self.assertEqual(
                (pacing["schema"], pacing["version"], pacing["last_request_epoch"]),
                (ga.REQUEST_STATE_SCHEMA, ga.STATE_VERSION, 1234.5),
            )
            self.assertEqual(stat.S_IMODE(ga.TABS_PATH.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(ga.LAST_PATH.stat().st_mode), 0o600)
            with ga.cache_lock():
                pass
            self.assertEqual(stat.S_IMODE(ga.LOCK_PATH.stat().st_mode), 0o600)

    def test_legacy_cache_is_rejected_not_read(self):
        with temporary_runtime():
            ga.ensure_state()
            (ga.CACHE_DIR / "search-legacy.json").write_text(json.dumps({"ok": True, "results": []}))
            with self.assertRaisesRegex(ga.CockpitError, "unsupported ancestry cache format"):
                ga.cache_read("search-legacy")

    def test_previous_cache_version_is_rejected_not_read(self):
        with temporary_runtime():
            ga.ensure_state()
            path = ga.CACHE_DIR / "search-v1.json"
            path.write_text(json.dumps({
                "schema": ga.CACHE_SCHEMA,
                "version": ga.CACHE_VERSION - 1,
                "meta": {"kind": "search"},
                "data": search_data(),
            }))
            with self.assertRaisesRegex(ga.CockpitError, "unsupported ancestry cache format"):
                ga.cache_read("search-v1")

    def test_cache_envelope_requires_strict_timestamp(self):
        loc = search_loc()
        key = ga.location_key(loc)
        envelope = {
            "schema": ga.CACHE_SCHEMA,
            "version": ga.CACHE_VERSION,
            "meta": {
                "kind": "search",
                "collection": "6224",
                "name": "Example_Person",
                "birth": "1911",
                "fetched_at": 123,
            },
            "data": search_data(),
        }
        with self.assertRaisesRegex(ga.CockpitError, "timestamp"):
            ga.validate_cache_envelope(key, envelope)

    def test_legacy_cache_command_returns_one_json_error(self):
        with temporary_runtime():
            ga.ensure_state()
            (ga.CACHE_DIR / "search-legacy.json").write_text(json.dumps({"ok": True, "results": []}))
            with patch.object(sys, "argv", ["gen ancestry", "cache", "stats"]):
                code, output = captured(ga.main)
            self.assertEqual(code, 1)
            self.assertFalse(output["ok"])
            self.assertEqual(output["command"], "ancestry.cache.stats")
            self.assertEqual(output["invalid_entries"], 1)
            self.assertIn("invalid cache entries", output["error"])

    def test_cache_only_miss_never_checks_cdp_or_fetches(self):
        with temporary_runtime(), patch.object(ga, "cdp_up") as cdp, patch.object(ga, "throttle") as throttle:
            fetch = Mock()
            with self.assertRaisesRegex(ga.CockpitError, "cache miss"):
                ga.cached_or_fetch(
                    "search-miss",
                    fresh=False,
                    cache_only=True,
                    fetch=fetch,
                    meta={"kind": "search"},
                    validate=lambda _data: None,
                )
            cdp.assert_not_called()
            throttle.assert_not_called()
            fetch.assert_not_called()

    def test_miss_is_rechecked_inside_lock_before_live_request(self):
        cached = search_data()
        with temporary_runtime(), patch.object(ga, "cache_read", side_effect=[None, cached]) as read:
            with patch.object(ga, "cdp_up") as cdp, patch.object(ga, "throttle") as throttle:
                fetch = Mock()
                got, was_cached = ga.cached_or_fetch(
                    "search-race",
                    fresh=False,
                    cache_only=False,
                    fetch=fetch,
                    meta={"kind": "search"},
                    validate=lambda data: ga.validate_location_data(search_loc(), data),
                )
        self.assertEqual(got, cached)
        self.assertTrue(was_cached)
        self.assertEqual(read.call_count, 2)
        cdp.assert_not_called()
        throttle.assert_not_called()
        fetch.assert_not_called()

    def test_validation_happens_before_cache_write(self):
        with temporary_runtime(), patch.object(ga, "cdp_up", return_value=True), patch.object(ga, "throttle"):
            with self.assertRaises(ga.CockpitError):
                ga.cached_or_fetch(
                    "search-invalid",
                    fresh=False,
                    cache_only=False,
                    fetch=lambda: ({"ok": True}, {"final_url": "https://www.ancestry.com"}),
                    meta={"kind": "search"},
                    validate=lambda data: ga.validate_location_data(search_loc(), data),
                )
            self.assertFalse((ga.CACHE_DIR / "search-invalid.json").exists())

    def test_valid_fetch_is_durable_before_return(self):
        with temporary_runtime(), patch.object(ga, "cdp_up", return_value=True), patch.object(ga, "throttle"):
            key = ga.location_key(search_loc())
            data, cached = ga.cached_or_fetch(
                key,
                fresh=False,
                cache_only=False,
                fetch=lambda: (search_data(), {"final_url": ga.url_for(search_loc())}),
                meta={"kind": "search", "collection": "6224", "name": "Example_Person", "birth": "1911"},
                validate=lambda value: ga.validate_location_data(search_loc(), value),
            )
            self.assertFalse(cached)
            self.assertEqual(data, ga.cache_read(key))

    def test_record_clear_requires_two_explicit_confirmations(self):
        with temporary_runtime():
            record_key = ga.location_key(record_loc())
            search_key = ga.location_key(search_loc())
            ga.cache_write(record_key, record_data(), {"kind": "record", "collection": "6224", "id": "100"})
            ga.cache_write(
                search_key,
                search_data(),
                {"kind": "search", "collection": "6224", "name": "Example_Person", "birth": "1911"},
            )
            args = SimpleNamespace(action="clear", kind=None, all=True, include_records=False, confirm=None)
            code, output = captured(ga.cmd_cache, args)
            self.assertEqual(code, 1)
            self.assertFalse(output["ok"])
            self.assertTrue((ga.CACHE_DIR / f"{record_key}.json").exists())
            self.assertTrue((ga.CACHE_DIR / f"{search_key}.json").exists())

            args = SimpleNamespace(action="clear", kind="search", all=False, include_records=False, confirm=None)
            code, output = captured(ga.cmd_cache, args)
            self.assertEqual((code, output["removed"]), (0, 1))
            self.assertTrue((ga.CACHE_DIR / f"{record_key}.json").exists())

            args = SimpleNamespace(
                action="clear",
                kind="record",
                all=False,
                include_records=True,
                confirm=ga.RECORD_DELETE_CONFIRMATION,
            )
            code, output = captured(ga.cmd_cache, args)
            self.assertEqual((code, output["removed"]), (0, 1))
            self.assertFalse((ga.CACHE_DIR / f"{record_key}.json").exists())

    def test_cache_admin_holds_unpaced_lock_and_tolerates_disappeared_target(self):
        with temporary_runtime():
            held = False

            @contextmanager
            def observed_lock():
                nonlocal held
                held = True
                try:
                    yield
                finally:
                    held = False

            def inventory():
                self.assertTrue(held)
                return [(
                    "search-gone",
                    {"kind": "search", "fetched_at": "2026-01-01T00:00:00Z"},
                    10,
                )], []

            args = SimpleNamespace(action="clear", kind="search", all=False, include_records=False, confirm=None)
            with patch.object(ga, "cache_lock", observed_lock), patch.object(ga, "cache_inventory", side_effect=inventory):
                with patch.object(ga, "throttle") as throttle, patch.object(ga, "cdp_up") as cdp:
                    code, output = captured(ga.cmd_cache, args)
            self.assertEqual((code, output["removed"]), (0, 0))
            self.assertFalse(held)
            throttle.assert_not_called()
            cdp.assert_not_called()

    def test_cache_kind_typo_is_a_json_error(self):
        with temporary_runtime():
            with patch.object(sys, "argv", ["gen ancestry", "cache", "list", "--kind", "seach"]):
                code, output = captured(ga.main)
            self.assertEqual(code, 1)
            self.assertFalse(output["ok"])
            self.assertEqual(output["error"], "unknown cache kind")
            self.assertEqual(output["expected"], list(ga.CACHE_KINDS))

    def test_cache_stats_honors_kind_filter(self):
        with temporary_runtime():
            ga.cache_write(
                ga.location_key(record_loc()),
                record_data(),
                {"kind": "record", "collection": "6224", "id": "100"},
            )
            ga.cache_write(
                ga.location_key(search_loc()),
                search_data(),
                {"kind": "search", "collection": "6224", "name": "Example_Person", "birth": "1911"},
            )
            args = SimpleNamespace(action="stats", kind="record")
            code, output = captured(ga.cmd_cache, args)
            self.assertEqual(code, 0)
            self.assertEqual(output["kind"], "record")
            self.assertEqual(output["entries"], 1)
            self.assertEqual(output["by_kind"], {"record": 1})

            args = SimpleNamespace(action="list", kind="record", all=False, include_records=False, confirm=None)
            code, output = captured(ga.cmd_cache, args)
            self.assertEqual(code, 0)
            self.assertEqual(output["count"], 1)
            self.assertEqual(output["entries"][0]["kind"], "record")

    def test_cache_admin_rejects_mislabeled_record_before_deletion(self):
        with temporary_runtime():
            loc = search_loc()
            key = ga.location_key(loc)
            ga.ensure_state()
            path = ga.CACHE_DIR / f"{key}.json"
            ga.atomic_write_json(path, {
                "schema": ga.CACHE_SCHEMA,
                "version": ga.CACHE_VERSION,
                "meta": {"kind": "search", "collection": "6224", "name": "Example_Person", "birth": "1911"},
                "data": record_data(),
            })
            with patch.object(sys, "argv", ["gen ancestry", "cache", "clear", "--kind", "search"]):
                code, output = captured(ga.main)
            self.assertEqual(code, 1)
            self.assertIn("cannot safely classify", output["error"])
            self.assertTrue(path.exists())

            with patch.object(sys, "argv", ["gen ancestry", "cache", "clear", "--all"]):
                code, output = captured(ga.main)
            self.assertEqual(code, 1)
            self.assertEqual(output["invalid_entries"], 1)
            self.assertTrue(path.exists())

            with patch.object(sys, "argv", [
                "gen ancestry", "cache", "clear", "--all", "--include-records",
                "--confirm", ga.RECORD_DELETE_CONFIRMATION,
            ]):
                code, output = captured(ga.main)
            self.assertEqual(code, 0)
            self.assertEqual(output["invalid_removed"], 1)
            self.assertFalse(path.exists())

    def test_cache_action_flags_are_strict(self):
        with temporary_runtime():
            with patch.object(sys, "argv", ["gen ancestry", "cache", "clear", "--kind", "search", "--all"]):
                code, output = captured(ga.main)
            self.assertEqual(code, 1)
            self.assertIn("exactly one", output["error"])

            with patch.object(sys, "argv", ["gen ancestry", "cache", "stats", "--all"]):
                code, output = captured(ga.main)
            self.assertEqual(code, 1)
            self.assertIn("only valid with cache clear", output["error"])


class NavigationTests(unittest.TestCase):
    def test_collection_goto_is_cacheable_and_cache_only(self):
        with temporary_runtime(), patch.object(ga, "cdp_up") as cdp:
            loc = {"type": "collection", "collection": "6224"}
            data = {"command": "ancestry.collection", "ok": True, "collection": "6224"}
            ga.cache_write(ga.location_key(loc), data, {"kind": "collection", "collection": "6224"})
            code, output = captured(
                ga.go_to_location,
                "alice",
                loc,
                True,
                False,
                True,
            )
            self.assertEqual(code, 0)
            self.assertFalse(output["navigated"])
            self.assertEqual(output["data"], data)
            cdp.assert_not_called()

    def test_back_restores_search_results_and_cursor_without_browser(self):
        with temporary_runtime():
            old = search_loc()
            state = ga.new_agent_state()
            state["location"] = record_loc()
            state["history"] = [{"location": old, "results": [row()], "cursor": 1}]
            ga.save_agent("alice", state)
            code, output = captured(ga.cmd_back, SimpleNamespace(agent="alice"))
            restored = ga.load_agent("alice")
            self.assertEqual(code, 0)
            self.assertEqual(output["command"], "ancestry.back")
            self.assertFalse(output["navigated"])
            self.assertEqual(restored["location"], old)
            self.assertEqual(restored["results"], [row()])
            self.assertEqual(restored["cursor"], 1)

    def test_next_and_prev_report_the_invoked_command(self):
        with temporary_runtime():
            state = ga.new_agent_state()
            state["location"] = search_loc()
            state["results"] = [row(record_id="100"), row(record_id="101")]
            ga.save_agent("alice", state)

            code, output = captured(ga.cmd_next, SimpleNamespace(agent="alice"))
            self.assertEqual(code, 0)
            self.assertEqual(output["command"], "ancestry.next")
            self.assertEqual(output["cursor"], 1)

            code, output = captured(ga.cmd_prev, SimpleNamespace(agent="alice"))
            self.assertEqual(code, 0)
            self.assertEqual(output["command"], "ancestry.prev")
            self.assertEqual(output["cursor"], 0)

    def test_open_reports_open_when_record_is_cache_served(self):
        with temporary_runtime(), patch.object(ga, "cdp_up") as cdp:
            state = ga.new_agent_state()
            state["location"] = search_loc()
            state["results"] = [row()]
            ga.save_agent("alice", state)
            loc = record_loc()
            ga.cache_write(
                ga.location_key(loc),
                record_data(),
                {"kind": "record", "collection": "6224", "id": "100"},
            )

            code, output = captured(
                ga.cmd_open,
                SimpleNamespace(agent="alice", n=0, fresh=False, cache_only=True),
            )
            self.assertEqual(code, 0)
            self.assertEqual(output["command"], "ancestry.open")
            self.assertFalse(output["navigated"])
            cdp.assert_not_called()

    def test_open_rejects_stale_cross_collection_results(self):
        with temporary_runtime():
            state = ga.new_agent_state()
            state["location"] = search_loc("6224")
            state["results"] = [row("9999")]
            ga.save_agent("alice", state)
            with patch.object(ga, "go_to_location") as go:
                with self.assertRaisesRegex(ga.CockpitError, "another collection"):
                    ga.cmd_open(SimpleNamespace(agent="alice", n=0, fresh=False, cache_only=True))
            go.assert_not_called()

    def test_open_requires_an_active_search(self):
        with temporary_runtime():
            state = ga.new_agent_state()
            state["location"] = record_loc()
            ga.save_agent("alice", state)
            code, output = captured(
                ga.cmd_open,
                SimpleNamespace(agent="alice", n=0, fresh=False, cache_only=True),
            )
            self.assertEqual(code, 1)
            self.assertEqual(output["error"], "no active search; goto a search first")


if __name__ == "__main__":
    unittest.main(verbosity=2)
