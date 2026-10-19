"""Générateurs d'exercices à résultats propres et sessions interactives (Couche 5)."""

from __future__ import annotations

from linalg_pedagopy.exercises.checkers import (
    OperationFeedback,
    ProposalStatus,
    check_gram_schmidt_step,
    check_row_operation,
)
from linalg_pedagopy.exercises.generators import (
    TwinExercise,
    cayley_orthogonal,
    generate_clean_least_squares,
    generate_integer_rref_matrix,
    generate_parametric_system,
    generate_rational_qr_matrix,
    generate_unimodular_matrix,
    generateurs,
)
from linalg_pedagopy.exercises.interactive import InteractiveMode, InteractiveSession

__all__ = [
    "InteractiveMode",
    "InteractiveSession",
    "OperationFeedback",
    "ProposalStatus",
    "TwinExercise",
    "cayley_orthogonal",
    "check_gram_schmidt_step",
    "check_row_operation",
    "generate_clean_least_squares",
    "generate_integer_rref_matrix",
    "generate_parametric_system",
    "generate_rational_qr_matrix",
    "generate_unimodular_matrix",
    "generateurs",
]
