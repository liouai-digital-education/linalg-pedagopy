"""Avertissement didactique au-delà de config.max_generic_dim (étape 3.5 du plan v6).

Gauss-Jordan sur une matrice à paramètres de taille > 4 émet un PedagogicalWarning
qui invite à chercher une structure remarquable ; le calcul est toujours mené à terme.
"""

from __future__ import annotations

import warnings

import pytest

from linalg_pedagopy import (
    CaseSplit,
    GaussJordan,
    Matrix,
    PedagogicalWarning,
    Vector,
    config,
    symbols,
    using_config,
)

a, = symbols("a")


def tridiagonale(n: int) -> Matrix:
    return Matrix([[a if i == j else (1 if abs(i - j) == 1 else 0) for j in range(n)] for i in range(n)])


def test_avertissement_au_dela_de_4() -> None:
    with pytest.warns(PedagogicalWarning, match=r"matrice 5×5 à paramètres : au-delà de 4×4") as avertis:
        res = GaussJordan(tridiagonale(5), Vector([1, 0, 0, 0, 1])).run()
    assert isinstance(res, CaseSplit)  # le calcul est mené à terme
    assert len([w for w in avertis if issubclass(w.category, PedagogicalWarning)]) == 1  # une fois par calcul
    assert "structure remarquable" in str(avertis[0].message)
    assert avertis[0].filename == __file__  # l'avertissement désigne la ligne de l'appelant


def _sans_avertissement(A: Matrix, b: Vector) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", PedagogicalWarning)
        GaussJordan(A, b).run()


def test_pas_d_avertissement() -> None:
    _sans_avertissement(tridiagonale(4), Vector([1, 0, 0, 1]))  # taille 4
    _sans_avertissement(Matrix([[i + j for j in range(5)] for i in range(5)]), Vector([1] * 5))  # sans paramètre
    with using_config(max_generic_dim=None):
        _sans_avertissement(tridiagonale(5), Vector([1, 0, 0, 0, 1]))


def test_seuil_reglable() -> None:
    with using_config(max_generic_dim=2):
        with pytest.warns(PedagogicalWarning, match=r"3×3 .* au-delà de 2×2"):
            GaussJordan(tridiagonale(3), Vector([1, 0, 1])).run()


def test_rectangulaire() -> None:
    A = Matrix([[a, 1, 0, 0, 0], [0, 1, a, 0, 1]])
    with pytest.warns(PedagogicalWarning, match=r"matrice 2×5"):
        GaussJordan(A, Vector([1, 0])).run()


@pytest.mark.parametrize("valeur", [0, -1, 2.5, "4"])
def test_valeur_invalide(valeur: object) -> None:
    with pytest.raises(ValueError):
        config.max_generic_dim = valeur  # type: ignore[assignment]
    assert config.max_generic_dim == 4
