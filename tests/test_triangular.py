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
