"""Machinerie d'élimination commune à Gauss-Jordan et au déterminant.

Étape 4.1 du plan v6 : fonctions pures (simplification des coefficients, critère et choix
du pivot, mise en forme des résultats d'une branche). Les étapes suivantes y ajoutent les
opérations élémentaires tracées puis le moteur d'élimination lui-même.
"""

from __future__ import annotations

from typing import Callable, Literal, Mapping

import sympy as sp

from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import Condition

PivotStrategy = Literal["simplest", "first", "partial"]


def _simplify_entry(expr: sp.Expr) -> sp.Expr:
    """Simplifie une entrée sous forme de fraction rationnelle canonique lisible."""
    if expr.is_Rational:
        return expr
    if expr.free_symbols and expr.is_rational_function(*expr.free_symbols):
        num, den = sp.fraction(sp.together(sp.cancel(expr)))
        if den != 1:
            return sp.Mul(sp.factor(num), 1 / sp.factor(den), evaluate=True)
        return sp.expand(num)
    return sp.simplify(expr)


def _factor_with_radicals(expr: sp.Expr, radicals: Mapping[sp.Symbol, tuple[sp.Expr, ...]]) -> sp.Expr:
    """Factorise une entrée sur Q(√d), pour les radicaux √d de la condition de sa branche.

    Sous « a ≠ √2 et a ≠ −√2 », (a − 2)/((a − 1)(a² − 2)) s'écrit
    (a − 2)/((a − 1)(a − √2)(a + √2)) : mêmes facteurs que la condition.
    Seuls les radicaux associés aux paramètres présents dans l'entrée sont utilisés.
    """
    syms = expr.free_symbols
    if not radicals or not syms:
        return expr
    ext = sorted({r for s in syms for r in radicals.get(s, ())}, key=sp.default_sort_key)
    if not ext or not expr.is_rational_function(*syms):
        return expr
    num, den = sp.fraction(sp.together(sp.cancel(expr)))
    return sp.Mul(_split_over(num, ext), 1 / _split_over(den, ext), evaluate=True)


def _split_over(poly: sp.Expr, ext: list[sp.Expr]) -> sp.Expr:
    """Factorise sur Q, puis décompose sur Q(√d) les seuls facteurs irréductibles de degré ≥ 2.

    Les facteurs déjà décomposés sur Q gardent leur écriture (1 − 2a ne devient pas −2(a − 1/2)).
    """
    parts = []
    for f in sp.Mul.make_args(sp.factor(poly)):
        base, e = f.as_base_exp()
        if base.free_symbols and base.is_polynomial() and sp.Poly(base).total_degree() >= 2:
            split = sp.factor(base, extension=ext)
            if len(sp.Mul.make_args(split)) > 1:
                f = split**e
        parts.append(f)
    return sp.Mul(*parts)


def _result_entry(cond: Condition) -> Callable[[sp.Expr], sp.Expr]:
    """Mise en forme des entrées d'un résultat (solution, inverse, base du noyau) selon ``config.factor_policy``."""
    radicals = cond.radicals() if config.factor_policy == "real_radicals" else {}
    if not radicals:
        return _simplify_entry
    return lambda e: _factor_with_radicals(_simplify_entry(e), radicals)


def _pivot_complexity_key(val: sp.Expr) -> tuple[int, int | float, int]:
    """Critère d'ordre D11 : ±1, entier de plus petite valeur absolue, rationnel de petite hauteur, expression courte."""
    if val == 1:
        return (0, 0, 1)
    if val == -1:
        return (0, 1, 2)
    if val.is_Integer:
        return (1, abs(int(val)), len(str(val)))
    if val.is_Rational:
        p, q = abs(int(val.p)), abs(int(val.q))
        return (2, max(p, q), p + q)
    if not val.free_symbols:
        return (3, len(str(val)), 0)
    return (4, len(str(val)), len(val.free_symbols))


def _choose_pivot(
    candidates: list[tuple[int, sp.Expr]], strategy: PivotStrategy
) -> tuple[int, sp.Expr]:
    """Pivot retenu parmi des candidats (ligne, valeur) inconditionnellement non nuls.

    ``simplest`` : le plus simple au sens de ``_pivot_complexity_key`` ; ``partial`` : la plus
    grande valeur absolue numérique ; ``first`` : le premier candidat.
    """
    if strategy == "simplest":
        return min(candidates, key=lambda item: _pivot_complexity_key(item[1]))
    if strategy == "partial":
        def _abs_eval(item: tuple[int, sp.Expr]) -> float:
            try:
                return float(abs(item[1].evalf()))
            except Exception:
                return 0.0
        return max(candidates, key=_abs_eval)
    return candidates[0]
