"""Comparaison exact vs virgule flottante (Couche 5)."""

from __future__ import annotations

from linalg_pedagopy.compare.numeric import (
    ComparisonReport,
    HilbertEntry,
    HilbertReport,
    InverseVsSolveReport,
    LauchliGSReport,
    LauchliLSReport,
    build_hilbert_matrix,
    build_lauchli_matrix,
    compare,
    explicit_inverse_vs_solve_experiment,
    hilbert_conditioning_experiment,
    lauchli_gram_schmidt_experiment,
    lauchli_least_squares_experiment,
)

__all__ = [
    "ComparisonReport",
    "HilbertEntry",
    "HilbertReport",
    "InverseVsSolveReport",
    "LauchliGSReport",
    "LauchliLSReport",
    "build_hilbert_matrix",
    "build_lauchli_matrix",
    "compare",
    "explicit_inverse_vs_solve_experiment",
    "hilbert_conditioning_experiment",
    "lauchli_gram_schmidt_experiment",
    "lauchli_least_squares_experiment",
]
