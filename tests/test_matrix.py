"""Tests de l'objet immuable Matrix (§5.3.2 : constructeurs, 4 vues du produit, Gram, délégations)."""

from __future__ import annotations

import pytest

from linalg_pedagopy import (
    DimensionMismatchError,
    Matrix,
    UniqueSolution,
    Vector,
    tracing,
)


def test_matrix_constructors_and_immutability() -> None:
    c1 = Vector([1, 2])
    c2 = Vector([3, 4])
    A = Matrix.from_columns([c1, c2])
    assert A == Matrix([[1, 3], [2, 4]])
    assert A.T == Matrix.from_rows([c1, c2])

    I2 = Matrix.identity(2)
    Z2 = Matrix.zeros(2, 2)
    B = Matrix.block([[A, I2], [0, A]])
    assert B.shape == (4, 4)
    assert B[:2, :2] == A
    assert B[:2, 2:] == I2
    assert B[2:, :2] == Z2
    assert B[2:, 2:] == A

    with pytest.raises(AttributeError):
        A.foo = 1  # type: ignore[attr-defined]


def test_matrix_matmul_four_views() -> None:
    A = Matrix([[1, 2], [3, 4], [5, 6]])
    B = Matrix([[2, -1], [0, 3]])
    expected = Matrix([[2, 5], [6, 9], [10, 13]])
    assert (A @ B) == expected

    for view in ("entries", "rows", "columns", "outer"):
        with tracing(level=2) as t:
            res = A.matmul(B, view=view)  # type: ignore[arg-type]
        assert res == expected
        assert len(t.tree.children) == 1
        assert t.tree.children[0].message_key == f"matrix.matmul.{view}"

    v = Vector([2, -1])
    assert (A @ v) == Vector([0, 2, 4])

    with pytest.raises(DimensionMismatchError):
        _ = B @ A


def test_matrix_gram_and_orthonormality() -> None:
    A = Matrix([[1, 2], [2, 1], [-1, 0]])
    G = A.gram()
    assert G == (A.T @ A)
    assert G == Matrix([[6, 4], [4, 5]])

    I3 = Matrix.identity(3)
    assert I3.has_orthonormal_columns() is True
    assert A.has_orthonormal_columns() is False


def test_matrix_delegations_to_gauss_jordan() -> None:
    A = Matrix([[1, 2], [3, 5]])
    assert A.rank() == 2
    assert A.rref() == Matrix.identity(2)
    assert A.nullspace() == ()
    inv_a = A.inv()
    assert inv_a == Matrix([[-5, 2], [3, -1]])

    sol = A.solve(Vector([5, 13]))
    assert isinstance(sol, UniqueSolution)
    assert sol.x == Vector([1, 2])


def test_inv_annonce_les_valeurs_singulieres_du_parametre() -> None:
    import pytest

    from linalg_pedagopy import CaseSplit, SingularMatrixError, symbols

    a, b = symbols("a b")
    # Inversible sauf pour a = ±1 : le message donne le déterminant et les valeurs singulières
    with pytest.raises(SingularMatrixError, match="s'annule pour a = 1 ou a = −1") as info:
        Matrix([[1, a], [a, 1]]).inv()
    assert "strict=False" in str(info.value)
    with pytest.raises(SingularMatrixError, match="a = b"):
        Matrix([[a, b], [1, 1]]).inv()
    with pytest.raises(SingularMatrixError, match="identiquement nul"):
        Matrix([[a, 2 * a], [1, 2]]).inv()
    # Une hypothèse qui exclut une valeur singulière la retire du message
    with pytest.raises(SingularMatrixError) as info2:
        Matrix([[1, a], [a, 1]]).inv(assumptions="a != 1")
    assert "a = −1" in str(info2.value) and "a = 1 " not in str(info2.value)
    # Comportements inchangés : toujours inversible, hypothèse qui fixe a, mode non strict
    assert Matrix([[1, a], [0, 1]]).inv() == Matrix([[1, -a], [0, 1]])
    assert Matrix([[1, a], [a, 1]]).inv(assumptions={"a": 2}) @ Matrix([[1, 2], [2, 1]]) == Matrix.identity(2)
    assert isinstance(Matrix([[1, a], [a, 1]]).inv(strict=False), CaseSplit)
    with pytest.raises(SingularMatrixError, match="rang 1 < 2"):
        Matrix([[1, 2], [2, 4]]).inv()
