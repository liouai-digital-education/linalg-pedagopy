"""Validation des fiches du tuteur : champs, exercice jumeau, fuite des indices, contrôle croisé."""

from __future__ import annotations

import re
from typing import Any, Mapping


from linalg_pedagopy.exercises.generators import TwinExercise
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tuteur.indices import evaluate_twin_spec
from linalg_pedagopy.tuteur.evaluation_sure import evaluer
from linalg_pedagopy.tuteur.verrou import _get_namespace_raw_dict
from linalg_pedagopy.tuteur.registre import verifier_type
from linalg_pedagopy.tuteur.catalogue import _all_fiches, _load_fiche_dict
from linalg_pedagopy.tuteur.seance import ExerciseSession


class ValidationReport:
    """Automatic validation report for an exercise sheet via validate_sheet."""

    __slots__ = (
        "id",
        "valid",
        "target_ok",
        "twin_ok",
        "hints_leak_free",
        "source_ok",
        "cross_check_ok",
        "errors",
    )

    def __init__(
        self,
        id: str,
        valid: bool,
        target_ok: bool,
        twin_ok: bool,
        hints_leak_free: bool,
        errors: tuple[str, ...] = (),
        *,
        source_ok: bool = True,
        cross_check_ok: bool = True,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "valid", bool(valid))
        object.__setattr__(self, "target_ok", bool(target_ok))
        object.__setattr__(self, "twin_ok", bool(twin_ok))
        object.__setattr__(self, "hints_leak_free", bool(hints_leak_free))
        object.__setattr__(self, "source_ok", bool(source_ok))
        object.__setattr__(self, "cross_check_ok", bool(cross_check_ok))
        object.__setattr__(self, "errors", tuple(errors))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("ValidationReport est immuable.")

    @property
    def valide(self) -> bool:
        return self.valid

    @property
    def cible_ok(self) -> bool:
        return self.target_ok

    @property
    def jumeau_ok(self) -> bool:
        return self.twin_ok

    @property
    def indices_sans_fuite(self) -> bool:
        return self.hints_leak_free

    @property
    def erreurs(self) -> tuple[str, ...]:
        return self.errors

    def __bool__(self) -> bool:
        return self.valid


def _cross_check_verifier(
    session: ExerciseSession,
    verif: Mapping[str, Any],
    raw_data: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    """Cross-checks the sheet's verifier by constructing a mathematical solution and testing acceptance/rejection."""
    vtype = verifier_type(str(verif.get("type", "")))
    if vtype is None:
        return True, []
    with suspend_tracing():
        try:
            errs = vtype.cross_check(session, verif, raw_data)
        except Exception as exc:
            errs = [f"Exception lors du cross-check : {exc}"]
    return (len(errs) == 0), errs


def validate_sheet(ex_id: str | int) -> ValidationReport:
    """Vérifie qu'une fiche est complète, sans fuite dans ses indices et cohérente avec le solveur."""
    fiche = _load_fiche_dict(ex_id)
    erreurs: list[str] = []

    for req_key in ("id", "type", "enonce", "verification", "indices"):
        if req_key not in fiche or not fiche[req_key]:
            erreurs.append(f"Champ obligatoire manquant ou vide : {req_key!r}")

    source_ok = True
    for meta_key in ("titre", "theme", "niveau", "numero"):
        if meta_key not in fiche or not str(fiche.get(meta_key, "")).strip():
            source_ok = False
            erreurs.append(f"Métadonnée de catalogue manquante ou vide : {meta_key!r}")
    try:
        if not 1 <= int(fiche.get("niveau", 0)) <= 3:
            source_ok = False
            erreurs.append("Le niveau doit être 1, 2 ou 3.")
    except (TypeError, ValueError):
        source_ok = False
        erreurs.append("Le niveau doit être un entier (1, 2 ou 3).")
    numeros = [int(f.get("numero", -1)) for f in _all_fiches()]
    if numeros.count(int(fiche.get("numero", -1))) > 1:
        source_ok = False
        erreurs.append(f"Numéro {fiche.get('numero')} utilisé par plusieurs fiches.")

    verif = dict(fiche.get("verification", {}))
    v_type = str(verif.get("type", ""))
    vtype = verifier_type(v_type)
    if vtype is None:
        erreurs.append(f"Type de vérificateur invalide : {v_type!r}")

    # 1. Target / verifier specification check
    cible_ok = True
    manque = vtype.missing_fields(v_type, verif) if vtype is not None else None
    if manque:
        cible_ok = False
        erreurs.append(manque)

    # 2. Twin generator check
    jumeau_ok = True
    jumeau_spec = fiche.get("jumeau")
    if jumeau_spec:
        twin_res = evaluate_twin_spec(str(jumeau_spec))
        if not isinstance(twin_res, TwinExercise) and "Erreur" in str(twin_res):
            jumeau_ok = False
            erreurs.append(f"Échec du générateur jumeau : {twin_res}")
    elif vtype is None or vtype.requires_twin:
        jumeau_ok = False
        erreurs.append("Champ 'jumeau' manquant.")

    # 3. Hint leak check (using persist_journal=False so validate_sheet never pollutes disk journal)
    indices_sans_fuite = True
    hints = [str(h) for h in fiche.get("indices", [])]
    if len(hints) < 3:
        erreurs.append("Une fiche doit comporter au moins 3 niveaux d'indices textuels.")
        indices_sans_fuite = False

    session = ExerciseSession(fiche, persist_journal=False)
    raw_cible_str = str(verif.get("cible", ""))
    for idx, h_text in enumerate(hints, start=1):
        if raw_cible_str and len(raw_cible_str) > 4 and raw_cible_str in h_text:
            indices_sans_fuite = False
            erreurs.append(f"L'indice {idx} contient littéralement la cible {raw_cible_str!r}.")
        if vtype is None or vtype.checks_hint_leak:
            try:
                check_h = session.verify(h_text)
                if check_h.valid:
                    indices_sans_fuite = False
                    erreurs.append(f"L'indice {idx} est accepté comme réponse valide par le vérificateur !")
            except Exception:
                pass
            # Also check if any Vector([...]) or Matrix([...]) literal inside the hint is accepted
            for lit_match in re.findall(r"(?:Vector|Matrix)\s*\(\s*\[[^\)]+\]\s*\)", h_text):
                try:
                    lit_obj = evaluer(lit_match, {"Vector": Vector, "Matrix": Matrix})
                    if session.verify(lit_obj).valid:
                        indices_sans_fuite = False
                        erreurs.append(f"L'indice {idx} divulgue une réponse explicite ({lit_match}) !")
                except Exception:
                    pass

    # 4. Cross-check verifier against the mathematical solver
    raw_data = _get_namespace_raw_dict(session.data)
    cross_check_ok, cc_errs = _cross_check_verifier(
        ExerciseSession(fiche, persist_journal=False),
        verif,
        raw_data,
    )
    if not cross_check_ok:
        erreurs.extend(cc_errs)

    valide = (
        cible_ok
        and jumeau_ok
        and indices_sans_fuite
        and source_ok
        and cross_check_ok
        and not erreurs
    )
    return ValidationReport(
        id=str(fiche.get("id", ex_id)),
        valid=valide,
        target_ok=cible_ok,
        twin_ok=jumeau_ok,
        hints_leak_free=indices_sans_fuite,
        source_ok=source_ok,
        cross_check_ok=cross_check_ok,
        errors=tuple(erreurs),
    )

valider_fiche = validate_sheet
