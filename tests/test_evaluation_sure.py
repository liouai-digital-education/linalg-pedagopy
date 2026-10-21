"""Interpréteur sûr du tuteur (étapes 6.4, 6.5 et 6.7 du plan v6).

Chaque tentative d'évasion utilise un effet de bord observable (``print`` vers une liste) :
le test échoue si le code passe, quel que soit le message d'erreur.
"""

from __future__ import annotations

import pytest
import sympy as sp

from linalg_pedagopy import Matrix, Vector, symbols
from linalg_pedagopy.exercises.generators import TwinExercise, generateurs, generators
from linalg_pedagopy.tutor.evaluation_sure import EvaluationRefusee, en_expression, evaluer, expression, lire_donnee
from linalg_pedagopy.tutor.hints import evaluate_twin_spec
from linalg_pedagopy.tutor.lab import _eval_math_predicate
from linalg_pedagopy.tutor.lock import LockedNamespace, _get_namespace_raw_dict
from linalg_pedagopy.tutor.panel import _parse_answer
from linalg_pedagopy.tutor.verifiers import _eval_data_expr, _parse_indexed_expr

NOMS = {"Vector": Vector, "Matrix": Matrix, "sqrt": sp.sqrt, "u": Vector([1, 2])}

# Charge utile : exécute print si une évasion réussit
CHARGE = "__import__('builtins').print('EVASION')"

EVASIONS = [
    "Vector.__init__.__globals__['__builtins__']['print']('EVASION')",
    "u.__class__.__mro__[-1].__subclasses__()",
    "sqrt.__globals__",
    "__import__('os')",
    "(lambda: 1)()",
    "[x for x in (1, 2)]",
    "{x: 1 for x in (1, 2)}",
    "(y := 1)",
    "f'{u}'",
    "u.format",
    "'{0.__class__}'.format(u)",
    "Vector(*[1, 2])",
    "Matrix(**{'rows': 1})",
    f"Vector([\"{CHARGE}\"])",
    f"Matrix([[\"{CHARGE}\"]])",
    f"sqrt(\"{CHARGE}\")",
    f"u + \"{CHARGE}\"",
    f"u.dot(Vector([\"{CHARGE}\"]))",
    "2 ** 10 ** 8",
    "[0] * 10 ** 9",
]


@pytest.fixture
def sans_effet(capsys: pytest.CaptureFixture[str]):  # type: ignore[no-untyped-def]
    yield
    assert "EVASION" not in capsys.readouterr().out


@pytest.mark.parametrize("texte", EVASIONS)
def test_evasions_refusees(texte: str, sans_effet: None) -> None:
    with pytest.raises((EvaluationRefusee, NameError, SyntaxError)):
        evaluer(texte, NOMS)


@pytest.mark.parametrize("texte", EVASIONS)
def test_evasions_refusees_en_mode_expression(texte: str, sans_effet: None) -> None:
    with pytest.raises((EvaluationRefusee, NameError, SyntaxError, sp.SympifyError, TypeError, AttributeError)):
        expression(texte, NOMS)


def test_modules_inaccessibles() -> None:
    with pytest.raises(EvaluationRefusee, match="« sp » est un module"):
        evaluer("sp.sympify('x')", {"sp": sp})


def test_constructions_admises() -> None:
    assert evaluer("Vector([1, 2]) + u", NOMS) == Vector([2, 4])
    assert evaluer("Matrix([[1, 0], [0, 1]]) @ u", NOMS) == Vector([1, 2])
    assert evaluer("u[0] * 3 - 1 if u.size == 2 else 0", NOMS) == 2
    assert evaluer("{'a': (3, 2), 'b': 'invalide'}", NOMS) == {"a": (3, 2), "b": "invalide"}
    assert evaluer("[1, -2][::-1]", NOMS) == [-2, 1]
    assert evaluer("not (1 < 2 <= 2) or 3 in [3]", NOMS) is True
    assert evaluer("1/3", NOMS) == 1 / 3  # sémantique de Python, comme eval
    assert evaluer("2 ** 100", NOMS) == 2**100


def test_mode_expression_comme_sympify() -> None:
    x, a = sp.symbols("x a")
    assert expression("1/3 + x^2") == sp.Rational(1, 3) + x**2
    assert expression("sqrt(2) * pi + Abs(a)") == sp.sqrt(2) * sp.pi + sp.Abs(a)
    assert expression("0.5") == sp.Float("0.5")
    assert expression("a + 1", {"a": sp.Integer(4)}) == 5
    with pytest.raises(EvaluationRefusee):
        expression("'chaîne'")
    assert en_expression(["1/2", 3, ("a",)]) == sp.sympify([sp.Rational(1, 2), 3, (a,)])
    (ar,) = symbols("a")
    assert lire_donnee([[1, "a"], ["a", 1]]) == [[1, ar], [ar, 1]]


def test_texte_libre_des_generateurs() -> None:
    """Le texte d'un générateur reste admis s'il ne peut appeler aucune fonction."""
    res = evaluate_twin_spec("generateurs.contre_exemple_guide(famille='R^2, coefficients dans {0, 1}')")
    assert isinstance(res, TwinExercise)
    refus = evaluate_twin_spec(f"generateurs.statistiques_vecteur(values=(\"{CHARGE}\",))")
    assert isinstance(refus, str) and "Expression refusée" in refus


def test_jumeau_limite_aux_generateurs(sans_effet: None) -> None:
    """Le champ jumeau ne voit que l'espace de noms des générateurs (étape 6.5)."""
    assert evaluate_twin_spec("generators.Vector([1])").startswith("Erreur dans l'exercice jumeau")
    erreur = evaluate_twin_spec("generators.statistiques_vecteur.__globals__")
    assert isinstance(erreur, str) and "attribut « __globals__ »" in erreur
    assert isinstance(evaluate_twin_spec("generators.vector_statistics()"), TwinExercise)
    assert generateurs is generators


@pytest.mark.parametrize(
    "lecture",
    [
        lambda: _parse_answer(f"Vector([\"{CHARGE}\"])"),
        lambda: _eval_data_expr(CHARGE, {}),
        lambda: _eval_math_predicate(f"norm(x) <= {CHARGE}", {"x": Vector([1])}),
        lambda: _parse_indexed_expr(f"p[1] + {CHARGE}", "p", 2),
        lambda: LockedNamespace({"v": [1, CHARGE]}, lambda: True),
    ],
)
def test_chaque_point_d_entree_du_tuteur(lecture, sans_effet: None) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(Exception):  # noqa: B017
        lecture()


def test_donnees_de_fiche_avec_parametre() -> None:
    ns = LockedNamespace({"A": [[1, "a"], ["a", 1]]}, lambda: True)
    (a,) = symbols("a")  # symbole réel, comme Matrix([[1, "a"], ...]) avant l'étape 6.4
    assert _get_namespace_raw_dict(ns)["A"].to_sympy() == sp.Matrix([[1, a], [a, 1]])


def test_indices_a_partir_de_un() -> None:
    expr, syms = _parse_indexed_expr("p[4] - (p[1] + p[2] + p[3])/3", "p", 4)
    assert expr == syms[3] - (syms[0] + syms[1] + syms[2]) / 3
    expr, syms = _parse_indexed_expr("x[i] + x[i + 1]", "x", 3, {"i": 2})
    assert expr == syms[1] + syms[2]


def test_plus_aucun_eval_ni_sympify_de_chaine() -> None:
    """Le tuteur et les exercices ne lisent plus de texte qu'avec l'interpréteur sûr."""
    import re
    from pathlib import Path

    racine = Path(__file__).resolve().parent.parent / "src" / "linalg_pedagopy"
    interdits = re.compile(r"\beval\(|\bexec\(|sympify\(|parse_expr\(")
    trouves = [
        f"{f.relative_to(racine)}:{i}"
        for dossier in ("tutor", "tuteur", "exercises")
        for f in sorted((racine / dossier).rglob("*.py"))
        if f.name != "evaluation_sure.py"
        for i, ligne in enumerate(f.read_text(encoding="utf-8").splitlines(), start=1)
        if interdits.search(ligne)
    ]
    assert trouves == []
