"""Tests de caractérisation du tuteur : énoncés, indices, jumeaux et diagnostics figés.

Pour chacune des fiches, on fige l'énoncé, les paliers d'indices, l'exercice jumeau et le
diagnostic produit pour une série de réponses fausses génériques, ainsi que le message de
réponses justes connues. Ces tests protègent le découpage du tuteur (phase 3).
Régénération après un changement voulu : LP_MAJ_REFERENCES=1 pytest tests/test_caracterisation_tuteur.py
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from linalg_pedagopy import Matrix, Vector, generators, tutor, using_config

from ._references import bloc, verifier_reference

REPONSES_GENERIQUES = [
    ("0", 0),
    ("'0'", "0"),
    ("Vector.zeros(2)", Vector.zeros(2)),
    ("Vector.zeros(3)", Vector.zeros(3)),
    ("Vector.ones(5)", Vector.ones(5)),
    ("Matrix.zeros(2, 2)", Matrix.zeros(2, 2)),
    ("Matrix.zeros(3, 1)", Matrix.zeros(3, 1)),
    ("Matrix.identity(3)", Matrix.identity(3)),
    ("[1, 2]", [1, 2]),
    ("{'a': 'valide'}", {"a": "valide"}),
    ("('0', '0')", ("0", "0")),
]

REPONSES_JUSTES = {
    "selection-composantes": Vector([0, 1, 0, -1, 0]),
    "validite-notations": {"a": "valide", "b": "invalide", "c": "valide", "d": "invalide"},
    "dimensions-produits": {"a": (3, 2), "b": (4, 2), "c": "invalide"},
    "pythagore": "norm_u**2 + norm_v**2",
    "mise-echelle-diagonale": "d_i * a_ij * e_j",
    "etendue-non-lineaire": {"x": Vector([1, 0]), "y": Vector([0, 1]), "alpha": 1, "beta": 1},
    "ordre-gram-schmidt": (Vector([1, 0]), Vector([1, 1])),
    "inverse-signes": Matrix([[2, 1], [1, 2]]),
    "inverse-droite-ligne": Matrix([[1], [0], [0]]),
    "inverse-carre": "B^2",
    "flux-tresorerie": Vector([0, 2, 0]),
    "deux-inverses-droite": (Matrix([[1, 1], [0, 1], [0, 0]]), Matrix([[-2, -2], [-1, 0], [1, 1]])),
    "norme-minimale": Vector([Fraction(1, 3), Fraction(2, 3), Fraction(1, 3)]),
    "identite-par-blocs": ["block([[A, B], [C, D]]) @ block([[I, 0], [0, I]])", "block([[A, B], [C, D]])"],
    "statistiques-vecteur": Vector([1, -2, 3, 2]).rms(),
    "moyenne-glissante": Matrix([
        [-Fraction(1, 3), -Fraction(1, 3), -Fraction(1, 3), 1, 0, 0],
        [0, -Fraction(1, 3), -Fraction(1, 3), -Fraction(1, 3), 1, 0],
        [0, 0, -Fraction(1, 3), -Fraction(1, 3), -Fraction(1, 3), 1],
    ]),
    "determinant-sarrus": 72,
    "determinant-blocs": 30,
    "parametre-singulier": [0, 2],
    "operations-elementaires-determinant": -8,
}

# Erreurs typiques déclarées dans les fiches de déterminants : diagnostic figé pour chacune
REPONSES_ERRONEES = {
    "determinant-sarrus": [43, 14, 40],
    "determinant-blocs": [11, 24],
    "parametre-singulier": [[2], [1, 2], "-a*(a - 2)", []],
    "operations-elementaires-determinant": [8, -24, -4, -2],
}


def _sans_temps(texte: str) -> str:
    return "\n".join(l for l in str(texte).splitlines() if not l.startswith("- Temps passé"))


@pytest.mark.parametrize("ex_id", tutor.list_exercises())
def test_caracterisation_fiche(ex_id: str, tmp_path: Path) -> None:
    ex = tutor.exercise(ex_id, journal_path=tmp_path / "journal.json")
    parts = [bloc("énoncé", ex.statement())]
    for lvl in (1, 2, 3, 4):
        parts.append(bloc(f"indice {lvl}", ex.hint()))
    parts.append(bloc("indice après déblocage complet", ex.hint()))
    tw = ex.twin()
    parts.append(bloc("jumeau (texte)", str(tw)))
    parts.append(bloc("jumeau (markdown)", tw._repr_markdown_() if hasattr(tw, "_repr_markdown_") else tw))
    for nom, rep in REPONSES_GENERIQUES:
        res = ex.verify(rep)
        parts.append(bloc(f"verify({nom}) -> {res.valid}", res.diagnostic))
    for reponse in REPONSES_ERRONEES.get(ex_id, []):
        res = ex.verify(reponse)
        assert not res.valid, reponse
        parts.append(bloc(f"erreur typique {reponse!r}", res.diagnostic))
    if ex_id in REPONSES_JUSTES:
        res = ex.verify(REPONSES_JUSTES[ex_id])
        assert res.valid, res.diagnostic
        parts.append(bloc("réponse juste", res.diagnostic))
    parts.append(bloc("bilan", _sans_temps(ex.summary())))
    rapport = tutor.validate_sheet(ex_id)
    parts.append(bloc("validation", f"{rapport.valid} {rapport.target_ok} {rapport.twin_ok} {rapport.hints_leak_free} {rapport.source_ok} {rapport.cross_check_ok} {rapport.errors}"))
    with using_config(tutor_mode="teacher"):
        parts.append(bloc("fiche enseignant", ex.teacher_sheet()._repr_markdown_()))
    verifier_reference(f"tuteur/{ex_id}", "\n".join(parts))


def test_caracterisation_laboratoires(tmp_path: Path) -> None:
    parts = []
    ex = tutor.exercise("orthogonalite-vrai-faux", journal_path=tmp_path / "j.json")
    parts.append(bloc("labo sans prédiction", ex.verify({"a": Vector([1, 0, 0])}).diagnostic))
    parts.append(bloc("prédiction", ex.predict(a="peut être faux", b="toujours vrai", c="peut être faux")))
    lab = ex.lab()
    for inst in [
        dict(a=Vector([1, 0, 0]), b=Vector([1, 1, 0]), c=Vector([0, 0, 1])),
        dict(a=Vector([1, 0, 0]), b=Vector([0, 1, 0]), c=Vector([0, 0, 1])),
        dict(a=Vector([1, 0, 1]), b=Vector([0, 1, 0]), c=Vector([0, 0, 1])),
    ]:
        rep = lab.test(**inst)
        parts.append(bloc(f"test {[str(v) for v in inst.values()]}", f"{rep.hypotheses_satisfied} {dict(rep.results_by_part)} {rep.found_counterexample}\n{rep.message}"))
    ex2 = tutor.exercise("inegalite-triangulaire-trois", journal_path=tmp_path / "j.json")
    ex2.predict("toujours vrai")
    rep = ex2.lab().test(a=Vector([1, -2, 1]), b=Vector([0, 3, -1]), c=Vector([2, 1, 0]))
    parts.append(bloc("inégalité triangulaire", f"{rep.found_counterexample}\n{rep.message}"))
    verifier_reference("tuteur/_laboratoires", "\n".join(parts))


def test_caracterisation_catalogue_glossaire_jumeaux() -> None:
    import inspect

    parts = [
        bloc("catalogue (texte)", str(tutor.catalog())),
        bloc("catalogue (markdown)", tutor.catalog()._repr_markdown_()),
        bloc("thèmes", tutor.themes()),
        bloc("glossaire", tutor.glossary()),
        bloc("glossaire noyau", tutor.glossary("noyau")),
    ]
    for nom, f in inspect.getmembers(type(generators), predicate=inspect.isfunction):
        tw = f()
        parts.append(bloc(f"générateur {nom}", f"{tw.title}\n{tw.statement}\n{tw.solution_summary}"))
    verifier_reference("tuteur/_catalogue_glossaire_jumeaux", "\n".join(parts))
