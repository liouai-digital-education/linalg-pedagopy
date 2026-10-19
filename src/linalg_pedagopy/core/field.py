"""Gestion du corps des réels, coercition des entrées et choix du domaine (§5.1.1, D1, D2, D10)."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Callable, Iterable

import sympy as sp
from sympy.polys.domains import EX, QQ, Domain
from sympy.polys.constructor import construct_domain

from linalg_pedagopy.config import FloatPolicy, config
from linalg_pedagopy.core.exceptions import InexactInputError

# Hook optionnel enregistré par le module trace pour éviter tout import montant core -> trace
_trace_hook: Callable[[str, str, int, dict[str, Any]], None] | None = None


def register_trace_hook(
    hook: Callable[[str, str, int, dict[str, Any]], None] | None,
) -> None:
    """Enregistre la fonction de rappel du traceur pour signaler les coercitions."""
    global _trace_hook
    _trace_hook = hook


def emit_core_event(kind_name: str, message_key: str, level: int, **params: Any) -> None:
    """Émet un événement vers le traceur actif si le hook est enregistré."""
    if _trace_hook is not None:
        _trace_hook(kind_name, message_key, level, params)


def symbols(*names: str, **assumptions: Any) -> tuple[sp.Symbol, ...]:
    """Crée un tuple de symboles SymPy portant par défaut l'hypothèse real=True (D1).

    Exemples:
        a, = symbols("a")
        a, b = symbols("a b")
        a, b = symbols("a", "b")
    """
    assumptions.setdefault("real", True)
    if len(names) == 1:
        res = sp.symbols(names[0], seq=True, **assumptions)
        return tuple(res)
    result: list[sp.Symbol] = []
    for name in names:
        sub = sp.symbols(name, seq=True, **assumptions)
        result.extend(sub)
    return tuple(result)


def _coerce_float_value(val: float, policy: FloatPolicy) -> sp.Expr:
    if policy == "reject":
        raise InexactInputError(
            f"Entrée flottante {val!r} refusée (float_policy='reject'). "
            "Utilisez un entier, Fraction(p, q) ou une chaîne comme '1/10'."
        )
    if policy == "keep":
        return sp.Float(val)
    # policy == "rationalize"
    rat = sp.Rational(repr(float(val)))
    emit_core_event(
        "WARNING",
        "field.float_rationalized",
        1,
        original=repr(float(val)),
        rational=rat,
    )
    return rat


def _ensure_real_symbols(expr: sp.Expr, *, warn: bool = True) -> sp.Expr:
    replacements: dict[sp.Symbol, sp.Symbol] = {}
    for sym in expr.free_symbols:
        if isinstance(sym, sp.Symbol) and sym.is_real is not True:
            assumptions = dict(sym.assumptions0)
            assumptions["real"] = True
            real_sym = sp.Symbol(sym.name, **assumptions)
            replacements[sym] = real_sym
            if warn:
                emit_core_event(
                    "WARNING",
                    "field.symbol_made_real",
                    2,
                    symbol=sym.name,
                )
    if replacements:
        expr = expr.xreplace(replacements)
    return expr


def match_symbol_substitutions(
    free_syms: Iterable[sp.Symbol],
    mapping: Mapping[Any, Any],
) -> dict[sp.Symbol, sp.Expr]:
    """Construit un dictionnaire de substitution {Symbol -> Expr} en appariant aussi par nom."""
    by_name: dict[str, list[sp.Symbol]] = {}
    for s in free_syms:
        if isinstance(s, sp.Symbol):
            by_name.setdefault(s.name, []).append(s)

    subs_map: dict[sp.Symbol, sp.Expr] = {}
    for k, v in mapping.items():
        val = to_exact(v)
        if isinstance(k, str):
            name = k
            sym_default = sp.Symbol(name, real=True)
            subs_map[sym_default] = val
        elif isinstance(k, sp.Symbol):
            name = k.name
            subs_map[k] = val
            subs_map[sp.Symbol(name, real=True)] = val
        else:
            continue
        for target_sym in by_name.get(name, ()):
            subs_map[target_sym] = val
    return subs_map


def to_exact(x: Any, *, float_policy: FloatPolicy | None = None) -> sp.Expr:
    """Convertit une entrée en expression SymPy exacte selon la politique D1/D2."""
    policy: FloatPolicy = float_policy if float_policy is not None else config.float_policy

    if isinstance(x, bool):
        raise TypeError("Un booléen n'est pas un scalaire valide.")

    if isinstance(x, int):
        return sp.Integer(x)

    if isinstance(x, Fraction):
        return sp.Rational(x.numerator, x.denominator)

    # Support des scalaires NumPy sans imposer l'import de numpy
    type_name = type(x).__module__
    if type_name.startswith("numpy"):
        if hasattr(x, "is_integer") or "int" in type(x).__name__:
            return sp.Integer(int(x))
        if "float" in type(x).__name__:
            return _coerce_float_value(float(x), policy)

    if isinstance(x, float):
        return _coerce_float_value(x, policy)

    if isinstance(x, str):
        try:
            parsed = sp.sympify(x, rational=(policy == "rationalize"))
        except Exception as exc:
            raise ValueError(f"Impossible d'interpréter l'expression {x!r}.") from exc
        if isinstance(parsed, sp.Expr):
            if policy == "reject" and parsed.atoms(sp.Float):
                raise InexactInputError(
                    f"La chaîne {x!r} contient un flottant refusé par float_policy='reject'."
                )
            return _ensure_real_symbols(parsed, warn=False)
        raise ValueError(f"L'entrée {x!r} ne représente pas une expression scalaire.")

    if isinstance(x, sp.Expr):
        expr = x
        float_atoms = list(expr.atoms(sp.Float))
        if float_atoms:
            if policy == "reject":
                raise InexactInputError(
                    f"L'expression {expr!r} contient un flottant ({float_atoms[0]!r}) "
                    "refusé par float_policy='reject'."
                )
            if policy == "rationalize":
                f_map = {
                    fl: _coerce_float_value(float(fl), policy) for fl in float_atoms
                }
                expr = expr.xreplace(f_map)
        return _ensure_real_symbols(expr, warn=True)

    raise TypeError(f"Type d'entrée non supporté pour to_exact : {type(x).__name__}")


def choose_domain(entries: Iterable[sp.Expr]) -> Domain:
    """Sélectionne le domaine le plus petit possible pour DomainMatrix (D10).

    Ordre de préférence :
    1. QQ si toutes les entrées sont rationnelles ;
    2. QQ(params) (corps de fractions rationnelles) si les entrées sont rationnelles en des paramètres ;
    3. Corps algébrique QQ<...> si les entrées sont des nombres algébriques sans paramètres ;
    4. EX en dernier recours.
    """
    items = [sp.sympify(e) for e in entries]
    if not items:
        return QQ

    if all(e.is_Rational for e in items):
        return QQ

    has_symbols = any(bool(e.free_symbols) for e in items)
    has_radicals = any(
        any(sub.is_Pow and not sub.exp.is_Integer for sub in e.atoms(sp.Pow))
        for e in items
    )

    if not has_symbols and has_radicals:
        try:
            dom, _ = construct_domain(items, field=True, extension=True)
            return dom
        except Exception:
            pass

    if has_symbols and not has_radicals:
        try:
            dom, _ = construct_domain(items, field=True)
            if dom != EX:
                return dom
        except Exception:
            pass

    try:
        dom, _ = construct_domain(items, field=True)
        return dom
    except Exception:
        return EX
