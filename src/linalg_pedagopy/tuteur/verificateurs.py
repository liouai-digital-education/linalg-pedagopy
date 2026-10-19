"""Les 9 vérificateurs spécialisés du tuteur VMLS (§7.6)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

import sympy as sp

from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.core.field import symbols, to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing


@dataclass(frozen=True)
class VerificationResult:
    """Résultat d'une vérification par le tuteur (§7.6)."""

    valide: bool
    diagnostic: str
    note_simplicite: str | None = None

    def __bool__(self) -> bool:
        return self.valide

    def __str__(self) -> str:
        return self.diagnostic

    def __repr__(self) -> str:
        return self.diagnostic


def _format_linear_comb(coeffs: Sequence[sp.Expr], var_name: str) -> str:
    """Formate une combinaison linéaire sum_j coeffs[j] * var_{j+1} de façon lisible (cf. §7.8)."""
    # Détecter s'il y a un groupe de coefficients identiques négatifs -1/k (comme dans 6.4)
    pos_unit_terms: list[str] = []
    neg_frac_groups: dict[sp.Expr, list[str]] = {}
    other_terms: list[str] = []

    for j, c in enumerate(coeffs, start=1):
        v_j = f"{var_name}_{j}"
        if oracle.decide(c).verdict == Verdict.ZERO:
            continue
        if c == 1:
            pos_unit_terms.append(v_j)
        elif c.is_Rational and c < 0 and c.p == -1 and c.q > 1:
            denom = sp.Integer(c.q)
            neg_frac_groups.setdefault(denom, []).append(v_j)
        else:
            other_terms.append((c, v_j))  # type: ignore[arg-type]

    if pos_unit_terms and len(neg_frac_groups) == 1 and not other_terms:
        denom, group_vars = next(iter(neg_frac_groups.items()))
        pos_str = " + ".join(pos_unit_terms)
        if len(group_vars) > 1:
            grp_str = " + ".join(group_vars)
            return f"{pos_str} - ({grp_str})/{denom}"
        return f"{pos_str} - {group_vars[0]}/{denom}"

    parts: list[str] = []
    for j, c in enumerate(coeffs, start=1):
        if oracle.decide(c).verdict == Verdict.ZERO:
            continue
        v_j = f"{var_name}_{j}"
        if not parts:
            if c == 1:
                parts.append(v_j)
            elif c == -1:
                parts.append(f"-{v_j}")
            else:
                parts.append(f"({c})·{v_j}" if not c.is_Integer else f"{c}·{v_j}")
        else:
            if c > 0:
                parts.append(f"+ {v_j}" if c == 1 else f"+ {c}·{v_j}")
            else:
                abs_c = -c
                parts.append(f"- {v_j}" if abs_c == 1 else f"- {abs_c}·{v_j}")
    return " ".join(parts) if parts else "0"


def _parse_indexed_expr(
    expr_str: str,
    var_name: str,
    n: int,
    extra_locals: Mapping[str, Any] | None = None,
) -> tuple[sp.Expr, list[sp.Symbol]]:
    """Convertit une expression indexée 1-based comme 'p[4] - (p[1]+p[2]+p[3])/3' en expression SymPy."""
    vec_syms = [sp.Symbol(f"{var_name}_{k}", real=True) for k in range(1, n + 1)]
    rewritten = re.sub(
        rf"\b{re.escape(var_name)}\[([^\]]+)\]",
        lambda m: f"__idx_{var_name}__({m.group(1)})",
        expr_str,
    )
    local_env: dict[str, Any] = {
        f"{var_name}_{k}": vec_syms[k - 1] for k in range(1, n + 1)
    }
    local_env[f"__idx_{var_name}__"] = lambda idx: vec_syms[int(idx) - 1]
    if extra_locals:
        local_env.update(extra_locals)
    parsed = sp.sympify(rewritten, locals=local_env)
    return sp.expand(parsed), vec_syms


def verifier_produit_scalaire(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 1 : produit_scalaire (§7.6)."""
    if not isinstance(reponse, Vector):
        try:
            reponse = Vector(reponse)
        except Exception:
            return VerificationResult(
                False,
                "Votre réponse doit être un vecteur (ex. Vector([...])).",
            )

    var_name = str(spec.get("inconnue", "x"))
    n = int(spec.get("taille", donnees.get("n", len(reponse))))
    if len(reponse) != n:
        return VerificationResult(
            False,
            f"Taille incorrecte : votre vecteur est de taille {len(reponse)}, "
            f"alors que {var_name} est dans R^{n}.",
        )

    cible_str = str(spec["cible"])
    target_expr, vec_syms = _parse_indexed_expr(cible_str, var_name, n, donnees)

    student_expr = sp.expand(
        sum((reponse[k] * vec_syms[k] for k in range(n)), sp.Integer(0))
    )
    student_fmt = _format_linear_comb(reponse.entries, var_name)

    diff = sp.simplify(student_expr - target_expr)
    if oracle.decide(diff).verdict == Verdict.ZERO:
        return VerificationResult(
            True,
            f"Exact ! Avec votre vecteur, a^T {var_name} = {student_fmt}.",
        )

    # Erreur de signe
    if oracle.decide(sp.simplify(student_expr + target_expr)).verdict == Verdict.ZERO:
        return VerificationResult(
            False,
            f"Avec votre vecteur, a^T {var_name} = {student_fmt} : c'est l'opposé de la quantité demandée (erreur de signe).",
        )

    # Résultat proportionnel (facteur de normalisation)
    if student_expr != 0 and target_expr != 0:
        ratio = sp.simplify(student_expr / target_expr)
        if not ratio.free_symbols and ratio != 1:
            return VerificationResult(
                False,
                f"Avec votre vecteur, a^T {var_name} = {student_fmt} : le résultat est proportionnel à la cible (facteur {ratio}). "
                "Vérifiez la normalisation !",
            )

    # Composante qui ne devrait pas intervenir
    target_free = target_expr.free_symbols
    student_free = student_expr.free_symbols
    extra_syms = sorted(student_free - target_free, key=lambda s: s.name)
    if extra_syms:
        return VerificationResult(
            False,
            f"Avec votre vecteur, a^T {var_name} = {student_fmt} : la composante {extra_syms[0]} "
            "intervient alors qu'elle ne figure pas dans la quantité à modéliser.",
        )

    return VerificationResult(
        False,
        f"Avec votre vecteur, a^T {var_name} = {student_fmt}. "
        f"Quels coefficients faut-il placer devant chaque composante de {var_name} ?",
    )


def verifier_matrice(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 2 : matrice — contrôle de la taille puis diagnostic ligne par ligne (§7.6, §7.7, §7.8)."""
    # Support d'un couple (A, b) si second_membre est attendu
    expected_rhs = spec.get("second_membre")
    rhs_student: Vector | None = None
    if isinstance(reponse, tuple) and len(reponse) == 2:
        mat_in, rhs_in = reponse
        A = mat_in if isinstance(mat_in, Matrix) else Matrix(mat_in)
        rhs_student = rhs_in if isinstance(rhs_in, Vector) else Vector(rhs_in)
    elif isinstance(reponse, Mapping) and "A" in reponse:
        A = reponse["A"] if isinstance(reponse["A"], Matrix) else Matrix(reponse["A"])
        if "b" in reponse:
            rhs_student = reponse["b"] if isinstance(reponse["b"], Vector) else Vector(reponse["b"])
    else:
        try:
            A = reponse if isinstance(reponse, Matrix) else Matrix(reponse)
        except Exception:
            return VerificationResult(
                False,
                "Votre réponse doit être une Matrix (ou un couple (A, b) si un second membre est demandé).",
            )

    var_name = str(spec.get("inconnue", "x"))
    out_name = str(spec.get("nom_sortie", "d"))
    n = int(spec.get("taille_entree", donnees.get("n", 6)))

    # Construction des expressions cibles par ligne
    target_row_exprs: list[sp.Expr] = []
    vec_syms: list[sp.Symbol] = []
    if "lignes_cibles" in spec:
        raw_lines = list(spec["lignes_cibles"])
        m = len(raw_lines)
        for line_s in raw_lines:
            rhs_part = line_s.split("=", 1)[1].strip() if "=" in line_s else line_s
            ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, donnees)
            target_row_exprs.append(ex_i)
    else:
        cible_str = str(spec["cible"])
        if "=" in cible_str:
            lhs_part, rhs_part = cible_str.split("=", 1)
            lhs_part = lhs_part.strip()
            if "[" in lhs_part:
                out_name = lhs_part.split("[", 1)[0].strip()
        else:
            rhs_part = cible_str
        m = int(spec.get("taille_sortie", donnees.get("m", 3)))
        for i_val in range(1, m + 1):
            local_d = dict(donnees)
            local_d["i"] = i_val
            ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, local_d)
            target_row_exprs.append(ex_i)

    # 1. Contrôle de la taille (m x n)
    if A.shape != (m, n):
        return VerificationResult(
            False,
            f"Taille incorrecte : votre matrice est de taille ({A.rows} x {A.cols}), "
            f"alors que l'entrée {var_name} est de taille {n} et la sortie {out_name} de taille {m}.",
        )

    # 2. Contrôle ligne par ligne
    correct_rows: list[int] = []
    wrong_rows: list[tuple[int, str]] = []

    for row_idx in range(m):
        row_coeffs = A[row_idx]
        student_row_expr = sp.expand(
            sum((row_coeffs[j] * vec_syms[j] for j in range(n)), sp.Integer(0))
        )
        diff = sp.simplify(student_row_expr - target_row_exprs[row_idx])
        if oracle.decide(diff).verdict == Verdict.ZERO:
            correct_rows.append(row_idx + 1)
        else:
            row_fmt = _format_linear_comb(row_coeffs, var_name)
            wrong_rows.append((row_idx + 1, row_fmt))

    if wrong_rows:
        lines_msg: list[str] = [f"Taille correcte ({m} x {n})."]
        if correct_rows:
            if len(correct_rows) == 1:
                lines_msg[0] += f" Ligne {correct_rows[0]} correcte."
            else:
                c_str = (
                    ", ".join(str(r) for r in correct_rows[:-1])
                    + f" et {correct_rows[-1]}"
                )
                lines_msg[0] += f" Lignes {c_str} correctes."
        first_bad_idx, first_bad_fmt = wrong_rows[0]
        lines_msg.append(
            f"Votre ligne {first_bad_idx} calcule {out_name}_{first_bad_idx} = {first_bad_fmt}."
        )
        question_hint = spec.get(
            "question_ligne",
            f"Relisez la définition de {out_name}_{first_bad_idx} : quel est le prix « du jour » pour i = {first_bad_idx} ?"
            if out_name == "d" and var_name == "p"
            else f"Relisez la définition de la composante {out_name}_{first_bad_idx} pour i = {first_bad_idx}.",
        )
        lines_msg.append(str(question_hint))
        return VerificationResult(False, "\n".join(lines_msg))

    # 3. Contrôle du second membre éventuel
    if expected_rhs is not None and rhs_student is not None:
        b_expected = Vector(expected_rhs)
        if len(rhs_student) != len(b_expected):
            return VerificationResult(
                False,
                f"La matrice A ({m} x {n}) est correcte, mais votre second membre b est de taille {len(rhs_student)} (attendu {len(b_expected)}).",
            )
        for idx, (bs, be) in enumerate(zip(rhs_student, b_expected), start=1):
            if oracle.decide(bs - be).verdict != Verdict.ZERO:
                return VerificationResult(
                    False,
                    f"La matrice A ({m} x {n}) est correcte, mais la composante b_{idx} = {bs} du second membre ne correspond pas à la condition {idx}.",
                )

    return VerificationResult(
        True,
        f"Taille correcte ({m} x {n}). Toutes les lignes de votre matrice calculent exactement {out_name} = A {var_name}.",
    )


def verifier_formule(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 3 : formule symbolique en fonction de paramètres (§7.6)."""
    param_names = list(spec.get("parametres", ["norm_u", "norm_v"]))
    param_syms = {name: symbols(name)[0] for name in param_names}
    local_env: dict[str, Any] = dict(param_syms)
    local_env.update({"sqrt": sp.sqrt, "Rational": sp.Rational})
    for k, v in donnees.items():
        if isinstance(v, (int, float, str)):
            local_env[k] = to_exact(v)

    cible_raw = spec["cible"]
    if isinstance(cible_raw, Mapping):
        if not isinstance(reponse, Mapping):
            return VerificationResult(
                False,
                f"Attendu un dictionnaire de formules pour les clés {list(cible_raw.keys())}.",
            )
        for key, target_s in cible_raw.items():
            if key not in reponse:
                return VerificationResult(False, f"Formule manquante pour '{key}'.")
            sub_res = verifier_formule(
                reponse[key],
                {"parametres": param_names, "cible": target_s},
                donnees,
            )
            if not sub_res.valide:
                return VerificationResult(False, f"Pour '{key}' : {sub_res.diagnostic}")
        return VerificationResult(True, "Toutes vos formules symboliques sont exactes !")

    try:
        student_expr = (
            reponse
            if isinstance(reponse, sp.Expr)
            else sp.sympify(str(reponse), locals=local_env)
        )
        target_expr = sp.sympify(str(cible_raw), locals=local_env)
    except Exception as exc:
        return VerificationResult(
            False,
            f"Impossible d'interpréter votre formule ({exc}). Utilisez les variables {param_names}.",
        )

    diff = sp.simplify(student_expr - target_expr)
    if oracle.decide(diff).verdict == Verdict.ZERO:
        return VerificationResult(
            True,
            f"Formule exacte ({student_expr}) !",
        )

    # Diagnostic : que donne la formule de l'étudiant pour des valeurs unitaires ?
    test_subs = {sym: sp.Integer(1) for sym in param_syms.values()}
    val_stu = sp.simplify(student_expr.xreplace(test_subs))
    return VerificationResult(
        False,
        f"Votre formule ({student_expr}) ne coïncide pas avec l'expression attendue "
        f"(par exemple, lorsque les paramètres valent 1, votre formule donne {val_stu}). "
        "Avez-vous bien développé le carré de la norme et utilisé l'hypothèse d'orthogonalité ?",
    )


def _eval_data_expr(expr_str: str, raw_data: Mapping[str, Any]) -> Any:
    env: dict[str, Any] = dict(raw_data)
    env.update(
        {
            "Vector": Vector,
            "Matrix": Matrix,
            "sqrt": sp.sqrt,
            "Rational": sp.Rational,
            "GramSchmidt": GramSchmidt,
        }
    )
    with suspend_tracing():
        return eval(expr_str, {"__builtins__": {}}, env)  # noqa: S307


def _detect_typical_value_error(
    student_val: sp.Expr,
    raw_data: Mapping[str, Any],
) -> str | None:
    """Détecteurs d'erreurs typiques de la table §7.6 (page 22)."""
    vecs = {k: v for k, v in raw_data.items() if isinstance(v, Vector)}
    with suspend_tracing():
        for name, v in vecs.items():
            # 1. ||x|| au lieu de rms(x)
            if oracle.decide(student_val - v.norm()).verdict == Verdict.ZERO:
                return (
                    "Votre valeur est la norme. Que faut-il encore faire pour "
                    "obtenir une moyenne quadratique ?"
                )
            # 2. Écart type avec 1/(n - 1) au lieu de 1/n
            if len(v) > 1:
                std_n_minus_1 = v.demean().norm() / sp.sqrt(sp.Integer(len(v) - 1))
                if oracle.decide(student_val - std_n_minus_1).verdict == Verdict.ZERO:
                    return (
                        "Vous avez utilisé la convention statistique en n − 1. "
                        "Quelle est la définition de VMLS ?"
                    )

        vec_items = list(vecs.items())
        if len(vec_items) >= 2:
            (_, x), (_, y) = vec_items[0], vec_items[1]
            if len(x) == len(y):
                # 3. Distance au carré ||x - y||^2
                dist_sq = (x - y).norm_sq()
                if oracle.decide(student_val - dist_sq).verdict == Verdict.ZERO:
                    return "Votre valeur est ||x − y||²."
                # 4. Cosinus de l'angle de x et y au lieu de la corrélation
                if x.is_zero() is False and y.is_zero() is False:
                    cos_xy = x.dot(y) / (x.norm() * y.norm())
                    if oracle.decide(student_val - cos_xy).verdict == Verdict.ZERO:
                        return (
                            "Vous avez calculé le cosinus de l'angle entre x et y. "
                            "Sur quels vecteurs la corrélation se calcule-t-elle ?"
                        )
    return None


def verifier_valeur(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 4 : valeur exacte calculée à la volée + détecteurs d'erreurs typiques (§7.6)."""
    calcul_spec = spec["calcul"]

    # Cas multi-questions (dictionnaire de calculs, ex. 3.9)
    if isinstance(calcul_spec, Mapping):
        if not isinstance(reponse, Mapping):
            # Si l'étudiant passe une seule valeur scalaire, vérifier si elle déclenche un détecteur d'erreur typique !
            try:
                stu_scalar = to_exact(reponse)
                err_msg = _detect_typical_value_error(stu_scalar, donnees)
                if err_msg is not None:
                    return VerificationResult(False, err_msg)
            except Exception:
                pass
            return VerificationResult(
                False,
                f"Attendu un dictionnaire de réponses pour les clés {list(calcul_spec.keys())}.",
            )

        for key, expr_s in calcul_spec.items():
            if key not in reponse:
                return VerificationResult(False, f"Clé '{key}' manquante dans votre réponse.")
            sub_res = verifier_valeur(reponse[key], {"calcul": expr_s}, donnees)
            if not sub_res.valide:
                return VerificationResult(False, f"Pour '{key}' : {sub_res.diagnostic}")
        return VerificationResult(True, "Toutes vos valeurs sont exactes !")

    expected = _eval_data_expr(str(calcul_spec), donnees)

    if isinstance(expected, Vector):
        try:
            stu_vec = reponse if isinstance(reponse, Vector) else Vector(reponse)
        except Exception:
            return VerificationResult(False, "Votre réponse doit être un vecteur.")
        if len(stu_vec) != len(expected):
            return VerificationResult(
                False,
                f"Taille de vecteur incorrecte : reçu {len(stu_vec)}, attendu {len(expected)}.",
            )
        if stu_vec == expected:
            return VerificationResult(True, "Exact ! Votre vecteur est correct.")
        for idx, (s_i, e_i) in enumerate(zip(stu_vec, expected), start=1):
            if oracle.decide(s_i - e_i).verdict != Verdict.ZERO:
                return VerificationResult(
                    False,
                    f"La composante {idx} de votre vecteur ({s_i}) est incorrecte.",
                )

    if isinstance(expected, Matrix):
        try:
            stu_mat = reponse if isinstance(reponse, Matrix) else Matrix(reponse)
        except Exception:
            return VerificationResult(False, "Votre réponse doit être une matrice.")
        if stu_mat == expected:
            return VerificationResult(True, "Exact ! Votre matrice est correcte.")
        return VerificationResult(False, "Votre matrice ne correspond pas au résultat attendu.")

    if isinstance(expected, bool):
        if bool(reponse) is expected:
            return VerificationResult(True, "Exact !")
        return VerificationResult(False, "Ce n'est pas la bonne conclusion.")

    try:
        stu_val = to_exact(reponse)
        exp_val = to_exact(expected)
    except Exception:
        return VerificationResult(False, f"Réponse scalaire exacte attendue (reçu {reponse!r}).")

    if oracle.decide(stu_val - exp_val).verdict == Verdict.ZERO:
        return VerificationResult(True, "Exact ! Votre valeur est correcte.")

    typical = _detect_typical_value_error(stu_val, donnees)
    if typical is not None:
        return VerificationResult(False, typical)

    if oracle.decide(stu_val + exp_val).verdict == Verdict.ZERO:
        return VerificationResult(
            False,
            f"Votre valeur ({stu_val}) a le mauvais signe.",
        )

    return VerificationResult(
        False,
        f"Votre valeur ({stu_val}) n'est pas égale à la valeur exacte attendue. Vérifiez chaque étape de votre calcul.",
    )


def verifier_propriete(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 5 : vérification par propriété définissante sans stocker de corrigé (§7.3 Principe 1, §7.6)."""
    prop_kind = str(spec.get("propriete", "right_inverse"))

    with suspend_tracing():
        if prop_kind == "two_right_inverses":
            # Exercice 11.11 : fournir deux inverses à droite distinctes B1 et B2 de A
            A = donnees["A"]
            if not isinstance(reponse, (tuple, list)) or len(reponse) != 2:
                return VerificationResult(
                    False,
                    "Fournissez un couple (B1, B2) de deux matrices inverses à droite distinctes.",
                )
            B1 = reponse[0] if isinstance(reponse[0], Matrix) else Matrix(reponse[0])
            B2 = reponse[1] if isinstance(reponse[1], Matrix) else Matrix(reponse[1])
            expected_shape = (A.cols, A.rows)
            for idx, B in enumerate((B1, B2), start=1):
                if B.shape != expected_shape:
                    return VerificationResult(
                        False,
                        f"B{idx} a la taille {B.shape}, alors qu'une inverse à droite de A ({A.shape}) doit être de taille {expected_shape}.",
                    )
                prod = A @ B
                if prod != Matrix.identity(A.rows):
                    return VerificationResult(
                        False,
                        f"Pour B{idx}, le produit A B{idx} vaut {prod} ≠ I_{A.rows}.",
                    )
            if B1 == B2:
                return VerificationResult(
                    False,
                    "A B1 = I et A B2 = I sont vérifiées, mais vos deux matrices B1 et B2 sont identiques ! "
                    "Choisissez deux valeurs différentes pour la variable libre.",
                )
            return VerificationResult(
                True,
                f"Bravo ! A B1 = I_{A.rows}, A B2 = I_{A.rows} et B1 ≠ B2 : vos deux inverses à droite sont valides.",
            )

        if prop_kind == "left_right_inverse_row":
            # Exercice 11.7 : inverse à droite d'une matrice ligne A (1 x n) ; pas d'inverse à gauche si n > 1
            A = donnees["A"]
            B = reponse if isinstance(reponse, Matrix) else Matrix(reponse)
            if B.shape != (A.cols, 1):
                return VerificationResult(
                    False,
                    f"Pour une matrice ligne A de taille {A.shape}, une inverse à droite B doit être de taille ({A.cols}, 1).",
                )
            prod = A @ B
            if prod == Matrix.identity(1):
                return VerificationResult(
                    True,
                    "Exact ! A B = [1] : votre colonne B est bien une inverse à droite de A (et A n'a pas d'inverse à gauche car ses colonnes sont liées).",
                )
            return VerificationResult(
                False,
                f"Avec votre matrice B, le produit A B vaut {prod} au lieu de [1].",
            )

        if prop_kind == "linear_system_solution":
            # Ex. 11.10 : flux de trésorerie c vérifiant A c = b (équations de la VAN)
            A = donnees["A"]
            b = donnees["b"]
            c_vec = reponse if isinstance(reponse, Vector) else Vector(reponse)
            if len(c_vec) != A.cols:
                return VerificationResult(
                    False,
                    f"Votre vecteur est de taille {len(c_vec)}, attendu {A.cols}.",
                )
            calc_b = A @ c_vec
            if calc_b == b:
                return VerificationResult(
                    True,
                    "Exact ! Votre vecteur de flux de trésorerie reproduit toutes les valeurs actuelles nettes annoncées.",
                )
            return VerificationResult(
                False,
                f"Avec votre vecteur c, les VAN obtenues sont A c = {calc_b} (attendu : {b}).",
            )

        if prop_kind == "square_inverse":
            # Ex. 11.9 : inverse de A^2 exprimée en fonction de B = A^{-1}
            A = donnees["A"]
            B_inv = A.inv(strict=True)
            assert isinstance(B_inv, Matrix)
            if isinstance(reponse, str):
                cleaned = reponse.replace(" ", "")
                if cleaned in ("B@B", "B**2", "B^2", "(A^-1)^2", "A^-2"):
                    return VerificationResult(
                        True,
                        "Exact ! Comme A² B² = A (A B) B = A I B = A B = I, l'inverse de A² est B² = (A⁻¹)².",
                    )
            mat_stu = reponse if isinstance(reponse, Matrix) else Matrix(reponse)
            prod = (A @ A) @ mat_stu
            if prod == Matrix.identity(A.rows):
                return VerificationResult(
                    True,
                    "Exact ! Le produit A² · X vaut bien I : votre matrice est l'inverse de A².",
                )
            return VerificationResult(
                False,
                f"Le produit A² par votre matrice donne {prod} ≠ I.",
            )

        if prop_kind == "kkt_minimum_norm":
            # Ex. 20.11 : solution de norme minimale de C x = d via le système KKT
            C = donnees["C"]
            d = donnees["d"]
            x_stu = reponse if isinstance(reponse, Vector) else Vector(reponse)
            if len(x_stu) != C.cols:
                return VerificationResult(
                    False,
                    f"Votre vecteur x est de taille {len(x_stu)}, attendu {C.cols}.",
                )
            cx = C @ x_stu
            if cx != d:
                return VerificationResult(
                    False,
                    f"Votre vecteur ne satisfait pas la contrainte C x = d : C x = {cx} ≠ {d}.",
                )
            # Optimalité KKT : x doit appartenir à Im(C^T), c'est-à-dire C^T (C C^T)^{-1} d
            cct_inv = (C @ C.T).inv(strict=True)
            assert isinstance(cct_inv, Matrix)
            x_opt = C.T @ (cct_inv @ d)
            if x_stu == x_opt:
                return VerificationResult(
                    True,
                    "Exact ! Votre vecteur x vérifie C x = d et les conditions KKT de norme minimale.",
                )
            return VerificationResult(
                False,
                f"Votre vecteur vérifie C x = d (||x||² = {x_stu.norm_sq()}), mais n'est pas de norme minimale "
                "(2x + C^T z = 0 n'est pas satisfait).",
            )

    return VerificationResult(False, f"Propriété {prop_kind!r} non reconnue.")


def _simplicity_score(objs: Sequence[Any]) -> str:
    max_dim = 1
    max_height = 0
    for obj in objs:
        if isinstance(obj, Vector):
            max_dim = max(max_dim, len(obj))
            for e in obj.entries:
                if e.is_Rational:
                    max_height = max(max_height, abs(int(e.p)), abs(int(e.q)))
        elif isinstance(obj, Matrix):
            max_dim = max(max_dim, obj.rows, obj.cols)
            for e in obj.flat_entries:
                if e.is_Rational:
                    max_height = max(max_height, abs(int(e.p)), abs(int(e.q)))
    qual = "excellente (très simple)" if max_dim <= 3 and max_height <= 2 else "bonne"
    return f"dimension max = {max_dim}, hauteur max des coefficients = {max_height} ({qual})"


def verifier_contre_exemple(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 6 : validation d'un contre-exemple et note de simplicité (§7.6)."""
    ce_kind = str(spec.get("cas", ""))

    with suspend_tracing():
        if ce_kind == "non_linearite_2_2":
            # Exercice 2.2 : démontrer par contre-exemple que f(x) = max_k x_k ou f(x) = x_1^2 n'est pas linéaire
            if not isinstance(reponse, Mapping) or "x" not in reponse or "y" not in reponse:
                return VerificationResult(
                    False,
                    "Fournissez un dictionnaire {'x': Vector([...]), 'y': Vector([...]), 'alpha': ..., 'beta': ...}.",
                )
            x = reponse["x"] if isinstance(reponse["x"], Vector) else Vector(reponse["x"])
            y = reponse["y"] if isinstance(reponse["y"], Vector) else Vector(reponse["y"])
            alpha = to_exact(reponse.get("alpha", 1))
            beta = to_exact(reponse.get("beta", 1))
            if len(x) != len(y) or len(x) < 2:
                return VerificationResult(
                    False,
                    "Les vecteurs x et y doivent avoir la même dimension (n >= 2).",
                )
            comb = alpha * x + beta * y
            # Test sur f(u) = max(u) - min(u) (amplitude / spread, VMLS ex. 2.2)
            def _spread(v: Vector) -> sp.Expr:
                return max(v.entries) - min(v.entries)

            lhs = _spread(comb)
            rhs = alpha * _spread(x) + beta * _spread(y)
            if oracle.decide(lhs - rhs).verdict != Verdict.ZERO:
                note = _simplicity_score([x, y])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! f(αx + βy) = {lhs} ≠ αf(x) + βf(y) = {rhs}. "
                    f"Note de simplicité : {note}.",
                    note_simplicite=note,
                )
            return VerificationResult(
                False,
                f"Sur votre instance, f(αx + βy) = {lhs} est égal à αf(x) + βf(y) = {rhs}. "
                "Choisissez deux vecteurs dont les maximums ne se trouvent pas à la même composante !",
            )

        if ce_kind == "ordre_gram_schmidt_5_2":
            # Exercice 5.2 : deux vecteurs a1, a2 tels que Gram-Schmidt sur (a1, a2) vs (a2, a1) donne des familles différentes
            if not isinstance(reponse, (tuple, list)) or len(reponse) != 2:
                return VerificationResult(
                    False,
                    "Fournissez un couple de deux vecteurs (a1, a2).",
                )
            a1 = reponse[0] if isinstance(reponse[0], Vector) else Vector(reponse[0])
            a2 = reponse[1] if isinstance(reponse[1], Vector) else Vector(reponse[1])
            if len(a1) != len(a2) or len(a1) < 2:
                return VerificationResult(
                    False,
                    "Les deux vecteurs a1 et a2 doivent être de même taille n >= 2.",
                )
            gs12 = GramSchmidt([a1, a2]).run()
            gs21 = GramSchmidt([a2, a1]).run()
            if not gs12.independent:  # type: ignore[union-attr]
                return VerificationResult(
                    False,
                    "Hypothèse non vérifiée : vos deux vecteurs a1 et a2 sont colinéaires (liés).",
                )
            q1, q2 = gs12.orthonormal  # type: ignore[union-attr]
            p1, p2 = gs21.orthonormal  # type: ignore[union-attr]
            same_set = (q1 == p1 and q2 == p2) or (q1 == p2 and q2 == p1)
            if not same_set:
                note = _simplicity_score([a1, a2])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! L'ordre (a1, a2) donne ({q1}, {q2}) tandis que (a2, a1) donne ({p1}, {p2}). "
                    f"Note de simplicité : {note}.",
                    note_simplicite=note,
                )
            return VerificationResult(
                False,
                "Sur votre exemple, les deux ordres produisent les mêmes vecteurs orthonormés (car a1 et a2 sont déjà orthogonaux). "
                "Choisissez deux vecteurs indépendants non orthogonaux !",
            )

        if ce_kind == "inverse_matrice_positive_11_12":
            # Exercice 11.12 : matrice carrée inversible à coefficients > 0 dont l'inverse n'est pas à coefficients > 0
            A = reponse if isinstance(reponse, Matrix) else Matrix(reponse)
            if A.rows != A.cols or A.rows < 2:
                return VerificationResult(
                    False,
                    "Fournissez une matrice carrée A de taille au moins 2×2.",
                )
            if any(e <= 0 for e in A.flat_entries):
                return VerificationResult(
                    False,
                    "Hypothèse non respectée : tous les coefficients de A doivent être strictement positifs (> 0).",
                )
            inv_a = A.inv(strict=False)
            if not isinstance(inv_a, Matrix):
                return VerificationResult(
                    False,
                    "Hypothèse non respectée : votre matrice A est singulière (non inversible).",
                )
            if any(e < 0 for e in inv_a.flat_entries):
                note = _simplicity_score([A])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! A est inversible à coefficients strictement positifs, "
                    f"et A⁻¹ = {inv_a} possède des coefficients négatifs. Note de simplicité : {note}.",
                    note_simplicite=note,
                )
            return VerificationResult(
                False,
                f"L'inverse de votre matrice A est {inv_a}, qui n'a aucun coefficient strictement négatif.",
            )

    return VerificationResult(False, f"Type de contre-exemple {ce_kind!r} non configuré.")


def verifier_egalites(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 8 : chaîne d'égalités vérifiée maillon par maillon sous les hypothèses (§7.6)."""
    if not isinstance(reponse, (list, tuple)) or len(reponse) < 2:
        return VerificationResult(
            False,
            "Fournissez une liste d'au moins deux expressions représentant les maillons successifs de votre chaîne d'égalités.",
        )

    # Environnement symbolique ou matriciel (ex. 20.8 pour les matrices par blocs)
    kind = str(spec.get("mode", "scalaire"))
    if kind == "blocs":
        A = Matrix([[1, 2], [3, 5]])
        B = Matrix([[2, -1], [0, 3]])
        C = Matrix([[4, 1], [-2, 2]])
        D = Matrix([[1, 3], [2, -1]])
        I = Matrix.identity(2)
        env = {"A": A, "B": B, "C": C, "D": D, "I": I, "block": Matrix.block}
        with suspend_tracing():
            vals = []
            for idx, step_expr in enumerate(reponse, start=1):
                try:
                    val = (
                        step_expr
                        if isinstance(step_expr, Matrix)
                        else eval(str(step_expr), {"__builtins__": {}}, env)  # noqa: S307
                    )
                    vals.append(val)
                except Exception as exc:
                    return VerificationResult(
                        False,
                        f"Erreur d'évaluation au maillon {idx} ({exc}).",
                    )
            for idx in range(len(vals) - 1):
                if vals[idx] != vals[idx + 1]:
                    return VerificationResult(
                        False,
                        f"Le maillon {idx + 1} -> {idx + 2} n'est pas valide : les deux expressions diffèrent.",
                    )
            return VerificationResult(
                True,
                f"Les {len(vals) - 1} égalités de votre chaîne sont vérifiées maillon par maillon !",
            )

    var_names = list(spec.get("variables", ["x", "y"]))
    local_syms = {v: symbols(v)[0] for v in var_names}
    subs_hyp: dict[sp.Symbol, sp.Expr] = {}
    for h_k, h_v in dict(spec.get("hypotheses_subs", {})).items():
        subs_hyp[local_syms.get(h_k, symbols(h_k)[0])] = sp.sympify(
            str(h_v), locals=local_syms
        )

    parsed_steps: list[sp.Expr] = []
    for idx, item in enumerate(reponse, start=1):
        try:
            expr = item if isinstance(item, sp.Expr) else sp.sympify(str(item), locals=local_syms)
            parsed_steps.append(expr.xreplace(subs_hyp))
        except Exception as exc:
            return VerificationResult(
                False,
                f"Impossible d'analyser le maillon {idx} : {item!r} ({exc}).",
            )

    for idx in range(len(parsed_steps) - 1):
        diff = sp.simplify(parsed_steps[idx] - parsed_steps[idx + 1])
        if oracle.decide(diff).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Égalité fausse entre le maillon {idx + 1} ({reponse[idx]}) et le maillon {idx + 2} ({reponse[idx + 1]}).",
            )

    return VerificationResult(
        True,
        f"Chaîne de {len(parsed_steps)} expressions algébriquement valide maillon par maillon !",
    )


def verifier_dimensions(
    reponse: Any,
    spec: Mapping[str, Any],
    donnees: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 9 : algèbre des tailles et validité de notations vectorielles/matricielles (§7.6)."""
    attendu = spec["attendu"]

    if isinstance(attendu, Mapping):
        if not isinstance(reponse, Mapping):
            return VerificationResult(
                False,
                f"Fournissez un dictionnaire pour les sous-questions {list(attendu.keys())} "
                "(ex. {'a': 'valide', 'b': 'invalide'} ou {'a': (m, n), 'b': 'invalide'}).",
            )
        wrong: list[str] = []
        for k, exp_val in attendu.items():
            if k not in reponse:
                wrong.append(f"sous-question ({k}) manquante")
                continue
            stu_val = reponse[k]
            if not _match_dim_answer(stu_val, exp_val):
                wrong.append(
                    f"({k}) : votre réponse {stu_val!r} est incorrecte (vérifiez la compatibilité des dimensions internes)"
                )
        if wrong:
            return VerificationResult(
                False,
                "Certaines réponses sont incorrectes : " + " ; ".join(wrong) + ".",
            )
        return VerificationResult(
            True,
            "Exact ! Toutes vos analyses de validité et de dimensions sont correctes.",
        )

    if _match_dim_answer(reponse, attendu):
        return VerificationResult(True, "Exact ! Votre analyse de la notation et des dimensions est correcte.")
    return VerificationResult(
        False,
        f"Votre réponse ({reponse!r}) est incorrecte. Rappellez-vous qu'un vecteur de R^n est une matrice n×1 : "
        "le produit u v sans transposition de u est invalide dès que n > 1.",
    )


def _match_dim_answer(student: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        expected = tuple(expected)
    if isinstance(student, list):
        student = tuple(student)
    if student == expected:
        return True
    s_str = str(student).strip().lower()
    e_str = str(expected).strip().lower()
    if s_str == e_str:
        return True
    if e_str == "invalide" and s_str in ("invalide", "invalid", "faux", "false", "none"):
        return True
    if e_str == "valide" and s_str in ("valide", "valid", "vrai", "true"):
        return True
    return False
