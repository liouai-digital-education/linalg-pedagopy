"""Tests de l'objet immuable Vector (§5.3.1)."""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
    DimensionMismatchError,
    UndefinedOperationError,
    Vector,
    symbols,
    tracing,
)


def test_vector_construction_and_immutability() -> None:
    v = Vector([1, "1/2", sp.sqrt(2)])
    assert len(v) == 3
    assert v[0] == 1
    assert v[1] == sp.Rational(1, 2)
    assert v[2] == sp.sqrt(2)
    assert v.shape == (3, 1)

    with pytest.raises(AttributeError):
        v.new_attr = 42  # type: ignore[attr-defined]

    assert Vector.zeros(3) == Vector([0, 0, 0])
    assert Vector.ones(3) == Vector([1, 1, 1])
    assert Vector.unit(1, 3) == Vector([0, 1, 0])


def test_vector_arithmetic_and_combination() -> None:
    u = Vector([1, 2, 3])
    v = Vector([4, -1, 2])
    assert u + v == Vector([5, 1, 5])
    assert u - v == Vector([-3, 3, 1])
    assert 3 * u == Vector([3, 6, 9])
    assert u * 3 == Vector([3, 6, 9])
    assert -u == Vector([-1, -2, -3])

    comb = Vector.combination([u, v], [2, -1])
    assert comb == Vector([-2, 5, 4])

    with pytest.raises(DimensionMismatchError):
        _ = u + Vector([1, 2])


def test_vector_dot_norm_rms_avg_std_demean_distance_angle() -> None:
    v = Vector([1, -2, 3, 2])
    assert v.avg() == sp.Integer(1)
    assert v.demean() == Vector([0, -3, 2, 1])
    assert v.norm() == sp.sqrt(18)
    assert v.rms() == sp.sqrt(sp.Rational(9, 2))
    assert v.std() == sp.sqrt(sp.Rational(7, 2))

    e1 = Vector([1, 0])
    e2 = Vector([0, 1])
    assert e1.dot(e2) == 0
    assert e1.distance(e2) == sp.sqrt(2)
    assert e1.angle(e2) == sp.pi / 2

    with pytest.raises(UndefinedOperationError):
        e1.angle(Vector.zeros(2))


def test_vector_is_zero_with_parameter() -> None:
    (a,) = symbols("a")
    v = Vector([a - 1, 0])
    res = v.is_zero()
    assert isinstance(res, CaseSplit)
    assert res.generic() is False
    assert res.at(a=1) is True


def test_vector_is_zero_with_product_and_several_parameters() -> None:
    a, b = symbols("a b")
    # a·b s'annule si a = 0 OU b = 0 : les deux cas doivent être couverts
    res = Vector([a * b, 0]).is_zero()
    assert isinstance(res, CaseSplit)
    assert res.at(a=0, b=5) is True
    assert res.at(a=1, b=0) is True
    assert res.at(a=1, b=2) is False
    # Deux composantes : toute valeur des paramètres tombe dans une branche
    res2 = Vector([a, b - 1]).is_zero()
    assert isinstance(res2, CaseSplit)
    assert res2.at(a=0, b=1) is True
    assert res2.at(a=0, b=2) is False
    assert res2.at(a=3, b=1) is False


def test_vector_traces_at_level_2_and_3() -> None:
    u = Vector([1, 2])
    v = Vector([3, 4])
    with tracing(level=3) as t:
        res = u.dot(v)
    assert res == 11
    assert len(t.tree.children) == 1
    assert t.tree.children[0].message_key == "vector.dot"
