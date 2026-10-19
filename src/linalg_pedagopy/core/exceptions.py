"""Hiérarchie des exceptions du package linalg_pedagopy."""

from __future__ import annotations

from typing import Any


class PedagopyError(Exception):
    """Base de toutes les exceptions du package linalg_pedagopy."""


class DimensionMismatchError(PedagopyError, ValueError):
    """Opération entre objets mathématiques de tailles incompatibles."""


class InexactInputError(PedagopyError, ValueError):
    """Flottant refusé lorsque float_policy='reject'."""


class UndecidableZeroError(PedagopyError, ArithmeticError):
    """Verdict UNKNOWN de l'oracle de nullité sans hypothèse fournie."""

    def __init__(self, expr: Any, message: str | None = None) -> None:
        self.expr = expr
        msg = message or (
            f"Impossible de décider formellement si l'expression {expr!r} est nulle. "
            "Fournissez une hypothèse explicite (assumptions=...)."
        )
        super().__init__(msg)


class SingularMatrixError(PedagopyError, ArithmeticError):
    """Inversion ou résolution demandée sur une matrice singulière en mode strict."""

    def __init__(self, message: str = "La matrice est singulière.", *, rank: int | None = None) -> None:
        self.rank = rank
        super().__init__(message)


class LinearDependenceError(PedagopyError, ArithmeticError):
    """Famille liée détectée en mode strict ; porte le témoin de dépendance linéaire."""

    def __init__(
        self,
        message: str = "La famille de vecteurs est linéairement dépendante.",
        *,
        index: int | None = None,
        witness: Any = None,
    ) -> None:
        self.index = index
        self.witness = witness
        super().__init__(message)


class RankDeficientError(PedagopyError, ArithmeticError):
    """Moindres carrés ou factorisation QR avec une matrice non de rang plein en colonnes."""

    def __init__(
        self,
        message: str = "La matrice n'est pas de rang plein en colonnes.",
        *,
        rank: int | None = None,
        ncols: int | None = None,
    ) -> None:
        self.rank = rank
        self.ncols = ncols
        super().__init__(message)


class UndefinedOperationError(PedagopyError, ArithmeticError):
    """Opération mathématiquement non définie (ex. angle avec un vecteur nul, division par zéro)."""


class LockedExerciseDataError(PedagopyError, PermissionError):
    """Tentative de calcul direct sur les données verrouillées d'un exercice du tuteur."""


class UnknownExerciseError(PedagopyError, LookupError):
    """Exercice introuvable dans le catalogue du tuteur (identifiant, numéro ou titre inconnu)."""
