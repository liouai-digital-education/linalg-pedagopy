"""Produits et métriques matricielles tracés, délégués par ``Matrix`` (phase 5 du plan v6).

Règle de délégation : ``Matrix`` garde la représentation et les opérations algébriques ; toute
logique avec boucle, discussion de cas ou trace vit dans ``algorithms/``. Ce module porte le
produit matriciel tracé selon une vue (``Matrix.matmul``), la matrice de Gram
(``Matrix.gram``), le contrôle d'orthonormalité des colonnes
(``Matrix.has_orthonormal_columns``) et l'annonce des valeurs singulières avant une inversion
(``Matrix.inv``). Les clés de trace restent ``matrix.*``.
"""

from __future__ import annotations

from typing import cast

import sympy as sp
from sympy.polys.matrices import DomainMatrix

from linalg_pedagopy.algorithms.determinant import Determinant, DetResult
from linalg_pedagopy.core.cases import CaseSplit, Condition
from linalg_pedagopy.core.exceptions import DimensionMismatchError, SingularMatrixError
from linalg_pedagopy.core.field import choose_domain
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, decide_all_zero, oracle
from linalg_pedagopy.objects.matrix import Matrix, MatmulView, register_procedure
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing


def matmul(A: Matrix, other: Matrix | Vector, *, view: MatmulView = "entries") -> Matrix | Vector:
    """Produit matriciel A @ B ou A @ v tracé selon la vue choisie (voir ``Matrix.matmul``)."""
    is_vec = isinstance(other, Vector)
    rhs_mat = Matrix(other) if isinstance(other, Vector) else other
    if A.cols != rhs_mat.rows:
        raise DimensionMismatchError(
            f"Dimensions incompatibles pour le produit matriciel : "
            f"{A.shape} @ {rhs_mat.shape} ({A.cols} != {rhs_mat.rows})."
        )
    if view not in ("entries", "rows", "columns", "outer"):
        raise ValueError(f"Vue de produit matriciel inconnue : {view!r}")

    m, k_dim, p = A.rows, A.cols, rhs_mat.cols

    with section(
        f"matrix.matmul.{view}",
        level=1,
        snapshot={"A": A, "B": other},
        m=m,
        k=k_dim,
        p=p,
        view=view,
    ):
        # Calcul interne rapide via DomainMatrix
        with suspend_tracing():
            all_entries = (*A.flat_entries, *rhs_mat.flat_entries)
            dom = choose_domain(all_entries)
            dm_a = DomainMatrix(
                [[dom.from_sympy(e) for e in r] for r in A.entries_grid],
                (m, k_dim),
                dom,
            )
            dm_b = DomainMatrix(
                [[dom.from_sympy(e) for e in r] for r in rhs_mat.entries_grid],
                (k_dim, p),
                dom,
            )
            dm_res = dm_a.matmul(dm_b)
            sym_mat = dm_res.to_Matrix()
            res_rows = [
                [sp.simplify(sym_mat[i, j]) for j in range(p)] for i in range(m)
            ]
            res_mat = Matrix._from_exact_rows(res_rows)

        if view == "entries":
            for i in range(m):
                row_i = A.row(i)
                for j in range(p):
                    col_j = rhs_mat.col(j)
                    val = res_rows[i][j]
                    record(
                        StepKind.DOT,
                        "matrix.matmul_entry",
                        level=2,
                        i=i + 1,
                        j=j + 1,
                        row=row_i,
                        col=col_j,
                        value=val,
                    )
        elif view == "rows":
            b_rows = rhs_mat.rows_as_vectors()
            for i in range(m):
                coeffs = A.entries_grid[i]
                row_res = res_mat.row(i)
                record(
                    StepKind.INFO,
                    "matrix.matmul_row",
                    level=2,
                    i=i + 1,
                    coeffs=coeffs,
                    b_rows=b_rows,
                    row_result=row_res,
                )
        elif view == "columns":
            a_cols = A.columns()
            for j in range(p):
                col_coeffs = [rhs_mat.entries_grid[idx][j] for idx in range(k_dim)]
                col_res = res_mat.col(j)
                record(
                    StepKind.INFO,
                    "matrix.matmul_col",
                    level=2,
                    j=j + 1,
                    coeffs=tuple(col_coeffs),
                    a_cols=a_cols,
                    col_result=col_res,
                )
        elif view == "outer":
            for k_idx in range(k_dim):
                col_k = Matrix(A.col(k_idx))
                row_k = Matrix([rhs_mat.entries_grid[k_idx]])
                with suspend_tracing():
                    outer_k = col_k.matmul(row_k, view="entries")
                record(
                    StepKind.INFO,
                    "matrix.matmul_outer_term",
                    level=2,
                    k=k_idx + 1,
                    col=A.col(k_idx),
                    row=rhs_mat.row(k_idx),
                    outer=outer_k,
                )

        final_out: Matrix | Vector = res_mat.col(0) if is_vec else res_mat
        record(
            StepKind.RESULT,
            "matrix.matmul_result",
            level=1,
            snapshot={"result": final_out},
            result=final_out,
        )
        return final_out


def gram(A: Matrix) -> Matrix:
    """Matrice de Gram G = A^T A avec coefficient (i, j) = a_i^T a_j."""
    cols = A.columns()
    n = A.cols
    with section("matrix.gram", level=1, snapshot={"A": A}, n=n):
        grid = [[sp.Integer(0)] * n for _ in range(n)]
        for i in range(n):
            for j in range(i, n):
                with suspend_tracing():
                    ip = cols[i].dot(cols[j])
                grid[i][j] = ip
                grid[j][i] = ip
                record(
                    StepKind.DOT,
                    "matrix.gram_entry",
                    level=2,
                    i=i + 1,
                    j=j + 1,
                    col_i=cols[i],
                    col_j=cols[j],
                    value=ip,
                )
        res = Matrix._from_exact_rows(grid)
        record(
            StepKind.RESULT,
            "matrix.gram_result",
            level=1,
            snapshot={"result": res},
            result=res,
        )
        return res


def has_orthonormal_columns(A: Matrix, assumptions: AssumptionsType = None) -> bool | CaseSplit[bool]:
    """Vérifie A^T A = I_n via l'oracle de nullité."""
    with section("matrix.orthonormal_check", level=1, snapshot={"A": A}):
        with suspend_tracing():
            g = A.gram()
            ident = Matrix.identity(A.cols)
            diff = g - ident
        has_cond = False
        for i in range(A.cols):
            for j in range(A.cols):
                dec = oracle.decide(diff[i, j], assumptions=assumptions)
                record(
                    StepKind.CHECK,
                    "matrix.orthonormal_entry",
                    level=2,
                    i=i + 1,
                    j=j + 1,
                    value= g[i, j],
                    target=ident[i, j],
                    verdict=dec.verdict.name,
                )
                if dec.verdict == Verdict.NONZERO:
                    return False
                if dec.verdict == Verdict.CONDITIONAL:
                    has_cond = True
                elif dec.verdict == Verdict.UNKNOWN:
                    oracle.is_zero(diff[i, j], assumptions=assumptions)

        if not has_cond:
            return True
        return decide_all_zero(diff.flat_entries, assumptions)


def annoncer_cas_singuliers(A: Matrix, assumptions: AssumptionsType) -> None:
    """Lève SingularMatrixError, avec les valeurs singulières, si des paramètres peuvent annuler det A."""
    with suspend_tracing():
        # Bareiss n'ouvre jamais de discussion, et zeros() sans split renvoie un tuple de conditions
        res = cast(DetResult, Determinant(A, method="bareiss", assumptions=assumptions).run())
        cas = cast("tuple[Condition, ...]", res.zeros())
    if not cas:
        return
    if len(cas) == 1 and cas[0].is_trivial:
        raise SingularMatrixError(
            f"La matrice {A.rows}x{A.cols} n'est inversible pour aucune valeur des paramètres : "
            "son déterminant est identiquement nul."
        )
    valeurs = " ou ".join(c.format_text() for c in cas)
    raise SingularMatrixError(
        f"La matrice {A.rows}x{A.cols} n'est pas inversible pour toutes les valeurs des "
        f"paramètres : det A = {sp.sstr(res.value)} s'annule pour {valeurs}. Utilisez strict=False "
        "pour obtenir l'inverse avec la discussion de cas, ou précisez des hypothèses (assumptions=...)."
    )


register_procedure("matmul", matmul)
register_procedure("gram", gram)
register_procedure("orthonormal_check", has_orthonormal_columns)
register_procedure("singular_check", annoncer_cas_singuliers)
