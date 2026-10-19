"""Validation d'opérations élémentaires proposées par l'élève et détection des erreurs de l'Annexe C (§5.6.3)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal

import sympy as sp

from linalg_pedagopy.core.field import to_exact
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing

ProposalStatus = Literal["invalid", "valid_no_progress", "valid_useful"]


@dataclass(frozen=True)
class OperationFeedback:
    """Retour détaillé du vérificateur d'opération (§5.6.3, Annexe C)."""

    status: ProposalStatus
    message: str
    new_matrix: Matrix | None = None
    error_code: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.status in ("valid_no_progress", "valid_useful")

    @property
    def is_useful(self) -> bool:
        return self.status == "valid_useful"

    def __str__(self) -> str:
        return self.message


_SWAP_RE = re.compile(
    r"^\s*L(\d+)\s*(?:<->|<=>|↔)\s*L(\d+)\s*$", re.IGNORECASE
)
_ASSIGN_RE = re.compile(
    r"^\s*(only_A\s*:\s*)?L(\d+)\s*(?:<-|←|=)\s*(.+?)\s*$", re.IGNORECASE
)


def check_row_operation(
    aug_matrix: Matrix,
    operation: str,
    *,
    num_lhs_cols: int | None = None,
    only_lhs: bool = False,
) -> OperationFeedback:
    """Analyse, valide et applique une opération élémentaire sur les lignes (Annexe C)."""
    m, total_cols = aug_matrix.shape
    n_cols = num_lhs_cols if num_lhs_cols is not None else total_cols

    # 1. Échange de deux lignes : Li <-> Lj
    m_swap = _SWAP_RE.match(operation)
    if m_swap:
        i = int(m_swap.group(1)) - 1
        j = int(m_swap.group(2)) - 1
        if not (0 <= i < m and 0 <= j < m):
            return OperationFeedback(
                status="invalid",
                message=f"Invalide : indice de ligne hors bornes (1..{m}).",
                error_code="index_out_of_bounds",
            )
        if i == j:
            return OperationFeedback(
                status="valid_no_progress",
                message=f"Valide mais sans progrès : échanger L{i + 1} avec elle-même ne modifie pas la matrice.",
                new_matrix=aug_matrix,
            )
        if only_lhs and total_cols > n_cols:
            return OperationFeedback(
                status="invalid",
                message="Invalide : opération appliquée à A mais pas au second membre. Le système obtenu n'est plus équivalent.",
                error_code="only_lhs",
            )
        rows = [list(r) for r in aug_matrix.entries_grid]
        rows[i], rows[j] = rows[j], rows[i]
        new_mat = Matrix._from_exact_rows(rows)
        return OperationFeedback(
            status="valid_useful",
            message=f"Valide. Les lignes L{i + 1} et L{j + 1} ont été échangées.",
            new_matrix=new_mat,
        )

    # 2. Affectation : Li <- expr
    m_assign = _ASSIGN_RE.match(operation)
    if not m_assign:
        return OperationFeedback(
            status="invalid",
            message=(
                f"Syntaxe d'opération non reconnue : {operation!r}. "
                "Exemples attendus : 'L2 <- L2 - 3*L1', 'L1 <-> L2', 'L2 <- (1/2)*L2'."
            ),
            error_code="syntax_error",
        )

    prefix_only_a = bool(m_assign.group(1)) or only_lhs
    target_i = int(m_assign.group(2)) - 1
    rhs_str = m_assign.group(3).strip()

    if not (0 <= target_i < m):
        return OperationFeedback(
            status="invalid",
            message=f"Invalide : la ligne L{target_i + 1} n'existe pas (1..{m}).",
            error_code="index_out_of_bounds",
        )

    if prefix_only_a and total_cols > n_cols:
        return OperationFeedback(
            status="invalid",
            message="Invalide : opération appliquée à A mais pas au second membre. Le système obtenu n'est plus équivalent.",
            error_code="only_lhs",
        )

    # Remplacement symbolique des L1..Lm par des symboles dédiés _ROW_0 .. _ROW_{m-1}
    row_syms = {k: sp.Symbol(f"_ROW_{k}", real=True) for k in range(m)}

    def _repl_row(match: re.Match[str]) -> str:
        idx = int(match.group(1)) - 1
        if not (0 <= idx < m):
            raise IndexError(f"Ligne L{idx + 1} hors bornes.")
        return f"_ROW_{idx}"

    try:
        rhs_rewritten = re.sub(r"\bL(\d+)\b", _repl_row, rhs_str, flags=re.IGNORECASE)
        local_dict: dict[str, Any] = {f"_ROW_{k}": row_syms[k] for k in range(m)}
        for sym in aug_matrix.to_sympy().free_symbols:
            if isinstance(sym, sp.Symbol):
                local_dict[sym.name] = sym
        parsed = sp.sympify(rhs_rewritten, locals=local_dict)
    except Exception as exc:
        return OperationFeedback(
            status="invalid",
            message=f"Invalide : impossible d'analyser l'opération ({exc}).",
            error_code="parse_error",
        )

    # Vérifier que parsed est une combinaison linéaire des _ROW_k (sans terme constant ni produit de lignes)
    poly_check = sp.expand(parsed)
    coeffs: dict[int, sp.Expr] = {}
    rem = poly_check
    for k, rsym in row_syms.items():
        c_k = sp.simplify(rem.coeff(rsym, 1))
        if c_k != 0:
            coeffs[k] = c_k
        rem = sp.simplify(rem - c_k * rsym)

    if rem != 0:
        return OperationFeedback(
            status="invalid",
            message="Invalide : l'expression n'est pas une opération linéaire sur les lignes.",
            error_code="nonlinear_row_op",
        )

    # Détection de transvection d'une ligne par elle-même : ex. "L2 <- L2 + lam*L2" ou "L2 <- L2 - L2"
    occurrences_target = len(
        re.findall(rf"\bL{target_i + 1}\b", rhs_str, flags=re.IGNORECASE)
    )
    other_rows = [k for k in coeffs if k != target_i]

    if occurrences_target >= 2 and not other_rows:
        c_self = coeffs.get(target_i, sp.Integer(0))
        lam = sp.simplify(c_self - 1)
        if oracle.decide(c_self).verdict == Verdict.ZERO:
            return OperationFeedback(
                status="invalid",
                message=(
                    f"Invalide : transvection d'une ligne par elle-même (L{target_i + 1} <- L{target_i + 1} + ({lam})*L{target_i + 1}). "
                    "C'est une dilatation déguisée, interdite si λ = -1 (annule la ligne)."
                ),
                error_code="self_transvection",
            )
        return OperationFeedback(
            status="valid_no_progress",
            message=(
                f"Attention : L{target_i + 1} <- L{target_i + 1} + ({lam})*L{target_i + 1} "
                f"est une dilatation déguisée par {c_self} (interdite si λ = -1)."
            ),
            error_code="self_transvection",
        )

    # Écrasement d'une ligne : L_i <- (combinaison des autres lignes) sans L_i
    if coeffs and target_i not in coeffs:
        autres = ", ".join(f"L{k + 1}" for k in sorted(other_rows))
        return OperationFeedback(
            status="invalid",
            message=(
                f"Invalide : L{target_i + 1} est remplacée par une expression qui ne la contient pas "
                f"({autres}). L'ancienne ligne L{target_i + 1} est perdue : l'opération n'est pas "
                f"inversible et le système change. Pour échanger deux lignes, écrivez "
                f"'L{target_i + 1} <-> L{sorted(other_rows)[0] + 1}' ; pour une transvection, conservez "
                f"L{target_i + 1} : 'L{target_i + 1} <- L{target_i + 1} + λ*L{sorted(other_rows)[0] + 1}'."
            ),
            error_code="row_overwrite",
        )

    # Cas d'une dilatation par 0 : L_i <- 0*L_i (aucune ligne présente dans coeffs)
    if not coeffs:
        return OperationFeedback(
            status="invalid",
            message=(
                "Invalide : une dilatation par 0 n'est pas une opération élémentaire "
                "(perte d'information) ; l'opération n'est pas inversible : le système change."
            ),
            error_code="zero_scaling",
        )

    if len(other_rows) > 1:
        return OperationFeedback(
            status="invalid",
            message="Invalide : une opération élémentaire ne fait intervenir qu'au plus deux lignes à la fois.",
            error_code="multiple_rows",
        )

    c_target = coeffs[target_i]
    dec_target = oracle.decide(c_target)
    if dec_target.verdict == Verdict.ZERO:
        return OperationFeedback(
            status="invalid",
            message="Invalide : une dilatation par 0 n'est pas une opération élémentaire (perte d'information).",
            error_code="zero_scaling",
        )

    # Détection de division/multiplication par une expression dépendant d'un paramètre (Annexe C)
    for c_val in coeffs.values():
        num_c, den_c = sp.fraction(sp.together(c_val))
        if num_c.free_symbols or den_c.free_symbols:
            cond_expr = den_c if den_c.free_symbols else num_c
            dec_param = oracle.decide(cond_expr)
            if dec_param.verdict == Verdict.CONDITIONAL and dec_param.condition is not None:
                return OperationFeedback(
                    status="invalid",
                    message=(
                        f"Attention : division ou dilatation par un pivot dépendant d'un paramètre "
                        f"sans discussion (condition d'annulation : {dec_param.condition}). "
                        "Séparez les cas avant de diviser."
                    ),
                    error_code="parameter_division_without_discussion",
                )

    # Cas 2a : Dilatation pure L_i <- c * L_i
    if not other_rows:
        rows = [list(r) for r in aug_matrix.entries_grid]
        old_row = rows[target_i]
        new_row = [sp.simplify(c_target * x) for x in old_row]
        rows[target_i] = new_row
        new_mat = Matrix._from_exact_rows(rows)

        # Est-ce que cette dilatation normalise le premier coefficient non nul à 1 ?
        first_nz_old = next(
            (x for x in old_row[:n_cols] if oracle.decide(x).verdict == Verdict.NONZERO),
            None,
        )
        if first_nz_old is not None and sp.simplify(c_target * first_nz_old) == 1 and c_target != 1:
            return OperationFeedback(
                status="valid_useful",
                message=f"Valide. Le pivot de la ligne L{target_i + 1} est maintenant normalisé à 1.",
                new_matrix=new_mat,
            )
        return OperationFeedback(
            status="valid_no_progress",
            message=f"Valide mais sans progrès direct : la ligne L{target_i + 1} a été multipliée par {c_target}.",
            new_matrix=new_mat,
        )

    # Cas 2b : Transvection L_i <- L_i + lam * L_j
    j = other_rows[0]
    lam = coeffs[j]
    rows = [list(r) for r in aug_matrix.entries_grid]
    old_i = rows[target_i]
    row_j = rows[j]
    new_i = [sp.simplify(c_target * old_i[c] + lam * row_j[c]) for c in range(total_cols)]
    rows[target_i] = new_i
    new_mat = Matrix._from_exact_rows(rows)

    # Trouver la colonne du premier coefficient non nul (pivot) de L_j
    pivot_col_j = next(
        (c for c in range(n_cols) if oracle.decide(row_j[c]).verdict == Verdict.NONZERO),
        None,
    )
    if pivot_col_j is not None:
        old_val = old_i[pivot_col_j]
        new_val = new_i[pivot_col_j]
        if oracle.decide(old_val).verdict == Verdict.NONZERO and oracle.decide(new_val).verdict == Verdict.ZERO:
            return OperationFeedback(
                status="valid_useful",
                message=(
                    f"Valide. Le coefficient ({target_i + 1},{pivot_col_j + 1}) est maintenant nul : "
                    "progression vers la forme échelonnée."
                ),
                new_matrix=new_mat,
            )
        # Détection d'erreur de signe dans le coefficient de transvection (Annexe C)
        expected_lam = sp.simplify(-c_target * old_val / row_j[pivot_col_j])
        if oracle.decide(lam + expected_lam).verdict == Verdict.ZERO and oracle.decide(old_val).verdict == Verdict.NONZERO:
            return OperationFeedback(
                status="valid_no_progress",
                message=(
                    f"Erreur de signe dans le coefficient de transvection : le coefficient ({target_i + 1},{pivot_col_j + 1}) "
                    f"vaut maintenant {new_val} et n'est pas annulé (coefficient attendu : {expected_lam})."
                ),
                new_matrix=new_mat,
                error_code="sign_error",
            )

    return OperationFeedback(
        status="valid_no_progress",
        message="Opération élémentaire valide, mais aucun nouveau zéro utile n'a été créé.",
        new_matrix=new_mat,
    )


def check_gram_schmidt_step(
    a_i: Vector,
    q_tildes_prev: list[Vector],
    proposed_vector: Vector,
    *,
    normalized_early: bool = False,
) -> OperationFeedback:
    """Vérifie une étape proposée pour Gram-Schmidt et détecte les erreurs de l'Annexe C."""
    if normalized_early:
        return OperationFeedback(
            status="invalid",
            message=(
                "Résultat non orthogonal : vous avez normalisé avant d'avoir soustrait "
                "toutes les projections. Rappel de l'ordre des étapes : soustraire toutes les projections "
                "sur q̃_1, ..., q̃_{i-1} avant de normaliser."
            ),
            error_code="early_normalization",
        )

    with suspend_tracing():
        # Calcul du vrai q_tilde_i
        expected = a_i
        unnormalized_attempt = a_i
        for q_j in q_tildes_prev:
            ip = q_j.dot(a_i)
            dsq = q_j.norm_sq()
            expected = expected - (ip / dsq) * q_j
            unnormalized_attempt = unnormalized_attempt - ip * q_j

        if proposed_vector == expected:
            return OperationFeedback(
                status="valid_useful",
                message="Valide. Le vecteur obtenu est bien orthogonal aux vecteurs précédents.",
            )

        # Vérifier si l'élève a oublié de diviser par q_tilde_j^T q_tilde_j (Annexe C)
        if proposed_vector == unnormalized_attempt and any(
            q_j.norm_sq() != 1 for q_j in q_tildes_prev
        ):
            residuals = [q_j.dot(proposed_vector) for q_j in q_tildes_prev]
            return OperationFeedback(
                status="invalid",
                message=(
                    "Projection sur un vecteur non normalisé sans diviser par q̃_j^T q̃_j : "
                    f"le vecteur obtenu n'est pas orthogonal (produit scalaire résiduel : {residuals[0]})."
                ),
                error_code="missing_norm_sq_division",
            )

        for idx, q_j in enumerate(q_tildes_prev, start=1):
            res_ip = q_j.dot(proposed_vector)
            if oracle.decide(res_ip).verdict != Verdict.ZERO:
                return OperationFeedback(
                    status="invalid",
                    message=(
                        f"Le vecteur obtenu n'est pas orthogonal à q̃_{idx} "
                        f"(produit scalaire résiduel : {res_ip} ≠ 0)."
                    ),
                    error_code="not_orthogonal",
                )

    return OperationFeedback(
        status="valid_useful",
        message="Vecteur orthogonal valide.",
    )
