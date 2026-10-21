"""Trace en tableau : ``explain().to_table()``.

Une ligne par opération, colonnes propres à l'algorithme (élimination, Gram-Schmidt,
substitution), des lignes de commentaire pour les autres étapes visibles, un tableau par
branche d'une discussion par cas ; rendus HTML, Markdown et LaTeX.
"""

from __future__ import annotations

import re

import sympy as sp

from linalg_pedagopy import CaseSplit, Determinant, GaussJordan, Matrix, Vector, symbols
from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.algorithms.least_squares import LeastSquares
from linalg_pedagopy.algorithms.qr import QR
from linalg_pedagopy.algorithms.triangular import BackSubstitution, ForwardSubstitution
from linalg_pedagopy.render.table import TraceTable

a, = symbols("a")
A = Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
b = Vector([8, -11, -3])


def _nb_cellules(ligne: str) -> int:
    return len(re.split(r"(?<!\\)\|", ligne)) - 2  # sans les bords


def _ops(table: TraceTable, section: int = 0) -> list:  # type: ignore[type-arg]
    return [r for r in table.sections[section].rows if r.kind == "op"]


def test_lignes_de_gauss_jordan() -> None:
    table = GaussJordan(A, b).run().explain().to_table()
    rows = table.sections[0].rows
    assert rows[0].kind == "start" and rows[0].matrix == A.augment(b)
    ops = _ops(table)
    assert [r.number for r in ops] == list(range(1, 11))
    assert [r.column for r in ops] == [1, 1, 1, 2, 2, 2, 2, 3, 3, 3]
    # Pivot choisi en (3,2) puis amené en place par l'échange L2 ↔ L3
    assert ops[3].pivot == (2, (2, 1)) and "leftrightarrow" in (ops[3].operation_latex or "")
    assert ops[3].text == "amener le pivot en place"
    assert ops[0].text == "ramener le pivot à 1"
    assert ops[1].text == "annuler le coefficient (2,1)"
    assert ops[-1].matrix == Matrix([[1, 0, 0, 2], [0, 1, 0, 3], [0, 0, 1, -1]])


def test_niveau_ajoute_des_commentaires() -> None:
    M = Matrix([[1, 2, -1, 3, -1], [2, 4, -1, 7, 1], [-1, -2, 3, -1, 7]])
    res = GaussJordan(M).run()
    niveau1 = [r.text for r in res.explain(level=1).to_table().sections[0].rows if r.kind == "comment"]
    niveau2 = [r.text for r in res.explain(level=2).to_table().sections[0].rows if r.kind == "comment"]
    assert not any("variable x_2 libre" in t for t in niveau1)
    assert any("variable x_2 libre" in t for t in niveau2)
    assert any(t.startswith("Noyau : variables libres x2, x4, x5") for t in niveau2)
    # Les opérations sont les mêmes quel que soit le niveau
    assert len(_ops(res.explain(level=1).to_table())) == len(_ops(res.explain(level=2).to_table()))


def test_un_tableau_par_branche() -> None:
    res = GaussJordan(Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3])).run()
    assert isinstance(res, CaseSplit)
    table = res.explain().to_table()
    assert len(table.sections) == len(res.branches)
    assert table.sections[0].heading == ("a ≠ 1 (générique)", "a \\neq 1 \\text{ (générique)}")
    assert table.sections[1].heading is not None and table.sections[1].heading[0] == "a = 1"


def test_determinant_bareiss_et_elimination() -> None:
    bareiss = Determinant(Matrix([[0, a, 1], [1, 0, 2], [a, 1, 0]])).run().explain().to_table()
    ops = _ops(bareiss)
    assert ops[0].text == "amener le pivot en place ; le déterminant change de signe"
    assert ops[1].pivot == (1, (0, 0)) and "\\frac" in (ops[1].operation_latex or "")
    assert ops[2].pivot == (a, (1, 1))
    assert "division exacte par le pivot précédent" in ops[2].text
    elim = Determinant(Matrix([[2, 4, 1], [1, 3, 2], [0, 1, 5]]), method="elimination").run().explain().to_table()
    assert any(r.text.endswith("le déterminant ne change pas") for r in _ops(elim))
    assert all(r.pivot is not None for r in _ops(elim))


def test_rendus() -> None:
    table = GaussJordan(A, b).run().explain().to_table()
    html = table.to_html()
    assert html.count("<table class='pedagopy-table'>") == 1 and "<th>Pivot</th>" in html
    assert table._repr_html_() == html
    assert "MathJax" in table.to_html(standalone=True)
    latex = table.to_latex()
    assert latex.count("\\begin{longtable}") == 1 and "\\multicolumn{5}" in latex
    assert table.to_latex(standalone=True).startswith("\\documentclass")
    assert str(table) == table.to_markdown()


def test_markdown_sans_barre_dans_les_cellules() -> None:
    """« | » sépare les cellules : ni la matrice augmentée ni une valeur absolue ne doivent en contenir."""
    x, = symbols("x")
    res = GaussJordan(Matrix([[1, 1], [1, sp.Abs(x) + 2]]), Vector([1, 2])).run()
    assert "\\vert" in res.explain().to_table().to_markdown()  # |x| écrit \vert x\vert
    for md in (GaussJordan(A, b).run().explain().to_table().to_markdown(), res.explain().to_table().to_markdown()):
        for ligne in md.splitlines():
            if ligne.startswith("|"):
                assert _nb_cellules(ligne) == 6, ligne


def test_resultat_seul() -> None:
    res = GaussJordan(A, b).run()
    table = res.explain(level=0).to_table()
    assert len(table.sections[0].rows) >= 1


def test_inverse() -> None:
    table = GaussJordan(Matrix([[2, 1], [1, 1]]), Matrix.identity(2), compute_inverse=True).run().explain().to_table()
    assert [s.layout for s in table.sections] == ["elimination"]
    assert len(_ops(table)) == 4
    assert any(r.matrix == Matrix([[1, -1], [-1, 2]]) for r in table.sections[0].rows if r.kind == "comment")


FAMILLE = [Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([0, 1, 1])]


def test_gram_schmidt_normalisation_finale() -> None:
    table = GramSchmidt(FAMILLE).run().explain().to_table()
    assert table.sections[0].layout == "gram_schmidt"
    ops = _ops(table)
    assert [r.number for r in ops] == list(range(1, 7))
    assert ops[0].text == "premier vecteur : conservé tel quel" and ops[0].detail is None
    assert ops[2].operation_latex == "\\tilde q_{3} = a_{3} - r_{1,3}\\,\\tilde q_{1} - r_{2,3}\\,\\tilde q_{2}"
    assert ops[2].detail == "r_{1,3} = \\frac{1}{2}, r_{2,3} = \\frac{1}{3}"
    assert ops[2].matrix == Matrix([[sp.Rational(-2, 3)], [sp.Rational(2, 3)], [sp.Rational(2, 3)]])
    assert ops[3].text == "rendre le vecteur unitaire" and "\\sqrt{2}" in (ops[3].detail or "")
    # Le vecteur traité et les coefficients ne font pas de ligne à part
    textes = [r.text for r in table.sections[0].rows if r.kind == "comment"]
    assert not any("Étape i" in t or "Coefficient de projection" in t for t in textes)


def test_gram_schmidt_normalisation_a_chaque_etape() -> None:
    ops = _ops(GramSchmidt(FAMILLE, normalize="each").run().explain().to_table())
    # orthogonalisation et normalisation alternent ; projections sur les q_j unitaires
    assert [r.operation_latex.split(" =")[0] for r in ops] == [  # type: ignore[union-attr]
        "\\tilde q_{1}", "q_{1}", "\\tilde q_{2}", "q_{2}", "\\tilde q_{3}", "q_{3}"
    ]
    assert ops[2].operation_latex == "\\tilde q_{2} = a_{2} - r_{1,2}\\,q_{1}"


def test_gram_schmidt_famille_liee() -> None:
    table = GramSchmidt([Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([2, 1, 1])]).run().explain().to_table()
    assert _ops(table)[-1].matrix == Matrix([[0], [0], [0]])
    assert "la famille est liée" in table.sections[0].rows[-1].text


def test_substitution_arriere_et_avant() -> None:
    arriere = BackSubstitution(Matrix([[2, 1, 1], [0, 3, -1], [0, 0, 4]]), Vector([5, 2, 8])).run()
    ops = _ops(arriere.explain().to_table())
    assert [r.subject for r in ops] == ["x_{3}", "x_{2}", "x_{1}"]
    assert ops[0].operation_latex == "x_{3} = \\frac{8}{4}"
    assert ops[1].operation_latex == "x_{2} = \\frac{2 - \\left(-1\\right)\\,x_{3}}{3} = \\frac{2 - \\left(-2\\right)}{3}"
    assert ops[2].operation_latex == "x_{1} = \\frac{5 - x_{2} - x_{3}}{2} = \\frac{5 - \\frac{10}{3}}{2}"
    assert [r.detail for r in ops] == ["2", "\\frac{4}{3}", "\\frac{5}{6}"]
    avant = ForwardSubstitution(Matrix([[1, 0, 0], [2, 1, 0], [-1, 3, 2]]), Vector([1, 4, 6])).run()
    ops = _ops(avant.explain().to_table())
    assert ops[1].operation_latex == "x_{2} = 4 - 2\\,x_{1} = 4 - 2"


def test_un_tableau_par_algorithme_et_par_disposition() -> None:
    assert [s.layout for s in QR(Matrix([[1, -1], [1, 0], [1, 1]])).run().explain().to_table().sections] == [
        "gram_schmidt"
    ]
    A2, b2 = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]]), Vector([1, 2, 2, 4])
    assert [s.layout for s in LeastSquares(A2, b2, method="qr").run().explain().to_table().sections] == [
        "substitution"
    ]
    assert [s.layout for s in LeastSquares(A2, b2, method="normal").run().explain().to_table().sections] == [
        "elimination"
    ]


def test_rendus_des_autres_dispositions() -> None:
    gs = GramSchmidt(FAMILLE).run().explain().to_table()
    sub = BackSubstitution(Matrix([[2, 1], [0, 3]]), Vector([5, 3])).run().explain().to_table()
    assert "<th>Vecteur traité</th>" in gs.to_html() and "<th>Valeur</th>" in sub.to_html()
    assert "\\begin{longtable}{r c l l p{4cm} c}" in gs.to_latex()
    assert "\\multicolumn{4}" in sub.to_latex()
    for table, n in ((gs, 6), (sub, 5)):
        for ligne in table.to_markdown().splitlines():
            if ligne.startswith("|"):
                assert _nb_cellules(ligne) == n, ligne
