"""Résolution de systèmes triangulaires par substitution avant et arrière."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.algorithms.base import Procedure, Result
from linalg_pedagopy.algorithms.elimination import _simplify_entry
from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    SingularMatrixError,
)
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle, _normalize_assumptions
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing, tracing


@dataclass(frozen=True)
class TriangularResult(Result):
    """Résultat typé d'une substitution avant ou arrière."""

    x: Vector = Vector([])
    A: Matrix = Matrix([])
    c: Vector = Vector([])

    def subs(self, mapping: Mapping[Any, Any]) -> TriangularResult:
        return TriangularResult(
            trace=self.trace,
            x=self.x.subs(mapping),
            A=self.A.subs(mapping),
            c=self.c.subs(mapping),
        )

    def _branch_summary_lines(self) -> list[str]:
        return [f"x = {self.x}"]

    def _run_verification(self) -> None:
        with suspend_tracing():
            res_vec = (self.A @ self.x) - self.c
            ok = res_vec.is_zero()
        record(
            StepKind.CHECK,
            "triangular.verify",
            level=1,
            residual=res_vec,
            ok=ok,
        )


class BackSubstitution(Procedure[TriangularResult]):
    """Résolution d'un système triangulaire supérieur R x = c par substitution arrière."""

    def __init__(
        self,
        R: Matrix,
        c: Vector,
        *,
        assumptions: AssumptionsType = None,
    ) -> None:
        if not isinstance(R, Matrix):
            R = Matrix(R)
        if not isinstance(c, Vector):
            c = Vector(c)
        if R.rows != R.cols:
            raise DimensionMismatchError(
                f"La matrice R doit être carrée (reçu {R.shape})."
            )
        if R.rows != len(c):
            raise DimensionMismatchError(
                f"Dimensions incompatibles entre R ({R.shape}) et c ({len(c)})."
            )
        n = R.rows
        for i in range(n):
            for j in range(i):
                if oracle.decide(R[i, j], assumptions=assumptions).verdict == Verdict.NONZERO:
                    raise ValueError(
                        f"La matrice R n'est pas triangulaire supérieure : R[{i + 1},{j + 1}] = {R[i, j]} != 0."
                    )
        self.R = R
        self.c = c
        self.assumptions = _normalize_assumptions(assumptions)

    def _execute(self) -> TriangularResult | CaseSplit[TriangularResult]:
        return self._solve(self.assumptions)

    def _solve(self, cond: Condition) -> TriangularResult | CaseSplit[TriangularResult]:
        subs_map = cond.substitutions()
        R_cur = self.R.subs(subs_map) if subs_map else self.R
        c_cur = self.c.subs(subs_map) if subs_map else self.c
        n = R_cur.rows

        with section("triangular.back_start", level=1, snapshot={"matrix": R_cur}, n=n):
            x_vals: list[sp.Expr] = [sp.Integer(0)] * n
            for i in range(n - 1, -1, -1):
                diag = _simplify_entry(R_cur[i, i])
                dec = oracle.decide(diag, assumptions=cond)
                if dec.verdict == Verdict.ZERO:
                    raise SingularMatrixError(
                        f"Coefficient diagonal R[{i + 1},{i + 1}] nul : système singulier."
                    )
                if dec.verdict == Verdict.CONDITIONAL and dec.condition is not None:
                    gen_cond = cond & Condition(eqs=(), neqs=dec.condition.eqs)
                    with tracing(level=3) as t_gen:
                        gen_res = self._solve(gen_cond)
                    if isinstance(gen_res, TriangularResult):
                        object.__setattr__(gen_res, "trace", t_gen.tree)
                        return CaseSplit(
                            branches=(Branch(gen_cond, gen_res, t_gen.tree),)
                        )
                    return gen_res

                sum_terms = _simplify_entry(
                    sum(
                        (R_cur[i, j] * x_vals[j] for j in range(i + 1, n)),
                        sp.Integer(0),
                    )
                )
                xi = _simplify_entry((c_cur[i] - sum_terms) / diag)
                x_vals[i] = xi
                record(
                    StepKind.BACK_SUBSTITUTION,
                    "triangular.step",
                    level=1,
                    i=i + 1,
                    ci=c_cur[i],
                    sum_terms=sum_terms,
                    diag=diag,
                    xi=xi,
                )

            x_vec = Vector._from_exact(x_vals)
            record(
                StepKind.RESULT,
                "triangular.result",
                level=1,
                snapshot={"result": x_vec},
                x=x_vec,
            )
            return TriangularResult(x=x_vec, A=R_cur, c=c_cur)


class ForwardSubstitution(Procedure[TriangularResult]):
    """Résolution d'un système triangulaire inférieur L x = c par substitution avant."""

    def __init__(
        self,
        L: Matrix,
        c: Vector,
        *,
        assumptions: AssumptionsType = None,
    ) -> None:
        if not isinstance(L, Matrix):
            L = Matrix(L)
        if not isinstance(c, Vector):
            c = Vector(c)
        if L.rows != L.cols:
            raise DimensionMismatchError(
                f"La matrice L doit être carrée (reçu {L.shape})."
            )
        if L.rows != len(c):
            raise DimensionMismatchError(
                f"Dimensions incompatibles entre L ({L.shape}) et c ({len(c)})."
            )
        n = L.rows
        for i in range(n):
            for j in range(i + 1, n):
                if oracle.decide(L[i, j], assumptions=assumptions).verdict == Verdict.NONZERO:
                    raise ValueError(
                        f"La matrice L n'est pas triangulaire inférieure : L[{i + 1},{j + 1}] = {L[i, j]} != 0."
                    )
        self.L = L
        self.c = c
        self.assumptions = _normalize_assumptions(assumptions)

    def _execute(self) -> TriangularResult | CaseSplit[TriangularResult]:
        return self._solve(self.assumptions)

    def _solve(self, cond: Condition) -> TriangularResult | CaseSplit[TriangularResult]:
        subs_map = cond.substitutions()
        L_cur = self.L.subs(subs_map) if subs_map else self.L
        c_cur = self.c.subs(subs_map) if subs_map else self.c
        n = L_cur.rows

        with section("triangular.forward_start", level=1, snapshot={"matrix": L_cur}, n=n):
            x_vals: list[sp.Expr] = [sp.Integer(0)] * n
            for i in range(n):
                diag = _simplify_entry(L_cur[i, i])
                dec = oracle.decide(diag, assumptions=cond)
                if dec.verdict == Verdict.ZERO:
                    raise SingularMatrixError(
                        f"Coefficient diagonal L[{i + 1},{i + 1}] nul : système singulier."
                    )
                if dec.verdict == Verdict.CONDITIONAL and dec.condition is not None:
                    gen_cond = cond & Condition(eqs=(), neqs=dec.condition.eqs)
                    with tracing(level=3) as t_gen:
                        gen_res = self._solve(gen_cond)
                    if isinstance(gen_res, TriangularResult):
                        object.__setattr__(gen_res, "trace", t_gen.tree)
                        return CaseSplit(
                            branches=(Branch(gen_cond, gen_res, t_gen.tree),)
                        )
                    return gen_res

                sum_terms = _simplify_entry(
                    sum((L_cur[i, j] * x_vals[j] for j in range(i)), sp.Integer(0))
                )
                xi = _simplify_entry((c_cur[i] - sum_terms) / diag)
                x_vals[i] = xi
                record(
                    StepKind.BACK_SUBSTITUTION,
                    "triangular.step",
                    level=1,
                    i=i + 1,
                    ci=c_cur[i],
                    sum_terms=sum_terms,
                    diag=diag,
                    xi=xi,
                )

            x_vec = Vector._from_exact(x_vals)
            record(
                StepKind.RESULT,
                "triangular.result",
                level=1,
                snapshot={"result": x_vec},
                x=x_vec,
            )
            return TriangularResult(x=x_vec, A=L_cur, c=c_cur)
