"""Moteur de rendu HTML avec MathJax et sections repliables <details>."""

from __future__ import annotations

import html
from typing import Any

import sympy as sp

from linalg_pedagopy.core.cases import CaseSplit
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.latex import branch_summary_parts, format_matrix_latex, format_value_latex
from linalg_pedagopy.render.text import format_conditions_latex, group_branches, translate
from linalg_pedagopy.trace.step import Step

_MATHJAX_HEAD = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Explication — linalg_pedagopy</title>
  <script>
    window.MathJax = {
      tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] }
    };
  </script>
  <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; margin: 1.5rem; }
    details { margin-left: 1rem; margin-top: 0.4rem; }
    summary { cursor: pointer; font-weight: 500; }
    .pedagopy-step { margin: 0.3rem 0; }
    .pedagopy-math { margin: 0.5rem 0 0.5rem 1.2rem; }
  </style>
</head>
<body>
"""

_MATHJAX_FOOT = """
</body>
</html>"""


def render_step_html(
    step: Step,
    *,
    max_level: int = 1,
    locale: str | None = None,
    standalone: bool = True,
) -> str:
    """Rend un arbre d'étapes Step en HTML repliable avec MathJax."""
    filtered = step.filter_level(max_level)
    if filtered is None:
        body = "<div class='pedagopy-explanation'></div>"
    else:
        nodes = filtered.children if filtered.message_key == "trace.root" else (filtered,)
        parts = [_render_node_html(n, locale=locale) for n in nodes]
        body = "<div class='pedagopy-explanation'>\n" + "\n".join(parts) + "\n</div>"

    if standalone:
        return _MATHJAX_HEAD + body + _MATHJAX_FOOT
    return body


def _render_node_html(node: Step, *, locale: str | None) -> str:
    msg = html.escape(translate(node.message_key, node.params, locale=locale))
    math_block = ""
    if "augmented_matrix" in node.snapshot and isinstance(node.snapshot["augmented_matrix"], Matrix):
        mat_tex = format_matrix_latex(node.snapshot["augmented_matrix"], node.highlight)
        math_block = f"<div class='pedagopy-math'>\\[{mat_tex}\\]</div>"
    elif "matrix" in node.snapshot and isinstance(node.snapshot["matrix"], Matrix):
        mat_tex = format_matrix_latex(node.snapshot["matrix"], node.highlight)
        math_block = f"<div class='pedagopy-math'>\\[{mat_tex}\\]</div>"
    elif "result" in node.snapshot and isinstance(node.snapshot["result"], (Matrix, Vector)):
        val_tex = format_value_latex(node.snapshot["result"])
        math_block = f"<div class='pedagopy-math'>\\[{val_tex}\\]</div>"

    if node.children:
        children_html = "\n".join(_render_node_html(c, locale=locale) for c in node.children)
        return (
            f"<details open>\n"
            f"  <summary>{msg}</summary>\n"
            f"  {math_block}\n"
            f"  {children_html}\n"
            f"</details>"
        )
    return f"<div class='pedagopy-step'>{msg}{math_block}</div>"


def render_casesplit_html(
    cs: CaseSplit[Any],
    *,
    max_level: int = 1,
    locale: str | None = None,
    standalone: bool = True,
) -> str:
    """Rend une discussion par cas CaseSplit en HTML avec MathJax."""
    params_tex = ", ".join(sp.latex(s) for s in cs.parameters) if cs.parameters else "\\text{paramètres}"
    items: list[str] = [f"<h3>Discussion selon \\({params_tex}\\)</h3>", "<ul>"]
    for group in group_branches(cs, max_level=max_level):
        branch = group[0]
        cond_tex = format_conditions_latex([b.condition for b in group])
        gen_tag = " (générique)" if branch.condition.is_generic else ""
        summary_html = "<br>".join(
            (f"\\({tex}\\)" if tex else html.escape(txt))
            for txt, tex in branch_summary_parts(branch.result)
        )
        sub_html = ""
        if max_level >= 2 and isinstance(branch.trace, Step):
            sub_html = render_step_html(
                branch.trace, max_level=max_level, locale=locale, standalone=False
            )
        items.append(
            f"<li><strong>Cas \\({cond_tex}\\){html.escape(gen_tag)}</strong> : {summary_html}{sub_html}</li>"
        )
    items.append("</ul>")
    body = "<div class='pedagopy-casesplit'>\n" + "\n".join(items) + "\n</div>"
    if standalone:
        return _MATHJAX_HEAD + body + _MATHJAX_FOOT
    return body


def render_result_html(res: Any, *, standalone: bool = True) -> str:
    """Niveau 0 : résultat seul, sans les étapes du calcul."""
    paragraphs = "\n".join(
        f"<p>\\({tex}\\)</p>" if tex else f"<p>{html.escape(txt)}</p>"
        for txt, tex in branch_summary_parts(res)
    )
    body = "<div class='pedagopy-result'>\n" + paragraphs + "\n</div>"
    if standalone:
        return _MATHJAX_HEAD + body + _MATHJAX_FOOT
    return body
