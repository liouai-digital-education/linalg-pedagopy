"""Trace d'un algorithme d'élimination présentée en tableau.

Une ligne par opération élémentaire (échange, dilatation, transvection, étape de Bareiss),
avec les colonnes N°, Colonne, Pivot, Opération, But et Matrice obtenue. Les autres étapes
visibles au niveau demandé (colonne sans pivot, noyau, résultat…) deviennent des lignes de
commentaire, avec leur matrice éventuelle. Une discussion par cas donne un tableau par branche.

Le tableau est tiré de la trace telle qu'elle est : aucun algorithme n'est modifié. Il couvre
Gauss-Jordan et le déterminant (élimination, Bareiss) ; les autres procédures donnent un
tableau de commentaires.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, replace
from typing import Any

import sympy as sp

from linalg_pedagopy.core.cases import CaseSplit
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.render.html import _MATHJAX_FOOT, _MATHJAX_HEAD
from linalg_pedagopy.render.latex import _latex_escape_text, format_matrix_latex
from linalg_pedagopy.render.text import format_conditions_latex, format_conditions_text, render_result_text, translate
from linalg_pedagopy.trace.step import Highlight, Step

# Opérations élémentaires : suffixe de la clé de trace
_OPERATIONS = ("row_swap", "row_scale", "row_add", "bareiss_step")
# Étapes absorbées par le tableau (colonne et pivot, matrice de départ)
_ABSORBEES = ("column_step", "pivot_chosen", "pivot")

_TABLE_CSS = """
<style>
  table.pedagopy-table { border-collapse: collapse; margin: 0.6rem 0 1.4rem; }
  table.pedagopy-table th, table.pedagopy-table td { border: 1px solid #ccc; padding: 0.3rem 0.6rem; vertical-align: middle; }
  table.pedagopy-table th { background: #f3f3f3; }
  table.pedagopy-table td.pedagopy-but { color: #555; font-size: 0.92em; }
  table.pedagopy-table td.pedagopy-commentaire { font-style: italic; color: #444; }
</style>
"""


@dataclass(frozen=True)
class TableRow:
    """Ligne du tableau : opération élémentaire (``op``), matrice de départ (``start``) ou commentaire."""

    kind: str
    text: str
    number: int | None = None
    column: int | None = None
    pivot: tuple[sp.Expr, tuple[int, int]] | None = None
    operation_latex: str | None = None
    matrix: Matrix | None = None
    highlight: Highlight | None = None


@dataclass(frozen=True)
class TableSection:
    """Tableau d'une trace ; ``heading`` (texte et LaTeX) pour une branche de discussion."""

    rows: tuple[TableRow, ...]
    heading: tuple[str, str] | None = None


@dataclass(frozen=True)
class TraceTable:
    """Trace présentée en tableau, rendue en HTML, Markdown ou LaTeX."""

    sections: tuple[TableSection, ...]
    locale: str | None = None

    def _headers(self) -> list[str]:
        return [
            translate(f"table.header_{k}", locale=self.locale)
            for k in ("number", "column", "pivot", "operation", "purpose", "matrix")
        ]

    def to_html(self, *, standalone: bool = False) -> str:
        """Tableau HTML ; formules en LaTeX pour MathJax (affichage dans JupyterLab)."""
        parts: list[str] = []
        ths = "".join(f"<th>{html.escape(h)}</th>" for h in self._headers())
        for sec in self.sections:
            if sec.heading is not None:
                parts.append(f"<h4>Cas \\({sec.heading[1]}\\)</h4>")
            trs = []
            for row in sec.rows:
                mat = f"\\({_matrice_latex(row)}\\)" if row.matrix is not None else ""
                if row.kind != "op":
                    trs.append(
                        f"<tr><td colspan='5' class='pedagopy-commentaire'>{html.escape(row.text)}</td><td>{mat}</td></tr>"
                    )
                    continue
                pivot = _pivot(row, "\\(", "\\)")
                trs.append(
                    "<tr>"
                    f"<td>{row.number}</td><td>{_colonne(row)}</td><td>{pivot}</td>"
                    f"<td>\\({row.operation_latex}\\)</td><td class='pedagopy-but'>{html.escape(row.text)}</td>"
                    f"<td>{mat}</td></tr>"
                )
            parts.append(
                f"<table class='pedagopy-table'><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
            )
        body = _TABLE_CSS + "\n".join(parts)
        return _MATHJAX_HEAD + body + _MATHJAX_FOOT if standalone else body

    def to_markdown(self) -> str:
        """Tableau Markdown, formules entre $…$ (sans « | », réservé aux séparateurs de cellules)."""
        out: list[str] = []
        entete = "| " + " | ".join(self._headers()) + " |"
        regle = "|---:|:---:|:---:|:---|:---|:---:|"
        for sec in self.sections:
            if sec.heading is not None:
                out += [f"#### Cas ${_sans_barre(sec.heading[1])}$", ""]
            out += [entete, regle]
            for row in sec.rows:
                mat = f"${_sans_barre(_matrice_latex(row, markdown=True))}$" if row.matrix is not None else ""
                texte = row.text.replace("|", "\\|")
                if row.kind != "op":
                    out.append(f"|  |  |  | *{texte}* |  | {mat} |")
                    continue
                op = _sans_barre(row.operation_latex or "")
                out.append(
                    f"| {row.number} | {_colonne(row)} | {_pivot(row, '$', '$', markdown=True)} | ${op}$ | {texte} | {mat} |"
                )
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def to_latex(self, *, standalone: bool = False) -> str:
        """Tableau LaTeX (``longtable``). Paquets : longtable, array, amsmath, xcolor.

        Les commentaires contiennent des caractères Unicode (←, ≠, √…) : compiler avec
        LuaLaTeX ou XeLaTeX.
        """
        lignes: list[str] = []
        entete = " & ".join(f"\\textbf{{{_latex_escape_text(h)}}}" for h in self._headers()) + " \\\\ \\hline"
        for sec in self.sections:
            if sec.heading is not None:
                lignes.append(f"\\paragraph{{Cas ${sec.heading[1]}$}}")
            lignes += [
                "\\begin{longtable}{r c c l p{4.2cm} c}",
                "\\hline",
                entete,
                "\\endhead",
            ]
            for row in sec.rows:
                mat = f"${_matrice_latex(row)}$" if row.matrix is not None else ""
                texte = _latex_escape_text(row.text)
                if row.kind != "op":
                    lignes.append(f"\\multicolumn{{5}}{{p{{11cm}}}}{{\\emph{{{texte}}}}} & {mat} \\\\")
                    continue
                lignes.append(
                    f"{row.number} & {_colonne(row)} & {_pivot(row, '$', '$')} & ${row.operation_latex}$ & {texte} & {mat} \\\\"
                )
            lignes += ["\\hline", "\\end{longtable}", ""]
        corps = "\n".join(lignes)
        if not standalone:
            return corps
        return (
            "\\documentclass{article}\n\\usepackage{longtable,array,amsmath,xcolor}\n"
            "\\usepackage[margin=1.5cm,landscape]{geometry}\n\\begin{document}\n" + corps + "\n\\end{document}\n"
        )

    def _repr_html_(self) -> str:
        return self.to_html()

    def __str__(self) -> str:
        return self.to_markdown()


def _colonne(row: TableRow) -> str:
    return str(row.column) if row.column is not None else ""


def _pivot(row: TableRow, ouvre: str, ferme: str, *, markdown: bool = False) -> str:
    if row.pivot is None:
        return ""
    valeur, (i, j) = row.pivot
    tex = sp.latex(valeur)
    if markdown:
        tex = _sans_barre(tex)
    return f"{ouvre}{tex}{ferme} en ({i + 1},{j + 1})"


def _sans_barre(tex: str) -> str:
    """Remplace « | » par \\vert : en Markdown, « | » sépare les cellules du tableau."""
    return tex.replace("|", "\\vert ")


def _matrice_latex(row: TableRow, *, markdown: bool = False) -> str:
    """Matrice de la ligne, pivot encadré et lignes modifiées en couleur, sans la flèche d'opération."""
    assert row.matrix is not None
    hl = replace(row.highlight, operation_latex=None) if row.highlight is not None else None
    if not markdown or hl is None or hl.augmented_split is None:
        return format_matrix_latex(row.matrix, hl)
    # Matrice augmentée en Markdown : deux blocs séparés par \middle\vert (la spécification
    # « {ccc|c} » contiendrait un « | »)
    k = hl.augmented_split
    gauche = format_matrix_latex(row.matrix[:, :k], replace(hl, augmented_split=None))
    droite = format_matrix_latex(row.matrix[:, k:], replace(hl, augmented_split=None, pivot=None))
    return (
        gauche.replace("\\left[", "\\left[", 1).replace("\\right]", "", 1)
        + "\\,\\middle\\vert\\,"
        + droite.replace("\\left[", "", 1)
    )


def _matrice_du_cliche(step: Step) -> Matrix | None:
    for valeur in step.snapshot.values():
        if isinstance(valeur, Matrix):
            return valeur
    return None


def _suffixe(cle: str) -> str:
    return cle.rsplit(".", 1)[-1]


def _pivots_par_colonne(step: Step, acc: dict[int, tuple[sp.Expr, tuple[int, int]]]) -> None:
    """Pivot annoncé pour chaque colonne (avant filtrage par niveau : il est de niveau 2)."""
    for c in step.children:
        suf = _suffixe(c.message_key)
        if suf == "pivot_chosen":
            col = int(c.params["col"]) - 1
            acc[col] = (c.params["pivot"], (int(c.params["row"]) - 1, col))
        elif suf == "pivot" and "col" in c.params:
            col = int(c.params["col"]) - 1
            acc[col] = (c.params["pivot"], (col, col))
        elif suf == "bareiss_step":
            k = int(c.params["k"]) - 1
            acc[k] = (c.params["pivot"], (k, k))
        _pivots_par_colonne(c, acc)


def _operation_bareiss(step: Step) -> str:
    k = int(step.params["k"])
    p = sp.latex(step.params["pivot"])
    q = sp.latex(step.params["previous"])
    return f"L_i \\leftarrow \\frac{{{p}\\,L_i - m_{{i{k}}}\\,L_{{{k}}}}}{{{q}}},\\ i > {k}"


def _but(step: Step, column: int | None, locale: str | None) -> str:
    prefixe, suf = step.message_key.rsplit(".", 1)
    params: dict[str, Any] = dict(step.params)
    params["col"] = column if column is not None else ""
    cle = f"table.{prefixe}_{suf}"
    texte = translate(cle, params, locale=locale)
    if texte.startswith(cle):  # pas de variante propre à la procédure
        texte = translate(f"table.{suf}", params, locale=locale)
    return texte


def _lignes(trace: Step, level: int, locale: str | None) -> list[TableRow]:
    pivots: dict[int, tuple[sp.Expr, tuple[int, int]]] = {}
    _pivots_par_colonne(trace, pivots)
    rows: list[TableRow] = []
    numero = 0

    def visiter(step: Step) -> None:
        nonlocal numero
        for c in step.children:
            suf = _suffixe(c.message_key)
            if suf == "start":
                rows.append(
                    TableRow(
                        kind="start",
                        text=translate("table.start", locale=locale),
                        matrix=_matrice_du_cliche(c),
                        highlight=Highlight(augmented_split=c.highlight.augmented_split) if c.highlight else None,
                    )
                )
            elif suf in _OPERATIONS:
                numero += 1
                hl = c.highlight
                col = hl.pivot[1] if hl is not None and hl.pivot is not None else None
                op = _operation_bareiss(c) if suf == "bareiss_step" else (hl.operation_latex if hl else "") or ""
                rows.append(
                    TableRow(
                        kind="op",
                        number=numero,
                        column=col + 1 if col is not None else None,
                        pivot=pivots.get(col) if col is not None else None,
                        operation_latex=op,
                        text=_but(c, col + 1 if col is not None else None, locale),
                        matrix=_matrice_du_cliche(c),
                        highlight=hl,
                    )
                )
            elif suf not in _ABSORBEES and c.level <= level:
                rows.append(
                    TableRow(
                        kind="comment",
                        text=translate(c.message_key, c.params, locale=locale),
                        matrix=_matrice_du_cliche(c),
                        highlight=c.highlight,
                    )
                )
            visiter(c)

    visiter(trace)
    return rows


def build_table(source: Any, *, level: int = 1, locale: str | None = None) -> TraceTable:
    """Tableau d'une trace (``Step``), d'une discussion par cas (``CaseSplit``) ou d'un résultat seul."""
    if isinstance(source, CaseSplit):
        sections = []
        for br in source.branches:
            heading = (
                format_conditions_text([br.condition]) + (" (générique)" if br.condition.is_generic else ""),
                format_conditions_latex([br.condition]) + (" \\text{ (générique)}" if br.condition.is_generic else ""),
            )
            if isinstance(br.trace, Step):
                rows = tuple(_lignes(br.trace, level, locale))
            else:
                rows = (TableRow(kind="comment", text=render_result_text(br.result)),)
            sections.append(TableSection(rows=rows, heading=heading))
        return TraceTable(sections=tuple(sections), locale=locale)
    if isinstance(source, Step):
        return TraceTable(sections=(TableSection(rows=tuple(_lignes(source, level, locale))),), locale=locale)
    return TraceTable(
        sections=(TableSection(rows=(TableRow(kind="comment", text=render_result_text(source)),)),), locale=locale
    )
