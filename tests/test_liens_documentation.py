"""Les liens relatifs de la documentation pointent vers des fichiers qui existent.

Un renommage de page (par exemple les guides passés en noms français) casse sans bruit les
liens qui la citent. Ce test parcourt les liens Markdown ``[texte](cible)`` des pages
versionnées, hors blocs de code, et vérifie que chaque cible relative existe. Les liens
externes (http, https, mailto) et les ancres seules (``#section``) ne sont pas vérifiés.
Côté site, aucun lien vers une page de la documentation ne doit rester en ``.md``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
PAGES = sorted(
    [
        RACINE / "README.md",
        RACINE / "TUTORIAL.md",
        RACINE / "CHANGELOG.md",
        *(RACINE / "docs").glob("*.md"),
        *(RACINE / "docs" / "dev").rglob("*.md"),
        *RACINE.glob("CONTRIBUTING.md"),
    ]
)
LIEN = re.compile(r"\]\(([^)\s]+)\)")
CLOTURE = re.compile(r"^\s*(```|~~~)")


def liens_relatifs(page: Path) -> list[tuple[int, str]]:
    """(numéro de ligne, cible) des liens relatifs de ``page``, hors blocs de code."""
    trouves: list[tuple[int, str]] = []
    dans_code = False
    for numero, ligne in enumerate(page.read_text(encoding="utf-8").splitlines(), start=1):
        if CLOTURE.match(ligne):
            dans_code = not dans_code
            continue
        if dans_code:
            continue
        for cible in LIEN.findall(re.sub(r"`[^`]*`", "", ligne)):
            if cible.startswith(("http://", "https://", "mailto:", "#")):
                continue
            trouves.append((numero, cible))
    return trouves


@pytest.mark.parametrize("page", PAGES, ids=lambda p: str(p.relative_to(RACINE)).replace("\\", "/"))
def test_liens_relatifs_valides(page: Path) -> None:
    casses = [
        f"ligne {numero} : {cible}"
        for numero, cible in liens_relatifs(page)
        if not (page.parent / cible.split("#", 1)[0]).exists()
    ]
    assert not casses, "liens vers des fichiers absents :\n" + "\n".join(casses)


def test_site_sans_lien_md_vers_les_guides() -> None:
    restants = [
        f"{fichier.name} : {lien}"
        for fichier in sorted((RACINE / "docs" / "site").glob("*.html"))
        for lien in re.findall(r'href="(\d\d_[\w-]+\.md[^"]*)"', fichier.read_text(encoding="utf-8"))
    ]
    assert not restants, "liens .md non convertis dans le site :\n" + "\n".join(restants)
