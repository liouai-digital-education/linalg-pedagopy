"""Tests complets du module tuteur/ (§7, §8.1 : valider_fiche sur les 35 fiches, 9 vérificateurs, verrou, labo, journal)."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import pytest
import sympy as sp

from linalg_pedagopy import (
    LockedExerciseDataError,
    Matrix,
    PedagopyError,
    Vector,
    using_config,
)
from linalg_pedagopy.tuteur import (
    exercice,
    glossaire,
    lister_exercices,
    mode,
    valider_fiche,
)

EXPECTED_33_COMPLETE_IDS = {
    "1.2", "1.3", "1.4",
    "2.1", "2.2",
    "3.2", "3.5", "3.9", "3.11", "3.14",
    "5.2",
    "6.4", "6.10",
    "7.2", "7.5",
    "8.1", "8.3",
    "10.5", "10.6", "10.10", "10.14", "10.16",
    "11.7", "11.9", "11.10", "11.11", "11.12",
    "12.6",
    "20.2", "20.6", "20.7", "20.8", "20.11",
}


def test_all_35_fiches_present_and_valid() -> None:
    all_ids = lister_exercices()
    assert len(EXPECTED_33_COMPLETE_IDS) == 33
    assert EXPECTED_33_COMPLETE_IDS.issubset(set(all_ids))
    assert "3.3" in all_ids and "3.13" in all_ids

    for ex_id in all_ids:
        rep = valider_fiche(ex_id)
        assert rep.valide is True, f"Échec de validation sur {ex_id} : {rep.erreurs}"
        assert rep.cible_ok is True
        assert rep.jumeau_ok is True
        assert rep.indices_sans_fuite is True


def test_seance_type_6_4_from_section_7_8(tmp_path: Path) -> None:
    """Reproduit exactement la séance type de la section 7.8 (page 23)."""
    t = Fraction(1, 3)
    ex = exercice("6.4", journal_path=tmp_path / "journal.json")

    enonce = ex.enonce()
    assert "page 15" in enonce
    ind1 = ex.indice()
    assert "Niveau 1" in ind1

    # Matrice avec la ligne 2 erronée (identique à la ligne 1)
    A_wrong = Matrix(
        [
            [-t, -t, -t, 1, 0, 0],
            [-t, -t, -t, 1, 0, 0],
            [0, 0, -t, -t, -t, 1],
        ]
    )
    ver_wrong = ex.verifier(A_wrong)
    assert ver_wrong.valide is False
    assert "Taille correcte (3 x 6). Lignes 1 et 3 correctes." in ver_wrong.diagnostic
    assert "Votre ligne 2 calcule d_2 = p_4 - (p_1 + p_2 + p_3)/3." in ver_wrong.diagnostic
    assert "Relisez la définition de d_2 : quel est le prix « du jour » pour i = 2 ?" in ver_wrong.diagnostic

    # Matrice corrigée
    A_right = Matrix(
        [
            [-t, -t, -t, 1, 0, 0],
            [0, -t, -t, -t, 1, 0],
            [0, 0, -t, -t, -t, 1],
        ]
    )
    ver_right = ex.verifier(A_right)
    assert ver_right.valide is True

    pan = ex.panneau()
    assert "6.4" in str(pan)
    assert "Validé" in ex.bilan()


def test_seance_type_labo_3_3_and_3_13_from_section_7_8(tmp_path: Path) -> None:
    """Reproduit l'exemple de vrai/faux 3.3 de la section 7.8 (page 23) et 3.13."""
    ex = exercice("3.3", journal_path=tmp_path / "journal.json")

    # Principe 6 : impossible d'ouvrir le labo sans prédiction préalable
    with pytest.raises(PedagopyError):
        ex.labo()

    ex.predire(a="peut être faux", b="toujours vrai", c="peut être faux")
    lab = ex.labo()
    rep = lab.tester(a=Vector([1, 0, 0]), b=Vector([1, 1, 0]), c=Vector([0, 0, 1]))

    assert rep.hypotheses_satisfied is True
    assert "Hypothèses vérifiées : a ⊥ c et b ⊥ c." in rep.message
    assert "(a) est faux sur votre instance : c'est un contre-exemple valide." in rep.message
    assert "(b) est vrai sur votre instance." in rep.message
    assert "(c) est faux sur votre instance : c'est un contre-exemple valide." in rep.message
    assert "Pour (b), des essais ne suffisent pas : rédigez une justification." in rep.message

    # Exercice 3.13 (inégalité triangulaire à 3 vecteurs, toujours vraie)
    ex_313 = exercice("3.13", journal_path=tmp_path / "journal.json")
    ex_313.predire("toujours vrai")
    rep_313 = ex_313.labo().tester(
        a=Vector([1, -2, 1]), b=Vector([0, 3, -1]), c=Vector([2, 1, 0])
    )
    assert rep_313.found_counterexample is False
    assert "rédigez une justification" in rep_313.message


def test_verrou_donnees_and_typical_error_detectors_on_3_9(tmp_path: Path) -> None:
    """Vérifie le Principe 5 (verrou) et les 4 détecteurs d'erreurs typiques de la page 22."""
    ex = exercice("3.9", journal_path=tmp_path / "journal.json")

    # Tant que l'exercice n'est pas résolu, l'appel direct à .rms() sur ex.donnees.x est bloqué
    with pytest.raises(LockedExerciseDataError):
        ex.donnees.x.rms()

    x = Vector([1, -2, 3, 2])
    y = Vector([2, 1, 0, 1])

    # 1. ||x|| au lieu de rms(x)
    r_norm = ex.verifier(x.norm())
    assert not r_norm.valide
    assert "Votre valeur est la norme. Que faut-il encore faire pour obtenir une moyenne quadratique ?" in r_norm.diagnostic

    # 2. Écart type avec 1/(n - 1)
    std_n_minus_1 = x.demean().norm() / sp.sqrt(3)
    r_std = ex.verifier(std_n_minus_1)
    assert not r_std.valide
    assert "convention statistique en n − 1" in r_std.diagnostic

    # 3. Distance au carré ||x - y||^2
    dist_sq = (x - y).norm_sq()
    r_dist = ex.verifier(dist_sq)
    assert not r_dist.valide
    assert "||x − y||²" in r_dist.diagnostic

    # 4. Cosinus de l'angle de x et y au lieu de la corrélation
    cos_xy = x.dot(y) / (x.norm() * y.norm())
    r_cos = ex.verifier(cos_xy)
    assert not r_cos.valide
    assert "cosinus de l'angle entre x et y" in r_cos.diagnostic

    # Soumission de la bonne valeur : déverrouille ex.donnees.x !
    r_ok = ex.verifier(x.rms())
    assert r_ok.valide is True
    assert ex.donnees.x.rms() == x.rms()


def test_all_nine_verifiers_and_hints(tmp_path: Path) -> None:
    j_path = tmp_path / "journal.json"

    # 1. produit_scalaire (1.2)
    ex_12 = exercice("1.2", journal_path=j_path)
    assert not ex_12.verifier(Vector([0, -1, 0, 1, 0])).valide  # erreur de signe
    assert not ex_12.verifier(Vector([0, 2, 0, -2, 0])).valide  # proportionnel
    assert not ex_12.verifier(Vector([1, 1, 0, -1, 0])).valide  # composante parasite x_1
    assert ex_12.verifier(Vector([0, 1, 0, -1, 0])).valide

    # 2. dimensions (1.3 et 10.5)
    ex_13 = exercice("1.3", journal_path=j_path)
    assert ex_13.verifier({"a": "valide", "b": "invalide", "c": "valide", "d": "invalide"}).valide

    ex_105 = exercice("10.5", journal_path=j_path)
    assert ex_105.verifier({"a": (3, 2), "b": (4, 2), "c": "invalide"}).valide

    # 3. formule (3.5 et 10.16)
    ex_35 = exercice("3.5", journal_path=j_path)
    assert not ex_35.verifier("norm_u + norm_v").valide
    assert ex_35.verifier("norm_u**2 + norm_v**2").valide

    ex_1016 = exercice("10.16", journal_path=j_path)
    assert ex_1016.verifier("d_i * a_ij * e_j").valide

    # 4. contre_exemple (2.2, 5.2, 11.12)
    ex_22 = exercice("2.2", journal_path=j_path)
    res_22 = ex_22.verifier({"x": Vector([1, 0]), "y": Vector([0, 1]), "alpha": 1, "beta": 1})
    assert res_22.valide and res_22.note_simplicite is not None

    ex_52 = exercice("5.2", journal_path=j_path)
    assert ex_52.verifier((Vector([1, 0]), Vector([1, 1]))).valide

    ex_1112 = exercice("11.12", journal_path=j_path)
    assert ex_1112.verifier(Matrix([[2, 1], [1, 2]])).valide

    # 5. propriete (11.7, 11.9, 11.10, 11.11, 20.11)
    ex_117 = exercice("11.7", journal_path=j_path)
    assert ex_117.verifier(Matrix([[1], [0], [0]])).valide
    assert ex_117.verifier(Matrix([[0], [1], [1]])).valide  # une autre inverse à droite valide !

    ex_119 = exercice("11.9", journal_path=j_path)
    assert ex_119.verifier("B^2").valide

    ex_1110 = exercice("11.10", journal_path=j_path)
    assert ex_1110.verifier(Vector([0, 2, 0])).valide

    ex_1111 = exercice("11.11", journal_path=j_path)
    B1 = Matrix([[1, 1], [0, 1], [0, 0]])
    B2 = Matrix([[-2, -2], [-1, 0], [1, 1]])
    assert not ex_1111.verifier((B1, B1)).valide  # deux matrices identiques refusées
    assert ex_1111.verifier((B1, B2)).valide

    ex_2011 = exercice("20.11", journal_path=j_path)
    assert ex_2011.verifier(Vector([Fraction(1, 3), Fraction(2, 3), Fraction(1, 3)])).valide

    # 6. egalites (20.8)
    ex_208 = exercice("20.8", journal_path=j_path)
    assert ex_208.verifier(
        ["block([[A, B], [C, D]]) @ block([[I, 0], [0, I]])", "block([[A, B], [C, D]])"]
    ).valide

    # 7. Échelle d'indices 1..4 et absence de niveau 5
    for lvl in range(1, 5):
        h = ex_12.indice()
        assert f"Niveau {lvl}" in h
    h5 = ex_12.indice(5)
    assert "n'existe pas de niveau 5" in h5


def test_glossaire_and_teacher_mode() -> None:
    g = glossaire("least squares")
    assert "Moindres carrés" in g

    ex = exercice("6.4")
    with pytest.raises(PermissionError):
        ex.fiche_enseignant()

    with using_config(tutor_mode="enseignant"):
        assert mode() == "enseignant"
        fiche = ex.fiche_enseignant()
        assert fiche["id"] == "6.4"
