"""Résolution de systèmes triangulaires par substitution avant et arrière."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    # Dans une discussion par cas : indice (à partir de 1) du coefficient diagonal nul
    # qui rend la substitution inapplicable dans cette branche (x est alors vide)
    singular_index: int | None = field(default=None, repr=False)

    @property
    def singular(self) -> bool:
        """Vrai si un coefficient diagonal s'annule dans cette branche (pas de substitution)."""
        return self.singular_index is not None

    def subs(self, mapping: Mapping[Any, Any]) -> TriangularResult:
        return TriangularResult(
            trace=self.trace,
            x=self.x.subs(mapping),
            A=self.A.subs(mapping),
            c=self.c.subs(mapping),
            singular_index=self.singular_index,
        )

    def _branch_summary_lines(self) -> list[str]:
        if self.singular:
            k = self.singular_index
            return [f"coefficient diagonal ({k},{k}) nul : système singulier, substitution impossible"]
        return [f"x = {self.x}"]

    def _run_verification(self) -> None:
        if self.singular:
            return
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
        return _substituer(self.R, self.c, cond, nom="R", arriere=True)


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
        return _substituer(self.L, self.c, cond, nom="L", arriere=False)


def _substituer(
    M: Matrix,
    c: Vector,
    cond: Condition,
    *,
    nom: str,
    arriere: bool,
    branche_singuliere: bool = False,
) -> TriangularResult | CaseSplit[TriangularResult]:
    """Substitution arrière (``arriere``) ou avant sous la condition ``cond``.

    Quand un coefficient diagonal peut s'annuler selon les paramètres, la discussion couvre
    tous les cas : branche générique (coefficient non nul), puis une branche par facteur qui
    l'annule, où la substitution ne s'applique pas (résultat ``singular``).
    """
    subs_map = cond.substitutions()
    M_cur = M.subs(subs_map) if subs_map else M
    c_cur = c.subs(subs_map) if subs_map else c
    n = M_cur.rows
    debut = "triangular.back_start" if arriere else "triangular.forward_start"
    ordre = range(n - 1, -1, -1) if arriere else range(n)

    with section(debut, level=1, snapshot={"matrix": M_cur}, n=n):
        x_vals: list[sp.Expr] = [sp.Integer(0)] * n
        for i in ordre:
            diag = _simplify_entry(M_cur[i, i])
            dec = oracle.decide(diag, assumptions=cond)
            if dec.verdict == Verdict.ZERO:
                if branche_singuliere:
                    record(StepKind.WARNING, "triangular.singular", level=1, name=nom, i=i + 1)
                    return TriangularResult(A=M_cur, c=c_cur, singular_index=i + 1)
                raise SingularMatrixError(
                    f"Coefficient diagonal {nom}[{i + 1},{i + 1}] nul : système singulier."
                )
            if dec.verdict == Verdict.CONDITIONAL and dec.factors:
                return _discuter(M, c, cond, dec.factors, nom=nom, arriere=arriere)

            autres = range(i + 1, n) if arriere else range(i)
            sum_terms = _simplify_entry(
                sum((M_cur[i, j] * x_vals[j] for j in autres), sp.Integer(0))
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
        return TriangularResult(x=x_vec, A=M_cur, c=c_cur)


def _discuter(
    M: Matrix,
    c: Vector,
    cond: Condition,
    factors: tuple[sp.Expr, ...],
    *,
    nom: str,
    arriere: bool,
) -> CaseSplit[TriangularResult]:
    """Branche générique puis branches disjointes où chaque facteur s'annule."""
    generique = cond
    for fac in factors:
        generique = generique & Condition.from_zero_expr(fac, is_zero=False)
    cas = [(generique, False)]
    prefixe = cond
    for fac in factors:
        cas.append((prefixe & Condition.from_zero_expr(fac, is_zero=True), True))
        prefixe = prefixe & Condition.from_zero_expr(fac, is_zero=False)

    branches: list[Branch[TriangularResult]] = []
    for sous, singuliere in cas:
        if sous.is_contradictory:
            continue
        with tracing(level=3) as t_sub:
            res = _substituer(M, c, sous, nom=nom, arriere=arriere, branche_singuliere=singuliere)
        if isinstance(res, CaseSplit):
            branches.extend(res.branches)
        else:
            object.__setattr__(res, "trace", t_sub.tree)
            branches.append(Branch(sous, res, t_sub.tree))
    return CaseSplit(branches=tuple(branches))
