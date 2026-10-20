"""Tests de Condition, CaseSplit et garde-fous de profondeur / nombre de branches."""

from __future__ import annotations

from hypothesis import given, settings, strategies as st
import pytest
import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
    Condition,
    GJResult,
    GaussJordan,
    Matrix,
    PedagopyError,
    UniqueSolution,
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


def test_condition_transitive_substitutions_and_contradiction() -> None:
    a, b = symbols("a b")
    cond = Condition.eq(a, b) & Condition.eq(b, 1)
    assert cond.substitutions() == {a: sp.Integer(1), b: sp.Integer(1)}
    assert not cond.is_contradictory

    # Contradiction a = 1 et a = 2
    contra = Condition.eq(a, 1) & Condition.eq(a, 2)
    assert contra.is_contradictory

    # Contradiction a != 1 et a = 1
    contra_neq = Condition.neq(a, 1) & Condition.eq(a, 1)
    assert contra_neq.is_contradictory

    # Tautology pruning: a != 1 under a = -1 drops the redundant inequality
    pruned = Condition.neq(a, 1) & Condition.eq(a, -1)
    assert pruned.neqs == ()
    assert pruned.eqs == ((a, sp.Integer(-1)),)

    # Nonlinear univariate polynomial implies_zero
    nl_cond = Condition.from_zero_expr(a**2 - 2, is_zero=True)
    assert nl_cond.implies_zero(a**4 - 4) is True
    assert nl_cond.implies_zero(a - 1) is False


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

    # CaseSplit.at() on tuple results (nullspace)
    ns_cs = A.nullspace()
    assert isinstance(ns_cs, CaseSplit)
    assert ns_cs.at(a=2) == ()
    ns_1 = ns_cs.at(a=1)
    assert len(ns_1) == 2


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


@settings(max_examples=25, deadline=None)
@given(
    c0=st.integers(min_value=-2, max_value=2),
    c1=st.integers(min_value=-2, max_value=2),
    r1=st.integers(min_value=-2, max_value=2),
    r2=st.integers(min_value=-2, max_value=2),
    a0=st.integers(min_value=-3, max_value=3),
    b0=st.integers(min_value=-3, max_value=3),
)
def test_property_casesplit_partition_and_specialization_commutation(
    c0: int,
    c1: int,
    r1: int,
    r2: int,
    a0: int,
    b0: int,
) -> None:
    """Property-based test (Plan v4 §0.1): disjoint partition & specialization commutation."""
    a, b = symbols("a b")
    A = Matrix([[a - c0, c1], [0, b - c1]])
    rhs = Vector([r1, r2 + a])

    res = GaussJordan(A, rhs).run()
    p0 = {"a": a0, "b": b0}
    direct = GaussJordan(A.subs(p0), rhs.subs(p0)).run()
    assert isinstance(direct, GJResult)

    if isinstance(res, CaseSplit):
        # Property 1: Exactly one branch is satisfied at any point p0 in R^2
        satisfied = [br for br in res.branches if br.condition.is_satisfied(p0)]
        assert len(satisfied) == 1, f"Attendu exactement 1 branche pour {p0}, obtenu {len(satisfied)}"

        # Property 2: Specialization commutes with solving
        specialized = res.at(**p0)
        assert specialized.rank == direct.rank
        assert specialized.rref == direct.rref
        assert type(specialized.solution) is type(direct.solution)
        if isinstance(specialized.solution, UniqueSolution) and isinstance(direct.solution, UniqueSolution):
            assert specialized.solution.x == direct.solution.x

        # Property 3: In the generic branch, A @ x == rhs
        gen = res.generic()
        if isinstance(gen.solution, UniqueSolution):
            assert (gen.A @ gen.solution.x) == gen.b
    else:
        assert res.subs(p0).rank == direct.rank
        assert res.subs(p0).rref == direct.rref
