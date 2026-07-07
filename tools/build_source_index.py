#!/usr/bin/env python3
"""Build a searchable JSON source index from index.html."""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
OUT_PATH = ROOT / "research" / "sources" / "source-index.json"


class SourceLedgerParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_source_ledger = False
        self.in_heading = False
        self.in_item = False
        self.in_anchor = False
        self.heading_parts: list[str] = []
        self.current: dict[str, object] | None = None
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "h2":
            self.in_heading = True
            self.heading_parts = []
        if self.in_source_ledger and tag == "li":
            self.in_item = True
            self.current = {"url": "", "title_parts": [], "parts": []}
        if self.in_item and tag == "a" and self.current is not None:
            self.in_anchor = True
            self.current["url"] = attr_map.get("href") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2":
            heading = "".join(self.heading_parts).strip()
            self.in_heading = False
            if heading == "Source Ledger":
                self.in_source_ledger = True
            elif self.in_source_ledger:
                self.in_source_ledger = False
        if self.in_item and tag == "a":
            self.in_anchor = False
        if self.in_item and tag == "li" and self.current is not None:
            parts = self.current["parts"]
            title_parts = self.current["title_parts"]
            raw = "".join(parts).strip() if isinstance(parts, list) else ""
            title = "".join(title_parts).strip() if isinstance(title_parts, list) else ""
            blurb = raw
            if title and raw.startswith(title):
                blurb = raw[len(title) :].strip()
            blurb = blurb.lstrip(". ").strip()
            self.items.append(
                {
                    "url": html_lib.unescape(str(self.current["url"])),
                    "title": html_lib.unescape(title),
                    "blurb": html_lib.unescape(blurb),
                }
            )
            self.in_item = False
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.in_heading:
            self.heading_parts.append(data)
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


def source_type(url: str, title: str) -> str:
    host = urlparse(url).netloc.lower()
    text = f"{url} {host} {title}".lower()
    if "findagrave" in text:
        return "cemetery_memorial"
    if "familysearch" in text:
        return "public_tree_index"
    if "archion" in text:
        return "church_record_target"
    if "newspapers" in text:
        return "newspaper"
    if any(term in text for term in ["ksgenweb", "genealogytrails", "interment.net"]):
        return "local_transcription"
    if "digitalcommons" in text or ".pdf" in text or "pdf" in text:
        return "compiled_pdf_or_journal"
    if any(term in text for term in ["wikitree", "rootsmagic", "ancestry", "treespot", "allshouse"]):
        return "compiled_tree_or_profile"
    if any(term in text for term in ["meyersgaz", "kartenmeister", "agoff"]):
        return "gazetteer_or_registry_context"
    if any(term in text for term in ["obituaries", "funeral", "hayspost", "mortuary"]):
        return "obituary"
    return "web_reference"


def lineage_tags(text: str) -> list[str]:
    rules = {
        "zimmerman": ["zimmerman", "zinkle", "zinkl", "mainhardt", "wuerttemberger", "archion"],
        "nauer": ["nauer", "koeberger", "waterloo", "wilmot"],
        "zodrow": ["zodrow", "grams", "sabanka", "lebehnke", "deutsch krone", "nowa lubianka"],
        "mundell": ["mundell", "clemans", "clemens", "flaherty", "rust", "cantwell", "adolph", "winona"],
        "dible": ["dible", "heckman", "haden", "dreibelbis", "zephaniah"],
        "long_mcclelland": ["long", "sleight", "mcclelland", "mcclellan", "love", "hoge"],
        "connelly_durham": ["connelly", "connolly", "durham", "ford", "staples"],
        "claar": ["claar", "klar", "white", "stropes", "hoyle", "hogle"],
    }
    lower = text.lower()
    return [tag for tag, needles in rules.items() if any(needle in lower for needle in needles)] or ["general"]


def evidence_role(blurb: str) -> str:
    lower = blurb.lower()
    if any(term in lower for term in ["target", "best next", "needed", "needs"]):
        return "research_target"
    if any(term in lower for term in ["conflict", "collision", "unresolved", "variant"]):
        return "conflict_or_disambiguation"
    if "context" in lower and "not proof" in lower:
        return "context_not_proof"
    if any(term in lower for term in ["compiled", "lead", "use as"]):
        return "lead"
    if any(term in lower for term in ["names", "lists", "gives", "states"]):
        return "evidence"
    return "reference"


def source_id(item: dict[str, str]) -> str:
    slug = slugify(item["title"])
    digest = hashlib.sha1(
        "\n".join([item["title"], item["url"], item["blurb"]]).encode("utf-8")
    ).hexdigest()[:8]
    return f"src.{slug}.{digest}"


def build_index() -> dict[str, object]:
    parser = SourceLedgerParser()
    parser.feed(HTML_PATH.read_text())
    records: list[dict[str, object]] = []
    for item in parser.items:
        search_text = " ".join([item["title"], item["blurb"]])
        records.append(
            {
                "id": source_id(item),
                "title": item["title"],
                "url": item["url"],
                "source_type": source_type(item["url"], item["title"]),
                "lineage_tags": lineage_tags(search_text),
                "evidence_role": evidence_role(item["blurb"]),
                "blurb": item["blurb"],
                "search_text": search_text,
            }
        )

    return {
        "schema_version": "1.0.0",
        "updated": "2026-07-07",
        "source": "Extracted from index.html Source Ledger",
        "record_count": len(records),
        "fields": {
            "id": "Stable local source id for notes and reasoning traces, generated from source title, URL, and blurb.",
            "title": "Human-readable source title from the artifact ledger.",
            "url": "Source URL.",
            "source_type": "Coarse type used for filtering and reliability expectations.",
            "lineage_tags": "Branch/search tags inferred from title and blurb.",
            "evidence_role": "How this source is currently being used.",
            "blurb": "Short indexing summary.",
            "search_text": "Concatenated title and blurb for simple full-text search.",
        },
        "sources": records,
    }


def main() -> int:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--check", action="store_true", help="fail if the generated index differs")
    args = arg_parser.parse_args()

    rendered = json.dumps(build_index(), indent=2, ensure_ascii=True) + "\n"
    if args.check:
        current = OUT_PATH.read_text() if OUT_PATH.exists() else ""
        if current != rendered:
            print(f"{OUT_PATH} is out of date; run python3 tools/build_source_index.py", file=sys.stderr)
            return 1
        print(f"{OUT_PATH} is current")
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(rendered)
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
