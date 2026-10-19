"""Moteur de rendu LaTeX (matrices augmentées, pivots encadrés, opérations sur flèches)."""

from __future__ import annotations

from typing import Any

import sympy as sp

from linalg_pedagopy.core.cases import CaseSplit
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.text import translate
from linalg_pedagopy.trace.step import Highlight, Step


def format_value_latex(val: Any) -> str:
    """Formate une valeur en LaTeX sans délimiteurs $."""
    if isinstance(val, Vector):
        rows_tex = " \\\\ ".join(sp.latex(e) for e in val.entries)
        return f"\\left[\\begin{{array}}{{c}} {rows_tex} \\end{{array}}\\right]"
    if isinstance(val, Matrix):
        return format_matrix_latex(val)
    if isinstance(val, sp.Basic):
        return sp.latex(val)
    if isinstance(val, (tuple, list)):
        return "\\left(" + ", ".join(format_value_latex(x) for x in val) + "\\right)"
    return str(val)


def format_matrix_latex(mat: Matrix, highlight: Highlight | None = None) -> str:
    """Formate une Matrix en LaTeX avec barre d'augmentation '|', pivot \\boxed et lignes colorées."""
    if mat.rows == 0 or mat.cols == 0:
        return "\\left[\\,\\right]"

    split_col = highlight.augmented_split if highlight is not None else None
    pivot_pos = highlight.pivot if highlight is not None else None
    high_rows = set(highlight.rows) if highlight is not None else set()

    if split_col is not None and 0 < split_col < mat.cols:
        col_spec = "c" * split_col + "|" + "c" * (mat.cols - split_col)
    else:
        col_spec = "c" * mat.cols

    row_strings: list[str] = []
    for i in range(mat.rows):
        cells: list[str] = []
        for j in range(mat.cols):
            cell_tex = sp.latex(mat[i, j])
            if pivot_pos is not None and pivot_pos == (i, j):
                cell_tex = f"\\boxed{{{cell_tex}}}"
            elif i in high_rows:
                cell_tex = f"\\color{{blue}}{{{cell_tex}}}"
            cells.append(cell_tex)
        row_strings.append(" & ".join(cells))

    body = " \\\\ ".join(row_strings)
    arr_tex = f"\\left[\\begin{{array}}{{{col_spec}}} {body} \\end{{array}}\\right]"
    if highlight is not None and highlight.operation_latex:
        return f"\\xrightarrow{{{highlight.operation_latex}}} {arr_tex}"
    return arr_tex


def render_step_latex(step: Step, *, max_level: int = 1, locale: str | None = None) -> str:
    """Rend un arbre d'étapes Step en environnement LaTeX itemize."""
    filtered = step.filter_level(max_level)
    if filtered is None:
        return ""

    nodes = filtered.children if filtered.message_key == "trace.root" else (filtered,)
    if not nodes:
        return ""

    lines = ["\\begin{itemize}"]
    for node in nodes:
        lines.extend(_render_node_latex(node, locale=locale))
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def _render_node_latex(node: Step, *, locale: str | None) -> list[str]:
    msg = translate(node.message_key, node.params, locale=locale)
    lines = [f"  \\item {msg}"]
    if "augmented_matrix" in node.snapshot and isinstance(node.snapshot["augmented_matrix"], Matrix):
        mat_tex = format_matrix_latex(node.snapshot["augmented_matrix"], node.highlight)
        lines.append(f"  \\[{mat_tex}\\]")
    elif "matrix" in node.snapshot and isinstance(node.snapshot["matrix"], Matrix):
        mat_tex = format_matrix_latex(node.snapshot["matrix"], node.highlight)
        lines.append(f"  \\[{mat_tex}\\]")
    elif "result" in node.snapshot and isinstance(node.snapshot["result"], (Matrix, Vector)):
        val_tex = format_value_latex(node.snapshot["result"])
        lines.append(f"  \\[{val_tex}\\]")

    if node.children:
        lines.append("  \\begin{itemize}")
        for child in node.children:
            for cl in _render_node_latex(child, locale=locale):
                lines.append("  " + cl)
        lines.append("  \\end{itemize}")
    return lines



def branch_summary_parts(result: Any) -> list[tuple[str, str]]:
    """Résumé d'une branche de CaseSplit sous forme de (texte, latex) par ligne.

    La partie texte est la phrase descriptive ; la partie LaTeX (éventuellement vide)
    contient la solution mise en forme mathématiquement, pour les rendus LaTeX,
    Markdown et HTML.
    """
    if hasattr(result, "_branch_summary_lines"):
        lines = list(result._branch_summary_lines())
    elif isinstance(result, (Matrix, Vector, sp.Basic)):
        return [("", format_value_latex(result))]
    else:
        lines = [str(result)]
    sol = getattr(result, "solution", None)
    parts: list[tuple[str, str]] = []
    for line in lines:
        if line.startswith("x = ") and sol is not None:
            if hasattr(sol, "x") and isinstance(getattr(sol, "x"), Vector):
                parts.append(("", "x = " + format_value_latex(sol.x)))
                continue
            if hasattr(sol, "x0") and hasattr(sol, "basis"):
                terms = [format_value_latex(sol.x0)] + [
                    f"t_{{{i + 1}}} {format_value_latex(v)}" for i, v in enumerate(sol.basis)
                ]
                parts.append(("", "x = " + " + ".join(terms)))
                continue
        parts.append((line, ""))
    return parts


def _latex_escape_text(s: str) -> str:
    """Échappe les caractères spéciaux LaTeX d'une phrase en texte."""
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"),
                 ("_", "\\_"), ("|", "\\textbar{}"), ("−", "-")):
        s = s.replace(a, b)
    return s


def render_casesplit_latex(
    cs: CaseSplit[Any],
    *,
    max_level: int = 1,
    locale: str | None = None,
) -> str:
    """Rend une discussion par cas CaseSplit en LaTeX."""
    params_tex = ", ".join(sp.latex(s) for s in cs.parameters) if cs.parameters else "\\text{paramètres}"
    lines = [f"\\textbf{{Discussion selon ${params_tex}$}}", "\\begin{itemize}"]
    for branch in cs.branches:
        cond_tex = branch.condition.format_latex()
        gen_tag = " \\text{ (générique)}" if branch.condition.is_generic else ""
        parts = branch_summary_parts(branch.result)
        summary_txt = " — ".join(
            (f"${tex}$" if tex else _latex_escape_text(txt)) for txt, tex in parts
        )
        lines.append(f"  \\item \\textbf{{Cas ${cond_tex}{gen_tag}$}} : {summary_txt}")
        if max_level >= 2 and isinstance(branch.trace, Step):
            sub_tex = render_step_latex(branch.trace, max_level=max_level, locale=locale)
            if sub_tex:
                lines.append(sub_tex)
    lines.append("\\end{itemize}")
    return "\n".join(lines)
