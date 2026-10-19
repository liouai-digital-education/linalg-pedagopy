"""Backward-compatible re-export of linalg_pedagopy.tutor.catalog."""

from __future__ import annotations

from linalg_pedagopy.tutor.catalog import (
    ExerciceSession,
    ExerciseSession,
    ValidationReport,
    exercice,
    exercise,
    glossaire,
    glossary,
    list_exercises,
    lister_exercices,
    mode,
    validate_sheet,
    valider_fiche,
)

__all__ = [
    "ExerciceSession",
    "ExerciseSession",
    "ValidationReport",
    "exercice",
    "exercise",
    "glossaire",
    "glossary",
    "list_exercises",
    "lister_exercices",
    "mode",
    "validate_sheet",
    "valider_fiche",
]
