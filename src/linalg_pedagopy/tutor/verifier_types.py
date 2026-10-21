"""Types de vérificateurs du tuteur : enregistrement et contrôles croisés.

Un contrôle croisé construit une solution mathématique à partir de la fiche et vérifie que le
vérificateur l'accepte (et rejette une réponse fausse). Il sert à la validation des fiches.
"""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.field import symbols
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.tutor.lab import _eval_math_predicate, _structured_vector_candidates
from linalg_pedagopy.tutor.registry import VerifierType, register_verifier, requires
from linalg_pedagopy.tutor.verifiers import (
    VerificationResult,
    _eval_data_expr,
    _parse_indexed_expr,
    racines_reelles,
    verify_counterexample,
    verify_dimensions,
    verify_equalities,
    verify_formula,
    verify_inner_product,
    verify_matrix,
    verify_property,
    verify_value,
    verify_value_set,
)


def _sans_seance(fonction: Any) -> Any:
    """Adapte un vérificateur ``f(réponse, spécification, données)`` à la signature du registre."""
    return lambda _session, response, spec, raw_data: fonction(response, spec, raw_data)


# ---------------------------------------------------------------------------
# Contrôles croisés
# ---------------------------------------------------------------------------


def _cross_check_inner_product(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    errs: list[str] = []
    var_name = str(verif.get("inconnue", verif.get("unknown", "x")))
    n = int(verif.get("taille", verif.get("size", raw_data.get("n", 4))))
    cible_str = str(verif.get("cible", verif.get("target")))
    target_expr, vec_syms = _parse_indexed_expr(cible_str, var_name, n, raw_data)
    coeffs = [sp.diff(target_expr, s) for s in vec_syms]
    sol_vec = Vector(coeffs)
    if not session.verify(sol_vec).valid:
        errs.append("Cross-check échoué : le vecteur reconstruit par dérivation formelle est rejeté.")
    wrong_vec = Vector.ones(n) if sol_vec != Vector.ones(n) else Vector.zeros(n)
    if session.verify(wrong_vec).valid:
        errs.append("Cross-check échoué : un vecteur erroné est accepté.")
    return errs


def _cross_check_matrix(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    var_name = str(verif.get("inconnue", verif.get("unknown", "x")))
    n = int(verif.get("taille_entree", verif.get("input_size", raw_data.get("n", 6))))
    rows_list: list[list[sp.Expr]] = []
    if "lignes_cibles" in verif:
        for line_s in verif["lignes_cibles"]:
            rhs_part = line_s.split("=", 1)[1].strip() if "=" in line_s else line_s
            ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, raw_data)
            rows_list.append([sp.diff(ex_i, s) for s in vec_syms])
    else:
        cible_str = str(verif.get("cible", verif.get("target")))
        rhs_part = cible_str.split("=", 1)[1].strip() if "=" in cible_str else cible_str
        m = int(verif.get("taille_sortie", verif.get("output_size", raw_data.get("m", 3))))
        for i_val in range(1, m + 1):
            local_d = dict(raw_data)
            local_d["i"] = i_val
            ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, local_d)
            rows_list.append([sp.diff(ex_i, s) for s in vec_syms])
    if not session.verify(Matrix(rows_list)).valid:
        return ["Cross-check échoué : la matrice reconstruite formellement est rejetée."]
    return []


def _cross_check_formula(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    if not session.verify(verif.get("cible", verif.get("target"))).valid:
        return ["Cross-check échoué : la formule cible est rejetée."]
    return []


def _cross_check_value(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    errs: list[str] = []
    calcul = verif.get("calcul", verif.get("compute"))
    if isinstance(calcul, Mapping):
        sol_dict = {k: _eval_data_expr(str(v), raw_data) for k, v in calcul.items()}
        if not session.verify(sol_dict).valid:
            errs.append("Cross-check échoué : le dictionnaire de valeurs exactes est rejeté.")
    else:
        sol_val = _eval_data_expr(str(calcul), raw_data)
        if not session.verify(sol_val).valid:
            errs.append("Cross-check échoué : la valeur calculée est rejetée.")
    # Une erreur typique déclarée ne doit jamais coïncider avec la bonne réponse
    for idx, erreur in enumerate(verif.get("erreurs", ()) or (), start=1):
        fausse = _eval_data_expr(str(erreur["valeur"]), raw_data)
        if session.verify(fausse).valid:
            errs.append(f"Cross-check échoué : l'erreur typique {idx} est acceptée comme bonne réponse.")
    return errs


def _cross_check_value_set(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    param = symbols(str(verif["inconnue"]))[0]
    expr = sp.sympify(_eval_data_expr(str(verif["calcul"]), raw_data))
    attendues = racines_reelles(expr, param)
    if attendues is None:
        return ["Cross-check échoué : l'expression ne s'annule pas en un nombre fini de valeurs."]
    errs: list[str] = []
    if not session.verify(list(attendues)).valid:
        errs.append("Cross-check échoué : l'ensemble exact des valeurs est rejeté.")
    if attendues and session.verify(list(attendues)[:-1]).valid:
        errs.append("Cross-check échoué : un ensemble incomplet est accepté.")
    intrus = max(attendues, default=sp.Integer(0)) + 1
    if session.verify([*attendues, intrus]).valid:
        errs.append("Cross-check échoué : une valeur qui n'annule pas l'expression est acceptée.")
    return errs


def _cross_check_dimensions(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    if not session.verify(verif["attendu"]).valid:
        return ["Cross-check échoué : les dimensions attendues sont rejetées."]
    return []


def _cross_check_property(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    prop = str(verif.get("propriete", ""))
    if prop == "left_right_inverse_row":
        A = raw_data["A"]
        # Construct a right inverse via A^T (A A^T)^{-1}
        aat_inv = (A @ A.T).inv(strict=True)
        assert isinstance(aat_inv, Matrix)
        if not session.verify(A.T @ aat_inv).valid:
            return ["Cross-check échoué : la pseudo-inverse à droite A^T(AA^T)^-1 est rejetée."]
    elif prop == "square_inverse":
        A_inv = raw_data["A"].inv(strict=True)
        assert isinstance(A_inv, Matrix)
        if not session.verify(A_inv @ A_inv).valid:
            return ["Cross-check échoué : (A^-1)^2 est rejetée."]
    elif prop == "linear_system_solution":
        sol = raw_data["A"].solve(raw_data["b"])
        if not session.verify(sol.x).valid:
            return ["Cross-check échoué : la solution de A.solve(b) est rejetée."]
    elif prop == "two_right_inverses":
        B1 = Matrix([[1, 1], [0, 1], [0, 0]])
        B2 = Matrix([[-2, -2], [-1, 0], [1, 1]])
        if not session.verify((B1, B2)).valid:
            return ["Cross-check échoué : deux inverses à droite valides sont rejetées."]
    elif prop == "kkt_minimum_norm":
        C = raw_data["C"]
        cct_inv = (C @ C.T).inv(strict=True)
        assert isinstance(cct_inv, Matrix)
        if not session.verify(C.T @ (cct_inv @ raw_data["d"])).valid:
            return ["Cross-check échoué : la solution KKT est rejetée."]
    return []


_CONTRE_EXEMPLES = {
    "non_linearite_etendue": {"x": Vector([1, 0]), "y": Vector([0, 1]), "alpha": 1, "beta": 1},
    "ordre_gram_schmidt": (Vector([1, 0]), Vector([1, 1])),
    "inverse_matrice_positive": Matrix([[2, 1], [1, 2]]),
}


def _cross_check_counterexample(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    cas = str(verif.get("cas", ""))
    if cas in _CONTRE_EXEMPLES and not session.verify(_CONTRE_EXEMPLES[cas]).valid:
        return [f"Cross-check échoué sur {cas}."]
    return []


def _cross_check_equalities(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    if session.verify(["0", "0"]).valid:
        return ["Cross-check échoué : la chaîne triviale ['0', '0'] est acceptée."]
    return []


def _cross_check_lab(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    cands = _structured_vector_candidates()
    for h in verif.get("hypotheses", []):
        _eval_math_predicate(str(h), cands[0])
    return []


# ---------------------------------------------------------------------------
# Laboratoire : la vérification passe par la séance
# ---------------------------------------------------------------------------


def _verify_lab(session: Any, response: Any, spec: Mapping[str, Any], raw_data: Mapping[str, Any]) -> Any:
    if isinstance(response, Mapping):
        rep = session.lab().test(**response)
        return VerificationResult(rep.found_counterexample, rep.message)
    return VerificationResult(
        False,
        "Pour cet exercice vrai/faux, enregistrez votre prédiction avec ex.predict(...) / ex.predire(...) "
        "puis explorez avec lab = ex.lab() ; lab.test(...).",
    )


# ---------------------------------------------------------------------------
# Enregistrement
# ---------------------------------------------------------------------------

_CIBLE = requires("cible", message="Le vérificateur {type!r} requiert un champ 'cible'.")

for _vtype in (
    VerifierType(
        "produit_scalaire",
        ("inner_product",),
        _sans_seance(verify_inner_product),
        "un vecteur, par exemple Vector([0, 1, 0]).",
        _CIBLE,
        _cross_check_inner_product,
    ),
    VerifierType(
        "matrice",
        ("matrix",),
        _sans_seance(verify_matrix),
        "une matrice, par exemple Matrix([[1, 0], [0, 1]]).",
        requires("cible|lignes_cibles", message="Le vérificateur 'matrice' requiert 'cible' ou 'lignes_cibles'."),
        _cross_check_matrix,
    ),
    VerifierType(
        "formule",
        ("formula",),
        _sans_seance(verify_formula),
        "une formule sous forme de chaîne, par exemple 'norm_u**2 + norm_v**2'.",
        _CIBLE,
        _cross_check_formula,
    ),
    VerifierType(
        "valeur",
        ("value",),
        _sans_seance(verify_value),
        "une valeur exacte (entier, fraction, expression comme sqrt(2)) ou un dictionnaire de valeurs.",
        requires("calcul", message="Le vérificateur 'valeur' requiert un champ 'calcul'."),
        _cross_check_value,
    ),
    VerifierType(
        "ensemble_valeurs",
        ("value_set",),
        _sans_seance(verify_value_set),
        "une liste de valeurs exactes, par exemple [1, -2] (liste vide [] s'il n'y en a aucune).",
        requires(
            "calcul",
            "inconnue",
            message="Le vérificateur 'ensemble_valeurs' requiert les champs 'calcul' et 'inconnue'.",
        ),
        _cross_check_value_set,
    ),
    VerifierType(
        "propriete",
        ("property",),
        _sans_seance(verify_property),
        "l'objet demandé par l'énoncé (vecteur, matrice ou couple de matrices).",
        requires("propriete", message="Le vérificateur 'propriete' requiert un champ 'propriete'."),
        _cross_check_property,
    ),
    VerifierType(
        "contre_exemple",
        ("counterexample",),
        _sans_seance(verify_counterexample),
        "le contre-exemple sous la forme indiquée dans l'énoncé.",
        requires("cas", message="Le vérificateur 'contre_exemple' requiert un champ 'cas'."),
        _cross_check_counterexample,
    ),
    VerifierType(
        "egalites",
        ("equalities",),
        _sans_seance(verify_equalities),
        "une liste de chaînes, une par maillon de la chaîne d'égalités.",
        requires(message=""),
        _cross_check_equalities,
    ),
    VerifierType(
        "dimensions",
        (),
        _sans_seance(verify_dimensions),
        "un dictionnaire, par exemple {'a': (3, 2), 'b': 'invalide'}.",
        requires("attendu", message="Le vérificateur 'dimensions' requiert un champ 'attendu'."),
        _cross_check_dimensions,
    ),
    VerifierType(
        "labo",
        ("lab",),
        _verify_lab,
        "un dictionnaire d'instances à tester au laboratoire, après ex.predict(...).",
        requires("enonce|affirmations", message="Le vérificateur 'labo' requiert 'enonce' ou 'affirmations'."),
        _cross_check_lab,
        requires_twin=False,
        checks_hint_leak=False,
    ),
):
    register_verifier(_vtype)
