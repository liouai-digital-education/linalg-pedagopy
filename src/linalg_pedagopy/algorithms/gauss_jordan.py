"""Élimination de Gauss-Jordan complète avec discussion par cas et choix du pivot."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.algorithms.base import (
    AffineSolution,
    EmptySolution,
    Procedure,
    Result,
    SolutionSet,
    UniqueSolution,
)
from linalg_pedagopy.algorithms.elimination import (
    EliminationEngine,
    EliminationSetup,
    EliminationState,
    PivotStrategy,
    Reduction,
    SplitRequest,
    _result_entry,
    kernel_basis,
    trace_kernel,
    _simplify_entry,
)
from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import CaseSplit, Condition
from linalg_pedagopy.core.field import pretty_expr
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    PedagogicalWarning,
    PedagopyError,
    SingularMatrixError,
)
from linalg_pedagopy.core.zero import (
    AssumptionsType,
    Verdict,
    _normalize_assumptions,
    domain_of,
    oracle,
)
from linalg_pedagopy.objects.matrix import Matrix, register_procedure
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.text import format_value_text
from linalg_pedagopy.trace.step import Highlight, StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing

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
        reduction: Reduction = "simultaneous",
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
        if pivot_strategy not in ("simplest", "first", "partial", "sparse"):
            raise ValueError(f"Stratégie de pivot inconnue : {pivot_strategy!r}")
        if reduction not in ("simultaneous", "back_substitution"):
            raise ValueError(f"Mode de réduction inconnu : {reduction!r}")

        self.A = A
        self.b = b
        self.pivot_strategy: PivotStrategy = pivot_strategy
        self.reduction: Reduction = reduction
        self.strict = strict
        self.max_depth = max_depth if max_depth is not None else config.max_case_depth
        self.max_cases = max_cases if max_cases is not None else config.max_cases
        self.assumptions = _normalize_assumptions(assumptions)
        self.compute_inverse = compute_inverse or (
            isinstance(b, Matrix) and A.rows == A.cols and b == Matrix.identity(A.rows)
        )
        # Un second membre fourni sans compute_inverse demande la solution, même s'il vaut I_n
        # (l'inverse est alors calculée en plus) ; avec compute_inverse=True, seule l'inverse l'est.
        self._solution_demandee = b is not None and not compute_inverse
        if compute_inverse and b is None and A.rows == A.cols:
            # Sans second membre, l'inverse se calcule en réduisant [A | I_n].
            self.b = Matrix.identity(A.rows)

    def _warn_if_large_symbolic(self) -> None:
        """Avertissement didactique au-delà de config.max_generic_dim pour une matrice à paramètres."""
        limit = config.max_generic_dim
        m, n = self.A.shape
        if limit is None or max(m, n) <= limit:
            return
        if not any(getattr(e, "free_symbols", None) for e in self.A.flat_entries):
            return
        warnings.warn(
            PedagogicalWarning(
                f"Élimination de Gauss-Jordan sur une matrice {m}×{n} à paramètres : au-delà de "
                f"{limit}×{limit}, la discussion par cas et les fractions deviennent difficiles à lire. "
                "Cherchez d'abord une structure remarquable (triangulaire par blocs, tridiagonale, "
                "a·I + b·J, Vandermonde…) qui conduit à une méthode plus directe. "
                "Le calcul est mené à terme ; pour ne plus voir cet avertissement : config.max_generic_dim = None."
            ),
            stacklevel=4,
        )

    def _execute(self) -> GJResult | CaseSplit[GJResult]:
        self._warn_if_large_symbolic()
        # Valeurs interdites par les dénominateurs des coefficients : elles restreignent toutes les branches
        entries = list(self.A.flat_entries)
        if isinstance(self.b, Matrix):
            entries += self.b.flat_entries
        elif self.b is not None:
            entries += self.b.entries
        domain = domain_of(entries, self.assumptions)
        cond = self.assumptions
        if not domain.is_trivial:
            cond = cond & domain
            if cond.is_contradictory:
                raise PedagopyError(
                    f"Les coefficients ne sont pas définis sous les hypothèses données : "
                    f"ils exigent {domain}."
                )
            record(StepKind.INFO, "gj.domain", level=1, domain=domain)
        engine: EliminationEngine[GJResult] = EliminationEngine(
            prefix="gj",
            setup=self._setup,
            on_complete=self._complete,
            pivot_strategy=self.pivot_strategy,
            reduction=self.reduction,
            max_depth=self.max_depth,
            max_cases=self.max_cases,
        )
        return engine.run(cond)

    def _setup(self, cond: Condition) -> EliminationSetup:
        """Grille de travail d'une branche : [A | b] sous les substitutions de la condition."""
        subs_map = cond.substitutions()
        A_cur = self.A.subs(subs_map) if subs_map else self.A
        b_cur = self.b.subs(subs_map) if (self.b is not None and subs_map) else self.b

        m, n = A_cur.shape
        aug = A_cur.augment(b_cur) if b_cur is not None else A_cur
        grid: list[list[sp.Expr]] = [
            [_simplify_entry(aug[i, j]) for j in range(aug.cols)] for i in range(m)
        ]
        return EliminationSetup(
            grid=grid,
            n_cols=n,
            split_col=n if b_cur is not None else None,
            start_params={"m": m, "n": n},
            context=(A_cur, b_cur),
        )

    def _complete(self, st: EliminationState) -> GJResult | SplitRequest:
        """Fin d'une branche : compatibilité, réduction par la condition, solution, inverse, résumé."""
        grid, cond, pivots = st.grid, st.cond, st.pivots
        A_cur, b_cur = st.setup.context
        m, n = len(grid), st.setup.n_cols
        total_cols = len(grid[0]) if grid else n
        split_col = st.setup.split_col
        # Vérification de compatibilité sur les lignes nulles si un second membre est présent
        rank = len(pivots)
        if b_cur is not None and self._solution_demandee:
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
                            return SplitRequest(factors=dec_rhs.factors, row=r, col=rhs_c, expr=rhs_val)

        # Branche à égalité non linéaire (a² − 3 = 0) : coefficients réduits modulo cette égalité
        nonlinear = cond.nonlinear_equations()
        if nonlinear:
            reduced = [[_simplify_entry(cond.reduce(x)) for x in row] for row in grid]
            if reduced != grid:
                grid = reduced
                record(
                    StepKind.INFO,
                    "gj.reduce_by_condition",
                    level=2,
                    snapshot={"augmented_matrix": Matrix._from_exact_rows(grid)},
                    highlight=Highlight(augmented_split=split_col),
                    equations=" et ".join(f"{pretty_expr(p)} = 0" for p, _ in nonlinear),
                )

        finish = _result_entry(cond)
        aug_rref = Matrix._from_exact_rows(grid)
        rref_a = aug_rref[:, :n] if n > 0 else Matrix.zeros(m, 0)
        free_vars = tuple(j for j in range(n) if j not in pivots)
        null_basis = kernel_basis(rref_a, pivots, finish=finish)
        if b_cur is None:
            # Réduction de A seule (rref, rang, noyau) : le noyau est l'objet étudié
            trace_kernel(rref_a, pivots, null_basis, announce_trivial=True)

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
                inverse_mat = Matrix._from_exact_rows(
                    [[finish(x) for x in row] for row in aug_rref[:, n:].entries_grid]
                )
                record(
                    StepKind.RESULT,
                    "gj.inverse_found",
                    level=1,
                    snapshot={"result": inverse_mat},
                    n=n,
                )

        if b_cur is not None and self._solution_demandee:
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
        finish = _result_entry(cond)
        inconsistent: list[tuple[int, sp.Expr]] = []
        for r in range(rank, m):
            for c_idx in range(n, total_cols):
                val = aug_rref[r, c_idx]
                dec_val = oracle.decide(val, assumptions=cond)
                if dec_val.verdict == Verdict.UNKNOWN:
                    oracle.is_zero(val, assumptions=cond)
                if dec_val.verdict == Verdict.NONZERO:
                    inconsistent.append((r, finish(val)))
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
                    x_entries[p_col] = finish(aug_rref[row_idx, n])
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
                        x_mat_rows[p_col][k_idx] = finish(aug_rref[row_idx, n + k_idx])
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
            x0_entries[p_col] = finish(aug_rref[row_idx, n])
        x0_vec = Vector._from_exact(x0_entries)
        # Les directions de l'ensemble affine sont les vecteurs de base du noyau
        trace_kernel(aug_rref[:, :n], pivots, null_basis)
        record(
            StepKind.RESULT,
            "gj.affine_solution",
            level=1,
            rank=rank,
            n=n,
            k=len(free_vars),
        )
        return AffineSolution(x0=x0_vec, basis=null_basis, free_vars=free_vars)


register_procedure("gauss_jordan", GaussJordan)
