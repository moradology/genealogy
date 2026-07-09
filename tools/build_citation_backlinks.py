#!/usr/bin/env python3
"""Regenerate Source Ledger backlinks from citation chips in index.html."""

from __future__ import annotations

import argparse
import html as html_lib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
SOURCE_SECTION_RE = re.compile(r'(<section class="sheet" id="sources">.*?</section>)', re.S)
LI_RE = re.compile(r"<li(?P<attrs>[^>]*)>(?P<body>.*?)</li>", re.S)
ID_RE = re.compile(r'\bid=(?:"([^"]+)"|([^\s>]+))')
SN_RE = re.compile(r"^s[1-9]\d*$")
GENERATED_RE = re.compile(r'\s*<span data-g>[^<]*</span>')


def normalize_label(label: str) -> str:
    label = label.replace("\xa0", " ").replace("·", "/").replace("–", "-")
    label = re.sub(r"\s+", " ", label.strip())
    return re.sub(r"\s*/\s*", "/", label)


def usable_label(label: str) -> bool:
    return bool(label) and label.lower() != "frontier" and not label.startswith("(")


class CitationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[dict[str, object]] = []
        self.cite_depth = 0
        self.cite_context = ""
        self.ahnen_depth = 0
        self.ahnen_context = ""
        self.ahnen_parts: list[str] = []
        self.person_labels: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []

    def context_id(self) -> str:
        for entry in reversed(self.stack):
            entry_id = str(entry["id"])
            classes = entry["classes"]
            if entry_id and isinstance(classes, set) and ("person" in classes or "case" in classes):
                return entry_id
        return ""

    def label_for(self, context: str) -> str:
        label = self.person_labels.get(context, "")
        return label if usable_label(label) else context

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        is_cite = tag == "a" and "cite" in classes
        if self.ahnen_depth:
            self.ahnen_depth += 1
        self.stack.append({"tag": tag, "id": attr_map.get("id") or "", "classes": classes, "is_cite": is_cite})
        if tag == "span" and "ahnen" in classes:
            self.ahnen_depth = 1
            self.ahnen_context = self.context_id()
            self.ahnen_parts = []
        if is_cite:
            self.cite_depth += 1
            self.cite_context = self.context_id()
        if self.cite_depth and tag == "a":
            href = attr_map.get("href") or ""
            if href.startswith("#"):
                self.links.append((html_lib.unescape(href[1:]), self.cite_context or self.context_id()))
            else:
                self.links.append((href, self.cite_context or self.context_id()))

    def handle_endtag(self, tag: str) -> None:
        while self.stack:
            entry = self.stack.pop()
            if self.ahnen_depth:
                self.ahnen_depth -= 1
                if not self.ahnen_depth:
                    label = normalize_label("".join(self.ahnen_parts))
                    if self.ahnen_context:
                        self.person_labels[self.ahnen_context] = label
                    self.ahnen_context = ""
                    self.ahnen_parts = []
            if entry["is_cite"]:
                self.cite_depth -= 1
                self.cite_context = ""
            if entry["tag"] == tag:
                break

    def handle_data(self, data: str) -> None:
        if self.ahnen_depth:
            self.ahnen_parts.append(data)


def attr_id(attrs: str) -> str:
    match = ID_RE.search(attrs)
    if not match:
        return ""
    return match.group(1) or match.group(2) or ""


def source_ids(section: str) -> list[str]:
    return [attr_id(match.group("attrs")) for match in LI_RE.finditer(section)]


def validate_source_ids(ids: list[str]) -> set[str]:
    failures = [f"{li_id or '(missing)'} != s{i}" for i, li_id in enumerate(ids, start=1) if li_id != f"s{i}"]
    if failures:
        print("Source Ledger anchors must be sequential sNN ids:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        raise SystemExit(1)
    return set(ids)


def citations_by_source(html: str) -> dict[str, list[str]]:
    parser = CitationParser()
    parser.feed(html)
    citations: dict[str, list[str]] = {}
    bad_targets: list[str] = []
    for target, context in parser.links:
        if not SN_RE.fullmatch(target):
            bad_targets.append(target or "(missing)")
        if not context:
            print(f"citation to {target or '(missing)'} has no person/case context", file=sys.stderr)
            raise SystemExit(1)
        label = parser.label_for(context)
        citations.setdefault(target, [])
        if label not in citations[target]:
            citations[target].append(label)
    if bad_targets:
        print("citation hrefs must target #sNN ledger anchors:", file=sys.stderr)
        for target in bad_targets:
            print(f"  {target}", file=sys.stderr)
        raise SystemExit(1)
    return citations


def recompute(html: str) -> str:
    section_match = SOURCE_SECTION_RE.search(html)
    if not section_match:
        print("Source Ledger section not found", file=sys.stderr)
        raise SystemExit(1)
    section = section_match.group(1)
    citations = citations_by_source(html)
    if not citations:
        print("no citation chips found", file=sys.stderr)
        raise SystemExit(1)

    ledger_ids = validate_source_ids(source_ids(section))
    missing = sorted(source_id for source_id in citations if source_id not in ledger_ids)
    if missing:
        print("citation targets missing from Source Ledger:", file=sys.stderr)
        for source_id in missing:
            print(f"  {source_id}", file=sys.stderr)
        raise SystemExit(1)

    def replace_li(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        body = GENERATED_RE.sub("", match.group("body"))
        li_id = attr_id(attrs)
        suffix = ""
        if li_id in citations:
            cited_by = ", ".join(html_lib.escape(label, quote=False) for label in citations[li_id])
            suffix = f' <span data-g>→ {cited_by}</span>'
        return f"<li{attrs}>{body}{suffix}</li>"

    fresh_section = LI_RE.sub(replace_li, section)
    return html[: section_match.start(1)] + fresh_section + html[section_match.end(1) :]


def main() -> int:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--check", action="store_true", help="fail if generated backlinks differ")
    args = arg_parser.parse_args()

    original = HTML_PATH.read_text()
    rendered = recompute(original)
    if args.check:
        if original != rendered:
            print(f"{HTML_PATH} citation backlinks are out of date; run uv run tools/build_citation_backlinks.py", file=sys.stderr)
            return 1
        print(f"{HTML_PATH} citation backlinks are current")
        return 0

    HTML_PATH.write_text(rendered)
    print(f"updated {HTML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
