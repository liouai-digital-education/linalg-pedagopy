"""Ce que le README et l'accueil de la documentation partagent reste identique.

Le README (vitrine sur GitHub) et ``docs/index.md`` (accueil du site) ont des rôles distincts,
mais deux passages doivent figurer dans les deux : l'installation, que chacun doit pouvoir
suivre seul, et l'attribution des exercices adaptés. Ce test empêche qu'ils divergent.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
README = (RACINE / "README.md").read_text(encoding="utf-8")
ACCUEIL = (RACINE / "docs" / "index.md").read_text(encoding="utf-8")


def bloc_installation(texte: str) -> str:
    """Premier bloc ```bash qui contient « pip install »."""
    for bloc in re.findall(r"```bash\n(.*?)```", texte, flags=re.DOTALL):
        if "pip install" in bloc:
            return str(bloc)
    raise AssertionError("aucun bloc d'installation")


def section(texte: str, titre: str) -> str:
    """Corps de la section de niveau 2 ``titre``, jusqu'au séparateur ou au titre suivant."""
    debut = texte.index(f"## {titre}\n")
    suite = re.search(r"\n(---|## )", texte[debut + 1 :])
    return texte[debut : debut + 1 + suite.start()].strip() if suite else texte[debut:].strip()


def test_meme_installation() -> None:
    assert bloc_installation(README) == bloc_installation(ACCUEIL)


def test_memes_remerciements() -> None:
    assert section(README, "Sources et remerciements") == section(ACCUEIL, "Sources et remerciements")
