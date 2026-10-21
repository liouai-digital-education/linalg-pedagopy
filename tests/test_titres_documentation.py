"""Les titres des guides sont les mêmes partout : H1 de la page, README, accueil et site.

Le H1 de chaque guide ``docs/NN_*.md`` est la seule source de son titre : le générateur du
site le reprend (onglet, navigation, recherche) et le retire du corps, si bien que chaque page
publiée n'a qu'un titre de niveau 1. Le README et l'accueil le citent tel quel.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
DOCS = RACINE / "docs"
GUIDES = sorted(DOCS.glob("[0-9][0-9]_*.md"))


def titres_h1(page: Path) -> list[str]:
    """Titres de niveau 1 de ``page``, hors blocs de code (où « # » ouvre un commentaire)."""
    titres: list[str] = []
    dans_code = False
    for ligne in page.read_text(encoding="utf-8").splitlines():
        if ligne.lstrip().startswith("```"):
            dans_code = not dans_code
        elif not dans_code and ligne.startswith("# "):
            titres.append(ligne[2:].strip())
    return titres


def texte_du_lien(page: Path, cible: str) -> list[str]:
    """Textes des liens de ``page`` vers ``cible`` (gras retiré)."""
    texte = page.read_text(encoding="utf-8")
    return [t.strip("*") for t in re.findall(r"\[([^\]]+)\]\(" + re.escape(cible) + r"\)", texte)]


@pytest.mark.parametrize("guide", GUIDES, ids=lambda p: p.name)
def test_un_seul_h1_numerote(guide: Path) -> None:
    titres = titres_h1(guide)
    assert len(titres) == 1, titres
    assert titres[0].startswith(guide.name[:2] + ". "), titres[0]


@pytest.mark.parametrize("guide", GUIDES, ids=lambda p: p.name)
def test_readme_et_accueil_citent_le_titre(guide: Path) -> None:
    (titre,) = titres_h1(guide)
    # Un guide peut aussi être cité dans le texte (« guide 09 ») ; la liste des guides donne le titre.
    assert titre in texte_du_lien(RACINE / "README.md", f"docs/{guide.name}")
    assert titre in texte_du_lien(DOCS / "index.md", guide.name)


def test_chaque_page_du_site_a_un_seul_h1() -> None:
    pages = [DOCS / "site" / "index.html", *(DOCS / "site" / g.with_suffix(".html").name for g in GUIDES)]
    nombres = {p.name: p.read_text(encoding="utf-8").count("<h1") for p in pages}
    assert all(n == 1 for n in nombres.values()), nombres
