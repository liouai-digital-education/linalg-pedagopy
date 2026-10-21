"""Vérificateur « labo » : exercices vrai/faux explorés au laboratoire de contre-exemples."""

from __future__ import annotations

from typing import Any, Mapping

from linalg_pedagopy.tuteur.labo import _eval_math_predicate, _structured_vector_candidates
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
)


def _verify_lab(session: Any, response: Any, spec: Mapping[str, Any], raw_data: Mapping[str, Any]) -> Any:
    if isinstance(response, Mapping):
        rep = session.lab().test(**response)
        return VerificationResult(rep.found_counterexample, rep.message)
    return VerificationResult(
        False,
        "Pour cet exercice vrai/faux, enregistrez votre prédiction avec ex.predict(...) / ex.predire(...) "
        "puis explorez avec lab = ex.lab() ; lab.test(...).",
    )


def _cross_check_lab(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    cands = _structured_vector_candidates()
    for h in verif.get("hypotheses", []):
        _eval_math_predicate(str(h), cands[0])
    return []


register_verifier(
    VerifierType(
        "labo",
        ("lab",),
        _verify_lab,
        "un dictionnaire d'instances à tester au laboratoire, après ex.predict(...).",
        requires("enonce|affirmations", message="Le vérificateur 'labo' requiert 'enonce' ou 'affirmations'."),
        _cross_check_lab,
        requires_twin=False,
        checks_hint_leak=False,
    )
)
