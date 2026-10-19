"""Tests du module core/field.py (coercition selon les 3 politiques, symboles réels, domaines)."""

from __future__ import annotations

from fractions import Fraction
import pytest
import sympy as sp
from sympy.polys.domains import QQ

from linalg_pedagopy import (
    InexactInputError,
    StepKind,
    choose_domain,
    symbols,
    to_exact,
    tracing,
    using_config,
)


def test_symbols_are_real_by_default() -> None:
    (a,) = symbols("a")
    b, c = symbols("b c")
    assert a.is_real is True
    assert b.is_real is True
    assert c.is_real is True
    # Sur R, sqrt(a**2) ne laisse pas un symbole complexe non typé
    assert sp.simplify(sp.conjugate(a)) == a


def test_non_real_sympy_symbol_is_recreated_as_real_with_trace_warning() -> None:
    x_complex = sp.Symbol("x")
    assert x_complex.is_real is None
    with tracing(level=2) as t:
        ex = to_exact(x_complex + 1)
    free = list(ex.free_symbols)
    assert len(free) == 1
    assert free[0].is_real is True
    assert any(
        child.kind == StepKind.WARNING and child.message_key == "field.symbol_made_real"
        for child in t.tree.children
    )


def test_to_exact_integers_fractions_strings() -> None:
    assert to_exact(3) == sp.Integer(3)
    assert to_exact(Fraction(2, 7)) == sp.Rational(2, 7)
    assert to_exact("1/3") == sp.Rational(1, 3)
    assert to_exact("sqrt(2)") == sp.sqrt(2)


def test_float_policy_rationalize_default() -> None:
    with using_config(float_policy="rationalize"):
        with tracing(level=1) as t:
            val = to_exact(0.1)
        assert val == sp.Rational(1, 10)
        assert any(
            c.kind == StepKind.WARNING and c.message_key == "field.float_rationalized"
            for c in t.tree.children
        )


def test_float_policy_reject_raises_inexact_input_error() -> None:
    with using_config(float_policy="reject"):
        with pytest.raises(InexactInputError):
            to_exact(0.1)
        with pytest.raises(InexactInputError):
            to_exact(sp.Float(0.25))


def test_float_policy_keep() -> None:
    with using_config(float_policy="keep"):
        val = to_exact(0.125)
        assert isinstance(val, sp.Float)


def test_choose_domain_hierarchy() -> None:
    # Rationnels -> QQ
    dom_q = choose_domain([sp.Integer(1), sp.Rational(2, 3)])
    assert dom_q == QQ

    # Fractions rationnelles en un paramètre -> Q(a)
    (a,) = symbols("a")
    dom_param = choose_domain([a + 1, sp.Integer(2) / (a - 1)])
    assert dom_param.is_Field

    # Nombres algébriques -> extension algébrique
    dom_alg = choose_domain([sp.Integer(1), sp.sqrt(2)])
    assert dom_alg.is_Field
