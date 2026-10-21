"""Tests de BackSubstitution et ForwardSubstitution (§5.4.3)."""

from __future__ import annotations

import pytest

from linalg_pedagopy import (
    BackSubstitution,
    ForwardSubstitution,
    Matrix,
    SingularMatrixError,
    TriangularResult,
    Vector,
)


def test_back_substitution() -> None:
    R = Matrix([[2, -1, 3], [0, 4, 2], [0, 0, -2]])
    x_true = Vector([1, -2, 3])
    c = R @ x_true

    res = BackSubstitution(R, c).run()
    assert isinstance(res, TriangularResult)
    assert res.x == x_true
    assert "résidu nul" in str(res.verify())


def test_forward_substitution() -> None:
    L = Matrix([[3, 0, 0], [-2, 1, 0], [4, 2, -1]])
    x_true = Vector([2, 5, -1])
    c = L @ x_true

    res = ForwardSubstitution(L, c).run()
    assert isinstance(res, TriangularResult)
    assert res.x == x_true
    assert "résidu nul" in str(res.verify())


def test_triangular_validation_and_singular() -> None:
    non_upper = Matrix([[1, 2], [3, 4]])
    with pytest.raises(ValueError):
        BackSubstitution(non_upper, Vector([1, 2]))

    singular_upper = Matrix([[1, 2], [0, 0]])
    with pytest.raises(SingularMatrixError):
        BackSubstitution(singular_upper, Vector([1, 0])).run()


def test_discussion_couvre_le_cas_singulier() -> None:
    """Un coefficient diagonal qui peut s'annuler donne aussi la branche singulière."""
    import sympy as sp

    from linalg_pedagopy import CaseSplit, symbols

    (a,) = symbols("a")
    res = BackSubstitution(Matrix([[1, 2], [0, a]]), Vector([1, 1])).run()
    assert isinstance(res, CaseSplit) and len(res.branches) == 2
    assert res.at(a=2).x == Vector([0, sp.Rational(1, 2)])
    singulier = res.at(a=0)
    assert singulier.singular and singulier.singular_index == 2 and len(singulier.x) == 0
    assert "substitution impossible" in str(res)

    avant = ForwardSubstitution(Matrix([[a, 0], [1, a - 1]]), Vector([1, 1])).run()
    assert isinstance(avant, CaseSplit)
    assert {b.result.singular_index for b in avant.branches} == {None, 1, 2}
    assert avant.at(a=0).singular_index == 1 and avant.at(a=1).singular_index == 2
