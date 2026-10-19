"""linalg_pedagopy v3.0 — Package pédagogique d'algèbre linéaire formelle."""

from __future__ import annotations

import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure") and getattr(_stream, "encoding", "").lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from linalg_pedagopy.algorithms import (
    QR,
    AffineSolution,
    BackSubstitution,
    DependenceWitness,
    EmptySolution,
    ForwardSubstitution,
    GaussJordan,
    GJResult,
    GramSchmidt,
    GSResult,
    LeastSquares,
    LSResult,
    Procedure,
    QRResult,
    Result,
    SolutionSet,
    TriangularResult,
    UniqueSolution,
)
from linalg_pedagopy.compare import compare
from linalg_pedagopy.config import config, using_config
from linalg_pedagopy.core import (
    Branch,
    CaseSplit,
    Condition,
    DimensionMismatchError,
    InexactInputError,
    LinearDependenceError,
    LockedExerciseDataError,
    PedagopyError,
    RankDeficientError,
    SingularMatrixError,
    UndecidableZeroError,
    UndefinedOperationError,
    Verdict,
    ZeroDecision,
    ZeroOracle,
    choose_domain,
    oracle,
    symbols,
    to_exact,
)
from linalg_pedagopy.exercises import (
    InteractiveSession,
    cayley_orthogonal,
    check_gram_schmidt_step,
    check_row_operation,
    generate_clean_least_squares,
    generate_integer_rref_matrix,
    generate_parametric_system,
    generate_rational_qr_matrix,
    generate_unimodular_matrix,
    generateurs,
)
from linalg_pedagopy.objects import Matrix, Vector
from linalg_pedagopy.render import Explanation
from linalg_pedagopy.trace import (
    Highlight,
    Step,
    StepKind,
    Tracer,
    record,
    section,
    suspend_tracing,
    tracing,
)
from linalg_pedagopy import tuteur

__version__ = "3.0.0"

__all__ = [
    "__version__",
    "AffineSolution",
    "BackSubstitution",
    "Branch",
    "CaseSplit",
    "Condition",
    "DependenceWitness",
    "DimensionMismatchError",
    "EmptySolution",
    "Explanation",
    "ForwardSubstitution",
    "GJResult",
    "GSResult",
    "GaussJordan",
    "GramSchmidt",
    "Highlight",
    "InexactInputError",
    "InteractiveSession",
    "LSResult",
    "LeastSquares",
    "LinearDependenceError",
    "LockedExerciseDataError",
    "Matrix",
    "PedagopyError",
    "Procedure",
    "QR",
    "QRResult",
    "RankDeficientError",
    "Result",
    "SingularMatrixError",
    "SolutionSet",
    "Step",
    "StepKind",
    "Tracer",
    "TriangularResult",
    "UndecidableZeroError",
    "UndefinedOperationError",
    "UniqueSolution",
    "Vector",
    "Verdict",
    "ZeroDecision",
    "ZeroOracle",
    "cayley_orthogonal",
    "check_gram_schmidt_step",
    "check_row_operation",
    "choose_domain",
    "compare",
    "config",
    "generate_clean_least_squares",
    "generate_integer_rref_matrix",
    "generate_parametric_system",
    "generate_rational_qr_matrix",
    "generate_unimodular_matrix",
    "generateurs",
    "oracle",
    "record",
    "section",
    "suspend_tracing",
    "symbols",
    "to_exact",
    "tracing",
    "tuteur",
    "using_config",
]
