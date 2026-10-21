"""Vérificateur « matrice » : matrice d'une application linéaire décrite par ses lignes."""

from __future__ import annotations

from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
    _format_linear_comb,
    _parse_indexed_expr,
    sans_seance,
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


register_verifier(
    VerifierType(
        "matrice",
        ("matrix",),
        sans_seance(verify_matrix),
        "une matrice, par exemple Matrix([[1, 0], [0, 1]]).",
        requires("cible|lignes_cibles", message="Le vérificateur 'matrice' requiert 'cible' ou 'lignes_cibles'."),
        _cross_check_matrix,
    )
)
