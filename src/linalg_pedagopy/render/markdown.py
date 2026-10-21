"""Moteur de rendu Markdown avec formules LaTeX $...$ et $$...$$."""

from __future__ import annotations

from typing import Any

import sympy as sp

from linalg_pedagopy.core.cases import CaseSplit
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.latex import branch_summary_parts, format_matrix_latex, format_value_latex
from linalg_pedagopy.render.text import format_conditions_latex, group_branches, translate
from linalg_pedagopy.trace.step import Step


def render_step_markdown(
    step: Step,
    *,
    max_level: int = 1,
    locale: str | None = None,
) -> str:
    """Rend un arbre d'étapes Step en Markdown hiérarchique avec LaTeX."""
    filtered = step.filter_level(max_level)
    if filtered is None:
        return ""

    nodes = filtered.children if filtered.message_key == "trace.root" else (filtered,)
    lines: list[str] = []
    for node in nodes:
        lines.extend(_render_node_md(node, depth=0, locale=locale))
    return "\n".join(lines)


def _render_node_md(node: Step, *, depth: int, locale: str | None) -> list[str]:
    indent = "  " * depth
    msg = translate(node.message_key, node.params, locale=locale)
    lines = [f"{indent}- {msg}"]

    if "augmented_matrix" in node.snapshot and isinstance(node.snapshot["augmented_matrix"], Matrix):
        mat_tex = format_matrix_latex(node.snapshot["augmented_matrix"], node.highlight)
        lines.append(f"{indent}  $${mat_tex}$$")
    elif "matrix" in node.snapshot and isinstance(node.snapshot["matrix"], Matrix):
        mat_tex = format_matrix_latex(node.snapshot["matrix"], node.highlight)
        lines.append(f"{indent}  $${mat_tex}$$")
    elif "result" in node.snapshot and isinstance(node.snapshot["result"], (Matrix, Vector)):
        val_tex = format_value_latex(node.snapshot["result"])
        lines.append(f"{indent}  $${val_tex}$$")

    for child in node.children:
        lines.extend(_render_node_md(child, depth=depth + 1, locale=locale))
    return lines


def render_casesplit_markdown(
    cs: CaseSplit[Any],
    *,
    max_level: int = 1,
    locale: str | None = None,
) -> str:
    """Rend un CaseSplit en Markdown avec LaTeX."""
    params_tex = ", ".join(sp.latex(s) for s in cs.parameters) if cs.parameters else "\\text{paramètres}"
    lines = [f"### Discussion selon ${params_tex}$", ""]
    for group in group_branches(cs, max_level=max_level):
        branch = group[0]
        cond_tex = format_conditions_latex([b.condition for b in group])
        gen_tag = " (générique)" if branch.condition.is_generic else ""
        summary_lines = [
            (f"${tex}$" if tex else txt) for txt, tex in branch_summary_parts(branch.result)
        ]
        first = summary_lines[0] if summary_lines else ""
        lines.append(f"- **Cas ${cond_tex}${gen_tag}** : {first}")
        for extra in summary_lines[1:]:
            lines.append(f"  - {extra}")
        if max_level >= 2 and isinstance(branch.trace, Step):
            sub_md = render_step_markdown(branch.trace, max_level=max_level, locale=locale)
            if sub_md:
                for sl in sub_md.splitlines():
                    lines.append("  " + sl)
    return "\n".join(lines)


def render_result_markdown(res: Any) -> str:
    """Niveau 0 : résultat seul, sans les étapes du calcul."""
    return "\n\n".join((f"${tex}$" if tex else txt) for txt, tex in branch_summary_parts(res))
