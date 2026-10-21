"""Tests de caractérisation de `verrou`, `indices` et `panneau` (étape 6.0 du plan v6).

Ils figent le comportement actuel avant le déplacement du code de `tutor/` vers `tuteur/`
(étape 6.6) et le remplacement des `eval` (étape 6.4).
"""

from __future__ import annotations

import sys
from typing import Any

import pytest
import sympy as sp

from linalg_pedagopy import Matrix, Vector, using_config
from linalg_pedagopy.core.exceptions import LockedExerciseDataError
from linalg_pedagopy.exercises.generators import TwinExercise
from linalg_pedagopy.tuteur.indices import LEVEL_TITLES, HintLadder, evaluate_twin_spec
from linalg_pedagopy.tuteur.panneau import PanneauFallback, build_panneau
from linalg_pedagopy.tuteur.verrou import LockedMatrix, LockedNamespace, LockedVector, _get_namespace_raw_dict
from linalg_pedagopy.tutor.panel import _parse_answer

# ---------------------------------------------------------------------------
# verrou
# ---------------------------------------------------------------------------


class _Interrupteur:
    """État de déverrouillage d'une séance, modifiable par le test."""

    def __init__(self) -> None:
        self.ouvert = False

    def __call__(self) -> bool:
        return self.ouvert


u = Vector([3, 4])
w = Vector([1, 2])
A = Matrix([[2, 1], [1, 1]])

OPERATIONS_VECTEUR = {
    "entries": lambda x: x.entries,
    "__getitem__": lambda x: x[0],
    "__iter__": lambda x: list(x),
    "rms()": lambda x: x.rms(),
    "norm()": lambda x: x.norm(),
    "norm_sq()": lambda x: x.norm_sq(),
    "avg()": lambda x: x.avg(),
    "std()": lambda x: x.std(),
    "demean()": lambda x: x.demean(),
    "dot()": lambda x: x.dot(w),
    "distance()": lambda x: x.distance(w),
    "angle()": lambda x: x.angle(w),
    "correlation()": lambda x: x.correlation(w),
    "+": lambda x: x + w,
    "-": lambda x: x - w,
    "*": lambda x: x * 2,
    "* à gauche": lambda x: 2 * x,
}

OPERATIONS_MATRICE = {
    "__getitem__": lambda m: m[0, 1],
    "__iter__": lambda m: list(m),
    "T": lambda m: m.T,
    "gram()": lambda m: m.gram(),
    "rref()": lambda m: m.rref(),
    "rank()": lambda m: m.rank(),
    "nullspace()": lambda m: m.nullspace(),
    "inv()": lambda m: m.inv(),
    "solve()": lambda m: m.solve(w),
    "@": lambda m: m @ w,
}


@pytest.mark.parametrize("nom", list(OPERATIONS_VECTEUR))
def test_vecteur_verrouille_puis_deverrouille(nom: str) -> None:
    op = OPERATIONS_VECTEUR[nom]
    cle = _Interrupteur()
    x = LockedVector(u, cle, name="u")
    with pytest.raises(LockedExerciseDataError, match=r"Calcul direct 'u\."):
        op(x)
    cle.ouvert = True
    assert op(x) == op(u)


@pytest.mark.parametrize("nom", list(OPERATIONS_MATRICE))
def test_matrice_verrouillee_puis_deverrouillee(nom: str) -> None:
    op = OPERATIONS_MATRICE[nom]
    cle = _Interrupteur()
    m = LockedMatrix(A, cle, name="A")
    with pytest.raises(LockedExerciseDataError, match=r"Calcul direct 'A\."):
        op(m)
    cle.ouvert = True
    assert op(m) == op(A)


def test_proprietes_de_forme_toujours_lisibles() -> None:
    x = LockedVector(u, lambda: False)
    m = LockedMatrix(A, lambda: False)
    assert (x.size, x.shape, len(x)) == (u.size, u.shape, len(u))
    assert (m.rows, m.cols, m.shape) == (2, 2, (2, 2))
    assert repr(x) == "LockedVector(size=2, verrouillé)"
    assert repr(m) == "LockedMatrix(shape=(2, 2), verrouillé)"
    assert str(x) == str(u) and str(m) == str(A)


def test_argument_verrouille_refuse() -> None:
    """Un vecteur verrouillé passé en argument est lui aussi protégé."""
    ouvert = LockedVector(u, lambda: True)
    ferme = LockedVector(w, lambda: False, name="w")
    with pytest.raises(LockedExerciseDataError, match=r"'w\.argument'"):
        ouvert.dot(ferme)
    with pytest.raises(LockedExerciseDataError):
        LockedMatrix(A, lambda: True) @ ferme
    assert ouvert.dot(LockedVector(w, lambda: True)) == u.dot(w)


def test_proxys_immuables_et_sans_donnees_inspectables() -> None:
    x = LockedVector(u, lambda: False)
    m = LockedMatrix(A, lambda: False)
    ns = LockedNamespace({"u": u}, lambda: False)
    for obj in (x, m, ns):
        with pytest.raises(AttributeError):
            obj.donnee = 1  # type: ignore[attr-defined]
        with pytest.raises(TypeError):
            vars(obj)
    with pytest.raises(LockedExerciseDataError):
        x._unwrap_for_constructor("Vector()")


def test_espace_de_noms() -> None:
    cle = _Interrupteur()
    ns = LockedNamespace(
        {"u": u, "A": A, "M": [[1, 2], [3, 4]], "v": [1, 2, 3], "n": 5, "vide": []}, cle
    )
    assert ns.keys() == ["u", "A", "M", "v", "n", "vide"]
    assert isinstance(ns.u, LockedVector) and isinstance(ns["A"], LockedMatrix)
    assert isinstance(ns.M, LockedMatrix) and ns.M.shape == (2, 2)
    assert isinstance(ns.v, LockedVector) and ns.v.size == 3
    assert ns.n == 5
    assert isinstance(ns.vide, LockedVector) and ns.vide.size == 0
    with pytest.raises(AttributeError, match="Aucune donnée nommée 'z'"):
        ns.z  # noqa: B018
    assert repr(ns).startswith("ExerciseData(u=LockedVector(size=2, verrouillé), A=LockedMatrix(")
    with pytest.raises(LockedExerciseDataError, match="raw_dict"):
        ns.raw_dict()
    brut = _get_namespace_raw_dict(ns)
    assert brut["M"] == Matrix([[1, 2], [3, 4]]) and brut["v"] == Vector([1, 2, 3])
    cle.ouvert = True
    assert ns.raw_dict() == brut


# ---------------------------------------------------------------------------
# indices
# ---------------------------------------------------------------------------

INDICES = ("Orientation : relire la définition.", "Outil : produit scalaire.", "Démarrage : poser x = …")


def test_specification_du_jumeau() -> None:
    assert isinstance(evaluate_twin_spec(None), TwinExercise)
    assert isinstance(evaluate_twin_spec("generateurs.statistiques_vecteur()"), TwinExercise)
    assert isinstance(evaluate_twin_spec("generators.vector_statistics()"), TwinExercise)
    assert evaluate_twin_spec("Voir le cours, § 2.") == "Voir le cours, § 2."
    erreur = evaluate_twin_spec("generators.inexistant()")
    assert isinstance(erreur, str) and erreur.startswith("Erreur dans l'exercice jumeau : generators.inexistant()")


def test_jumeau_texte_libre_non_evalue() -> None:
    assert evaluate_twin_spec("__import__('os')") == "__import__('os')"


_EVASION = "statistiques_vecteur.__globals__['__builtins__']['len']('abc')"


@pytest.mark.xfail(strict=True, reason="eval contournable par __globals__ : interpréteur ast de l'étape 6.4")
def test_jumeau_sans_acces_aux_fonctions_integrees() -> None:
    res = evaluate_twin_spec("generators." + _EVASION)
    assert isinstance(res, str) and res.startswith("Erreur dans l'exercice jumeau")


def test_echelle_progressive() -> None:
    debloques: list[int] = []
    echelle = HintLadder(INDICES, on_unlock=debloques.append)
    assert echelle.request_hint() == f"**[{LEVEL_TITLES[1]}]**\n\n{INDICES[0]}"
    # Un palier trop lointain est ramené au suivant
    assert echelle.request_hint(level=3).startswith(f"**[{LEVEL_TITLES[2]}]**")
    # Relire un palier déjà débloqué ne débloque rien
    assert echelle.request_hint(level=1).startswith(f"**[{LEVEL_TITLES[1]}]**")
    assert echelle.request_hint(level=0).startswith(f"**[{LEVEL_TITLES[1]}]**")
    assert echelle.request_hint().endswith(INDICES[2])
    quatre = echelle.request_hint()
    assert quatre.startswith(f"**[{LEVEL_TITLES[4]}]**")
    assert debloques == [1, 2, 3, 4] and echelle.unlocked_level == 4
    assert "Il n'existe pas de palier 5" in echelle.request_hint()


def test_palier_sans_texte_et_jumeau_avec_complement() -> None:
    echelle = HintLadder(("seul indice",), twin_spec="Jumeau : voir l'exemple 3.")
    assert echelle.format_level(2).endswith("Relisez les définitions des notions indiquées dans l'énoncé.")
    assert echelle.format_level(4) == f"**[{LEVEL_TITLES[4]}]**\n\nJumeau : voir l'exemple 3."
    assert echelle.jumeau_spec == "Jumeau : voir l'exemple 3."
    complet = HintLadder((*INDICES, "Complément du palier 4."))
    assert complet.format_level(4).endswith("\n\nComplément du palier 4.")
    assert HintLadder((), initial_unlocked_level=2).unlocked_level == 2


def test_deblocage_differe_par_tentatives() -> None:
    with using_config(hint_min_attempts=2):
        echelle = HintLadder(INDICES)
        echelle.request_hint(current_attempts=0)  # le premier palier reste libre
        msg = echelle.request_hint(current_attempts=1)
        assert msg.startswith("Déblocage différé : effectuez au moins 1 tentative(s)")
        assert echelle.unlocked_level == 1
        assert echelle.request_hint(current_attempts=2).startswith(f"**[{LEVEL_TITLES[2]}]**")


def test_deblocage_differe_par_delai(monkeypatch: pytest.MonkeyPatch) -> None:
    import linalg_pedagopy.tutor.hints as hints

    horloge = [1000.0]
    monkeypatch.setattr(hints.time, "time", lambda: horloge[0])
    with using_config(hint_min_delay_seconds=30):
        echelle = HintLadder(INDICES)
        echelle.request_hint()
        horloge[0] += 10
        assert echelle.request_hint() == (
            "Déblocage différé : veuillez patienter encore 20 s avant de débloquer le niveau 2."
        )
        horloge[0] += 20
        assert echelle.request_hint().startswith(f"**[{LEVEL_TITLES[2]}]**")


# ---------------------------------------------------------------------------
# panneau
# ---------------------------------------------------------------------------


def test_lecture_des_reponses() -> None:
    assert _parse_answer("Vector([1, 2])") == Vector([1, 2])
    assert _parse_answer("Matrix([[1, 0], [0, 1]])") == Matrix.identity(2)
    assert _parse_answer("sqrt(2) + Rational(1, 3)") == sp.sqrt(2) + sp.Rational(1, 3)
    assert _parse_answer("pi") == sp.pi
    assert _parse_answer("{'a': [1, 2], 'b': (3,)}") == {"a": [1, 2], "b": (3,)}
    with pytest.raises(NameError):
        _parse_answer("open('x')")
    with pytest.raises(NameError):
        _parse_answer("__import__('os')")


@pytest.mark.xfail(strict=True, reason="eval contournable par __globals__ : interpréteur ast de l'étape 6.4")
def test_reponse_sans_acces_aux_fonctions_integrees() -> None:
    with pytest.raises(Exception):  # noqa: B017
        _parse_answer("Vector.__init__.__globals__['__builtins__']['len']('abcd')")


class _SeanceFactice:
    """Séance minimale : enregistre les appels du panneau."""

    def __init__(self) -> None:
        self.appels: list[tuple[str, Any]] = []

    def statement(self) -> str:
        return "Énoncé <b>gras</b>"

    def summary(self) -> str:
        return "Bilan : 0 tentative"

    def hint(self, level: int | None = None) -> str:
        self.appels.append(("hint", level))
        return f"indice {level}"

    def twin(self) -> str:
        self.appels.append(("twin", None))
        return "jumeau"

    def verify(self, obj: Any) -> str:
        self.appels.append(("verify", obj))
        return "verdict"


def test_panneau_de_repli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "ipywidgets", None)
    s = _SeanceFactice()
    pan = build_panneau(s)
    assert isinstance(pan, PanneauFallback)
    assert str(pan) == "Énoncé <b>gras</b>\n\nBilan : 0 tentative"
    assert pan._repr_markdown_().startswith("Énoncé <b>gras</b>\n\n---\n\nBilan : 0 tentative")
    assert "installez `ipywidgets`" in pan._repr_markdown_()
    assert "Énoncé &lt;b&gt;gras&lt;/b&gt;" in pan._repr_html_()


def test_panneau_ipywidgets_boutons(monkeypatch: pytest.MonkeyPatch) -> None:
    widgets = pytest.importorskip("ipywidgets")
    import IPython.display

    affiches: list[str] = []
    monkeypatch.setattr(IPython.display, "display", lambda obj: affiches.append(obj.data))
    s = _SeanceFactice()
    pan = build_panneau(s)
    assert isinstance(pan, widgets.VBox)
    (btn_indice, choix, btn_jumeau, btn_bilan) = pan.children[1].children
    (saisie, btn_verifier) = pan.children[2].children

    btn_indice.click()
    choix.value = 3
    assert choix.value == 0  # remis sur « Relire le palier… »
    btn_jumeau.click()
    btn_bilan.click()
    btn_verifier.click()  # saisie vide
    saisie.value = "Vector([1, 2])"
    btn_verifier.click()
    saisie.value = "Vector([1, 2"
    btn_verifier.click()

    assert s.appels == [("hint", None), ("hint", 3), ("twin", None), ("verify", Vector([1, 2]))]
    assert affiches[0] == "Énoncé <b>gras</b>"
    assert affiches[1:6] == ["indice None", "indice 3", "jumeau", "Bilan : 0 tentative",
                             "Saisissez une réponse avant de vérifier."]
    assert affiches[6] == "verdict"
    assert affiches[7].startswith("Réponse illisible :") and affiches[7].endswith("Exemple attendu : `Vector([1, 2])`.")
