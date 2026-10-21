"""Tests de caractérisation des campagnes du bac à sable (étape 3.1 du plan v6).

Chaque cas de ``tests/campagnes.py`` est figé dans ``tests/references/campagnes/`` : discussion
de cas, explications en texte aux niveaux 0 à 3, ou message d'erreur quand un plafond est
atteint. Ces références servent de filet de sécurité pour l'extraction du moteur (phase 4)
et rendent visibles les corrections voulues des étapes 3.2 à 3.5.

Les cas lents (> 5 s) portent la marque ``lent`` : ``pytest -m "not lent"`` les écarte.
Régénération après un changement voulu : LP_MAJ_REFERENCES=1 pytest tests/test_caracterisation_campagnes.py
"""

from __future__ import annotations

import warnings
from typing import Any

import pytest

from linalg_pedagopy import CaseSplit, PedagogicalWarning, PedagopyError

from ._references import bloc, verifier_reference
from .campagnes import CAS_CAMPAGNES, Cas


def rendu(cas: Cas) -> str:
    parts = [bloc("carnet", f"{cas.carnet} — {cas.description}")]
    with warnings.catch_warnings(record=True) as avertis:
        warnings.simplefilter("always", PedagogicalWarning)
        try:
            res: Any = cas.calcul()
        except PedagopyError as err:
            res = err
    for w in avertis:
        if issubclass(w.category, PedagogicalWarning):
            parts.append(bloc("avertissement", str(w.message)))
    if isinstance(res, PedagopyError):
        parts.append(bloc("erreur", f"{type(res).__name__} : {res}"))
        return "\n".join(parts)
    parts.append(bloc("repr", repr(res)))
    if isinstance(res, CaseSplit):
        parts.append(bloc("str", str(res)))
    for lvl in (0, 1, 2, 3):
        parts.append(bloc(f"texte niveau {lvl}", res.explain(level=lvl).to_text()))
    return "\n".join(parts)


@pytest.mark.parametrize(
    "nom",
    [pytest.param(nom, marks=pytest.mark.lent) if cas.lent else nom for nom, cas in sorted(CAS_CAMPAGNES.items())],
)
def test_caracterisation_campagne(nom: str) -> None:
    verifier_reference(f"campagnes/{nom}", rendu(CAS_CAMPAGNES[nom]))
