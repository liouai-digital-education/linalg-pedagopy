"""Moteurs de rendu et internationalisation (Couche 4)."""

from __future__ import annotations

from linalg_pedagopy.render.explanation import Explanation
from linalg_pedagopy.render.html import render_casesplit_html, render_step_html
from linalg_pedagopy.render.latex import (
    format_matrix_latex,
    format_value_latex,
    render_casesplit_latex,
    render_step_latex,
)
from linalg_pedagopy.render.markdown import (
    render_casesplit_markdown,
    render_step_markdown,
)
from linalg_pedagopy.render.text import (
    format_matrix_inline_text,
    format_value_text,
    load_catalog,
    render_casesplit_text,
    render_step_text,
    translate,
)

__all__ = [
    "Explanation",
    "format_matrix_inline_text",
    "format_matrix_latex",
    "format_value_latex",
    "format_value_text",
    "load_catalog",
    "render_casesplit_html",
    "render_casesplit_latex",
    "render_casesplit_markdown",
    "render_casesplit_text",
    "render_step_html",
    "render_step_latex",
    "render_step_markdown",
    "render_step_text",
    "translate",
]
