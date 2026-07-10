#!/usr/bin/env python3
"""Extract hand-authored family card display blocks from index.html."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = Path("index.html")
PEOPLE_PATH = Path("research/people/people.jsonl")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import family_display  # noqa: E402
from check_family_core import TOKEN_RE  # noqa: E402

VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
     "meta", "param", "source", "track", "wbr"}
)
SCRIPT_RE = re.compile(
    r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.I | re.S
)
ATTR_RE = re.compile(
    r"(?P<name>[A-Za-z_:][\w:.-]*)"
    r"(?:\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\s>]+)))?"
)
STEM_BEGIN_RE = re.compile(r"\A\s*BEGIN\s+stem:([A-Za-z0-9._-]+)\s*\Z")


def fail(message: str) -> NoReturn:
    print(message)
    raise SystemExit(1)


def element_node(tag: str, attrs: list[tuple[str, str | None]]) -> dict[str, Any]:
    return {
        "type": "element",
        "tag": tag,
        "attrs": {name: value if value is not None else "" for name, value in attrs},
        "children": [],
    }


def text_node(data: str) -> dict[str, Any]:
    return {"type": "text", "data": data}


def comment_node(data: str) -> dict[str, Any]:
    return {"type": "comment", "data": data}


class TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = element_node("__root__", [])
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = element_node(tag, attrs)
        self.stack[-1]["children"].append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1]["children"].append(element_node(tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        for position in range(len(self.stack) - 1, 0, -1):
            if self.stack[position]["tag"] == tag:
                del self.stack[position:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1]["children"].append(text_node(data))

    def handle_comment(self, data: str) -> None:
        self.stack[-1]["children"].append(comment_node(data))


def attrs(raw: str) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for match in ATTR_RE.finditer(raw):
        value = match.group("double")
        if value is None:
            value = match.group("single")
        if value is None:
            value = match.group("bare")
        values[match.group("name").lower()] = value
    return values


def people_index(source: str) -> list[dict[str, Any]]:
    matches = []
    for match in SCRIPT_RE.finditer(source):
        if attrs(match.group("attrs")).get("id") == "people-index":
            matches.append(match)
    if len(matches) != 1:
        fail(f"extract_family_display: expected one #people-index script, found {len(matches)}")
    payload = json.loads(matches[0].group("body"))
    if not isinstance(payload, dict) or not isinstance(payload.get("people"), list):
        fail("extract_family_display: #people-index JSON must contain a people list")
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in payload["people"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("i"), str):
            fail("extract_family_display: #people-index entry missing string i")
        entry_id = entry["i"]
        if entry_id in seen:
            fail(f"extract_family_display: duplicate #people-index entry {entry_id}")
        seen.add(entry_id)
        entries.append(entry)
    return entries


def read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        fail(f"extract_family_display: missing canonical store: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            fail(f"extract_family_display: {path}:{line_number}: blank JSONL line")
        row = json.loads(line)
        if not isinstance(row, dict):
            fail(f"extract_family_display: {path}:{line_number}: row must be an object")
        rows.append(row)
    return rows


def parse_tree(source: str) -> dict[str, Any]:
    parser = TreeParser()
    parser.feed(source)
    parser.close()
    return parser.root


def class_set(node: dict[str, Any]) -> set[str]:
    value = node.get("attrs", {}).get("class", "")
    return set(str(value).split())


def has_class(node: dict[str, Any], class_name: str) -> bool:
    return class_name in class_set(node)


def node_id(node: dict[str, Any]) -> str | None:
    value = node.get("attrs", {}).get("id")
    return value if isinstance(value, str) and value else None


def element_children(node: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        child for child in node.get("children", [])
        if child.get("type") == "element"
    ]


def text_content(node: dict[str, Any]) -> str:
    if node["type"] == "text":
        return node["data"]
    if node["type"] == "comment":
        return ""
    return "".join(text_content(child) for child in node.get("children", []))


def inner_html(node: dict[str, Any]) -> str:
    return "".join(serialize(child) for child in node.get("children", []))


def serialize(node: dict[str, Any]) -> str:
    kind = node["type"]
    if kind == "text":
        return html.escape(node["data"], quote=False)
    if kind == "comment":
        return "<!--" + node["data"] + "-->"
    tag = node["tag"]
    attrs_text = "".join(
        f' {name}="{html.escape(str(value), quote=True)}"'
        for name, value in node.get("attrs", {}).items()
    )
    if tag in VOID_TAGS:
        return f"<{tag}{attrs_text}>"
    return f"<{tag}{attrs_text}>{inner_html(node)}</{tag}>"


def find_descendants(
    node: dict[str, Any],
    *,
    tag: str | None = None,
    class_name: str | None = None,
    id_value: str | None = None,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for child in element_children(node):
        if (
            (tag is None or child["tag"] == tag)
            and (class_name is None or has_class(child, class_name))
            and (id_value is None or node_id(child) == id_value)
        ):
            found.append(child)
        found.extend(
            find_descendants(child, tag=tag, class_name=class_name, id_value=id_value)
        )
    return found


def direct_child(
    node: dict[str, Any], tag: str, class_name: str | None = None
) -> dict[str, Any] | None:
    for child in element_children(node):
        if child["tag"] == tag and (class_name is None or has_class(child, class_name)):
            return child
    return None


def nonblank_children(node: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for child in node.get("children", []):
        if child["type"] == "text" and child["data"].strip() == "":
            continue
        if child["type"] == "comment":
            continue
        result.append(child)
    return result


def plain_text_from_children(
    children: list[dict[str, Any]], row_id: str, construct: str, refusals: list[str]
) -> str:
    parts: list[str] = []
    for child in children:
        if child["type"] == "text":
            parts.append(child["data"])
        elif child["type"] == "comment":
            continue
        else:
            refusals.append(f"{row_id}: {construct} contains unexpected <{child['tag']}>")
    return "".join(parts)


def anchor_label(node: dict[str, Any], row_id: str, field: str, refusals: list[str]) -> str:
    return plain_text_from_children(node.get("children", []), row_id, field, refusals)


def prose_token_ok(value: str) -> bool:
    stripped = TOKEN_RE.sub("", value)
    return "<" not in value and "{" not in stripped and "}" not in stripped


def validate_prose_tokens(
    block: dict[str, Any], row_id: str, refusals: list[str]
) -> None:
    for field in ("identity", "details", "vitals", "card_name", "title_override",
                  "ahnen_override"):
        value = block.get(field)
        if isinstance(value, str) and not prose_token_ok(value):
            refusals.append(f"{row_id}: display.{field} is outside TOKEN grammar")


def reverse_prose(
    children: list[dict[str, Any]],
    row_id: str,
    field: str,
    source_by_code: dict[str, str],
    refusals: list[str],
) -> str:
    parts: list[str] = []
    for child in children:
        kind = child["type"]
        if kind == "text":
            parts.append(child["data"])
            continue
        if kind == "comment":
            continue
        tag = child["tag"]
        if tag == "a":
            classes = class_set(child)
            href = child.get("attrs", {}).get("href", "")
            label = anchor_label(child, row_id, f"{field} anchor", refusals)
            if "cite" in classes:
                code = href[1:] if href.startswith("#") else href
                source_id = source_by_code.get(code)
                if source_id is None:
                    refusals.append(f"{row_id}: {field} cite anchor {href!r} is unknown")
                else:
                    parts.append(f"{{{{cite:{source_id}}}}}")
            elif "case-chip" in classes:
                if href.startswith("#") and href[1:]:
                    parts.append(f"{{{{case:{href[1:]}}}}}")
                else:
                    refusals.append(f"{row_id}: {field} case-chip has invalid href {href!r}")
            elif classes:
                refusals.append(f"{row_id}: {field} anchor has unexpected classes {sorted(classes)}")
            elif href.startswith("#") and href[1:]:
                parts.append(f"{{{{link:{href}|{label}}}}}")
            elif href.startswith(("http://", "https://")):
                parts.append(f"{{{{url:{href}|{label}}}}}")
            else:
                refusals.append(f"{row_id}: {field} anchor has unsupported href {href!r}")
            continue
        if tag == "span" and class_set(child) == {"vs"}:
            parts.append("{{vs}}")
            continue
        refusals.append(f"{row_id}: {field} contains unexpected <{tag}>")
    return "".join(parts)


def extract_cameo(
    node: dict[str, Any], row_id: str, refusals: list[str]
) -> dict[str, Any]:
    children = nonblank_children(node)
    img = children[0] if children and children[0].get("tag") == "img" else None
    caption = children[1] if len(children) > 1 and children[1].get("tag") == "figcaption" else None
    if img is None or caption is None or len(children) != 2:
        refusals.append(f"{row_id}: cameo figure must contain img and figcaption")
        return {}
    link_children = nonblank_children(caption)
    link = link_children[0] if link_children and link_children[0].get("tag") == "a" else None
    if link is None or len(link_children) != 1:
        refusals.append(f"{row_id}: cameo figcaption must contain one credit link")
        return {}
    attrs_map = img["attrs"]
    width = attrs_map.get("width", "")
    height = attrs_map.get("height", "")
    if not str(width).isdigit() or not str(height).isdigit():
        refusals.append(f"{row_id}: cameo image width and height must be integers")
        return {}
    credit_url = link["attrs"].get("href", "")
    if not str(credit_url).startswith(("http://", "https://")):
        refusals.append(f"{row_id}: cameo credit link must be an http(s) URL")
    return {
        "src": attrs_map.get("src", ""),
        "alt": attrs_map.get("alt", ""),
        "width": int(str(width)),
        "height": int(str(height)),
        "credit_url": credit_url,
        "credit_label": anchor_label(link, row_id, "cameo credit", refusals),
    }


def extract_record_roll(
    table: dict[str, Any], row_id: str, refusals: list[str]
) -> list[dict[str, Any]]:
    tbody = direct_child(table, "tbody")
    rows_parent = tbody if tbody is not None else table
    rows: list[dict[str, Any]] = []
    for child in nonblank_children(rows_parent):
        if child.get("tag") != "tr":
            refusals.append(f"{row_id}: record-roll contains unexpected <{child.get('tag')}>")
            continue
        cells: list[str] = []
        for cell in nonblank_children(child):
            if cell.get("tag") != "td":
                refusals.append(f"{row_id}: record-roll row contains unexpected <{cell.get('tag')}>")
                continue
            cells.append(plain_text_from_children(cell.get("children", []), row_id, "record cell", refusals))
        entry: dict[str, Any] = {"cells": cells}
        if has_class(child, "focal"):
            entry["focal"] = True
        rows.append(entry)
    return rows


def extract_record_fields(
    dl: dict[str, Any], row_id: str, refusals: list[str]
) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for item in nonblank_children(dl):
        if item.get("tag") != "div":
            refusals.append(f"{row_id}: record-fields contains unexpected <{item.get('tag')}>")
            continue
        dt = direct_child(item, "dt")
        dd = direct_child(item, "dd")
        if dt is None or dd is None:
            refusals.append(f"{row_id}: record-fields entry must contain dt and dd")
            continue
        entry: dict[str, Any] = {
            "dt": plain_text_from_children(dt.get("children", []), row_id, "record dt", refusals),
            "dd": plain_text_from_children(dd.get("children", []), row_id, "record dd", refusals),
        }
        if has_class(item, "focal"):
            entry["focal"] = True
        fields.append(entry)
    return fields


def anchor_class_for_card(node: dict[str, Any], row_id: str, refusals: list[str]) -> str:
    anchors = [
        class_name.removeprefix("anchor-")
        for class_name in class_set(node)
        if class_name.startswith("anchor-")
    ]
    if len(anchors) != 1:
        refusals.append(f"{row_id}: record-card must have one anchor-* class")
        return ""
    return anchors[0]


def extract_record_card(
    node: dict[str, Any], row_id: str, refusals: list[str]
) -> tuple[str, dict[str, Any], str]:
    evidence_id = node.get("attrs", {}).get("data-evidence-id", "")
    if not evidence_id:
        refusals.append(f"{row_id}: record-card missing data-evidence-id")
    anchor_class = anchor_class_for_card(node, row_id, refusals)
    head_node = direct_child(node, "figcaption", "record-head")
    cite_node = direct_child(node, "p", "record-cite")
    table = direct_child(node, "table", "record-roll")
    fields = direct_child(node, "dl", "record-fields")
    if head_node is None or cite_node is None:
        refusals.append(f"{row_id}: record-card missing head or cite")
    if (table is None) == (fields is None):
        refusals.append(f"{row_id}: record-card must contain exactly one body variant")
    display: dict[str, Any] = {
        "variant": "roll" if table is not None else "fields",
        "head": "" if head_node is None else plain_text_from_children(
            head_node.get("children", []), row_id, "record head", refusals
        ),
        "cite": "" if cite_node is None else plain_text_from_children(
            cite_node.get("children", []), row_id, "record cite", refusals
        ),
    }
    if table is not None:
        display["roll"] = extract_record_roll(table, row_id, refusals)
    if fields is not None:
        display["fields"] = extract_record_fields(fields, row_id, refusals)
    return evidence_id, display, anchor_class


def store_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row.get("id")
        if isinstance(row_id, str):
            by_id[row_id] = row
    return by_id


def registry_groups(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        anchor = entry.get("h")
        if isinstance(anchor, str) and anchor:
            groups.setdefault(anchor, []).append(entry)
    return groups


def entry_slots(entry: dict[str, Any]) -> list[int]:
    slots = entry.get("ah")
    if not isinstance(slots, list):
        return []
    return [slot for slot in slots if isinstance(slot, int) and not isinstance(slot, bool)]


def sorted_slotted_members(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slotted = [member for member in members if entry_slots(member)]
    return sorted(slotted, key=lambda member: (min(entry_slots(member)), members.index(member)))


def derived_title(members: list[dict[str, Any]]) -> str | None:
    ordered = sorted_slotted_members(members)
    if not ordered:
        ordered = members
    names = [member.get("n") for member in ordered if isinstance(member.get("n"), str)]
    return " + ".join(names) if names else None


def derived_ahnen(members: list[dict[str, Any]]) -> str | None:
    slots: list[int] = []
    branch = None
    for member in members:
        if branch is None and isinstance(member.get("a"), str):
            branch = member["a"]
        slots.extend(entry_slots(member))
    if branch is None:
        return None
    return family_display.ahnen_label(branch, slots)


def tag_class(head: dict[str, Any], row_id: str, refusals: list[str]) -> str:
    tag_span = direct_child(head, "span", "tag")
    if tag_span is None:
        refusals.append(f"{row_id}: person-head missing tag span")
        return ""
    candidates = sorted(class_set(tag_span) & set(family_display.TAG_LABELS))
    if len(candidates) != 1:
        refusals.append(f"{row_id}: tag span must carry one confidence class")
        return ""
    return candidates[0]


def expected_tag(
    row_id: str, store_people: dict[str, dict[str, Any]], refusals: list[str]
) -> str:
    if row_id.startswith("gap."):
        return "open"
    row = store_people.get(row_id)
    if row is None:
        refusals.append(f"{row_id}: missing store person row")
        return ""
    confidence = row.get("confidence")
    if not isinstance(confidence, str):
        refusals.append(f"{row_id}: store person row missing confidence")
        return ""
    return confidence


def extract_aliases(
    children: list[dict[str, Any]], row_id: str, refusals: list[str]
) -> tuple[list[str], list[dict[str, Any]]]:
    aliases: list[str] = []
    remaining: list[dict[str, Any]] = []
    consuming = True
    for child in children:
        if child["type"] == "text" and child["data"].strip() == "":
            continue
        if consuming and child["type"] == "element" and child["tag"] == "span":
            alias = node_id(child)
            if alias and not class_set(child) and text_content(child) == "":
                aliases.append(alias)
                continue
        consuming = False
        if child["type"] != "comment":
            remaining.append(child)
    return aliases, remaining


def extract_details(
    details_node: dict[str, Any],
    row_id: str,
    source_by_code: dict[str, str],
    refusals: list[str],
) -> tuple[str, list[dict[str, Any]]]:
    children = details_node.get("children", [])
    cursor = 0
    cameos: list[dict[str, Any]] = []
    while cursor < len(children):
        child = children[cursor]
        if child["type"] == "text" and child["data"].strip() == "":
            cursor += 1
            continue
        if child["type"] == "element" and child["tag"] == "figure" and has_class(child, "cameo"):
            cameo = extract_cameo(child, row_id, refusals)
            if cameo:
                cameos.append(cameo)
            cursor += 1
            continue
        break
    for later in children[cursor:]:
        if later["type"] == "element" and later["tag"] == "figure" and has_class(later, "cameo"):
            refusals.append(f"{row_id}: cameo figure appears after details prose begins")
    details = reverse_prose(children[cursor:], row_id, "details", source_by_code, refusals)
    return details, cameos


def extract_row(
    row: dict[str, Any],
    store_people: dict[str, dict[str, Any]],
    groups: dict[str, list[dict[str, Any]]],
    cite_codes: dict[str, str],
    source_by_code: dict[str, str],
    refusals: list[str],
) -> tuple[str, dict[str, Any], dict[str, dict[str, Any]], list[tuple[str, str]]]:
    row_id = node_id(row) or ""
    if not row_id:
        refusals.append("person row missing id")
        return "", {}, {}, []
    aliases, children = extract_aliases(row.get("children", []), row_id, refusals)
    head = next(
        (child for child in children if child.get("type") == "element"
         and child.get("tag") == "div" and has_class(child, "person-head")),
        None,
    )
    if head is None:
        refusals.append(f"{row_id}: missing person-head")
        return row_id, {}, {}, []
    name_span = direct_child(head, "span", "person-name")
    ahnen_span = direct_child(head, "span", "ahnen")
    if name_span is None or ahnen_span is None:
        refusals.append(f"{row_id}: person-head missing name or ahnen span")
        return row_id, {}, {}, []
    page_tag = tag_class(head, row_id, refusals)
    wanted_tag = expected_tag(row_id, store_people, refusals)
    if page_tag and wanted_tag and page_tag != wanted_tag:
        refusals.append(f"{row_id}: page tag {page_tag!r} != store confidence {wanted_tag!r}")

    vitals_node = next(
        (child for child in children if child.get("type") == "element"
         and child.get("tag") == "div" and has_class(child, "vitals")),
        None,
    )
    identity_node = next(
        (child for child in children if child.get("type") == "element"
         and child.get("tag") == "p" and has_class(child, "identity")),
        None,
    )
    details_node = next(
        (child for child in children if child.get("type") == "element"
         and child.get("tag") == "div" and has_class(child, "person-details")),
        None,
    )
    if identity_node is None or details_node is None:
        refusals.append(f"{row_id}: missing identity or person-details")
        return row_id, {}, {}, []

    block: dict[str, Any] = {
        "identity": reverse_prose(identity_node.get("children", []), row_id, "identity", source_by_code, refusals),
    }
    if vitals_node is not None:
        block["vitals"] = reverse_prose(vitals_node.get("children", []), row_id, "vitals", source_by_code, refusals)
    details, cameos = extract_details(details_node, row_id, source_by_code, refusals)
    block["details"] = details
    if cameos:
        block["cameos"] = cameos
    if aliases:
        block["alias_anchors"] = aliases

    members = groups.get(row_id, [])
    page_title_text = text_content(name_span)
    page_ahnen_text = text_content(ahnen_span)
    rule_title = derived_title(members)
    rule_ahnen = derived_ahnen(members)
    if rule_title is not None and page_title_text != rule_title:
        block["title_override"] = reverse_prose(
            name_span.get("children", []), row_id, "title", source_by_code, refusals
        )
    if rule_ahnen is not None and page_ahnen_text != rule_ahnen:
        block["ahnen_override"] = page_ahnen_text
    if rule_ahnen is None and page_ahnen_text:
        block["ahnen_override"] = page_ahnen_text

    evidence: dict[str, dict[str, Any]] = {}
    card_refs: list[tuple[str, str]] = []
    for child in children:
        if child.get("type") == "element" and child.get("tag") == "figure" and has_class(child, "record-card"):
            evidence_id, display, anchor_class = extract_record_card(child, row_id, refusals)
            if evidence_id:
                evidence[evidence_id] = display
                card_refs.append((evidence_id, anchor_class))
    if card_refs:
        block["record_cards"] = [evidence_id for evidence_id, _anchor in card_refs]
    validate_prose_tokens(block, row_id, refusals)

    original = serialize(row)
    record_cards_html = "".join(
        family_display.render_record_card(evidence_id, evidence[evidence_id], anchor_class)
        for evidence_id, anchor_class in card_refs
        if evidence_id in evidence
    )
    rendered = family_display.render_person_card(
        row_id=row_id,
        title_html=inner_html(name_span),
        ahnen_text=page_ahnen_text,
        tag=page_tag or wanted_tag,
        display=block,
        cite_map=cite_codes,
        record_cards_html=record_cards_html,
        alias_ids=tuple(aliases),
    )
    if family_display.dom_stream(rendered) != family_display.dom_stream(original):
        refusals.append(f"{row_id}: extracted display block fails DOM round-trip")
    return row_id, block, evidence, card_refs


def section_node(root: dict[str, Any], section_id: str) -> dict[str, Any] | None:
    matches = find_descendants(root, tag="section", id_value=section_id)
    return matches[0] if matches else None


def person_rows_in_section(section: dict[str, Any]) -> list[dict[str, Any]]:
    return find_descendants(section, tag="div", class_name="person")


def extract_layout(section: dict[str, Any], section_id: str, refusals: list[str]) -> list[dict[str, Any]]:
    branches = find_descendants(section, tag="div", class_name="branch")
    if not branches:
        refusals.append(f"{section_id}: no div.branch blocks found")
        return []
    blocks: list[dict[str, Any]] = []
    for position, branch in enumerate(branches, start=1):
        where = f"{section_id} branch {position}"
        generations_nodes = find_descendants(branch, tag="div", class_name="generations")
        if len(generations_nodes) != 1:
            refusals.append(
                f"{where}: expected one div.generations, found {len(generations_nodes)}")
            blocks.append({"section": section_id, "branch": position, "generations": []})
            continue
        generations: list[dict[str, Any]] = []
        for gen in element_children(generations_nodes[0]):
            if gen["tag"] != "div" or not has_class(gen, "generation"):
                continue
            label_node = direct_child(gen, "div", "gen-label")
            people_node = direct_child(gen, "div", "people")
            if label_node is None or people_node is None:
                refusals.append(f"{where}: generation missing label or people container")
                continue
            items: list[str] = []
            for child in people_node.get("children", []):
                if child["type"] == "text" and child["data"].strip() == "":
                    continue
                if child["type"] == "comment":
                    match = STEM_BEGIN_RE.fullmatch(child["data"])
                    if match:
                        items.append(match.group(1))
                    continue
                if child["type"] != "element":
                    continue
                if child["tag"] == "div" and has_class(child, "person"):
                    row_id = node_id(child)
                    if row_id:
                        items.append(row_id)
                    else:
                        refusals.append(f"{where}: person row without id in layout")
                elif child["tag"] == "div" and has_class(child, "stem"):
                    continue
                else:
                    refusals.append(f"{where}: layout contains unexpected <{child['tag']}>")
            generations.append({"label": text_content(label_node), "items": items})
        blocks.append({"section": section_id, "branch": position, "generations": generations})
    return blocks


def empty_payload(refusals: list[str]) -> dict[str, Any]:
    return {"people": {}, "gaps": {}, "evidence": {}, "layout": [], "refusals": refusals}


def build_payload(root: Path, section_id: str) -> dict[str, Any]:
    html_path = root / HTML_PATH
    if not html_path.is_file():
        return empty_payload([f"missing presentation file: {html_path}"])
    source = html_path.read_text(encoding="utf-8")
    tree = parse_tree(source)
    section = section_node(tree, section_id)
    if section is None:
        return empty_payload([f"{section_id}: section not found"])

    registry = people_index(source)
    groups = registry_groups(registry)
    store_people = store_by_id(read_jsonl_objects(root / PEOPLE_PATH))
    cite_codes = family_display.cite_map(root)
    source_by_code = {code: source_id for source_id, code in cite_codes.items()}

    refusals: list[str] = []
    payload: dict[str, Any] = {
        "people": {},
        "gaps": {},
        "evidence": {},
        "layout": extract_layout(section, section_id, refusals),
        "refusals": refusals,
    }
    for row in person_rows_in_section(section):
        row_id, block, evidence, _card_refs = extract_row(
            row, store_people, groups, cite_codes, source_by_code, refusals
        )
        if not row_id or not block:
            continue
        if row_id.startswith("gap."):
            payload["gaps"][row_id] = block
        else:
            payload["people"][row_id] = block
        payload["evidence"].update(evidence)

    if refusals:
        return empty_payload(refusals)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--section", required=True)
    args = parser.parse_args(argv)
    payload = build_payload(args.root.resolve(), args.section)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 1 if payload["refusals"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
