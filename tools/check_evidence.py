#!/usr/bin/env python3
"""Validate the canonical JSONL evidence store.

The evidence files are the durable text truth. This checker intentionally has no
reader for the older pull-note or HTML-ledger shapes: malformed or legacy records
must be migrated, not silently accepted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = Path("research/evidence")
EXPECTED_SHARDS = frozenset(
    {"connelly.jsonl", "dible.jsonl", "mundell.jsonl", "zimmerman.jsonl"}
)

REQUIRED_FIELDS = frozenset(
    {
        "id",
        "record_type",
        "title",
        "repository",
        "citation",
        "accessed",
        "status",
        "confidence",
        "supports",
        "opposes",
        "person_refs",
        "case_refs",
        "privacy_review",
        "acquisition",
        "source_urls",
        "transcription",
        "local_assets",
    }
)
OPTIONAL_FIELDS = frozenset({"citation_gap", "cache_provenance", "display"})
DISPLAY_ENTITY_RE = re.compile(r"&#?[a-zA-Z0-9]+;")
RECORD_TYPES = frozenset(
    {
        "census",
        "church_register",
        "death_index",
        "divorce",
        "marriage",
        "obituary_index",
        "probate",
        "record_bundle",
        "search_log",
    }
)
STATUSES = frozenset({"found", "not_found", "partial"})
CONFIDENCES = frozenset({"high", "medium", "low", "not_applicable"})

EVIDENCE_ID_RE = re.compile(r"ev\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
PERSON_ID_RE = re.compile(r"person\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
CASE_ID_RE = re.compile(r"case\.\d{2}\Z")
PULL_RE = re.compile(r"\d{2}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
URL_RE = re.compile(r"https?://\S+\Z")
CACHE_KEY_RE = re.compile(r"record-[0-9a-f]{16}\Z")
CACHE_RECORD_ADDRESS_RE = re.compile(r"record/(\d+)/(\d+)\Z")
CACHE_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z"
)
# Avoid matching ordinary nine-digit collection/record ids. Compact digits are
# sensitive only when explicitly labelled as a Social Security number.
FORMATTED_SSN_RE = re.compile(r"(?<!\d)\d{3}[- ]\d{2}[- ]\d{4}(?!\d)")
LABELLED_SSN_RE = re.compile(
    r"\b(?:ssn|social security(?: number)?)\D{0,24}\d{9}\b", re.IGNORECASE
)


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    record_count: int
    pull_count: int

    @property
    def ok(self) -> bool:
        return not self.errors


class RecordCardParser(HTMLParser):
    """Collect canonical evidence ids from public record-card projections."""

    def __init__(self) -> None:
        super().__init__()
        self.cards: list[str | None] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag != "figure":
            return
        values = dict(attrs)
        if "record-card" in (values.get("class") or "").split():
            self.cards.append(values.get("data-evidence-id"))


def collect_record_card_refs(root: Path, errors: list[str]) -> list[str]:
    """Require each visible record card to name one canonical evidence record."""

    html_path = root / "index.html"
    if not html_path.is_file():
        return []
    parser = RecordCardParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    refs: list[str] = []
    for position, ref in enumerate(parser.cards, 1):
        if not ref:
            errors.append(
                f"index.html record card {position} is missing data-evidence-id"
            )
        elif not EVIDENCE_ID_RE.fullmatch(ref):
            errors.append(
                f"index.html record card {position} has invalid evidence id {ref!r}"
            )
        else:
            refs.append(ref)
    return refs


def _canonical_ids(
    path: Path,
    label: str,
    expected_node_type: str,
    grammar: re.Pattern[str],
    errors: list[str],
) -> set[str]:
    """Read one canonical ID store without consulting a presentation."""

    ids: set[str] = set()
    if not path.is_file():
        errors.append(f"missing canonical {label} store: {path}")
        return ids
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        where = f"{path}:{line_number}"
        if not line.strip():
            errors.append(f"{where}: blank lines are not allowed in canonical JSONL")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{where}: invalid {label} JSON: {exc.msg} at column {exc.colno}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{where}: canonical {label} record must be an object")
            continue
        value = record.get("id")
        if record.get("node_type") != expected_node_type:
            errors.append(
                f"{where}: canonical {label} node_type must be {expected_node_type!r}"
            )
            continue
        if not isinstance(value, str) or grammar.fullmatch(value) is None:
            errors.append(f"{where}: invalid canonical {label} id {value!r}")
            continue
        if value in ids:
            errors.append(f"{where}: duplicate canonical {label} id {value!r}")
            continue
        ids.add(value)
    return ids


def collect_reference_universe(root: Path, errors: list[str]) -> set[str]:
    """Collect person and case ids only from their canonical JSONL stores."""

    people = _canonical_ids(
        root / "research/people/people.jsonl",
        "person",
        "person",
        PERSON_ID_RE,
        errors,
    )
    cases = _canonical_ids(
        root / "research/cases/cases.jsonl",
        "case",
        "case",
        CASE_ID_RE,
        errors,
    )
    return people | cases


def _nonempty_string(record: dict[str, Any], field: str, where: str, errors: list[str]) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: {field} must be a non-empty string")


def _unique_string_list(
    record: dict[str, Any], field: str, where: str, errors: list[str]
) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{where}: {field} must be a list of strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{where}: {field} contains duplicate values")
    return value


def _safe_pull_path(value: Any, field: str, where: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{where}: {field} must be a non-empty path string")
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        errors.append(f"{where}: {field} must be a normalized repository-relative path")
        return None
    if path.parts[:2] != ("research", "pulls"):
        errors.append(f"{where}: {field} must live under research/pulls/")
        return None
    return value


def _validate_privacy(record: dict[str, Any], where: str, errors: list[str]) -> None:
    review = record.get("privacy_review")
    expected_keys = {
        "status",
        "reviewed",
        "living_people",
        "sensitive_identifiers",
    }
    if not isinstance(review, dict):
        errors.append(f"{where}: privacy_review must be an object")
        return
    if set(review) != expected_keys:
        errors.append(
            f"{where}: privacy_review fields must be exactly {sorted(expected_keys)}"
        )
        return
    if review["status"] != "passed":
        errors.append(f"{where}: privacy_review.status must be 'passed'")
    if review["living_people"] != "excluded":
        errors.append(f"{where}: privacy_review.living_people must be 'excluded'")
    if review["sensitive_identifiers"] != "excluded":
        errors.append(
            f"{where}: privacy_review.sensitive_identifiers must be 'excluded'"
        )
    try:
        dt.date.fromisoformat(review["reviewed"])
    except (TypeError, ValueError):
        errors.append(f"{where}: privacy_review.reviewed must be an ISO date")

    # Scan only prose-bearing fields. URLs, ids, and SHA-256 hashes legitimately
    # contain long digit runs and are not transcriptions of source content.
    prose_fields = ["title", "repository", "citation", "citation_gap", "transcription"]
    prose = "\n".join(
        str(record[field]) for field in prose_fields if record.get(field) is not None
    )
    assets = record.get("local_assets")
    if isinstance(assets, list):
        prose += "\n" + "\n".join(
            asset.get("role", "") for asset in assets if isinstance(asset, dict)
        )
    if FORMATTED_SSN_RE.search(prose) or LABELLED_SSN_RE.search(prose):
        errors.append(f"{where}: possible full Social Security number in evidence prose")


def _validate_acquisition(
    record: dict[str, Any],
    where: str,
    root: Path,
    require_local_assets: bool,
    errors: list[str],
) -> tuple[str, str] | None:
    acquisition = record.get("acquisition")
    expected_keys = {"provider", "batch", "pull", "local_dirs"}
    if not isinstance(acquisition, dict):
        errors.append(f"{where}: acquisition must be an object")
        return None
    if set(acquisition) != expected_keys:
        errors.append(f"{where}: acquisition fields must be exactly {sorted(expected_keys)}")
        return None
    for field in ("provider", "batch", "pull"):
        if not isinstance(acquisition[field], str) or not acquisition[field]:
            errors.append(f"{where}: acquisition.{field} must be a non-empty string")
    if isinstance(acquisition.get("pull"), str) and not PULL_RE.fullmatch(
        acquisition["pull"]
    ):
        errors.append(f"{where}: acquisition.pull must be a two-digit string")

    local_dirs = acquisition.get("local_dirs")
    normalized_dirs: list[str] = []
    if not isinstance(local_dirs, list):
        errors.append(f"{where}: acquisition.local_dirs must be a list")
    else:
        if len(local_dirs) != len(set(item for item in local_dirs if isinstance(item, str))):
            errors.append(f"{where}: acquisition.local_dirs contains duplicate values")
        for index, value in enumerate(local_dirs):
            path = _safe_pull_path(
                value, f"acquisition.local_dirs[{index}]", where, errors
            )
            if path is not None:
                normalized_dirs.append(path)
                if require_local_assets and not (root / path).is_dir():
                    errors.append(f"{where}: required local pull directory is missing: {path}")

    assets = record.get("local_assets")
    if not isinstance(assets, list):
        errors.append(f"{where}: local_assets must be a list")
    else:
        seen_paths: set[str] = set()
        for index, asset in enumerate(assets):
            asset_where = f"{where}: local_assets[{index}]"
            if not isinstance(asset, dict):
                errors.append(f"{asset_where} must be an object")
                continue
            allowed = {"path", "role", "sha256"}
            if not {"path", "role"}.issubset(asset) or set(asset) - allowed:
                errors.append(
                    f"{asset_where} fields must be path, role, and optional sha256"
                )
                continue
            path = _safe_pull_path(asset.get("path"), "path", asset_where, errors)
            if path is None:
                continue
            if path in seen_paths:
                errors.append(f"{where}: duplicate local asset path {path}")
            seen_paths.add(path)
            if normalized_dirs and not any(
                PurePosixPath(local_dir) in PurePosixPath(path).parents
                for local_dir in normalized_dirs
            ):
                errors.append(
                    f"{asset_where}: path is outside acquisition.local_dirs: {path}"
                )
            if not isinstance(asset.get("role"), str) or not asset["role"].strip():
                errors.append(f"{asset_where}: role must be a non-empty string")
            checksum = asset.get("sha256")
            if checksum is not None and (
                not isinstance(checksum, str) or not SHA256_RE.fullmatch(checksum)
            ):
                errors.append(f"{asset_where}: sha256 must be 64 lowercase hex digits")

            local_path = root / path
            if not local_path.is_file():
                if require_local_assets:
                    errors.append(f"{asset_where}: required local asset is missing: {path}")
            elif isinstance(checksum, str) and SHA256_RE.fullmatch(checksum):
                actual = hashlib.sha256(local_path.read_bytes()).hexdigest()
                if actual != checksum:
                    errors.append(
                        f"{asset_where}: sha256 mismatch for {path}: expected {checksum}, got {actual}"
                    )

    batch = acquisition.get("batch")
    pull = acquisition.get("pull")
    if isinstance(batch, str) and isinstance(pull, str):
        return batch, pull
    return None


def _display_text(value: Any, spot: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{spot} must be a non-empty string")
        return
    if "<" in value:
        errors.append(f"{spot} must not contain raw HTML ('<')")
    if DISPLAY_ENTITY_RE.search(value):
        errors.append(f"{spot} must hold plain unicode, not HTML entities")


def _validate_display_block(
    record: dict[str, Any], where: str, errors: list[str]
) -> None:
    """The optional record-card display block: what the page renders when a
    person or gap card cites this evidence. Curation stays deliberate - the
    cross-reference rule lives in validate_repository."""
    display = record.get("display")
    if display is None:
        return
    if not isinstance(display, dict):
        errors.append(f"{where}: display must be an object")
        return
    variant = display.get("variant")
    if variant not in ("roll", "fields"):
        errors.append(f"{where}: display.variant must be 'roll' or 'fields'")
        return
    body_field = "roll" if variant == "roll" else "fields"
    expected = {"variant", "head", body_field, "cite"}
    if set(display) != expected:
        errors.append(
            f"{where}: display fields must be exactly {sorted(expected)} "
            f"for the {variant} variant"
        )
        return
    _display_text(display["head"], f"{where}: display.head", errors)
    _display_text(display["cite"], f"{where}: display.cite", errors)
    body = display[body_field]
    if not isinstance(body, list) or not body:
        errors.append(f"{where}: display.{body_field} must be a non-empty list")
        return
    for position, entry in enumerate(body, 1):
        spot = f"{where}: display.{body_field}[{position}]"
        if not isinstance(entry, dict):
            errors.append(f"{spot} must be an object")
            continue
        allowed = {"cells", "focal"} if variant == "roll" else {"dt", "dd", "focal"}
        required = allowed - {"focal"}
        if not required <= set(entry) <= allowed:
            errors.append(
                f"{spot} fields must be {sorted(required)} plus optional 'focal'"
            )
            continue
        if "focal" in entry and not isinstance(entry["focal"], bool):
            errors.append(f"{spot}.focal must be a boolean")
        if variant == "roll":
            cells = entry["cells"]
            if (not isinstance(cells, list) or len(cells) != 3
                    or not all(isinstance(cell, str) and cell for cell in cells)):
                errors.append(f"{spot}.cells must be exactly three non-empty strings")
            else:
                for cell in cells:
                    _display_text(cell, f"{spot} cell", errors)
        else:
            for key in ("dt", "dd"):
                _display_text(entry[key], f"{spot}.{key}", errors)


def _collect_display_card_refs(root: Path) -> list[str]:
    """Every ev.* named by a person/gap display.record_cards list."""
    refs: list[str] = []
    for rel in ("research/people/people.jsonl", "research/people/relationships.jsonl"):
        path = root / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            display = row.get("display") if isinstance(row, dict) else None
            if isinstance(display, dict):
                for ref in display.get("record_cards") or []:
                    if isinstance(ref, str):
                        refs.append(ref)
    return refs


def _validate_cache_provenance(
    record: dict[str, Any], where: str, errors: list[str]
) -> None:
    provenance = record.get("cache_provenance")
    if provenance is None:
        return
    expected = {
        "provider",
        "cache_key",
        "cache_schema",
        "cache_version",
        "data_sha256",
        "fetched_at",
        "record_address",
        "requested_url",
        "final_url",
        "url_gap",
    }
    if not isinstance(provenance, dict):
        errors.append(f"{where}: cache_provenance must be an object")
        return
    if set(provenance) != expected:
        errors.append(
            f"{where}: cache_provenance fields must be exactly {sorted(expected)}"
        )
        return
    if provenance["provider"] != "Ancestry":
        errors.append(f"{where}: cache_provenance.provider must be 'Ancestry'")
    key = provenance["cache_key"]
    if not isinstance(key, str) or CACHE_KEY_RE.fullmatch(key) is None:
        errors.append(
            f"{where}: cache_provenance.cache_key must be a record cache key"
        )
    address = provenance["record_address"]
    address_match = (
        CACHE_RECORD_ADDRESS_RE.fullmatch(address)
        if isinstance(address, str)
        else None
    )
    if address_match is None:
        errors.append(
            f"{where}: cache_provenance.record_address must use record/COLL/ID"
        )
    elif isinstance(key, str):
        collection, record_id = address_match.groups()
        raw_key = f"record|collection={collection}|id={record_id}"
        expected_key = "record-" + hashlib.sha1(raw_key.encode()).hexdigest()[:16]
        if key != expected_key:
            errors.append(
                f"{where}: cache_provenance.cache_key does not match record_address"
            )
    if provenance["cache_schema"] != "gen.ancestry.cache":
        errors.append(
            f"{where}: cache_provenance.cache_schema must be 'gen.ancestry.cache'"
        )
    version = provenance["cache_version"]
    if type(version) is not int or version < 1:
        errors.append(
            f"{where}: cache_provenance.cache_version must be a positive integer"
        )
    digest = provenance["data_sha256"]
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        errors.append(
            f"{where}: cache_provenance.data_sha256 must be 64 lowercase hex digits"
        )
    fetched_at = provenance["fetched_at"]
    if (
        not isinstance(fetched_at, str)
        or CACHE_TIMESTAMP_RE.fullmatch(fetched_at) is None
    ):
        errors.append(
            f"{where}: cache_provenance.fetched_at must be a UTC timestamp"
        )
    parsed_urls: dict[str, Any] = {}
    for field in ("requested_url", "final_url"):
        url = provenance[field]
        if url is None:
            continue
        if not isinstance(url, str) or URL_RE.fullmatch(url) is None:
            errors.append(f"{where}: cache_provenance.{field} must be an HTTP URL")
            continue
        try:
            parsed = urlparse(url)
        except ValueError:
            errors.append(
                f"{where}: cache_provenance.{field} must be a valid URL"
            )
            continue
        parsed_urls[field] = parsed
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host == "ancestry.com" or host.endswith(".ancestry.com")
        ):
            errors.append(
                f"{where}: cache_provenance.{field} must be an Ancestry HTTPS URL"
            )
    requested = parsed_urls.get("requested_url")
    final = parsed_urls.get("final_url")
    requested_match = (
        re.fullmatch(r"/search/collections/(\d+)/records/(\d+)/?", requested.path)
        if requested is not None
        else None
    )
    final_match = None
    if final is not None:
        final_match = re.fullmatch(
            r"/search/collections/(\d+)/records/(\d+)/?", final.path
        )
        if final_match is None:
            discovery = re.fullmatch(
                r"/discoveryui-content/view/(\d+):(\d+)/?", final.path
            )
            if discovery is not None:
                final_match = (discovery.group(2), discovery.group(1))
    if requested is not None and requested_match is None:
        errors.append(
            f"{where}: cache_provenance.requested_url must identify one collection record"
        )
    requested_identity = (
        requested_match.groups() if requested_match is not None else None
    )
    final_identity = (
        final_match.groups()
        if hasattr(final_match, "groups")
        else final_match
    )
    if final is not None and final_identity is None:
        errors.append(
            f"{where}: cache_provenance.final_url must identify one collection record"
        )
    elif requested_identity is not None and final_identity is not None and final_identity != requested_identity:
        errors.append(
            f"{where}: cache_provenance requested/final record identities differ"
        )
    address_identity = address_match.groups() if address_match is not None else None
    for field, identity in (
        ("requested_url", requested_identity),
        ("final_url", final_identity),
    ):
        if identity is not None and address_identity is not None and identity != address_identity:
            errors.append(
                f"{where}: cache_provenance.{field} does not match record_address"
            )
    url_gap = provenance["url_gap"]
    missing_urls = [
        field
        for field in ("requested_url", "final_url")
        if provenance[field] is None
    ]
    if missing_urls:
        if not isinstance(url_gap, str) or not url_gap.strip():
            errors.append(
                f"{where}: cache_provenance.url_gap must explain missing acquisition URLs"
            )
    elif url_gap is not None:
        errors.append(
            f"{where}: cache_provenance.url_gap must be null when acquisition URLs are present"
        )
    acquisition = record.get("acquisition")
    if isinstance(acquisition, dict) and acquisition.get("provider") != "Ancestry":
        errors.append(
            f"{where}: cache-backed evidence acquisition.provider must be 'Ancestry'"
        )


def _validate_record(
    record: Any,
    where: str,
    root: Path,
    references: set[str],
    require_local_assets: bool,
    errors: list[str],
) -> tuple[str | None, tuple[str, str] | None]:
    if not isinstance(record, dict):
        errors.append(f"{where}: each JSONL line must be an object")
        return None, None

    missing = REQUIRED_FIELDS - set(record)
    unknown = set(record) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if missing:
        errors.append(f"{where}: missing required fields {sorted(missing)}")
    if unknown:
        errors.append(f"{where}: unknown fields {sorted(unknown)}")

    for field in ("id", "record_type", "title", "repository", "citation", "accessed", "status", "confidence", "transcription"):
        _nonempty_string(record, field, where, errors)
    if "citation_gap" in record:
        _nonempty_string(record, "citation_gap", where, errors)

    evidence_id = record.get("id")
    if isinstance(evidence_id, str) and not EVIDENCE_ID_RE.fullmatch(evidence_id):
        errors.append(f"{where}: invalid evidence id {evidence_id!r}")
    if record.get("record_type") not in RECORD_TYPES:
        errors.append(f"{where}: record_type must be one of {sorted(RECORD_TYPES)}")
    if record.get("status") not in STATUSES:
        errors.append(f"{where}: status must be one of {sorted(STATUSES)}")
    if record.get("confidence") not in CONFIDENCES:
        errors.append(f"{where}: confidence must be one of {sorted(CONFIDENCES)}")
    try:
        dt.date.fromisoformat(record.get("accessed"))
    except (TypeError, ValueError):
        errors.append(f"{where}: accessed must be an ISO date")

    person_refs = _unique_string_list(record, "person_refs", where, errors)
    case_refs = _unique_string_list(record, "case_refs", where, errors)
    supports = _unique_string_list(record, "supports", where, errors)
    opposes = _unique_string_list(record, "opposes", where, errors)
    for ref in person_refs:
        if not PERSON_ID_RE.fullmatch(ref):
            errors.append(f"{where}: person_refs contains non-person id {ref!r}")
    for ref in case_refs:
        if not CASE_ID_RE.fullmatch(ref):
            errors.append(f"{where}: case_refs contains non-case id {ref!r}")
    all_record_refs = set(person_refs) | set(case_refs)
    for field, values in (("supports", supports), ("opposes", opposes)):
        for ref in values:
            if ref not in all_record_refs:
                errors.append(f"{where}: {field} ref {ref!r} is absent from person_refs/case_refs")
    overlap = set(supports) & set(opposes)
    if overlap:
        errors.append(f"{where}: supports and opposes overlap: {sorted(overlap)}")
    for ref in sorted(all_record_refs | set(supports) | set(opposes)):
        if ref not in references:
            errors.append(f"{where}: unresolved person/case reference {ref!r}")

    urls = _unique_string_list(record, "source_urls", where, errors)
    for url in urls:
        if not URL_RE.fullmatch(url):
            errors.append(f"{where}: invalid source URL {url!r}")
    provenance = record.get("cache_provenance")
    if isinstance(provenance, dict):
        for field in ("requested_url", "final_url"):
            url = provenance.get(field)
            if isinstance(url, str) and url not in urls:
                errors.append(
                    f"{where}: cache_provenance.{field} must appear in source_urls"
                )

    _validate_privacy(record, where, errors)
    _validate_cache_provenance(record, where, errors)
    _validate_display_block(record, where, errors)
    pull_key = _validate_acquisition(
        record, where, root, require_local_assets, errors
    )
    return evidence_id if isinstance(evidence_id, str) else None, pull_key


def validate_repository(
    root: Path = ROOT,
    evidence_dir: Path = EVIDENCE_DIR,
    require_local_assets: bool = False,
) -> ValidationResult:
    root = root.resolve()
    directory = evidence_dir if evidence_dir.is_absolute() else root / evidence_dir
    errors: list[str] = []
    references = collect_reference_universe(root, errors)
    record_card_refs = collect_record_card_refs(root, errors)

    if not directory.is_dir():
        errors.append(f"evidence directory is missing: {directory}")
        return ValidationResult(tuple(errors), 0, 0)
    shards = sorted(directory.glob("*.jsonl"))
    shard_names = {path.name for path in shards}
    if shard_names != EXPECTED_SHARDS:
        missing = sorted(EXPECTED_SHARDS - shard_names)
        unexpected = sorted(shard_names - EXPECTED_SHARDS)
        if missing:
            errors.append(f"missing evidence shards: {missing}")
        if unexpected:
            errors.append(f"unexpected evidence shards: {unexpected}")

    seen_ids: dict[str, str] = {}
    seen_pulls: dict[tuple[str, str], str] = {}
    display_ids: dict[str, str] = {}
    record_count = 0
    for path in shards:
        relative = path.relative_to(root) if path.is_relative_to(root) else path
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            where = f"{relative}:{line_number}"
            if not line.strip():
                errors.append(f"{where}: blank lines are not allowed in JSONL")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{where}: invalid JSON: {exc.msg} at column {exc.colno}")
                continue
            record_count += 1
            evidence_id, pull_key = _validate_record(
                record,
                where,
                root,
                references,
                require_local_assets,
                errors,
            )
            if evidence_id is not None:
                if evidence_id in seen_ids:
                    errors.append(
                        f"{where}: duplicate evidence id {evidence_id!r}; first seen at {seen_ids[evidence_id]}"
                    )
                else:
                    seen_ids[evidence_id] = where
                if isinstance(record, dict) and record.get("display") is not None:
                    display_ids[evidence_id] = where
            if pull_key is not None:
                if pull_key in seen_pulls:
                    errors.append(
                        f"{where}: duplicate logical pull {pull_key[0]}/{pull_key[1]}; first seen at {seen_pulls[pull_key]}"
                    )
                else:
                    seen_pulls[pull_key] = where

    for ref in record_card_refs:
        if ref not in seen_ids:
            errors.append(f"index.html record card references unknown evidence id {ref!r}")

    # Curation rule: every evidence display block is referenced by exactly one
    # person/gap record_cards list, and every reference has a display block.
    display_card_refs = _collect_display_card_refs(root)
    reference_counts: dict[str, int] = {}
    for ref in display_card_refs:
        reference_counts[ref] = reference_counts.get(ref, 0) + 1
        if ref not in seen_ids:
            errors.append(
                f"display.record_cards references unknown evidence id {ref!r}"
            )
        elif ref not in display_ids:
            errors.append(
                f"display.record_cards references {ref!r}, which has no evidence "
                "display block"
            )
    for evidence_id, where in sorted(display_ids.items()):
        count = reference_counts.get(evidence_id, 0)
        if count != 1:
            errors.append(
                f"{where}: the display block for {evidence_id!r} must be "
                f"referenced by exactly one record_cards list (found {count})"
            )

    return ValidationResult(tuple(errors), record_count, len(seen_pulls))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument(
        "--require-local-assets",
        action="store_true",
        help="fail when ignored pull directories or assets are absent",
    )
    args = parser.parse_args(argv)
    result = validate_repository(
        root=args.root,
        evidence_dir=args.evidence_dir,
        require_local_assets=args.require_local_assets,
    )
    if not result.ok:
        print("evidence validation failed:", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        f"evidence ok: {result.record_count} records, "
        f"{result.pull_count} unique logical pulls"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
