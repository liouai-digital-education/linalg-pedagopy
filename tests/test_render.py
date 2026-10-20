"""Tests des moteurs de rendu render/ (texte, LaTeX, Markdown, HTML, Explanation.save)."""

from __future__ import annotations

from pathlib import Path

from linalg_pedagopy import GaussJordan, Highlight, Matrix, Vector
from linalg_pedagopy.render import format_matrix_latex


def test_render_text_latex_markdown_html_and_save(tmp_path: Path) -> None:
    A = Matrix([[1, 2], [3, 5]])
    b = Vector([5, 13])
    res = GaussJordan(A, b).run()
    exp = res.explain(level=2)

    txt = exp.to_text()
    assert "$$" not in txt
    assert "Gauss-Jordan" in txt

    tex = exp.to_latex()
    assert "\\left[\\begin{array}{cc|c}" in tex
    assert "\\boxed{" in tex
    assert "\\xrightarrow{" in tex

    md = exp.to_markdown()
    assert "$$" in md
    assert exp._repr_markdown_() == md

    htm = exp.to_html(standalone=True)
    assert "<details" in htm
    assert "MathJax" in htm

    # Sauvegarde dans les différents formats
    p_tex = exp.save(tmp_path / "trace.tex")
    p_md = exp.save(tmp_path / "trace.md")
    p_htm = exp.save(tmp_path / "trace.html")
    assert p_tex.exists() and "\\begin{itemize}" in p_tex.read_text(encoding="utf-8")
    assert p_md.exists() and "$$" in p_md.read_text(encoding="utf-8")
    assert p_htm.exists() and "<html" in p_htm.read_text(encoding="utf-8")


def test_format_augmented_matrix_latex_features() -> None:
    M = Matrix([[1, 2, 3], [0, 4, 5]])
    hl = Highlight(
        pivot=(1, 1),
        rows=(1,),
        augmented_split=2,
        operation_latex="L_2 \\leftarrow L_2 - 3 L_1",
    )
    tex = format_matrix_latex(M, hl)
    assert "\\begin{array}{cc|c}" in tex
    assert "\\boxed{4}" in tex
    assert "\\color{blue}{5}" in tex
    assert "\\xrightarrow{L_2 \\leftarrow L_2 - 3 L_1}" in tex


def test_explain_level_0_shows_result_only() -> None:
    A = Matrix([[1, 2], [3, 4]])
    res = GaussJordan(A, Vector([1, 1])).run()
    expl = res.explain(level=0)
    texte = expl.to_text()
    assert texte == "pivots non nuls, rang 2, solution unique\nx = ( −1, 1 )"
    # Aucune étape du calcul : ni opération sur les lignes, ni en-tête de procédure
    assert "←" not in texte and "Réduction" not in texte
    assert r"x = \left[" in expl.to_markdown()
    assert r"x = \left[" in expl.to_latex()
    html = expl.to_html(standalone=False)
    assert html.startswith("<div class='pedagopy-result'>") and r"\(x = " in html
    # Le niveau 1 garde la trace complète
    assert "Réduction de Gauss-Jordan" in res.explain(level=1).to_text()
