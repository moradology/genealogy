#!/usr/bin/env python3
"""Check page-local ids, cross-page fragment links, and canonical anchors."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

import page_map


ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)

    def _collect(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value is not None:
                self.ids.append(value)
            if tag == "a" and name == "href" and value is not None:
                self.hrefs.append(value)


def _jsonl_rows(path: Path) -> Iterable[dict]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if isinstance(row, dict):
                yield row


def site_pages(root: Path) -> list[str]:
    return ["index.html"] + [
        page for page in page_map.BRANCH_PAGES.values() if (root / page).is_file()
    ]


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def canonical_anchors(root: Path) -> frozenset[str]:
    anchors: set[str] = set()

    for row in _jsonl_rows(root / "research" / "people" / "people.jsonl"):
        anchor = row.get("public_anchor")
        if isinstance(anchor, str):
            anchors.add(anchor)

    for row in _jsonl_rows(root / "research" / "people" / "relationships.jsonl"):
        anchor = row.get("public_anchor")
        if row.get("node_type") == "gap" and isinstance(anchor, str):
            anchors.add(anchor)

    for row in _jsonl_rows(root / "research" / "cases" / "cases.jsonl"):
        value = row.get("id")
        if isinstance(value, str):
            anchors.add(value)

    for row in _jsonl_rows(root / "research" / "sources" / "sources.jsonl"):
        html_id = row.get("html_id")
        if isinstance(html_id, str):
            anchors.add(html_id)

    return frozenset(anchors)


def check_duplicate_ids(
    parsed: dict[str, PageParser], errors: list[str]
) -> None:
    for page, parser in parsed.items():
        counts = Counter(parser.ids)
        for value in sorted(value for value, count in counts.items() if count > 1):
            errors.append(f"{page}: duplicate id {value!r}")


def check_hrefs(
    parsed: dict[str, PageParser], actual_pages: frozenset[str], errors: list[str]
) -> None:
    possible_pages = frozenset({"index.html", *page_map.BRANCH_PAGES.values()})
    ids_by_page = {page: set(parser.ids) for page, parser in parsed.items()}

    for page, parser in parsed.items():
        for href in parser.hrefs:
            if href.startswith("#"):
                target = href[1:]
                if target not in ids_by_page[page]:
                    errors.append(f"{page}: href {href!r} targets missing id {target!r}")
                continue

            target_page, separator, target = href.partition("#")
            if separator and target_page in possible_pages:
                if target_page not in actual_pages:
                    errors.append(f"{page}: href {href!r} targets missing page {target_page!r}")
                elif target not in ids_by_page[target_page]:
                    errors.append(
                        f"{page}: href {href!r} targets missing id {target!r} "
                        f"on {target_page}"
                    )


def check_canonical_anchors(
    root: Path, parsed: dict[str, PageParser], errors: list[str]
) -> None:
    assignments = page_map.page_assignments(root)
    locations: dict[str, list[str]] = defaultdict(list)

    for page, parser in parsed.items():
        for value in parser.ids:
            locations[value].append(page)

    for anchor in sorted(canonical_anchors(root)):
        expected_page = assignments.get(anchor)
        if expected_page is None:
            errors.append(f"canonical anchor {anchor!r} has no page assignment")
            continue

        actual_pages = locations.get(anchor, [])
        if len(actual_pages) != 1:
            errors.append(
                f"canonical anchor {anchor!r} appears {len(actual_pages)} times "
                f"site-wide; expected exactly once on {expected_page}"
            )
        elif actual_pages[0] != expected_page:
            errors.append(
                f"canonical anchor {anchor!r} appears on {actual_pages[0]}; "
                f"expected {expected_page}"
            )


def check(root: Path) -> list[str]:
    pages = site_pages(root)
    parsed = {page: parse_page(root / page) for page in pages}
    errors: list[str] = []

    check_duplicate_ids(parsed, errors)
    check_hrefs(parsed, frozenset(pages), errors)
    check_canonical_anchors(root, parsed, errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    root = args.root
    pages = site_pages(root)
    parsed = {page: parse_page(root / page) for page in pages}
    errors: list[str] = []
    check_duplicate_ids(parsed, errors)
    check_hrefs(parsed, frozenset(pages), errors)
    check_canonical_anchors(root, parsed, errors)

    if errors:
        for error in errors:
            print(error)
        return 1

    id_count = sum(len(parser.ids) for parser in parsed.values())
    href_count = sum(len(parser.hrefs) for parser in parsed.values())
    print(
        f"check_pages: {len(pages)} page(s), {id_count} id(s), "
        f"{href_count} href(s), {len(canonical_anchors(root))} canonical anchor(s) OK"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
