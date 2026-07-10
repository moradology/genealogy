#!/usr/bin/env python3
"""Isolated mutation tests for the canonical family-core validator."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from check_family_core import ROOT, validate_repository


def person(
    person_id: str,
    display_name: str,
    *,
    role: str = "ancestor",
    branches: list[str] | None = None,
    public_anchor: str | None = None,
) -> dict:
    return {
        "id": person_id,
        "node_type": "person",
        "display_name": display_name,
        "index_names": [display_name],
        "name_variants": [],
        "branches": branches or ["zimmerman"],
        "role": role,
        "confidence": "documented",
        "privacy": "public_deceased",
        "public_anchor": public_anchor,
    }


def parent_relationship() -> dict:
    return {
        "id": "relationship.parent-anchor",
        "node_type": "relationship",
        "relationship_type": "parent_of",
        "parent_role": "father",
        "person_a": "person.alex-senior",
        "person_b": "person.avery-anchor",
        "status": "accepted",
        "confidence": "documented",
        "branches": ["zimmerman"],
        "evidence_refs": ["ev.test.record"],
        "source_refs": [],
        "case_refs": [],
        "provenance_note": "The test record names Alex as Avery's parent.",
    }


def open_gap() -> dict:
    return {
        "id": "gap.avery-mother",
        "node_type": "gap",
        "gap_type": "parentage",
        "label": "Avery's mother",
        "subject_persons": ["person.avery-anchor"],
        "candidate_persons": ["person.casey-candidate"],
        "open_roles": ["mother"],
        "branches": ["zimmerman"],
        "case_refs": ["case.01"],
        "evidence_refs": [],
        "source_refs": ["src.test.record"],
        "public_anchor": "gap.avery-mother",
        "status": "open",
        "resolution_note": "",
        "resolved_on": None,
        "owner_follow_up_required": False,
        "pedigree": {"Z": [3], "M": [], "D": [], "C": []},
    }


class FamilyCoreFixture:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        (self.root / "research/people").mkdir(parents=True)
        (self.root / "research/evidence").mkdir(parents=True)
        (self.root / "research/sources").mkdir(parents=True)
        (self.root / "research/cases").mkdir(parents=True)
        (self.root / "research/evidence/test.jsonl").write_text(
            json.dumps({"id": "ev.test.record"}) + "\n", encoding="utf-8"
        )
        (self.root / "research/sources/sources.jsonl").write_text(
            json.dumps({"id": "src.test.record"}) + "\n", encoding="utf-8"
        )
        (self.root / "research/cases/cases.jsonl").write_text(
            json.dumps({"id": "case.01", "status": "open"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "index.html").write_text(
            '<div id="person.avery-anchor"></div>'
            '<div id="gap.avery-mother"></div>',
            encoding="utf-8",
        )
        self.people = [
            person(
                "person.avery-anchor",
                "Avery Anchor",
                role="anchor",
                public_anchor="person.avery-anchor",
            ),
            person("person.alex-senior", "Alex Senior"),
            person(
                "person.casey-candidate",
                "Casey Candidate",
                role="candidate",
            ),
            person(
                "person.morgan-mundell",
                "Morgan Mundell",
                role="anchor",
                branches=["mundell"],
            ),
            person(
                "person.dana-dible",
                "Dana Dible",
                role="anchor",
                branches=["dible"],
            ),
            person(
                "person.connie-connelly",
                "Connie Connelly",
                role="anchor",
                branches=["connelly"],
            ),
        ]
        self.rows = [parent_relationship(), open_gap()]
        self.write()

    def close(self) -> None:
        self._temporary.cleanup()

    @staticmethod
    def _jsonl(rows: list[dict]) -> str:
        return "".join(
            json.dumps(row, separators=(",", ":")) + "\n" for row in rows
        )

    def write(self) -> None:
        (self.root / "research/people/people.jsonl").write_text(
            self._jsonl(self.people), encoding="utf-8"
        )
        (self.root / "research/people/relationships.jsonl").write_text(
            self._jsonl(self.rows), encoding="utf-8"
        )

    def validate(self):
        self.write()
        return validate_repository(root=self.root)


class FamilyCoreValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = FamilyCoreFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_error_contains(self, needle: str) -> None:
        result = self.fixture.validate()
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            any(needle in error for error in result.errors),
            f"expected {needle!r} in {result.errors!r}",
        )

    def test_valid_minimal_family_core(self) -> None:
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.person_count, 6)
        self.assertEqual(result.relationship_count, 1)
        self.assertEqual(result.gap_count, 1)

    def test_duplicate_global_id_is_rejected(self) -> None:
        duplicate = copy.deepcopy(self.fixture.people[0])
        self.fixture.people.append(duplicate)
        self.assert_error_contains("duplicate global id")

    def test_synthetic_person_row_is_rejected(self) -> None:
        fake = self.fixture.people[1]
        fake["id"] = "person.avery-parents"
        fake["display_name"] = "Parents of Avery"
        fake["index_names"] = ["Parents of Avery"]
        self.fixture.rows[0]["person_a"] = fake["id"]
        self.assert_error_contains("one actual individual")

    def test_unresolved_relationship_endpoint_is_rejected(self) -> None:
        self.fixture.rows[0]["person_a"] = "person.missing"
        self.assert_error_contains("unresolved person endpoint")

    def test_unresolved_typed_reference_is_rejected(self) -> None:
        self.fixture.rows[0]["source_refs"] = ["src.missing"]
        self.assert_error_contains("unresolved ref")

    def test_relationship_without_support_reference_is_rejected(self) -> None:
        self.fixture.rows[0]["evidence_refs"] = []
        self.assert_error_contains("every relationship must cite")

    def test_self_relationship_is_rejected(self) -> None:
        self.fixture.rows[0]["person_a"] = "person.avery-anchor"
        self.assert_error_contains("endpoints must be distinct")

    def test_duplicate_spouse_pair_is_rejected_in_reverse_order(self) -> None:
        first = parent_relationship()
        first.update(
            {
                "id": "relationship.spouse-one",
                "relationship_type": "spouse_of",
                "parent_role": None,
                "person_a": "person.alex-senior",
                "person_b": "person.casey-candidate",
                "status": "hypothesis",
                "confidence": "lead",
                "evidence_refs": [],
                "case_refs": ["case.01"],
            }
        )
        second = copy.deepcopy(first)
        second["id"] = "relationship.spouse-two"
        second["person_a"], second["person_b"] = (
            second["person_b"],
            second["person_a"],
        )
        self.fixture.rows.extend([first, second])
        self.assert_error_contains("duplicate spouse_of pair")

    def test_accepted_parent_cycle_is_rejected(self) -> None:
        reverse = parent_relationship()
        reverse["id"] = "relationship.anchor-parent"
        reverse["person_a"] = "person.avery-anchor"
        reverse["person_b"] = "person.alex-senior"
        self.fixture.rows.append(reverse)
        self.assert_error_contains("contains a cycle")

    def test_rejected_parent_is_retained_but_excluded_from_cycles(self) -> None:
        reverse = parent_relationship()
        reverse["id"] = "relationship.anchor-parent-rejected"
        reverse["person_a"] = "person.avery-anchor"
        reverse["person_b"] = "person.alex-senior"
        reverse["status"] = "rejected"
        reverse["provenance_note"] += " Rejected on 2026-07-09: test conflict."
        self.fixture.rows.append(reverse)
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.relationship_count, 2)

    def test_disconnected_hypothesis_parent_cycle_is_rejected(self) -> None:
        self.fixture.people.extend(
            [
                person(
                    "person.loop-one",
                    "Loop One",
                    role="candidate",
                    branches=["mundell"],
                ),
                person(
                    "person.loop-two",
                    "Loop Two",
                    role="candidate",
                    branches=["mundell"],
                ),
            ]
        )
        first = parent_relationship()
        first.update(
            {
                "id": "relationship.loop-one-to-loop-two",
                "person_a": "person.loop-one",
                "person_b": "person.loop-two",
                "status": "hypothesis",
                "confidence": "lead",
                "branches": ["mundell"],
            }
        )
        second = copy.deepcopy(first)
        second["id"] = "relationship.loop-two-to-loop-one"
        second["person_a"], second["person_b"] = (
            second["person_b"],
            second["person_a"],
        )
        self.fixture.rows.extend([first, second])
        self.assert_error_contains("contains a cycle")

    def test_parent_role_semantics_are_required(self) -> None:
        self.fixture.rows[0]["parent_role"] = None
        self.assert_error_contains("parent_role must be 'father' or 'mother'")

        self.fixture.rows[0]["relationship_type"] = "spouse_of"
        self.fixture.rows[0]["parent_role"] = "father"
        self.assert_error_contains("parent_role must be null for spouse_of")

    def test_only_one_accepted_parent_per_child_role_is_allowed(self) -> None:
        competing = parent_relationship()
        competing["id"] = "relationship.competing-father"
        competing["person_a"] = "person.casey-candidate"
        self.fixture.rows.append(competing)
        self.assert_error_contains("more than one accepted father")

    def test_multiple_hypothesis_parents_for_one_role_are_allowed(self) -> None:
        self.fixture.rows[0]["status"] = "hypothesis"
        self.fixture.rows[0]["confidence"] = "lead"
        alternative = parent_relationship()
        alternative["id"] = "relationship.alternative-father"
        alternative["person_a"] = "person.casey-candidate"
        alternative["status"] = "hypothesis"
        alternative["confidence"] = "lead"
        self.fixture.rows.append(alternative)
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)

    def test_each_branch_requires_one_distinct_anchor(self) -> None:
        self.fixture.people[-1]["role"] = "ancestor"
        self.assert_error_contains("must have exactly one anchor")

    def test_bad_gap_is_rejected(self) -> None:
        gap = self.fixture.rows[1]
        gap["candidate_persons"] = ["person.avery-anchor"]
        gap["case_refs"] = []
        self.assert_error_contains("must be disjoint")
        result = self.fixture.validate()
        self.assertTrue(
            any("case_refs must not be empty" in error for error in result.errors),
            result.errors,
        )

    def test_duplicate_gap_pedigree_slot_is_rejected(self) -> None:
        duplicate = copy.deepcopy(self.fixture.rows[1])
        duplicate["id"] = "gap.avery-father"
        duplicate["label"] = "Avery's father"
        duplicate["open_roles"] = ["father"]
        duplicate["public_anchor"] = None
        self.fixture.rows.append(duplicate)
        self.assert_error_contains("pedigree slot Z-3")

    def test_resolved_gap_requires_durable_resolution_state(self) -> None:
        gap = self.fixture.rows[1]
        gap["status"] = "resolved"
        gap["candidate_persons"] = []
        gap["open_roles"] = []
        gap["pedigree"] = {"Z": [], "M": [], "D": [], "C": []}
        gap["resolution_note"] = "The cited record identifies the remaining parent."
        gap["resolved_on"] = "2026-07-09"
        gap["owner_follow_up_required"] = True
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)

        gap["resolved_on"] = None
        self.assert_error_contains("resolved gap resolved_on is required")

    def test_unknown_schema_field_is_rejected(self) -> None:
        self.fixture.people[0]["legacy_id"] = "old-shape"
        self.assert_error_contains("unknown fields")

    def test_public_anchor_must_exist_in_projection(self) -> None:
        self.fixture.people[0]["public_anchor"] = "person.absent"
        self.assert_error_contains("absent from index.html")

    def test_lists_must_be_sorted_and_unique(self) -> None:
        self.fixture.people[0]["name_variants"] = ["Zed", "Alpha", "Alpha"]
        result = self.fixture.validate()
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(any("duplicate values" in error for error in result.errors))
        self.assertTrue(any("must be sorted" in error for error in result.errors))


class CanonicalFamilyRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = [
            json.loads(line)
            for line in (ROOT / "research/people/relationships.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        ]
        cls.by_id = {row["id"]: row for row in cls.rows}

    def test_older_rust_parent_edge_is_documented(self) -> None:
        edge = self.by_id["relationship.parent.rust_jan_aissen-to-rust_aisse_jansen"]
        self.assertEqual(edge["person_a"], "person.rust.jan_aissen")
        self.assertEqual(edge["person_b"], "person.rust.aisse_jansen")
        self.assertEqual(edge["parent_role"], "father")
        self.assertEqual((edge["status"], edge["confidence"]), ("accepted", "documented"))
        self.assertIn("ev.ancestry.1830-1841-rust-parish", edge["evidence_refs"])

    def test_rust_wives_and_proposed_parents_remain_distinct(self) -> None:
        frauke_spouse = self.by_id[
            "relationship.spouse.rust_frauke_folkerts_everwyn-to-rust_john_aissen"
        ]
        nomdje_spouse = self.by_id[
            "relationship.spouse.nomdje_n_rust-to-rust_john_aissen"
        ]
        self.assertEqual(frauke_spouse["status"], "accepted")
        self.assertEqual(nomdje_spouse["status"], "accepted")
        proposed = {
            (row.get("person_a"), row.get("parent_role"), row.get("status"))
            for row in self.rows
            if row.get("relationship_type") == "parent_of"
            and row.get("person_b") == "person.rust.john_f"
        }
        self.assertEqual(
            proposed,
            {
                ("person.rust.john_aissen", "father", "hypothesis"),
                ("person.rust.frauke_folkerts_everwyn", "mother", "hypothesis"),
            },
        )

    def test_full_ford_hypothesis_set_is_explicit(self) -> None:
        candidates = {
            (row.get("person_a"), row.get("parent_role"), row.get("status"))
            for row in self.rows
            if row.get("relationship_type") == "parent_of"
            and row.get("person_b") == "person.ford.john_laborn"
        }
        self.assertEqual(
            candidates,
            {
                ("person.davis.aritta", "mother", "hypothesis"),
                ("person.ford.john_laborn_sr", "father", "hypothesis"),
                ("person.ford.levi", "father", "hypothesis"),
            },
        )
        gap = self.by_id["gap.ford.john_laborn.parentage"]
        self.assertEqual(
            gap["candidate_persons"],
            [
                "person.davis.aritta",
                "person.ford.john_laborn_sr",
                "person.ford.levi",
            ],
        )


def display_block(**overrides) -> dict:
    block = {
        "identity": "Avery anchor; spouse of {{link:#person.alex-senior|Alex}}.",
        "details": ("Documented at the county seat.{{cite:src.test.record}} "
                    "See {{case:case.01}} and {{url:https://example.org/x|the notice}}."),
    }
    block.update(overrides)
    return block


class DisplayBlockTests(unittest.TestCase):
    """The optional display block: person/gap prose fields for the generated
    family cards. Allowed only on card-owner rows; plain-unicode prose with
    the {{...}} token grammar; cameo and record-card shapes enforced."""

    def setUp(self) -> None:
        self.fixture = FamilyCoreFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_error_contains(self, needle: str) -> None:
        result = self.fixture.validate()
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            any(needle in error for error in result.errors),
            f"expected {needle!r} in {result.errors!r}",
        )

    def test_full_display_block_is_accepted(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            card_name="Avery A. Anchor",
            vitals="b. 1900 - m. 1922{{vs}}1923 - d. 1980",
            cameos=[{"src": "images/people/avery.jpg", "alt": "Avery at the farm",
                     "width": 137, "height": 157,
                     "credit_url": "https://example.org/avery",
                     "credit_label": "Photo: county archive"}],
            record_cards=["ev.test.record"],
        )
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)

    def test_gap_display_with_alias_anchors_is_accepted(self) -> None:
        self.fixture.rows[1]["display"] = display_block(
            alias_anchors=["person.casey-candidate"])
        result = self.fixture.validate()
        self.assertTrue(result.ok, result.errors)

    def test_display_on_non_owner_row_is_rejected(self) -> None:
        self.fixture.people[1]["public_anchor"] = "person.avery-anchor"
        self.fixture.people[1]["display"] = display_block()
        self.assert_error_contains("card-owner")

    def test_unknown_display_field_is_rejected(self) -> None:
        self.fixture.people[0]["display"] = display_block(prose="nope")
        self.assert_error_contains("unknown display fields")

    def test_missing_identity_is_rejected(self) -> None:
        block = display_block()
        del block["identity"]
        self.fixture.people[0]["display"] = block
        self.assert_error_contains("missing display fields")

    def test_raw_html_in_display_prose_is_rejected(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            details="a <b>bold</b> claim")
        self.assert_error_contains("raw HTML")

    def test_entities_in_display_prose_are_rejected(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            details="a &ndash; b")
        self.assert_error_contains("plain unicode")

    def test_malformed_tokens_are_rejected(self) -> None:
        for bad in ("{{cite:not-a-source}}", "{{teleport:x}}",
                    "{{link:#person.alex-senior}}", "{{cite:src.x} }",
                    "stray }} closer", "open {{ brace"):
            self.fixture.people[0]["display"] = display_block(details=bad)
            self.assert_error_contains("token")

    def test_cameo_shape_is_enforced(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            cameos=[{"src": "images/people/avery.jpg", "alt": "Avery",
                     "width": 137, "credit_url": "https://example.org",
                     "credit_label": "Photo"}])
        self.assert_error_contains("cameo")

    def test_record_card_refs_must_be_evidence_ids(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            record_cards=["source.notes"])
        self.assert_error_contains("record_cards")

    def test_alias_anchor_must_resolve(self) -> None:
        self.fixture.rows[1]["display"] = display_block(
            alias_anchors=["person.nobody"])
        self.assert_error_contains("alias_anchors")

    def test_alias_anchors_are_gap_only(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            alias_anchors=["person.casey-candidate"])
        self.assert_error_contains("unknown display fields")

    def test_cite_token_must_resolve(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            details="Claimed.{{cite:src.missing.deadbeef}}")
        self.assert_error_contains("cites unknown source")

    def test_case_token_must_resolve(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            details="See {{case:case.99}}.")
        self.assert_error_contains("unknown case")

    def test_link_token_must_resolve(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            identity="Spouse of {{link:#person.nobody|Nobody}}.")
        self.assert_error_contains("links unknown anchor")

    def test_plain_override_fields_reject_tokens(self) -> None:
        self.fixture.people[0]["display"] = display_block(
            card_name="A {{vs}} B")
        self.assert_error_contains("must not carry tokens")

    def test_whitelists_stay_in_parity_with_projection(self) -> None:
        import build_people_index
        import check_family_core
        self.assertEqual(check_family_core.PERSON_FIELDS,
                         build_people_index.PERSON_FIELDS)
        self.assertEqual(check_family_core.GAP_FIELDS,
                         build_people_index.GAP_FIELDS)
        self.assertEqual(check_family_core.RELATIONSHIP_FIELDS,
                         build_people_index.RELATIONSHIP_FIELDS)


if __name__ == "__main__":
    unittest.main()
