"""Tests du tuteur : validation des 35 fiches, 9 vérificateurs, verrou, laboratoire, journal."""

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
    "selection-composantes",
    "validite-notations",
    "recette-week-end",
    "centre-moins-extremes",
    "etendue-non-lineaire",
    "distance-deux-vecteurs",
    "pythagore",
    "statistiques-vecteur",
    "notation-x-carre",
    "rms-difference-orthogonale",
    "ordre-gram-schmidt",
    "moyenne-glissante",
    "vecteur-repete",
    "produit-polynomes",
    "convolution-vecteurs",
    "interpolation-hermite",
    "matrice-application-plan",
    "dimensions-produits",
    "reseau-amitie",
    "somme-composantes",
    "dynamique-trois-pas",
    "mise-echelle-diagonale",
    "inverse-droite-ligne",
    "inverse-carre",
    "flux-tresorerie",
    "deux-inverses-droite",
    "inverse-signes",
    "sommes-de-paires",
    "angle-et-distance",
    "independance-gram-schmidt",
    "renverser-vecteur",
    "identite-par-blocs",
    "norme-minimale",
}


def test_all_35_fiches_present_and_valid() -> None:
    all_ids = lister_exercices()
    assert len(EXPECTED_33_COMPLETE_IDS) == 33
    assert EXPECTED_33_COMPLETE_IDS.issubset(set(all_ids))
    assert "orthogonalite-vrai-faux" in all_ids and "inegalite-triangulaire-trois" in all_ids

    for ex_id in all_ids:
        rep = valider_fiche(ex_id)
        assert rep.valide is True, f"Échec de validation sur {ex_id} : {rep.erreurs}"
        assert rep.cible_ok is True
        assert rep.jumeau_ok is True
        assert rep.indices_sans_fuite is True


def test_seance_type_6_4_from_section_7_8(tmp_path: Path) -> None:
    """Séance type sur la moyenne glissante : diagnostic ligne par ligne puis validation."""
    t = Fraction(1, 3)
    ex = exercice("moyenne-glissante", journal_path=tmp_path / "journal.json")

    enonce = ex.enonce()
    assert "Écart à la moyenne glissante" in enonce
    assert "VMLS" not in enonce
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
    assert "Écart à la moyenne glissante" in str(pan)
    assert "validé" in ex.bilan()


def test_seance_type_labo_3_3_and_3_13_from_section_7_8(tmp_path: Path) -> None:
    """Exercices vrai/faux au laboratoire de contre-exemples."""
    ex = exercice("orthogonalite-vrai-faux", journal_path=tmp_path / "journal.json")

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
    ex_313 = exercice("inegalite-triangulaire-trois", journal_path=tmp_path / "journal.json")
    ex_313.predire("toujours vrai")
    rep_313 = ex_313.labo().tester(
        a=Vector([1, -2, 1]), b=Vector([0, 3, -1]), c=Vector([2, 1, 0])
    )
    assert rep_313.found_counterexample is False
    assert "rédigez une justification" in rep_313.message


def test_verrou_donnees_and_typical_error_detectors_on_3_9(tmp_path: Path) -> None:
    """Verrou des données et détecteurs d'erreurs typiques."""
    ex = exercice("statistiques-vecteur", journal_path=tmp_path / "journal.json")

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
    ex_12 = exercice("selection-composantes", journal_path=j_path)
    assert not ex_12.verifier(Vector([0, -1, 0, 1, 0])).valide  # erreur de signe
    assert not ex_12.verifier(Vector([0, 2, 0, -2, 0])).valide  # proportionnel
    assert not ex_12.verifier(Vector([1, 1, 0, -1, 0])).valide  # composante parasite x_1
    assert ex_12.verifier(Vector([0, 1, 0, -1, 0])).valide

    # 2. dimensions (1.3 et 10.5)
    ex_13 = exercice("validite-notations", journal_path=j_path)
    assert ex_13.verifier({"a": "valide", "b": "invalide", "c": "valide", "d": "invalide"}).valide

    ex_105 = exercice("dimensions-produits", journal_path=j_path)
    assert ex_105.verifier({"a": (3, 2), "b": (4, 2), "c": "invalide"}).valide

    # 3. formule (3.5 et 10.16)
    ex_35 = exercice("pythagore", journal_path=j_path)
    assert not ex_35.verifier("norm_u + norm_v").valide
    assert ex_35.verifier("norm_u**2 + norm_v**2").valide

    ex_1016 = exercice("mise-echelle-diagonale", journal_path=j_path)
    assert ex_1016.verifier("d_i * a_ij * e_j").valide

    # 4. contre_exemple (2.2, 5.2, 11.12)
    ex_22 = exercice("etendue-non-lineaire", journal_path=j_path)
    res_22 = ex_22.verifier({"x": Vector([1, 0]), "y": Vector([0, 1]), "alpha": 1, "beta": 1})
    assert res_22.valide and res_22.note_simplicite is not None

    ex_52 = exercice("ordre-gram-schmidt", journal_path=j_path)
    assert ex_52.verifier((Vector([1, 0]), Vector([1, 1]))).valide

    ex_1112 = exercice("inverse-signes", journal_path=j_path)
    assert ex_1112.verifier(Matrix([[2, 1], [1, 2]])).valide

    # 5. propriete (11.7, 11.9, 11.10, 11.11, 20.11)
    ex_117 = exercice("inverse-droite-ligne", journal_path=j_path)
    assert ex_117.verifier(Matrix([[1], [0], [0]])).valide
    assert ex_117.verifier(Matrix([[0], [1], [1]])).valide  # une autre inverse à droite valide !

    ex_119 = exercice("inverse-carre", journal_path=j_path)
    assert ex_119.verifier("B^2").valide

    ex_1110 = exercice("flux-tresorerie", journal_path=j_path)
    assert ex_1110.verifier(Vector([0, 2, 0])).valide

    ex_1111 = exercice("deux-inverses-droite", journal_path=j_path)
    B1 = Matrix([[1, 1], [0, 1], [0, 0]])
    B2 = Matrix([[-2, -2], [-1, 0], [1, 1]])
    assert not ex_1111.verifier((B1, B1)).valide  # deux matrices identiques refusées
    assert ex_1111.verifier((B1, B2)).valide

    ex_2011 = exercice("norme-minimale", journal_path=j_path)
    assert ex_2011.verifier(Vector([Fraction(1, 3), Fraction(2, 3), Fraction(1, 3)])).valide

    # 6. egalites (20.8)
    ex_208 = exercice("identite-par-blocs", journal_path=j_path)
    assert ex_208.verifier(
        ["block([[A, B], [C, D]]) @ block([[I, 0], [0, I]])", "block([[A, B], [C, D]])"]
    ).valide

    # 7. Échelle d'indices 1..4 et absence de niveau 5
    for lvl in range(1, 5):
        h = ex_12.indice()
        assert f"Niveau {lvl}" in h
    h5 = ex_12.indice(5)
    assert "palier 5" in h5


def test_glossaire_and_teacher_mode() -> None:
    g = glossaire("least squares")
    assert "Moindres carrés" in g

    ex = exercice("moyenne-glissante")
    with pytest.raises(PermissionError):
        ex.fiche_enseignant()

    with using_config(tutor_mode="enseignant"):
        assert mode() == "enseignant"
        fiche = ex.fiche_enseignant()
        assert fiche["id"] == "moyenne-glissante"


def test_phase0_tutor_tamper_proof_and_anti_bypass(tmp_path: Path) -> None:
    """Aucun contournement du tuteur n'est possible."""
    from linalg_pedagopy import tutor

    j_path = tmp_path / "journal_sec.json"
    ex = tutor.exercise("statistiques-vecteur", journal_path=j_path)

    # 1. Aucun attribut secret sur l'instance ou __dict__
    with pytest.raises(AttributeError):
        _ = ex._fiche  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        _ = ex._verification_spec  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        ex._unlocked = True  # type: ignore[attr-defined]

    # 2. Aucun accès aux vecteurs/matrices bruts via data / donnees
    with pytest.raises(LockedExerciseDataError):
        ex.data.raw_dict()
    with pytest.raises(AttributeError):
        _ = ex.data._raw
    with pytest.raises(AttributeError):
        _ = ex.data.x._vec
    with pytest.raises(LockedExerciseDataError):
        _ = ex.data.x.entries
    with pytest.raises(LockedExerciseDataError):
        _ = list(ex.data.x)
    with pytest.raises(LockedExerciseDataError):
        _ = ex.data.x[0]
    with pytest.raises(LockedExerciseDataError):
        _ = Vector(ex.data.x)

    # Même contrôle sur une matrice verrouillée (ex. 11.7)
    ex_mat = tutor.exercise("inverse-droite-ligne", journal_path=j_path)
    with pytest.raises(AttributeError):
        _ = ex_mat.data.A._mat
    with pytest.raises(LockedExerciseDataError):
        _ = ex_mat.data.A[0, 0]
    with pytest.raises(LockedExerciseDataError):
        _ = Matrix(ex_mat.data.A)

    # 3. Anti-trivialité sur verify_equalities (ex. 20.8)
    ex_eq = tutor.exercise("identite-par-blocs", journal_path=j_path)
    assert not ex_eq.verify(["0", "0"]).valid
    assert not ex_eq.verify(["I", "I"]).valid
    assert not ex_eq.verify(
        ["block([[A, B], [C, D]])", "block([[A, B], [C, D]])"]
    ).valid


def test_phase0_journal_persistence_across_sessions_and_no_validation_pollution(
    tmp_path: Path,
) -> None:
    """Persistance du journal entre séances et non-pollution par validate_sheet."""
    from linalg_pedagopy import tutor

    j_path = tmp_path / "journal_persist.json"
    with using_config(journal_path=j_path):
        # validate_sheet ne doit pas créer ni polluer le fichier journal
        rep = tutor.validate_sheet("selection-composantes")
        assert rep.valid is True
        assert rep.source_ok is True
        assert rep.cross_check_ok is True
        assert not j_path.exists()

        # Séance 1 : 2 tentatives erronées + déblocage de 2 indices
        s1 = tutor.exercise("selection-composantes")
        s1.verify(Vector([1, 0, 0, 0, 0]))
        s1.verify(Vector([0, -1, 0, 1, 0]))
        s1.hint()
        s1.hint()
        assert s1.journal.attempts == 2
        assert s1.journal.hints_unlocked == [1, 2]

        # Séance 2 (réinstanciation de exercise("selection-composantes")) : l'état du journal est rechargé !
        s2 = tutor.exercise("selection-composantes")
        assert s2.journal.attempts == 2
        assert s2.journal.hints_unlocked == [1, 2]
        # Le prochain appel à hint() débloque le niveau 3 (et non le niveau 1)
        h3 = s2.hint()
        assert "Niveau 3" in h3
        assert s2.journal.hints_unlocked == [1, 2, 3]


def test_phase0_english_nomenclature_api(tmp_path: Path) -> None:
    """Vérifie l'API anglaise complète du module tutor et de generators."""
    from linalg_pedagopy import generators, tutor

    j_path = tmp_path / "journal_en.json"
    ids = tutor.list_exercises()
    assert len(ids) == 35
    assert "Moindres carrés" in tutor.glossary("least squares")

    ex = tutor.exercise("selection-composantes", journal_path=j_path)
    assert "Sélectionner des composantes" in ex.statement()
    assert "Niveau 1" in ex.hint()
    twin_obj = ex.twin()
    assert "a^T x" in str(twin_obj)

    res = ex.verify(Vector([0, 1, 0, -1, 0]))
    assert res.valid is True
    assert "validé" in ex.summary()
    assert "Sélectionner des composantes" in str(ex.panel())

    with using_config(tutor_mode="teacher"):
        assert tutor.mode() == "teacher"
        sheet = ex.teacher_sheet()
        assert sheet["id"] == "selection-composantes"
        assert "titre" in sheet and "theme" in sheet

    twin_ma = generators.moving_average(window=2, n=5)
    assert "5" in twin_ma.title


def test_fiches_sans_reference_externe_ni_caractere_corrompu() -> None:
    """Chaque fiche a un titre, un thème, un niveau, et aucun texte ne cite de source externe."""
    from pathlib import Path

    import yaml

    import linalg_pedagopy

    fiches = Path(linalg_pedagopy.__file__).parent / "tuteur" / "fiches"
    files = sorted(fiches.glob("*.yaml"))
    assert len(files) == 35
    numeros = set()
    for f in files:
        raw = f.read_text(encoding="utf-8")
        assert "VMLS" not in raw and "Boyd" not in raw, f.name
        assert "textsuperscript" not in raw, f.name
        data = yaml.safe_load(raw)
        assert data["id"] == f.stem
        assert data["titre"] and data["theme"] and data["niveau"] in (1, 2, 3)
        numeros.add(data["numero"])
    assert numeros == set(range(1, 36))
