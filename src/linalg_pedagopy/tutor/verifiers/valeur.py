"""Vérificateur « valeur » : valeur exacte, avec reconnaissance des erreurs typiques."""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.field import to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tutor.registry import VerifierType, register_verifier, requires
from linalg_pedagopy.tutor.verifiers.commun import (
    VerificationResult,
    _eval_data_expr,
    sans_seance,
)


def _detect_typical_value_error(
    student_val: sp.Expr,
    raw_data: Mapping[str, Any],
) -> str | None:
    """Détecteurs des erreurs typiques des étudiants."""
    vecs = {k: v for k, v in raw_data.items() if isinstance(v, Vector)}
    with suspend_tracing():
        for _name, v in vecs.items():
            # 1. ||x|| instead of rms(x)
            if oracle.decide(student_val - v.norm()).verdict == Verdict.ZERO:
                return (
                    "Votre valeur est la norme. Que faut-il encore faire pour "
                    "obtenir une moyenne quadratique ?"
                )
            # 2. Sample standard deviation with 1/(n - 1) instead of 1/n
            if len(v) > 1:
                std_n_minus_1 = v.demean().norm() / sp.sqrt(sp.Integer(len(v) - 1))
                if oracle.decide(student_val - std_n_minus_1).verdict == Verdict.ZERO:
                    return (
                        "Vous avez utilisé la convention statistique en n − 1. "
                        "Quelle est la définition de l'écart type utilisée dans ce cours (division par n) ?"
                    )

        vec_items = list(vecs.items())
        if len(vec_items) >= 2:
            (_, x), (_, y) = vec_items[0], vec_items[1]
            if len(x) == len(y):
                # 3. Squared distance ||x - y||^2
                dist_sq = (x - y).norm_sq()
                if oracle.decide(student_val - dist_sq).verdict == Verdict.ZERO:
                    return "Votre valeur est ||x − y||²."
                # 4. Cosine of angle between x and y instead of correlation
                if x.is_zero() is False and y.is_zero() is False:
                    cos_xy = x.dot(y) / (x.norm() * y.norm())
                    if oracle.decide(student_val - cos_xy).verdict == Verdict.ZERO:
                        return (
                            "Vous avez calculé le cosinus de l'angle entre x et y. "
                            "Sur quels vecteurs la corrélation se calcule-t-elle ?"
                        )
    return None


def _erreur_typique_declaree(
    valeur: sp.Expr,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> str | None:
    """Erreurs typiques propres à une fiche : ``erreurs: [{valeur: expr, diagnostic: msg}]``.

    Chaque ``valeur`` est une expression évaluée sur les données de la fiche (la valeur
    qu'obtient l'étudiant qui commet l'erreur) ; elle est testée avant les détecteurs génériques.
    """
    for erreur in spec.get("erreurs", ()) or ():
        try:
            fausse = to_exact(_eval_data_expr(str(erreur["valeur"]), data))
        except Exception:
            continue
        if oracle.decide(valeur - fausse).verdict == Verdict.ZERO:
            return str(erreur["diagnostic"])
    return None


def verify_value(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 4: exact value computed on the fly + typical error detectors."""
    calcul_spec = spec.get("calcul", spec.get("compute"))

    if isinstance(calcul_spec, Mapping):
        if not isinstance(response, Mapping):
            try:
                stu_scalar = to_exact(response)
                err_msg = _detect_typical_value_error(stu_scalar, data)
                if err_msg is not None:
                    return VerificationResult(False, err_msg)
            except Exception:
                pass
            primary_expr = spec.get("calcul_principal")
            if primary_expr:
                return verify_value(response, {"calcul": primary_expr}, data)
            return VerificationResult(
                False,
                f"Attendu un dictionnaire de réponses pour les clés {list(calcul_spec.keys())}.",
            )

        for key, expr_s in calcul_spec.items():
            if key not in response:
                return VerificationResult(False, f"Clé '{key}' manquante dans votre réponse.")
            sub_res = verify_value(response[key], {"calcul": expr_s}, data)
            if not sub_res.valid:
                return VerificationResult(False, f"Pour '{key}' : {sub_res.diagnostic}")
        return VerificationResult(True, "Toutes vos valeurs sont exactes !")

    expected = _eval_data_expr(str(calcul_spec), data)

    if isinstance(expected, Vector):
        try:
            stu_vec = response if isinstance(response, Vector) else Vector(response)
        except Exception:
            return VerificationResult(False, "Votre réponse doit être un vecteur.")
        if len(stu_vec) != len(expected):
            return VerificationResult(
                False,
                f"Taille de vecteur incorrecte : reçu {len(stu_vec)}, attendu {len(expected)}.",
            )
        if stu_vec == expected:
            return VerificationResult(True, "Exact ! Votre vecteur est correct.")
        for idx, (s_i, e_i) in enumerate(zip(stu_vec, expected), start=1):
            if oracle.decide(s_i - e_i).verdict != Verdict.ZERO:
                return VerificationResult(
                    False,
                    f"La composante {idx} de votre vecteur ({s_i}) est incorrecte.",
                )

    if isinstance(expected, Matrix):
        try:
            stu_mat = response if isinstance(response, Matrix) else Matrix(response)
        except Exception:
            return VerificationResult(False, "Votre réponse doit être une matrice.")
        if stu_mat == expected:
            return VerificationResult(True, "Exact ! Votre matrice est correcte.")
        return VerificationResult(False, "Votre matrice ne correspond pas au résultat attendu.")

    if isinstance(expected, bool):
        if bool(response) is expected:
            return VerificationResult(True, "Exact !")
        return VerificationResult(False, "Ce n'est pas la bonne conclusion.")

    try:
        stu_val = to_exact(response)
        exp_val = to_exact(expected)
    except Exception:
        return VerificationResult(False, f"Réponse scalaire exacte attendue (reçu {response!r}).")

    if oracle.decide(stu_val - exp_val).verdict == Verdict.ZERO:
        return VerificationResult(True, "Exact ! Votre valeur est correcte.")

    declaree = _erreur_typique_declaree(stu_val, spec, data)
    if declaree is not None:
        return VerificationResult(False, declaree)

    typical = _detect_typical_value_error(stu_val, data)
    if typical is not None:
        return VerificationResult(False, typical)

    if oracle.decide(stu_val + exp_val).verdict == Verdict.ZERO:
        return VerificationResult(
            False,
            f"Votre valeur ({stu_val}) a le mauvais signe.",
        )

    return VerificationResult(
        False,
        f"Votre valeur ({stu_val}) n'est pas égale à la valeur exacte attendue. Vérifiez chaque étape de votre calcul.",
    )


def _cross_check_value(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    errs: list[str] = []
    calcul = verif.get("calcul", verif.get("compute"))
    if isinstance(calcul, Mapping):
        sol_dict = {k: _eval_data_expr(str(v), raw_data) for k, v in calcul.items()}
        if not session.verify(sol_dict).valid:
            errs.append("Cross-check échoué : le dictionnaire de valeurs exactes est rejeté.")
    else:
        sol_val = _eval_data_expr(str(calcul), raw_data)
        if not session.verify(sol_val).valid:
            errs.append("Cross-check échoué : la valeur calculée est rejetée.")
    # Une erreur typique déclarée ne doit jamais coïncider avec la bonne réponse
    for idx, erreur in enumerate(verif.get("erreurs", ()) or (), start=1):
        fausse = _eval_data_expr(str(erreur["valeur"]), raw_data)
        if session.verify(fausse).valid:
            errs.append(f"Cross-check échoué : l'erreur typique {idx} est acceptée comme bonne réponse.")
    return errs


register_verifier(
    VerifierType(
        "valeur",
        ("value",),
        sans_seance(verify_value),
        "une valeur exacte (entier, fraction, expression comme sqrt(2)) ou un dictionnaire de valeurs.",
        requires("calcul", message="Le vérificateur 'valeur' requiert un champ 'calcul'."),
        _cross_check_value,
    )
)
