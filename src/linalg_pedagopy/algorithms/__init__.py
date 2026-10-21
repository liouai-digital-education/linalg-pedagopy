"""Algorithmes et procédures pédagogiques tracées (Couche 3)."""

from __future__ import annotations

from linalg_pedagopy.algorithms.base import (
    AffineSolution,
    EmptySolution,
    Procedure,
    Result,
    SolutionSet,
    UniqueSolution,
)
from linalg_pedagopy.algorithms.determinant import Determinant, DetResult
from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan, GJResult
from linalg_pedagopy.algorithms.gram_schmidt import (
    DependenceWitness,
    GramSchmidt,
    GSResult,
)
from linalg_pedagopy.algorithms.least_squares import LeastSquares, LSResult
from linalg_pedagopy.algorithms import products as _products  # noqa: F401  (enregistre matmul, gram…)
from linalg_pedagopy.algorithms.qr import QR, QRResult
from linalg_pedagopy.algorithms.triangular import (
    BackSubstitution,
    ForwardSubstitution,
    TriangularResult,
)

__all__ = [
    "AffineSolution",
    "BackSubstitution",
    "DependenceWitness",
    "DetResult",
    "Determinant",
    "EmptySolution",
    "ForwardSubstitution",
    "GJResult",
    "GSResult",
    "GaussJordan",
    "GramSchmidt",
    "LSResult",
    "LeastSquares",
    "Procedure",
    "QR",
    "QRResult",
    "Result",
    "SolutionSet",
    "TriangularResult",
    "UniqueSolution",
]
