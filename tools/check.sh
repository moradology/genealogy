#!/bin/sh
# Single local gate. CI runs this same script.
# Note: never name a shell variable 'status' (read-only alias in zsh).
set -e
cd "$(dirname "$0")/.."

uv run python -c "import json; json.load(open('ancestry_geospatial.geojson')); print('geojson ok')"
uv run python -c "import json; json.load(open('research/sources/source-index.json')); print('source-index ok')"
uv run tools/build_source_index.py --check
uv run tools/check_refs.py

INLINE_JS="$(mktemp -t genealogy_inline.XXXXXX.js)"
export INLINE_JS
uv run python - <<'PY'
import os
import re
from pathlib import Path
html = Path("index.html").read_text()
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
joined = "\n;\n".join(block for block in scripts if block.strip())
Path(os.environ["INLINE_JS"]).write_text(joined)
print(f"extracted {len(scripts)} inline script blocks")
PY
node --check "$INLINE_JS"
rm -f "$INLINE_JS"
echo "inline js parses"

if [ -d node_modules/playwright ]; then
  node tools/acceptance_spec.js
else
  echo "SKIPPED acceptance spec: run 'npm ci' first to install pinned playwright" >&2
  exit 1
fi
