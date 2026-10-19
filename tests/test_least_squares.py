"""Tests de LeastSquares (§5.4.6 : 3 méthodes cohérentes, A^T r_hat = 0, Annexe A, rang déficient)."""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    LSResult,
    LeastSquares,
    Matrix,
    RankDeficientError,
    Vector,
)


def test_least_squares_appendix_a_and_three_methods_coherence() -> None:
    A = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]])
    b = Vector([1, 2, 2, 4])

    res_rat = LeastSquares(A, b, method="rational_qr").run()
    res_qr = LeastSquares(A, b, method="qr").run()
    res_norm = LeastSquares(A, b, method="normal").run()

    assert isinstance(res_rat, LSResult)
    assert isinstance(res_qr, LSResult)
    assert isinstance(res_norm, LSResult)

    expected_x = Vector([sp.Rational(9, 10), sp.Rational(9, 10)])
    assert res_rat.x_hat == expected_x
    assert res_qr.x_hat == expected_x
    assert res_norm.x_hat == expected_x

    # Convention VMLS (D9) : r_hat = A x_hat - b
    assert res_rat.r_hat == (A @ expected_x) - b
    assert (A.T @ res_rat.r_hat).is_zero() is True

    # Pseudo-inverse A† x = x_hat
    assert (res_rat.pseudoinverse @ b) == expected_x

    # Vérification tracée A^T r_hat = 0 colonne par colonne
    ver_exp = res_rat.verify()
    assert "ZERO" in str(ver_exp)


def test_least_squares_rank_deficient_raises() -> None:
    A = Matrix([[1, 2], [2, 4], [3, 6]])
    b = Vector([1, 2, 3])
    with pytest.raises(RankDeficientError):
        LeastSquares(A, b).run()
