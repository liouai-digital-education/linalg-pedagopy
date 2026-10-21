"""Vérificateur « egalites » : chaîne d'égalités contrôlée maillon par maillon."""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.field import symbols
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tuteur.evaluation_sure import evaluer, expression
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
    raison_illisible,
    sans_seance,
)


def verify_equalities(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Vérifie une chaîne d'égalités maillon par maillon (chaîne non triviale, membres de départ et d'arrivée)."""
    if not isinstance(response, (list, tuple)) or len(response) < 2:
        return VerificationResult(
            False,
            "Fournissez une liste d'au moins deux expressions représentant les maillons successifs de votre chaîne d'égalités.",
        )

    # Anti-triviality: reject identical consecutive steps (e.g. ["0", "0"] or ["I", "I"])
    for idx in range(len(response) - 1):
        s1 = str(response[idx]).replace(" ", "")
        s2 = str(response[idx + 1]).replace(" ", "")
        if s1 == s2:
            return VerificationResult(
                False,
                f"Maillon trivial refusé : les maillons {idx + 1} et {idx + 2} sont identiques ({response[idx]!r}).",
            )

    kind = str(spec.get("mode", "scalaire"))
    if kind == "blocs":
        A = Matrix([[1, 2], [3, 5]])
        B = Matrix([[2, -1], [0, 3]])
        C = Matrix([[4, 1], [-2, 2]])
        D = Matrix([[1, 3], [2, -1]])
        I = Matrix.identity(2)
        env = {"A": A, "B": B, "C": C, "D": D, "I": I, "block": Matrix.block}
        with suspend_tracing():
            vals: list[Matrix] = []
            for idx, step_expr in enumerate(response, start=1):
                try:
                    val = (
                        step_expr
                        if isinstance(step_expr, Matrix)
                        else evaluer(str(step_expr), env)
                    )
                    if not isinstance(val, Matrix):
                        return VerificationResult(
                            False,
                            f"Le maillon {idx} ne produit pas une matrice par blocs valide.",
                        )
                    vals.append(val)
                except Exception as exc:
                    return VerificationResult(
                        False,
                        f"Impossible de calculer le maillon {idx} : {raison_illisible(str(step_expr), exc)} "
                        "Utilisez A, B, C, D, I, block([[…], […]]) et les opérations +, -, @.",
                    )

            target_block = Matrix.block([[A, B], [C, D]])
            if vals[0] != target_block or vals[-1] != target_block:
                return VerificationResult(
                    False,
                    "Votre chaîne doit partir du produit par blocs [[A, B], [C, D]] @ [[I, 0], [0, I]] "
                    "et aboutir à [[A, B], [C, D]].",
                )
            first_str = str(response[0]).replace(" ", "")
            if "@" not in first_str:
                return VerificationResult(
                    False,
                    "Le premier maillon doit exprimer le produit matriciel par blocs avec '@'.",
                )

            for idx in range(len(vals) - 1):
                if vals[idx] != vals[idx + 1]:
                    return VerificationResult(
                        False,
                        f"Le maillon {idx + 1} -> {idx + 2} n'est pas valide : les deux expressions diffèrent.",
                    )
            return VerificationResult(
                True,
                f"Les {len(vals) - 1} égalités de votre chaîne sont vérifiées maillon par maillon !",
            )

    var_names = list(spec.get("variables", ["x", "y"]))
    local_syms = {v: symbols(v)[0] for v in var_names}
    subs_hyp: dict[sp.Symbol, sp.Expr] = {}
    for h_k, h_v in dict(spec.get("hypotheses_subs", {})).items():
        subs_hyp[local_syms.get(h_k, symbols(h_k)[0])] = expression(str(h_v), local_syms)

    raw_steps: list[sp.Expr] = []
    parsed_steps: list[sp.Expr] = []
    for idx, item in enumerate(response, start=1):
        try:
            expr = item if isinstance(item, sp.Expr) else expression(str(item), local_syms)
            raw_steps.append(expr)
            parsed_steps.append(expr.xreplace(subs_hyp))
        except Exception as exc:
            return VerificationResult(
                False,
                f"Impossible de lire le maillon {idx} ({item!r}) : {raison_illisible(str(item), exc)}",
            )

    # Check start/end endpoints if specified or prevent constant-only trivial chains
    start_spec = spec.get("depart", spec.get("start"))
    end_spec = spec.get("arrivee", spec.get("end"))
    if start_spec is not None:
        start_expr = expression(str(start_spec), local_syms)
        if oracle.decide(sp.simplify(raw_steps[0] - start_expr)).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Le premier maillon ({response[0]}) ne correspond pas au membre de départ attendu ({start_spec}).",
            )
    elif subs_hyp and not raw_steps[0].free_symbols:
        return VerificationResult(
            False,
            "Le premier maillon de votre chaîne doit faire intervenir les variables de l'énoncé avant substitution des hypothèses.",
        )

    if end_spec is not None:
        end_expr = expression(str(end_spec), local_syms).xreplace(subs_hyp)
        if oracle.decide(sp.simplify(parsed_steps[-1] - end_expr)).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Le dernier maillon ({response[-1]}) n'aboutit pas au résultat attendu ({end_spec}).",
            )

    for idx in range(len(parsed_steps) - 1):
        diff = sp.simplify(parsed_steps[idx] - parsed_steps[idx + 1])
        if oracle.decide(diff).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Égalité fausse entre le maillon {idx + 1} ({response[idx]}) et le maillon {idx + 2} ({response[idx + 1]}).",
            )

    return VerificationResult(
        True,
        f"Chaîne de {len(parsed_steps)} expressions algébriquement valide maillon par maillon !",
    )


def _cross_check_equalities(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    if session.verify(["0", "0"]).valid:
        return ["Cross-check échoué : la chaîne triviale ['0', '0'] est acceptée."]
    return []


register_verifier(
    VerifierType(
        "egalites",
        ("equalities",),
        sans_seance(verify_equalities),
        "une liste de chaînes, une par maillon de la chaîne d'égalités.",
        requires(message=""),
        _cross_check_equalities,
    )
)
