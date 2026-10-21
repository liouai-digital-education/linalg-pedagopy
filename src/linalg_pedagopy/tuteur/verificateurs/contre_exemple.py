"""Vérificateur « contre_exemple » : contre-exemple à une affirmation."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import sympy as sp

from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.core.field import to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
    sans_seance,
)


def _simplicity_score(objs: Sequence[Any]) -> str:
    max_dim = 1
    max_height = 0
    for obj in objs:
        if isinstance(obj, Vector):
            max_dim = max(max_dim, len(obj))
            for e in obj.entries:
                if e.is_Rational:
                    max_height = max(max_height, abs(int(e.p)), abs(int(e.q)))
        elif isinstance(obj, Matrix):
            max_dim = max(max_dim, obj.rows, obj.cols)
            for e in obj.flat_entries:
                if e.is_Rational:
                    max_height = max(max_height, abs(int(e.p)), abs(int(e.q)))
    qual = "excellente (très simple)" if max_dim <= 3 and max_height <= 2 else "bonne"
    return f"dimension max = {max_dim}, hauteur max des coefficients = {max_height} ({qual})"


def verify_counterexample(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 6: counterexample validation and simplicity note."""
    ce_kind = str(spec.get("cas", spec.get("case", "")))

    with suspend_tracing():
        if ce_kind == "non_linearite_etendue":
            if not isinstance(response, Mapping) or "x" not in response or "y" not in response:
                return VerificationResult(
                    False,
                    "Fournissez un dictionnaire {'x': Vector([...]), 'y': Vector([...]), 'alpha': ..., 'beta': ...}.",
                )
            x = response["x"] if isinstance(response["x"], Vector) else Vector(response["x"])
            y = response["y"] if isinstance(response["y"], Vector) else Vector(response["y"])
            alpha = to_exact(response.get("alpha", 1))
            beta = to_exact(response.get("beta", 1))
            if len(x) != len(y) or len(x) < 2:
                return VerificationResult(
                    False,
                    "Les vecteurs x et y doivent avoir la même dimension (n >= 2).",
                )
            comb = alpha * x + beta * y

            def _spread(v: Vector) -> sp.Expr:
                return max(v.entries) - min(v.entries)

            def _max_entry(v: Vector) -> sp.Expr:
                return max(v.entries)

            lhs_spread = _spread(comb)
            rhs_spread = alpha * _spread(x) + beta * _spread(y)
            lhs_max = _max_entry(comb)
            rhs_max = alpha * _max_entry(x) + beta * _max_entry(y)
            if (
                oracle.decide(lhs_spread - rhs_spread).verdict != Verdict.ZERO
                or oracle.decide(lhs_max - rhs_max).verdict != Verdict.ZERO
            ):
                note = _simplicity_score([x, y])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! f(αx + βy) ≠ αf(x) + βf(y). "
                    f"Note de simplicité : {note}.",
                    simplicity_note=note,
                )
            return VerificationResult(
                False,
                f"Sur votre instance, f(αx + βy) = {lhs_spread} est égal à αf(x) + βf(y) = {rhs_spread}. "
                "Choisissez deux vecteurs dont les maximums ne se trouvent pas à la même composante !",
            )

        if ce_kind == "ordre_gram_schmidt":
            if not isinstance(response, (tuple, list)) or len(response) != 2:
                return VerificationResult(
                    False,
                    "Fournissez un couple de deux vecteurs (a1, a2).",
                )
            try:
                a1 = response[0] if isinstance(response[0], Vector) else Vector(response[0])
                a2 = response[1] if isinstance(response[1], Vector) else Vector(response[1])
            except Exception:
                return VerificationResult(False, "Fournissez un couple de deux vecteurs (a1, a2).")
            if len(a1) != len(a2) or len(a1) < 2:
                return VerificationResult(
                    False,
                    "Les deux vecteurs a1 et a2 doivent être de même taille n >= 2.",
                )
            gs12 = GramSchmidt([a1, a2]).run()
            gs21 = GramSchmidt([a2, a1]).run()
            if not gs12.independent:  # type: ignore[union-attr]
                return VerificationResult(
                    False,
                    "Hypothèse non vérifiée : vos deux vecteurs a1 et a2 sont colinéaires (liés).",
                )
            q1, q2 = gs12.orthonormal  # type: ignore[union-attr]
            p1, p2 = gs21.orthonormal  # type: ignore[union-attr]
            same_set = (q1 == p1 and q2 == p2) or (q1 == p2 and q2 == p1)
            if not same_set:
                note = _simplicity_score([a1, a2])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! L'ordre (a1, a2) donne ({q1}, {q2}) tandis que (a2, a1) donne ({p1}, {p2}). "
                    f"Note de simplicité : {note}.",
                    simplicity_note=note,
                )
            return VerificationResult(
                False,
                "Sur votre exemple, les deux ordres produisent les mêmes vecteurs orthonormés (car a1 et a2 sont déjà orthogonaux). "
                "Choisissez deux vecteurs indépendants non orthogonaux !",
            )

        if ce_kind == "inverse_matrice_positive":
            try:
                A = response if isinstance(response, Matrix) else Matrix(response)
            except Exception:
                return VerificationResult(False, "Fournissez une matrice carrée A.")
            if A.rows != A.cols or A.rows < 2:
                return VerificationResult(
                    False,
                    "Fournissez une matrice carrée A de taille au moins 2×2.",
                )
            if any(e <= 0 for e in A.flat_entries):
                return VerificationResult(
                    False,
                    "Hypothèse non respectée : tous les coefficients de A doivent être strictement positifs (> 0).",
                )
            inv_a = A.inv(strict=False)
            if not isinstance(inv_a, Matrix):
                return VerificationResult(
                    False,
                    "Hypothèse non respectée : votre matrice A est singulière (non inversible).",
                )
            if any(e < 0 for e in inv_a.flat_entries):
                note = _simplicity_score([A])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! A est inversible à coefficients strictement positifs, "
                    f"et A⁻¹ = {inv_a} possède des coefficients négatifs. Note de simplicité : {note}.",
                    simplicity_note=note,
                )
            return VerificationResult(
                False,
                f"L'inverse de votre matrice A est {inv_a}, qui n'a aucun coefficient strictement négatif.",
            )

    return VerificationResult(False, f"Type de contre-exemple {ce_kind!r} non configuré.")


_CONTRE_EXEMPLES = {
    "non_linearite_etendue": {"x": Vector([1, 0]), "y": Vector([0, 1]), "alpha": 1, "beta": 1},
    "ordre_gram_schmidt": (Vector([1, 0]), Vector([1, 1])),
    "inverse_matrice_positive": Matrix([[2, 1], [1, 2]]),
}


def _cross_check_counterexample(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    cas = str(verif.get("cas", ""))
    if cas in _CONTRE_EXEMPLES and not session.verify(_CONTRE_EXEMPLES[cas]).valid:
        return [f"Cross-check échoué sur {cas}."]
    return []


register_verifier(
    VerifierType(
        "contre_exemple",
        ("counterexample",),
        sans_seance(verify_counterexample),
        "le contre-exemple sous la forme indiquée dans l'énoncé.",
        requires("cas", message="Le vérificateur 'contre_exemple' requiert un champ 'cas'."),
        _cross_check_counterexample,
    )
)
