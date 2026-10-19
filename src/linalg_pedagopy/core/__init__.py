"""Noyau formel de linalg_pedagopy (Couche 0)."""

from __future__ import annotations

from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    InexactInputError,
    LinearDependenceError,
    LockedExerciseDataError,
    UnknownExerciseError,
    PedagopyError,
    RankDeficientError,
    SingularMatrixError,
    UndecidableZeroError,
    UndefinedOperationError,
)
from linalg_pedagopy.core.field import choose_domain, symbols, to_exact
from linalg_pedagopy.core.zero import Verdict, ZeroDecision, ZeroOracle, oracle

__all__ = [
    "Branch",
    "CaseSplit",
    "Condition",
    "DimensionMismatchError",
    "InexactInputError",
    "LinearDependenceError",
    "LockedExerciseDataError",
    "UnknownExerciseError",
    "PedagopyError",
    "RankDeficientError",
    "SingularMatrixError",
    "UndecidableZeroError",
    "UndefinedOperationError",
    "Verdict",
    "ZeroDecision",
    "ZeroOracle",
    "choose_domain",
    "oracle",
    "symbols",
    "to_exact",
]
