"""Compatibilité : le tuteur s'appelle désormais ``linalg_pedagopy.tuteur``.

``linalg_pedagopy.tutor`` et ses sous-modules (``catalog``, ``session``, ``validation``,
``hints``, ``journal``, ``lab``, ``lock``, ``panel``, ``registry``, ``verifiers``) réexportent les
noms de ``tuteur``. Ils seront signalés par un ``DeprecationWarning`` en 0.3.2.0 et supprimés
en 0.4.0.0.
"""

from __future__ import annotations

# Les sous-modules sont chargés d'abord : chargés plus tard, ils remplaceraient l'attribut du
# même nom (le module tutor.catalog masquerait la fonction tutor.catalog).
from linalg_pedagopy.tutor import (  # noqa: F401
    catalog as _catalog,
    hints as _hints,
    journal as _journal,
    lab as _lab,
    lock as _lock,
    panel as _panel,
    registry as _registry,
    session as _session,
    validation as _validation,
    verifiers as _verifiers,
)
from linalg_pedagopy.tuteur import *  # noqa: E402, F403
from linalg_pedagopy.tuteur import __all__  # noqa: E402, F401
