"""Tests de l'oracle de nullité core/zero.py (4 verdicts, radicaux, paramètres)."""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    Condition,
    UndecidableZeroError,
    Verdict,
    oracle,
    symbols,
    tracing,
)


def test_zero_oracle_rational_domain() -> None:
    d0 = oracle.decide(sp.Rational(1, 3) - sp.Rational(2, 6))
    assert d0.verdict == Verdict.ZERO
    assert d0.method == "domain"

    d1 = oracle.decide(sp.Rational(5, 7))
    assert d1.verdict == Verdict.NONZERO
    assert d1.method == "domain"


def test_zero_oracle_algebraic_radicals() -> None:
    expr_zero = sp.Add(
        sp.Mul(sp.sqrt(2), sp.sqrt(3), evaluate=False),
        -sp.sqrt(6),
        evaluate=False,
    )
    with tracing(level=3) as t:
        d = oracle.decide(expr_zero)
    assert d.verdict == Verdict.ZERO
    assert d.method == "minpoly"
    assert any(c.message_key == "zero.minpoly_zero" for c in t.tree.children)

    # Radical imbriqué sqrt(3 + 2*sqrt(2)) - (1 + sqrt(2)) == 0
    nested = sp.sqrt(3 + 2 * sp.sqrt(2)) - 1 - sp.sqrt(2)
    dn = oracle.decide(nested)
    assert dn.verdict == Verdict.ZERO
    assert dn.method == "minpoly"

    # Radical non nul
    d_nz = oracle.decide(sp.sqrt(2) + sp.sqrt(3) - sp.sqrt(5))
    assert d_nz.verdict == Verdict.NONZERO


def test_zero_oracle_conditional_on_parameter() -> None:
    (a,) = symbols("a")
    d = oracle.decide(a - 1)
    assert d.verdict == Verdict.CONDITIONAL
    assert d.condition is not None
    assert str(d.condition) == "a = 1"

    # Sous l'hypothèse a = 1, devient ZERO
    d_eq = oracle.decide(a - 1, assumptions=Condition.eq(a, 1))
    assert d_eq.verdict == Verdict.ZERO

    # Sous l'hypothèse a != 1, devient NONZERO
    d_neq = oracle.decide(a - 1, assumptions=Condition.neq(a, 1))
    assert d_neq.verdict == Verdict.NONZERO

    # Un polynôme strictement positif sur R (a^2 + 1) est NONZERO sans condition !
    d_pos = oracle.decide(a**2 + 1)
    assert d_pos.verdict == Verdict.NONZERO


def test_zero_oracle_unknown_raises_undecidable() -> None:
    (a,) = symbols("a")
    f = sp.Function("f")
    expr = f(a) - 1
    d = oracle.decide(expr)
    assert d.verdict == Verdict.UNKNOWN
    with pytest.raises(UndecidableZeroError):
        oracle.is_zero(expr)
