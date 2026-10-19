"""Gestion des conditions paramétriques et discussions par cas CaseSplit (§5.1.3, D4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterator, Mapping, Sequence, TypeVar

import sympy as sp

from linalg_pedagopy.core.field import symbols, to_exact

R = TypeVar("R")

# Hook optionnel enregistré par le module render pour éviter tout import montant core -> render
_explain_casesplit_hook: Callable[[Any, int, str], Any] | None = None


def register_casesplit_explain_hook(
    hook: Callable[[Any, int, str], Any] | None,
) -> None:
    """Enregistre la fonction de rendu pour CaseSplit.explain()."""
    global _explain_casesplit_hook
    _explain_casesplit_hook = hook


def _normalize_relation_expr(expr: sp.Expr) -> tuple[sp.Expr, sp.Expr]:
    """Transforme une expression polynomiale P == 0 en couple lisible (lhs, rhs), ex. (a, 1)."""
    expr = sp.simplify(sp.together(expr))
    num, _ = sp.fraction(expr)
    expr = sp.expand(num)
    free = sorted(expr.free_symbols, key=lambda s: s.name)
    if len(free) == 1:
        sym = free[0]
        try:
            poly = sp.Poly(expr, sym)
            if poly.degree() == 1:
                c1, c0 = poly.all_coeffs()
                rhs = sp.simplify(-c0 / c1)
                return sym, rhs
        except Exception:
            pass
    # Si la forme est sym - rhs où rhs ne contient pas sym
    if len(free) >= 1:
        sym = free[0]
        try:
            poly = sp.Poly(expr, sym)
            if poly.degree() == 1:
                c1, c0 = poly.all_coeffs()
                if not c1.free_symbols:
                    rhs = sp.simplify(-c0 / c1)
                    return sym, rhs
        except Exception:
            pass
    return expr, sp.Integer(0)


@dataclass(frozen=True)
class Condition:
    """Conjonction d'égalités et d'inégalités polynomiales en les paramètres (§5.1.3)."""

    eqs: tuple[tuple[sp.Expr, sp.Expr], ...] = ()
    neqs: tuple[tuple[sp.Expr, sp.Expr], ...] = ()

    @classmethod
    def true(cls) -> Condition:
        """Condition toujours vraie (aucune contrainte)."""
        return cls()

    @classmethod
    def from_zero_expr(cls, expr: sp.Expr, *, is_zero: bool) -> Condition:
        """Construit une condition d'annulation (is_zero=True) ou de non-annulation (is_zero=False)."""
        lhs, rhs = _normalize_relation_expr(expr)
        if is_zero:
            return cls(eqs=((lhs, rhs),))
        return cls(neqs=((lhs, rhs),))

    @classmethod
    def eq(cls, lhs: Any, rhs: Any = 0) -> Condition:
        """Construit une condition d'égalité lhs = rhs."""
        expr = to_exact(lhs) - to_exact(rhs)
        norm_l, norm_r = _normalize_relation_expr(expr)
        return cls(eqs=((norm_l, norm_r),))

    @classmethod
    def neq(cls, lhs: Any, rhs: Any = 0) -> Condition:
        """Construit une condition d'inégalité lhs ≠ rhs."""
        expr = to_exact(lhs) - to_exact(rhs)
        norm_l, norm_r = _normalize_relation_expr(expr)
        return cls(neqs=((norm_l, norm_r),))

    @property
    def is_trivial(self) -> bool:
        return not self.eqs and not self.neqs

    @property
    def is_generic(self) -> bool:
        """Une branche est générique si elle ne comporte que des inégalités (aucune égalité)."""
        return len(self.eqs) == 0

    @property
    def free_symbols(self) -> set[sp.Symbol]:
        syms: set[sp.Symbol] = set()
        for l, r in (*self.eqs, *self.neqs):
            syms |= l.free_symbols | r.free_symbols
        return {s for s in syms if isinstance(s, sp.Symbol)}

    def and_with(self, other: Condition) -> Condition:
        """Conjonction logique de deux conditions sans doublons."""
        new_eqs = list(self.eqs)
        for item in other.eqs:
            if item not in new_eqs:
                new_eqs.append(item)
        new_neqs = list(self.neqs)
        for item in other.neqs:
            if item not in new_neqs:
                new_neqs.append(item)
        return Condition(eqs=tuple(new_eqs), neqs=tuple(new_neqs))

    def __and__(self, other: Condition) -> Condition:
        return self.and_with(other)

    def substitutions(self) -> dict[sp.Symbol, sp.Expr]:
        """Extrait les substitutions directes (symbole -> expression) des égalités."""
        subs_map: dict[sp.Symbol, sp.Expr] = {}
        for lhs, rhs in self.eqs:
            if isinstance(lhs, sp.Symbol) and lhs not in rhs.free_symbols:
                subs_map[lhs] = rhs
        return subs_map

    def implies_zero(self, expr: sp.Expr) -> bool | None:
        """Teste si la condition courante fixe le statut nul/non-nul de expr.

        Renvoie:
            True si expr == 0 sous cette condition,
            False si expr != 0 est garanti par cette condition,
            None si la condition ne tranche pas.
        """
        subs_map = self.substitutions()
        reduced = sp.simplify(expr.xreplace(subs_map)) if subs_map else sp.simplify(expr)
        if reduced == 0:
            return True
        if not reduced.free_symbols and reduced.is_zero is False:
            return False

        norm_l, norm_r = _normalize_relation_expr(reduced)
        for l, r in self.eqs:
            if sp.simplify((norm_l - norm_r) - (l - r)) == 0 or sp.simplify((norm_l - norm_r) + (l - r)) == 0:
                return True
        for l, r in self.neqs:
            diff_rel = sp.simplify((norm_l - norm_r) - (l - r))
            if diff_rel == 0 or sp.simplify((norm_l - norm_r) + (l - r)) == 0:
                return False
            # Si reduced divise l - r, alors l - r != 0 implique reduced != 0
            diff_neq = sp.simplify(l - r)
            if diff_neq.has(*reduced.free_symbols):
                try:
                    q, rem = sp.div(diff_neq, reduced)
                    if rem == 0:
                        return False
                except Exception:
                    pass
        return None

    def is_satisfied(self, values: Mapping[str | sp.Symbol, Any]) -> bool:
        """Vérifie si les valeurs passées pour les paramètres satisfont la condition."""
        subs_map: dict[sp.Symbol, sp.Expr] = {}
        for k, v in values.items():
            sym = symbols(k)[0] if isinstance(k, str) else k
            subs_map[sym] = to_exact(v)

        for lhs, rhs in self.eqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff != 0:
                return False
        for lhs, rhs in self.neqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff == 0:
                return False
        return True

    def format_text(self) -> str:
        """Rendu texte lisible, ex. 'a ≠ 1 et b = 0'."""
        parts: list[str] = []
        for lhs, rhs in self.neqs:
            parts.append(f"{lhs} ≠ {rhs}")
        for lhs, rhs in self.eqs:
            parts.append(f"{lhs} = {rhs}")
        return " et ".join(parts) if parts else "toujours"

    def format_latex(self) -> str:
        """Rendu LaTeX de la condition."""
        parts: list[str] = []
        for lhs, rhs in self.neqs:
            parts.append(f"{sp.latex(lhs)} \\neq {sp.latex(rhs)}")
        for lhs, rhs in self.eqs:
            parts.append(f"{sp.latex(lhs)} = {sp.latex(rhs)}")
        return " \\text{ et } ".join(parts) if parts else "\\text{toujours}"

    def __str__(self) -> str:
        return self.format_text()


@dataclass(frozen=True)
class Branch(Generic[R]):
    """Branche d'une discussion par cas : (condition, résultat, sous-trace)."""

    condition: Condition
    result: R
    trace: Any = None


@dataclass(frozen=True)
class CaseSplit(Generic[R]):
    """Discussion ordonnée par cas selon un ou plusieurs paramètres (§5.1.3, D4)."""

    branches: tuple[Branch[R], ...]
    parameters: tuple[sp.Symbol, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.parameters and self.branches:
            syms: set[sp.Symbol] = set()
            for b in self.branches:
                syms |= b.condition.free_symbols
            ordered = tuple(sorted(syms, key=lambda s: s.name))
            object.__setattr__(self, "parameters", ordered)

    def __len__(self) -> int:
        return len(self.branches)

    def __iter__(self) -> Iterator[Branch[R]]:
        return iter(self.branches)

    def __getitem__(self, index: int) -> Branch[R]:
        return self.branches[index]

    def generic(self) -> R:
        """Renvoie le résultat de la branche générique (première branche sans égalité)."""
        for branch in self.branches:
            if branch.condition.is_generic:
                return branch.result
        return self.branches[0].result

    def at(self, **values: Any) -> R:
        """Renvoie le résultat correspondant aux valeurs données des paramètres."""
        subs_map: dict[sp.Symbol, sp.Expr] = {
            symbols(k)[0]: to_exact(v) for k, v in values.items()
        }
        # On teste d'abord les cas particuliers (égalités), puis la branche générique
        particular = [b for b in self.branches if not b.condition.is_generic]
        generics = [b for b in self.branches if b.condition.is_generic]
        for branch in (*particular, *generics):
            if branch.condition.is_satisfied(subs_map):
                res = branch.result
                if hasattr(res, "subs"):
                    return res.subs(subs_map)  # type: ignore[no-any-return]
                return res
        raise ValueError(
            f"Aucune branche ne correspond aux valeurs fournies : {values!r}"
        )

    def explain(self, level: int | None = None, fmt: str = "auto") -> Any:
        """Produit une Explanation détaillant chaque branche de la discussion."""
        if _explain_casesplit_hook is None:
            raise RuntimeError("Le module render n'est pas initialisé.")
        return _explain_casesplit_hook(self, level if level is not None else 1, fmt)

    def _repr_markdown_(self) -> str:
        """Rendu Markdown avec formules LaTeX dans Jupyter (§5.5)."""
        return self.explain().to_markdown()

    def _repr_latex_(self) -> str:
        """Rendu LaTeX dans Jupyter."""
        return self.explain().to_latex()
