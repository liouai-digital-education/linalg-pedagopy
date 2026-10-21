"""Vérificateur « produit_scalaire » : vecteur des coefficients d'une forme linéaire."""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.tutor.registry import VerifierType, register_verifier, requires
from linalg_pedagopy.tutor.verifiers.commun import (
    VerificationResult,
    _format_linear_comb,
    _parse_indexed_expr,
    sans_seance,
)


def verify_inner_product(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 1: inner_product / produit_scalaire."""
    if not isinstance(response, Vector):
        try:
            response = Vector(response)
        except Exception:
            return VerificationResult(
                False,
                "Votre réponse doit être un vecteur (ex. Vector([...])).",
            )

    var_name = str(spec.get("inconnue", spec.get("unknown", "x")))
    n = int(spec.get("taille", spec.get("size", data.get("n", len(response)))))
    if len(response) != n:
        return VerificationResult(
            False,
            f"Taille incorrecte : votre vecteur est de taille {len(response)}, "
            f"alors que {var_name} est dans R^{n}.",
        )

    cible_str = str(spec.get("cible", spec.get("target")))
    target_expr, vec_syms = _parse_indexed_expr(cible_str, var_name, n, data)

    student_expr = sp.expand(
        sum((response[k] * vec_syms[k] for k in range(n)), sp.Integer(0))
    )
    student_fmt = _format_linear_comb(response.entries, var_name)

    diff = sp.simplify(student_expr - target_expr)
    if oracle.decide(diff).verdict == Verdict.ZERO:
        return VerificationResult(
            True,
            f"Exact ! Avec votre vecteur, a^T {var_name} = {student_fmt}.",
        )

    if oracle.decide(sp.simplify(student_expr + target_expr)).verdict == Verdict.ZERO:
        return VerificationResult(
            False,
            f"Avec votre vecteur, a^T {var_name} = {student_fmt} : c'est l'opposé de la quantité demandée (erreur de signe).",
        )

    if student_expr != 0 and target_expr != 0:
        ratio = sp.simplify(student_expr / target_expr)
        if not ratio.free_symbols and ratio != 1:
            return VerificationResult(
                False,
                f"Avec votre vecteur, a^T {var_name} = {student_fmt} : le résultat est proportionnel à la cible (facteur {ratio}). "
                "Vérifiez la normalisation !",
            )

    target_free = target_expr.free_symbols
    student_free = student_expr.free_symbols
    extra_syms = sorted(student_free - target_free, key=lambda s: s.name)
    if extra_syms:
        return VerificationResult(
            False,
            f"Avec votre vecteur, a^T {var_name} = {student_fmt} : la composante {extra_syms[0]} "
            "intervient alors qu'elle ne figure pas dans la quantité à modéliser.",
        )

    return VerificationResult(
        False,
        f"Avec votre vecteur, a^T {var_name} = {student_fmt}. "
        f"Quels coefficients faut-il placer devant chaque composante de {var_name} ?",
    )


def _cross_check_inner_product(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    errs: list[str] = []
    var_name = str(verif.get("inconnue", verif.get("unknown", "x")))
    n = int(verif.get("taille", verif.get("size", raw_data.get("n", 4))))
    cible_str = str(verif.get("cible", verif.get("target")))
    target_expr, vec_syms = _parse_indexed_expr(cible_str, var_name, n, raw_data)
    coeffs = [sp.diff(target_expr, s) for s in vec_syms]
    sol_vec = Vector(coeffs)
    if not session.verify(sol_vec).valid:
        errs.append("Cross-check échoué : le vecteur reconstruit par dérivation formelle est rejeté.")
    wrong_vec = Vector.ones(n) if sol_vec != Vector.ones(n) else Vector.zeros(n)
    if session.verify(wrong_vec).valid:
        errs.append("Cross-check échoué : un vecteur erroné est accepté.")
    return errs


_CIBLE = requires("cible", message="Le vérificateur {type!r} requiert un champ 'cible'.")

register_verifier(
    VerifierType(
        "produit_scalaire",
        ("inner_product",),
        sans_seance(verify_inner_product),
        "un vecteur, par exemple Vector([0, 1, 0]).",
        _CIBLE,
        _cross_check_inner_product,
    )
)
