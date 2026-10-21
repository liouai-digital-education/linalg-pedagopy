"""Facteurs de signe strict constant à plusieurs paramètres (étape 3.3 du plan v6).

Un polynôme de degré 2 en plusieurs paramètres réels qui s'écrit, en complétant les
carrés, comme une somme de carrés et d'une constante > 0 ne s'annule jamais sur R :
l'oracle ne doit pas ouvrir de branche pour lui.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st
import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
    GaussJordan,
    Matrix,
    Vector,
    Verdict,
    oracle,
    symbols,
)
from linalg_pedagopy.core.zero import domain_of, strict_sign, sum_of_squares

a, b, c = symbols("a b c")


def test_completion_des_carres() -> None:
    squares, rest = sum_of_squares(a**2 + a * b + b**2 + 1)  # type: ignore[misc]
    assert squares == ((1, a + b / 2), (sp.Rational(3, 4), b))
    assert rest == 1
    assert strict_sign(a**2 + a * b + b**2 + 1) == (1, "(a + b/2)² + 3/4·b² + 1")


def test_signe_strict() -> None:
    assert strict_sign(2 * a**2 + 2 * a * b + b**2 + 3) is not None
    assert strict_sign(a**2 - 2 * a * b + 2 * b**2 + 1) == (1, "(a − b)² + b² + 1")
    assert strict_sign(a**2 + b**2 + c**2 + a * b + b * c + 1) is not None
    assert strict_sign(a**2 + b**2 - 2 * a + 2) == (1, "(a − 1)² + b² + 1")
    assert strict_sign(-(a**2 + a * b + b**2 + 1)) == (-1, "(a + b/2)² + 3/4·b² + 1")


def test_pas_de_signe_strict() -> None:
    assert strict_sign(a**2 - 2 * a + b**2 + 1) is None  # s'annule en (1, 0)
    assert strict_sign(a**2 - a * b + b**2) is None  # s'annule en (0, 0)
    assert strict_sign(a * b + 1) is None  # change de signe
    assert strict_sign(a**2 - b**2 + 1) is None
    assert strict_sign(a**2 + b + 1) is None  # b n'apparaît qu'au degré 1
    assert strict_sign(a**2 * b**2 + a + 1) is None  # degré 4 : hors du champ de la méthode


@settings(max_examples=60, deadline=None)
@given(st.lists(st.integers(-4, 4), min_size=6, max_size=6))
def test_decomposition_exacte(coefs: list[int]) -> None:
    p = coefs[0] * a**2 + coefs[1] * a * b + coefs[2] * b**2 + coefs[3] * a + coefs[4] * b + coefs[5]
    dec = sum_of_squares(p)
    if dec is None:
        return
    squares, rest = dec
    assert all(k > 0 for k, _ in squares)
    assert sp.expand(sum(k * lin**2 for k, lin in squares) + rest - p) == 0
    if strict_sign(p) is not None:
        # aucun zéro réel : le minimum, atteint quand tous les carrés s'annulent, vaut rest > 0
        assert rest > 0


def test_oracle_sans_branche_parasite() -> None:
    q = a**2 + a * b + b**2 + 1
    assert oracle.decide(q).verdict == Verdict.NONZERO
    d = oracle.decide((b - 2) * q)
    assert d.verdict == Verdict.CONDITIONAL
    assert d.factors == (b - 2,)
    assert domain_of([1 / q]).is_trivial


def test_gauss_jordan_sans_branche_parasite() -> None:
    q = a**2 + a * b + b**2 + 1
    res = GaussJordan(Matrix([[q, 1], [0, b - 2]]), Vector([1, 1])).run()
    assert isinstance(res, CaseSplit)
    assert [br.condition.format_text() for br in res.branches] == ["b ≠ 2", "b = 2"]
    texte = res.branches[0].result.explain(level=3).to_text()
    assert "a² + a·b + b² + 1 = (a + b/2)² + 3/4·b² + 1 > 0" in texte
