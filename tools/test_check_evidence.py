#!/usr/bin/env python3
"""Regression tests for the canonical evidence validator (stdlib only)."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from check_evidence import EXPECTED_SHARDS, ROOT, validate_repository


def ancestry_record_cache_key(collection: str = "6742", record_id: str = "1") -> str:
    raw = f"record|collection={collection}|id={record_id}"
    return "record-" + hashlib.sha1(raw.encode()).hexdigest()[:16]


def valid_record() -> dict:
    return {
        "id": "ev.test.record",
        "record_type": "census",
        "title": "Test census record",
        "repository": "Test archive",
        "citation": "Test archive, volume 1, page 2.",
        "accessed": "2026-07-09",
        "status": "found",
        "confidence": "high",
        "supports": ["case.01", "person.test"],
        "opposes": [],
        "person_refs": ["person.test"],
        "case_refs": ["case.01"],
        "privacy_review": {
            "status": "passed",
            "reviewed": "2026-07-09",
            "living_people": "excluded",
            "sensitive_identifiers": "excluded",
        },
        "acquisition": {
            "provider": "Test provider",
            "batch": "test-batch",
            "pull": "01",
            "local_dirs": ["research/pulls/test-batch/01-test"],
        },
        "source_urls": ["https://example.test/record/1"],
        "transcription": "A privacy-safe abstract.",
        "local_assets": [],
    }


class EvidenceFixture:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "research/evidence").mkdir(parents=True)
        (self.root / "research/people").mkdir(parents=True)
        (self.root / "research/cases").mkdir(parents=True)
        (self.root / "research/people/people.jsonl").write_text(
            json.dumps({"id": "person.test", "node_type": "person"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "research/cases/cases.jsonl").write_text(
            json.dumps({"id": "case.01", "node_type": "case"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "index.html").write_text(
            '<div id="person.test"></div><section id="case.01"></section>',
            encoding="utf-8",
        )
        (self.root / "ancestry_geospatial.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": []}),
            encoding="utf-8",
        )
        for shard in EXPECTED_SHARDS:
            (self.root / "research/evidence" / shard).write_text("", encoding="utf-8")

    def close(self) -> None:
        self._tmp.cleanup()

    def write(self, records: list[dict]) -> None:
        text = "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records)
        (self.root / "research/evidence/mundell.jsonl").write_text(text, encoding="utf-8")

    def validate(self, require_local_assets: bool = False):
        return validate_repository(
            root=self.root, require_local_assets=require_local_assets
        )


class EvidenceValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = EvidenceFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_error_contains(self, needle: str, result) -> None:
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            any(needle in error for error in result.errors),
            f"expected {needle!r} in {result.errors!r}",
        )

    def test_valid_minimal_store(self) -> None:
        self.fixture.write([valid_record()])
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.record_count, 1)
        self.assertEqual(result.pull_count, 1)

    def test_canonical_hyphenated_multisegment_person_id_is_accepted(self) -> None:
        person_id = "person.test-hyphen.extra"
        (self.fixture.root / "research/people/people.jsonl").write_text(
            json.dumps({"id": person_id, "node_type": "person"}) + "\n",
            encoding="utf-8",
        )
        record = valid_record()
        record["person_refs"] = [person_id]
        record["supports"] = ["case.01", person_id]
        self.fixture.write([record])
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)

    def test_duplicate_evidence_id_is_rejected(self) -> None:
        first = valid_record()
        second = copy.deepcopy(first)
        second["acquisition"]["pull"] = "02"
        self.fixture.write([first, second])
        self.assert_error_contains("duplicate evidence id", self.fixture.validate())

    def test_duplicate_logical_pull_is_rejected(self) -> None:
        first = valid_record()
        second = copy.deepcopy(first)
        second["id"] = "ev.test.second"
        self.fixture.write([first, second])
        self.assert_error_contains("duplicate logical pull", self.fixture.validate())

    def test_unknown_reference_is_rejected(self) -> None:
        record = valid_record()
        record["person_refs"] = ["person.missing"]
        record["supports"] = ["case.01", "person.missing"]
        self.fixture.write([record])
        self.assert_error_contains("unresolved person/case reference", self.fixture.validate())

    def test_html_and_geo_only_person_is_rejected(self) -> None:
        """Presentation data cannot create a person identity after cutover."""

        record = valid_record()
        record["person_refs"] = ["person.presentation_only"]
        record["supports"] = ["case.01", "person.presentation_only"]
        self.fixture.write([record])
        (self.fixture.root / "index.html").write_text(
            '<div id="person.presentation_only"></div><section id="case.01"></section>',
            encoding="utf-8",
        )
        (self.fixture.root / "ancestry_geospatial.geojson").write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "id": "event.presentation-only",
                            "properties": {"person_id": "person.presentation_only"},
                            "geometry": None,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.assert_error_contains(
            "unresolved person/case reference", self.fixture.validate()
        )

    def test_support_endpoint_must_be_in_subject_refs(self) -> None:
        record = valid_record()
        record["person_refs"] = []
        self.fixture.write([record])
        self.assert_error_contains("absent from person_refs/case_refs", self.fixture.validate())

    def test_unknown_schema_field_is_rejected(self) -> None:
        record = valid_record()
        record["legacy_citation"] = "old shape"
        self.fixture.write([record])
        self.assert_error_contains("unknown fields", self.fixture.validate())

    def test_privacy_attestation_is_required(self) -> None:
        record = valid_record()
        record["privacy_review"]["living_people"] = "included"
        self.fixture.write([record])
        self.assert_error_contains(
            "privacy_review.living_people must be 'excluded'", self.fixture.validate()
        )

    def test_formatted_ssn_is_rejected(self) -> None:
        record = valid_record()
        record["transcription"] = "Restricted identifier 123-45-6789."
        self.fixture.write([record])
        self.assert_error_contains("Social Security number", self.fixture.validate())

    def test_labelled_compact_ssn_is_rejected(self) -> None:
        record = valid_record()
        record["citation"] = "Social Security number: 123456789"
        self.fixture.write([record])
        self.assert_error_contains("Social Security number", self.fixture.validate())

    def test_missing_private_asset_is_optional_unless_requested(self) -> None:
        record = valid_record()
        record["local_assets"] = [
            {
                "path": "research/pulls/test-batch/01-test/record.png",
                "role": "record capture",
                "sha256": "0" * 64,
            }
        ]
        self.fixture.write([record])
        self.assertTrue(self.fixture.validate().ok)
        self.assert_error_contains(
            "required local", self.fixture.validate(require_local_assets=True)
        )

    def test_open_web_acquisition_may_have_no_local_directory(self) -> None:
        record = valid_record()
        record["acquisition"]["local_dirs"] = []
        self.fixture.write([record])
        self.assertTrue(self.fixture.validate().ok)

    def test_valid_record_cache_provenance_is_accepted(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        record["source_urls"] = [
            "https://www.ancestry.com/search/collections/6742/records/1"
        ]
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key(),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": "https://www.ancestry.com/search/collections/6742/records/1",
            "final_url": "https://www.ancestry.com/search/collections/6742/records/1",
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assertTrue(self.fixture.validate().ok, self.fixture.validate().errors)

    def test_cache_provenance_rejects_non_record_key(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": "search-0123456789abcdef",
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": "https://www.ancestry.com/search/collections/6742/?name=Test_Person",
            "final_url": "https://www.ancestry.com/search/collections/6742?name=Test_Person",
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assert_error_contains(
            "must be a record cache key", self.fixture.validate()
        )

    def test_cache_provenance_rejects_non_ancestry_urls(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key(),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": "https://example.test/search/collections/6742/records/1",
            "final_url": "https://example.test/search/collections/6742/records/1",
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assert_error_contains(
            "must be an Ancestry HTTPS URL", self.fixture.validate()
        )

    def test_cache_provenance_rejects_malformed_url_without_crashing(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        malformed = "https://[bad/search/collections/6742/records/1"
        record["source_urls"] = [malformed]
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key(),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": malformed,
            "final_url": malformed,
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assert_error_contains("must be a valid URL", self.fixture.validate())

    def test_cache_provenance_final_url_must_be_a_source_url(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key(),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": "https://www.ancestry.com/search/collections/6742/records/1",
            "final_url": "https://www.ancestry.com/search/collections/6742/records/1",
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assert_error_contains(
            "final_url must appear in source_urls", self.fixture.validate()
        )

    def test_cache_provenance_accepts_explicit_legacy_url_gap(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        record["source_urls"] = []
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key(),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": None,
            "final_url": None,
            "url_gap": "Legacy acquisition did not retain URLs; refresh required.",
        }
        self.fixture.write([record])
        self.assertTrue(self.fixture.validate().ok, self.fixture.validate().errors)

    def test_cache_provenance_rejects_missing_urls_without_gap(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        record["source_urls"] = []
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key(),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": None,
            "final_url": None,
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assert_error_contains(
            "url_gap must explain missing acquisition URLs", self.fixture.validate()
        )

    def test_cache_provenance_key_must_match_record_address(self) -> None:
        record = valid_record()
        record["acquisition"]["provider"] = "Ancestry"
        url = "https://www.ancestry.com/search/collections/6742/records/1"
        record["source_urls"] = [url]
        record["cache_provenance"] = {
            "provider": "Ancestry",
            "cache_key": ancestry_record_cache_key("6742", "2"),
            "cache_schema": "gen.ancestry.cache",
            "cache_version": 3,
            "data_sha256": "1" * 64,
            "fetched_at": "2026-07-09T20:48:33Z",
            "record_address": "record/6742/1",
            "requested_url": url,
            "final_url": url,
            "url_gap": None,
        }
        self.fixture.write([record])
        self.assert_error_contains(
            "cache_key does not match record_address", self.fixture.validate()
        )

    def test_present_asset_checksum_is_verified(self) -> None:
        asset = self.fixture.root / "research/pulls/test-batch/01-test/record.png"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"private test image")
        record = valid_record()
        record["local_assets"] = [
            {
                "path": "research/pulls/test-batch/01-test/record.png",
                "role": "record capture",
                "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
            }
        ]
        self.fixture.write([record])
        self.assertTrue(self.fixture.validate(require_local_assets=True).ok)
        record["local_assets"][0]["sha256"] = "0" * 64
        self.fixture.write([record])
        self.assert_error_contains("sha256 mismatch", self.fixture.validate())

    def test_unsafe_asset_path_is_rejected(self) -> None:
        record = valid_record()
        record["local_assets"] = [
            {"path": "research/pulls/../secret.png", "role": "bad path"}
        ]
        self.fixture.write([record])
        self.assert_error_contains("normalized repository-relative path", self.fixture.validate())

    def test_record_card_requires_evidence_id(self) -> None:
        self.fixture.write([valid_record()])
        (self.fixture.root / "index.html").write_text(
            '<div id="person.test"></div><section id="case.01"></section>'
            '<figure class="record-card"></figure>',
            encoding="utf-8",
        )
        self.assert_error_contains("missing data-evidence-id", self.fixture.validate())

    def test_record_card_evidence_id_must_resolve(self) -> None:
        self.fixture.write([valid_record()])
        (self.fixture.root / "index.html").write_text(
            '<div id="person.test"></div><section id="case.01"></section>'
            '<figure class="record-card" data-evidence-id="ev.test.missing"></figure>',
            encoding="utf-8",
        )
        self.assert_error_contains("unknown evidence id", self.fixture.validate())


class MigratedEvidenceRegressionTests(unittest.TestCase):
    def test_initial_migration_preserves_first_23_logical_pulls(self) -> None:
        result = validate_repository(root=ROOT)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.pull_count, result.record_count)
        records = []
        for path in sorted((ROOT / "research/evidence").glob("*.jsonl")):
            records.extend(
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line
            )
        ancestry_batch = [
            record
            for record in records
            if record["acquisition"]["batch"] == "ancestry-2026-07"
        ]
        migrated_pulls = {
            record["acquisition"]["pull"]
            for record in ancestry_batch
            if 1 <= int(record["acquisition"]["pull"]) <= 23
        }
        self.assertEqual(migrated_pulls, {f"{number:02d}" for number in range(1, 24)})

    def test_duplicate_pull_01_is_one_evidence_record(self) -> None:
        records = []
        for path in sorted((ROOT / "research/evidence").glob("*.jsonl")):
            records.extend(
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line
            )
        pull_01 = [
            record
            for record in records
            if record["acquisition"]["batch"] == "ancestry-2026-07"
            and record["acquisition"]["pull"] == "01"
        ]
        self.assertEqual(len(pull_01), 1)
        self.assertEqual(pull_01[0]["id"], "ev.ancestry.1910-zodrow")
        self.assertEqual(len(pull_01[0]["acquisition"]["local_dirs"]), 2)

    def test_public_record_cards_point_to_canonical_evidence(self) -> None:
        from check_evidence import RecordCardParser

        parser = RecordCardParser()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(
            set(parser.cards),
            {
                "ev.ancestry.1910-rust",
                "ev.ancestry.1910-zodrow",
                "ev.ancestry.1939-mundell-divorce",
                "ev.ancestry.1940-adolph-mundell",
            },
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
