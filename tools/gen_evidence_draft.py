#!/usr/bin/env python3
"""Build a review-required canonical evidence draft from one cached record."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

import gen_ancestry


CENSUS_COLLECTIONS = {
    "8054": "1850",
    "7667": "1860",
    "7163": "1870",
    "6742": "1880",
    "7602": "1900",
    "7884": "1910",
    "6061": "1920",
    "6224": "1930",
    "2442": "1940",
    "62308": "1950",
}
EVIDENCE_ID_RE = re.compile(r"ev\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
PERSON_ID_RE = re.compile(r"person\.[a-z0-9]+(?:[._-][a-z0-9]+)*\Z")
CASE_ID_RE = re.compile(r"case\.\d{2}\Z")
RECORD_TYPES = (
    "census",
    "church_register",
    "death_index",
    "divorce",
    "marriage",
    "obituary_index",
    "probate",
    "record_bundle",
    "search_log",
)


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def field_value(fields: dict[str, str], *labels: str) -> str | None:
    folded = {key.casefold(): value for key, value in fields.items()}
    for label in labels:
        value = folded.get(label.casefold())
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def inferred_title(collection: str, fields: dict[str, str]) -> str:
    name = field_value(fields, "Name") or "unnamed subject"
    year = CENSUS_COLLECTIONS.get(collection)
    if year:
        return f"{year} United States census record for {name}"
    return f"Ancestry collection {collection} record for {name}"


def citation_from_record(
    collection: str, record_id: str, data: dict[str, Any]
) -> tuple[str, str | None, list[str]]:
    metadata = data.get("citation_metadata")
    warnings: list[str] = []
    if isinstance(metadata, dict):
        citation_fields = metadata.get("fields")
        source_citation = (
            citation_fields.get("source_citation")
            if isinstance(citation_fields, dict)
            else None
        )
        if isinstance(source_citation, str) and source_citation.strip():
            if metadata.get("complete") is False:
                warnings.extend(
                    warning
                    for warning in metadata.get("warnings", [])
                    if isinstance(warning, str)
                )
            return (
                f"{source_citation.strip()}; Ancestry collection {collection}, record {record_id}.",
                None,
                warnings,
            )

    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    year = CENSUS_COLLECTIONS.get(collection)
    if year:
        place = field_value(
            fields,
            f"Home in {year}",
            "Home in 1950",
            "Residence Place",
            "Home in 1940",
        )
        name = field_value(fields, "Name")
        details: list[str] = []
        if place:
            details.append(place)
        for label, rendered in (
            ("Enumeration District", "enumeration district"),
            ("Sheet Number", "sheet"),
            ("Page Number", "page"),
            ("Dwelling Number", "dwelling"),
            ("Family Number", "family"),
            ("Line Number", "line"),
        ):
            value = field_value(fields, label)
            if value:
                details.append(f"{rendered} {value}")
        subject = f", {name}" if name else ""
        location = ", ".join(details)
        location = f", {location}" if location else ""
        citation = (
            f"{year} U.S. census{location}{subject}; "
            f"Ancestry collection {collection}, record {record_id}."
        )
        gap = (
            "The cached structured record did not expose a complete source citation; "
            "verify roll, page or sheet, and enumeration district against the record image."
        )
        warnings.append("citation assembled only from fields present in the cached record")
        return citation, gap, warnings

    warnings.append("collection-specific citation format is unknown")
    return (
        f"Ancestry collection {collection}, record {record_id}.",
        "Replace this fallback with the repository, record-set, jurisdiction, and image-level citation before landing.",
        warnings,
    )


def build_draft(
    *,
    address: str,
    evidence_id: str,
    record_type: str | None,
    title: str | None,
    batch: str | None,
    person_refs: list[str],
    case_refs: list[str],
) -> dict[str, Any]:
    loc = gen_ancestry.parse_address(address)
    if not isinstance(loc, dict) or loc.get("type") != "record":
        raise gen_ancestry.CockpitError(
            "--from-cache must be one record/COLL/ID address", address=address
        )
    key = gen_ancestry.location_key(loc)
    with gen_ancestry.cache_lock():
        envelope = gen_ancestry.cache_read_envelope(key)
    if envelope is None:
        raise gen_ancestry.CockpitError(
            "cached record not found; no live request was made", key=key
        )
    meta, data = envelope
    if data.get("command") != "ancestry.record":
        raise gen_ancestry.CockpitError(
            "cached entry is not an Ancestry record", key=key
        )

    collection = loc["collection"]
    record_id = loc["id"]
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    citation, citation_gap, citation_warnings = citation_from_record(
        collection, record_id, data
    )
    fetched_at = meta["fetched_at"]
    requested_url = meta.get("requested_url")
    final_url = meta.get("final_url")
    present_urls = [
        value for value in (final_url, requested_url) if isinstance(value, str)
    ]
    source_urls = list(dict.fromkeys(present_urls))
    missing_url_fields = [
        field
        for field, value in (
            ("requested_url", requested_url),
            ("final_url", final_url),
        )
        if not isinstance(value, str)
    ]
    url_gap = None
    if missing_url_fields:
        requested_url = requested_url if isinstance(requested_url, str) else None
        final_url = final_url if isinstance(final_url, str) else None
        url_gap = (
            "The legacy cached acquisition did not retain "
            + " or ".join(missing_url_fields)
            + "; refresh the record to capture complete acquisition URLs."
        )
    inferred_record_type = "census" if collection in CENSUS_COLLECTIONS else "record_bundle"
    draft: dict[str, Any] = {
        "id": evidence_id,
        "record_type": record_type or inferred_record_type,
        "title": title or inferred_title(collection, fields),
        "repository": (
            "National Archives and Records Administration, Record Group 29; accessed through Ancestry"
            if collection in CENSUS_COLLECTIONS
            else "Ancestry"
        ),
        "citation": citation,
        "accessed": fetched_at[:10],
        "status": "found",
        "confidence": "medium",
        "supports": [],
        "opposes": [],
        "person_refs": sorted(set(person_refs)),
        "case_refs": sorted(set(case_refs)),
        "privacy_review": {
            "status": "pending",
            "reviewed": "",
            "living_people": "review_required",
            "sensitive_identifiers": "review_required",
        },
        "acquisition": {
            "provider": "Ancestry",
            "batch": batch or f"ancestry-{fetched_at[:7]}",
            "pull": "auto",
            "local_dirs": [],
        },
        "cache_provenance": {
            "provider": "Ancestry",
            "cache_key": key,
            "cache_schema": gen_ancestry.CACHE_SCHEMA,
            "cache_version": gen_ancestry.CACHE_VERSION,
            "data_sha256": meta["data_sha256"],
            "fetched_at": fetched_at,
            "record_address": address,
            "requested_url": requested_url,
            "final_url": final_url,
            "url_gap": url_gap,
        },
        "source_urls": source_urls,
        "transcription": "Replace with a privacy-reviewed transcription or abstract before landing.",
        "local_assets": [],
    }
    if citation_gap:
        draft["citation_gap"] = citation_gap

    extraction = data.get("household_extraction")
    warnings = list(citation_warnings)
    if url_gap is not None:
        warnings.append(url_gap)
    if isinstance(extraction, dict):
        warnings.extend(
            warning
            for warning in extraction.get("warnings", [])
            if isinstance(warning, str)
        )
        if extraction.get("complete") is False:
            warnings.append("household extraction is incomplete; inspect before transcribing")

    requires_review = [
        "privacy_review must be completed and changed to passed",
        "transcription must be replaced with a reviewed abstract",
        "citation and any citation_gap must be verified",
        "person_refs, case_refs, supports, and opposes must reflect the conclusion",
        "record_type, title, repository, status, and confidence must be confirmed",
    ]
    return {
        "command": "evidence.draft",
        "ok": True,
        "cache": draft["cache_provenance"],
        "draft": draft,
        "requires_review": requires_review,
        "warnings": list(dict.fromkeys(warnings)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--from-cache", required=True, metavar="record/COLL/ID")
    parser.add_argument("--id", dest="evidence_id", required=True)
    parser.add_argument("--record-type", choices=RECORD_TYPES)
    parser.add_argument("--title")
    parser.add_argument("--batch")
    parser.add_argument("--person-ref", action="append", default=[])
    parser.add_argument("--case-ref", action="append", default=[])
    args = parser.parse_args(argv)
    if EVIDENCE_ID_RE.fullmatch(args.evidence_id) is None:
        emit(
            {
                "command": "evidence.draft",
                "ok": False,
                "error": "--id must be a canonical ev.* id",
                "id": args.evidence_id,
            }
        )
        return 1
    invalid_people = [ref for ref in args.person_ref if PERSON_ID_RE.fullmatch(ref) is None]
    invalid_cases = [ref for ref in args.case_ref if CASE_ID_RE.fullmatch(ref) is None]
    if invalid_people or invalid_cases:
        emit(
            {
                "command": "evidence.draft",
                "ok": False,
                "error": "subject refs must use canonical person.* and case.NN ids",
                "invalid_person_refs": invalid_people,
                "invalid_case_refs": invalid_cases,
            }
        )
        return 1
    try:
        emit(
            build_draft(
                address=args.from_cache,
                evidence_id=args.evidence_id,
                record_type=args.record_type,
                title=args.title,
                batch=args.batch,
                person_refs=args.person_ref,
                case_refs=args.case_ref,
            )
        )
    except gen_ancestry.CockpitError as exc:
        emit(
            {
                "command": "evidence.draft",
                "ok": False,
                "error": exc.error,
                **exc.details,
            }
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
