"""Objet mathématique immuable Matrix (§5.3.2, D5, D9, D10)."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, Literal, Mapping, Sequence, overload

import sympy as sp
from sympy.polys.matrices import DomainMatrix

from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    UndefinedOperationError,
)
from linalg_pedagopy.core.field import choose_domain, to_exact
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing

MatmulView = Literal["entries", "rows", "columns", "outer"]

# Hook optionnel enregistré par le module algorithms pour déléguer à GaussJordan sans import montant
_gauss_jordan_factory: Callable[..., Any] | None = None


def register_gauss_jordan_hook(factory: Callable[..., Any]) -> None:
    """Enregistre la fabrique GaussJordan pour les méthodes déléguées de Matrix."""
    global _gauss_jordan_factory
    _gauss_jordan_factory = factory


class Matrix:
    """Matrice immuable m x n à coefficients exacts sur R (§5.3.2, D5)."""

    __slots__ = ("_rows", "_nrows", "_ncols", "_domain_matrix")

    def __init__(self, data: Iterable[Any]) -> None:
        if isinstance(data, Matrix):
            object.__setattr__(self, "_rows", data._rows)
            object.__setattr__(self, "_nrows", data._nrows)
            object.__setattr__(self, "_ncols", data._ncols)
            object.__setattr__(self, "_domain_matrix", data._domain_matrix)
            return

        if isinstance(data, Vector):
            rows_tuple = tuple((e,) for e in data.entries)
            object.__setattr__(self, "_rows", rows_tuple)
            object.__setattr__(self, "_nrows", len(rows_tuple))
            object.__setattr__(self, "_ncols", 1 if rows_tuple else 0)
            object.__setattr__(self, "_domain_matrix", None)
            return

        if isinstance(data, sp.MatrixBase):
            m, n = data.rows, data.cols
            rows_tuple = tuple(
                tuple(to_exact(data[i, j]) for j in range(n)) for i in range(m)
            )
            object.__setattr__(self, "_rows", rows_tuple)
            object.__setattr__(self, "_nrows", m)
            object.__setattr__(self, "_ncols", n)
            object.__setattr__(self, "_domain_matrix", None)
            return

        raw_rows = [list(r) for r in data]
        if not raw_rows:
            object.__setattr__(self, "_rows", ())
            object.__setattr__(self, "_nrows", 0)
            object.__setattr__(self, "_ncols", 0)
            object.__setattr__(self, "_domain_matrix", None)
            return

        ncols = len(raw_rows[0])
        for idx, r in enumerate(raw_rows):
            if len(r) != ncols:
                raise DimensionMismatchError(
                    f"Ligne {idx + 1} de longueur {len(r)}, attendu {ncols}."
                )
        rows_tuple = tuple(tuple(to_exact(x) for x in r) for r in raw_rows)
        object.__setattr__(self, "_rows", rows_tuple)
        object.__setattr__(self, "_nrows", len(rows_tuple))
        object.__setattr__(self, "_ncols", ncols)
        object.__setattr__(self, "_domain_matrix", None)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Matrix est immuable (D5).")

    @classmethod
    def _from_exact_rows(cls, rows: Sequence[Sequence[sp.Expr]]) -> Matrix:
        obj = object.__new__(cls)
        rows_tuple = tuple(tuple(r) for r in rows)
        nrows = len(rows_tuple)
        ncols = len(rows_tuple[0]) if nrows > 0 else 0
        object.__setattr__(obj, "_rows", rows_tuple)
        object.__setattr__(obj, "_nrows", nrows)
        object.__setattr__(obj, "_ncols", ncols)
        object.__setattr__(obj, "_domain_matrix", None)
        return obj

    @classmethod
    def from_rows(cls, rows: Sequence[Vector | Sequence[Any]]) -> Matrix:
        """Construit une matrice à partir d'une liste de vecteurs-lignes ou séquences."""
        if not rows:
            return cls([])
        converted = [list(r.entries) if isinstance(r, Vector) else list(r) for r in rows]
        return cls(converted)

    @classmethod
    def from_columns(cls, columns: Sequence[Vector | Sequence[Any]]) -> Matrix:
        """Construit une matrice à partir d'une liste de vecteurs-colonnes (§5.3.2)."""
        if not columns:
            return cls([])
        col_vecs = [c if isinstance(c, Vector) else Vector(c) for c in columns]
        m = len(col_vecs[0])
        for idx, col in enumerate(col_vecs):
            if len(col) != m:
                raise DimensionMismatchError(
                    f"Colonne {idx + 1} de taille {len(col)}, attendu {m}."
                )
        n = len(col_vecs)
        rows = [[col_vecs[j][i] for j in range(n)] for i in range(m)]
        return cls._from_exact_rows(rows)

    @classmethod
    def zeros(cls, m: int, n: int | None = None) -> Matrix:
        """Matrice nulle de taille m x n (ou m x m si n est omis)."""
        ncols = m if n is None else n
        if m < 0 or ncols < 0:
            raise ValueError("Les dimensions d'une matrice doivent être positives ou nulles.")
        if m == 0 or ncols == 0:
            obj = object.__new__(cls)
            object.__setattr__(obj, "_rows", ())
            object.__setattr__(obj, "_nrows", m)
            object.__setattr__(obj, "_ncols", ncols)
            object.__setattr__(obj, "_domain_matrix", None)
            return obj
        z = sp.Integer(0)
        return cls._from_exact_rows([[z] * ncols for _ in range(m)])

    @classmethod
    def ones(cls, m: int, n: int | None = None) -> Matrix:
        """Matrice de 1 de taille m x n."""
        ncols = m if n is None else n
        one = sp.Integer(1)
        return cls._from_exact_rows([[one] * ncols for _ in range(m)])

    @classmethod
    def identity(cls, n: int) -> Matrix:
        """Matrice identité I_n de taille n x n (§5.3.2)."""
        if n < 0:
            raise ValueError("La dimension n doit être positive ou nulle.")
        z, one = sp.Integer(0), sp.Integer(1)
        return cls._from_exact_rows(
            [[one if i == j else z for j in range(n)] for i in range(n)]
        )

    @classmethod
    def diag(cls, diagonal: Iterable[Any]) -> Matrix:
        """Matrice diagonale à partir d'une séquence de coefficients."""
        vals = [to_exact(x) for x in diagonal]
        n = len(vals)
        z = sp.Integer(0)
        return cls._from_exact_rows(
            [[vals[i] if i == j else z for j in range(n)] for i in range(n)]
        )

    @classmethod
    def block(cls, blocks: Sequence[Sequence[Matrix | Vector | int]]) -> Matrix:
        """Construit une matrice par blocs (§5.3.2).

        Un entier 0 dans un bloc est remplacé par une matrice nulle aux dimensions compatibles.
        """
        if not blocks or not blocks[0]:
            return cls([])
        b_rows = len(blocks)
        b_cols = len(blocks[0])
        for br in blocks:
            if len(br) != b_cols:
                raise DimensionMismatchError("Grille de blocs irrégulière.")

        # Conversion des Vector en Matrix colonne
        grid: list[list[Matrix | int]] = []
        for br in blocks:
            row_list: list[Matrix | int] = []
            for item in br:
                if isinstance(item, Vector):
                    row_list.append(Matrix(item))
                elif isinstance(item, Matrix):
                    row_list.append(item)
                elif isinstance(item, int) and item == 0:
                    row_list.append(0)
                else:
                    row_list.append(Matrix([[to_exact(item)]]))
            grid.append(row_list)

        # Détermination des hauteurs de lignes de blocs et largeurs de colonnes de blocs
        row_heights: list[int | None] = [None] * b_rows
        col_widths: list[int | None] = [None] * b_cols

        for i in range(b_rows):
            for j in range(b_cols):
                item = grid[i][j]
                if isinstance(item, Matrix):
                    if row_heights[i] is None:
                        row_heights[i] = item.rows
                    elif row_heights[i] != item.rows:
                        raise DimensionMismatchError(
                            f"Hauteur incohérente dans la ligne de blocs {i + 1} : {row_heights[i]} vs {item.rows}."
                        )
                    if col_widths[j] is None:
                        col_widths[j] = item.cols
                    elif col_widths[j] != item.cols:
                        raise DimensionMismatchError(
                            f"Largeur incohérente dans la colonne de blocs {j + 1} : {col_widths[j]} vs {item.cols}."
                        )

        heights = [h if h is not None else 1 for h in row_heights]
        widths = [w if w is not None else 1 for w in col_widths]

        full_rows: list[list[sp.Expr]] = []
        for i in range(b_rows):
            h = heights[i]
            resolved_row_blocks: list[Matrix] = []
            for j in range(b_cols):
                w = widths[j]
                item = grid[i][j]
                if isinstance(item, int):
                    resolved_row_blocks.append(cls.zeros(h, w))
                else:
                    resolved_row_blocks.append(item)
            for local_r in range(h):
                combined: list[sp.Expr] = []
                for blk in resolved_row_blocks:
                    combined.extend(blk._rows[local_r])
                full_rows.append(combined)

        return cls._from_exact_rows(full_rows)

    @property
    def rows(self) -> int:
        return self._nrows

    @property
    def cols(self) -> int:
        return self._ncols

    @property
    def shape(self) -> tuple[int, int]:
        return (self._nrows, self._ncols)

    @property
    def entries_grid(self) -> tuple[tuple[sp.Expr, ...], ...]:
        return self._rows

    @property
    def flat_entries(self) -> tuple[sp.Expr, ...]:
        return tuple(e for r in self._rows for e in r)

    def row(self, i: int) -> Vector:
        """Renvoie la ligne i (0-based) sous forme de Vector."""
        if not (0 <= i < self._nrows):
            raise IndexError(f"Indice de ligne {i} hors bornes (0..{self._nrows - 1}).")
        return Vector._from_exact(self._rows[i])

    def col(self, j: int) -> Vector:
        """Renvoie la colonne j (0-based) sous forme de Vector."""
        if not (0 <= j < self._ncols):
            raise IndexError(f"Indice de colonne {j} hors bornes (0..{self._ncols - 1}).")
        return Vector._from_exact(self._rows[i][j] for i in range(self._nrows))

    def columns(self) -> tuple[Vector, ...]:
        """Renvoie le tuple des vecteurs-colonnes de la matrice."""
        return tuple(self.col(j) for j in range(self._ncols))

    def rows_as_vectors(self) -> tuple[Vector, ...]:
        """Renvoie le tuple des vecteurs-lignes de la matrice."""
        return tuple(self.row(i) for i in range(self._nrows))

    def augment(self, right: Matrix | Vector) -> Matrix:
        """Construit la matrice augmentée [A | right]."""
        rhs = Matrix(right) if isinstance(right, Vector) else right
        if self._nrows != rhs.rows:
            raise DimensionMismatchError(
                f"Impossible d'augmenter une matrice {self.shape} avec {rhs.shape}."
            )
        return Matrix._from_exact_rows(
            [(*self._rows[i], *rhs._rows[i]) for i in range(self._nrows)]
        )

    def to_sympy(self) -> sp.Matrix:
        """Convertit la matrice en sympy.Matrix."""
        if self._nrows == 0 or self._ncols == 0:
            return sp.Matrix(self._nrows, self._ncols, [])
        return sp.Matrix([list(r) for r in self._rows])

    def to_domain_matrix(self) -> DomainMatrix:
        """Convertit la matrice en DomainMatrix sur le plus petit domaine exact (D10)."""
        dm = self._domain_matrix
        if dm is None:
            dom = choose_domain(self.flat_entries)
            rows_dom = [[dom.from_sympy(e) for e in r] for r in self._rows]
            dm = DomainMatrix(rows_dom, (self._nrows, self._ncols), dom)
            object.__setattr__(self, "_domain_matrix", dm)
        return dm

    def subs(self, mapping: Mapping[Any, Any]) -> Matrix:
        """Substitue des symboles par des valeurs et renvoie une nouvelle Matrix."""
        sym_map = {
            (sp.Symbol(k, real=True) if isinstance(k, str) else k): to_exact(v)
            for k, v in mapping.items()
        }
        return Matrix._from_exact_rows(
            [[sp.simplify(e.xreplace(sym_map)) for e in r] for r in self._rows]
        )

    @overload
    def __getitem__(self, key: tuple[int, int]) -> sp.Expr: ...

    @overload
    def __getitem__(self, key: int) -> tuple[sp.Expr, ...]: ...

    @overload
    def __getitem__(self, key: tuple[slice | int, slice | int]) -> Matrix: ...

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return self._rows[key]
        if isinstance(key, tuple) and len(key) == 2:
            r_idx, c_idx = key
            if isinstance(r_idx, int) and isinstance(c_idx, int):
                return self._rows[r_idx][c_idx]
            rows_sel = (
                [self._rows[r_idx]]
                if isinstance(r_idx, int)
                else list(self._rows[r_idx])
            )
            if isinstance(c_idx, int):
                sub_rows = [[r[c_idx]] for r in rows_sel]
            else:
                sub_rows = [list(r[c_idx]) for r in rows_sel]
            return Matrix._from_exact_rows(sub_rows)
        raise TypeError(f"Indexation de Matrix invalide : {key!r}")

    def __len__(self) -> int:
        return self._nrows

    def __iter__(self) -> Iterator[tuple[sp.Expr, ...]]:
        return iter(self._rows)

    @property
    def T(self) -> Matrix:
        """Transposée A^T avec trace (A^T)_{ij} = A_{ji} (§5.3.2)."""
        with section("matrix.transpose", level=2, A=self, shape=self.shape):
            if self._nrows == 0 or self._ncols == 0:
                res = Matrix.zeros(self._ncols, self._nrows)
            else:
                transposed_rows = [
                    [self._rows[i][j] for i in range(self._nrows)]
                    for j in range(self._ncols)
                ]
                res = Matrix._from_exact_rows(transposed_rows)
            record(
                StepKind.RESULT,
                "matrix.transpose_result",
                level=2,
                snapshot={"matrix": res},
                result=res,
            )
            return res

    def _check_same_shape(self, other: Matrix) -> None:
        if self.shape != other.shape:
            raise DimensionMismatchError(
                f"Dimensions de matrices incompatibles : {self.shape} et {other.shape}."
            )

    def __add__(self, other: Matrix) -> Matrix:
        if not isinstance(other, Matrix):
            return NotImplemented
        self._check_same_shape(other)
        with section("matrix.add", level=2, A=self, B=other):
            rows = [
                [sp.simplify(self._rows[i][j] + other._rows[i][j]) for j in range(self._ncols)]
                for i in range(self._nrows)
            ]
            res = Matrix._from_exact_rows(rows)
            record(StepKind.RESULT, "matrix.add_result", level=2, result=res)
            return res

    def __sub__(self, other: Matrix) -> Matrix:
        if not isinstance(other, Matrix):
            return NotImplemented
        self._check_same_shape(other)
        with section("matrix.sub", level=2, A=self, B=other):
            rows = [
                [sp.simplify(self._rows[i][j] - other._rows[i][j]) for j in range(self._ncols)]
                for i in range(self._nrows)
            ]
            res = Matrix._from_exact_rows(rows)
            record(StepKind.RESULT, "matrix.sub_result", level=2, result=res)
            return res

    def __neg__(self) -> Matrix:
        return Matrix._from_exact_rows([[-e for e in r] for r in self._rows])

    def __mul__(self, scalar: Any) -> Matrix:
        if isinstance(scalar, (Matrix, Vector)):
            raise TypeError("Utilisez l'opérateur '@' pour le produit matriciel (D9, §5.3.2).")
        try:
            c = to_exact(scalar)
        except TypeError:
            return NotImplemented
        with section("matrix.scale", level=2, scalar=c, A=self):
            rows = [[sp.simplify(c * e) for e in r] for r in self._rows]
            res = Matrix._from_exact_rows(rows)
            record(StepKind.RESULT, "matrix.scale_result", level=2, result=res)
            return res

    def __rmul__(self, scalar: Any) -> Matrix:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Any) -> Matrix:
        c = to_exact(scalar)
        if oracle.decide(c).verdict == Verdict.ZERO:
            raise UndefinedOperationError("Division d'une matrice par le scalaire nul.")
        return self * (sp.Integer(1) / c)

    @overload
    def __matmul__(self, other: Vector) -> Vector: ...

    @overload
    def __matmul__(self, other: Matrix) -> Matrix: ...

    def __matmul__(self, other: Matrix | Vector) -> Matrix | Vector:
        if not isinstance(other, (Matrix, Vector)):
            return NotImplemented
        return self.matmul(other, view="entries")

    @overload
    def matmul(self, other: Vector, *, view: MatmulView = "entries") -> Vector: ...

    @overload
    def matmul(self, other: Matrix, *, view: MatmulView = "entries") -> Matrix: ...

    def matmul(
        self,
        other: Matrix | Vector,
        *,
        view: MatmulView = "entries",
    ) -> Matrix | Vector:
        """Produit matriciel A @ B ou A @ v tracé selon la vue choisie (§5.3.2, VMLS ch. 10).

        Vues disponibles :
        - 'entries' : coefficient (i, j) comme produit scalaire ligne i de A . colonne j de B ;
        - 'rows'    : ligne i de AB comme combinaison linéaire des lignes de B ;
        - 'columns' : colonne j de AB comme combinaison linéaire A * b_j des colonnes de A ;
        - 'outer'   : somme de produits extérieurs sum_{k=1}^n a_k * b_k^T.
        """
        is_vec = isinstance(other, Vector)
        rhs_mat = Matrix(other) if is_vec else other
        if self._ncols != rhs_mat.rows:
            raise DimensionMismatchError(
                f"Dimensions incompatibles pour le produit matriciel : "
                f"{self.shape} @ {rhs_mat.shape} ({self._ncols} != {rhs_mat.rows})."
            )
        if view not in ("entries", "rows", "columns", "outer"):
            raise ValueError(f"Vue de produit matriciel inconnue : {view!r}")

        m, k_dim, p = self._nrows, self._ncols, rhs_mat.cols

        with section(
            f"matrix.matmul.{view}",
            level=1,
            snapshot={"A": self, "B": other},
            m=m,
            k=k_dim,
            p=p,
            view=view,
        ):
            # Calcul interne rapide via DomainMatrix (D10)
            with suspend_tracing():
                all_entries = (*self.flat_entries, *rhs_mat.flat_entries)
                dom = choose_domain(all_entries)
                dm_a = DomainMatrix(
                    [[dom.from_sympy(e) for e in r] for r in self._rows],
                    (m, k_dim),
                    dom,
                )
                dm_b = DomainMatrix(
                    [[dom.from_sympy(e) for e in r] for r in rhs_mat._rows],
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
                    row_i = self.row(i)
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
                    coeffs = self._rows[i]
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
                a_cols = self.columns()
                for j in range(p):
                    coeffs = [rhs_mat._rows[idx][j] for idx in range(k_dim)]
                    col_res = res_mat.col(j)
                    record(
                        StepKind.INFO,
                        "matrix.matmul_col",
                        level=2,
                        j=j + 1,
                        coeffs=tuple(coeffs),
                        a_cols=a_cols,
                        col_result=col_res,
                    )
            elif view == "outer":
                for k_idx in range(k_dim):
                    col_k = Matrix(self.col(k_idx))
                    row_k = Matrix([rhs_mat._rows[k_idx]])
                    with suspend_tracing():
                        outer_k = col_k.matmul(row_k, view="entries")
                    record(
                        StepKind.INFO,
                        "matrix.matmul_outer_term",
                        level=2,
                        k=k_idx + 1,
                        col=self.col(k_idx),
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

    def gram(self) -> Matrix:
        """Matrice de Gram G = A^T A avec coefficient (i, j) = a_i^T a_j (§5.3.2, VMLS ch. 10)."""
        cols = self.columns()
        n = self._ncols
        with section("matrix.gram", level=1, snapshot={"A": self}, n=n):
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

    def has_orthonormal_columns(
        self, assumptions: AssumptionsType = None
    ) -> bool | CaseSplit[bool]:
        """Vérifie A^T A = I_n via l'oracle de nullité (§5.3.2)."""
        with section("matrix.orthonormal_check", level=1, snapshot={"A": self}):
            with suspend_tracing():
                g = self.gram()
                ident = Matrix.identity(self._ncols)
                diff = g - ident
            cond_all = Condition.true()
            has_cond = False
            for i in range(self._ncols):
                for j in range(self._ncols):
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
                    if dec.verdict == Verdict.CONDITIONAL and dec.condition is not None:
                        has_cond = True
                        cond_all = cond_all & dec.condition
                    elif dec.verdict == Verdict.UNKNOWN:
                        oracle.is_zero(diff[i, j], assumptions=assumptions)

            if not has_cond:
                return True
            neg_cond = Condition(eqs=(), neqs=cond_all.eqs)
            return CaseSplit(
                branches=(
                    Branch(condition=neg_cond, result=False, trace=None),
                    Branch(condition=cond_all, result=True, trace=None),
                )
            )

    def _require_gj(self) -> Callable[..., Any]:
        if _gauss_jordan_factory is None:
            raise RuntimeError("Le module algorithms.gauss_jordan n'est pas initialisé.")
        return _gauss_jordan_factory

    def rref(self) -> Matrix | CaseSplit[Matrix]:
        """Calcule la forme échelonnée réduite via GaussJordan (§5.3.2)."""
        gj_cls = self._require_gj()
        res = gj_cls(self).run()
        if isinstance(res, CaseSplit):
            return CaseSplit(
                branches=tuple(
                    Branch(b.condition, b.result.rref, b.trace) for b in res.branches
                ),
                parameters=res.parameters,
            )
        return res.rref  # type: ignore[no-any-return]

    def rank(self) -> int | CaseSplit[int]:
        """Calcule le rang de la matrice via GaussJordan (§5.3.2)."""
        gj_cls = self._require_gj()
        res = gj_cls(self).run()
        if isinstance(res, CaseSplit):
            return CaseSplit(
                branches=tuple(
                    Branch(b.condition, b.result.rank, b.trace) for b in res.branches
                ),
                parameters=res.parameters,
            )
        return res.rank  # type: ignore[no-any-return]

    def nullspace(self) -> tuple[Vector, ...] | CaseSplit[tuple[Vector, ...]]:
        """Calcule une base du noyau ker(A) via GaussJordan (§5.3.2)."""
        gj_cls = self._require_gj()
        b_zero = Vector.zeros(self._nrows)
        res = gj_cls(self, b_zero).run()
        if isinstance(res, CaseSplit):
            return CaseSplit(
                branches=tuple(
                    Branch(b.condition, b.result.nullspace_basis, b.trace)
                    for b in res.branches
                ),
                parameters=res.parameters,
            )
        return res.nullspace_basis  # type: ignore[no-any-return]

    def inv(
        self,
        *,
        assumptions: Any = None,
        strict: bool = True,
    ) -> Matrix | None | CaseSplit[Matrix | None]:
        """Calcule l'inverse A^{-1} via GaussJordan sur [A | I_n] (§5.3.2, §5.4.2)."""
        if self._nrows != self._ncols:
            raise DimensionMismatchError(
                f"Seules les matrices carrées sont inversibles (reçu {self.shape})."
            )
        gj_cls = self._require_gj()
        res = gj_cls(
            self,
            Matrix.identity(self._nrows),
            assumptions=assumptions,
            strict=strict,
            compute_inverse=True,
        ).run()
        if isinstance(res, CaseSplit):
            return CaseSplit(
                branches=tuple(
                    Branch(b.condition, b.result.inverse, b.trace) for b in res.branches
                ),
                parameters=res.parameters,
            )
        return res.inverse  # type: ignore[no-any-return]

    def solve(
        self,
        b: Vector | Matrix,
        *,
        assumptions: Any = None,
        strict: bool = False,
    ) -> Any:
        """Résout A x = b via GaussJordan et renvoie un SolutionSet ou un CaseSplit (§5.3.2)."""
        gj_cls = self._require_gj()
        res = gj_cls(self, b, assumptions=assumptions, strict=strict).run()
        if isinstance(res, CaseSplit):
            return CaseSplit(
                branches=tuple(
                    Branch(b.condition, b.result.solution, b.trace) for b in res.branches
                ),
                parameters=res.parameters,
            )
        return res.solution

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return False
        if self.shape != other.shape:
            return False
        with suspend_tracing():
            for i in range(self._nrows):
                for j in range(self._ncols):
                    dec = oracle.decide(self._rows[i][j] - other._rows[i][j], trace_level3=False)
                    if dec.verdict != Verdict.ZERO:
                        return False
        return True

    def __hash__(self) -> int:
        return hash(self._rows)

    def __repr__(self) -> str:
        rows_str = ", ".join(
            "[" + ", ".join(str(e) for e in r) + "]" for r in self._rows
        )
        return f"Matrix([{rows_str}])"

    def __str__(self) -> str:
        if self._nrows == 0 or self._ncols == 0:
            return f"Matrix([], shape={self.shape})"
        return str(sp.pretty(self.to_sympy(), use_unicode=True))

    def _repr_latex_(self) -> str:
        """Rendu LaTeX pour JupyterLab (§5.5)."""
        if self._nrows == 0 or self._ncols == 0:
            return "$\\left[\\,\\right]$"
        cols_spec = "c" * self._ncols
        body = " \\\\ ".join(
            " & ".join(sp.latex(e) for e in r) for r in self._rows
        )
        return f"$\\left[\\begin{{array}}{{{cols_spec}}} {body} \\end{{array}}\\right]$"
