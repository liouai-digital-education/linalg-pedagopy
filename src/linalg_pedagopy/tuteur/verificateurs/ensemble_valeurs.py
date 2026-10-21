"""Vérificateur « ensemble_valeurs » : ensemble des valeurs qui annulent une expression."""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.field import symbols, to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tuteur.evaluation_sure import en_expression
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
    _eval_data_expr,
    sans_seance,
)


def racines_reelles(expr: sp.Expr, inconnue: sp.Symbol) -> list[sp.Expr] | None:
    """Racines réelles exactes d'une expression en une inconnue, ou None si l'ensemble n'est pas fini."""
    solutions = sp.solveset(sp.together(expr), inconnue, domain=sp.S.Reals)
    if solutions is sp.S.EmptySet:
        return []
    if not isinstance(solutions, sp.FiniteSet):
        return None
    return sorted((sp.nsimplify(s) if s.is_Float else s for s in solutions), key=lambda s: float(s.evalf()))


def verify_value_set(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 10 : ensemble des valeurs d'un paramètre qui annulent une expression (par exemple det A)."""
    nom = str(spec.get("inconnue", spec.get("unknown", "a")))
    param = symbols(nom)[0]
    quoi = str(spec.get("expression", "l'expression"))
    expr = en_expression(_eval_data_expr(str(spec.get("calcul", spec.get("compute"))), data))
    attendues = racines_reelles(expr, param)
    if attendues is None:
        return VerificationResult(False, f"Vérification impossible : {quoi} ne s'annule pas en un nombre fini de valeurs.")

    if isinstance(response, Mapping):
        return VerificationResult(False, "Attendu une liste de valeurs, par exemple [1, -2].")
    elements = list(response) if isinstance(response, (list, tuple, set, frozenset)) else [response]
    valeurs: list[sp.Expr] = []
    for element in elements:
        try:
            v = to_exact(element)
        except Exception:
            return VerificationResult(False, "Attendu une liste de valeurs exactes, par exemple [1, -2].")
        if isinstance(v, sp.Basic) and v.free_symbols:
            return VerificationResult(
                False,
                f"Vous avez donné une expression en {nom} : il reste à trouver les valeurs de {nom} qui annulent {quoi}.",
            )
        valeurs.append(v)

    with suspend_tracing():
        for v in valeurs:
            en_v = sp.simplify(expr.subs(param, v))
            if oracle.decide(en_v).verdict != Verdict.ZERO:
                return VerificationResult(
                    False,
                    f"Pour {nom} = {v}, {quoi} vaut {en_v} ≠ 0 : cette valeur ne convient pas.",
                )
        manquantes = [
            e for e in attendues if not any(oracle.decide(v - e).verdict == Verdict.ZERO for v in valeurs)
        ]
    if manquantes and not valeurs:
        return VerificationResult(
            False,
            f"Votre liste est vide, or {quoi} s'annule pour certaines valeurs de {nom}. "
            f"Cherchez les valeurs de {nom} qui annulent {quoi}.",
        )
    if manquantes:
        return VerificationResult(
            False,
            f"Vos valeurs annulent bien {quoi}, mais il en manque {len(manquantes)} (sur {len(attendues)}). "
            f"Avez-vous factorisé complètement {quoi} ?",
        )
    ensemble = "{" + ", ".join(str(e) for e in attendues) + "}" if attendues else "∅"
    return VerificationResult(True, f"Exact : {quoi} s'annule exactement pour {nom} ∈ {ensemble}.")


def _cross_check_value_set(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    param = symbols(str(verif["inconnue"]))[0]
    expr = en_expression(_eval_data_expr(str(verif["calcul"]), raw_data))
    attendues = racines_reelles(expr, param)
    if attendues is None:
        return ["Cross-check échoué : l'expression ne s'annule pas en un nombre fini de valeurs."]
    errs: list[str] = []
    if not session.verify(list(attendues)).valid:
        errs.append("Cross-check échoué : l'ensemble exact des valeurs est rejeté.")
    if attendues and session.verify(list(attendues)[:-1]).valid:
        errs.append("Cross-check échoué : un ensemble incomplet est accepté.")
    intrus = max(attendues, default=sp.Integer(0)) + 1
    if session.verify([*attendues, intrus]).valid:
        errs.append("Cross-check échoué : une valeur qui n'annule pas l'expression est acceptée.")
    return errs


register_verifier(
    VerifierType(
        "ensemble_valeurs",
        ("value_set",),
        sans_seance(verify_value_set),
        "une liste de valeurs exactes, par exemple [1, -2] (liste vide [] s'il n'y en a aucune).",
        requires(
            "calcul",
            "inconnue",
            message="Le vérificateur 'ensemble_valeurs' requiert les champs 'calcul' et 'inconnue'.",
        ),
        _cross_check_value_set,
    )
)
