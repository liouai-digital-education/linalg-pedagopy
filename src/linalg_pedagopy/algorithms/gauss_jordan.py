"""Élimination de Gauss-Jordan complète avec discussion par cas et choix du pivot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

import sympy as sp

from linalg_pedagopy.algorithms.base import (
    AffineSolution,
    EmptySolution,
    Procedure,
    Result,
    SolutionSet,
    UniqueSolution,
)
from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    PedagopyError,
    SingularMatrixError,
)
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle, _normalize_assumptions
from linalg_pedagopy.objects.matrix import Matrix, register_gauss_jordan_hook
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.text import format_value_text
from linalg_pedagopy.trace.step import Highlight, Step, StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing, tracing

PivotStrategy = Literal["simplest", "first", "partial"]


def _simplify_entry(expr: sp.Expr) -> sp.Expr:
    """Simplifie une entrée sous forme de fraction rationnelle canonique lisible."""
    if expr.is_Rational:
        return expr
    if expr.free_symbols and expr.is_rational_function(*expr.free_symbols):
        num, den = sp.fraction(sp.together(sp.cancel(expr)))
        if den != 1:
            return sp.Mul(sp.factor(num), 1 / sp.factor(den), evaluate=True)
        return sp.expand(num)
    return sp.simplify(expr)


def _pivot_complexity_key(val: sp.Expr) -> tuple[int, int | float, int]:
    """Critère d'ordre D11 : ±1, entier de plus petite valeur absolue, rationnel de petite hauteur, expression courte."""
    if val == 1:
        return (0, 0, 1)
    if val == -1:
        return (0, 1, 2)
    if val.is_Integer:
        return (1, abs(int(val)), len(str(val)))
    if val.is_Rational:
        p, q = abs(int(val.p)), abs(int(val.q))
        return (2, max(p, q), p + q)
    if not val.free_symbols:
        return (3, len(str(val)), 0)
    return (4, len(str(val)), len(val.free_symbols))


@dataclass(frozen=True)
class GJResult(Result):
    """Résultat typé de la réduction de Gauss-Jordan."""

    A: Matrix = Matrix([])
    b: Vector | Matrix | None = None
    rref: Matrix = Matrix([])
    augmented_rref: Matrix = Matrix([])
    pivots: tuple[int, ...] = ()
    rank: int = 0
    free_vars: tuple[int, ...] = ()
    nullspace_basis: tuple[Vector, ...] = ()
    solution: SolutionSet | None = None
    inverse: Matrix | None = None

    def subs(self, mapping: Mapping[Any, Any]) -> GJResult:
        return GJResult(
            trace=self.trace,
            A=self.A.subs(mapping),
            b=self.b.subs(mapping) if self.b is not None else None,
            rref=self.rref.subs(mapping),
            augmented_rref=self.augmented_rref.subs(mapping),
            pivots=self.pivots,
            rank=self.rank,
            free_vars=self.free_vars,
            nullspace_basis=tuple(v.subs(mapping) for v in self.nullspace_basis),
            solution=self.solution.subs(mapping) if self.solution is not None else None,
            inverse=self.inverse.subs(mapping) if self.inverse is not None else None,
        )

    def _branch_summary_lines(self) -> list[str]:
        """Résumé concis pour le rendu d'une branche de CaseSplit."""
        if isinstance(self.solution, UniqueSolution):
            return [
                f"pivots non nuls, rang {self.rank}, solution unique",
                f"x = {format_value_text(self.solution.x)}",
            ]
        if isinstance(self.solution, EmptySolution):
            inc_rows = self.solution.inconsistent_rows
            n = self.A.cols
            zeros_str = " ".join("0" for _ in range(n))
            if len(inc_rows) >= 2:
                r_names = " et ".join(f"L{r + 1}" for r, _w in inc_rows)
                r_vals = " et ".join(f"({zeros_str} | {w})" for _r, w in inc_rows)
                line1 = f"{r_names} deviennent {r_vals}"
            elif len(inc_rows) == 1:
                r0, w0 = inc_rows[0]
                line1 = f"L{r0 + 1} devient ({zeros_str} | {w0})"
            else:
                line1 = f"L{self.solution.row + 1} devient ({zeros_str} | {self.solution.witness})"
            return [
                line1,
                f"système incompatible (témoin : 0 = {self.solution.witness})",
            ]
        if isinstance(self.solution, AffineSolution):
            return [
                f"rang {self.rank}, infinité de solutions ({len(self.free_vars)} variable(s) libre(s))",
                f"x = {self.solution}",
            ]
        if self.inverse is not None:
            return [f"matrice inversible de rang {self.rank}"]
        return [
            f"rang {self.rank}, colonnes pivots {[p + 1 for p in self.pivots]}"
        ]

    def _run_verification(self) -> None:
        with section("gj.verify", level=1):
            # 1. Vérifier que les vecteurs de base du noyau annulent A
            with suspend_tracing():
                for idx, v in enumerate(self.nullspace_basis, start=1):
                    prod = self.A @ v
                    is_z = prod.is_zero()
                    record(
                        StepKind.CHECK,
                        "gj.verify_ok",
                        level=2,
                        detail=f"A · v_{idx} = 0 ({is_z})",
                    )
            # 2. Si solution unique ou affine, vérifier A x = b
            if isinstance(self.solution, UniqueSolution):
                with suspend_tracing():
                    diff = (self.A @ self.solution.x) - self.b  # type: ignore[operator]
                record(
                    StepKind.CHECK,
                    "gj.verify_ok",
                    level=1,
                    detail=f"A x - b = {diff}",
                )
            elif isinstance(self.solution, AffineSolution) and isinstance(self.b, Vector):
                with suspend_tracing():
                    diff0 = (self.A @ self.solution.x0) - self.b
                record(
                    StepKind.CHECK,
                    "gj.verify_ok",
                    level=1,
                    detail=f"A x_0 - b = {diff0}",
                )
            elif self.inverse is not None:
                with suspend_tracing():
                    prod_inv = (self.A @ self.inverse) - Matrix.identity(self.A.rows)
                record(
                    StepKind.CHECK,
                    "gj.verify_ok",
                    level=1,
                    detail=f"A · A^(-1) - I = {prod_inv}",
                )
            else:
                record(
                    StepKind.CHECK,
                    "gj.verify_ok",
                    level=1,
                    detail=f"Forme échelonnée réduite de rang {self.rank}",
                )


class GaussJordan(Procedure[GJResult]):
    """Procédure d'élimination de Gauss-Jordan."""

    def __init__(
        self,
        A: Matrix,
        b: Vector | Matrix | None = None,
        *,
        pivot_strategy: PivotStrategy = "simplest",
        strict: bool = False,
        max_depth: int | None = None,
        max_cases: int | None = None,
        assumptions: AssumptionsType = None,
        compute_inverse: bool = False,
    ) -> None:
        if not isinstance(A, Matrix):
            A = Matrix(A)
        if b is not None and not isinstance(b, (Vector, Matrix)):
            b = Vector(b)
        if b is not None and A.rows != b.rows:
            raise DimensionMismatchError(
                f"Le nombre de lignes de A ({A.rows}) diffère de celui du second membre ({b.rows})."
            )
        if pivot_strategy not in ("simplest", "first", "partial"):
            raise ValueError(f"Stratégie de pivot inconnue : {pivot_strategy!r}")

        self.A = A
        self.b = b
        self.pivot_strategy: PivotStrategy = pivot_strategy
        self.strict = strict
        self.max_depth = max_depth if max_depth is not None else config.max_case_depth
        self.max_cases = max_cases if max_cases is not None else config.max_cases
        self.assumptions = _normalize_assumptions(assumptions)
        self.compute_inverse = compute_inverse or (
            isinstance(b, Matrix) and A.rows == A.cols and b == Matrix.identity(A.rows)
        )
        if compute_inverse and b is None and A.rows == A.cols:
            # Sans second membre, l'inverse se calcule en réduisant [A | I_n].
            self.b = Matrix.identity(A.rows)

    def _execute(self) -> GJResult | CaseSplit[GJResult]:
        state = {"cases_count": 1}
        return self._solve_under_condition(self.A, self.b, self.assumptions, depth=0, state=state)

    def _solve_under_condition(
        self,
        A_in: Matrix,
        b_in: Vector | Matrix | None,
        cond: Condition,
        *,
        depth: int,
        state: dict[str, int],
    ) -> GJResult | CaseSplit[GJResult]:
        subs_map = cond.substitutions()
        A_cur = A_in.subs(subs_map) if subs_map else A_in
        b_cur = b_in.subs(subs_map) if (b_in is not None and subs_map) else b_in

        m, n = A_cur.shape
        aug = A_cur.augment(b_cur) if b_cur is not None else A_cur
        total_cols = aug.cols
        split_col = n if b_cur is not None else None

        grid: list[list[sp.Expr]] = [
            [_simplify_entry(aug[i, j]) for j in range(total_cols)] for i in range(m)
        ]

        pivots: list[int] = []
        pivot_row = 0

        with section(
            "gj.start",
            level=1,
            snapshot={"augmented_matrix": Matrix._from_exact_rows(grid)},
            highlight=Highlight(augmented_split=split_col),
            m=m,
            n=n,
        ):
            for col in range(n):
                if pivot_row >= m:
                    break

                # Analyse des candidats dans la colonne `col` pour r >= pivot_row
                nonzero_cands: list[tuple[int, sp.Expr]] = []
                cond_cands: list[tuple[int, sp.Expr, tuple[sp.Expr, ...]]] = []
                unknown_cands: list[tuple[int, sp.Expr]] = []

                for r in range(pivot_row, m):
                    val = _simplify_entry(grid[r][col])
                    grid[r][col] = val
                    dec = oracle.decide(val, assumptions=cond)
                    if dec.verdict == Verdict.NONZERO:
                        nonzero_cands.append((r, val))
                    elif dec.verdict == Verdict.CONDITIONAL:
                        cond_cands.append((r, val, dec.factors))
                    elif dec.verdict == Verdict.UNKNOWN:
                        unknown_cands.append((r, val))

                # S'il n'y a aucun candidat inconditionnellement non nul mais un candidat conditionnel -> CaseSplit
                if not nonzero_cands and cond_cands:
                    cand_r, cand_val, cand_factors = min(
                        cond_cands, key=lambda item: _pivot_complexity_key(item[1])
                    )
                    return self._split_on_factors(
                        A_in,
                        b_in,
                        cond,
                        factors=cand_factors,
                        row=cand_r,
                        col=col,
                        expr=cand_val,
                        depth=depth,
                        state=state,
                    )

                if not nonzero_cands and not cond_cands and unknown_cands:
                    oracle.is_zero(unknown_cands[0][1], assumptions=cond)

                if not nonzero_cands:
                    record(
                        StepKind.INFO,
                        "gj.col_zero",
                        level=2,
                        col=col + 1,
                    )
                    continue

                # Choix du pivot selon pivot_strategy
                if self.pivot_strategy == "simplest":
                    chosen_r, chosen_val = min(
                        nonzero_cands, key=lambda item: _pivot_complexity_key(item[1])
                    )
                elif self.pivot_strategy == "partial":
                    def _abs_eval(item: tuple[int, sp.Expr]) -> float:
                        try:
                            return float(abs(item[1].evalf()))
                        except Exception:
                            return 0.0
                    chosen_r, chosen_val = max(nonzero_cands, key=_abs_eval)
                else:
                    chosen_r, chosen_val = nonzero_cands[0]

                with section(
                    "gj.column_step",
                    level=2,
                    col=col + 1,
                    row=pivot_row + 1,
                ):
                    record(
                        StepKind.INFO,
                        "gj.pivot_chosen",
                        level=2,
                        row=chosen_r + 1,
                        col=col + 1,
                        pivot=chosen_val,
                        strategy=self.pivot_strategy,
                    )

                    # Échange de lignes éventuel
                    if chosen_r != pivot_row:
                        grid[pivot_row], grid[chosen_r] = grid[chosen_r], grid[pivot_row]
                        snap_mat = Matrix._from_exact_rows(grid)
                        record(
                            StepKind.ROW_SWAP,
                            "gj.row_swap",
                            level=1,
                            snapshot={"augmented_matrix": snap_mat},
                            highlight=Highlight(
                                pivot=(pivot_row, col),
                                rows=(pivot_row, chosen_r),
                                augmented_split=split_col,
                                operation_latex=f"L_{{{pivot_row + 1}}} \\leftrightarrow L_{{{chosen_r + 1}}}",
                            ),
                            i=pivot_row + 1,
                            j=chosen_r + 1,
                        )

                    # Normalisation de la ligne pivot si le pivot != 1
                    pivot_val = grid[pivot_row][col]
                    if oracle.decide(pivot_val - 1, assumptions=cond).verdict != Verdict.ZERO:
                        scale = _simplify_entry(sp.Integer(1) / pivot_val)
                        grid[pivot_row] = [
                            _simplify_entry(scale * x) for x in grid[pivot_row]
                        ]
                        grid[pivot_row][col] = sp.Integer(1)
                        snap_mat = Matrix._from_exact_rows(grid)
                        record(
                            StepKind.ROW_SCALE,
                            "gj.row_scale",
                            level=1,
                            snapshot={"augmented_matrix": snap_mat},
                            highlight=Highlight(
                                pivot=(pivot_row, col),
                                rows=(pivot_row,),
                                augmented_split=split_col,
                                operation_latex=f"L_{{{pivot_row + 1}}} \\leftarrow \\left({sp.latex(scale)}\\right) L_{{{pivot_row + 1}}}",
                            ),
                            i=pivot_row + 1,
                            scale=scale,
                        )

                    # Élimination dans toutes les autres lignes (au-dessus et en-dessous)
                    for r in range(m):
                        if r == pivot_row:
                            continue
                        factor = _simplify_entry(grid[r][col])
                        dec_f = oracle.decide(factor, assumptions=cond)
                        if dec_f.verdict == Verdict.ZERO:
                            grid[r][col] = sp.Integer(0)
                            continue
                        # Transvection L_r <- L_r - factor * L_pivot
                        grid[r] = [
                            _simplify_entry(grid[r][c_idx] - factor * grid[pivot_row][c_idx])
                            for c_idx in range(total_cols)
                        ]
                        grid[r][col] = sp.Integer(0)
                        sign_str = "-" if not str(factor).startswith("-") else "+"
                        lam_abs = -factor if str(factor).startswith("-") else factor
                        snap_mat = Matrix._from_exact_rows(grid)
                        record(
                            StepKind.ROW_ADD,
                            "gj.row_add",
                            level=1,
                            snapshot={"augmented_matrix": snap_mat},
                            highlight=Highlight(
                                pivot=(pivot_row, col),
                                rows=(r,),
                                augmented_split=split_col,
                                operation_latex=f"L_{{{r + 1}}} \\leftarrow L_{{{r + 1}}} {sign_str} \\left({sp.latex(lam_abs)}\\right) L_{{{pivot_row + 1}}}",
                            ),
                            i=r + 1,
                            j=pivot_row + 1,
                            col=col + 1,
                            sign=sign_str,
                            lam=lam_abs,
                        )

                pivots.append(col)
                pivot_row += 1

            # Vérification de compatibilité sur les lignes nulles si un second membre est présent
            rank = len(pivots)
            if b_cur is not None and not self.compute_inverse:
                has_unconditional_inconsistency = False
                for r in range(rank, m):
                    for rhs_c in range(n, total_cols):
                        rhs_val = _simplify_entry(grid[r][rhs_c])
                        grid[r][rhs_c] = rhs_val
                        if oracle.decide(rhs_val, assumptions=cond).verdict == Verdict.NONZERO:
                            has_unconditional_inconsistency = True
                if not has_unconditional_inconsistency:
                    for r in range(rank, m):
                        for rhs_c in range(n, total_cols):
                            rhs_val = grid[r][rhs_c]
                            dec_rhs = oracle.decide(rhs_val, assumptions=cond)
                            if dec_rhs.verdict == Verdict.CONDITIONAL:
                                return self._split_on_factors(
                                    A_in,
                                    b_in,
                                    cond,
                                    factors=dec_rhs.factors,
                                    row=r,
                                    col=rhs_c,
                                    expr=rhs_val,
                                    depth=depth,
                                    state=state,
                                )

            aug_rref = Matrix._from_exact_rows(grid)
            rref_a = aug_rref[:, :n] if n > 0 else Matrix.zeros(m, 0)
            free_vars = tuple(j for j in range(n) if j not in pivots)
            null_basis = self._extract_nullspace(rref_a, pivots, free_vars)

            solution: SolutionSet | None = None
            inverse_mat: Matrix | None = None

            if self.compute_inverse and m == n:
                if rank < n:
                    record(
                        StepKind.INFO,
                        "gj.singular_inverse",
                        level=1,
                        rank=rank,
                        n=n,
                    )
                    if self.strict:
                        raise SingularMatrixError(
                            f"La matrice {n}x{n} est singulière (rang {rank} < {n}).",
                            rank=rank,
                        )
                    inverse_mat = None
                else:
                    inverse_mat = aug_rref[:, n:]
                    record(
                        StepKind.RESULT,
                        "gj.inverse_found",
                        level=1,
                        snapshot={"result": inverse_mat},
                        n=n,
                    )

            if b_cur is not None and not self.compute_inverse:
                solution = self._build_solution_set(
                    aug_rref,
                    m=m,
                    n=n,
                    total_cols=total_cols,
                    pivots=tuple(pivots),
                    free_vars=free_vars,
                    null_basis=null_basis,
                    is_vector_rhs=isinstance(b_cur, Vector),
                    cond=cond,
                )

            record(
                StepKind.RESULT,
                "gj.summary",
                level=1,
                snapshot={"augmented_matrix": aug_rref},
                highlight=Highlight(augmented_split=split_col),
                rank=rank,
                pivots=[p + 1 for p in pivots],
            )

            return GJResult(
                A=A_cur,
                b=b_cur,
                rref=rref_a,
                augmented_rref=aug_rref,
                pivots=tuple(pivots),
                rank=rank,
                free_vars=free_vars,
                nullspace_basis=null_basis,
                solution=solution,
                inverse=inverse_mat,
            )

    def _split_on_factors(
        self,
        A_in: Matrix,
        b_in: Vector | Matrix | None,
        cond: Condition,
        *,
        factors: tuple[sp.Expr, ...],
        row: int,
        col: int,
        expr: sp.Expr,
        depth: int,
        state: dict[str, int],
    ) -> CaseSplit[GJResult]:
        if depth >= self.max_depth:
            raise PedagopyError(
                f"Profondeur maximale de discussion par cas atteinte (max_depth={self.max_depth}). "
                "Fournissez des hypothèses sur les paramètres (assumptions=...)."
            )
        if state["cases_count"] + len(factors) > self.max_cases:
            raise PedagopyError(
                f"Nombre maximal de branches dépassé (max_cases={self.max_cases}). "
                "Fournissez des hypothèses sur les paramètres (assumptions=...)."
            )

        state["cases_count"] += len(factors)

        # 1. Branche générique : tous les facteurs sont non nuls
        gen_cond = cond
        for fac in factors:
            gen_cond = gen_cond & Condition.from_zero_expr(fac, is_zero=False)

        branches: list[Branch[GJResult]] = []

        if not gen_cond.is_contradictory:
            with tracing(level=3) as t_gen:
                gen_res = self._solve_under_condition(
                    A_in, b_in, gen_cond, depth=depth + 1, state=state
                )
            if isinstance(gen_res, CaseSplit):
                for b_sub in gen_res.branches:
                    branches.append(b_sub)
            else:
                object.__setattr__(gen_res, "trace", t_gen.tree)
                branches.append(Branch(condition=gen_cond, result=gen_res, trace=t_gen.tree))

        # 2. Branches particulières disjointes : le facteur i s'annule et les précédents (< i) sont non nuls
        prefix_neq = cond
        for fac in factors:
            part_cond = prefix_neq & Condition.from_zero_expr(fac, is_zero=True)
            prefix_neq = prefix_neq & Condition.from_zero_expr(fac, is_zero=False)
            if part_cond.is_contradictory:
                continue
            with tracing(level=3) as t_part:
                part_res = self._solve_under_condition(
                    A_in, b_in, part_cond, depth=depth + 1, state=state
                )
            if isinstance(part_res, CaseSplit):
                for b_sub in part_res.branches:
                    branches.append(b_sub)
            else:
                object.__setattr__(part_res, "trace", t_part.tree)
                branches.append(Branch(condition=part_cond, result=part_res, trace=t_part.tree))

        # Enregistrement dans la trace courante
        params_names = ", ".join(sorted(s.name for s in expr.free_symbols))
        record(
            StepKind.CASE_SPLIT,
            "gj.case_split",
            level=1,
            param=params_names,
            row=row + 1,
            col=col + 1,
            expr=expr,
        )
        return CaseSplit(branches=tuple(branches))

    @staticmethod
    def _extract_nullspace(
        rref_a: Matrix,
        pivots: list[int],
        free_vars: tuple[int, ...],
    ) -> tuple[Vector, ...]:
        n = rref_a.cols
        basis: list[Vector] = []
        for f_col in free_vars:
            vec = [sp.Integer(0)] * n
            vec[f_col] = sp.Integer(1)
            for row_idx, p_col in enumerate(pivots):
                vec[p_col] = _simplify_entry(-rref_a[row_idx, f_col])
            basis.append(Vector._from_exact(vec))
        return tuple(basis)

    def _build_solution_set(
        self,
        aug_rref: Matrix,
        *,
        m: int,
        n: int,
        total_cols: int,
        pivots: tuple[int, ...],
        free_vars: tuple[int, ...],
        null_basis: tuple[Vector, ...],
        is_vector_rhs: bool,
        cond: Condition,
    ) -> SolutionSet:
        rank = len(pivots)
        inconsistent: list[tuple[int, sp.Expr]] = []
        for r in range(rank, m):
            for c_idx in range(n, total_cols):
                val = aug_rref[r, c_idx]
                dec_val = oracle.decide(val, assumptions=cond)
                if dec_val.verdict == Verdict.UNKNOWN:
                    oracle.is_zero(val, assumptions=cond)
                if dec_val.verdict == Verdict.NONZERO:
                    inconsistent.append((r, val))
                    break

        if inconsistent:
            first_r, first_w = inconsistent[0]
            record(
                StepKind.RESULT,
                "gj.inconsistent",
                level=1,
                row=first_r + 1,
                rhs=first_w,
            )
            if self.strict:
                raise SingularMatrixError(
                    f"Système incompatible à la ligne L{first_r + 1} (0 = {first_w}).",
                    rank=rank,
                )
            return EmptySolution(
                row=first_r,
                witness=first_w,
                inconsistent_rows=tuple(inconsistent),
            )

        rhs_cols = total_cols - n
        if not free_vars:
            if is_vector_rhs or rhs_cols == 1:
                x_entries = [sp.Integer(0)] * n
                for row_idx, p_col in enumerate(pivots):
                    x_entries[p_col] = _simplify_entry(aug_rref[row_idx, n])
                x_vec = Vector._from_exact(x_entries)
                record(
                    StepKind.RESULT,
                    "gj.unique_solution",
                    level=1,
                    snapshot={"result": x_vec},
                    rank=rank,
                    x=x_vec,
                )
                return UniqueSolution(x=x_vec)
            else:
                x_mat_rows = [[sp.Integer(0)] * rhs_cols for _ in range(n)]
                for row_idx, p_col in enumerate(pivots):
                    for k_idx in range(rhs_cols):
                        x_mat_rows[p_col][k_idx] = _simplify_entry(aug_rref[row_idx, n + k_idx])
                x_mat = Matrix._from_exact_rows(x_mat_rows)
                record(
                    StepKind.RESULT,
                    "gj.unique_solution",
                    level=1,
                    snapshot={"result": x_mat},
                    rank=rank,
                    x=x_mat,
                )
                return UniqueSolution(x=x_mat)

        # Cas affine (variables libres présentes)
        x0_entries = [sp.Integer(0)] * n
        for row_idx, p_col in enumerate(pivots):
            x0_entries[p_col] = _simplify_entry(aug_rref[row_idx, n])
        x0_vec = Vector._from_exact(x0_entries)
        record(
            StepKind.RESULT,
            "gj.affine_solution",
            level=1,
            rank=rank,
            n=n,
            k=len(free_vars),
        )
        return AffineSolution(x0=x0_vec, basis=null_basis, free_vars=free_vars)


register_gauss_jordan_hook(GaussJordan)
