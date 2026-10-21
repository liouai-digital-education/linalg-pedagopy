"""Factorisation des résultats selon la condition de la branche (étape 3.2 du plan v6).

- ``config.factor_policy = "real_radicals"`` (défaut) : les résultats d'une branche sont
  factorisés avec les radicaux √d qui apparaissent dans sa condition ;
- dans une branche à égalité non linéaire (a² − 3 = 0), les coefficients sont réduits
  modulo cette égalité (témoins d'incompatibilité compris).
"""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
    Condition,
    EmptySolution,
    GaussJordan,
    Matrix,
    UniqueSolution,
    Vector,
    config,
    symbols,
    using_config,
)

a, b = symbols("a b")


def _branche(res: CaseSplit, texte: str):  # type: ignore[no-untyped-def]
    for br in res.branches:
        if br.condition.format_text() == texte:
            return br.result
    raise AssertionError(f"branche « {texte} » absente : {[br.condition.format_text() for br in res.branches]}")


# --- Condition.radicals et Condition.reduce


def test_radicaux_de_la_condition() -> None:
    cond = Condition.neq(a**2 - 2) & Condition.neq(a, 1)
    assert cond.radicals() == {a: (sp.sqrt(2),)}
    assert Condition.neq(a**2 + a - 3).radicals() == {a: (sp.sqrt(13),)}


def test_pas_de_radicaux_sans_racine_irrationnelle() -> None:
    assert Condition.neq(a**2 - 4).radicals() == {}
    assert Condition.neq(a**2 + 1).radicals() == {}
    assert Condition.neq(a - b).radicals() == {}
    assert Condition.eq(a**2 - 2).radicals() == {}


def test_reduction_modulo_une_egalite_non_lineaire() -> None:
    cond = Condition.eq(a**2 - 3)
    assert cond.reduce(a**4 - 3 * a**2 + 2) == 2
    assert cond.reduce(a**3) == 3 * a
    assert sp.simplify(cond.reduce((2 - a**2) / (a - 1)) - (-1) / (a - 1)) == 0
    assert cond.reduce(b * a**2) == 3 * b


def test_reduction_sans_effet() -> None:
    assert Condition.eq(a, 1).reduce(a**2) == a**2  # égalité linéaire : déjà appliquée par substitution
    assert Condition.neq(a**2 - 3).reduce(a**4) == a**4  # pas d'égalité
    cond = Condition.eq(a**2 - 3)
    assert cond.reduce(sp.Integer(5)) == 5
    assert cond.reduce(1 / (a**2 - 3)) == 1 / (a**2 - 3)  # dénominateur nul : expression rendue telle quelle


# --- Gauss-Jordan


def _pivot_quadratique() -> CaseSplit:
    res = GaussJordan(Matrix([[a**2 - 2, 1], [0, a - 1]]), Vector([1, 1])).run()
    assert isinstance(res, CaseSplit)
    return res


def test_solution_factorisee_comme_sa_condition() -> None:
    gen = _branche(_pivot_quadratique(), "a ≠ √(2) et a ≠ −√(2) et a ≠ 1")
    assert isinstance(gen.solution, UniqueSolution)
    x1 = gen.solution.x[0]
    assert x1.has(sp.sqrt(2))
    assert sp.simplify(x1 - (a - 2) / ((a - 1) * (a**2 - 2))) == 0
    facteurs = set(sp.Mul.make_args(sp.fraction(x1)[1]))
    assert {a - 1, a - sp.sqrt(2), a + sp.sqrt(2)} <= facteurs


def test_politique_rationnelle() -> None:
    with using_config(factor_policy="rational"):
        gen = _branche(_pivot_quadratique(), "a ≠ √(2) et a ≠ −√(2) et a ≠ 1")
    x1 = gen.solution.x[0]
    assert not x1.has(sp.sqrt(2))
    assert a**2 - 2 in sp.Mul.make_args(sp.fraction(x1)[1])


def test_politique_invalide() -> None:
    with pytest.raises(ValueError):
        config.factor_policy = "complex"  # type: ignore[assignment]
    assert config.factor_policy == "real_radicals"


def test_inverse_factorisee_et_facteurs_rationnels_conserves() -> None:
    A = Matrix([[a, 2, 1], [1, a, 1], [1, 1, a]])
    res = GaussJordan(A, compute_inverse=True).run()
    assert isinstance(res, CaseSplit)
    inv = res.branches[0].result.inverse
    assert inv is not None
    attendue = A.to_sympy().inv()
    for i in range(3):
        for j in range(3):
            assert sp.simplify(inv[i, j] - attendue[i, j]) == 0
    assert inv[0, 0].has(sp.sqrt(13))
    # 1 − 2a est déjà factorisé sur Q : il garde son écriture
    assert 1 - 2 * a in sp.Mul.make_args(sp.fraction(inv[0, 1])[0])


def test_temoin_reduit_par_la_condition() -> None:
    T = Matrix([[a if i == j else (1 if abs(i - j) == 1 else 0) for j in range(5)] for i in range(5)])
    res = GaussJordan(T, Vector([1, 0, 0, 0, 1])).run()
    assert isinstance(res, CaseSplit)
    br = _branche(res, "a ≠ 1 et a ≠ 0 et a ≠ −1 et a² − 3 = 0")
    assert isinstance(br.solution, EmptySolution)
    assert br.solution.witness == 2
    texte = br.explain(level=2).to_text()
    assert "a² − 3 = 0 : chaque coefficient est remplacé par son reste" in texte


def test_branche_singuliere_de_l_inverse_reduite() -> None:
    res = GaussJordan(Matrix([[a, 2, 1], [1, a, 1], [1, 1, a]]), compute_inverse=True, strict=False).run()
    br = _branche(res, "a ≠ 1 et a² + a − 3 = 0")
    assert br.rank == 2
    assert br.augmented_rref[2, 2] == 0
    assert all(not e.has(a**2) for e in br.augmented_rref.flat_entries)
