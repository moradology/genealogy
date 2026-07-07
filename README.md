# Zimmerman-Dible Genealogy

Static working artifact for the Zimmerman-Dible ancestry research.

## Files

- `index.html` - shareable browser artifact.
- `ancestry_geospatial.geojson` - machine-readable temporal and family-link geography records.

## Local Checks

```sh
python3 -m json.tool ancestry_geospatial.geojson >/dev/null
python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path

class Parser(HTMLParser):
    pass

parser = Parser()
parser.feed(Path("index.html").read_text())
parser.close()
print("html parse ok")
PY
```

## Hosted Site

GitHub Pages: https://moradology.github.io/genealogy/
