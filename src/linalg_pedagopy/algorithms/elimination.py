"""Machinerie d'élimination commune à Gauss-Jordan et au déterminant.

- Étape 4.1 du plan v6 : fonctions pures (simplification des coefficients, critère et choix
  du pivot, mise en forme des résultats d'une branche).
- Étape 4.2 : opérations élémentaires tracées (``RowOps`` : échange, dilatation,
  transvection, étape de Bareiss).
- Étape 4.3 : moteur d'élimination (``EliminationEngine``) : parcours des colonnes, choix
  du pivot, discussion par cas quand aucun pivot n'est inconditionnellement non nul.
- Étape 4.7 : base du noyau lue sur la forme réduite (``kernel_basis``) et sa trace
  (``trace_kernel``).
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Literal, Mapping, TypeVar

import sympy as sp

from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.zero import Verdict, case_limit_error, oracle
from linalg_pedagopy.core.field import pretty_expr
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.text import format_value_text
from linalg_pedagopy.trace.step import Highlight, StepKind
from linalg_pedagopy.trace.tracer import record, section, tracing

PivotStrategy = Literal["simplest", "first", "partial", "sparse"]
Reduction = Literal["simultaneous", "back_substitution"]
R = TypeVar("R")


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


def _factor_with_radicals(expr: sp.Expr, radicals: Mapping[sp.Symbol, tuple[sp.Expr, ...]]) -> sp.Expr:
    """Factorise une entrée sur Q(√d), pour les radicaux √d de la condition de sa branche.

    Sous « a ≠ √2 et a ≠ −√2 », (a − 2)/((a − 1)(a² − 2)) s'écrit
    (a − 2)/((a − 1)(a − √2)(a + √2)) : mêmes facteurs que la condition.
    Seuls les radicaux associés aux paramètres présents dans l'entrée sont utilisés.
    """
    syms = expr.free_symbols
    if not radicals or not syms:
        return expr
    ext = sorted({r for s in syms for r in radicals.get(s, ())}, key=sp.default_sort_key)
    if not ext or not expr.is_rational_function(*syms):
        return expr
    num, den = sp.fraction(sp.together(sp.cancel(expr)))
    return sp.Mul(_split_over(num, ext), 1 / _split_over(den, ext), evaluate=True)


def _split_over(poly: sp.Expr, ext: list[sp.Expr]) -> sp.Expr:
    """Factorise sur Q, puis décompose sur Q(√d) les seuls facteurs irréductibles de degré ≥ 2.

    Les facteurs déjà décomposés sur Q gardent leur écriture (1 − 2a ne devient pas −2(a − 1/2)).
    """
    parts = []
    for f in sp.Mul.make_args(sp.factor(poly)):
        base, e = f.as_base_exp()
        if base.free_symbols and base.is_polynomial() and sp.Poly(base).total_degree() >= 2:
            split = sp.factor(base, extension=ext)
            if len(sp.Mul.make_args(split)) > 1:
                f = split**e
        parts.append(f)
    return sp.Mul(*parts)


def _result_entry(cond: Condition) -> Callable[[sp.Expr], sp.Expr]:
    """Mise en forme des entrées d'un résultat (solution, inverse, base du noyau) selon ``config.factor_policy``."""
    radicals = cond.radicals() if config.factor_policy == "real_radicals" else {}
    if not radicals:
        return _simplify_entry
    return lambda e: _factor_with_radicals(_simplify_entry(e), radicals)


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


def _choose_pivot(
    candidates: list[tuple[int, sp.Expr]],
    strategy: PivotStrategy,
    grid: list[list[sp.Expr]] | None = None,
    col: int = 0,
) -> tuple[int, sp.Expr]:
    """Pivot retenu parmi des candidats (ligne, valeur) inconditionnellement non nuls.

    ``simplest`` : le plus simple au sens de ``_pivot_complexity_key`` ; ``partial`` : la plus
    grande valeur absolue numérique ; ``first`` : le premier candidat ; ``sparse`` (critère
    de Markowitz, la colonne étant fixée) : la ligne qui a le moins de coefficients non nuls
    à partir de la colonne du pivot, ce qui limite le remplissage, puis le plus simple.
    """
    if strategy == "sparse" and grid is not None:
        def _markowitz(item: tuple[int, sp.Expr]) -> tuple[int, tuple[int, int | float, int]]:
            nonzeros = sum(1 for x in grid[item[0]][col:] if x != 0)
            return (nonzeros, _pivot_complexity_key(item[1]))
        return min(candidates, key=_markowitz)
    if strategy in ("simplest", "sparse"):
        return min(candidates, key=lambda item: _pivot_complexity_key(item[1]))
    if strategy == "partial":
        def _abs_eval(item: tuple[int, sp.Expr]) -> float:
            try:
                return float(abs(item[1].evalf()))
            except Exception:
                return 0.0
        return max(candidates, key=_abs_eval)
    return candidates[0]


@dataclass(frozen=True)
class RowOps:
    """Opérations élémentaires sur une grille de coefficients, enregistrées dans la trace.

    ``prefix`` choisit les clés de trace (``gj.row_swap``, ``det.row_swap``…),
    ``snapshot_key`` le nom de l'instantané (``augmented_matrix`` ou ``matrix``) et
    ``split_col`` la position de la barre d'une matrice augmentée. ``signed_add`` règle
    l'écriture des transvections : ``L2 ← L2 − (a − 1)·L1`` avec le signe du
    multiplicateur (Gauss-Jordan), ou toujours ``L2 ← L2 − (λ)·L1`` (déterminant).
    """

    prefix: str
    snapshot_key: str = "augmented_matrix"
    split_col: int | None = None
    signed_add: bool = True

    def _snapshot(self, grid: list[list[sp.Expr]]) -> dict[str, Any]:
        return {self.snapshot_key: Matrix._from_exact_rows(grid)}

    def swap(self, grid: list[list[sp.Expr]], i: int, j: int, *, col: int) -> None:
        """Échange des lignes i et j (pivot en (i, col))."""
        grid[i], grid[j] = grid[j], grid[i]
        record(
            StepKind.ROW_SWAP,
            f"{self.prefix}.row_swap",
            level=1,
            snapshot=self._snapshot(grid),
            highlight=Highlight(
                pivot=(i, col),
                rows=(i, j),
                augmented_split=self.split_col,
                operation_latex=f"L_{{{i + 1}}} \\leftrightarrow L_{{{j + 1}}}",
            ),
            i=i + 1,
            j=j + 1,
        )

    def scale(self, grid: list[list[sp.Expr]], i: int, *, col: int) -> sp.Expr:
        """Dilatation de la ligne i qui ramène le pivot (i, col) à 1 ; renvoie le facteur."""
        scale = _simplify_entry(sp.Integer(1) / grid[i][col])
        grid[i] = [_simplify_entry(scale * x) for x in grid[i]]
        grid[i][col] = sp.Integer(1)
        record(
            StepKind.ROW_SCALE,
            f"{self.prefix}.row_scale",
            level=1,
            snapshot=self._snapshot(grid),
            highlight=Highlight(
                pivot=(i, col),
                rows=(i,),
                augmented_split=self.split_col,
                operation_latex=f"L_{{{i + 1}}} \\leftarrow \\left({sp.latex(scale)}\\right) L_{{{i + 1}}}",
            ),
            i=i + 1,
            scale=scale,
        )
        return scale

    def add_multiple(
        self, grid: list[list[sp.Expr]], target: int, source: int, factor: sp.Expr, *, col: int
    ) -> None:
        """Transvection L_target ← L_target − factor·L_source, qui annule le coefficient (target, col)."""
        grid[target] = [
            _simplify_entry(grid[target][c] - factor * grid[source][c]) for c in range(len(grid[target]))
        ]
        grid[target][col] = sp.Integer(0)
        if not self.signed_add:
            record(
                StepKind.ROW_ADD,
                f"{self.prefix}.row_add",
                level=1,
                snapshot=self._snapshot(grid),
                highlight=Highlight(
                    pivot=(source, col),
                    rows=(target,),
                    augmented_split=self.split_col,
                    operation_latex=f"L_{{{target + 1}}} \\leftarrow L_{{{target + 1}}} - \\left({sp.latex(factor)}\\right) L_{{{source + 1}}}",
                ),
                i=target + 1,
                j=source + 1,
                lam=factor,
            )
            return
        sign_str = "-" if not str(factor).startswith("-") else "+"
        lam_abs = -factor if str(factor).startswith("-") else factor
        # Un multiplicateur somme est parenthésé : L2 ← L2 − (a − 1)·L1
        lam_txt = format_value_text(lam_abs)
        if isinstance(lam_abs, sp.Add):
            lam_txt = f"({lam_txt})"
        record(
            StepKind.ROW_ADD,
            f"{self.prefix}.row_add",
            level=1,
            snapshot=self._snapshot(grid),
            highlight=Highlight(
                pivot=(source, col),
                rows=(target,),
                augmented_split=self.split_col,
                operation_latex=f"L_{{{target + 1}}} \\leftarrow L_{{{target + 1}}} {sign_str} \\left({sp.latex(lam_abs)}\\right) L_{{{source + 1}}}",
            ),
            i=target + 1,
            j=source + 1,
            col=col + 1,
            sign="−" if sign_str == "-" else "+",
            lam=lam_abs,
            lam_txt=lam_txt,
        )

    def bareiss_step(self, grid: list[list[sp.Expr]], k: int, previous: sp.Expr) -> None:
        """Étape k de Bareiss : m_ij ← (m_kk·m_ij − m_ik·m_kj) / pivot précédent, division exacte."""
        n = len(grid)
        pivot = grid[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                grid[i][j] = _simplify_entry(sp.cancel((pivot * grid[i][j] - grid[i][k] * grid[k][j]) / previous))
                record(
                    StepKind.INFO,
                    f"{self.prefix}.bareiss_entry",
                    level=3,
                    i=i + 1,
                    j=j + 1,
                    k=k + 1,
                    value=grid[i][j],
                )
            grid[i][k] = sp.Integer(0)
        record(
            StepKind.ROW_ADD,
            f"{self.prefix}.bareiss_step",
            level=1,
            snapshot=self._snapshot(grid),
            highlight=Highlight(pivot=(k, k), rows=tuple(range(k + 1, n)), augmented_split=self.split_col),
            k=k + 1,
            pivot=pivot,
            previous=previous,
        )


@dataclass
class EliminationSetup:
    """Grille de travail d'une branche, fournie au moteur par la procédure.

    ``n_cols`` : nombre de colonnes à éliminer (celles de A, sans le second membre) ;
    ``split_col`` : position de la barre de la matrice augmentée ; ``start_params`` :
    paramètres de l'étape de trace ``{prefix}.start`` ; ``context`` : données propres à
    la procédure, rendues telles quelles à ``on_complete``.
    """

    grid: list[list[sp.Expr]]
    n_cols: int
    split_col: int | None = None
    start_params: dict[str, Any] = field(default_factory=dict)
    context: Any = None


@dataclass
class EliminationState:
    """État d'une branche en fin d'élimination, transmis à ``on_complete``."""

    grid: list[list[sp.Expr]]
    cond: Condition
    pivots: list[int]
    setup: EliminationSetup
    ops: RowOps
    swaps: int = 0


@dataclass(frozen=True)
class SplitRequest:
    """Demande de discussion par cas renvoyée par ``on_complete`` (ex. compatibilité du second membre)."""

    factors: tuple[sp.Expr, ...]
    row: int
    col: int
    expr: sp.Expr


class EliminationEngine(Generic[R]):
    """Élimination tracée avec discussion par cas, commune aux procédures qui échelonnent.

    Pour chaque condition (branche), ``setup`` construit la grille ; le moteur parcourt les
    colonnes, choisit les pivots inconditionnellement non nuls, et sépare en cas quand un
    pivot ne l'est que sous condition : branche générique (tous les facteurs non nuls),
    puis une branche par facteur nul, les précédents non nuls. ``on_complete`` fabrique le
    résultat d'une branche, ou renvoie un ``SplitRequest`` pour une discussion supplémentaire.

    ``reduce_above`` : annuler aussi les coefficients au-dessus du pivot (forme réduite) ;
    ``reduction`` : avec ``reduce_above``, ``simultaneous`` annule au-dessus et au-dessous de
    chaque pivot en une passe (Gauss-Jordan) ; ``back_substitution`` échelonne d'abord vers le
    bas, puis remonte de la dernière colonne pivot à la première (``{prefix}.back_substitution``) ;
    ``normalize_pivots`` : ramener chaque pivot à 1 (sinon, le multiplicateur d'une
    transvection est le coefficient divisé par le pivot).

    Présentation de la trace : ``start_section`` ouvre une section ``{prefix}.start`` par
    branche ; ``column_sections`` regroupe chaque colonne dans ``{prefix}.column_step``
    avec ``{prefix}.pivot_chosen`` (sinon, ``{prefix}.pivot`` est annoncé après l'échange
    éventuel) ; ``stop_on_zero_column`` arrête l'élimination à la première colonne sans
    pivot (``{prefix}.zero_column``) au lieu de passer à la suivante ; ``signed_add`` :
    voir ``RowOps``. ``limit_arguments`` : les messages de plafond citent les arguments
    ``max_cases`` et ``max_depth`` de la procédure (sinon, la seule configuration).
    """

    def __init__(
        self,
        *,
        prefix: str,
        setup: Callable[[Condition], EliminationSetup],
        on_complete: Callable[[EliminationState], R | SplitRequest],
        max_depth: int,
        max_cases: int,
        pivot_strategy: PivotStrategy = "simplest",
        reduce_above: bool = True,
        reduction: Reduction = "simultaneous",
        normalize_pivots: bool = True,
        snapshot_key: str = "augmented_matrix",
        signed_add: bool = True,
        start_section: bool = True,
        column_sections: bool = True,
        stop_on_zero_column: bool = False,
        limit_arguments: bool = True,
    ) -> None:
        self.prefix = prefix
        self.setup = setup
        self.on_complete = on_complete
        self.max_depth = max_depth
        self.max_cases = max_cases
        self.pivot_strategy: PivotStrategy = pivot_strategy
        self.reduce_above = reduce_above
        self.reduction: Reduction = reduction
        self.normalize_pivots = normalize_pivots
        self.snapshot_key = snapshot_key
        self.signed_add = signed_add
        self.start_section = start_section
        self.column_sections = column_sections
        self.stop_on_zero_column = stop_on_zero_column
        self.limit_arguments = limit_arguments

    def run(self, cond: Condition) -> R | CaseSplit[R]:
        """Élimination sous la condition initiale (hypothèses et domaine de définition)."""
        return self._solve(cond, depth=0, state={"cases_count": 1})

    def _solve(self, cond: Condition, *, depth: int, state: dict[str, Any]) -> R | CaseSplit[R]:
        setup = self.setup(cond)
        grid = setup.grid
        m, n = len(grid), setup.n_cols
        ops = RowOps(
            self.prefix, snapshot_key=self.snapshot_key, split_col=setup.split_col, signed_add=self.signed_add
        )
        pivots: list[int] = []
        pivot_row = 0
        swaps = 0

        start = (
            section(
                f"{self.prefix}.start",
                level=1,
                snapshot=ops._snapshot(grid),
                highlight=Highlight(augmented_split=setup.split_col),
                **setup.start_params,
            )
            if self.start_section
            else nullcontext()
        )
        with start:
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

                # Aucun candidat inconditionnellement non nul mais un candidat conditionnel : discussion par cas
                if not nonzero_cands and cond_cands:
                    cand_r, cand_val, cand_factors = min(
                        cond_cands, key=lambda item: _pivot_complexity_key(item[1])
                    )
                    return self._split(
                        cond, SplitRequest(cand_factors, cand_r, col, cand_val), depth=depth, state=state
                    )

                if not nonzero_cands and not cond_cands and unknown_cands:
                    oracle.is_zero(unknown_cands[0][1], assumptions=cond)

                if not nonzero_cands:
                    if self.stop_on_zero_column:
                        record(StepKind.INFO, f"{self.prefix}.zero_column", level=1, col=col + 1)
                        break
                    record(
                        StepKind.INFO,
                        f"{self.prefix}.col_zero",
                        level=2,
                        col=col + 1,
                    )
                    continue

                chosen_r, chosen_val = _choose_pivot(nonzero_cands, self.pivot_strategy, grid, col)

                column = (
                    section(
                        f"{self.prefix}.column_step",
                        level=2,
                        col=col + 1,
                        row=pivot_row + 1,
                    )
                    if self.column_sections
                    else nullcontext()
                )
                with column:
                    if self.column_sections:
                        record(
                            StepKind.INFO,
                            f"{self.prefix}.pivot_chosen",
                            level=2,
                            row=chosen_r + 1,
                            col=col + 1,
                            pivot=chosen_val,
                            strategy=self.pivot_strategy,
                        )

                    # Échange de lignes éventuel
                    if chosen_r != pivot_row:
                        ops.swap(grid, pivot_row, chosen_r, col=col)
                        swaps += 1
                    if not self.column_sections:
                        record(StepKind.INFO, f"{self.prefix}.pivot", level=2, col=col + 1, pivot=chosen_val)

                    # Normalisation de la ligne pivot si le pivot != 1
                    if (
                        self.normalize_pivots
                        and oracle.decide(grid[pivot_row][col] - 1, assumptions=cond).verdict != Verdict.ZERO
                    ):
                        ops.scale(grid, pivot_row, col=col)

                    # Élimination dans les autres lignes (toutes, ou seulement sous le pivot)
                    pivot_val = grid[pivot_row][col]
                    simultaneous = self.reduce_above and self.reduction == "simultaneous"
                    for r in range(m) if simultaneous else range(pivot_row + 1, m):
                        if r == pivot_row:
                            continue
                        factor = _simplify_entry(grid[r][col])
                        dec_f = oracle.decide(factor, assumptions=cond)
                        if dec_f.verdict == Verdict.ZERO:
                            grid[r][col] = sp.Integer(0)
                            continue
                        if not self.normalize_pivots:
                            factor = _simplify_entry(factor / pivot_val)
                        # Transvection L_r <- L_r - factor * L_pivot
                        ops.add_multiple(grid, r, pivot_row, factor, col=col)

                pivots.append(col)
                pivot_row += 1

            if self.reduce_above and self.reduction == "back_substitution" and pivots:
                self._back_substitution(grid, pivots, cond, ops)

            outcome = self.on_complete(EliminationState(grid, cond, pivots, setup, ops, swaps))
            if isinstance(outcome, SplitRequest):
                return self._split(cond, outcome, depth=depth, state=state)
            return outcome

    def _back_substitution(
        self, grid: list[list[sp.Expr]], pivots: list[int], cond: Condition, ops: RowOps
    ) -> None:
        """Remontée : annule les coefficients au-dessus des pivots, de la dernière colonne pivot à la première."""
        with section(f"{self.prefix}.back_substitution", level=2, k=len(pivots)):
            for p_row in range(len(pivots) - 1, -1, -1):
                col = pivots[p_row]
                pivot_val = grid[p_row][col]
                for r in range(p_row):
                    factor = _simplify_entry(grid[r][col])
                    if oracle.decide(factor, assumptions=cond).verdict == Verdict.ZERO:
                        grid[r][col] = sp.Integer(0)
                        continue
                    if not self.normalize_pivots:
                        factor = _simplify_entry(factor / pivot_val)
                    ops.add_multiple(grid, r, p_row, factor, col=col)

    def _split(
        self, cond: Condition, request: SplitRequest, *, depth: int, state: dict[str, Any]
    ) -> CaseSplit[R]:
        factors = request.factors
        seen: list[sp.Expr] = state.setdefault("factors", [])
        seen.extend(f for f in factors if f not in seen)
        if depth >= self.max_depth:
            raise case_limit_error(
                limit="max_depth",
                value=self.max_depth,
                reached=depth + 1,
                factors=seen,
                condition=cond,
                argument="max_depth" if self.limit_arguments else None,
            )
        if state["cases_count"] + len(factors) > self.max_cases:
            raise case_limit_error(
                limit="max_cases",
                value=self.max_cases,
                reached=state["cases_count"] + len(factors),
                factors=seen,
                condition=cond,
                argument="max_cases" if self.limit_arguments else None,
            )

        state["cases_count"] += len(factors)

        # 1. Branche générique : tous les facteurs sont non nuls
        gen_cond = cond
        for fac in factors:
            gen_cond = gen_cond & Condition.from_zero_expr(fac, is_zero=False)
        sub_conds = [gen_cond]

        # 2. Branches particulières disjointes : le facteur i s'annule et les précédents (< i) sont non nuls
        prefix_neq = cond
        for fac in factors:
            sub_conds.append(prefix_neq & Condition.from_zero_expr(fac, is_zero=True))
            prefix_neq = prefix_neq & Condition.from_zero_expr(fac, is_zero=False)

        branches: list[Branch[R]] = []
        for sub in sub_conds:
            if sub.is_contradictory:
                continue
            with tracing(level=3) as t_sub:
                res = self._solve(sub, depth=depth + 1, state=state)
            if isinstance(res, CaseSplit):
                branches.extend(res.branches)
            else:
                object.__setattr__(res, "trace", t_sub.tree)
                branches.append(Branch(condition=sub, result=res, trace=t_sub.tree))

        # Enregistrement dans la trace courante
        params_names = ", ".join(sorted(s.name for s in request.expr.free_symbols))
        record(
            StepKind.CASE_SPLIT,
            f"{self.prefix}.case_split",
            level=1,
            param=params_names,
            row=request.row + 1,
            col=request.col + 1,
            expr=request.expr,
        )
        return CaseSplit(branches=tuple(branches))


def _variables(cols: list[int] | tuple[int, ...]) -> str:
    return ", ".join(f"x{c + 1}" for c in cols)


def kernel_basis(
    rref: Matrix,
    pivots: list[int] | tuple[int, ...],
    *,
    finish: Callable[[sp.Expr], sp.Expr] = _simplify_entry,
) -> tuple[Vector, ...]:
    """Base du noyau lue sur une forme échelonnée réduite (colonnes de A seulement).

    Pour chaque variable libre x_f, on pose x_f = 1 et les autres variables libres nulles ;
    les variables principales se lisent sur la forme réduite : x_p = −Σ r_(p, f)·x_f.
    """
    n = rref.cols
    free_vars = [j for j in range(n) if j not in pivots]
    basis: list[Vector] = []
    for f_col in free_vars:
        vec = [sp.Integer(0)] * n
        vec[f_col] = sp.Integer(1)
        for row_idx, p_col in enumerate(pivots):
            vec[p_col] = finish(-rref[row_idx, f_col])
        basis.append(Vector._from_exact(vec))
    return tuple(basis)


def trace_kernel(
    rref: Matrix,
    pivots: list[int] | tuple[int, ...],
    basis: tuple[Vector, ...],
    *,
    announce_trivial: bool = False,
) -> None:
    """Étapes ``ker.*`` (niveau 2) qui expliquent la base du noyau construite par ``kernel_basis``.

    Variables libres et théorème du rang, système homogène équivalent, chaque vecteur de
    base, puis la sous-matrice identité des composantes libres, qui prouve que la famille
    est libre. ``announce_trivial`` : sans variable libre, annoncer ker A = {0} et sa base vide.
    """
    n = rref.cols
    pivots = list(pivots)
    free_vars = [j for j in range(n) if j not in pivots]
    rank, k = len(pivots), len(free_vars)
    if not free_vars:
        if announce_trivial:
            record(StepKind.INFO, "ker.trivial", level=2, rank=rank, n=n)
        return

    record(
        StepKind.INFO,
        "ker.free_vars",
        level=2,
        free=_variables(free_vars),
        pivots=_variables(pivots) or "aucune",
        n=n,
        rank=rank,
        k=k,
    )
    if pivots:
        xs = [sp.Symbol(f"x{j + 1}") for j in range(n)]
        equations = " ; ".join(
            f"x{p + 1} = {pretty_expr(sp.Add(*(-rref[row, f] * xs[f] for f in free_vars)))}"
            for row, p in enumerate(pivots)
        )
        record(StepKind.INFO, "ker.param_system", level=2, equations=equations)
    for idx, (f_col, v) in enumerate(zip(free_vars, basis), start=1):
        record(
            StepKind.INFO,
            "ker.vector" if k > 1 else "ker.vector_single",
            level=2,
            index=idx,
            var=f"x{f_col + 1}",
            vector=v,
        )
    record(
        StepKind.INFO,
        "ker.identity_block" if k > 1 else "ker.identity_single",
        level=2,
        vars=_variables(free_vars),
        vectors=", ".join(f"v{i}" for i in range(1, k + 1)),
        k=k,
    )
