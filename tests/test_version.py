"""La version du paquet est la même dans pyproject.toml et dans linalg_pedagopy.__version__."""

from __future__ import annotations

import re
from pathlib import Path

import linalg_pedagopy

RACINE = Path(__file__).resolve().parent.parent


def test_version_identique_dans_pyproject_et_le_paquet() -> None:
    texte = (RACINE / "pyproject.toml").read_text(encoding="utf-8")
    trouve = re.search(r'^version\s*=\s*"([^"]+)"', texte, re.MULTILINE)
    assert trouve is not None
    assert linalg_pedagopy.__version__ == trouve.group(1)
