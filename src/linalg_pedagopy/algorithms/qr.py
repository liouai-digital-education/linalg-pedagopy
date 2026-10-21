"""Factorisation QR rationnelle et normalisée."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.algorithms.base import Procedure, Result
from linalg_pedagopy.algorithms.elimination import _simplify_entry
from linalg_pedagopy.algorithms.gram_schmidt import DependenceWitness, GSResult, GramSchmidt
from linalg_pedagopy.core.cases import Branch, CaseSplit
from linalg_pedagopy.core.exceptions import RankDeficientError
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing


@dataclass(frozen=True)
class QRResult(Result):
    """Résultat typé de la factorisation QR."""

    A: Matrix = Matrix([])
    Q: Matrix = Matrix([])
    R: Matrix = Matrix([])
    Q_tilde: Matrix = Matrix([])
    R_tilde: Matrix = Matrix([])
    D_sq: Matrix = Matrix([])
    d_sq: tuple[sp.Expr, ...] = ()
    full_rank: bool = True
    witness: DependenceWitness | None = None

    def subs(self, mapping: Mapping[Any, Any]) -> QRResult:
        """Résultat spécialisé : paramètres remplacés par des valeurs (``mapping`` : symbole ou nom → valeur)."""
        sym_map = {
            (sp.Symbol(k, real=True) if isinstance(k, str) else k): v
            for k, v in mapping.items()
        }
        return QRResult(
            trace=self.trace,
            A=self.A.subs(mapping),
            Q=self.Q.subs(mapping) if self.Q.rows > 0 else Matrix([]),
            R=self.R.subs(mapping) if self.R.rows > 0 else Matrix([]),
            Q_tilde=self.Q_tilde.subs(mapping) if self.Q_tilde.rows > 0 else Matrix([]),
            R_tilde=self.R_tilde.subs(mapping) if self.R_tilde.rows > 0 else Matrix([]),
            D_sq=self.D_sq.subs(mapping) if self.D_sq.rows > 0 else Matrix([]),
            d_sq=tuple(sp.simplify(e.xreplace(sym_map)) for e in self.d_sq),
            full_rank=self.full_rank,
            witness=self.witness,
        )

    def _branch_summary_lines(self) -> list[str]:
        if self.full_rank:
            return [f"rang plein ({self.A.cols}), factorisation A = Q R"]
        return [f"colonnes liées ({self.witness})"]

    def _run_verification(self) -> None:
        n = self.A.cols
        with section("qr.verify", level=1, n=n):
            if not self.full_rank:
                record(
                    StepKind.CHECK,
                    "gj.verify_ok",
                    level=1,
                    detail=f"Colonnes dépendantes : {self.witness}",
                )
                return

            with suspend_tracing():
                diff_a = (self.Q @ self.R) - self.A
                for i in range(diff_a.rows):
                    for j in range(diff_a.cols):
                        dec = oracle.decide(diff_a[i, j])
                        if dec.verdict != Verdict.ZERO:
                            raise AssertionError(
                                f"Échec de vérification QR = A en ({i + 1},{j + 1}) : {diff_a[i, j]}"
                            )
            record(StepKind.CHECK, "qr.verify_qr_eq_a", level=1)

            with suspend_tracing():
                diff_i = (self.Q.T @ self.Q) - Matrix.identity(n)
                for i in range(n):
                    for j in range(n):
                        dec = oracle.decide(diff_i[i, j])
                        if dec.verdict != Verdict.ZERO:
                            raise AssertionError(
                                f"Échec de vérification Q^T Q = I en ({i + 1},{j + 1}) : {diff_i[i, j]}"
                            )
            record(StepKind.CHECK, "qr.verify_qtq_eq_i", level=1, n=n)


class QR(Procedure[QRResult]):
    """Procédure de factorisation QR rationnelle puis normalisée."""

    def __init__(
        self,
        A: Matrix,
        *,
        strict: bool = False,
        assumptions: AssumptionsType = None,
    ) -> None:
        if not isinstance(A, Matrix):
            A = Matrix(A)
        self.A = A
        self.strict = strict
        self.assumptions = assumptions

    def _execute(self) -> QRResult | CaseSplit[QRResult]:
        m, n = self.A.shape
        with section("qr.start", level=1, snapshot={"A": self.A}, m=m, n=n):
            gs_proc = GramSchmidt(
                self.A.columns(),
                normalize="end",
                strict=False,
                assumptions=self.assumptions,
            )
            gs_res = gs_proc._execute()
            if isinstance(gs_res, CaseSplit):
                branches: list[Branch[QRResult]] = []
                for b in gs_res.branches:
                    qr_b = self._from_gs_result(self.A.subs(b.condition.substitutions()), b.result)
                    object.__setattr__(qr_b, "trace", b.trace)
                    branches.append(Branch(b.condition, qr_b, b.trace))
                return CaseSplit(branches=tuple(branches), parameters=gs_res.parameters)

            return self._from_gs_result(self.A, gs_res)

    def _from_gs_result(self, A_mat: Matrix, gs_res: GSResult) -> QRResult:
        n = A_mat.cols
        if not gs_res.independent:
            if self.strict:
                raise RankDeficientError(
                    f"La matrice A n'est pas de rang plein en colonnes ({gs_res.witness}).",
                    rank=len(gs_res.orthogonal),
                    ncols=n,
                )
            return QRResult(
                A=A_mat,
                Q=Matrix([]),
                R=Matrix([]),
                Q_tilde=gs_res.Q_tilde,
                R_tilde=gs_res.r_tilde,
                D_sq=Matrix.diag(gs_res.d_sq),
                d_sq=gs_res.d_sq,
                full_rank=False,
                witness=gs_res.witness,
            )

        Q_tilde = gs_res.Q_tilde
        R_tilde = gs_res.r_tilde
        D_sq = Matrix.diag(gs_res.d_sq)
        record(
            StepKind.INFO,
            "qr.rational_step",
            level=1,
            snapshot={"matrix": Q_tilde},
        )

        Q = gs_res.Q
        d_norms = [_simplify_entry(sp.sqrt(dsq)) for dsq in gs_res.d_sq]
        R_rows = [
            [
                _simplify_entry(d_norms[i] * R_tilde[i, j]) if j >= i else sp.Integer(0)
                for j in range(n)
            ]
            for i in range(n)
        ]
        R = Matrix._from_exact_rows(R_rows)

        record(
            StepKind.INFO,
            "qr.normalize_step",
            level=1,
            snapshot={"matrix": R},
        )
        record(
            StepKind.RESULT,
            "qr.summary",
            level=1,
            snapshot={"result": Q},
        )
        return QRResult(
            A=A_mat,
            Q=Q,
            R=R,
            Q_tilde=Q_tilde,
            R_tilde=R_tilde,
            D_sq=D_sq,
            d_sq=gs_res.d_sq,
            full_rank=True,
            witness=None,
        )
