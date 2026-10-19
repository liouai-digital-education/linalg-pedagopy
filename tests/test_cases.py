"""Tests de Condition, CaseSplit et garde-fous de profondeur / nombre de branches."""

from __future__ import annotations

import pytest

from linalg_pedagopy import (
    Branch,
    CaseSplit,
    Condition,
    GaussJordan,
    Matrix,
    PedagopyError,
    Vector,
    symbols,
)


def test_condition_formatting_and_satisfaction() -> None:
    a, b = symbols("a b")
    c1 = Condition.neq(a, 1)
    c2 = Condition.eq(b, 0)
    comb = c1 & c2
    assert comb.format_text() == "a ≠ 1 et b = 0"
    assert comb.is_satisfied({"a": 2, "b": 0}) is True
    assert comb.is_satisfied({"a": 1, "b": 0}) is False
    assert comb.is_satisfied({"a": 2, "b": 3}) is False


def test_casesplit_generic_and_at() -> None:
    (a,) = symbols("a")
    A = Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]])
    b = Vector([1, 2, 3])
    cs = GaussJordan(A, b).run()
    assert isinstance(cs, CaseSplit)
    assert len(cs) == 2

    gen = cs.generic()
    assert gen.rank == 3
    assert gen.solution is not None and gen.solution.is_unique

    at_1 = cs.at(a=1)
    assert at_1.rank == 1
    assert at_1.solution is not None and not at_1.solution.is_consistent

    at_2 = cs.at(a=2)
    assert at_2.rank == 3
    assert at_2.solution.x == Vector([-2, 1, 2])  # type: ignore[union-attr]


def test_casesplit_guardrails_max_depth_and_max_cases() -> None:
    a, b = symbols("a b")
    A = Matrix([[a, 0], [0, b]])
    rhs = Vector([1, 1])

    # max_depth=1 doit refuser le second embranchement sur b
    with pytest.raises(PedagopyError):
        GaussJordan(A, rhs, max_depth=1).run()

    # max_cases=1 doit refuser dès le premier embranchement
    with pytest.raises(PedagopyError):
        GaussJordan(A, rhs, max_cases=1).run()
