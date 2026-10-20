"""Tests du catalogue nommé, des améliorations du tuteur et des matrices structurées."""

from __future__ import annotations

from pathlib import Path

import pytest

from linalg_pedagopy import (
    GaussJordan,
    Matrix,
    UnknownExerciseError,
    Vector,
    convolution,
    convolution_matrix,
    difference_matrix,
    generators,
    moving_average_matrix,
    reversal_matrix,
    running_sum_matrix,
    selection_matrix,
    symbols,
    tutor,
    vandermonde,
)


def test_catalogue_ordonne_par_theme_et_numero() -> None:
    cat = tutor.catalog()
    assert len(cat) == 35
    assert [row["numero"] for row in cat] == list(range(1, 36))
    assert cat[0]["id"] == "selection-composantes"
    assert set(tutor.themes()) == {row["theme"] for row in cat}
    md = cat._repr_markdown_()
    assert md.startswith("| N° | Exercice |")
    conv = tutor.catalog("convolution")
    assert [row["id"] for row in conv] == ["convolution-vecteurs", "produit-polynomes"]
    assert tutor.list_exercises("Convolution") == ["convolution-vecteurs", "produit-polynomes"]


def test_exercice_par_identifiant_numero_ou_titre(tmp_path: Path) -> None:
    j = tmp_path / "j.json"
    a = tutor.exercise("moyenne-glissante", journal_path=j)
    b = tutor.exercise(16, journal_path=j)
    c = tutor.exercise("Écart à la moyenne glissante", journal_path=j)
    assert a.id == b.id == c.id == "moyenne-glissante"
    assert a.number == 16 and a.title == "Écart à la moyenne glissante"
    assert a.theme == "Matrices et applications linéaires" and a.level == 2
    with pytest.raises(UnknownExerciseError, match="moyenne-glissante"):
        tutor.exercise("moyene-glissante")
    with pytest.raises(UnknownExerciseError):
        tutor.exercise(99)


def test_enonce_sans_reference_externe(tmp_path: Path) -> None:
    for ex_id in tutor.list_exercises():
        ex = tutor.exercise(ex_id, journal_path=tmp_path / "j.json")
        st = ex.statement()
        assert st.startswith(f"### Exercice {ex.number} — {ex.title}")
        assert "VMLS" not in st and "textsuperscript" not in st


def test_indices_apres_deblocage_complet_et_reinitialisation(tmp_path: Path) -> None:
    ex = tutor.exercise("moyenne-glissante", journal_path=tmp_path / "j.json")
    for lvl in range(1, 5):
        assert f"Niveau {lvl}" in ex.hint()
    recap = ex.hint()
    assert "Tous les paliers" in recap and "ex.reset()" in recap
    assert "Niveau 2" in ex.hint(2)
    # nouvelle séance : la progression est reprise
    ex2 = tutor.exercise("moyenne-glissante", journal_path=tmp_path / "j.json")
    assert "séance précédente" in ex2.hint()
    ex2.reset()
    assert "Niveau 1" in ex2.hint()
    ex3 = tutor.exercise("moyenne-glissante", journal_path=tmp_path / "j.json")
    assert ex3.journal.hints_unlocked == [1]


def test_jumeaux_pertinents_et_sans_tabulation() -> None:
    for name in [
        "matrice_par_effet", "evaluation_polynome", "puissance_matrice", "matrice_adjacence",
        "mise_echelle_diagonale", "inverse_produit", "resolution_systeme", "identite_blocs",
        "inegalite_triangulaire", "statistiques_vecteur",
    ]:
        tw = getattr(generators, name)()
        text = tw.title + tw.statement + tw.solution_summary
        assert "\t" not in text and "VMLS" not in text


def test_glossaire_francais_et_liste() -> None:
    assert "Noyau" in tutor.glossary("noyau")
    assert "Glossaire" in tutor.glossary()
    with pytest.raises(KeyError):
        tutor.glossary("zzzz")


def test_matrices_structurees() -> None:
    D = difference_matrix(4)
    S = running_sum_matrix(4)
    assert D.shape == (3, 4) and S.shape == (4, 4)
    assert (D @ S).entries_grid == ((0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    assert moving_average_matrix(5, 3).shape == (3, 5)
    assert vandermonde([0, 1, 2]) == Matrix([[1, 0, 0], [1, 1, 1], [1, 2, 4]])
    assert convolution([1, -2, 1], [2, 1]) == Vector([2, -3, 0, 1])
    assert convolution_matrix([2, 1], 3) @ Vector([1, -2, 1]) == Vector([2, -3, 0, 1])
    assert selection_matrix([1, 3], 5) @ Vector([10, 11, 12, 13, 14]) == Vector([11, 13])
    assert reversal_matrix(3) @ Vector([1, 2, 3]) == Vector([3, 2, 1])
    with pytest.raises(ValueError):
        moving_average_matrix(2, 3)


def test_affichage_des_conditions_et_du_casesplit() -> None:
    a, b = symbols("a b")
    res = GaussJordan(Matrix([[1, 1, b**2], [1, a, 1], [1, 1, a]]), Vector([1, 2, 3])).run()
    texte = str(res)
    assert "**" not in texte and "··" not in texte
    assert "b ≠ 1 et b ≠ −1" in texte and "a ≠ b²" in texte
    assert repr(res).startswith("<CaseSplit selon a, b : 5 cas")
    md = res.explain().to_markdown()
    assert "\\frac" in md  # solution générique rendue en LaTeX


def test_compute_inverse_sans_second_membre() -> None:
    A = Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    res = GaussJordan(A, compute_inverse=True).run()
    assert res.inverse == Matrix([[-24, 18, 5], [20, -15, -4], [-5, 4, 1]])
    assert res.inverse == A.inv()
