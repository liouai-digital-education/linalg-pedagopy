"""Rendu texte (terminal Unicode) et chargement des catalogues i18n."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import sympy as sp
import yaml

from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import CaseSplit
from linalg_pedagopy.core.field import pretty_expr
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import Highlight, Step

_LOCALES_DIR = Path(__file__).parent / "locales"


@lru_cache(maxsize=8)
def load_catalog(locale: str = "fr") -> dict[str, Any]:
    """Charge le fichier YAML de locale demandé (fr par défaut)."""
    path = _LOCALES_DIR / f"{locale}.yaml"
    if not path.exists():
        path = _LOCALES_DIR / "fr.yaml"
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def _lookup_key(catalog: Mapping[str, Any], dotted_key: str) -> str | None:
    curr: Any = catalog
    for part in dotted_key.split("."):
        if isinstance(curr, Mapping) and part in curr:
            curr = curr[part]
        else:
            return None
    return curr if isinstance(curr, str) else None


def format_value_text(val: Any) -> str:
    """Formate une valeur (Vector, Matrix, SymPy Expr) en texte Unicode sans LaTeX."""
    if isinstance(val, Vector):
        items = ", ".join(_pretty_scalar(e) for e in val.entries)
        return f"( {items} )"
    if isinstance(val, Matrix):
        return format_matrix_inline_text(val)
    if isinstance(val, sp.Basic):
        return _pretty_scalar(val)
    if isinstance(val, (tuple, list)):
        return "(" + ", ".join(format_value_text(x) for x in val) + ")"
    return str(val)


def _pretty_scalar(expr: sp.Basic) -> str:
    return pretty_expr(expr)


def format_matrix_inline_text(mat: Matrix, highlight: Highlight | None = None) -> str:
    """Formate une matrice (éventuellement augmentée) sur une ou plusieurs lignes Unicode."""
    split_col = highlight.augmented_split if highlight is not None else None
    rows_str: list[str] = []
    for r_idx in range(mat.rows):
        row = mat[r_idx]
        if split_col is not None and 0 < split_col < mat.cols:
            left = " ".join(str(e) for e in row[:split_col])
            right = " ".join(str(e) for e in row[split_col:])
            rows_str.append(f"({left} | {right})")
        else:
            rows_str.append("(" + " ".join(str(e) for e in row) + ")")
    return "[" + "; ".join(rows_str) + "]"


def translate(
    message_key: str,
    params: Mapping[str, Any] | None = None,
    *,
    locale: str | None = None,
) -> str:
    """Traduit une clé de message avec ses paramètres dans la locale active."""
    loc = locale or config.locale
    catalog = load_catalog(loc)
    template = _lookup_key(catalog, message_key)
    raw_params = dict(params) if params else {}
    formatted_params = {k: format_value_text(v) for k, v in raw_params.items()}
    if template is not None:
        try:
            return template.format(**formatted_params)
        except KeyError:
            return template
    if formatted_params:
        kv = ", ".join(f"{k}={v}" for k, v in formatted_params.items())
        return f"{message_key} ({kv})"
    return message_key


def render_step_text(step: Step, *, max_level: int = 1, locale: str | None = None) -> str:
    """Rend un arbre d'étapes Step en texte Unicode arborescent (├─ / └─)."""
    filtered = step.filter_level(max_level)
    if filtered is None:
        return ""

    if filtered.message_key == "trace.root":
        lines: list[str] = []
        children = filtered.children
        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            lines.extend(_render_node_lines(child, prefix="", is_last=is_last, is_root_child=True, locale=locale))
        return "\n".join(lines)

    return "\n".join(_render_node_lines(filtered, prefix="", is_last=True, is_root_child=True, locale=locale))


def _render_node_lines(
    node: Step,
    *,
    prefix: str,
    is_last: bool,
    is_root_child: bool,
    locale: str | None,
) -> list[str]:
    msg = translate(node.message_key, node.params, locale=locale)
    if is_root_child and not prefix:
        connector = ""
        child_prefix = ""
    else:
        connector = "└─ " if is_last else "├─ "
        child_prefix = prefix + ("   " if is_last else "│  ")

    lines = [f"{prefix}{connector}{msg}"]

    if "augmented_matrix" in node.snapshot and isinstance(node.snapshot["augmented_matrix"], Matrix):
        mat_str = format_matrix_inline_text(node.snapshot["augmented_matrix"], node.highlight)
        sub_indent = child_prefix if connector else "   "
        lines.append(f"{sub_indent}{mat_str}")

    for idx, child in enumerate(node.children):
        last_c = idx == len(node.children) - 1
        next_prefix = child_prefix if connector else ""
        lines.extend(
            _render_node_lines(
                child,
                prefix=next_prefix,
                is_last=last_c,
                is_root_child=False,
                locale=locale,
            )
        )
    return lines


def render_casesplit_text(
    cs: CaseSplit[Any],
    *,
    max_level: int = 1,
    locale: str | None = None,
) -> str:
    """Rend un CaseSplit en texte."""
    params_str = ", ".join(pretty_expr(s) for s in cs.parameters) if cs.parameters else "les paramètres"
    lines = [f"Discussion selon {params_str}"]
    n_branches = len(cs.branches)
    for idx, branch in enumerate(cs.branches):
        is_last = idx == n_branches - 1
        connector = "└─ " if is_last else "├─ "
        cont_prefix = "   " if is_last else "│  "
        cond_txt = branch.condition.format_text()
        gen_tag = " (générique)" if branch.condition.is_generic else ""
        summary_lines = _summarize_branch_result_text(branch.result)
        if summary_lines:
            first_summary = summary_lines[0]
            lines.append(f"{connector}Cas {cond_txt}{gen_tag} : {first_summary}")
            for extra in summary_lines[1:]:
                lines.append(f"{cont_prefix}  {extra}")
        else:
            lines.append(f"{connector}Cas {cond_txt}{gen_tag}")

        if max_level >= 2 and isinstance(branch.trace, Step):
            sub_txt = render_step_text(branch.trace, max_level=max_level, locale=locale)
            if sub_txt:
                for sub_line in sub_txt.splitlines():
                    lines.append(f"{cont_prefix}  {sub_line}")
    return "\n".join(lines)


def _summarize_branch_result_text(res: Any) -> list[str]:
    if hasattr(res, "_branch_summary_lines"):
        return list(res._branch_summary_lines())
    return [format_value_text(res)]
