#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools==4.58.4", "brotli==1.1.0"]
# ///
"""Rebuild the embedded font subsets baked into index.html.

Inputs are pinned to one immutable commit of google/fonts with a SHA256
per file, cached in tools/font-data/ (gitignored). Libre Caslon Text is
the [wght] variable font and the subset keeps the 400-700 axis (real
bold on the plates, not synthetic); IBM Plex Mono is the static Regular.

The glyph set is every character the document actually uses (data-URI
payloads stripped, HTML entities decoded) plus Polish and German
extras as future-content insurance for Westpreussen / Nowa Lubianka
grade names, plus a typographic quote/dash set. Subsetting drops
hinting and keeps kern/liga/ccmp/mark/mkmk; output is WOFF2. Each font
is built twice and compared to prove determinism before anything is
written.

Unlike build_basemap.py there is no historical byte parity to chase:
the blobs this tool replaced were unreproducible (unknown original
subset parameters), so this pipeline's own output became ground truth
at its landing commit, and --check gates from then on.

  ./gen build fonts --check              rebuild and byte-compare
  ./gen build fonts                      splice into index.html
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html as html_entities
import io
import re
import sys
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets/fonts.css"
# Glyph coverage comes from the rendered page text, not the asset file.
GLYPH_SOURCES = (ROOT / "index.html", ROOT / "assets/site.css",
                 ROOT / "assets/app.js")
CACHE = ROOT / "tools" / "font-data"

FONTS_COMMIT = "e4572de925a4c3be12f1f9983ee0adbe1eb6e9fe"
FONTS_BASE = f"https://raw.githubusercontent.com/google/fonts/{FONTS_COMMIT}"
FAMILIES = [
    {
        "family": "Libre Caslon Text",
        "path": "ofl/librecaslontext/LibreCaslonText%5Bwght%5D.ttf",
        "cache_name": "LibreCaslonText-wght.ttf",
        "sha256": "c11809dbfd5445886293d89b32bfc2584075c80e77750cf1c284113e36b8b3f4",
        "weight": "400 700",
    },
    {
        "family": "IBM Plex Mono",
        "path": "ofl/ibmplexmono/IBMPlexMono-Regular.ttf",
        "cache_name": "IBMPlexMono-Regular.ttf",
        "sha256": "6a3412f058c7d8dfd9170c41e85ade48e5156ecb89356110ca57a0a27734af46",
        "weight": "400",
    },
]

EXTRAS = (
    "ĄąĆćĘęŁłŃń"  # A/C/E/L/N-ogonek/acute/stroke
    "ÓóŚśŻżŹź"              # O-acute, S-acute, Z-dot, Z-acute
    "ÄäÖöÜüẞß"              # umlauts + sharp s
    "“”‘’‚„‹›«»"  # quotes
    "–—…·×° "                    # dashes, ellipsis, middot, degree, nbsp
)

LAYOUT_FEATURES = ["kern", "liga", "ccmp", "mark", "mkmk"]


def fetch(spec) -> Path:
    path = CACHE / spec["cache_name"]
    if path.exists():
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got == spec["sha256"]:
            return path
        print(f"cached {spec['cache_name']} has sha256 {got}; re-downloading", file=sys.stderr)
    CACHE.mkdir(parents=True, exist_ok=True)
    url = f"{FONTS_BASE}/{spec['path']}"
    print(f"downloading {url}")
    data = urllib.request.urlopen(url, timeout=120).read()
    got = hashlib.sha256(data).hexdigest()
    if got != spec["sha256"]:
        print(f"{spec['cache_name']}: downloaded sha256 {got} != pinned {spec['sha256']}", file=sys.stderr)
        raise SystemExit(1)
    path.write_bytes(data)
    return path


def glyph_text(html: str) -> str:
    stripped = re.sub(r"data:font/woff2;base64,[A-Za-z0-9+/=]+", "", html)
    decoded = html_entities.unescape(stripped)
    chars = {c for c in decoded if ord(c) >= 32}
    chars.update(EXTRAS)
    return "".join(sorted(chars))


def subset_woff2(ttf_path: Path, text: str) -> bytes:
    font = TTFont(str(ttf_path), recalcTimestamp=False)
    options = subset.Options()
    options.hinting = False
    options.layout_features = LAYOUT_FEATURES
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff2"
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def build() -> str:
    html = "".join(path.read_text() for path in GLYPH_SOURCES)
    text = glyph_text(html)
    print(f"glyph set: {len(text)} characters")
    lines = [
        "/* Embedded subsets of Libre Caslon Text and IBM Plex Mono (SIL OFL 1.1, via google/fonts). */"
    ]
    for spec in FAMILIES:
        path = fetch(spec)
        woff2 = subset_woff2(path, text)
        again = subset_woff2(path, text)
        if woff2 != again:
            print(f"{spec['family']}: two builds differ; refusing to write", file=sys.stderr)
            raise SystemExit(1)
        payload = base64.b64encode(woff2).decode()
        print(f"{spec['family']}: {len(woff2)} bytes woff2, {len(payload)} base64 chars")
        lines.append("@font-face {")
        lines.append(f'  font-family: "{spec["family"]}";')
        lines.append(f"  font-weight: {spec['weight']};")
        lines.append("  font-style: normal;")
        lines.append("  font-display: swap;")
        lines.append(f"  src: url(data:font/woff2;base64,{payload}) format(\"woff2\");")
        lines.append("}")
    return "\n".join(lines)


def region_bounds(html: str):
    begin = "/* BEGIN GENERATED fonts"
    end = "/* END GENERATED fonts */"
    if html.count(begin) != 1 or html.count(end) != 1:
        print("assets/fonts.css must contain exactly one BEGIN/END GENERATED fonts pair", file=sys.stderr)
        raise SystemExit(1)
    start = html.index("\n", html.index(begin)) + 1
    return start, html.index(end)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated = build()
    html = TARGET.read_text()
    start, stop = region_bounds(html)
    if args.check:
        current = html[start:stop].rstrip("\n")
        if current != generated:
            print("fonts: region differs from generator output; run ./gen build fonts", file=sys.stderr)
            return 1
        print(f"fonts: byte-identical ({stop - start} bytes)")
        return 0
    TARGET.write_text(html[:start] + generated + "\n" + html[stop:])
    print("index.html fonts region rewritten; run ./gen stamp --write next")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
