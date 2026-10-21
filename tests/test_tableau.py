"""Trace en tableau : ``explain().to_table()`` (Gauss-Jordan et déterminant).

Une ligne par opération élémentaire (N°, Colonne, Pivot, Opération, But, Matrice obtenue),
des lignes de commentaire pour les autres étapes visibles, un tableau par branche d'une
discussion par cas ; rendus HTML, Markdown et LaTeX.
"""

from __future__ import annotations

import re

import sympy as sp

from linalg_pedagopy import CaseSplit, Determinant, GaussJordan, Matrix, Vector, symbols
from linalg_pedagopy.render.table import TraceTable

a, = symbols("a")
A = Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
b = Vector([8, -11, -3])


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
                cellules = re.split(r"(?<!\\)\|", ligne)
                assert len(cellules) == 8, ligne  # 6 colonnes, plus les bords


def test_resultat_seul() -> None:
    res = GaussJordan(A, b).run()
    table = res.explain(level=0).to_table()
    assert len(table.sections[0].rows) >= 1
