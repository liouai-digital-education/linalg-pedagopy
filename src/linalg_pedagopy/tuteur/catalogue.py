"""Backward-compatible re-export of linalg_pedagopy.tutor.catalog, session and validation."""

from __future__ import annotations

from linalg_pedagopy.tutor.catalog import (
    catalog,
    catalogue,
    ExerciseCatalog,
    glossaire,
    glossary,
    list_exercises,
    lister_exercices,
    mode,
    recharger_catalogue,
    reload_catalog,
    THEMES,
    themes,
)
from linalg_pedagopy.tutor.session import (
    exercice,
    ExerciceSession,
    exercise,
    ExerciseSession,
)
from linalg_pedagopy.tutor.validation import (
    validate_sheet,
    ValidationReport,
    valider_fiche,
)

__all__ = [
    "catalog",
    "catalogue",
    "exercice",
    "ExerciceSession",
    "exercise",
    "ExerciseCatalog",
    "ExerciseSession",
    "glossaire",
    "glossary",
    "list_exercises",
    "lister_exercices",
    "mode",
    "recharger_catalogue",
    "reload_catalog",
    "THEMES",
    "themes",
    "validate_sheet",
    "ValidationReport",
    "valider_fiche",
]
