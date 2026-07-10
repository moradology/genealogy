#!/bin/sh
# Single local gate. CI runs this same script.
# Note: never name a shell variable 'status' (read-only alias in zsh).
set -e
cd "$(dirname "$0")/.."

uv run python -c "import json; json.load(open('ancestry_geospatial.geojson')); print('geojson ok')"
uv run python -c "import json; json.load(open('research/sources/source-index.json')); print('source-index ok')"
uv run tools/build_source_index.py --check
uv run tools/build_citation_backlinks.py --check
uv run tools/check_family_core.py
uv run tools/test_check_family_core.py
uv run tools/build_people_index.py --check
uv run tools/test_build_people_index.py
uv run tools/check_evidence.py
uv run tools/test_check_evidence.py
uv run tools/check_cases.py
uv run tools/test_check_cases.py
uv run tools/check_traces.py
uv run tools/test_check_traces.py
uv run tools/check_refs.py
uv run tools/check_people_index.py
uv run tools/check_geo_sync.py
uv run tools/test_gen.py
uv run tools/test_gen_ancestry.py
uv run tools/test_gen_store.py
uv run tools/build_plate_keys.py --check
if [ -d tools/basemap-data ]; then
  uv run tools/build_basemap.py --check
else
  echo "note: tools/basemap-data absent; skipping basemap byte check (run build_basemap.py --check after basemap edits)"
fi
if [ -d tools/font-data ]; then
  uv run tools/build_fonts.py --check
else
  echo "note: tools/font-data absent; skipping font byte check (run build_fonts.py --check after text/font edits)"
fi
uv run tools/stamp.py --check

INLINE_DIR="$(mktemp -d)"
INLINE_JS="$INLINE_DIR/inline.js"
export INLINE_JS
uv run python - <<'PY'
import os
import re
from pathlib import Path
html = Path("index.html").read_text()
scripts = [content for attrs, content in
           re.findall(r"<script([^>]*)>(.*?)</script>", html, flags=re.S | re.I)
           if 'type="application/json"' not in attrs.lower()]
joined = "\n;\n".join(block for block in scripts if block.strip())
Path(os.environ["INLINE_JS"]).write_text(joined)
print(f"extracted {len(scripts)} inline script blocks")
PY
node --check "$INLINE_JS"
rm -rf "$INLINE_DIR"
echo "inline js parses"

if [ -d node_modules/playwright ]; then
  node tools/acceptance_spec.js
else
  echo "SKIPPED acceptance spec: run 'npm ci' first to install pinned playwright" >&2
  exit 1
fi
