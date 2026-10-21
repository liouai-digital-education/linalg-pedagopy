"""Tests de caractérisation des algorithmes : traces, discussions de cas et résultats figés.

Ces tests ne disent pas ce qui est *juste* : ils détectent tout changement de sortie.
Ils protègent les refactorisations (en particulier l'extraction du moteur d'élimination).
Régénération après un changement voulu : LP_MAJ_REFERENCES=1 pytest tests/test_caracterisation_algorithmes.py
"""

from __future__ import annotations

from typing import Any, Callable

import pytest
import sympy as sp

from linalg_pedagopy import (
    BackSubstitution,
    CaseSplit,
    Determinant,
    Condition,
    ForwardSubstitution,
    GaussJordan,
    GramSchmidt,
    LeastSquares,
    Matrix,
    QR,
    Vector,
    oracle,
    symbols,
    tracing,
)
from linalg_pedagopy.exercises import InteractiveSession, check_gram_schmidt_step, check_row_operation

from ._references import bloc, verifier_reference

a, b, m = symbols("a b m")


def Fraction_(p: int, q: int) -> sp.Rational:
    return sp.Rational(p, q)


def _corps_html(html: str) -> str:
    debut = html.find("<body>")
    fin = html.find("</body>")
    return html[debut + 6 : fin].strip() if debut >= 0 and fin >= 0 else html


def rendu_complet(res: Any, *, verifier: bool = True) -> str:
    """Toutes les sorties observables d'un résultat (ou d'un CaseSplit)."""
    parts = [bloc("repr", repr(res))]
    if isinstance(res, CaseSplit):
        parts.append(bloc("str", str(res)))
    for lvl in (0, 1, 2, 3):
        parts.append(bloc(f"texte niveau {lvl}", res.explain(level=lvl).to_text()))
    exp = res.explain(level=2)
    parts.append(bloc("markdown niveau 2", exp.to_markdown()))
    parts.append(bloc("latex niveau 2", exp.to_latex()))
    parts.append(bloc("html niveau 2 (corps)", _corps_html(exp.to_html())))
    if verifier and not isinstance(res, CaseSplit) and hasattr(res, "verify"):
        parts.append(bloc("verify", res.verify().to_text()))
    return "\n".join(parts)


CAS_ALGORITHMES: dict[str, Callable[[], Any]] = {
    # --- Gauss-Jordan : types de solutions
    "gj_unique": lambda: GaussJordan(Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]), Vector([8, -11, -3])).run(),
    "gj_affine": lambda: GaussJordan(Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), Vector([1, 2, 3])).run(),
    "gj_incompatible": lambda: GaussJordan(Matrix([[1, 1], [1, 1]]), Vector([1, 2])).run(),
    "gj_rref_sans_second_membre": lambda: GaussJordan(Matrix([[1, 2, 0, 1], [2, 4, 1, 3], [3, 6, 1, 4]])).run(),
    "gj_rectangulaire_large": lambda: GaussJordan(Matrix([[1, -1, 2], [0, 1, 1]]), Vector([1, 0])).run(),
    "gj_rectangulaire_haute": lambda: GaussJordan(Matrix([[1, 0], [0, 1], [1, 1]]), Vector([1, 2, 3])).run(),
    "gj_fractions": lambda: GaussJordan(Matrix([[sp.Rational(1, 2), sp.Rational(1, 3)], [sp.Rational(1, 4), 1]]), Vector([1, 2])).run(),
    # --- Inverse
    "gj_inverse": lambda: GaussJordan(Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]]), compute_inverse=True).run(),
    "gj_inverse_singuliere": lambda: GaussJordan(Matrix([[1, 2], [2, 4]]), compute_inverse=True).run(),
    "gj_inverse_parametre": lambda: GaussJordan(Matrix([[1, a], [a, 1]]), compute_inverse=True).run(),
    # --- Stratégies de pivot (pivot nul en tête : échange nécessaire)
    "gj_pivot_simplest": lambda: GaussJordan(Matrix([[0, 2, 1], [3, 1, 2], [1, 1, 1]]), Vector([1, 2, 3])).run(),
    "gj_pivot_first": lambda: GaussJordan(Matrix([[0, 2, 1], [3, 1, 2], [1, 1, 1]]), Vector([1, 2, 3]), pivot_strategy="first").run(),
    "gj_pivot_partial": lambda: GaussJordan(Matrix([[0, 2, 1], [3, 1, 2], [1, 1, 1]]), Vector([1, 2, 3]), pivot_strategy="partial").run(),
    # --- Paramètres
    "gj_parametre_a": lambda: GaussJordan(Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3])).run(),
    "gj_parametre_a_symetrique": lambda: GaussJordan(Matrix([[1, a], [a, 1]]), Vector([1, 1])).run(),
    "gj_parametre_m_trois_cas": lambda: GaussJordan(Matrix([[1, 1, m], [1, m, 1], [m, 1, 1]]), Vector([1, 1, 1])).run(),
    "gj_deux_parametres": lambda: GaussJordan(Matrix([[1, 1, b**2], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3])).run(),
    "gj_hypothese_a_different_de_1": lambda: GaussJordan(Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3]), assumptions=Condition.neq(a, 1)).run(),
    "gj_hypothese_a_egal_1": lambda: GaussJordan(Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3]), assumptions=Condition.eq(a, 1)).run(),
    "gj_radicaux": lambda: GaussJordan(Matrix([[m, sp.sqrt(1 - m**2)], [sp.sqrt(1 - m**2), -m]]), Vector([1, 1])).run(),
    "gj_second_membre_parametre": lambda: GaussJordan(Matrix([[1, 1], [1, 1]]), Vector([1, a])).run(),
    # --- Substitutions triangulaires
    "remontee": lambda: BackSubstitution(Matrix([[2, 1, -1], [0, 3, 2], [0, 0, 4]]), Vector([3, 8, 4])).run(),
    "descente": lambda: ForwardSubstitution(Matrix([[2, 0, 0], [1, 3, 0], [-1, 2, 4]]), Vector([2, 7, 9])).run(),
    # --- Gram-Schmidt et QR
    "gs_fin": lambda: GramSchmidt([Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([0, 1, 1])]).run(),
    "gs_chaque": lambda: GramSchmidt([Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([0, 1, 1])], normalize="each").run(),
    "gs_famille_liee": lambda: GramSchmidt([Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([2, 1, 1])]).run(),
    "gs_parametre": lambda: GramSchmidt([Vector([1, a]), Vector([a, 1])]).run(),
    "qr": lambda: QR(Matrix([[1, -1], [1, 0], [1, 1]])).run(),
    "qr_rang_deficient": lambda: QR(Matrix([[1, 2], [2, 4], [3, 6]])).run(),
    # --- Déterminant (filet de sécurité de la phase 4 : traces de Bareiss, élimination, cofacteurs, Sarrus)
    "det_bareiss_parametre": lambda: Determinant(Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]])).run(),
    "det_bareiss_echange": lambda: Determinant(Matrix([[0, a, 1], [1, 0, b], [a, 1, 0]])).run(),
    "det_elimination_echange": lambda: Determinant(Matrix([[0, 2, 1], [3, 1, 2], [1, 1, 1]]), method="elimination").run(),
    "det_cofacteurs_4x4": lambda: Determinant(Matrix([[2, -1, 3, 0], [1, 4, 0, 2], [-2, 1, 5, 1], [0, 1, 1, 1]]), method="cofactors").run(),
    "det_sarrus": lambda: Determinant(Matrix([[2, -1, 3], [1, 4, 0], [-2, 1, 5]]), method="sarrus").run(),
    "det_singuliere": lambda: Determinant(Matrix([[1, 2], [2, 4]])).run(),
    # --- Moindres carrés
    "mc_qr_rationnelle": lambda: LeastSquares(Matrix([[1, 0], [1, 1], [1, 2], [1, 3]]), Vector([1, 2, 2, 4])).run(),
    "mc_qr": lambda: LeastSquares(Matrix([[1, 0], [1, 1], [1, 2], [1, 3]]), Vector([1, 2, 2, 4]), method="qr").run(),
    "mc_normales": lambda: LeastSquares(Matrix([[1, 0], [1, 1], [1, 2], [1, 3]]), Vector([1, 2, 2, 4]), method="normal").run(),
    "mc_parametre": lambda: LeastSquares(Matrix([[1, a], [1, 1], [1, 2]]), Vector([1, 2, 2])).run(),
}

@pytest.mark.parametrize("nom", sorted(CAS_ALGORITHMES))
def test_caracterisation_algorithme(nom: str) -> None:
    verifier_reference(f"algorithmes/{nom}", rendu_complet(CAS_ALGORITHMES[nom]()))


def test_caracterisation_methodes_de_matrix() -> None:
    A = Matrix([[1, a, 1], [a, 1, 1], [1, 1, a]])
    B = Matrix([[1, 2, 0, 1], [2, 4, 1, 3], [3, 6, 1, 4]])
    C = Matrix([[1, a], [a, 1]])
    parts = [
        bloc("rref paramétrée", repr(A.rref())),
        bloc("rang paramétré", repr(A.rank())),
        bloc("rang paramétré (texte)", str(A.rank())),
        bloc("noyau paramétré", str(A.nullspace())),
        bloc("rref", B.rref()),
        bloc("rang", B.rank()),
        bloc("noyau", B.nullspace()),
        bloc("inverse paramétrée (strict=False)", str(C.inv(strict=False))),
        bloc("solve", B.solve(Vector([1, 3, 4]))),
        bloc("gram", Matrix([[1, 1], [1, -1], [2, 0]]).gram()),
        bloc("colonnes orthonormées", Matrix([[1, 0], [0, 1], [0, 0]]).has_orthonormal_columns()),
    ]
    verifier_reference("algorithmes/methodes_matrix", "\n".join(parts))


def test_caracterisation_traces_contextuelles() -> None:
    """Traces enregistrées par tracing() pour les produits et métriques (niveaux 1 à 3)."""
    from linalg_pedagopy import Explanation

    parts = []
    A = Matrix([[1, 2], [3, 4]])
    B = Matrix([[0, 1], [1, 0]])
    for vue in ("entries", "rows", "columns", "outer"):
        with tracing(level=3) as tr:
            A.matmul(B, view=vue)
        parts.append(bloc(f"matmul {vue}", Explanation(tr.tree, level=3).to_text()))
    x, y = Vector([1, -2, 3, 2]), Vector([2, 1, 0, 1])
    with tracing(level=3) as tr:
        x.dot(y), x.norm(), x.rms(), x.std(), x.correlation(y), x.angle(y), x.distance(y)
    parts.append(bloc("métriques", Explanation(tr.tree, level=3).to_text()))
    with tracing(level=1) as tr:
        GaussJordan(Matrix([[2, 1], [4, 3]]), Vector([5, 11])).run()
        GaussJordan(Matrix([[1, 1], [1, -1]]), Vector([2, 0])).run()
    parts.append(bloc("deux calculs regroupés (niveau 1)", Explanation(tr.tree, level=1).to_text()))
    verifier_reference("algorithmes/traces_contextuelles", "\n".join(parts))


def test_caracterisation_oracle_de_nullite() -> None:
    """Verdicts, facteurs, conditions et méthodes de l'oracle sur des expressions variées."""
    x, = symbols("x")
    p, = symbols("p", positive=True)
    expressions = [
        0, 3, sp.Rational(-2, 7), a - 2, a**2 + 1, (a - 1) ** 2, a * b, a**2 - b**2,
        sp.sqrt(2) - sp.sqrt(2), sp.sqrt(2) + sp.sqrt(3), sp.sqrt(1 - m**2), sp.sqrt(a**2 + 1) - 1,
        sp.sqrt(a) - 2, p, p - 1, sp.exp(x), sp.sin(x), x * sp.exp(x), sp.Abs(a) + 1,
        1 / (a - 1) - 1, (a**2 - 1) / (a - 1), sp.pi - 3,
    ]
    lignes = []
    for e in expressions:
        d = oracle.decide(e)
        cond = d.format_cases() or "—"
        dom = d.domain.format_text() if d.domain is not None else "—"
        lignes.append(f"{sp.sstr(e)!s:28s} | {d.verdict.name:11s} | facteurs {tuple(sp.sstr(f) for f in d.factors)} | condition {cond} | domaine {dom} | méthode {d.method}")
    hyp = []
    for e, c in [(a - 2, Condition.neq(a - 2)), (a - 2, Condition.eq(a, 2)), (a**2 - 4, Condition.eq(a, -2)), (a * b, Condition.neq(a))]:
        d = oracle.decide(e, assumptions=c)
        hyp.append(f"{sp.sstr(e)} sous {c} : {d.verdict.name} (facteurs {tuple(sp.sstr(f) for f in d.factors)})")
    for e in [sp.sin(1) ** 2 + sp.cos(1) ** 2 - 1, sp.log(2) + sp.log(3) - sp.log(6), sp.exp(1) - 2,
              sp.sqrt(2) * sp.sqrt(3) - sp.sqrt(6), sp.cos(sp.pi / 5) - (1 + sp.sqrt(5)) / 4,
              sp.sin(a) ** 2 + sp.cos(a) ** 2 - 1, (sp.sqrt(a) + 1) * (sp.sqrt(a) - 1) - a + 1]:
        d = oracle.decide(e)
        hyp.append(f"{sp.sstr(e)} : {d.verdict.name} (méthode {d.method})")
    for fmt in ["a != 1", "a == 2", "a = 3", ["a != 1", "b != 0"], {"a": "!=1"}, {"a": 2}, {"a": ["!=1", "!=2"]}, {a: "==0"}]:
        d = oracle.decide((a - 1) * (a - 2) * a, assumptions=fmt)
        hyp.append(f"hypothèse {fmt!r} : {d.verdict.name} (facteurs {tuple(sp.sstr(f) for f in d.factors)})")
    from linalg_pedagopy import UndecidableZeroError
    for e in [0, 5, a - 1, sp.sin(a)]:
        try:
            hyp.append(f"is_zero({sp.sstr(e)}) = {oracle.is_zero(e)}")
        except UndecidableZeroError as err:
            hyp.append(f"is_zero({sp.sstr(e)}) lève UndecidableZeroError ({err})")
    verifier_reference("algorithmes/oracle", bloc("décisions", "\n".join(lignes)) + "\n" + bloc("avec hypothèses et cas particuliers", "\n".join(hyp)))


def test_caracterisation_sessions_et_verificateur_d_operations() -> None:
    M = Matrix([[1, 2, 5], [3, 8, 17], [1, 1, 1]])
    ops = [
        "L2 <- L2 - 3*L1", "L2 <- L2 + 3*L1", "L2 <- 0*L2", "L2 <- L2**2", "L1 <- L2", "L1 <- L1 - L1",
        "L1 <-> L3", "L1 <-> L1", "L9 <- L1", "only_A: L1 <-> L2", "L2 <- (1/2)*L2", "L3 <- L3 - L1 - L2",
        "échanger 1 et 2", "L3 <- 2*L3 + L1",
    ]
    lignes = []
    for op in ops:
        f = check_row_operation(M, op, num_lhs_cols=2)
        lignes.append(f"{op:22s} | {f.status:17s} | {f.error_code} | {f.message}")
    gs = []
    a1, a2 = Vector([1, 1, 0]), Vector([1, 0, 1])
    for prop, early in [(Vector([Fraction_(1, 2), Fraction_(-1, 2), 1]), False), (Vector([1, 0, 1]), False), (Vector([1, -1, 2]), False), (Vector([1, -1, 2]), True)]:
        f = check_gram_schmidt_step(a2, [a1], prop, normalized_early=early)
        gs.append(f"{prop} (normalisé tôt={early}) | {f.status} | {f.error_code} | {f.message}")
    s = InteractiveSession(GaussJordan(Matrix([[1, 2], [3, 8]]), Vector([5, 17])))
    sess = [s.hint()]
    for op in ["L2 <- L2 - 3*L1", "L2 <- (1/2)*L2", "L1 <- L1 - 2*L2"]:
        sess.append(f"{op} -> {s.propose(op)}")
        sess.append(s.hint())
    sess.append(f"complet : {s.is_complete()}")
    pr = InteractiveSession(GaussJordan(Matrix([[1, 2], [3, 8]]), Vector([5, 17])), mode="predict_reveal")
    sess += [pr.reveal(), pr.predict("x"), pr.reveal(), pr.reveal(), pr.reveal()]
    co = InteractiveSession(GramSchmidt([Vector([1, 1]), Vector([1, 0])]), mode="completion", mask_ratio=0.5)
    sess.append(str(co.completion_view()))
    verifier_reference(
        "algorithmes/sessions_et_operations",
        bloc("opérations de lignes", "\n".join(lignes)) + "\n" + bloc("étapes de Gram-Schmidt", "\n".join(gs))
        + "\n" + bloc("sessions", "\n".join(str(x) for x in sess)),
    )
