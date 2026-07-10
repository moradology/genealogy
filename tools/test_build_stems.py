#!/usr/bin/env python3
"""Acceptance checks for the descent-stem projection builder (tools/build_stems.py).

Offline, stdlib only, no try/except. Exercises bootstrap marker-ization, write,
--check, and error paths against a synthetic fixture repo via --root, in the
same style as test_build_docket.py. Run: uv run tools/test_build_stems.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "tools/build_stems.py"
failures: list[str] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        failures.append(f"{name}: {detail}")


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BUILDER), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


def person(pid: str, name: str, anchor: str | None = None) -> dict:
    return {
        "id": pid, "node_type": "person", "display_name": name,
        "index_names": [name], "name_variants": [], "branches": ["zimmerman"],
        "role": "ancestor", "confidence": "strong", "privacy": "public_deceased",
        "public_anchor": anchor or pid,
    }


def plink(parent: str, child: str, role: str, confidence: str = "documented",
          status: str = "accepted") -> dict:
    return {
        "id": f"relationship.parent.{parent.split('.')[-1]}-to-{child.split('.')[-1]}",
        "node_type": "relationship", "relationship_type": "parent_of",
        "person_a": parent, "person_b": child, "parent_role": role,
        "status": status, "confidence": confidence, "branches": ["zimmerman"],
        "evidence_refs": [], "source_refs": ["src.test.x"], "case_refs": [],
        "provenance_note": "test",
    }


def stem_row(sid: str, anchor: str, target: str, line_label: str,
             note_suffix: str | None = None, short_names: dict | None = None,
             via: str = "mother") -> dict:
    row = {
        "id": sid, "node_type": "stem", "anchor": anchor, "target": target,
        "from_label": "Anna A. Anchor", "via_prose": via,
        "link_text": "Linked Target", "line_label": line_label,
    }
    if note_suffix is not None:
        row["note_suffix"] = note_suffix
    if short_names is not None:
        row["short_names"] = short_names
    return row


PEOPLE = [
    person("person.a", "Anna Alpha Anchor"),
    person("person.m", "Mira Middle"),
    person("person.t", "Tessa Target"),
    person("person.t2", "Willa Second"),
]
LINKS = [
    plink("person.m", "person.a", "father", confidence="documented"),
    plink("person.t", "person.m", "mother", confidence="strong"),
    plink("person.t2", "person.a", "mother", confidence="documented"),
]
# Two hand-authored stems in current page style: entities, no markers.
HAND_STEMS = (
    '<div class="stem"><span class="stem-label">descent</span> Anna A. Anchor '
    '<span class="stem-arrow">&rarr;</span> father Mira Middle, then grandmother '
    '<a href="#person.t">Linked Target</a> <span class="stem-arrow">&rarr;</span> '
    'this line <span class="tag strong">Strong lead</span> '
    '<span class="stem-note">weakest step: Mira&ndash;Tessa</span></div>',
    '<div class="stem"><span class="stem-label">descent</span> Anna A. Anchor '
    '<span class="stem-arrow">&rarr;</span> mother '
    '<a href="#person.t2">Linked Target</a> <span class="stem-arrow">&rarr;</span> '
    'the Second line <span class="tag documented">Documented</span> '
    '<span class="stem-note">weakest step: Ann&ndash;Willa, obituary</span></div>',
)


def make_root(tmp: Path, stems: list[dict], hand_stems: tuple = HAND_STEMS,
              links: list[dict] | None = None) -> Path:
    root = tmp / "repo"
    (root / "research" / "people").mkdir(parents=True)
    jl = lambda rows: "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)  # noqa: E731
    (root / "research" / "people" / "people.jsonl").write_text(jl(PEOPLE), encoding="utf-8")
    (root / "research" / "people" / "relationships.jsonl").write_text(
        jl(links if links is not None else LINKS), encoding="utf-8")
    (root / "research" / "people" / "stems.jsonl").write_text(jl(stems), encoding="utf-8")
    body = "\n".join(
        f'<div class="generation"><div class="gen-label">Gen {n}</div>'
        f'<div class="people">{stem}</div></div>'
        for n, stem in enumerate(hand_stems, start=1))
    (root / "index.html").write_text(
        f"<html><head></head><body>\n<section id=\"branch-test\">\n{body}\n"
        "</section>\n</body></html>\n", encoding="utf-8")
    return root


STORE_ROWS = [
    stem_row("stem.a.two-hop", "person.a", "person.t", "this line",
             via="father Mira Middle, then grandmother"),
    stem_row("stem.a.one-hop", "person.a", "person.t2", "the Second line",
             note_suffix="obituary", short_names={"person.a": "Ann"}),
]


with tempfile.TemporaryDirectory(prefix="build-stems-test-") as td:
    tmp = Path(td)

    # 1. Bootstrap: marker-izes the two hand stems, normalizes entities,
    #    computes tags and weakest-step notes from the chain
    root = make_root(tmp / "boot", STORE_ROWS)
    result = run(root)
    html = (root / "index.html").read_text(encoding="utf-8")
    check("bootstrap exits 0", result.returncode == 0, result.stdout + result.stderr)
    check("bootstrap inserts keyed markers",
          html.count("<!-- BEGIN stem:stem.a.two-hop -->") == 1
          and html.count("<!-- BEGIN stem:stem.a.one-hop -->") == 1, html)
    check("bootstrap emits unicode arrows", "→" in html and "&rarr;" not in html, html)
    check("two-hop stem computes strong tag from weakest link",
          '<span class="tag strong">Strong lead</span>' in html, html)
    check("weakest-step pair uses first-word short names",
          "weakest step: Mira–Tessa</span>" in html, html)
    check("short_names override and note_suffix render",
          "weakest step: Ann–Willa, obituary</span>" in html, html)
    check("one-hop stem stays documented",
          '<span class="tag documented">Documented</span>' in html, html)
    check("href targets the public anchor", 'href="#person.t2"' in html, html)

    # 2. Idempotence + --check green
    before = (root / "index.html").read_bytes()
    result = run(root)
    check("second write is a no-op", result.returncode == 0
          and (root / "index.html").read_bytes() == before, result.stdout)
    result = run(root, "--check")
    check("check green after write", result.returncode == 0, result.stdout + result.stderr)

    # 3. Drift: a stems.jsonl edit reddens --check with remediation text
    rows = [dict(STORE_ROWS[0]), dict(STORE_ROWS[1])]
    rows[1]["line_label"] = "the Renamed line"
    (root / "research" / "people" / "stems.jsonl").write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows),
        encoding="utf-8")
    result = run(root, "--check")
    check("store edit reddens check", result.returncode == 1, result.stdout)
    check("check names the remediation", "./gen build stems" in result.stdout, result.stdout)
    result = run(root)
    check("rebuild after store edit", result.returncode == 0
          and "the Renamed line" in (root / "index.html").read_text(encoding="utf-8"),
          result.stdout)

    # 4. Drift: a RELATIONSHIP confidence edit alone reddens --check
    #    (documented -> lead on the weakest link flips tag, label, and note)
    weakened = [dict(l) for l in LINKS]
    weakened[2]["confidence"] = "lead"
    (root / "research" / "people" / "relationships.jsonl").write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in weakened),
        encoding="utf-8")
    result = run(root, "--check")
    check("confidence edit reddens check", result.returncode == 1, result.stdout)
    result = run(root)
    html = (root / "index.html").read_text(encoding="utf-8")
    check("weakened chain regenerates Working lead tag",
          '<span class="tag lead">Working lead</span>' in html, html)

    # 5. Error paths: zero bytes written
    bad = make_root(tmp / "bad-target",
                    [stem_row("stem.a.bad", "person.a", "person.nobody", "this line")])
    before = (bad / "index.html").read_bytes()
    result = run(bad)
    check("unknown target exits 1", result.returncode == 1, result.stdout + result.stderr)
    check("unknown target writes nothing", (bad / "index.html").read_bytes() == before)

    unreachable = make_root(
        tmp / "bad-chain",
        [stem_row("stem.a.unreachable", "person.t2", "person.t", "this line")])
    before = (unreachable / "index.html").read_bytes()
    result = run(unreachable)
    check("unreachable chain exits 1", result.returncode == 1, result.stdout + result.stderr)
    check("unreachable chain writes nothing",
          (unreachable / "index.html").read_bytes() == before)

    diamond_links = LINKS + [
        plink("person.m2", "person.a", "mother", confidence="documented"),
        plink("person.t", "person.m2", "father", confidence="documented"),
    ]
    ambiguous = make_root(
        tmp / "bad-diamond",
        [stem_row("stem.a.ambiguous", "person.a", "person.t", "this line")],
        links=diamond_links)
    result = run(ambiguous)
    check("ambiguous chain exits 1", result.returncode == 1, result.stdout + result.stderr)

    dup = make_root(tmp / "bad-dup", [STORE_ROWS[0], STORE_ROWS[0]])
    result = run(dup)
    check("duplicate stem id exits 1", result.returncode == 1, result.stdout + result.stderr)

    # Bootstrap refusals: count mismatch and per-position target disagreement
    fewer = make_root(tmp / "bad-count", [STORE_ROWS[0]])
    before = (fewer / "index.html").read_bytes()
    result = run(fewer)
    check("bootstrap count mismatch exits 1", result.returncode == 1, result.stdout)
    check("bootstrap count mismatch writes nothing",
          (fewer / "index.html").read_bytes() == before)

    swapped = make_root(tmp / "bad-order", [STORE_ROWS[1], STORE_ROWS[0]])
    result = run(swapped)
    check("bootstrap order mismatch exits 1", result.returncode == 1, result.stdout)

    # 6. Raw HTML in store text is rejected
    tainted = make_root(tmp / "bad-lint",
                        [stem_row("stem.a.tainted", "person.a", "person.t2",
                                  "the <b>bold</b> line")])
    result = run(tainted)
    check("raw html in store text exits 1", result.returncode == 1,
          result.stdout + result.stderr)

    # 7. Splice safety: a hand-deleted END marker must refuse, never over-splice
    root = make_root(tmp / "no-end", STORE_ROWS)
    run(root)
    html_path = root / "index.html"
    marked = html_path.read_text(encoding="utf-8")
    begin = "<!-- BEGIN stem:stem.a.two-hop -->"
    start = marked.index(begin)
    end_at = marked.index("<!-- END -->", start)
    html_path.write_text(marked[:end_at] + marked[end_at + len("<!-- END -->"):],
                         encoding="utf-8")
    before = html_path.read_bytes()
    result = run(root)
    check("missing END refuses", result.returncode == 1, result.stdout + result.stderr)
    check("missing END writes nothing", html_path.read_bytes() == before)

    # Duplicate BEGIN for one key also refuses
    html_path.write_text(
        marked + '<!-- BEGIN stem:stem.a.two-hop --><div class="stem">x</div>'
        "<!-- END -->", encoding="utf-8")
    result = run(root)
    check("duplicate marker key refuses", result.returncode == 1,
          result.stdout + result.stderr)

    # 8. Bootstrap same-target swap: href order agrees but the words do not
    swapped_hand = (
        '<div class="stem"><span class="stem-label">descent</span> Anna A. Anchor '
        '<span class="stem-arrow">→</span> mother <a href="#person.t2">Linked Target</a> '
        '<span class="stem-arrow">→</span> line A <span class="tag documented">Documented</span> '
        '<span class="stem-note">weakest step: Ann–Willa, obituary</span></div>',
        '<div class="stem"><span class="stem-label">descent</span> Anna A. Anchor '
        '<span class="stem-arrow">→</span> mother <a href="#person.t2">Linked Target</a> '
        '<span class="stem-arrow">→</span> line B <span class="tag documented">Documented</span> '
        '<span class="stem-note">weakest step: Ann–Willa, obituary</span></div>',
    )
    swap_rows = [
        stem_row("stem.same.one", "person.a", "person.t2", "line B",
                 note_suffix="obituary", short_names={"person.a": "Ann"}),
        stem_row("stem.same.two", "person.a", "person.t2", "line A",
                 note_suffix="obituary", short_names={"person.a": "Ann"}),
    ]
    swap = make_root(tmp / "bad-swap", swap_rows, hand_stems=swapped_hand)
    before = (swap / "index.html").read_bytes()
    result = run(swap)
    check("bootstrap same-target swap refuses", result.returncode == 1,
          result.stdout + result.stderr)
    check("bootstrap swap writes nothing", (swap / "index.html").read_bytes() == before)
    aligned = make_root(tmp / "good-swap", list(reversed(swap_rows)),
                        hand_stems=swapped_hand)
    result = run(aligned)
    check("bootstrap aligned same-target pair succeeds", result.returncode == 0,
          result.stdout + result.stderr)

    # 9. A non-accepted link in the chain refuses: no Documented claim over a
    # hypothesis edge
    hypothesis_links = [dict(l) for l in LINKS]
    hypothesis_links[2]["status"] = "hypothesis"
    hypo = make_root(tmp / "bad-status", [STORE_ROWS[1]],
                     hand_stems=(HAND_STEMS[1],), links=hypothesis_links)
    result = run(hypo)
    check("hypothesis chain link refuses", result.returncode == 1
          and "accepted" in result.stdout, result.stdout + result.stderr)

    # 10. Stem ids follow the canonical grammar
    bad_id = stem_row("stem.same.one", "person.a", "person.t2", "this line")
    bad_id["id"] = "stem.bad id"
    result = run(make_root(tmp / "bad-id", [bad_id]))
    check("malformed stem id refuses", result.returncode == 1,
          result.stdout + result.stderr)

if failures:
    print("BUILD STEMS TEST FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("build_stems: all contract checks passed")
