"""Regroupement à l'affichage des branches aux résultats identiques (étape 4.8 du plan v6).

Aux niveaux 0 et 1, les branches particulières dont le résumé est identique sont affichées
ensemble (« Cas a = 3, a = 2 ou a = 1 : … ») ; la branche générique reste seule et, à
partir du niveau 2, chaque branche garde sa trace. Le ``CaseSplit`` n'est pas modifié.
"""

from __future__ import annotations

from linalg_pedagopy import CaseSplit, Determinant, GaussJordan, Matrix, Vector, symbols

a, b = symbols("a b")
V = Matrix([[1, x, x**2, x**3] for x in (1, 2, 3, a)])


def _vandermonde() -> CaseSplit:
    res = GaussJordan(V, Vector([0, 0, 0, 1])).run()
    assert isinstance(res, CaseSplit)
    return res


def test_regroupement_en_texte() -> None:
    res = _vandermonde()
    texte = str(res)
    assert "Cas a = 3, a = 2 ou a = 1 : L4 devient (0 0 0 0 | 1)" in texte
    assert texte.count("Cas ") == 2
    assert "(générique)" in texte


def test_le_casesplit_n_est_pas_modifie() -> None:
    res = _vandermonde()
    assert len(res.branches) == 4
    assert [br.condition.format_text() for br in res.branches[1:]] == ["a = 3", "a = 2", "a = 1"]
    assert res.at(a=2).rank == 3


def test_pas_de_regroupement_au_niveau_2() -> None:
    texte = _vandermonde().explain(level=2).to_text()
    assert "ou a = 1" not in texte
    assert texte.count("Cas ") == 4


def test_conditions_composees_entre_parentheses() -> None:
    res = GaussJordan(Matrix([[1, 1, b**2], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3])).run()
    assert "Cas (a = 1 et b = 1) ou (a = 1 et b = −1) :" in str(res)


def test_autres_rendus() -> None:
    res = Determinant(Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]]), method="elimination").run()
    ex = res.explain(level=1)
    assert "a = -2 \\text{ ou } a = 1" in ex.to_latex()
    assert "a = -2 \\text{ ou } a = 1" in ex.to_markdown()
    assert "a = -2 \\text{ ou } a = 1" in ex.to_html()
    assert "Cas a = −2 ou a = 1 : det A = 0" in ex.to_text()
