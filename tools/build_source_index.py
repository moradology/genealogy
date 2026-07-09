#!/usr/bin/env python3
"""Build the searchable source index from canonical Git-tracked JSONL.

`research/sources/sources.jsonl` is authoritative. The HTML Source Ledger is a
presentation projection checked semantically against it; HTML is never parsed
to create or classify source records.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
SOURCES_PATH = ROOT / "research" / "sources" / "sources.jsonl"
META_PATH = ROOT / "research" / "sources" / "sources-meta.json"
OUT_PATH = ROOT / "research" / "sources" / "source-index.json"
REQUIRED = frozenset({
    "html_id", "group", "id", "title", "url", "source_type", "lineage_tags",
    "evidence_role", "blurb", "search_text",
})
SOURCE_TYPES = frozenset({
    "archival_record", "cemetery_memorial", "church_record_target", "compiled_pdf_or_journal",
    "compiled_tree_or_profile", "gazetteer_or_registry_context", "local_transcription",
    "newspaper", "obituary", "public_tree_index", "web_reference",
})
EVIDENCE_ROLES = frozenset({
    "conflict_or_disambiguation", "context_not_proof", "evidence", "lead",
    "reference", "research_target",
})


class SourceLedgerParser(HTMLParser):
    """Parse only enough HTML to prove the presentation matches JSONL truth."""

    def __init__(self) -> None:
        super().__init__()
        self.in_source_ledger = False
        self.in_heading = False
        self.in_summary = False
        self.in_item = False
        self.in_anchor = False
        self.ignore_depth = 0
        self.heading_parts: list[str] = []
        self.summary_parts: list[str] = []
        self.current_group = ""
        self.current: dict[str, object] | None = None
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        if self.ignore_depth:
            self.ignore_depth += 1
            return
        if self.in_item and tag == "span" and ("scode" in classes or "data-g" in attr_map):
            self.ignore_depth = 1
            return
        if self.in_summary and tag == "span" and "count" in classes:
            self.ignore_depth = 1
            return
        if tag == "h2":
            self.in_heading = True
            self.heading_parts = []
        if self.in_source_ledger and tag == "summary":
            self.in_summary = True
            self.summary_parts = []
        if self.in_source_ledger and tag == "li":
            self.in_item = True
            self.current = {
                "url": "", "html_id": attr_map.get("id") or "", "title_parts": [], "parts": [],
            }
        if self.in_item and tag == "a" and self.current is not None:
            self.in_anchor = True
            self.current["url"] = attr_map.get("href") or ""

    def handle_endtag(self, tag: str) -> None:
        if self.ignore_depth:
            self.ignore_depth -= 1
            return
        if tag == "h2":
            heading = "".join(self.heading_parts).strip()
            self.in_heading = False
            if heading == "Source Ledger":
                self.in_source_ledger = True
            elif self.in_source_ledger:
                self.in_source_ledger = False
        if self.in_summary and tag == "summary":
            self.current_group = "".join(self.summary_parts).strip()
            self.in_summary = False
        if self.in_item and tag == "a":
            self.in_anchor = False
        if self.in_item and tag == "li" and self.current is not None:
            parts = self.current["parts"]
            title_parts = self.current["title_parts"]
            raw = "".join(parts).strip() if isinstance(parts, list) else ""
            title = "".join(title_parts).strip() if isinstance(title_parts, list) else ""
            blurb = raw[len(title):].strip() if title and raw.startswith(title) else raw
            self.items.append({
                "html_id": html_lib.unescape(str(self.current["html_id"])),
                "group": html_lib.unescape(self.current_group),
                "title": html_lib.unescape(title),
                "url": html_lib.unescape(str(self.current["url"])),
                "blurb": html_lib.unescape(blurb.lstrip(". ").strip()),
            })
            self.in_item = False
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.ignore_depth:
            return
        if self.in_heading:
            self.heading_parts.append(data)
        if self.in_summary:
            self.summary_parts.append(data)
        if self.in_item and self.current is not None:
            parts = self.current["parts"]
            if isinstance(parts, list):
                parts.append(data)
            if self.in_anchor:
                title_parts = self.current["title_parts"]
                if isinstance(title_parts, list):
                    title_parts.append(data)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:70].strip("-") or "source"


def source_id(record: dict[str, object]) -> str:
    digest = hashlib.sha1(str(record["url"]).encode("utf-8")).hexdigest()[:8]
    return f"src.{slugify(str(record['title']))}.{digest}"


def canonical_sources() -> list[dict[str, object]]:
    records = [json.loads(line) for line in SOURCES_PATH.read_text().splitlines() if line.strip()]
    failures = []
    seen_ids = set()
    seen_urls = set()
    for position, record in enumerate(records, start=1):
        missing = REQUIRED - set(record)
        if missing:
            failures.append(f"source line {position} missing fields: {sorted(missing)}")
            continue
        if record["html_id"] != f"s{position}":
            failures.append(f"source line {position} html_id {record['html_id']!r} != s{position}")
        expected_id = source_id(record)
        if record["id"] != expected_id:
            failures.append(f"{record['html_id']} id {record['id']!r} != {expected_id!r}")
        if record["id"] in seen_ids:
            failures.append(f"duplicate source id {record['id']}")
        if record["url"] in seen_urls:
            failures.append(f"duplicate source URL {record['url']}")
        seen_ids.add(record["id"])
        seen_urls.add(record["url"])
        if record["source_type"] not in SOURCE_TYPES:
            failures.append(f"{record['html_id']} invalid source_type {record['source_type']!r}")
        if record["evidence_role"] not in EVIDENCE_ROLES:
            failures.append(f"{record['html_id']} invalid evidence_role {record['evidence_role']!r}")
        if not isinstance(record["lineage_tags"], list) or not record["lineage_tags"]:
            failures.append(f"{record['html_id']} lineage_tags must be a non-empty list")
        expected_search = f"{record['title']} {record['blurb']}"
        if record["search_text"] != expected_search:
            failures.append(f"{record['html_id']} search_text is not title + blurb")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        raise SystemExit(1)
    return records


def check_html_projection(records: list[dict[str, object]]) -> None:
    parser = SourceLedgerParser()
    parser.feed(HTML_PATH.read_text())
    failures = []
    if len(parser.items) != len(records):
        failures.append(f"HTML ledger has {len(parser.items)} items; canonical JSONL has {len(records)}")
    fields = ("html_id", "group", "title", "url", "blurb")
    for position, (canonical, projected) in enumerate(zip(records, parser.items), start=1):
        for field in fields:
            if canonical[field] != projected[field]:
                failures.append(
                    f"source {position} HTML {field} drift: {projected[field]!r} != {canonical[field]!r}")
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        raise SystemExit(1)


def build_index(records: list[dict[str, object]]) -> dict[str, object]:
    meta = json.loads(META_PATH.read_text())
    public_records = [
        {key: value for key, value in record.items() if key not in {"html_id", "group"}}
        for record in records
    ]
    return {
        **meta,
        "record_count": len(public_records),
        "fields": {
            "id": "Stable local source id; readable slug from title plus a URL-only hash.",
            "title": "Human-readable source title.",
            "url": "Source URL.",
            "source_type": "Explicit source type used for reliability expectations.",
            "lineage_tags": "Explicit branch/search tags.",
            "evidence_role": "Explicit statement of how this source is used.",
            "blurb": "Short indexing summary.",
            "search_text": "Title plus blurb for simple full-text search.",
        },
        "sources": public_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if either projection differs")
    args = parser.parse_args()
    records = canonical_sources()
    check_html_projection(records)
    rendered = json.dumps(build_index(records), indent=2, ensure_ascii=True) + "\n"
    if args.check:
        current = OUT_PATH.read_text() if OUT_PATH.exists() else ""
        if current != rendered:
            print(f"{OUT_PATH} is out of date; run ./gen build source-index", file=sys.stderr)
            return 1
        print(f"{OUT_PATH} is current from canonical sources.jsonl")
        return 0
    OUT_PATH.write_text(rendered)
    print(f"wrote {OUT_PATH} from {SOURCES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
