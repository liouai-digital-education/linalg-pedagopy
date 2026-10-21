"""Chaque élément public du paquet a une docstring.

La définition d'« élément public » est celle de ``scripts/mesurer_docstrings.py`` (modules, classes,
fonctions et méthodes sans « _ » initial, dans des modules publics), chargé ici par son chemin.
Pour voir l'état du paquet : ``python scripts/mesurer_docstrings.py --liste``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "mesurer_docstrings.py"
_spec = importlib.util.spec_from_file_location("mesurer_docstrings", SCRIPT)
assert _spec is not None and _spec.loader is not None
mesure = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mesure)


def test_les_elements_publics_sont_nombreux() -> None:
    # Garde-fou : une erreur de parcours (mauvais dossier) donnerait un test vide et vert.
    assert len(mesure.elements_publics()) > 400


def test_chaque_element_public_a_une_docstring() -> None:
    manquants = mesure.sans_docstring()
    assert not manquants, "éléments publics sans docstring :\n" + "\n".join(manquants)
