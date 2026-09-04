import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_app_version_matches_citation():
    cff = (ROOT / "CITATION.cff").read_text()
    cff_version = re.search(r'^version:\s*"([^"]+)"', cff, re.M).group(1)

    app_source = (ROOT / "app.py").read_text()
    app_version = re.search(r'^version = "([^"]+)"', app_source, re.M).group(1)

    assert app_version == cff_version
