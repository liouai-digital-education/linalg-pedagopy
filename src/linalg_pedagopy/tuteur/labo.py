"""Backward-compatible re-export of linalg_pedagopy.tutor.lab."""

from __future__ import annotations

from linalg_pedagopy.tutor.lab import (
    CounterexampleLab,
    LabReport,
    _eval_math_predicate,
    _structured_vector_candidates,
)

__all__ = [
    "CounterexampleLab",
    "LabReport",
    "_eval_math_predicate",
    "_structured_vector_candidates",
]
