"""Vérificateur « dimensions » : dimensions de produits et d'expressions matricielles."""

from __future__ import annotations

from typing import Any, Mapping

from linalg_pedagopy.tutor.registry import VerifierType, register_verifier, requires
from linalg_pedagopy.tutor.verifiers.commun import (
    VerificationResult,
    sans_seance,
)


def verify_dimensions(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 9: dimension algebra and validity of vector/matrix notations."""
    attendu = spec.get("attendu", spec.get("expected"))

    if isinstance(attendu, Mapping):
        if not isinstance(response, Mapping):
            return VerificationResult(
                False,
                f"Fournissez un dictionnaire pour les sous-questions {list(attendu.keys())} "
                "(ex. {'a': 'valide', 'b': 'invalide'} ou {'a': (m, n), 'b': 'invalide'}).",
            )
        wrong: list[str] = []
        for k, exp_val in attendu.items():
            if k not in response:
                wrong.append(f"sous-question ({k}) manquante")
                continue
            stu_val = response[k]
            if not _match_dim_answer(stu_val, exp_val):
                wrong.append(
                    f"({k}) : votre réponse {stu_val!r} est incorrecte (vérifiez la compatibilité des dimensions internes)"
                )
        if wrong:
            return VerificationResult(
                False,
                "Certaines réponses sont incorrectes : " + " ; ".join(wrong) + ".",
            )
        return VerificationResult(
            True,
            "Exact ! Toutes vos analyses de validité et de dimensions sont correctes.",
        )

    if _match_dim_answer(response, attendu):
        return VerificationResult(True, "Exact ! Votre analyse de la notation et des dimensions est correcte.")
    return VerificationResult(
        False,
        f"Votre réponse ({response!r}) est incorrecte. Rappelez-vous qu'un vecteur de R^n est une matrice n×1 : "
        "le produit u v sans transposition de u est invalide dès que n > 1.",
    )


def _match_dim_answer(student: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        expected = tuple(expected)
    if isinstance(student, list):
        student = tuple(student)
    if student == expected:
        return True
    s_str = str(student).strip().lower()
    e_str = str(expected).strip().lower()
    if s_str == e_str:
        return True
    if e_str in ("invalide", "invalid") and s_str in ("invalide", "invalid", "non valide", "non défini", "non definie", "indéfini"):
        return True
    if e_str in ("valide", "valid") and s_str in ("valide", "valid", "vrai", "true"):
        return True
    return False


def _cross_check_dimensions(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    if not session.verify(verif["attendu"]).valid:
        return ["Cross-check échoué : les dimensions attendues sont rejetées."]
    return []


register_verifier(
    VerifierType(
        "dimensions",
        (),
        sans_seance(verify_dimensions),
        "un dictionnaire, par exemple {'a': (3, 2), 'b': 'invalide'}.",
        requires("attendu", message="Le vérificateur 'dimensions' requiert un champ 'attendu'."),
        _cross_check_dimensions,
    )
)
