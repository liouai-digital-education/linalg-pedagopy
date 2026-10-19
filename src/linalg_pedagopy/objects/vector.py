"""Objet mathématique immuable Vector (§5.3.1, D5, D9, D10)."""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping, Sequence, overload

import sympy as sp
from sympy.polys.matrices import DomainMatrix

from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    UndefinedOperationError,
)
from linalg_pedagopy.core.field import choose_domain, match_symbol_substitutions, to_exact
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import current_tracer, record, section, suspend_tracing


class Vector:
    """Vecteur colonne immuable à coefficients exacts sur R (§5.3.1, D5)."""

    __slots__ = ("_entries", "_domain_matrix")

    def __init__(self, entries: Iterable[Any]) -> None:
        if getattr(entries, "_is_locked_tutor_proxy", False):
            entries = entries._unwrap_for_constructor("Vector(...)")  # type: ignore[attr-defined]
        if isinstance(entries, Vector):
            object.__setattr__(self, "_entries", entries._entries)
            object.__setattr__(self, "_domain_matrix", entries._domain_matrix)
            return
        if isinstance(entries, sp.MatrixBase):
            if entries.cols == 1 or entries.rows == 1:
                raw_list = list(entries)
            else:
                raise DimensionMismatchError(
                    f"Impossible de convertir une matrice {entries.rows}x{entries.cols} en Vector."
                )
        else:
            raw_list = list(entries)

        coerced = tuple(to_exact(x) for x in raw_list)
        object.__setattr__(self, "_entries", coerced)
        object.__setattr__(self, "_domain_matrix", None)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Vector est immuable (D5).")

    @classmethod
    def zeros(cls, n: int) -> Vector:
        """Vecteur nul de taille n."""
        if n < 0:
            raise ValueError("La dimension n doit être positive ou nulle.")
        return cls([sp.Integer(0)] * n)

    @classmethod
    def ones(cls, n: int) -> Vector:
        """Vecteur de 1 de taille n."""
        if n < 0:
            raise ValueError("La dimension n doit être positive ou nulle.")
        return cls([sp.Integer(1)] * n)

    @classmethod
    def unit(cls, i: int, n: int) -> Vector:
        """Vecteur canonique e_i de taille n (indice i à partir de 0 dans l'API Python, D9)."""
        if not (0 <= i < n):
            raise IndexError(f"Indice {i} hors bornes pour un vecteur de taille {n}.")
        items = [sp.Integer(1 if k == i else 0) for k in range(n)]
        return cls(items)

    @classmethod
    def combination(cls, vs: Sequence[Vector], cs: Sequence[Any]) -> Vector:
        """Calcule la combinaison linéaire sum_i c_i * v_i avec trace (§5.3.1)."""
        if len(vs) != len(cs):
            raise DimensionMismatchError(
                f"Nombre de vecteurs ({len(vs)}) différent du nombre de coefficients ({len(cs)})."
            )
        if not vs:
            raise ValueError("La liste de vecteurs ne peut pas être vide.")
        n = len(vs[0])
        for v in vs[1:]:
            if len(v) != n:
                raise DimensionMismatchError(
                    f"Tous les vecteurs doivent avoir la même taille ({n} vs {len(v)})."
                )
        scalars = [to_exact(c) for c in cs]
        with section(
            "vector.combination",
            level=2,
            snapshot={"vectors": tuple(vs), "coeffs": tuple(scalars)},
            count=len(vs),
            dim=n,
        ):
            acc = [sp.Integer(0)] * n
            for idx, (v, c) in enumerate(zip(vs, scalars), start=1):
                scaled = [sp.simplify(c * x) for x in v._entries]
                record(
                    StepKind.INFO,
                    "vector.combination_term",
                    level=3,
                    i=idx,
                    coeff=c,
                    vector=v,
                    scaled=cls._from_exact(scaled),
                )
                acc = [sp.simplify(a + s) for a, s in zip(acc, scaled)]
            res = cls._from_exact(acc)
            record(
                StepKind.RESULT,
                "vector.combination_result",
                level=2,
                snapshot={"result": res},
                result=res,
            )
            return res

    @classmethod
    def _from_exact(cls, entries: Iterable[sp.Expr]) -> Vector:
        obj = object.__new__(cls)
        object.__setattr__(obj, "_entries", tuple(entries))
        object.__setattr__(obj, "_domain_matrix", None)
        return obj

    @property
    def entries(self) -> tuple[sp.Expr, ...]:
        return self._entries

    @property
    def size(self) -> int:
        return len(self._entries)

    @property
    def shape(self) -> tuple[int, int]:
        """Un Vector est vu comme une matrice colonne n x 1 (§5.3.2)."""
        return (len(self._entries), 1)

    @property
    def rows(self) -> int:
        return len(self._entries)

    @property
    def cols(self) -> int:
        return 1

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[sp.Expr]:
        return iter(self._entries)

    @overload
    def __getitem__(self, index: int) -> sp.Expr: ...

    @overload
    def __getitem__(self, index: slice) -> Vector: ...

    def __getitem__(self, index: int | slice) -> sp.Expr | Vector:
        if isinstance(index, slice):
            return Vector._from_exact(self._entries[index])
        return self._entries[index]

    def to_sympy(self) -> sp.Matrix:
        """Convertit le vecteur en matrice colonne SymPy n x 1."""
        return sp.Matrix([[e] for e in self._entries])

    def to_domain_matrix(self) -> DomainMatrix:
        """Convertit le vecteur en DomainMatrix n x 1 sur le plus petit domaine exact (D10)."""
        dm = self._domain_matrix
        if dm is None:
            dom = choose_domain(self._entries)
            rows_dom = [[dom.from_sympy(e)] for e in self._entries]
            dm = DomainMatrix(rows_dom, (len(self._entries), 1), dom)
            object.__setattr__(self, "_domain_matrix", dm)
        return dm

    def subs(self, mapping: Mapping[Any, Any]) -> Vector:
        """Substitue des symboles par des valeurs et renvoie un nouveau Vector."""
        free: set[sp.Symbol] = set()
        for e in self._entries:
            free |= {s for s in e.free_symbols if isinstance(s, sp.Symbol)}
        sym_map = match_symbol_substitutions(free, mapping)
        return Vector._from_exact(
            sp.simplify(e.xreplace(sym_map)) for e in self._entries
        )

    def _check_same_size(self, other: Vector) -> None:
        if not isinstance(other, Vector):
            raise TypeError(f"Attendu Vector, reçu {type(other).__name__}.")
        if len(self._entries) != len(other._entries):
            raise DimensionMismatchError(
                f"Tailles de vecteurs incompatibles : {len(self._entries)} et {len(other._entries)}."
            )

    def __add__(self, other: Vector) -> Vector:
        if not isinstance(other, Vector):
            return NotImplemented
        self._check_same_size(other)
        with section("vector.add", level=2, u=self, v=other):
            res_entries: list[sp.Expr] = []
            for idx, (a, b) in enumerate(zip(self._entries, other._entries), start=1):
                val = sp.simplify(a + b)
                record(
                    StepKind.INFO,
                    "vector.add_comp",
                    level=3,
                    i=idx,
                    a=a,
                    b=b,
                    val=val,
                )
                res_entries.append(val)
            res = Vector._from_exact(res_entries)
            record(StepKind.RESULT, "vector.add_result", level=2, result=res)
            return res

    def __sub__(self, other: Vector) -> Vector:
        if not isinstance(other, Vector):
            return NotImplemented
        self._check_same_size(other)
        with section("vector.sub", level=2, u=self, v=other):
            res_entries: list[sp.Expr] = []
            for idx, (a, b) in enumerate(zip(self._entries, other._entries), start=1):
                val = sp.simplify(a - b)
                record(
                    StepKind. SUBTRACT,
                    "vector.sub_comp",
                    level=3,
                    i=idx,
                    a=a,
                    b=b,
                    val=val,
                )
                res_entries.append(val)
            res = Vector._from_exact(res_entries)
            record(StepKind.RESULT, "vector.sub_result", level=2, result=res)
            return res

    def __neg__(self) -> Vector:
        return Vector._from_exact(-e for e in self._entries)

    def __mul__(self, scalar: Any) -> Vector:
        try:
            c = to_exact(scalar)
        except TypeError:
            return NotImplemented
        with section("vector.scale", level=2, scalar=c, v=self):
            res_entries: list[sp.Expr] = []
            for idx, a in enumerate(self._entries, start=1):
                val = sp.simplify(c * a)
                record(
                    StepKind.INFO,
                    "vector.scale_comp",
                    level=3,
                    i=idx,
                    scalar=c,
                    a=a,
                    val=val,
                )
                res_entries.append(val)
            res = Vector._from_exact(res_entries)
            record(StepKind.RESULT, "vector.scale_result", level=2, result=res)
            return res

    def __rmul__(self, scalar: Any) -> Vector:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> Vector:
        c = to_exact(scalar)
        dec = oracle.decide(c)
        if dec.verdict == Verdict.ZERO:
            raise UndefinedOperationError("Division d'un vecteur par le scalaire nul.")
        return self * (sp.Integer(1) / c)

    def dot(self, other: Vector) -> sp.Expr:
        """Produit scalaire u^T v = sum_i u_i * v_i (§5.3.1)."""
        self._check_same_size(other)
        with section("vector.dot", level=2, u=self, v=other):
            terms: list[sp.Expr] = []
            for idx, (a, b) in enumerate(zip(self._entries, other._entries), start=1):
                prod = sp.simplify(a * b)
                terms.append(prod)
                record(
                    StepKind.DOT,
                    "vector.dot_term",
                    level=3,
                    i=idx,
                    a=a,
                    b=b,
                    prod=prod,
                )
            total = sp.simplify(sum(terms, sp.Integer(0)))
            record(
                StepKind.DOT,
                "vector.dot_result",
                level=2,
                terms=tuple(terms),
                result=total,
            )
            return total

    def norm_sq(self) -> sp.Expr:
        """Carré de la norme euclidienne ||v||^2 = v^T v."""
        with suspend_tracing():
            return sp.simplify(sum((e**2 for e in self._entries), sp.Integer(0)))

    def norm(self) -> sp.Expr:
        """Norme euclidienne ||v|| = sqrt(sum_i v_i^2) (§5.3.1)."""
        with section("vector.norm", level=2, v=self):
            squares = [sp.simplify(e**2) for e in self._entries]
            sum_sq = sp.simplify(sum(squares, sp.Integer(0)))
            record(
                StepKind.NORM,
                "vector.norm_squares",
                level=3,
                squares=tuple(squares),
                sum_sq=sum_sq,
            )
            res = sp.simplify(sp.sqrt(sum_sq))
            record(StepKind.NORM, "vector.norm_result", level=2, sum_sq=sum_sq, result=res)
            return res

    def rms(self) -> sp.Expr:
        """Moyenne quadratique rms(v) = ||v|| / sqrt(n) (VMLS ch. 1, D9)."""
        n = len(self._entries)
        if n == 0:
            raise UndefinedOperationError("rms() n'est pas défini sur un vecteur vide.")
        with section("vector.rms", level=2, v=self, n=n):
            nrm = self.norm()
            res = sp.simplify(nrm / sp.sqrt(sp.Integer(n)))
            record(
                StepKind.RESULT,
                "vector.rms_result",
                level=2,
                norm=nrm,
                n=n,
                result=res,
            )
            return res

    def avg(self) -> sp.Expr:
        """Moyenne arithmétique avg(v) = (1/n) * sum_i v_i (VMLS ch. 1)."""
        n = len(self._entries)
        if n == 0:
            raise UndefinedOperationError("avg() n'est pas défini sur un vecteur vide.")
        with section("vector.avg", level=2, v=self, n=n):
            total = sp.simplify(sum(self._entries, sp.Integer(0)))
            res = sp.simplify(total / sp.Integer(n))
            record(
                StepKind.RESULT,
                "vector.avg_result",
                level=2,
                total=total,
                n=n,
                result=res,
            )
            return res

    def demean(self) -> Vector:
        """Vecteur centré v - avg(v)*1 (de-meaned vector, VMLS ch. 3)."""
        n = len(self._entries)
        if n == 0:
            return self
        with section("vector.demean", level=2, v=self):
            mean = self.avg()
            res = Vector._from_exact(sp.simplify(e - mean) for e in self._entries)
            record(
                StepKind.RESULT,
                "vector.demean_result",
                level=2,
                mean=mean,
                result=res,
            )
            return res

    def std(self) -> sp.Expr:
        """Écart type std(v) = rms(v - avg(v)*1) (convention VMLS en 1/sqrt(n), ch. 3)."""
        n = len(self._entries)
        if n == 0:
            raise UndefinedOperationError("std() n'est pas défini sur un vecteur vide.")
        with section("vector.std", level=2, v=self, n=n):
            centered = self.demean()
            res = centered.rms()
            record(
                StepKind.RESULT,
                "vector.std_result",
                level=2,
                centered=centered,
                result=res,
            )
            return res

    def distance(self, other: Vector) -> sp.Expr:
        """Distance euclidienne ||u - v|| (§5.3.1)."""
        self._check_same_size(other)
        with section("vector.distance", level=2, u=self, v=other):
            diff = self - other
            dist = diff.norm()
            record(
                StepKind.RESULT,
                "vector.distance_result",
                level=2,
                diff=diff,
                result=dist,
            )
            return dist

    def angle(self, other: Vector) -> sp.Expr:
        """Angle en radians arccos(u^T v / (||u|| ||v||)) avec vérification de Cauchy-Schwarz (§5.3.1)."""
        self._check_same_size(other)
        if self.is_zero() is True or other.is_zero() is True:
            raise UndefinedOperationError(
                "L'angle avec un vecteur nul n'est pas défini."
            )
        with section("vector.angle", level=2, u=self, v=other):
            ip = self.dot(other)
            nu = self.norm()
            nv = other.norm()
            denom = sp.simplify(nu * nv)
            if oracle.decide(denom).verdict == Verdict.ZERO:
                raise UndefinedOperationError(
                    "L'angle avec un vecteur de norme nulle n'est pas défini."
                )
            cos_theta = sp.simplify(ip / denom)
            record(
                StepKind.CHECK,
                "vector.cauchy_schwarz",
                level=2,
                inner=ip,
                norm_prod=denom,
                cos_theta=cos_theta,
            )
            theta = sp.simplify(sp.acos(cos_theta))
            record(
                StepKind.RESULT,
                "vector.angle_result",
                level=2,
                cos_theta=cos_theta,
                result=theta,
            )
            return theta

    def correlation(self, other: Vector) -> sp.Expr:
        """Coefficient de corrélation de VMLS ch. 3 : (u_tilde^T v_tilde) / (||u_tilde|| ||v_tilde||)."""
        self._check_same_size(other)
        with section("vector.correlation", level=2, u=self, v=other):
            du = self.demean()
            dv = other.demean()
            nu = du.norm()
            nv = dv.norm()
            if oracle.decide(nu).verdict == Verdict.ZERO or oracle.decide(nv).verdict == Verdict.ZERO:
                raise UndefinedOperationError(
                    "La corrélation n'est pas définie pour un vecteur constant (écart type nul)."
                )
            res = sp.simplify(du.dot(dv) / (nu * nv))
            record(StepKind.RESULT, "vector.correlation_result", level=2, result=res)
            return res

    def is_zero(self, assumptions: AssumptionsType = None) -> bool | CaseSplit[bool]:
        """Teste si le vecteur est nul via ZeroOracle ; peut renvoyer un CaseSplit[bool] (§5.3.1)."""
        cond_zero = Condition.true()
        has_conditional = False
        for e in self._entries:
            dec = oracle.decide(e, assumptions=assumptions)
            if dec.verdict == Verdict.NONZERO:
                return False
            if dec.verdict == Verdict.CONDITIONAL and dec.condition is not None:
                has_conditional = True
                cond_zero = cond_zero & dec.condition
            elif dec.verdict == Verdict.UNKNOWN:
                # Re-lève UndecidableZeroError via oracle.is_zero
                oracle.is_zero(e, assumptions=assumptions)

        if not has_conditional:
            return True

        # Si certaines composantes dépendent d'un paramètre :
        # Si cond_zero a des égalités contradictoires (ex. a = 1 et a = 2), le vecteur n'est jamais nul
        subs_map = cond_zero.substitutions()
        for e in self._entries:
            if oracle.decide(e.xreplace(subs_map)).verdict == Verdict.NONZERO:
                return False

        # Sinon on construit un CaseSplit[bool] : générique False, particulier True
        neg_cond = Condition(
            eqs=(),
            neqs=cond_zero.eqs,
        )
        branches = (
            Branch(condition=neg_cond, result=False, trace=None),
            Branch(condition=cond_zero, result=True, trace=None),
        )
        return CaseSplit(branches=branches)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        if len(self._entries) != len(other._entries):
            return False
        with suspend_tracing():
            for a, b in zip(self._entries, other._entries):
                dec = oracle.decide(a - b, trace_level3=False)
                if dec.verdict != Verdict.ZERO:
                    return False
        return True

    def __hash__(self) -> int:
        return hash(self._entries)

    def __repr__(self) -> str:
        items = ", ".join(str(e) for e in self._entries)
        return f"Vector([{items}])"

    def __str__(self) -> str:
        items = ", ".join(str(e) for e in self._entries)
        return f"({items})"

    def _repr_latex_(self) -> str:
        """Rendu LaTeX pour JupyterLab (§5.5)."""
        rows_tex = " \\\\ ".join(sp.latex(e) for e in self._entries)
        return f"$\\left[\\begin{{array}}{{c}} {rows_tex} \\end{{array}}\\right]$"
