"""Trace arborescente contextuelle (Couche 1)."""

from __future__ import annotations

from linalg_pedagopy.trace.step import Highlight, Step, StepKind
from linalg_pedagopy.trace.tracer import (
    Tracer,
    current_tracer,
    record,
    section,
    suspend_tracing,
    tracing,
)

__all__ = [
    "Highlight",
    "Step",
    "StepKind",
    "Tracer",
    "current_tracer",
    "record",
    "section",
    "suspend_tracing",
    "tracing",
]
