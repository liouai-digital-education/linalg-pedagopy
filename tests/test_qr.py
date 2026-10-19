"""Tests de la factorisation QR (§5.4.5 : QR = A, Q^T Q = I_n, diagonale de R positive)."""

from __future__ import annotations

import pytest

from linalg_pedagopy import (
    Matrix,
    QR,
    QRResult,
    RankDeficientError,
)


def test_qr_factorization_identities_and_positive_diagonal() -> None:
    A = Matrix([[1, 1], [1, 0], [0, 1]])
    res = QR(A).run()
    assert isinstance(res, QRResult)
    assert res.full_rank is True

    # Factorisation rationnelle A = Q_tilde * R_tilde
    assert (res.Q_tilde @ res.R_tilde) == A
    assert (res.Q_tilde.T @ res.Q_tilde) == res.D_sq

    # Factorisation normalisée A = Q * R et Q^T Q = I_n
    assert (res.Q @ res.R) == A
    assert (res.Q.T @ res.Q) == Matrix.identity(2)

    # Diagonale de R strictement positive (D9)
    for i in range(A.cols):
        assert res.R[i, i].is_positive is True

    exp = res.verify()
    assert "Q R - A = 0" in str(exp)
    assert "Q^T Q - I" in str(exp)


def test_qr_rank_deficient() -> None:
    A = Matrix([[1, 2], [2, 4], [3, 6]])
    res = QR(A, strict=False).run()
    assert isinstance(res, QRResult)
    assert res.full_rank is False

    with pytest.raises(RankDeficientError):
        QR(A, strict=True).run()
