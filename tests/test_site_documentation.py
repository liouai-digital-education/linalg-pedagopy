"""Le site de documentation généré (docs/site/) ne contient pas de jeton de protection non restitué.

scripts/build_docs_site.py remplace formules et diagrammes par des jetons pendant la conversion
Markdown, puis les restitue ; un jeton résiduel s'afficherait tel quel dans la page publiée.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parent.parent / "docs" / "site"
FICHIERS = sorted([*SITE.glob("*.html"), SITE / "assets" / "js" / "search_index.json"])
JETON = re.compile(r"academic_token|acadtok\d+z", re.IGNORECASE)


def test_le_site_est_present() -> None:
    assert len(FICHIERS) >= 10


@pytest.mark.parametrize("fichier", FICHIERS, ids=lambda p: p.name)
def test_aucun_jeton_residuel(fichier: Path) -> None:
    texte = fichier.read_text(encoding="utf-8")
    trouve = JETON.search(texte)
    assert trouve is None, (
        f"jeton non restitué : {texte[max(0, trouve.start() - 60):trouve.end() + 20]!r} "
        "(régénérer avec python scripts/build_docs_site.py)"
    )
