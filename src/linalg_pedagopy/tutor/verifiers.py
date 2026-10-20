"""Les 9 vérificateurs spécialisés du tuteur."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

import sympy as sp

from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan
from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.algorithms.least_squares import LeastSquares
from linalg_pedagopy.algorithms.qr import QR
from linalg_pedagopy.algorithms.triangular import BackSubstitution, ForwardSubstitution
from linalg_pedagopy.core.field import symbols, to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing


def raison_illisible(texte: str, exc: BaseException | None = None) -> str:
    """Explique en français pourquoi une saisie ne peut pas être lue.

    Le message d'exception de SymPy ou de Python n'est jamais recopié : il est en
    anglais, peu lisible pour un étudiant et change d'une version à l'autre.
    """
    t = str(texte)
    if "\n" in t.strip() or re.search(r"[⎛-⎯─-╿]", t):
        return "écrivez la formule sur une seule ligne, en texte (pas une matrice ou une expression affichée)."
    if re.search(r"(?<![=!<>])=(?!=)", t):
        return "saisissez seulement l'expression, sans signe « = »."
    if t.count("(") != t.count(")") or t.count("[") != t.count("]"):
        return "les parenthèses ou les crochets ne sont pas équilibrés."
    if re.search(r"\d[A-Za-z_(]|\)\s*[(A-Za-z_\d]|[A-Za-z_]\w*\s+[A-Za-z_(]", t):
        return "chaque multiplication s'écrit avec * (par exemple 2*x ou (a + b)*c)."
    if isinstance(exc, NameError):
        nom = re.search(r"'(\w+)'", str(exc))
        return f"le nom « {nom.group(1)} » n'est pas connu ici." if nom else "un nom utilisé n'est pas connu ici."
    return "la syntaxe n'est pas valide (vérifiez les opérateurs : +, -, *, /, ** pour les puissances)."


class VerificationResult:
    """Result of a tutor verification with bilingual attribute support."""

    __slots__ = ("valid", "diagnostic", "simplicity_note")

    def __init__(
        self,
        valid: bool | None = None,
        diagnostic: str = "",
        simplicity_note: str | None = None,
        *,
        valide: bool | None = None,
        note_simplicite: str | None = None,
    ) -> None:
        v = valid if valid is not None else bool(valide)
        note = simplicity_note if simplicity_note is not None else note_simplicite
        object.__setattr__(self, "valid", bool(v))
        object.__setattr__(self, "diagnostic", str(diagnostic))
        object.__setattr__(self, "simplicity_note", note)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("VerificationResult est immuable.")

    @property
    def valide(self) -> bool:
        return self.valid

    @property
    def note_simplicite(self) -> str | None:
        return self.simplicity_note

    def __bool__(self) -> bool:
        return self.valid

    def __str__(self) -> str:
        return self.diagnostic

    def __repr__(self) -> str:
        return self.diagnostic

    def _repr_markdown_(self) -> str:
        if self.valid:
            box = (
                f"<div style='padding: 12px 16px; border-left: 4px solid #16a34a; "
                f"background-color: #f0fdf4; border-radius: 4px; color: #166534; margin: 12px 0;'>\n"
                f"<strong style='font-size: 1.05em;'>✓ Réponse validée</strong>\n\n"
                f"{self.diagnostic}\n"
                f"</div>"
            )
            if self.simplicity_note:
                box += f"\n\n> *Note de simplicité* : {self.simplicity_note}"
            return box
        else:
            return (
                f"<div style='padding: 12px 16px; border-left: 4px solid #dc2626; "
                f"background-color: #fef2f2; border-radius: 4px; color: #991b1b; margin: 12px 0;'>\n"
                f"<strong style='font-size: 1.05em;'>✗ Diagnostic d'erreur</strong>\n\n"
                f"{self.diagnostic}\n"
                f"</div>"
            )


def _format_linear_comb(coeffs: Sequence[sp.Expr], var_name: str) -> str:
    """Formats a linear combination sum_j coeffs[j] * var_{j+1} in readable form."""
    pos_unit_terms: list[str] = []
    neg_frac_groups: dict[sp.Expr, list[str]] = {}
    other_terms: list[tuple[sp.Expr, str]] = []

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
            other_terms.append((c, v_j))

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
    """Converts a 1-based indexed expression like 'p[4] - (p[1]+p[2]+p[3])/3' into a SymPy expression."""
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


def verify_inner_product(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 1: inner_product / produit_scalaire."""
    if not isinstance(response, Vector):
        try:
            response = Vector(response)
        except Exception:
            return VerificationResult(
                False,
                "Votre réponse doit être un vecteur (ex. Vector([...])).",
            )

    var_name = str(spec.get("inconnue", spec.get("unknown", "x")))
    n = int(spec.get("taille", spec.get("size", data.get("n", len(response)))))
    if len(response) != n:
        return VerificationResult(
            False,
            f"Taille incorrecte : votre vecteur est de taille {len(response)}, "
            f"alors que {var_name} est dans R^{n}.",
        )

    cible_str = str(spec.get("cible", spec.get("target")))
    target_expr, vec_syms = _parse_indexed_expr(cible_str, var_name, n, data)

    student_expr = sp.expand(
        sum((response[k] * vec_syms[k] for k in range(n)), sp.Integer(0))
    )
    student_fmt = _format_linear_comb(response.entries, var_name)

    diff = sp.simplify(student_expr - target_expr)
    if oracle.decide(diff).verdict == Verdict.ZERO:
        return VerificationResult(
            True,
            f"Exact ! Avec votre vecteur, a^T {var_name} = {student_fmt}.",
        )

    if oracle.decide(sp.simplify(student_expr + target_expr)).verdict == Verdict.ZERO:
        return VerificationResult(
            False,
            f"Avec votre vecteur, a^T {var_name} = {student_fmt} : c'est l'opposé de la quantité demandée (erreur de signe).",
        )

    if student_expr != 0 and target_expr != 0:
        ratio = sp.simplify(student_expr / target_expr)
        if not ratio.free_symbols and ratio != 1:
            return VerificationResult(
                False,
                f"Avec votre vecteur, a^T {var_name} = {student_fmt} : le résultat est proportionnel à la cible (facteur {ratio}). "
                "Vérifiez la normalisation !",
            )

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


def verify_matrix(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 2: matrix / matrice — shape check then row-by-row diagnostic."""
    expected_rhs = spec.get("second_membre", spec.get("rhs"))
    rhs_student: Vector | None = None
    if isinstance(response, tuple) and len(response) == 2:
        mat_in, rhs_in = response
        A = mat_in if isinstance(mat_in, Matrix) else Matrix(mat_in)
        rhs_student = rhs_in if isinstance(rhs_in, Vector) else Vector(rhs_in)
    elif isinstance(response, Mapping) and "A" in response:
        A = response["A"] if isinstance(response["A"], Matrix) else Matrix(response["A"])
        if "b" in response:
            rhs_student = response["b"] if isinstance(response["b"], Vector) else Vector(response["b"])
    else:
        try:
            A = response if isinstance(response, Matrix) else Matrix(response)
        except Exception:
            return VerificationResult(
                False,
                "Votre réponse doit être une Matrix (ou un couple (A, b) si un second membre est demandé).",
            )

    var_name = str(spec.get("inconnue", spec.get("unknown", "x")))
    out_name = str(spec.get("nom_sortie", spec.get("output_name", "d")))
    n = int(spec.get("taille_entree", spec.get("input_size", data.get("n", 6))))

    target_row_exprs: list[sp.Expr] = []
    vec_syms: list[sp.Symbol] = []
    target_lines_key = "lignes_cibles" if "lignes_cibles" in spec else ("target_rows" if "target_rows" in spec else None)
    if target_lines_key is not None:
        raw_lines = list(spec[target_lines_key])
        m = len(raw_lines)
        for line_s in raw_lines:
            rhs_part = line_s.split("=", 1)[1].strip() if "=" in line_s else line_s
            ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, data)
            target_row_exprs.append(ex_i)
    else:
        cible_str = str(spec.get("cible", spec.get("target")))
        if "=" in cible_str:
            lhs_part, rhs_part = cible_str.split("=", 1)
            lhs_part = lhs_part.strip()
            if "[" in lhs_part:
                out_name = lhs_part.split("[", 1)[0].strip()
        else:
            rhs_part = cible_str
        m = int(spec.get("taille_sortie", spec.get("output_size", data.get("m", 3))))
        for i_val in range(1, m + 1):
            local_d = dict(data)
            local_d["i"] = i_val
            ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, local_d)
            target_row_exprs.append(ex_i)

    if A.shape != (m, n):
        return VerificationResult(
            False,
            f"Taille incorrecte : votre matrice est de taille ({A.rows} x {A.cols}), "
            f"alors que l'entrée {var_name} est de taille {n} et la sortie {out_name} de taille {m}.",
        )

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


def verify_formula(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 3: symbolic formula in terms of parameters."""
    param_names = list(spec.get("parametres", spec.get("parameters", ["norm_u", "norm_v"])))
    param_syms = {name: symbols(name)[0] for name in param_names}
    local_env: dict[str, Any] = dict(param_syms)
    local_env.update({"sqrt": sp.sqrt, "Rational": sp.Rational})
    for k, v in data.items():
        if isinstance(v, (int, float, str)):
            local_env[k] = to_exact(v)

    cible_raw = spec.get("cible", spec.get("target"))
    if isinstance(cible_raw, Mapping):
        if not isinstance(response, Mapping):
            return VerificationResult(
                False,
                f"Attendu un dictionnaire de formules pour les clés {list(cible_raw.keys())}.",
            )
        for key, target_s in cible_raw.items():
            if key not in response:
                return VerificationResult(False, f"Formule manquante pour '{key}'.")
            sub_res = verify_formula(
                response[key],
                {"parametres": param_names, "cible": target_s},
                data,
            )
            if not sub_res.valid:
                return VerificationResult(False, f"Pour '{key}' : {sub_res.diagnostic}")
        return VerificationResult(True, "Toutes vos formules symboliques sont exactes !")

    variables = ", ".join(param_names)
    if not isinstance(response, (str, int, sp.Expr)):
        return VerificationResult(
            False,
            "Votre réponse n'a pas la forme attendue : une formule sous forme de chaîne, "
            f"écrite avec les variables {variables}.",
        )
    target_expr = sp.sympify(str(cible_raw), locals=local_env)
    try:
        student_expr = (
            response
            if isinstance(response, sp.Expr)
            else sp.sympify(str(response), locals=local_env)
        )
    except Exception as exc:
        return VerificationResult(
            False,
            f"Impossible de lire votre formule : {raison_illisible(str(response), exc)} "
            f"Utilisez les variables {variables}.",
        )

    diff = sp.simplify(student_expr - target_expr)
    if oracle.decide(diff).verdict == Verdict.ZERO:
        return VerificationResult(
            True,
            f"Formule exacte ({student_expr}) !",
        )

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
            "GaussJordan": GaussJordan,
            "QR": QR,
            "LeastSquares": LeastSquares,
            "BackSubstitution": BackSubstitution,
            "ForwardSubstitution": ForwardSubstitution,
        }
    )
    with suspend_tracing():
        return eval(expr_str, {"__builtins__": {}}, env)  # noqa: S307


def _detect_typical_value_error(
    student_val: sp.Expr,
    raw_data: Mapping[str, Any],
) -> str | None:
    """Détecteurs des erreurs typiques des étudiants."""
    vecs = {k: v for k, v in raw_data.items() if isinstance(v, Vector)}
    with suspend_tracing():
        for _name, v in vecs.items():
            # 1. ||x|| instead of rms(x)
            if oracle.decide(student_val - v.norm()).verdict == Verdict.ZERO:
                return (
                    "Votre valeur est la norme. Que faut-il encore faire pour "
                    "obtenir une moyenne quadratique ?"
                )
            # 2. Sample standard deviation with 1/(n - 1) instead of 1/n
            if len(v) > 1:
                std_n_minus_1 = v.demean().norm() / sp.sqrt(sp.Integer(len(v) - 1))
                if oracle.decide(student_val - std_n_minus_1).verdict == Verdict.ZERO:
                    return (
                        "Vous avez utilisé la convention statistique en n − 1. "
                        "Quelle est la définition de l'écart type utilisée dans ce cours (division par n) ?"
                    )

        vec_items = list(vecs.items())
        if len(vec_items) >= 2:
            (_, x), (_, y) = vec_items[0], vec_items[1]
            if len(x) == len(y):
                # 3. Squared distance ||x - y||^2
                dist_sq = (x - y).norm_sq()
                if oracle.decide(student_val - dist_sq).verdict == Verdict.ZERO:
                    return "Votre valeur est ||x − y||²."
                # 4. Cosine of angle between x and y instead of correlation
                if x.is_zero() is False and y.is_zero() is False:
                    cos_xy = x.dot(y) / (x.norm() * y.norm())
                    if oracle.decide(student_val - cos_xy).verdict == Verdict.ZERO:
                        return (
                            "Vous avez calculé le cosinus de l'angle entre x et y. "
                            "Sur quels vecteurs la corrélation se calcule-t-elle ?"
                        )
    return None


def _erreur_typique_declaree(
    valeur: sp.Expr,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> str | None:
    """Erreurs typiques propres à une fiche : ``erreurs: [{valeur: expr, diagnostic: msg}]``.

    Chaque ``valeur`` est une expression évaluée sur les données de la fiche (la valeur
    qu'obtient l'étudiant qui commet l'erreur) ; elle est testée avant les détecteurs génériques.
    """
    for erreur in spec.get("erreurs", ()) or ():
        try:
            fausse = to_exact(_eval_data_expr(str(erreur["valeur"]), data))
        except Exception:
            continue
        if oracle.decide(valeur - fausse).verdict == Verdict.ZERO:
            return str(erreur["diagnostic"])
    return None


def racines_reelles(expr: sp.Expr, inconnue: sp.Symbol) -> list[sp.Expr] | None:
    """Racines réelles exactes d'une expression en une inconnue, ou None si l'ensemble n'est pas fini."""
    solutions = sp.solveset(sp.together(expr), inconnue, domain=sp.S.Reals)
    if solutions is sp.S.EmptySet:
        return []
    if not isinstance(solutions, sp.FiniteSet):
        return None
    return sorted((sp.nsimplify(s) if s.is_Float else s for s in solutions), key=lambda s: float(s.evalf()))


def verify_value_set(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Vérificateur 10 : ensemble des valeurs d'un paramètre qui annulent une expression (par exemple det A)."""
    nom = str(spec.get("inconnue", spec.get("unknown", "a")))
    param = symbols(nom)[0]
    quoi = str(spec.get("expression", "l'expression"))
    expr = sp.sympify(_eval_data_expr(str(spec.get("calcul", spec.get("compute"))), data))
    attendues = racines_reelles(expr, param)
    if attendues is None:
        return VerificationResult(False, f"Vérification impossible : {quoi} ne s'annule pas en un nombre fini de valeurs.")

    if isinstance(response, Mapping):
        return VerificationResult(False, "Attendu une liste de valeurs, par exemple [1, -2].")
    elements = list(response) if isinstance(response, (list, tuple, set, frozenset)) else [response]
    valeurs: list[sp.Expr] = []
    for element in elements:
        try:
            v = to_exact(element)
        except Exception:
            return VerificationResult(False, "Attendu une liste de valeurs exactes, par exemple [1, -2].")
        if isinstance(v, sp.Basic) and v.free_symbols:
            return VerificationResult(
                False,
                f"Vous avez donné une expression en {nom} : il reste à trouver les valeurs de {nom} qui annulent {quoi}.",
            )
        valeurs.append(v)

    with suspend_tracing():
        for v in valeurs:
            en_v = sp.simplify(expr.subs(param, v))
            if oracle.decide(en_v).verdict != Verdict.ZERO:
                return VerificationResult(
                    False,
                    f"Pour {nom} = {v}, {quoi} vaut {en_v} ≠ 0 : cette valeur ne convient pas.",
                )
        manquantes = [
            e for e in attendues if not any(oracle.decide(v - e).verdict == Verdict.ZERO for v in valeurs)
        ]
    if manquantes and not valeurs:
        return VerificationResult(
            False,
            f"Votre liste est vide, or {quoi} s'annule pour certaines valeurs de {nom}. "
            f"Cherchez les valeurs de {nom} qui annulent {quoi}.",
        )
    if manquantes:
        return VerificationResult(
            False,
            f"Vos valeurs annulent bien {quoi}, mais il en manque {len(manquantes)} (sur {len(attendues)}). "
            f"Avez-vous factorisé complètement {quoi} ?",
        )
    ensemble = "{" + ", ".join(str(e) for e in attendues) + "}" if attendues else "∅"
    return VerificationResult(True, f"Exact : {quoi} s'annule exactement pour {nom} ∈ {ensemble}.")


def verify_value(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 4: exact value computed on the fly + typical error detectors."""
    calcul_spec = spec.get("calcul", spec.get("compute"))

    if isinstance(calcul_spec, Mapping):
        if not isinstance(response, Mapping):
            try:
                stu_scalar = to_exact(response)
                err_msg = _detect_typical_value_error(stu_scalar, data)
                if err_msg is not None:
                    return VerificationResult(False, err_msg)
            except Exception:
                pass
            primary_expr = spec.get("calcul_principal")
            if primary_expr:
                return verify_value(response, {"calcul": primary_expr}, data)
            return VerificationResult(
                False,
                f"Attendu un dictionnaire de réponses pour les clés {list(calcul_spec.keys())}.",
            )

        for key, expr_s in calcul_spec.items():
            if key not in response:
                return VerificationResult(False, f"Clé '{key}' manquante dans votre réponse.")
            sub_res = verify_value(response[key], {"calcul": expr_s}, data)
            if not sub_res.valid:
                return VerificationResult(False, f"Pour '{key}' : {sub_res.diagnostic}")
        return VerificationResult(True, "Toutes vos valeurs sont exactes !")

    expected = _eval_data_expr(str(calcul_spec), data)

    if isinstance(expected, Vector):
        try:
            stu_vec = response if isinstance(response, Vector) else Vector(response)
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
            stu_mat = response if isinstance(response, Matrix) else Matrix(response)
        except Exception:
            return VerificationResult(False, "Votre réponse doit être une matrice.")
        if stu_mat == expected:
            return VerificationResult(True, "Exact ! Votre matrice est correcte.")
        return VerificationResult(False, "Votre matrice ne correspond pas au résultat attendu.")

    if isinstance(expected, bool):
        if bool(response) is expected:
            return VerificationResult(True, "Exact !")
        return VerificationResult(False, "Ce n'est pas la bonne conclusion.")

    try:
        stu_val = to_exact(response)
        exp_val = to_exact(expected)
    except Exception:
        return VerificationResult(False, f"Réponse scalaire exacte attendue (reçu {response!r}).")

    if oracle.decide(stu_val - exp_val).verdict == Verdict.ZERO:
        return VerificationResult(True, "Exact ! Votre valeur est correcte.")

    declaree = _erreur_typique_declaree(stu_val, spec, data)
    if declaree is not None:
        return VerificationResult(False, declaree)

    typical = _detect_typical_value_error(stu_val, data)
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


def verify_property(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 5: verification by defining mathematical property without storing an answer key."""
    prop_kind = str(spec.get("propriete", spec.get("property", "right_inverse")))

    with suspend_tracing():
        if prop_kind == "two_right_inverses":
            A = data["A"]
            if not isinstance(response, (tuple, list)) or len(response) != 2:
                return VerificationResult(
                    False,
                    "Fournissez un couple (B1, B2) de deux matrices inverses à droite distinctes.",
                )
            try:
                B1 = response[0] if isinstance(response[0], Matrix) else Matrix(response[0])
                B2 = response[1] if isinstance(response[1], Matrix) else Matrix(response[1])
            except Exception:
                return VerificationResult(
                    False,
                    "B1 et B2 doivent être deux matrices valides.",
                )
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
            A = data["A"]
            try:
                B = response if isinstance(response, Matrix) else Matrix(response)
            except Exception:
                return VerificationResult(False, "Votre réponse doit être une matrice colonne B.")
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
            A = data["A"]
            b = data["b"]
            try:
                c_vec = response if isinstance(response, Vector) else Vector(response)
            except Exception:
                return VerificationResult(False, "Votre réponse doit être un vecteur.")
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
            A = data["A"]
            B_inv = A.inv(strict=True)
            assert isinstance(B_inv, Matrix)
            if isinstance(response, str):
                cleaned = response.replace(" ", "")
                if cleaned in ("B@B", "B**2", "B^2", "(A^-1)^2", "A^-2"):
                    return VerificationResult(
                        True,
                        "Exact ! Comme A² B² = A (A B) B = A I B = A B = I, l'inverse de A² est B² = (A⁻¹)².",
                    )
            try:
                mat_stu = response if isinstance(response, Matrix) else Matrix(response)
            except Exception:
                return VerificationResult(False, "Fournissez la formule ('B^2') ou la matrice inverse de A².")
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
            C = data["C"]
            d = data["d"]
            try:
                x_stu = response if isinstance(response, Vector) else Vector(response)
            except Exception:
                return VerificationResult(False, "Votre réponse doit être un vecteur x.")
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


def verify_counterexample(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 6: counterexample validation and simplicity note."""
    ce_kind = str(spec.get("cas", spec.get("case", "")))

    with suspend_tracing():
        if ce_kind == "non_linearite_etendue":
            if not isinstance(response, Mapping) or "x" not in response or "y" not in response:
                return VerificationResult(
                    False,
                    "Fournissez un dictionnaire {'x': Vector([...]), 'y': Vector([...]), 'alpha': ..., 'beta': ...}.",
                )
            x = response["x"] if isinstance(response["x"], Vector) else Vector(response["x"])
            y = response["y"] if isinstance(response["y"], Vector) else Vector(response["y"])
            alpha = to_exact(response.get("alpha", 1))
            beta = to_exact(response.get("beta", 1))
            if len(x) != len(y) or len(x) < 2:
                return VerificationResult(
                    False,
                    "Les vecteurs x et y doivent avoir la même dimension (n >= 2).",
                )
            comb = alpha * x + beta * y

            def _spread(v: Vector) -> sp.Expr:
                return max(v.entries) - min(v.entries)

            def _max_entry(v: Vector) -> sp.Expr:
                return max(v.entries)

            lhs_spread = _spread(comb)
            rhs_spread = alpha * _spread(x) + beta * _spread(y)
            lhs_max = _max_entry(comb)
            rhs_max = alpha * _max_entry(x) + beta * _max_entry(y)
            if (
                oracle.decide(lhs_spread - rhs_spread).verdict != Verdict.ZERO
                or oracle.decide(lhs_max - rhs_max).verdict != Verdict.ZERO
            ):
                note = _simplicity_score([x, y])
                return VerificationResult(
                    True,
                    f"Contre-exemple valide ! f(αx + βy) ≠ αf(x) + βf(y). "
                    f"Note de simplicité : {note}.",
                    simplicity_note=note,
                )
            return VerificationResult(
                False,
                f"Sur votre instance, f(αx + βy) = {lhs_spread} est égal à αf(x) + βf(y) = {rhs_spread}. "
                "Choisissez deux vecteurs dont les maximums ne se trouvent pas à la même composante !",
            )

        if ce_kind == "ordre_gram_schmidt":
            if not isinstance(response, (tuple, list)) or len(response) != 2:
                return VerificationResult(
                    False,
                    "Fournissez un couple de deux vecteurs (a1, a2).",
                )
            try:
                a1 = response[0] if isinstance(response[0], Vector) else Vector(response[0])
                a2 = response[1] if isinstance(response[1], Vector) else Vector(response[1])
            except Exception:
                return VerificationResult(False, "Fournissez un couple de deux vecteurs (a1, a2).")
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
                    simplicity_note=note,
                )
            return VerificationResult(
                False,
                "Sur votre exemple, les deux ordres produisent les mêmes vecteurs orthonormés (car a1 et a2 sont déjà orthogonaux). "
                "Choisissez deux vecteurs indépendants non orthogonaux !",
            )

        if ce_kind == "inverse_matrice_positive":
            try:
                A = response if isinstance(response, Matrix) else Matrix(response)
            except Exception:
                return VerificationResult(False, "Fournissez une matrice carrée A.")
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
                    simplicity_note=note,
                )
            return VerificationResult(
                False,
                f"L'inverse de votre matrice A est {inv_a}, qui n'a aucun coefficient strictement négatif.",
            )

    return VerificationResult(False, f"Type de contre-exemple {ce_kind!r} non configuré.")


def verify_equalities(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 8: equality chain verified link by link with anti-triviality and endpoint checks."""
    if not isinstance(response, (list, tuple)) or len(response) < 2:
        return VerificationResult(
            False,
            "Fournissez une liste d'au moins deux expressions représentant les maillons successifs de votre chaîne d'égalités.",
        )

    # Anti-triviality: reject identical consecutive steps (e.g. ["0", "0"] or ["I", "I"])
    for idx in range(len(response) - 1):
        s1 = str(response[idx]).replace(" ", "")
        s2 = str(response[idx + 1]).replace(" ", "")
        if s1 == s2:
            return VerificationResult(
                False,
                f"Maillon trivial refusé : les maillons {idx + 1} et {idx + 2} sont identiques ({response[idx]!r}).",
            )

    kind = str(spec.get("mode", "scalaire"))
    if kind == "blocs":
        A = Matrix([[1, 2], [3, 5]])
        B = Matrix([[2, -1], [0, 3]])
        C = Matrix([[4, 1], [-2, 2]])
        D = Matrix([[1, 3], [2, -1]])
        I = Matrix.identity(2)
        env = {"A": A, "B": B, "C": C, "D": D, "I": I, "block": Matrix.block}
        with suspend_tracing():
            vals: list[Matrix] = []
            for idx, step_expr in enumerate(response, start=1):
                try:
                    val = (
                        step_expr
                        if isinstance(step_expr, Matrix)
                        else eval(str(step_expr), {"__builtins__": {}}, env)  # noqa: S307
                    )
                    if not isinstance(val, Matrix):
                        return VerificationResult(
                            False,
                            f"Le maillon {idx} ne produit pas une matrice par blocs valide.",
                        )
                    vals.append(val)
                except Exception as exc:
                    return VerificationResult(
                        False,
                        f"Impossible de calculer le maillon {idx} : {raison_illisible(str(step_expr), exc)} "
                        "Utilisez A, B, C, D, I, block([[…], […]]) et les opérations +, -, @.",
                    )

            target_block = Matrix.block([[A, B], [C, D]])
            if vals[0] != target_block or vals[-1] != target_block:
                return VerificationResult(
                    False,
                    "Votre chaîne doit partir du produit par blocs [[A, B], [C, D]] @ [[I, 0], [0, I]] "
                    "et aboutir à [[A, B], [C, D]].",
                )
            first_str = str(response[0]).replace(" ", "")
            if "@" not in first_str:
                return VerificationResult(
                    False,
                    "Le premier maillon doit exprimer le produit matriciel par blocs avec '@'.",
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

    raw_steps: list[sp.Expr] = []
    parsed_steps: list[sp.Expr] = []
    for idx, item in enumerate(response, start=1):
        try:
            expr = item if isinstance(item, sp.Expr) else sp.sympify(str(item), locals=local_syms)
            raw_steps.append(expr)
            parsed_steps.append(expr.xreplace(subs_hyp))
        except Exception as exc:
            return VerificationResult(
                False,
                f"Impossible de lire le maillon {idx} ({item!r}) : {raison_illisible(str(item), exc)}",
            )

    # Check start/end endpoints if specified or prevent constant-only trivial chains
    start_spec = spec.get("depart", spec.get("start"))
    end_spec = spec.get("arrivee", spec.get("end"))
    if start_spec is not None:
        start_expr = sp.sympify(str(start_spec), locals=local_syms)
        if oracle.decide(sp.simplify(raw_steps[0] - start_expr)).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Le premier maillon ({response[0]}) ne correspond pas au membre de départ attendu ({start_spec}).",
            )
    elif subs_hyp and not raw_steps[0].free_symbols:
        return VerificationResult(
            False,
            "Le premier maillon de votre chaîne doit faire intervenir les variables de l'énoncé avant substitution des hypothèses.",
        )

    if end_spec is not None:
        end_expr = sp.sympify(str(end_spec), locals=local_syms).xreplace(subs_hyp)
        if oracle.decide(sp.simplify(parsed_steps[-1] - end_expr)).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Le dernier maillon ({response[-1]}) n'aboutit pas au résultat attendu ({end_spec}).",
            )

    for idx in range(len(parsed_steps) - 1):
        diff = sp.simplify(parsed_steps[idx] - parsed_steps[idx + 1])
        if oracle.decide(diff).verdict != Verdict.ZERO:
            return VerificationResult(
                False,
                f"Égalité fausse entre le maillon {idx + 1} ({response[idx]}) et le maillon {idx + 2} ({response[idx + 1]}).",
            )

    return VerificationResult(
        True,
        f"Chaîne de {len(parsed_steps)} expressions algébriquement valide maillon par maillon !",
    )


def verify_dimensions(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Verifier 9: dimension algebra and validity of vector/matrix notations."""
    attendu = spec.get("attendu", spec.get("expected"))

    if isinstance(attendu, Mapping):
        if not isinstance(response, Mapping):
            return VerificationResult(
                False,
                f"Fournissez un dictionnaire pour les sous-questions {list(attendu.keys())} "
                "(ex. {'a': 'valide', 'b': 'invalide'} ou {'a': (m, n), 'b': 'invalide'}).",
            )
        wrong: list[str] = []
        for k, exp_val in attendu.items():
            if k not in response:
                wrong.append(f"sous-question ({k}) manquante")
                continue
            stu_val = response[k]
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

    if _match_dim_answer(response, attendu):
        return VerificationResult(True, "Exact ! Votre analyse de la notation et des dimensions est correcte.")
    return VerificationResult(
        False,
        f"Votre réponse ({response!r}) est incorrecte. Rappelez-vous qu'un vecteur de R^n est une matrice n×1 : "
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
    if e_str in ("invalide", "invalid") and s_str in ("invalide", "invalid", "non valide", "non défini", "non definie", "indéfini"):
        return True
    if e_str in ("valide", "valid") and s_str in ("valide", "valid", "vrai", "true"):
        return True
    return False


# French backward-compatible aliases
verifier_produit_scalaire = verify_inner_product
verifier_matrice = verify_matrix
verifier_formule = verify_formula
verifier_valeur = verify_value
verifier_ensemble_valeurs = verify_value_set
verifier_propriete = verify_property
verifier_contre_exemple = verify_counterexample
verifier_egalites = verify_equalities
verifier_dimensions = verify_dimensions
