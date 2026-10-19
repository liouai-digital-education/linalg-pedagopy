"""Algorithme de Gram-Schmidt (variante rationnelle normalize='end' et VMLS normalize='each', §5.4.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

import sympy as sp

from linalg_pedagopy.algorithms.base import Procedure, Result
from linalg_pedagopy.algorithms.gauss_jordan import _simplify_entry
from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    LinearDependenceError,
)
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle, _normalize_assumptions
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing, tracing

NormalizeMode = Literal["end", "each"]


@dataclass(frozen=True)
class DependenceWitness:
    """Témoin exact de dépendance linéaire pour Gram-Schmidt (§5.4.4, D8)."""

    index: int  # indice 0-based du vecteur dépendant a_i
    q_tilde_coeffs: tuple[sp.Expr, ...]  # coefficients r_tilde_{j, i} tels que a_i = sum_{j<i} r_tilde_{j,i} q_tilde_j
    a_coeffs: tuple[sp.Expr, ...]  # coefficients c_j tels que a_i = sum_{j<i} c_j a_j
    expression: str

    def __str__(self) -> str:
        return self.expression


@dataclass(frozen=True)
class GSResult(Result):
    """Résultat typé de l'algorithme de Gram-Schmidt (§5.4.4, D8)."""

    independent: bool = True
    vectors: tuple[Vector, ...] = ()
    orthogonal: tuple[Vector, ...] = ()  # vecteurs orthogonaux q_tilde_i
    orthonormal: tuple[Vector, ...] = ()  # vecteurs orthonormés q_i
    r_tilde: Matrix = Matrix([])  # matrice triangulaire supérieure unitaire R_tilde
    d_sq: tuple[sp.Expr, ...] = ()  # normes au carré ||q_tilde_i||^2
    dependent_index: int | None = None
    witness: DependenceWitness | None = None

    @property
    def Q(self) -> Matrix:
        """Matrice Q dont les colonnes sont les vecteurs orthonormés."""
        if not self.orthonormal:
            return Matrix([])
        return Matrix.from_columns(self.orthonormal)

    @property
    def Q_tilde(self) -> Matrix:
        """Matrice Q_tilde dont les colonnes sont les vecteurs orthogonaux rationnels."""
        if not self.orthogonal:
            return Matrix([])
        return Matrix.from_columns(self.orthogonal)

    def subs(self, mapping: Mapping[Any, Any]) -> GSResult:
        sym_map = {
            (sp.Symbol(k, real=True) if isinstance(k, str) else k): v
            for k, v in mapping.items()
        }
        return GSResult(
            trace=self.trace,
            independent=self.independent,
            vectors=tuple(v.subs(mapping) for v in self.vectors),
            orthogonal=tuple(v.subs(mapping) for v in self.orthogonal),
            orthonormal=tuple(v.subs(mapping) for v in self.orthonormal),
            r_tilde=self.r_tilde.subs(mapping) if self.r_tilde.rows > 0 else Matrix([]),
            d_sq=tuple(sp.simplify(e.xreplace(sym_map)) for e in self.d_sq),
            dependent_index=self.dependent_index,
            witness=self.witness,
        )

    def _branch_summary_lines(self) -> list[str]:
        if self.independent:
            return [f"famille libre ({len(self.orthonormal)} vecteurs orthonormés)"]
        return [
            f"famille liée (a_{(self.dependent_index or 0) + 1} dépendant, témoin : {self.witness})"
        ]

    def _run_verification(self) -> None:
        with section("gs.verify", level=1):
            if self.independent and self.orthonormal:
                Q_mat = self.Q
                Q_mat.has_orthonormal_columns()
            elif self.witness is not None and self.dependent_index is not None:
                idx = self.dependent_index
                with suspend_tracing():
                    comb = Vector.combination(
                        self.orthogonal[:idx], self.witness.q_tilde_coeffs
                    )
                    diff = self.vectors[idx] - comb
                record(
                    StepKind.CHECK,
                    "gj.verify_ok",
                    level=1,
                    detail=f"Témoin vérifié : a_{idx + 1} - comb = {diff}",
                )


class GramSchmidt(Procedure[GSResult]):
    """Procédure d'orthogonalisation de Gram-Schmidt (§5.4.4)."""

    def __init__(
        self,
        vectors: Sequence[Vector | Sequence[Any]] | Matrix,
        *,
        normalize: NormalizeMode = "end",
        strict: bool = False,
        assumptions: AssumptionsType = None,
    ) -> None:
        if isinstance(vectors, Matrix):
            vec_list = list(vectors.columns())
        else:
            vec_list = [v if isinstance(v, Vector) else Vector(v) for v in vectors]

        if not vec_list:
            raise ValueError("La famille de vecteurs ne peut pas être vide.")
        m = len(vec_list[0])
        for idx, v in enumerate(vec_list):
            if len(v) != m:
                raise DimensionMismatchError(
                    f"Le vecteur {idx + 1} est de taille {len(v)}, attendu {m}."
                )
        if normalize not in ("end", "each"):
            raise ValueError(f"Mode de normalisation inconnu : {normalize!r}")

        self.vectors = tuple(vec_list)
        self.normalize: NormalizeMode = normalize
        self.strict = strict
        self.assumptions = _normalize_assumptions(assumptions)

    def _execute(self) -> GSResult | CaseSplit[GSResult]:
        return self._run_gs(self.assumptions, depth=0)

    def _run_gs(self, cond: Condition, *, depth: int) -> GSResult | CaseSplit[GSResult]:
        subs_map = cond.substitutions()
        vecs = tuple(v.subs(subs_map) if subs_map else v for v in self.vectors)
        k = len(vecs)
        m = len(vecs[0])

        with section(
            "gs.start",
            level=1,
            k=k,
            m=m,
            mode=self.normalize,
        ):
            q_tildes: list[Vector] = []
            q_units: list[Vector] = []
            d_sq_list: list[sp.Expr] = []
            r_tilde_grid = [
                [sp.Integer(1 if i == j else 0) for j in range(k)] for i in range(k)
            ]

            for i in range(k):
                a_i = vecs[i]
                with section("gs.vector_step", level=1, i=i + 1, a_i=a_i):
                    if self.normalize == "end":
                        q_tilde_entries = list(a_i.entries)
                        coeffs_i: list[sp.Expr] = []
                        for j in range(i):
                            with suspend_tracing():
                                num = q_tildes[j].dot(a_i)
                                den = d_sq_list[j]
                            r_ji = _simplify_entry(num / den)
                            r_tilde_grid[j][i] = r_ji
                            coeffs_i.append(r_ji)
                            record(
                                StepKind.PROJECTION,
                                "gs.proj_coeff",
                                level=2,
                                j=j + 1,
                                i=i + 1,
                                coeff=r_ji,
                            )
                            q_tilde_entries = [
                                _simplify_entry(q_tilde_entries[row] - r_ji * q_tildes[j][row])
                                for row in range(m)
                            ]
                        q_tilde = Vector._from_exact(q_tilde_entries)
                    else:
                        # normalize == "each" (algorithme de VMLS tel quel)
                        q_tilde_entries = list(a_i.entries)
                        coeffs_i = []
                        for j in range(i):
                            with suspend_tracing():
                                r_ji_unit = _simplify_entry(q_units[j].dot(a_i))
                                num_rat = q_tildes[j].dot(a_i)
                                den_rat = d_sq_list[j]
                            r_ji_rat = _simplify_entry(num_rat / den_rat)
                            r_tilde_grid[j][i] = r_ji_rat
                            coeffs_i.append(r_ji_rat)
                            record(
                                StepKind.PROJECTION,
                                "gs.proj_coeff_unit",
                                level=2,
                                j=j + 1,
                                i=i + 1,
                                coeff=r_ji_unit,
                            )
                            q_tilde_entries = [
                                _simplify_entry(q_tilde_entries[row] - r_ji_unit * q_units[j][row])
                                for row in range(m)
                            ]
                        q_tilde = Vector._from_exact(q_tilde_entries)

                    record(
                        StepKind.SUBTRACT,
                        "gs.subtract",
                        level=2,
                        i=i + 1,
                        q_tilde=q_tilde,
                        snapshot={"result": q_tilde},
                    )

                    # Test de nullité de ||q_tilde_i||^2 via ZeroOracle
                    norm_sq = _simplify_entry(q_tilde.norm_sq())
                    dec = oracle.decide(norm_sq, assumptions=cond)

                    if dec.verdict == Verdict.CONDITIONAL and dec.factors:
                        return self._split_gs(cond, dec.factors, depth=depth)

                    if dec.verdict == Verdict.UNKNOWN:
                        oracle.is_zero(norm_sq, assumptions=cond)

                    if dec.verdict == Verdict.ZERO:
                        # Dépendance linéaire détectée ! Construction du témoin
                        witness = self._build_witness(i, coeffs_i, r_tilde_grid)
                        record(
                            StepKind.RESULT,
                            "gs.dependent",
                            level=1,
                            i=i + 1,
                            witness=witness.expression,
                        )
                        if self.strict:
                            raise LinearDependenceError(
                                f"a_{i + 1} est combinaison linéaire des vecteurs précédents ({witness.expression}).",
                                index=i,
                                witness=witness,
                            )
                        return GSResult(
                            independent=False,
                            vectors=vecs,
                            orthogonal=tuple(q_tildes),
                            orthonormal=tuple(q_units),
                            r_tilde=Matrix._from_exact_rows(
                                [r[: len(q_tildes)] for r in r_tilde_grid[: len(q_tildes)]]
                            )
                            if q_tildes
                            else Matrix([]),
                            d_sq=tuple(d_sq_list),
                            dependent_index=i,
                            witness=witness,
                        )

                    q_tildes.append(q_tilde)
                    d_sq_list.append(norm_sq)

                    if self.normalize == "each":
                        norm_val = _simplify_entry(sp.sqrt(norm_sq))
                        if any(
                            sub.is_Pow and not sub.exp.is_Integer
                            for sub in norm_val.atoms(sp.Pow)
                        ):
                            record(
                                StepKind.WARNING,
                                "gs.radical_warning",
                                level=2,
                                i=i + 1,
                            )
                        q_unit = Vector._from_exact(
                            _simplify_entry(e / norm_val) for e in q_tilde.entries
                        )
                        q_units.append(q_unit)
                        record(
                            StepKind.NORMALIZE,
                            "gs.normalize_step",
                            level=1,
                            i=i + 1,
                            norm=norm_val,
                            q=q_unit,
                            snapshot={"result": q_unit},
                        )

            # Si normalize == "end", on normalise tous les vecteurs à la fin
            if self.normalize == "end":
                with section("gs.end_normalize", level=1, k=k):
                    for idx, (qt, dsq) in enumerate(zip(q_tildes, d_sq_list), start=1):
                        norm_val = _simplify_entry(sp.sqrt(dsq))
                        q_unit = Vector._from_exact(
                            _simplify_entry(e / norm_val) for e in qt.entries
                        )
                        q_units.append(q_unit)
                        record(
                            StepKind.NORMALIZE,
                            "gs.normalize_step",
                            level=2,
                            i=idx,
                            norm=norm_val,
                            q=q_unit,
                            snapshot={"result": q_unit},
                        )

            record(StepKind.RESULT, "gs.summary_indep", level=1, k=k)
            return GSResult(
                independent=True,
                vectors=vecs,
                orthogonal=tuple(q_tildes),
                orthonormal=tuple(q_units),
                r_tilde=Matrix._from_exact_rows(r_tilde_grid),
                d_sq=tuple(d_sq_list),
                dependent_index=None,
                witness=None,
            )

    def _split_gs(
        self,
        cond: Condition,
        factors: tuple[sp.Expr, ...],
        *,
        depth: int,
    ) -> CaseSplit[GSResult]:
        gen_cond = cond
        for fac in factors:
            gen_cond = gen_cond & Condition.from_zero_expr(fac, is_zero=False)
        branches: list[Branch[GSResult]] = []

        with tracing(level=3) as t_gen:
            gen_res = self._run_gs(gen_cond, depth=depth + 1)
        if isinstance(gen_res, CaseSplit):
            branches.extend(gen_res.branches)
        else:
            object.__setattr__(gen_res, "trace", t_gen.tree)
            branches.append(Branch(gen_cond, gen_res, t_gen.tree))

        for fac in factors:
            part_cond = cond & Condition.from_zero_expr(fac, is_zero=True)
            with tracing(level=3) as t_part:
                part_res = self._run_gs(part_cond, depth=depth + 1)
            if isinstance(part_res, CaseSplit):
                branches.extend(part_res.branches)
            else:
                object.__setattr__(part_res, "trace", t_part.tree)
                branches.append(Branch(part_cond, part_res, t_part.tree))

        return CaseSplit(branches=tuple(branches))

    @staticmethod
    def _build_witness(
        i: int,
        q_tilde_coeffs: list[sp.Expr],
        r_tilde_grid: list[list[sp.Expr]],
    ) -> DependenceWitness:
        # Calcul des coefficients sur les vecteurs d'origine a_0 .. a_{i-1}
        # comme A_{:, :i} = Q_tilde_{:, :i} * R_tilde_{:i, :i}, on résout R_tilde_{:i, :i} * c = q_tilde_coeffs
        a_coeffs = list(q_tilde_coeffs)
        for row in range(i - 1, -1, -1):
            s = sum(
                (r_tilde_grid[row][col] * a_coeffs[col] for col in range(row + 1, i)),
                sp.Integer(0),
            )
            a_coeffs[row] = _simplify_entry(a_coeffs[row] - s)

        terms_q: list[str] = []
        for j, c in enumerate(q_tilde_coeffs):
            if c != 0:
                terms_q.append(f"({c})·q̃_{j + 1}" if c != 1 else f"q̃_{j + 1}")
        rhs_str = " + ".join(terms_q) if terms_q else "0"
        expr_str = f"a_{i + 1} = {rhs_str}"
        return DependenceWitness(
            index=i,
            q_tilde_coeffs=tuple(q_tilde_coeffs),
            a_coeffs=tuple(a_coeffs),
            expression=expr_str,
        )
