"""Tests de GaussJordan (§5.4.2 : rang, solution unique, affine, vide, inversion, paramètres, Annexe A)."""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    AffineSolution,
    CaseSplit,
    EmptySolution,
    GJResult,
    GaussJordan,
    Matrix,
    SingularMatrixError,
    UniqueSolution,
    Vector,
    symbols,
    tracing,
)


def test_gauss_jordan_unique_solution_and_sympy_oracle() -> None:
    A = Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
    b = Vector([8, -11, -3])
    res = GaussJordan(A, b).run()
    assert isinstance(res, GJResult)
    assert res.rank == 3
    assert res.pivots == (0, 1, 2)
    assert isinstance(res.solution, UniqueSolution)
    assert res.solution.x == Vector([2, 3, -1])

    # Comparaison avec l'oracle sympy.Matrix.rref()
    sp_rref, sp_pivots = A.to_sympy().rref()
    assert res.rref == Matrix(sp_rref)
    assert res.pivots == tuple(sp_pivots)

    exp = res.verify()
    assert "A x - b" in str(exp)


def test_gauss_jordan_affine_solution() -> None:
    A = Matrix([[1, 2, -1], [2, 4, -2]])
    b = Vector([3, 6])
    res = GaussJordan(A, b).run()
    assert isinstance(res, GJResult)
    assert res.rank == 1
    assert res.free_vars == (1, 2)
    assert isinstance(res.solution, AffineSolution)
    # Vérifier que x0 + t1*v1 + t2*v2 satisfait A x = b pour des paramètres arbitraires
    x_sample = res.solution.at_params(5, -2)
    assert (A @ x_sample) == b


def test_gauss_jordan_empty_solution() -> None:
    A = Matrix([[1, 2], [2, 4]])
    b = Vector([3, 7])
    res = GaussJordan(A, b).run()
    assert isinstance(res, GJResult)
    assert res.rank == 1
    assert isinstance(res.solution, EmptySolution)
    assert res.solution.row == 1
    assert res.solution.witness == 1


def test_gauss_jordan_inversion_and_strict_mode() -> None:
    A = Matrix([[1, 2], [3, 5]])
    res = GaussJordan(A, Matrix.identity(2), compute_inverse=True).run()
    assert isinstance(res, GJResult)
    assert res.inverse == Matrix([[-5, 2], [3, -1]])

    S = Matrix([[1, 2], [2, 4]])
    res_sing = GaussJordan(S, Matrix.identity(2), strict=False, compute_inverse=True).run()
    assert isinstance(res_sing, GJResult)
    assert res_sing.inverse is None
    assert res_sing.rank == 1

    with pytest.raises(SingularMatrixError):
        GaussJordan(S, Matrix.identity(2), strict=True, compute_inverse=True).run()


def test_gauss_jordan_appendix_a_parameter_discussion() -> None:
    """Vérifie exactement la session de l'Annexe A (page 27 du plan v3)."""
    (a,) = symbols("a")
    A = Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]])
    b = Vector([1, 2, 3])

    with tracing(level=2):
        res = GaussJordan(A, b).run()

    assert isinstance(res, CaseSplit)
    text_out = str(res.explain(level=1))
    assert "Discussion selon a" in text_out
    assert "Cas a ≠ 1 (générique) : pivots non nuls, rang 3, solution unique" in text_out
    assert "Cas a = 1 : L2 et L3 deviennent (0 0 0 | 1) et (0 0 0 | 2)" in text_out
    assert "système incompatible (témoin : 0 = 1)" in text_out

    gen_sol = res.generic().solution
    assert isinstance(gen_sol, UniqueSolution)
    expected_x = Vector([(a - 4) / (a - 1), sp.Integer(1) / (a - 1), sp.Integer(2) / (a - 1)])
    assert gen_sol.x == expected_x


def test_gauss_jordan_radical_matrix_inversion() -> None:
    """Vérifie l'inversion d'une matrice avec radicaux symboliques (sqrt(1 - m**2))."""
    (m,) = symbols("m")
    M = Matrix([
        [m, -sp.sqrt(1 - m**2)],
        [sp.sqrt(1 - m**2), m]
    ])

    # 1. Inversion sans hypothèse -> CaseSplit
    cs = M.inv()
    assert isinstance(cs, CaseSplit)
    assert len(cs.branches) == 2

    # Branche générique m != 0
    inv_gen = cs.generic()
    assert inv_gen == Matrix([[m, sp.sqrt(1 - m**2)], [-sp.sqrt(1 - m**2), m]])
    assert M @ inv_gen == Matrix.identity(2)

    # 2. Inversion avec hypothèse explicite m != 0
    inv_direct = M.inv(assumptions="m != 0")
    assert isinstance(inv_direct, Matrix)
    assert inv_direct == Matrix([[m, sp.sqrt(1 - m**2)], [-sp.sqrt(1 - m**2), m]])
    assert M @ inv_direct == Matrix.identity(2)


def test_gauss_jordan_domain_of_coefficients() -> None:
    a, b = symbols("a b")
    # (a² − 1)/(a − 1) n'est pas défini en a = 1 : aucune branche ne doit couvrir cette valeur
    M = Matrix([[(a**2 - 1) / (a - 1), 1], [1, 1]])
    res = GaussJordan(M).run()
    assert isinstance(res, CaseSplit)
    for branch in res.branches:
        assert branch.condition.implies_zero(a - 1) is False
    assert res.at(a=2).rank == 2
    assert res.at(a=0).rank == 1
    with pytest.raises(ValueError):
        res.at(a=1)

    # Sans discussion de cas, la trace annonce le domaine
    with tracing(level=1) as t:
        res_u = GaussJordan(Matrix([[1 / (a - 1), 1], [0, 2]]), Vector([1, b])).run()
    assert isinstance(res_u, GJResult)
    assert any(c.message_key == "gj.domain" for c in t.tree.children)

    # Hypothèses incompatibles avec le domaine : erreur explicite ; compatibles : pas de message
    from linalg_pedagopy import PedagopyError

    with pytest.raises(PedagopyError, match="a ≠ 1"):
        GaussJordan(M, assumptions={"a": 1}).run()
    with tracing(level=1) as t_ok:
        GaussJordan(M, assumptions="a != 1").run()
    assert not any(c.message_key == "gj.domain" for c in t_ok.tree.children)
