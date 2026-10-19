"""Gestion des conditions paramétriques et discussions par cas CaseSplit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterator, Mapping, Sequence, TypeVar

import sympy as sp

from linalg_pedagopy.core.field import match_symbol_substitutions, pretty_expr, symbols, to_exact

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
            if poly.degree() > 1 and poly.LC().is_number and poly.LC() < 0:
                expr = sp.expand(-expr)
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


def _compute_transitive_substitutions(
    eqs: Sequence[tuple[sp.Expr, sp.Expr]],
) -> dict[sp.Symbol, sp.Expr]:
    """Calcule la clôture transitive des substitutions linéaires issues des égalités."""
    subs_map: dict[sp.Symbol, sp.Expr] = {}
    changed = True
    while changed:
        changed = False
        for lhs, rhs in eqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff == 0:
                continue
            nl, nr = _normalize_relation_expr(diff)
            if isinstance(nl, sp.Symbol) and nl not in nr.free_symbols and nl not in subs_map:
                subs_map[nl] = nr
                subs_map = {
                    k: sp.simplify(v.xreplace({nl: nr}))
                    for k, v in subs_map.items()
                }
                changed = True
    return subs_map


@dataclass(frozen=True)
class Condition:
    """Conjonction d'égalités et d'inégalités polynomiales en les paramètres."""

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
    def is_contradictory(self) -> bool:
        """Vérifie si la conjonction d'égalités et d'inégalités est contradictoire sur R."""
        subs_map = self.substitutions()
        for lhs, rhs in self.eqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff == 0:
                continue
            if not diff.free_symbols and diff.is_zero is False:
                return True
            if len(diff.free_symbols) == 1:
                sym = next(iter(diff.free_symbols))
                try:
                    if not sp.solve(diff, sym):
                        return True
                except Exception:
                    pass
        for lhs, rhs in self.neqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff == 0:
                return True
            nl, nr = _normalize_relation_expr(diff)
            for el, er in self.eqs:
                eq_diff = sp.simplify((el - er).xreplace(subs_map))
                if sp.simplify((nl - nr) - eq_diff) == 0 or sp.simplify((nl - nr) + eq_diff) == 0:
                    return True
        return False

    @property
    def free_symbols(self) -> set[sp.Symbol]:
        syms: set[sp.Symbol] = set()
        for l, r in (*self.eqs, *self.neqs):
            syms |= l.free_symbols | r.free_symbols
        return {s for s in syms if isinstance(s, sp.Symbol)}

    def and_with(self, other: Condition) -> Condition:
        """Conjonction logique de deux conditions avec réduction des égalités et élagage des tautologies."""
        raw_eqs = list(self.eqs)
        for item in other.eqs:
            if item not in raw_eqs:
                raw_eqs.append(item)
        raw_neqs = list(self.neqs)
        for item in other.neqs:
            if item not in raw_neqs:
                raw_neqs.append(item)

        if not raw_eqs:
            return Condition(eqs=(), neqs=tuple(raw_neqs))

        subs_map = _compute_transitive_substitutions(raw_eqs)
        new_eqs: list[tuple[sp.Expr, sp.Expr]] = []
        for lhs, rhs in raw_eqs:
            if isinstance(lhs, sp.Symbol) and lhs in subs_map:
                cand_eq = (lhs, subs_map[lhs])
                if cand_eq not in new_eqs:
                    new_eqs.append(cand_eq)
                # Si rhs réduit diffère de subs_map[lhs], conserver la relation pour détecter la contradiction
                diff_check = sp.simplify((lhs - rhs).xreplace(subs_map))
                if diff_check != 0 and (lhs, rhs) not in new_eqs:
                    new_eqs.append((lhs, rhs))
            else:
                diff = sp.simplify((lhs - rhs).xreplace(subs_map))
                if diff == 0:
                    continue
                nl, nr = _normalize_relation_expr(diff)
                if (nl, nr) not in new_eqs:
                    new_eqs.append((nl, nr))

        new_neqs: list[tuple[sp.Expr, sp.Expr]] = []
        for lhs, rhs in raw_neqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff == 0:
                zero_pair = (sp.Integer(0), sp.Integer(0))
                if zero_pair not in new_neqs:
                    new_neqs.append(zero_pair)
                continue
            # Une inégalité constante non nulle (ex. -2 != 0 sous a = -1) est une tautologie : on l'élague
            if not diff.free_symbols and diff.is_zero is False:
                continue
            nl, nr = _normalize_relation_expr(diff)
            if (nl, nr) not in new_neqs:
                new_neqs.append((nl, nr))

        return Condition(eqs=tuple(new_eqs), neqs=tuple(new_neqs))

    def __and__(self, other: Condition) -> Condition:
        return self.and_with(other)

    def substitutions(self) -> dict[sp.Symbol, sp.Expr]:
        """Extrait la clôture transitive des substitutions (symbole -> expression) des égalités."""
        return _compute_transitive_substitutions(self.eqs)

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
        red_poly = sp.expand(norm_l - norm_r)

        for l, r in self.eqs:
            eq_diff = sp.simplify((l - r).xreplace(subs_map))
            if eq_diff == 0:
                continue
            el, er = _normalize_relation_expr(eq_diff)
            eq_poly = sp.expand(el - er)
            if sp.simplify(red_poly - eq_poly) == 0 or sp.simplify(red_poly + eq_poly) == 0:
                return True
            if eq_poly.free_symbols and eq_poly.free_symbols <= red_poly.free_symbols:
                try:
                    _, rem = sp.div(red_poly, eq_poly)
                    if sp.simplify(rem) == 0:
                        return True
                except Exception:
                    pass
                if len(eq_poly.free_symbols) == 1 and red_poly.free_symbols == eq_poly.free_symbols:
                    sym = next(iter(eq_poly.free_symbols))
                    try:
                        if red_poly.is_polynomial(sym) and eq_poly.is_polynomial(sym):
                            rem_u = sp.rem(red_poly, eq_poly, sym)
                            if sp.simplify(rem_u) == 0:
                                return True
                            g = sp.gcd(red_poly, eq_poly, sym)
                            if sp.Poly(g, sym).degree() == 0:
                                return False
                    except Exception:
                        pass

        for l, r in self.neqs:
            diff_neq = sp.simplify((l - r).xreplace(subs_map))
            if diff_neq == 0:
                continue
            nl, nr = _normalize_relation_expr(diff_neq)
            neq_poly = sp.expand(nl - nr)
            if sp.simplify(red_poly - neq_poly) == 0 or sp.simplify(red_poly + neq_poly) == 0:
                return False
            # Si red_poly divise neq_poly, alors neq_poly != 0 implique red_poly != 0
            if neq_poly.has(*red_poly.free_symbols):
                try:
                    _, rem = sp.div(neq_poly, red_poly)
                    if sp.simplify(rem) == 0:
                        return False
                except Exception:
                    pass
        return None

    def is_satisfied(self, values: Mapping[str | sp.Symbol, Any]) -> bool:
        """Vérifie si les valeurs passées pour les paramètres satisfont la condition."""
        subs_map = match_symbol_substitutions(self.free_symbols, values)

        for lhs, rhs in self.eqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff != 0:
                return False
        for lhs, rhs in self.neqs:
            diff = sp.simplify((lhs - rhs).xreplace(subs_map))
            if diff == 0:
                return False
        return True

    @staticmethod
    def _split_neq(lhs: sp.Expr, rhs: sp.Expr) -> list[tuple[sp.Expr, sp.Expr]]:
        """Décompose 'p(s) ≠ 0' en 's ≠ r_1 et s ≠ r_2 …' quand p se factorise sur R.

        Purement d'affichage : un produit est non nul si et seulement si chacun
        de ses facteurs l'est. On ne décompose que les polynômes en une seule
        variable dont toutes les racines sont réelles et explicites.
        """
        try:
            expr = sp.expand(sp.sympify(lhs) - sp.sympify(rhs))
            syms = expr.free_symbols
            if len(syms) != 1 or (sp.sympify(rhs) != 0 and sp.Poly(expr, *syms).degree() <= 1):
                return [(lhs, rhs)]
            s = next(iter(syms))
            poly = sp.Poly(expr, s)
            if poly.degree() < 1:
                return [(lhs, rhs)]
            roots = sp.roots(poly)
            if sum(roots.values()) != poly.degree() or not all(r.is_real for r in roots):
                return [(lhs, rhs)]
            return [(s, r) for r in sorted(roots, key=lambda r: float(r), reverse=True)]
        except Exception:
            return [(lhs, rhs)]

    def format_text(self) -> str:
        """Rendu texte lisible, ex. 'a ≠ 1 et b = 0', 'b ≠ 1 et b ≠ −1'."""
        parts: list[str] = []
        for lhs, rhs in self.neqs:
            for l2, r2 in self._split_neq(lhs, rhs):
                parts.append(f"{pretty_expr(l2)} ≠ {pretty_expr(r2)}")
        for lhs, rhs in self.eqs:
            parts.append(f"{pretty_expr(lhs)} = {pretty_expr(rhs)}")
        return " et ".join(parts) if parts else "toujours"

    def format_latex(self) -> str:
        """Rendu LaTeX de la condition."""
        parts: list[str] = []
        for lhs, rhs in self.neqs:
            for l2, r2 in self._split_neq(lhs, rhs):
                parts.append(f"{sp.latex(l2)} \\neq {sp.latex(r2)}")
        for lhs, rhs in self.eqs:
            parts.append(f"{sp.latex(lhs)} = {sp.latex(rhs)}")
        return " \\text{ et } ".join(parts) if parts else "\\text{toujours}"

    def __str__(self) -> str:
        return self.format_text()


def _subs_branch_result(res: Any, subs_map: Mapping[sp.Symbol, sp.Expr]) -> Any:
    if hasattr(res, "subs"):
        return res.subs(subs_map)
    if isinstance(res, tuple):
        return tuple(_subs_branch_result(item, subs_map) for item in res)
    if isinstance(res, list):
        return [_subs_branch_result(item, subs_map) for item in res]
    return res


@dataclass(frozen=True)
class Branch(Generic[R]):
    """Branche d'une discussion par cas : (condition, résultat, sous-trace)."""

    condition: Condition
    result: R
    trace: Any = field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class CaseSplit(Generic[R]):
    """Discussion ordonnée par cas selon un ou plusieurs paramètres."""

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
        all_syms: set[sp.Symbol] = set(self.parameters)
        for b in self.branches:
            all_syms |= b.condition.free_symbols
        subs_map = match_symbol_substitutions(all_syms, values)
        # On teste d'abord les cas particuliers (égalités), puis la branche générique
        particular = [b for b in self.branches if not b.condition.is_generic]
        generics = [b for b in self.branches if b.condition.is_generic]
        for branch in (*particular, *generics):
            if branch.condition.is_satisfied(subs_map):
                return _subs_branch_result(branch.result, subs_map)  # type: ignore[no-any-return]
        raise ValueError(
            f"Aucune branche ne correspond aux valeurs fournies : {values!r}"
        )

    def explain(self, level: int | None = None, fmt: str = "auto") -> Any:
        """Produit une Explanation détaillant chaque branche de la discussion."""
        if _explain_casesplit_hook is None:
            raise RuntimeError("Le module render n'est pas initialisé.")
        return _explain_casesplit_hook(self, level if level is not None else 1, fmt)

    def __str__(self) -> str:
        return str(self.explain().to_text())

    def __repr__(self) -> str:
        params = ", ".join(s.name for s in self.parameters) or "les paramètres"
        cases = " | ".join(b.condition.format_text() for b in self.branches)
        return f"<CaseSplit selon {params} : {len(self.branches)} cas — {cases}>"

    def _repr_markdown_(self) -> str:
        """Rendu Markdown avec formules LaTeX dans Jupyter."""
        return self.explain().to_markdown()

    def _repr_latex_(self) -> str:
        """Rendu LaTeX dans Jupyter."""
        return self.explain().to_latex()
