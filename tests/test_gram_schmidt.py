"""Tests de GramSchmidt (§5.4.4 : variantes normalize='end' et 'each', témoin de dépendance)."""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    GSResult,
    GramSchmidt,
    LinearDependenceError,
    Vector,
)


def test_gram_schmidt_both_variants_produce_equal_orthonormal_vectors() -> None:
    a1 = Vector([1, 1, 0])
    a2 = Vector([1, 0, 1])
    a3 = Vector([0, 1, 1])

    res_end = GramSchmidt([a1, a2, a3], normalize="end").run()
    res_each = GramSchmidt([a1, a2, a3], normalize="each").run()

    assert isinstance(res_end, GSResult)
    assert isinstance(res_each, GSResult)
    assert res_end.independent is True
    assert res_each.independent is True

    # Dans normalize="end", les q_tilde sont tous rationnels !
    for qt in res_end.orthogonal:
        assert all(e.is_Rational for e in qt.entries)

    # Les deux variantes produisent exactement la même base orthonormée
    assert res_end.orthonormal == res_each.orthonormal
    assert res_end.Q.has_orthonormal_columns() is True
    res_end.verify()


def test_gram_schmidt_linear_dependence_witness_and_strict_mode() -> None:
    a1 = Vector([1, 2, -1])
    a2 = Vector([2, 0, 1])
    a3 = 2 * a1 - a2  # dépendant !

    res = GramSchmidt([a1, a2, a3], strict=False).run()
    assert isinstance(res, GSResult)
    assert res.independent is False
    assert res.dependent_index == 2
    assert res.witness is not None
    assert res.witness.a_coeffs == (sp.Integer(2), sp.Integer(-1))

    with pytest.raises(LinearDependenceError) as exc_info:
        GramSchmidt([a1, a2, a3], strict=True).run()
    assert exc_info.value.index == 2
    assert exc_info.value.witness is not None
