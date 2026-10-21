"""Noyau tracé (étape 4.7 du plan v6).

La base du noyau est lue sur la forme réduite ; la trace (niveau 2) annonce les variables
libres et le théorème du rang, le système homogène équivalent, chaque vecteur de base et la
sous-matrice identité qui prouve la liberté. Elle apparaît pour une réduction sans second
membre (rref, rang, noyau) et pour une solution affine, pas pour un système incompatible.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st
import sympy as sp

from linalg_pedagopy import AffineSolution, GaussJordan, Matrix, Vector

A = Matrix([[1, 2, -1, 3, -1], [2, 4, -1, 7, 1], [-1, -2, 3, -1, 7]])


def _texte(res: object, niveau: int = 2) -> str:
    return res.explain(level=niveau).to_text()  # type: ignore[attr-defined]


def test_noyau_d_un_systeme_sous_determine() -> None:
    res = GaussJordan(A).run()
    assert res.nullspace_basis == (
        Vector([-2, 1, 0, 0, 0]),
        Vector([-4, 0, -1, 1, 0]),
        Vector([-2, 0, -3, 0, 1]),
    )
    texte = _texte(res)
    assert "variables libres x2, x4, x5 (colonnes sans pivot), variables principales x1, x3" in texte
    assert "dim ker A = n − rg A = 5 − 2 = 3" in texte
    assert "x1 = −2·x2 − 4·x4 − 2·x5 ; x3 = −x4 − 3·x5" in texte
    assert "En posant x4 = 1 et les autres variables libres nulles : v2 = ( −4, 0, −1, 1, 0 )" in texte
    assert "Les composantes x2, x4, x5 de v1, v2, v3 forment la matrice identité I_3" in texte
    # Détail de niveau 2 : absent du niveau 1
    assert "Noyau :" not in _texte(res, 1)


def test_noyau_trivial_et_vecteur_unique() -> None:
    texte = _texte(GaussJordan(Matrix([[1, 2], [3, 4]])).run())
    assert "ker A = {0}, de dimension 0 ; sa base est la famille vide" in texte
    texte = _texte(GaussJordan(Matrix([[1, 2], [2, 4]])).run())
    assert "En posant x2 = 1 : v1 = ( −2, 1 )" in texte
    assert "La composante x2 de v1 vaut 1" in texte


def test_noyau_dans_une_solution_affine_seulement() -> None:
    affine = GaussJordan(Matrix([[1, 2], [2, 4]]), Vector([1, 2])).run()
    assert isinstance(affine.solution, AffineSolution)
    texte = _texte(affine)
    assert texte.index("Noyau :") < texte.index("ensemble affine")
    # Système incompatible, solution unique, inverse : pas de construction du noyau
    assert "Noyau :" not in _texte(GaussJordan(Matrix([[1, 2], [2, 4]]), Vector([1, 3])).run())
    assert "Noyau :" not in _texte(GaussJordan(Matrix([[1, 2], [3, 4]]), Vector([1, 3])).run())
    assert "Noyau :" not in _texte(GaussJordan(Matrix([[1, 2], [2, 4]]), compute_inverse=True).run())
    assert "ker A = {0}" not in _texte(GaussJordan(Matrix([[1, 2], [3, 4]]), compute_inverse=True).run())


def test_nullspace_sans_colonne_de_zeros() -> None:
    assert A.nullspace() == GaussJordan(A).run().nullspace_basis
    assert Matrix([[1, 2], [3, 4]]).nullspace() == ()


@settings(max_examples=40, deadline=None)
@given(
    st.integers(1, 4).flatmap(
        lambda m: st.integers(1, 5).flatmap(
            lambda n: st.lists(st.lists(st.integers(-3, 3), min_size=n, max_size=n), min_size=m, max_size=m)
        )
    )
)
def test_theoreme_du_rang_et_bloc_identite(lignes: list[list[int]]) -> None:
    M = Matrix(lignes)
    res = GaussJordan(M).run()
    n = M.cols
    base = res.nullspace_basis
    assert len(base) == n - res.rank == n - sp.Matrix(lignes).rank()
    for v in base:
        assert all(e == 0 for e in (M @ v).entries)
    # Composantes libres des vecteurs de base : matrice identité
    libres = [j for j in range(n) if j not in res.pivots]
    assert [[v[j] for v in base] for j in libres] == [[int(i == k) for k in range(len(base))] for i in range(len(libres))]
