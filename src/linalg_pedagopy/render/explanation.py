"""Objet Explanation retourné par explain() et verify() (§5.5)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from linalg_pedagopy.core.cases import CaseSplit, register_casesplit_explain_hook
from linalg_pedagopy.render.html import render_casesplit_html, render_step_html
from linalg_pedagopy.render.latex import render_casesplit_latex, render_step_latex
from linalg_pedagopy.render.markdown import (
    render_casesplit_markdown,
    render_step_markdown,
)
from linalg_pedagopy.render.text import render_casesplit_text, render_step_text
from linalg_pedagopy.trace.step import Step


@dataclass(frozen=True)
class Explanation:
    """Représentation multi-format d'une trace de calcul ou d'une discussion par cas (§5.5)."""

    source: Step | CaseSplit[Any]
    level: int = 1
    fmt: str = "auto"
    locale: str | None = None

    def to_text(self, level: int | None = None) -> str:
        """Produit le rendu texte Unicode pour le terminal."""
        lvl = self.level if level is None else level
        if isinstance(self.source, CaseSplit):
            return render_casesplit_text(self.source, max_level=lvl, locale=self.locale)
        return render_step_text(self.source, max_level=lvl, locale=self.locale)

    def to_latex(self, level: int | None = None) -> str:
        """Produit le rendu LaTeX complet."""
        lvl = self.level if level is None else level
        if isinstance(self.source, CaseSplit):
            return render_casesplit_latex(self.source, max_level=lvl, locale=self.locale)
        return render_step_latex(self.source, max_level=lvl, locale=self.locale)

    def to_markdown(self, level: int | None = None) -> str:
        """Produit le rendu Markdown avec formules LaTeX $...$ et $$...$$."""
        lvl = self.level if level is None else level
        if isinstance(self.source, CaseSplit):
            return render_casesplit_markdown(self.source, max_level=lvl, locale=self.locale)
        return render_step_markdown(self.source, max_level=lvl, locale=self.locale)

    def to_html(self, level: int | None = None, *, standalone: bool = True) -> str:
        """Produit le rendu HTML avec MathJax et sections repliables."""
        lvl = self.level if level is None else level
        if isinstance(self.source, CaseSplit):
            return render_casesplit_html(
                self.source, max_level=lvl, locale=self.locale, standalone=standalone
            )
        return render_step_html(
            self.source, max_level=lvl, locale=self.locale, standalone=standalone
        )

    def save(self, path: str | Path, *, fmt: str | None = None) -> Path:
        """Sauvegarde l'explication dans un fichier (.txt, .tex, .md, .html)."""
        target = Path(path)
        chosen = fmt
        if chosen is None:
            ext = target.suffix.lower()
            if ext == ".tex":
                chosen = "latex"
            elif ext in (".md", ".markdown"):
                chosen = "markdown"
            elif ext in (".html", ".htm"):
                chosen = "html"
            else:
                chosen = "text"

        if chosen == "latex":
            content = self.to_latex()
        elif chosen == "markdown":
            content = self.to_markdown()
        elif chosen == "html":
            content = self.to_html(standalone=True)
        else:
            content = self.to_text()

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def _repr_markdown_(self) -> str:
        """Rendu automatique dans JupyterLab (§5.5)."""
        return self.to_markdown()

    def __str__(self) -> str:
        if self.fmt == "latex":
            return self.to_latex()
        if self.fmt == "markdown":
            return self.to_markdown()
        if self.fmt == "html":
            return self.to_html()
        return self.to_text()

    def __repr__(self) -> str:
        return self.to_text()


def _casesplit_hook(cs: CaseSplit[Any], level: int, fmt: str) -> Explanation:
    return Explanation(source=cs, level=level, fmt=fmt)


def _step_hook(step: Step, level: int, fmt: str) -> Explanation:
    return Explanation(source=step, level=level, fmt=fmt)


register_casesplit_explain_hook(_casesplit_hook)
from linalg_pedagopy.algorithms.base import register_explain_step_hook  # noqa: E402

register_explain_step_hook(_step_hook)

