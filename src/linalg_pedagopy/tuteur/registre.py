"""Registre des types de vérificateurs du tuteur.

Chaque type (``valeur``, ``matrice``…) est décrit une fois : nom français, alias anglais,
fonction de vérification, forme de réponse attendue, champs obligatoires de la fiche et
contrôle croisé de la validation. La séance, la validation des fiches et les messages de
forme attendue lisent ce registre au lieu d'enchaîner des ``if v_type in (...)``.

Pour ajouter un type : écrire sa fonction de vérification, puis appeler
``register_verifier(VerifierType(...))`` dans un nouveau module de ``tuteur/verificateurs/``, importé
par ``tuteur/verificateurs/__init__.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Mapping

if TYPE_CHECKING:
    from linalg_pedagopy.tuteur.verificateurs import VerificationResult

# verify(séance, réponse, spécification, données brutes) -> VerificationResult
VerifyFunction = Callable[[Any, Any, Mapping[str, Any], Mapping[str, Any]], "VerificationResult"]
# cross_check(séance, spécification, données brutes) -> erreurs
CrossCheckFunction = Callable[[Any, Mapping[str, Any], Mapping[str, Any]], list[str]]
# missing_fields(type écrit dans la fiche, spécification) -> message d'erreur ou None
MissingFieldsFunction = Callable[[str, Mapping[str, Any]], str | None]


@dataclass(frozen=True)
class VerifierType:
    """Description d'un type de vérificateur."""

    name: str
    aliases: tuple[str, ...]
    verify: VerifyFunction
    expected_form: str
    missing_fields: MissingFieldsFunction
    cross_check: CrossCheckFunction
    # Les fiches de laboratoire (vrai/faux) n'ont ni exercice jumeau ni réponse à divulguer
    requires_twin: bool = True
    checks_hint_leak: bool = True

    @property
    def names(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


_REGISTRY: dict[str, VerifierType] = {}


def register_verifier(vtype: VerifierType) -> None:
    """Enregistre un type sous son nom français et ses alias."""
    for nom in vtype.names:
        if nom in _REGISTRY and _REGISTRY[nom] is not vtype:
            raise ValueError(f"Type de vérificateur déjà enregistré : {nom!r}")
        _REGISTRY[nom] = vtype


def verifier_type(name: str) -> VerifierType | None:
    """Type enregistré sous ce nom (français ou anglais), ou None."""
    return _REGISTRY.get(name)


def verifier_type_names() -> frozenset[str]:
    """Tous les noms acceptés dans le champ ``type`` d'une fiche."""
    return frozenset(_REGISTRY)


def requires(*champs: str, message: str) -> MissingFieldsFunction:
    """Contrôle de champs obligatoires : chacun des groupes ``a|b`` doit avoir au moins un champ présent."""

    def controle(v_type: str, verif: Mapping[str, Any]) -> str | None:
        for groupe in champs:
            if not any(c in verif for c in groupe.split("|")):
                return message.format(type=v_type)
        return None

    return controle
