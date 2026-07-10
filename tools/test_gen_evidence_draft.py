#!/usr/bin/env python3
"""Regression tests for cache-backed evidence draft generation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gen_ancestry
import gen_evidence_draft
from test_check_evidence import EvidenceFixture


ROOT = Path(__file__).resolve().parents[1]


def record_data(*, literal_citation: bool) -> dict:
    citation_fields = (
        {
            "source_citation": "Year: 1880; Census Place: Test Township, Test County, Kansas",
            "source_information": "Ancestry.com. 1880 United States Federal Census.",
        }
        if literal_citation
        else {}
    )
    warnings = [] if literal_citation else ["Source Citation text was not available"]
    return {
        "command": "ancestry.record",
        "ok": True,
        "collection": "6742",
        "record_id": "123",
        "fields": {
            "Name": "Test Person",
            "Home in 1880": "Test Township, Test County, Kansas, USA",
            "Dwelling Number": "42",
        },
        "household": [
            {"name": "Test Person", "age": "40", "relation": "Self (Head)"}
        ],
        "household_extraction": {
            "present": True,
            "complete": True,
            "dwelling_complete": None,
            "method": "table",
            "columns": ["name", "age", "relation"],
            "warnings": [],
        },
        "citation_metadata": {
            "complete": literal_citation,
            "fields": citation_fields,
            "warnings": warnings,
        },
    }


class CacheFixture:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.state = self.root / "state/ancestry"
        self.cache = self.root / "cache"
        self._patch = patch.multiple(
            gen_ancestry,
            STATE_DIR=self.state,
            CACHE_DIR=self.cache,
            LOCK_PATH=self.state / "queue.lock",
            LAST_PATH=self.state / "last_request",
            AGENTS_DIR=self.state / "agents",
            SESSIONS_DIR=self.state / "sessions",
            TABS_PATH=self.state / "tabs.json",
        )
        self._patch.start()

    def close(self) -> None:
        self._patch.stop()
        self._tmp.cleanup()

    def write_record(
        self, *, literal_citation: bool, include_urls: bool = True
    ) -> tuple[str, dict]:
        loc = {"type": "record", "collection": "6742", "id": "123"}
        key = gen_ancestry.location_key(loc)
        data = record_data(literal_citation=literal_citation)
        url = "https://www.ancestry.com/search/collections/6742/records/123"
        metadata = {
            "kind": "record",
            "collection": "6742",
            "id": "123",
        }
        if include_urls:
            metadata.update({"requested_url": url, "final_url": url})
        gen_ancestry.cache_write(
            key,
            data,
            metadata,
        )
        return key, data


class EvidenceDraftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = CacheFixture()

    def tearDown(self) -> None:
        self.cache.close()

    def draft(self) -> dict:
        return gen_evidence_draft.build_draft(
            address="record/6742/123",
            evidence_id="ev.ancestry.test-record",
            record_type=None,
            title=None,
            batch=None,
            person_refs=[],
            case_refs=[],
        )

    def assert_reviewed_draft_valid(self, record: dict) -> None:
        record["privacy_review"] = {
            "status": "passed",
            "reviewed": "2026-07-09",
            "living_people": "excluded",
            "sensitive_identifiers": "excluded",
        }
        record["transcription"] = "A privacy-reviewed abstract."
        record["acquisition"]["pull"] = "01"
        fixture = EvidenceFixture()
        try:
            fixture.write([record])
            result = fixture.validate()
        finally:
            fixture.close()
        self.assertTrue(result.ok, result.errors)

    def test_literal_source_citation_and_digest_are_preserved(self) -> None:
        _key, data = self.cache.write_record(literal_citation=True)
        payload = self.draft()
        draft = payload["draft"]
        self.assertIn("Year: 1880", draft["citation"])
        self.assertNotIn("citation_gap", draft)
        expected = hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(draft["cache_provenance"]["data_sha256"], expected)
        self.assertEqual(
            draft["cache_provenance"]["record_address"], "record/6742/123"
        )
        self.assertIsNone(draft["cache_provenance"]["url_gap"])
        self.assertEqual(draft["privacy_review"]["status"], "pending")
        self.assert_reviewed_draft_valid(draft)

    def test_missing_literal_citation_gets_explicit_gap(self) -> None:
        self.cache.write_record(literal_citation=False)
        payload = self.draft()
        self.assertIn("citation_gap", payload["draft"])
        self.assertTrue(payload["warnings"])

    def test_legacy_record_without_urls_gets_explicit_provenance_gap(self) -> None:
        self.cache.write_record(literal_citation=True, include_urls=False)
        payload = self.draft()
        provenance = payload["draft"]["cache_provenance"]
        self.assertEqual(provenance["record_address"], "record/6742/123")
        self.assertIsNone(provenance["requested_url"])
        self.assertIsNone(provenance["final_url"])
        self.assertIn("legacy cached acquisition", provenance["url_gap"])
        self.assertEqual(payload["draft"]["source_urls"], [])
        self.assertIn(provenance["url_gap"], payload["warnings"])
        self.assert_reviewed_draft_valid(payload["draft"])

    def test_cache_miss_never_probes_cdp(self) -> None:
        with patch.object(gen_ancestry, "cdp_up", side_effect=AssertionError("CDP called")):
            with self.assertRaises(gen_ancestry.CockpitError) as caught:
                self.draft()
        self.assertIn("no live request", caught.exception.error)

    def test_invalid_cache_envelope_never_probes_cdp(self) -> None:
        gen_ancestry.ensure_state()
        loc = {"type": "record", "collection": "6742", "id": "123"}
        key = gen_ancestry.location_key(loc)
        url = "https://www.ancestry.com/search/collections/6742/records/123"
        gen_ancestry.atomic_write_json(
            self.cache.cache / f"{key}.json",
            {
                "schema": gen_ancestry.CACHE_SCHEMA,
                "version": gen_ancestry.CACHE_VERSION,
                "meta": {
                    "kind": "record",
                    "collection": "6742",
                    "id": "123",
                    "fetched_at": "2026-07-09T20:48:33Z",
                    "data_sha256": "0" * 64,
                    "requested_url": url,
                    "final_url": url,
                },
                "data": record_data(literal_citation=True),
            },
        )
        with patch.object(gen_ancestry, "cdp_up", side_effect=AssertionError("CDP called")):
            with self.assertRaises(gen_ancestry.CockpitError) as caught:
                self.draft()
        self.assertIn("digest mismatch", caught.exception.error)

    def test_pending_draft_is_rejected_by_evidence_validator(self) -> None:
        self.cache.write_record(literal_citation=True)
        record = self.draft()["draft"]
        fixture = EvidenceFixture()
        try:
            fixture.write([record])
            result = fixture.validate()
        finally:
            fixture.close()
        self.assertFalse(result.ok)
        self.assertTrue(
            any("privacy_review.status must be 'passed'" in error for error in result.errors),
            result.errors,
        )

    def test_root_wrapper_reads_cache_only(self) -> None:
        self.cache.write_record(literal_citation=True)
        env = {
            **os.environ,
            "GEN_ANCESTRY_UNSAFE_TEST": "1",
            "GEN_ANCESTRY_CACHE_DIR": str(self.cache.cache),
            "GEN_COCKPIT_DIR": str(self.cache.root / "subprocess-state"),
        }
        result = subprocess.run(
            [
                str(ROOT / "gen"),
                "evidence",
                "draft",
                "--from-cache",
                "record/6742/123",
                "--id",
                "ev.ancestry.test-record",
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "evidence.draft")


if __name__ == "__main__":
    unittest.main(verbosity=2)
