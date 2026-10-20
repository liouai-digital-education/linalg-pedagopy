"""Tests de l'oracle de nullité core/zero.py (4 verdicts, radicaux, paramètres)."""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
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


def test_zero_oracle_parametric_radicals_and_assumptions() -> None:
    m, a, b = symbols("m a b")
    # Somme/différence avec radical paramétré : m - sqrt(1 - m^2) s'annule en m = sqrt(2)/2
    expr_rad = m - sp.sqrt(1 - m**2)
    dec_rad = oracle.decide(expr_rad)
    assert dec_rad.verdict == Verdict.CONDITIONAL
    assert dec_rad.condition is not None
    assert dec_rad.condition.substitutions() == {m: sp.sqrt(2) / 2}

    # Sous m = sqrt(2)/2, l'expression est ZERO
    assert oracle.decide(expr_rad, assumptions=dec_rad.condition).verdict == Verdict.ZERO
    # Sous m = -sqrt(2)/2 (racine parasite d'unrad), l'expression est NONZERO
    assert oracle.decide(expr_rad, assumptions=Condition.eq(m, -sp.sqrt(2) / 2)).verdict == Verdict.NONZERO

    # 1 + sqrt(m^2 + 1) est strictement positif sur R -> NONZERO
    assert oracle.decide(1 + sp.sqrt(m**2 + 1)).verdict == Verdict.NONZERO

    # Polynôme multivarié strictement positif sur R : a^2 + b^2 + 1 -> NONZERO
    assert oracle.decide(a**2 + b**2 + 1).verdict == Verdict.NONZERO

    # Symbole portant l'hypothèse SymPy nonzero=True
    (nz,) = symbols("nz", nonzero=True)
    assert oracle.decide(nz).verdict == Verdict.NONZERO


def test_zero_oracle_domain_keeps_forbidden_values() -> None:
    a, b = symbols("a b")
    # La simplification par a - 1 ne doit pas effacer la valeur interdite a = 1
    d = oracle.decide((a**2 - 1) / (a - 1))
    assert d.verdict == Verdict.CONDITIONAL
    assert d.factors == (a + 1,)
    assert str(d.condition) == "a = −1"
    assert d.domain is not None and str(d.domain) == "a ≠ 1"

    d_inv = oracle.decide(1 / (a - 1))
    assert d_inv.verdict == Verdict.NONZERO
    assert d_inv.domain is not None and str(d_inv.domain) == "a ≠ 1"

    # Deux paramètres : chaque facteur du dénominateur est une valeur interdite
    d2 = oracle.decide(a / (b * (a + 1)))
    assert d2.verdict == Verdict.CONDITIONAL
    assert d2.factors == (a,)
    assert d2.domain is not None
    assert d2.domain.implies_zero(b) is False and d2.domain.implies_zero(a + 1) is False

    # Un dénominateur qui ne s'annule pas sur R n'impose rien ; un polynôme non plus
    assert oracle.decide(1 / (a**2 + 1)).domain is None
    assert oracle.decide(a - 2).domain is None


def test_zero_oracle_domain_and_assumptions() -> None:
    (a,) = symbols("a")
    expr = (a**2 - 1) / (a - 1)
    # Une hypothèse qui exclut déjà la valeur interdite rend le domaine superflu
    d_neq = oracle.decide(expr, assumptions="a != 1")
    assert d_neq.verdict == Verdict.CONDITIONAL
    assert d_neq.domain is None
    # Hors du domaine, l'expression n'est pas définie : l'oracle ne conclut pas
    d_out = oracle.decide(expr, assumptions={"a": 1})
    assert d_out.verdict == Verdict.UNKNOWN
    assert d_out.method == "undefined"
    # Dans le domaine, les verdicts restent exacts
    assert oracle.decide(expr, assumptions={"a": -1}).verdict == Verdict.ZERO
    assert oracle.decide(expr, assumptions={"a": 2}).verdict == Verdict.NONZERO


def test_zero_oracle_product_condition_is_a_disjunction() -> None:
    a, b = symbols("a b")
    d = oracle.decide(a * b)
    assert d.verdict == Verdict.CONDITIONAL
    assert [str(c) for c in d.cases] == ["a = 0", "b = 0"]
    assert d.format_cases() == "a = 0 ou b = 0"
    assert d.condition == d.cases[0]
    # Un seul facteur : une seule alternative ; verdict tranché : aucune
    assert oracle.decide(a - 2).format_cases() == "a = 2"
    assert oracle.decide(a**2 + 1).cases == ()


def test_decide_all_zero_branches_are_disjoint_and_exhaustive() -> None:
    from linalg_pedagopy.core.zero import decide_all_zero

    a, b = symbols("a b")
    res = decide_all_zero([a * b, 0])
    assert isinstance(res, CaseSplit)
    for va in (-1, 0, 2):
        for vb in (0, 3):
            matching = [br for br in res.branches if br.condition.is_satisfied({a: va, b: vb})]
            assert len(matching) == 1
            assert matching[0].result is (va * vb == 0)
    assert decide_all_zero([0, sp.Rational(0)]) is True
    assert decide_all_zero([a, 1]) is False
    assert decide_all_zero([a * b], assumptions="a != 0").at(a=1, b=0) is True
