"""Fichiers de référence pour les tests de caractérisation.

Un test de caractérisation fige une sortie complète (trace, discussion de cas, diagnostic)
dans ``tests/references/<nom>.txt`` et vérifie à chaque exécution qu'elle n'a pas changé,
au caractère près. Ils servent de filet de sécurité pendant les refactorisations.

- Comparer : ``pytest``
- Régénérer après un changement **voulu** : ``LP_MAJ_REFERENCES=1 pytest`` (puis relire le diff git)
"""

from __future__ import annotations

import difflib
import os
from pathlib import Path

import pytest

REFERENCES = Path(__file__).resolve().parent / "references"


def _normaliser(texte: str) -> str:
    texte = texte.replace("\r\n", "\n")
    return texte if texte.endswith("\n") else texte + "\n"


def verifier_reference(nom: str, texte: str) -> None:
    """Compare ``texte`` au fichier de référence ``nom`` (ou l'écrit si LP_MAJ_REFERENCES=1)."""
    chemin = REFERENCES / f"{nom}.txt"
    texte = _normaliser(texte)
    if os.environ.get("LP_MAJ_REFERENCES") == "1":
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8", newline="\n")
        return
    if not chemin.exists():
        pytest.fail(
            f"Référence absente : {chemin.relative_to(REFERENCES.parent)}. "
            "Générez-la avec LP_MAJ_REFERENCES=1 pytest, puis relisez-la."
        )
    attendu = _normaliser(chemin.read_text(encoding="utf-8"))
    if texte != attendu:
        diff = list(
            difflib.unified_diff(
                attendu.splitlines(), texte.splitlines(), "référence", "obtenu", lineterm="", n=2
            )
        )
        extrait = "\n".join(diff[:80]) + ("\n…" if len(diff) > 80 else "")
        pytest.fail(f"La sortie de « {nom} » a changé :\n{extrait}")


def bloc(titre: str, contenu: object) -> str:
    """Formate une section d'un fichier de référence."""
    return f"===== {titre} =====\n{contenu}\n"
