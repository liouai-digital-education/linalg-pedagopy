"""Tests du déterminant exact (algorithms/determinant.py) : méthodes, paramètres, propriétés, cas limites."""

from __future__ import annotations

import random

import pytest
import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
    Determinant,
    DetResult,
    DimensionMismatchError,
    Matrix,
    PedagopyError,
    symbols,
    tracing,
)


def _aleatoire(gen: random.Random, n: int, *, rationnel: bool) -> list[list[sp.Rational]]:
    def coef() -> sp.Rational:
        if rationnel:
            return sp.Rational(gen.randint(-9, 9), gen.randint(1, 5))
        return sp.Integer(gen.randint(-9, 9))

    return [[coef() for _ in range(n)] for _ in range(n)]


@pytest.mark.parametrize("rationnel", [False, True], ids=["entiers", "rationnels"])
def test_comparaison_avec_sympy_sur_matrices_aleatoires(rationnel: bool) -> None:
    gen = random.Random(2026 + rationnel)
    for _ in range(25):
        n = gen.randint(1, 5)
        lignes = _aleatoire(gen, n, rationnel=rationnel)
        attendu = sp.Matrix(lignes).det()
        A = Matrix(lignes)
        methodes = ["auto", "bareiss", "elimination"]
        if n <= 4:
            methodes.append("cofactors")
        if n == 3:
            methodes.append("sarrus")
        for m in methodes:
            assert sp.simplify(Determinant(A, method=m).run().value - attendu) == 0, (m, lignes)


def test_matrice_parametree_exemple_du_plan() -> None:
    (a,) = symbols("a")
    A = Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]])
    attendu = (a - 1) ** 2 * (a + 2)
    for m in ("auto", "bareiss", "cofactors", "sarrus"):
        res = Determinant(A, method=m).run()
        assert sp.expand(res.value - attendu) == 0
    res = Determinant(A).run()
    assert res.method == "bareiss"
    assert res.value == attendu
    assert dict(res.factors) == {a - 1: 2, a + 2: 1}
    assert A.det() == attendu


def test_quatre_methodes_egales_en_3x3_et_trois_en_4x4() -> None:
    a, b = symbols("a b")
    A3 = Matrix([[a, b, 1], [2, a, b], [1, 0, a + b]])
    valeurs = {m: sp.expand(Determinant(A3, method=m).run().value) for m in ("bareiss", "cofactors", "sarrus")}
    assert len(set(valeurs.values())) == 1
    N3 = Matrix([[2, 1, 3], [0, 4, 5], [1, 0, 6]])
    assert {Determinant(N3, method=m).run().value for m in ("bareiss", "elimination", "cofactors", "sarrus")} == {41}
    A4 = Matrix([[1, 2, 0, 1], [0, a, 1, 2], [3, 0, 1, b], [1, 1, 1, 1]])
    valeurs4 = {sp.expand(Determinant(A4, method=m).run().value) for m in ("bareiss", "cofactors")}
    assert valeurs4 == {sp.expand(sp.Matrix(A4.entries_grid).det())}


def test_bareiss_coefficients_intermediaires_polynomiaux() -> None:
    a, b = symbols("a b")
    A = Matrix([[a, 1, b, 2], [1, a, 1, b], [b, 1, a, 1], [2, b, 1, a]])
    with tracing(level=3) as t:
        res = Determinant(A, method="bareiss").run()
    valeurs = []

    def parcourir(noeud):  # type: ignore[no-untyped-def]
        if noeud.message_key == "det.bareiss_entry":
            valeurs.append(noeud.params["value"])
        for enfant in noeud.children:
            parcourir(enfant)

    parcourir(t.tree)
    assert valeurs, "aucune étape de Bareiss tracée"
    assert all(sp.fraction(sp.together(v))[1] == 1 for v in valeurs)
    assert sp.expand(res.value - sp.Matrix(A.entries_grid).det()) == 0


def test_proprietes_du_determinant() -> None:
    (a,) = symbols("a")
    A = Matrix([[a, 2, 0], [1, 3, a], [0, 1, 1]])
    B = Matrix([[1, 0, 2], [a, 1, 0], [1, 1, 1]])
    assert sp.expand((A @ B).det() - A.det() * B.det()) == 0
    assert sp.expand(A.T.det() - A.det()) == 0
    echange = Matrix([A.row(1).entries, A.row(0).entries, A.row(2).entries])
    assert sp.expand(echange.det() + A.det()) == 0
    triangulaire = Matrix([[2, 5, 7], [0, 3, 1], [0, 0, a]])
    assert triangulaire.det() == 6 * a


def test_cas_limites() -> None:
    (a,) = symbols("a")
    assert Matrix.zeros(3, 3).det() == 0
    assert Matrix([[7]]).det() == 7
    assert Matrix([[0, 1], [1, 0]]).det() == -1
    # Pivot identiquement nul : Bareiss échange les lignes
    assert Determinant(Matrix([[0, a], [a, 0]]), method="bareiss").run().value == -(a**2)
    with pytest.raises(DimensionMismatchError):
        Determinant(Matrix([[1, 2, 3], [4, 5, 6]]))
    with pytest.raises(DimensionMismatchError):
        Determinant(Matrix([[1, 2], [3, 4]]), method="sarrus")
    with pytest.raises(PedagopyError, match="bareiss"):
        Determinant(Matrix.identity(5), method="cofactors")
    with pytest.raises(ValueError):
        Determinant(Matrix.identity(2), method="laplace")  # type: ignore[arg-type]


def test_nombre_d_echanges_annonce() -> None:
    # Deux échanges (pivots les plus simples) : signe +, et la trace annonce bien 2 échanges
    res = Determinant(Matrix([[2, 4, 1], [1, 3, 2], [0, 1, 5]]), method="elimination").run()
    texte = res.explain(level=1).to_text()
    assert texte.count("On échange les lignes") == 2
    assert "(2 échange(s) de lignes)" in texte
    assert res.value == 7


def test_elimination_interrompue_sur_pivot_conditionnel() -> None:
    (a,) = symbols("a")
    A = Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]])
    with pytest.raises(PedagopyError, match="method='bareiss'"):
        Determinant(A, method="elimination").run()
    # Avec une hypothèse qui tranche les pivots, l'élimination aboutit
    res = Determinant(A, method="elimination", assumptions={"a": 3}).run()
    assert res.value == 20


def test_zeros_et_discussion_inversible() -> None:
    (a,) = symbols("a")
    res = Determinant(Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]])).run()
    assert {str(c) for c in res.zeros()} == {"a = 1", "a = −2"}
    inversible = res.zeros(split=True)
    assert isinstance(inversible, CaseSplit)
    assert inversible.at(a=0) is True
    assert inversible.at(a=1) is False
    assert inversible.at(a=-2) is False
    assert Determinant(Matrix.identity(3)).run().zeros() == ()
    assert Determinant(Matrix.identity(3)).run().zeros(split=True) is True
    nul = Determinant(Matrix([[a, 2 * a], [1, 2]])).run()
    assert nul.value == 0
    assert len(nul.zeros()) == 1 and nul.zeros()[0].is_trivial


def test_domaine_des_coefficients() -> None:
    (a,) = symbols("a")
    A = Matrix([[1 / (a - 1), 1], [0, 1]])
    with tracing(level=1) as t:
        res = Determinant(A).run()
    assert sp.simplify(res.value - 1 / (a - 1)) == 0
    assert any(c.message_key == "det.domain" for c in t.tree.children)
    with pytest.raises(PedagopyError, match="a ≠ 1"):
        Determinant(A, assumptions={"a": 1}).run()


def test_trace_verification_et_resultat() -> None:
    res = Determinant(Matrix([[2, 1, 3], [0, 4, 5], [1, 0, 6]]), method="sarrus").run()
    assert isinstance(res, DetResult)
    texte = res.explain(level=1).to_text()
    assert "Règle de Sarrus" in texte and "det A = 41" in texte
    assert res.explain(level=0).to_text() == "det A = 41 (méthode : Sarrus)"
    assert "résultat confirmé" in res.verify().to_text()
    # La colonne 2 a deux zéros, aucune ligne n'en a plus d'un : développement suivant la colonne 2
    cof = Determinant(Matrix([[1, 0, 2], [3, 0, 4], [5, 6, 7]]), method="cofactors").run()
    assert "colonne 2" in cof.explain(level=1).to_text()
    assert cof.value == 12
    # À égalité entre une ligne et une colonne, on développe suivant la ligne
    egalite = Determinant(Matrix([[1, 0, 2], [0, 3, 0], [4, 0, 5]]), method="cofactors").run()
    assert "ligne 2" in egalite.explain(level=1).to_text()
