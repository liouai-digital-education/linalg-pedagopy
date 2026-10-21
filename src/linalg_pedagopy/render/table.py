"""Trace d'un algorithme présentée en tableau.

Une ligne par opération, dont les colonnes dépendent de l'algorithme (disposition) :

- élimination (Gauss-Jordan, inverse, déterminant) : N°, Colonne, Pivot, Opération, But,
  Matrice obtenue ; une ligne par échange, dilatation, transvection ou étape de Bareiss ;
- Gram-Schmidt (et QR) : N°, Vecteur traité, Coefficients, Opération, But, Vecteur obtenu ;
  une ligne par orthogonalisation, une par normalisation ;
- substitution (systèmes triangulaires) : N°, Inconnue, Calcul, But, Valeur.

Les autres étapes visibles au niveau demandé (colonne sans pivot, noyau, résultat…) deviennent
des lignes de commentaire, avec leur matrice éventuelle. Une discussion par cas donne un tableau
par branche ; une trace qui enchaîne deux algorithmes (moindres carrés par QR) donne un tableau
par algorithme.

Le tableau est tiré de la trace telle qu'elle est : aucun algorithme n'est modifié.
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
# Étapes absorbées par le tableau (colonne et pivot, vecteur traité et coefficients)
_ABSORBEES = ("column_step", "pivot_chosen", "pivot", "vector_step", "proj_coeff", "proj_coeff_unit")


@dataclass(frozen=True)
class _Disposition:
    """Colonnes d'un tableau : en-têtes, cellules d'une ligne d'opération, formats Markdown et LaTeX."""

    headers: tuple[str, ...]
    cells: tuple[str, ...]  # champ de TableRow affiché dans chaque colonne
    markdown_rule: str
    latex_spec: str
    comment_col: int  # colonne du texte d'un commentaire en Markdown
    comment_width: str  # largeur du commentaire en LaTeX


_DISPOSITIONS = {
    "elimination": _Disposition(
        ("number", "column", "pivot", "operation", "purpose", "matrix"),
        ("number", "column", "pivot", "operation", "purpose", "matrix"),
        "|---:|:---:|:---:|:---|:---|:---:|",
        "r c c l p{4.2cm} c",
        3,
        "11cm",
    ),
    "gram_schmidt": _Disposition(
        ("number", "vector", "coefficients", "operation", "purpose", "vector_result"),
        ("number", "subject", "detail", "operation", "purpose", "matrix"),
        "|---:|:---:|:---|:---|:---|:---:|",
        "r c l l p{4cm} c",
        3,
        "12cm",
    ),
    "substitution": _Disposition(
        ("number", "unknown", "computation", "purpose", "value"),
        ("number", "subject", "operation", "purpose", "detail"),
        "|---:|:---:|:---|:---|:---:|",
        "r c l p{4cm} c",
        2,
        "10cm",
    ),
}

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
    subject: str | None = None  # LaTeX : vecteur traité, inconnue calculée
    detail: str | None = None  # LaTeX : coefficients de projection, norme
    layout: str | None = None  # disposition d'une ligne d'opération


@dataclass(frozen=True)
class TableSection:
    """Tableau d'une trace ; ``heading`` (texte et LaTeX) pour une branche de discussion."""

    rows: tuple[TableRow, ...]
    heading: tuple[str, str] | None = None
    layout: str = "elimination"


@dataclass(frozen=True)
class TraceTable:
    """Trace présentée en tableau, rendue en HTML, Markdown ou LaTeX."""

    sections: tuple[TableSection, ...]
    locale: str | None = None

    def _headers(self, sec: TableSection) -> list[str]:
        return [translate(f"table.header_{k}", locale=self.locale) for k in _DISPOSITIONS[sec.layout].headers]

    def to_html(self, *, standalone: bool = False) -> str:
        """Tableau HTML ; formules en LaTeX pour MathJax (affichage dans JupyterLab)."""
        parts: list[str] = []
        for sec in self.sections:
            disp = _DISPOSITIONS[sec.layout]
            ths = "".join(f"<th>{html.escape(h)}</th>" for h in self._headers(sec))
            if sec.heading is not None:
                parts.append(f"<h4>Cas \\({sec.heading[1]}\\)</h4>")
            trs = []
            for row in sec.rows:
                mat = f"\\({_matrice_latex(row)}\\)" if row.matrix is not None else ""
                if row.kind != "op":
                    trs.append(
                        f"<tr><td colspan='{len(disp.cells) - 1}' class='pedagopy-commentaire'>"
                        f"{html.escape(row.text)}</td><td>{mat}</td></tr>"
                    )
                    continue
                tds = []
                for champ in disp.cells:
                    if champ == "matrix":
                        tds.append(f"<td>{mat}</td>")
                    elif champ == "purpose":
                        tds.append(f"<td class='pedagopy-but'>{html.escape(row.text)}</td>")
                    else:
                        tds.append("<td>" + _cellule(row, champ, "\\(", "\\)") + "</td>")
                trs.append("<tr>" + "".join(tds) + "</tr>")
            parts.append(
                f"<table class='pedagopy-table'><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
            )
        body = _TABLE_CSS + "\n".join(parts)
        return _MATHJAX_HEAD + body + _MATHJAX_FOOT if standalone else body

    def to_markdown(self) -> str:
        """Tableau Markdown, formules entre $…$ (sans « | », réservé aux séparateurs de cellules)."""
        out: list[str] = []
        for sec in self.sections:
            disp = _DISPOSITIONS[sec.layout]
            if sec.heading is not None:
                out += [f"#### Cas ${_sans_barre(sec.heading[1])}$", ""]
            out += ["| " + " | ".join(self._headers(sec)) + " |", disp.markdown_rule]
            for row in sec.rows:
                mat = f"${_sans_barre(_matrice_latex(row, markdown=True))}$" if row.matrix is not None else ""
                texte = row.text.replace("|", "\\|")
                if row.kind != "op":
                    vides = [""] * (len(disp.cells) - 1)
                    vides[disp.comment_col] = f"*{texte}*"
                    out.append("| " + " | ".join(vides + [mat]) + " |")
                    continue
                cellules = []
                for champ in disp.cells:
                    if champ == "matrix":
                        cellules.append(mat)
                    elif champ == "purpose":
                        cellules.append(texte)
                    else:
                        cellules.append(_cellule(row, champ, "$", "$", markdown=True))
                out.append("| " + " | ".join(cellules) + " |")
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def to_latex(self, *, standalone: bool = False) -> str:
        """Tableau LaTeX (``longtable``). Paquets : longtable, array, amsmath, xcolor.

        Les commentaires contiennent des caractères Unicode (←, ≠, √…) : compiler avec
        LuaLaTeX ou XeLaTeX.
        """
        lignes: list[str] = []
        for sec in self.sections:
            disp = _DISPOSITIONS[sec.layout]
            entete = " & ".join(f"\\textbf{{{_latex_escape_text(h)}}}" for h in self._headers(sec)) + " \\\\ \\hline"
            if sec.heading is not None:
                lignes.append(f"\\paragraph{{Cas ${sec.heading[1]}$}}")
            lignes += [
                f"\\begin{{longtable}}{{{disp.latex_spec}}}",
                "\\hline",
                entete,
                "\\endhead",
            ]
            for row in sec.rows:
                mat = f"${_matrice_latex(row)}$" if row.matrix is not None else ""
                texte = _latex_escape_text(row.text)
                if row.kind != "op":
                    lignes.append(
                        f"\\multicolumn{{{len(disp.cells) - 1}}}{{p{{{disp.comment_width}}}}}"
                        f"{{\\emph{{{texte}}}}} & {mat} \\\\"
                    )
                    continue
                cellules = []
                for champ in disp.cells:
                    if champ == "matrix":
                        cellules.append(mat)
                    elif champ == "purpose":
                        cellules.append(texte)
                    else:
                        cellules.append(_cellule(row, champ, "$", "$"))
                lignes.append(" & ".join(cellules) + " \\\\")
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


def _cellule(row: TableRow, champ: str, ouvre: str, ferme: str, *, markdown: bool = False) -> str:
    """Cellule d'une ligne d'opération (hors But et matrice)."""
    if champ == "number":
        return str(row.number) if row.number is not None else ""
    if champ == "column":
        return _colonne(row)
    if champ == "pivot":
        return _pivot(row, ouvre, ferme, markdown=markdown)
    tex = {"operation": row.operation_latex, "subject": row.subject, "detail": row.detail}[champ]
    if not tex:
        return ""
    return f"{ouvre}{_sans_barre(tex) if markdown else tex}{ferme}"


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


def _colonne_latex(v: Any) -> str:
    return format_matrix_latex(Matrix.from_columns([v]))


def _ligne_gram_schmidt(c: Step, vecteur: Step | None, locale: str | None) -> TableRow:
    """Orthogonalisation de a_i (``gs.subtract``) ou normalisation de q̃_i (``gs.normalize_step``)."""
    i = int(c.params["i"])
    if _suffixe(c.message_key) == "normalize_step":
        norme = f"\\lVert \\tilde q_{{{i}}} \\rVert"
        return TableRow(
            kind="op",
            layout="gram_schmidt",
            text=translate("table.gs_normalize_step", locale=locale),
            subject=f"\\tilde q_{{{i}}}",
            detail=f"{norme} = {sp.latex(c.params['norm'])}",
            operation_latex=f"q_{{{i}}} = \\frac{{\\tilde q_{{{i}}}}}{{{norme}}}",
            matrix=Matrix.from_columns([c.params["q"]]),
        )
    coeffs = [] if vecteur is None else [
        e for e in vecteur.children if _suffixe(e.message_key) in ("proj_coeff", "proj_coeff_unit")
    ]
    q = "q" if any(_suffixe(e.message_key) == "proj_coeff_unit" for e in coeffs) else "\\tilde q"
    termes = "".join(f" - r_{{{e.params['j']},{i}}}\\,{q}_{{{e.params['j']}}}" for e in coeffs)
    a_i = vecteur.params["a_i"] if vecteur is not None else None
    return TableRow(
        kind="op",
        layout="gram_schmidt",
        text=translate("table.gs_subtract" if coeffs else "table.gs_first", {"i": i}, locale=locale),
        subject=f"a_{{{i}}} = {_colonne_latex(a_i)}" if a_i is not None else f"a_{{{i}}}",
        detail=", ".join(f"r_{{{e.params['j']},{i}}} = {sp.latex(e.params['coeff'])}" for e in coeffs) or None,
        operation_latex=f"\\tilde q_{{{i}}} = a_{{{i}}}{termes}",
        matrix=Matrix.from_columns([c.params["q_tilde"]]),
    )


def _facteur(coef: sp.Expr) -> str:
    tex = sp.latex(coef)
    return f"\\left({tex}\\right)" if isinstance(coef, sp.Add) or tex.startswith("-") else tex


def _ligne_substitution(c: Step, systeme: Step | None, locale: str | None) -> TableRow:
    """Calcul d'une inconnue (``triangular.step``) : x_i = (c_i - Σ r_ij x_j) / r_ii."""
    i = int(c.params["i"])
    somme = sp.sympify(c.params["sum_terms"])
    diag = sp.sympify(c.params["diag"])

    def fraction(num: str) -> str:
        return num if diag == 1 else f"\\frac{{{num}}}{{{sp.latex(diag)}}}"

    ci = sp.latex(c.params["ci"])
    calcul = f"x_{{{i}}} = "
    R = _matrice_du_cliche(systeme) if systeme is not None else None
    if R is not None and somme != 0:
        # Formule avec les coefficients de la ligne i, puis valeurs des inconnues connues
        connues = range(i, R.cols) if systeme is not None and systeme.message_key.endswith("back_start") else range(i - 1)
        termes = "".join(
            " - " + ("" if R[i - 1, j] == 1 else _facteur(R[i - 1, j]) + "\\,") + f"x_{{{j + 1}}}"
            for j in connues
            if R[i - 1, j] != 0
        )
        calcul += fraction(ci + termes) + " = "
    calcul += fraction(ci + (f" - {_facteur(somme)}" if somme != 0 else ""))
    return TableRow(
        kind="op",
        layout="substitution",
        text=translate("table.triangular_step", {"i": i}, locale=locale),
        subject=f"x_{{{i}}}",
        operation_latex=calcul,
        detail=sp.latex(c.params["xi"]),
    )


def _lignes(trace: Step, level: int, locale: str | None) -> list[TableRow]:
    pivots: dict[int, tuple[sp.Expr, tuple[int, int]]] = {}
    _pivots_par_colonne(trace, pivots)
    rows: list[TableRow] = []
    numero = 0

    def visiter(step: Step) -> None:
        nonlocal numero
        for c in step.children:
            prefixe = c.message_key.rsplit(".", 1)[0]
            suf = _suffixe(c.message_key)
            if suf == "start" and prefixe in ("gj", "det"):
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
                        layout="elimination",
                        number=numero,
                        column=col + 1 if col is not None else None,
                        pivot=pivots.get(col) if col is not None else None,
                        operation_latex=op,
                        text=_but(c, col + 1 if col is not None else None, locale),
                        matrix=_matrice_du_cliche(c),
                        highlight=hl,
                    )
                )
            elif prefixe == "gs" and suf in ("subtract", "normalize_step"):
                numero += 1
                vecteur = step if _suffixe(step.message_key) == "vector_step" else None
                rows.append(replace(_ligne_gram_schmidt(c, vecteur, locale), number=numero))
            elif prefixe == "triangular" and suf == "step":
                numero += 1
                rows.append(replace(_ligne_substitution(c, step, locale), number=numero))
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


def _sections(rows: list[TableRow], heading: tuple[str, str] | None) -> list[TableSection]:
    """Un tableau par disposition : une trace qui enchaîne deux algorithmes en donne deux."""
    sections: list[TableSection] = []
    courant: list[TableRow] = []
    disposition: str | None = None
    for row in rows:
        if row.layout is not None and disposition is not None and row.layout != disposition:
            sections.append(TableSection(tuple(courant), heading if not sections else None, disposition))
            courant = []
        if row.layout is not None:
            disposition = row.layout
        courant.append(row)
    sections.append(TableSection(tuple(courant), heading if not sections else None, disposition or "elimination"))
    return sections


def build_table(source: Any, *, level: int = 1, locale: str | None = None) -> TraceTable:
    """Tableau d'une trace (``Step``), d'une discussion par cas (``CaseSplit``) ou d'un résultat seul."""
    if isinstance(source, CaseSplit):
        sections: list[TableSection] = []
        for br in source.branches:
            heading = (
                format_conditions_text([br.condition]) + (" (générique)" if br.condition.is_generic else ""),
                format_conditions_latex([br.condition]) + (" \\text{ (générique)}" if br.condition.is_generic else ""),
            )
            if isinstance(br.trace, Step):
                sections += _sections(_lignes(br.trace, level, locale), heading)
            else:
                rows = (TableRow(kind="comment", text=render_result_text(br.result)),)
                sections.append(TableSection(rows=rows, heading=heading))
        return TraceTable(sections=tuple(sections), locale=locale)
    if isinstance(source, Step):
        return TraceTable(sections=tuple(_sections(_lignes(source, level, locale), None)), locale=locale)
    return TraceTable(
        sections=(TableSection(rows=(TableRow(kind="comment", text=render_result_text(source)),)),), locale=locale
    )
