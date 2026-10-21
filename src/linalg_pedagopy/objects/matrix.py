"""Objet mathématique immuable Matrix."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, Literal, Mapping, Sequence, overload

import sympy as sp
from sympy.polys.matrices import DomainMatrix

from linalg_pedagopy.core.cases import Branch, CaseSplit
from linalg_pedagopy.core.exceptions import (
    DimensionMismatchError,
    UndefinedOperationError,
)
from linalg_pedagopy.core.field import choose_domain, match_symbol_substitutions, to_exact
from linalg_pedagopy.core.zero import AssumptionsType, Verdict, oracle
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section, suspend_tracing

MatmulView = Literal["entries", "rows", "columns", "outer"]

# Registre des procédures de ``algorithms/`` auxquelles ``Matrix`` délègue (sans import montant) :
# "gauss_jordan", "determinant", "matmul", "gram", "orthonormal_check", "singular_check".
_procedures: dict[str, Callable[..., Any]] = {}


def register_procedure(name: str, factory: Callable[..., Any]) -> None:
    """Enregistre une procédure de ``algorithms/`` pour les méthodes déléguées de Matrix."""
    _procedures[name] = factory


def _procedure(name: str) -> Callable[..., Any]:
    try:
        return _procedures[name]
    except KeyError:
        raise RuntimeError(f"La procédure « {name} » de linalg_pedagopy.algorithms n'est pas initialisée.") from None


def _champ(res: Any, attr: str) -> Any:
    """Attribut ``attr`` d'un résultat, ou ``CaseSplit`` de cet attribut branche par branche."""
    if isinstance(res, CaseSplit):
        return CaseSplit(
            branches=tuple(Branch(b.condition, getattr(b.result, attr), b.trace) for b in res.branches),
            parameters=res.parameters,
        )
    return getattr(res, attr)


class Matrix:
    """Matrice immuable m x n à coefficients exacts sur R."""

    __slots__ = ("_rows", "_nrows", "_ncols", "_domain_matrix")

    # Attributs posés par object.__setattr__ (objet immuable) ; annotés pour mypy.
    _rows: tuple[tuple[sp.Expr, ...], ...]
    _nrows: int
    _ncols: int
    _domain_matrix: DomainMatrix | None  # cache, calculé à la demande

    def __init__(self, data: Iterable[Any]) -> None:
        if getattr(data, "_is_locked_tutor_proxy", False):
            data = data._unwrap_for_constructor("Matrix(...)")  # type: ignore[attr-defined]
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
        raise AttributeError("Matrix est immuable : créez une nouvelle matrice plutôt que de la modifier.")

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
        """Construit une matrice à partir d'une liste de vecteurs-colonnes."""
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
        """Matrice identité I_n de taille n x n."""
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
        """Construit une matrice par blocs.

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
        """Convertit la matrice en DomainMatrix sur le plus petit domaine exact."""
        dm = self._domain_matrix
        if dm is None:
            dom = choose_domain(self.flat_entries)
            rows_dom = [[dom.from_sympy(e) for e in r] for r in self._rows]
            dm = DomainMatrix(rows_dom, (self._nrows, self._ncols), dom)
            object.__setattr__(self, "_domain_matrix", dm)
        return dm

    def subs(self, mapping: Mapping[Any, Any]) -> Matrix:
        """Substitue des symboles par des valeurs et renvoie une nouvelle Matrix."""
        free: set[sp.Symbol] = set()
        for e in self.flat_entries:
            free |= {s for s in e.free_symbols if isinstance(s, sp.Symbol)}
        sym_map = match_symbol_substitutions(free, mapping)
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
        """Transposée A^T avec trace (A^T)_{ij} = A_{ji}."""
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
            raise TypeError("Utilisez l'opérateur '@' pour le produit matriciel (le symbole * est réservé au produit par un scalaire).")
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
        return self.__mul__(sp.Integer(1) / c)

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
        """Produit matriciel A @ B ou A @ v tracé selon la vue choisie.

        Vues disponibles :
        - 'entries' : coefficient (i, j) comme produit scalaire ligne i de A . colonne j de B ;
        - 'rows'    : ligne i de AB comme combinaison linéaire des lignes de B ;
        - 'columns' : colonne j de AB comme combinaison linéaire A * b_j des colonnes de A ;
        - 'outer'   : somme de produits extérieurs sum_{k=1}^n a_k * b_k^T.
        """
        return _procedure("matmul")(self, other, view=view)  # type: ignore[no-any-return]

    # --- Méthodes de commodité -------------------------------------------------------------
    # Règle de délégation : quelques lignes chacune, qui appellent une procédure de
    # ``algorithms/`` (registre ``_procedures``). Toute boucle, discussion de cas ou trace vit
    # dans ``algorithms/`` ; voir docs/dev/architecture.md.

    def gram(self) -> Matrix:
        """Matrice de Gram G = A^T A avec coefficient (i, j) = a_i^T a_j."""
        return _procedure("gram")(self)  # type: ignore[no-any-return]

    def has_orthonormal_columns(
        self, assumptions: AssumptionsType = None
    ) -> bool | CaseSplit[bool]:
        """Vérifie A^T A = I_n via l'oracle de nullité."""
        return _procedure("orthonormal_check")(self, assumptions)  # type: ignore[no-any-return]

    def rref(self, *, assumptions: Any = None) -> Matrix | CaseSplit[Matrix]:
        """Calcule la forme échelonnée réduite via GaussJordan."""
        return _champ(_procedure("gauss_jordan")(self, assumptions=assumptions).run(), "rref")  # type: ignore[no-any-return]

    def rank(self, *, assumptions: Any = None) -> int | CaseSplit[int]:
        """Calcule le rang de la matrice via GaussJordan."""
        return _champ(_procedure("gauss_jordan")(self, assumptions=assumptions).run(), "rank")  # type: ignore[no-any-return]

    def nullspace(
        self, *, assumptions: Any = None
    ) -> tuple[Vector, ...] | CaseSplit[tuple[Vector, ...]]:
        """Calcule une base du noyau ker(A) via GaussJordan (réduction de A seule, sans colonne de zéros)."""
        return _champ(_procedure("gauss_jordan")(self, assumptions=assumptions).run(), "nullspace_basis")  # type: ignore[no-any-return]

    def inv(
        self,
        *,
        assumptions: Any = None,
        strict: bool = True,
    ) -> Matrix | None | CaseSplit[Matrix | None]:
        """Calcule l'inverse A^{-1} via GaussJordan sur [A | I_n].

        Avec des paramètres et ``strict=True``, les valeurs qui rendent la matrice singulière
        sont annoncées d'emblée, à partir du déterminant (méthode de Bareiss).
        """
        if self._nrows != self._ncols:
            raise DimensionMismatchError(
                f"Seules les matrices carrées sont inversibles (reçu {self.shape})."
            )
        if strict and any(e.free_symbols for e in self.flat_entries):
            _procedure("singular_check")(self, assumptions)
        res = _procedure("gauss_jordan")(
            self, Matrix.identity(self._nrows), assumptions=assumptions, strict=strict, compute_inverse=True
        ).run()
        return _champ(res, "inverse")  # type: ignore[no-any-return]

    @overload
    def det(
        self, *, method: Literal["auto", "bareiss", "cofactors", "sarrus"] = ..., assumptions: Any = None
    ) -> sp.Expr: ...

    @overload
    def det(self, *, method: str, assumptions: Any = None) -> sp.Expr | CaseSplit[sp.Expr]: ...

    def det(self, *, method: str = "auto", assumptions: Any = None) -> sp.Expr | CaseSplit[sp.Expr]:
        """Déterminant exact, factorisé (méthodes : auto, bareiss, elimination, cofactors, sarrus).

        Avec ``method="elimination"`` et des paramètres, un pivot qui peut s'annuler donne
        une discussion par cas (``CaseSplit`` des valeurs).
        """
        res = _procedure("determinant")(self, method=method, assumptions=assumptions).run()
        return _champ(res, "value")

    def solve(
        self,
        b: Vector | Matrix,
        *,
        assumptions: Any = None,
        strict: bool = False,
    ) -> Any:
        """Résout A x = b via GaussJordan et renvoie un SolutionSet ou un CaseSplit."""
        return _champ(_procedure("gauss_jordan")(self, b, assumptions=assumptions, strict=strict).run(), "solution")

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
        """Rendu LaTeX pour JupyterLab."""
        if self._nrows == 0 or self._ncols == 0:
            return "$\\left[\\,\\right]$"
        cols_spec = "c" * self._ncols
        body = " \\\\ ".join(
            " & ".join(sp.latex(e) for e in r) for r in self._rows
        )
        return f"$\\left[\\begin{{array}}{{{cols_spec}}} {body} \\end{{array}}\\right]$"
