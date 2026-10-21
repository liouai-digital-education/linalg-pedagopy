"""Vérificateur « formule » : formule symbolique comparée à la cible."""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.field import symbols, to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.tuteur.evaluation_sure import expression
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
    raison_illisible,
    sans_seance,
)


def verify_formula(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Vérifie une formule symbolique écrite avec les paramètres de l'énoncé."""
    param_names = list(spec.get("parametres", spec.get("parameters", ["norm_u", "norm_v"])))
    param_syms = {name: symbols(name)[0] for name in param_names}
    local_env: dict[str, Any] = dict(param_syms)
    local_env.update({"sqrt": sp.sqrt, "Rational": sp.Rational})
    for k, v in data.items():
        if isinstance(v, (int, float, str)):
            local_env[k] = to_exact(v)

    cible_raw = spec.get("cible", spec.get("target"))
    if isinstance(cible_raw, Mapping):
        if not isinstance(response, Mapping):
            return VerificationResult(
                False,
                f"Attendu un dictionnaire de formules pour les clés {list(cible_raw.keys())}.",
            )
        for key, target_s in cible_raw.items():
            if key not in response:
                return VerificationResult(False, f"Formule manquante pour '{key}'.")
            sub_res = verify_formula(
                response[key],
                {"parametres": param_names, "cible": target_s},
                data,
            )
            if not sub_res.valid:
                return VerificationResult(False, f"Pour '{key}' : {sub_res.diagnostic}")
        return VerificationResult(True, "Toutes vos formules symboliques sont exactes !")

    variables = ", ".join(param_names)
    if not isinstance(response, (str, int, sp.Expr)):
        return VerificationResult(
            False,
            "Votre réponse n'a pas la forme attendue : une formule sous forme de chaîne, "
            f"écrite avec les variables {variables}.",
        )
    target_expr = expression(str(cible_raw), local_env)
    try:
        student_expr = (
            response
            if isinstance(response, sp.Expr)
            else expression(str(response), local_env)
        )
    except Exception as exc:
        return VerificationResult(
            False,
            f"Impossible de lire votre formule : {raison_illisible(str(response), exc)} "
            f"Utilisez les variables {variables}.",
        )

    diff = sp.simplify(student_expr - target_expr)
    if oracle.decide(diff).verdict == Verdict.ZERO:
        return VerificationResult(
            True,
            f"Formule exacte ({student_expr}) !",
        )

    test_subs = {sym: sp.Integer(1) for sym in param_syms.values()}
    val_stu = sp.simplify(student_expr.xreplace(test_subs))
    return VerificationResult(
        False,
        f"Votre formule ({student_expr}) ne coïncide pas avec l'expression attendue "
        f"(par exemple, lorsque les paramètres valent 1, votre formule donne {val_stu}). "
        "Avez-vous bien développé le carré de la norme et utilisé l'hypothèse d'orthogonalité ?",
    )


def _cross_check_formula(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    if not session.verify(verif.get("cible", verif.get("target"))).valid:
        return ["Cross-check échoué : la formule cible est rejetée."]
    return []


_CIBLE = requires("cible", message="Le vérificateur {type!r} requiert un champ 'cible'.")

register_verifier(
    VerifierType(
        "formule",
        ("formula",),
        sans_seance(verify_formula),
        "une formule sous forme de chaîne, par exemple 'norm_u**2 + norm_v**2'.",
        _CIBLE,
        _cross_check_formula,
    )
)
