"""Registre des types de vérificateurs du tuteur (étape 6.1 du plan v6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from linalg_pedagopy.tutor.catalog import _load_fiche_dict
from linalg_pedagopy.tutor.session import ExerciseSession
from linalg_pedagopy.tutor.registry import (
    VerifierType,
    register_verifier,
    requires,
    verifier_type,
    verifier_type_names,
)

TYPES = {
    "produit_scalaire": "inner_product",
    "matrice": "matrix",
    "formule": "formula",
    "valeur": "value",
    "ensemble_valeurs": "value_set",
    "propriete": "property",
    "contre_exemple": "counterexample",
    "egalites": "equalities",
    "labo": "lab",
}


def test_noms_francais_et_alias_anglais() -> None:
    assert verifier_type_names() == frozenset(TYPES) | frozenset(TYPES.values()) | {"dimensions"}
    for fr, en in TYPES.items():
        assert verifier_type(fr) is verifier_type(en)
        assert verifier_type(fr).name == fr  # type: ignore[union-attr]
    assert verifier_type("inconnu") is None


def test_un_nom_ne_s_enregistre_qu_une_fois() -> None:
    double = VerifierType(
        "valeur", (), lambda *a: None, "", requires(message=""), lambda *a: []
    )
    with pytest.raises(ValueError, match="déjà enregistré : 'valeur'"):
        register_verifier(double)


@pytest.mark.parametrize(
    ("v_type", "verif", "message"),
    [
        ("formula", {}, "Le vérificateur 'formula' requiert un champ 'cible'."),
        ("produit_scalaire", {"cible": "x"}, None),
        ("matrice", {"lignes_cibles": []}, None),
        ("matrice", {}, "Le vérificateur 'matrice' requiert 'cible' ou 'lignes_cibles'."),
        ("ensemble_valeurs", {"calcul": "a"}, "Le vérificateur 'ensemble_valeurs' requiert les champs 'calcul' et 'inconnue'."),
        ("labo", {"affirmations": []}, None),
        ("egalites", {}, None),
    ],
)
def test_champs_obligatoires(v_type: str, verif: dict[str, object], message: str | None) -> None:
    vtype = verifier_type(v_type)
    assert vtype is not None
    assert vtype.missing_fields(v_type, verif) == message


def test_seul_le_labo_se_passe_de_jumeau_et_du_controle_de_fuite() -> None:
    sans = {n for n in verifier_type_names() if not verifier_type(n).requires_twin}  # type: ignore[union-attr]
    assert sans == {"labo", "lab"}
    assert {n for n in verifier_type_names() if not verifier_type(n).checks_hint_leak} == {"labo", "lab"}  # type: ignore[union-attr]


def test_type_inconnu_dans_une_seance(tmp_path: Path) -> None:
    fiche = dict(_load_fiche_dict("moyenne-glissante"))
    fiche["verification"] = {**fiche["verification"], "type": "inconnu"}
    ex = ExerciseSession(fiche, persist_journal=False)
    res = ex.verify(1)
    assert res.valid is False
    assert res.diagnostic == "Votre réponse n'a pas la forme attendue : relisez l'énoncé."
