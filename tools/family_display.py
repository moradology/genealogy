#!/usr/bin/env python3
"""Shared render seams for the family page projection.

Store prose is plain unicode carrying the {{...}} token grammar owned by
check_family_core (validated at store time). Rendering happens here, once:
text escapes via html.escape(quote=False), tokens expand to the page's exact
byte shapes (including the historical unquoted-attribute cite anchors), and
dom_stream() canonicalizes any fragment to an event list so migrations can
prove DOM-equivalence where byte identity is impossible. Builders import
these functions; nothing here reads or writes index.html.
"""

from __future__ import annotations

import html as html_module
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import family_rules  # noqa: E402
from check_family_core import TOKEN_RE  # noqa: E402

SOURCES_PATH = "research/sources/sources.jsonl"
TAG_LABELS = {"documented": "Documented", "strong": "Strong lead",
              "lead": "Working lead", "open": "Open edge"}


def fail(message: str) -> NoReturn:
    print(message)
    raise SystemExit(1)


def _escape(value: str) -> str:
    return html_module.escape(value, quote=False)


def _attr(value: str) -> str:
    return html_module.escape(value, quote=True)


def cite_map(root: Path) -> dict[str, str]:
    """src.* id -> positional sN ledger code, validated against row order."""
    mapping: dict[str, str] = {}
    path = root / SOURCES_PATH
    for position, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        source_id = row.get("id")
        html_id = row.get("html_id")
        if not isinstance(source_id, str) or not source_id:
            fail(f"{path} line {position}: missing source id")
        if html_id != f"s{position}":
            fail(f"{path} line {position}: html_id {html_id!r} != s{position}")
        mapping[source_id] = html_id
    return mapping


def render_prose(value: str, cite_codes: dict[str, str],
                 known_anchors: set[str] | None = None) -> str:
    parts: list[str] = []
    cursor = 0
    for match in TOKEN_RE.finditer(value):
        parts.append(_escape(value[cursor: match.start()]))
        token = match.group(0)[2:-2]
        if token == "vs":
            parts.append('<span class="vs">vs.</span>')
        elif token.startswith("cite:"):
            source_id = token[len("cite:"):]
            if source_id not in cite_codes:
                fail(f"cite token {source_id!r} does not resolve in sources.jsonl")
            code = cite_codes[source_id]
            parts.append(f"<a class=cite href=#{code}>{code}</a>")
        elif token.startswith("case:"):
            case_id = token[len("case:"):]
            parts.append(f'<a class="case-chip" href="#{case_id}">{case_id}</a>')
        elif token.startswith("link:"):
            target, label = token[len("link:"):].split("|", 1)
            if known_anchors is not None and target[1:] not in known_anchors:
                fail(f"link token targets unknown anchor {target[1:]!r}")
            parts.append(f'<a href="{target}">{_escape(label)}</a>')
        else:
            url, label = token[len("url:"):].split("|", 1)
            parts.append(f'<a href="{_attr(url)}">{_escape(label)}</a>')
        cursor = match.end()
    parts.append(_escape(value[cursor:]))
    return "".join(parts)


def registry_groups(entries: list[dict]) -> dict[str, list[dict]]:
    """Registry entries grouped by their card anchor (the 'h' field)."""
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        anchor = entry.get("h")
        if isinstance(anchor, str) and anchor:
            groups.setdefault(anchor, []).append(entry)
    return groups


def entry_slots(entry: dict) -> list[int]:
    slots = entry.get("ah")
    if not isinstance(slots, list):
        return []
    return [slot for slot in slots
            if isinstance(slot, int) and not isinstance(slot, bool)]


def derived_title(members: list[dict]) -> str | None:
    """Rule: slotted members' display names joined ' + ' in slot order."""
    slotted = [member for member in members if entry_slots(member)]
    ordered = sorted(
        slotted, key=lambda member: (min(entry_slots(member)),
                                     members.index(member)))
    if not ordered:
        ordered = members
    names = [member.get("n") for member in ordered
             if isinstance(member.get("n"), str)]
    return " + ".join(names) if names else None


def derived_ahnen(members: list[dict]) -> str | None:
    """Rule: branch code + every member slot through ahnen_label."""
    slots: list[int] = []
    branch = None
    for member in members:
        if branch is None and isinstance(member.get("a"), str):
            branch = member["a"]
        slots.extend(entry_slots(member))
    if branch is None:
        return None
    return ahnen_label(branch, slots)


def ahnen_label(branch: str, slots: list[int]) -> str | None:
    """Z-1, M-4·5, D-16·20, Z-24–27; None when the row holds no slots."""
    if not slots:
        return None
    ordered = sorted(slots)
    runs: list[list[int]] = []
    for slot in ordered:
        if runs and slot == runs[-1][1] + 1:
            runs[-1][1] = slot
        else:
            runs.append([slot, slot])
    parts: list[str] = []
    for start, end in runs:
        if end - start >= 2:
            parts.append(f"{start}–{end}")
        else:
            parts.extend(str(value) for value in range(start, end + 1))
    return f"{branch}-" + "·".join(parts)


def render_record_card(evidence_id: str, display: dict, anchor_class: str) -> str:
    head = _escape(display["head"])
    cite_line = _escape(display["cite"])
    if display["variant"] == "roll":
        rows: list[str] = []
        for row in display["roll"]:
            focal = ' class="focal"' if row.get("focal") else ""
            cells = "".join(f"<td>{_escape(cell)}</td>" for cell in row["cells"])
            rows.append(f"<tr{focal}>{cells}</tr>")
        body = ('<table class="record-roll"><tbody>' + "".join(rows)
                + "</tbody></table>")
    else:
        entries: list[str] = []
        for field in display["fields"]:
            focal = ' class="focal"' if field.get("focal") else ""
            entries.append(f"<div{focal}><dt>{_escape(field['dt'])}</dt>"
                           f"<dd>{_escape(field['dd'])}</dd></div>")
        body = '<dl class="record-fields">' + "".join(entries) + "</dl>"
    return (f'<figure class="record-card anchor-{anchor_class}" '
            f'data-evidence-id="{evidence_id}">'
            f'<figcaption class="record-head">{head}</figcaption>'
            f'{body}<p class="record-cite">{cite_line}</p></figure>')


def render_person_card(*, row_id: str, title_html: str, ahnen_text: str,
                       tag: str, display: dict, cite_map: dict[str, str],
                       known_anchors: set[str] | None = None,
                       record_cards_html: str = "",
                       alias_ids: tuple = ()) -> str:
    if tag not in TAG_LABELS:
        fail(f"{row_id}: unknown confidence tag {tag!r}")
    parts = [f'<div class="person" id="{row_id}">']
    for alias in alias_ids:
        parts.append(f'<span id="{alias}"></span>')
    parts.append('<div class="person-head">'
                 f'<span class="person-name">{title_html}</span> '
                 f'<span class="ahnen">{ahnen_text}</span> '
                 f'<span class="tag {tag}">{TAG_LABELS[tag]}</span></div>')
    vitals = display.get("vitals")
    if vitals:
        parts.append(f'<div class="vitals">'
                     f"{render_prose(vitals, cite_map, known_anchors)}</div>")
    parts.append(f'<p class="identity">'
                 f"{render_prose(display['identity'], cite_map, known_anchors)}</p>")
    cameos = "".join(
        '<figure class="cameo">'
        f'<img src="{_attr(cameo["src"])}" alt="{_attr(cameo["alt"])}" '
        f'width="{cameo["width"]}" height="{cameo["height"]}" loading="lazy">'
        f'<figcaption><a href="{_attr(cameo["credit_url"])}">'
        f'{_escape(cameo["credit_label"])}</a></figcaption></figure>'
        for cameo in display.get("cameos") or [])
    parts.append(f'<div class="person-details">{cameos}'
                 f"{render_prose(display['details'], cite_map, known_anchors)}</div>")
    parts.append(record_cards_html)
    parts.append("</div>")
    return "".join(parts)


TAG_STRIP_RE = re.compile(r"<[^>]+>")


def visible_text(fragment: str) -> str:
    """Collapse a fragment to its space-normalized, entity-decoded text."""
    return " ".join(html_module.unescape(TAG_STRIP_RE.sub(" ", fragment)).split())


def stem_short_name(row: dict, people: dict[str, dict], person_id: str) -> str:
    override = (row.get("short_names") or {}).get(person_id)
    if isinstance(override, str) and override:
        return override
    return people[person_id]["display_name"].split()[0]


def render_stem(row: dict, people: dict[str, dict], links: list[dict]) -> str:
    """A descent stem: editorial words from the store row, confidence tag and
    weakest-step pair computed from the live relationship chain."""
    where = f"stems.jsonl {row['id']!r}"
    chains = family_rules.parent_chains(links, row["anchor"], row["target"])
    if not chains:
        fail(f"{where}: no upward parent chain from {row['anchor']} to {row['target']}")
    if len(chains) > 1:
        fail(f"{where}: {len(chains)} distinct chains from {row['anchor']} to "
             f"{row['target']}; stems require exactly one")
    for link in chains[0]:
        if link.get("status") != "accepted":
            fail(f"{where}: chain link {link.get('id')!r} has status "
                 f"{link.get('status')!r}; a descent stem may only claim a "
                 "fully accepted chain")
    weakest = family_rules.weakest_parent_step(chains[0])
    confidence = weakest.get("confidence")
    if confidence not in TAG_LABELS:
        fail(f"{where}: weakest link {weakest.get('id')!r} has unknown "
             f"confidence {confidence!r}")
    pair = (f"{_escape(stem_short_name(row, people, weakest['person_b']))}"
            f"–{_escape(stem_short_name(row, people, weakest['person_a']))}")
    note = f"weakest step: {pair}"
    suffix = row.get("note_suffix")
    if suffix:
        note += f", {_escape(suffix)}"
    href = "#" + people[row["target"]]["public_anchor"]
    return (
        '<div class="stem"><span class="stem-label">descent</span> '
        f'{_escape(row["from_label"])} <span class="stem-arrow">→</span> '
        f'{_escape(row["via_prose"])} <a href="{href}">{_escape(row["link_text"])}</a> '
        f'<span class="stem-arrow">→</span> {_escape(row["line_label"])} '
        f'<span class="tag {confidence}">{TAG_LABELS[confidence]}</span> '
        f'<span class="stem-note">{note}</span></div>'
    )


class _StreamParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[tuple] = []

    def handle_starttag(self, tag, attrs):
        self.events.append(("start", tag, tuple(sorted(attrs))))

    def handle_startendtag(self, tag, attrs):
        self.events.append(("start", tag, tuple(sorted(attrs))))

    def handle_endtag(self, tag):
        self.events.append(("end", tag))

    def handle_data(self, data):
        if self.events and self.events[-1][0] == "text":
            self.events[-1] = ("text", self.events[-1][1] + data)
        else:
            self.events.append(("text", data))

    def handle_comment(self, data):
        # Generated-region markers are invisible to DOM equivalence.
        return


def dom_stream(fragment: str) -> list[tuple]:
    """Canonical event stream: entity/unicode and attribute order invisible."""
    parser = _StreamParser()
    parser.feed(fragment)
    parser.close()
    return parser.events
