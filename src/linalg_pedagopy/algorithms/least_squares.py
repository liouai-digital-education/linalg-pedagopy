"""Moindres carrés linéaires par QR rationnelle, QR normalisée ou équations normales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

import sympy as sp

from linalg_pedagopy.algorithms.base import Procedure, Result, UniqueSolution
from linalg_pedagopy.algorithms.elimination import _simplify_entry
from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan
from linalg_pedagopy.algorithms.qr import QR, QRResult
from linalg_pedagopy.algorithms.triangular import BackSubstitution
from linalg_pedagopy.core.cases import Branch, CaseSplit
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    RankDeficientError,
)
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing, tracing

LSMethod = Literal["rational_qr", "qr", "normal"]


@dataclass(frozen=True)
class LSResult(Result):
    """Résultat typé d'un problème de moindres carrés min ||A x - b||."""

    A: Matrix = Matrix([])
    b: Vector = Vector([])
    x_hat: Vector = Vector([])
    y_hat: Vector = Vector([])  # A x_hat
    r_hat: Vector = Vector([])  # résidu r_hat = A x_hat - b 
    residual_norm: sp.Expr = sp.Integer(0)
    residual_rms: sp.Expr = sp.Integer(0)
    method: LSMethod = "rational_qr"
    full_rank: bool = True
    witness: Any = None

    @property
    def residual(self) -> Vector:
        """Alias pour r_hat = A x_hat - b."""
        return self.r_hat

    @property
    def pseudoinverse(self) -> Matrix:
        """Formule théorique de la pseudo-inverse A^† = (A^T A)^(-1) A^T."""
        with suspend_tracing():
            ata = self.A.T @ self.A
            ata_inv = ata.inv(strict=True)
            if not isinstance(ata_inv, Matrix):
                raise RankDeficientError("Impossible de calculer la pseudo-inverse.")
            return ata_inv @ self.A.T

    def subs(self, mapping: Mapping[Any, Any]) -> LSResult:
        sym_map = {
            (sp.Symbol(k, real=True) if isinstance(k, str) else k): v
            for k, v in mapping.items()
        }
        return LSResult(
            trace=self.trace,
            A=self.A.subs(mapping),
            b=self.b.subs(mapping),
            x_hat=self.x_hat.subs(mapping),
            y_hat=self.y_hat.subs(mapping),
            r_hat=self.r_hat.subs(mapping),
            residual_norm=sp.simplify(self.residual_norm.xreplace(sym_map)),
            residual_rms=sp.simplify(self.residual_rms.xreplace(sym_map)),
            method=self.method,
            full_rank=self.full_rank,
            witness=self.witness,
        )

    def _branch_summary_lines(self) -> list[str]:
        if not self.full_rank:
            return [f"rang déficient (colonnes liées : {self.witness})"]
        return [
            f"rang plein ({self.A.cols}), solution des moindres carrés x_hat = {self.x_hat}",
            f"résidu r_hat = {self.r_hat}, ||r_hat|| = {self.residual_norm}",
        ]

    def _run_verification(self) -> None:
        if not self.full_rank:
            return
        with section("ls.verify", level=1):
            cols = self.A.columns()
            for j, col_j in enumerate(cols, start=1):
                with suspend_tracing():
                    ip = _simplify_entry(col_j.dot(self.r_hat))
                dec = oracle.decide(ip)
                record(
                    StepKind.CHECK,
                    "ls.verify_col",
                    level=1,
                    j=j,
                    val=ip,
                    verdict=dec.verdict.name,
                )
                if dec.verdict != Verdict.ZERO:
                    raise AssertionError(
                        f"Le résidu n'est pas orthogonal à la colonne {j} : a_{j}^T r_hat = {ip}"
                    )


class LeastSquares(Procedure[LSResult]):
    """Procédure de résolution de min ||A x - b|| au sens des moindres carrés."""

    def __init__(
        self,
        A: Matrix,
        b: Vector,
        *,
        method: LSMethod = "rational_qr",
        assumptions: AssumptionsType = None,
    ) -> None:
        if not isinstance(A, Matrix):
            A = Matrix(A)
        if not isinstance(b, Vector):
            b = Vector(b)
        if A.rows != len(b):
            raise DimensionMismatchError(
                f"Le nombre de lignes de A ({A.rows}) diffère de la taille de b ({len(b)})."
            )
        if A.rows < A.cols:
            raise RankDeficientError(
                f"Moindres carrés requiert m >= n (reçu {A.rows}x{A.cols}).",
                rank=A.rows,
                ncols=A.cols,
            )
        if method not in ("rational_qr", "qr", "normal"):
            raise ValueError(f"Méthode de moindres carrés inconnue : {method!r}")

        self.A = A
        self.b = b
        self.method: LSMethod = method
        self.assumptions = assumptions

    def _execute(self) -> LSResult | CaseSplit[LSResult]:
        m, n = self.A.shape
        with section(
            "ls.start",
            level=1,
            snapshot={"A": self.A, "b": self.b},
            m=m,
            n=n,
            method=self.method,
        ):
            # Vérification du rang plein en colonnes via QR rationnelle
            with suspend_tracing():
                qr_check = QR(self.A, strict=False, assumptions=self.assumptions).run()

            if isinstance(qr_check, CaseSplit):
                branches: list[Branch[LSResult]] = []
                for br in qr_check.branches:
                    subs_map = br.condition.substitutions()
                    A_sub = self.A.subs(subs_map) if subs_map else self.A
                    b_sub = self.b.subs(subs_map) if subs_map else self.b
                    if not br.result.full_rank:
                        ls_def = LSResult(
                            trace=br.trace,
                            A=A_sub,
                            b=b_sub,
                            method=self.method,
                            full_rank=False,
                            witness=br.result.witness,
                        )
                        branches.append(Branch(br.condition, ls_def, br.trace))
                        continue
                    with tracing(level=3) as t_br:
                        ls_sub = self._solve_full_rank(
                            A_sub, b_sub, br.result, assumptions=br.condition
                        )
                    object.__setattr__(ls_sub, "trace", t_br.tree)
                    branches.append(Branch(br.condition, ls_sub, t_br.tree))
                return CaseSplit(branches=tuple(branches), parameters=qr_check.parameters)

            if not qr_check.full_rank:
                raise RankDeficientError(
                    f"La matrice A ({m}x{n}) n'est pas de rang plein en colonnes.",
                    rank=len(qr_check.d_sq),
                    ncols=n,
                )

            return self._solve_full_rank(self.A, self.b, qr_check, assumptions=self.assumptions)

    def _solve_full_rank(
        self,
        A_mat: Matrix,
        b_vec: Vector,
        qr_res: QRResult,
        *,
        assumptions: AssumptionsType,
    ) -> LSResult:
        m, n = A_mat.shape
        record(StepKind.CHECK, "ls.rank_check", level=1, rank=n, n=n)
        record(StepKind.INFO, "ls.pseudoinverse_note", level=2)

        if self.method == "rational_qr":
            Q_tilde = qr_res.Q_tilde
            R_tilde = qr_res.R_tilde
            d_sq = qr_res.d_sq
            with suspend_tracing():
                qt_b = Q_tilde.T @ b_vec
            rhs_entries = [
                _simplify_entry(qt_b[i] / d_sq[i]) for i in range(n)
            ]
            rhs_vec = Vector._from_exact(rhs_entries)
            record(
                StepKind.INFO,
                "ls.rational_qr_step",
                level=1,
                rhs=rhs_vec,
                snapshot={"matrix": R_tilde, "result": rhs_vec},
            )
            back_res = BackSubstitution(R_tilde, rhs_vec, assumptions=assumptions)._execute()
            if isinstance(back_res, CaseSplit):
                x_hat = back_res.generic().x
            else:
                x_hat = back_res.x

        elif self.method == "qr":
            Q = qr_res.Q
            R = qr_res.R
            with suspend_tracing():
                rhs_vec = Vector._from_exact(
                    _simplify_entry(e) for e in (Q.T @ b_vec).entries
                )
            record(
                StepKind.INFO,
                "ls.qr_step",
                level=1,
                rhs=rhs_vec,
                snapshot={"matrix": R, "result": rhs_vec},
            )
            back_res = BackSubstitution(R, rhs_vec, assumptions=assumptions)._execute()
            if isinstance(back_res, CaseSplit):
                x_hat = back_res.generic().x
            else:
                x_hat = back_res.x

        else:
            # method == "normal" : (A^T A) x_hat = A^T b via GaussJordan
            ata = A_mat.gram()
            atb = A_mat.T @ b_vec
            record(
                StepKind.INFO,
                "ls.normal_step",
                level=1,
                snapshot={"matrix": ata, "result": atb},
            )
            gj_res = GaussJordan(ata, atb, assumptions=assumptions)._execute()
            if isinstance(gj_res, CaseSplit):
                sol = gj_res.generic().solution
            else:
                sol = gj_res.solution
            if not isinstance(sol, UniqueSolution) or not isinstance(sol.x, Vector):
                raise RankDeficientError("Les équations normales n'ont pas une solution unique.")
            x_hat = sol.x

        x_hat = Vector._from_exact(_simplify_entry(e) for e in x_hat.entries)
        with suspend_tracing():
            y_hat = Vector._from_exact(
                _simplify_entry(e) for e in (A_mat @ x_hat).entries
            )
            # Convention : r_hat = A x_hat - b
            r_hat = Vector._from_exact(
                _simplify_entry(e) for e in (y_hat - b_vec).entries
            )
            norm_r = _simplify_entry(r_hat.norm())
            rms_r = _simplify_entry(r_hat.rms())

        record(
            StepKind.RESULT,
            "ls.analysis",
            level=1,
            x_hat=x_hat,
            y_hat=y_hat,
            r_hat=r_hat,
            snapshot={"result": x_hat},
        )
        record(
            StepKind.INFO,
            "ls.metrics",
            level=1,
            norm_r=norm_r,
            rms_r=rms_r,
        )

        return LSResult(
            A=A_mat,
            b=b_vec,
            x_hat=x_hat,
            y_hat=y_hat,
            r_hat=r_hat,
            residual_norm=norm_r,
            residual_rms=rms_r,
            method=self.method,
        )
