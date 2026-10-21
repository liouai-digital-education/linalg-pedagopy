"""Oracle de nullité à quatre verdicts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Any, Iterable, Mapping

import sympy as sp

from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import CaseLimitError, UndecidableZeroError
from linalg_pedagopy.core.field import emit_core_event, pretty_expr, symbols, to_exact


class Verdict(Enum):
    """Les quatre verdicts possibles de l'oracle de nullité."""

    ZERO = auto()
    NONZERO = auto()
    CONDITIONAL = auto()
    UNKNOWN = auto()


AssumptionsType = Condition | Mapping[str | sp.Symbol, Any] | None


@dataclass(frozen=True)
class ZeroDecision:
    """Résultat détaillé d'une décision de l'oracle de nullité.

    Pour un verdict conditionnel, ``cases`` est la condition d'annulation complète :
    l'expression est nulle si et seulement si l'une de ces conditions est vérifiée
    (``a*b`` : ``a = 0`` ou ``b = 0``). ``condition`` n'en est que la première.

    ``domain`` réunit les valeurs interdites par les dénominateurs (par exemple
    ``a ≠ 1`` pour ``(a**2 - 1)/(a - 1)``) : le verdict ne vaut que sur ce domaine.
    """

    verdict: Verdict
    condition: Condition | None = None
    method: str = ""
    factors: tuple[sp.Expr, ...] = ()
    domain: Condition | None = None
    cases: tuple[Condition, ...] = ()

    def format_cases(self) -> str:
        """Condition d'annulation complète en texte, ex. « a = 0 ou b = 0 »."""
        return " ou ".join(c.format_text() for c in self.cases)


def _normalize_assumptions(assumptions: Any) -> Condition:
    if assumptions is None:
        return Condition.true()
    if isinstance(assumptions, Condition):
        return assumptions
    if isinstance(assumptions, str):
        return _parse_single_assumption(assumptions)
    if isinstance(assumptions, (list, tuple, set)):
        cond = Condition.true()
        for item in assumptions:
            cond = cond & _normalize_assumptions(item)
        return cond
    if isinstance(assumptions, Mapping):
        cond = Condition.true()
        for k, v in assumptions.items():
            sym = symbols(k)[0] if isinstance(k, str) else k
            if isinstance(v, (list, tuple, set)):
                for sub_v in v:
                    cond = cond & _parse_mapping_val(sym, sub_v)
            else:
                cond = cond & _parse_mapping_val(sym, v)
        return cond
    return Condition.true()


def _parse_mapping_val(sym: sp.Symbol, v: Any) -> Condition:
    if isinstance(v, str):
        v_s = v.strip()
        if v_s.startswith("!="):
            rhs = to_exact(v_s[2:].strip())
            return Condition.neq(sym, rhs)
        if v_s.startswith("=="):
            rhs = to_exact(v_s[2:].strip())
            return Condition.eq(sym, rhs)
        if v_s.startswith("="):
            rhs = to_exact(v_s[1:].strip())
            return Condition.eq(sym, rhs)
    return Condition.eq(sym, to_exact(v))


def _parse_single_assumption(s: str) -> Condition:
    s = s.strip()
    if "!=" in s:
        lhs_s, rhs_s = s.split("!=", 1)
        lhs = to_exact(lhs_s.strip())
        rhs = to_exact(rhs_s.strip())
        from linalg_pedagopy.core.cases import _normalize_relation_expr

        diff = sp.simplify(lhs - rhs)
        norm_l, norm_r = _normalize_relation_expr(diff)
        return Condition.neq(norm_l, norm_r)
    if "==" in s:
        lhs_s, rhs_s = s.split("==", 1)
        lhs = to_exact(lhs_s.strip())
        rhs = to_exact(rhs_s.strip())
        return Condition.eq(lhs, rhs)
    if "=" in s:
        lhs_s, rhs_s = s.split("=", 1)
        lhs = to_exact(lhs_s.strip())
        rhs = to_exact(rhs_s.strip())
        return Condition.eq(lhs, rhs)
    return Condition.true()


def _extract_polynomial_factors(num: sp.Expr) -> list[sp.Expr]:
    """Extrait les facteurs irréductibles non constants d'un polynôme."""
    try:
        _, factors_list = sp.factor_list(num)
        res = [f for f, _exp in factors_list if f.free_symbols]
        return res if res else [num]
    except Exception:
        return [num]


def sum_of_squares(poly: Any) -> tuple[tuple[tuple[sp.Expr, sp.Expr], ...], sp.Expr] | None:
    """Réduction de Gauss d'un polynôme réel de degré 2 : p = Σ c_k·ℓ_k² + r, avec c_k > 0.

    Les carrés sont complétés paramètre par paramètre (ordre alphabétique) ; chaque
    ℓ_k est linéaire et r est une constante. Renvoie ``None`` si le polynôme n'est pas
    de degré total 2 à coefficients rationnels en des symboles réels, ou s'il n'est pas
    minoré (un coefficient de carré ≤ 0 ou un paramètre qui n'apparaît qu'au degré 1).

    Exemple : a² + a·b + b² + 1 = (a + b/2)² + 3/4·b² + 1.
    """
    expr = sp.expand(to_exact(poly))
    syms = sorted(expr.free_symbols, key=lambda x: x.name)
    if not syms or not all(isinstance(x, sp.Symbol) and x.is_real is True for x in syms):
        return None
    try:
        P = sp.Poly(expr, *syms)
    except sp.PolynomialError:
        return None
    if P.total_degree() != 2 or not all(c.is_Rational for c in P.coeffs()):
        return None
    squares: list[tuple[sp.Expr, sp.Expr]] = []
    rest = expr
    for x in syms:
        q = sp.Poly(rest, x)
        if q.degree() <= 0:
            continue
        if q.degree() == 1:
            return None
        c2 = q.coeff_monomial(x**2)
        c1 = q.coeff_monomial(x)
        if not (c2.is_Rational and c2 > 0):
            return None
        lin = sp.expand(x + c1 / (2 * c2))
        squares.append((c2, lin))
        rest = sp.expand(rest - c2 * lin**2)
    if rest.free_symbols:
        return None
    return tuple(squares), rest


def strict_sign(poly: Any) -> tuple[int, str] | None:
    """Signe strict et constant sur R^k d'un polynôme de degré 2 en plusieurs paramètres, avec son certificat.

    Renvoie ``(1, "(a + b/2)² + 3/4·b² + 1")`` si le polynôme est > 0 partout,
    ``(-1, …)`` s'il est < 0 partout (certificat de son opposé), ``None`` sinon : il
    s'annule alors en un point réel, ou la méthode ne s'applique pas.
    """
    for sign in (1, -1):
        dec = sum_of_squares(sign * sp.expand(to_exact(poly)))
        if dec is None:
            continue
        squares, rest = dec
        if rest.is_Rational and rest > 0:
            parts = []
            for c, lin in squares:
                carre = pretty_expr(lin**2) if lin.is_Symbol else f"({pretty_expr(lin)})²"
                parts.append(carre if c == 1 else f"{pretty_expr(c)}·{carre}")
            parts.append(pretty_expr(rest))
            return sign, " + ".join(parts)
    return None


def _never_zero(fac: sp.Expr) -> bool:
    """Facteur à plusieurs paramètres de signe strict constant sur R (somme de carrés et d'une constante)."""
    return len(fac.free_symbols) >= 2 and strict_sign(fac) is not None


def _denominator_factors(expr: sp.Expr) -> list[sp.Expr]:
    """Facteurs non constants du dénominateur, relevés avant toute simplification.

    Seuls les dénominateurs polynomiaux sont analysés ; un radical au dénominateur
    imposerait une inégalité, que ``Condition`` ne représente pas.
    """
    free = expr.free_symbols
    if not free:
        return []
    try:
        _num, den = sp.fraction(sp.together(expr))
        if not den.free_symbols or not den.is_polynomial(*free):
            return []
        _, factors_list = sp.factor_list(sp.expand(den))
    except Exception:
        return []
    return [
        f
        for f, _exp in factors_list
        if f.free_symbols and not (f.is_positive is True or f.is_negative is True or _never_zero(f))
    ]


def domain_of(exprs: Iterable[Any], assumptions: AssumptionsType = None) -> Condition:
    """Domaine de définition commun d'expressions : conjonction des ``facteur ≠ 0`` de leurs dénominateurs.

    Les facteurs déjà non nuls sous les hypothèses sont omis ; un facteur que les
    hypothèses annulent donne une condition contradictoire avec elles.
    """
    cond = _normalize_assumptions(assumptions)
    domain = Condition.true()
    for e in exprs:
        expr = to_exact(e) if not isinstance(e, sp.Expr) else e
        for fac in _denominator_factors(expr):
            if (cond & domain).implies_zero(fac) is not False:
                domain = domain & Condition.from_zero_expr(fac, is_zero=False)
    return domain


def _extract_factors(expr: sp.Expr) -> list[sp.Expr]:
    """Extrait les facteurs polynomiaux ou issus de puissances/radicaux (y compris via unrad)."""
    free = expr.free_symbols
    if not free:
        return []
    if expr.is_rational_function(*free):
        together_expr = sp.together(sp.cancel(expr))
        num, _den = sp.fraction(together_expr)
        num_expanded = sp.expand(num)
        if num_expanded == 0:
            return [sp.Integer(0)]
        return _extract_polynomial_factors(num_expanded)

    factors: list[sp.Expr] = []
    try:
        together_expr = sp.together(expr)
        num, _den = sp.fraction(together_expr)
        if num == 0:
            return [sp.Integer(0)]
        powers = num.as_powers_dict()
        for base, exp in powers.items():
            if exp.is_number and exp > 0 and base.has(*free):
                if base.is_rational_function(*free):
                    together_b = sp.together(sp.cancel(base))
                    num_b, _ = sp.fraction(together_b)
                    for fac in _extract_polynomial_factors(sp.expand(num_b)):
                        if fac not in factors:
                            factors.append(fac)
        if not factors:
            from sympy.solvers.solvers import unrad

            unrad_res = unrad(num, *sorted(free, key=lambda s: s.name))
            if unrad_res is not None:
                poly_eq, cov = unrad_res
                if not cov:
                    for fac in _extract_polynomial_factors(sp.expand(poly_eq)):
                        if fac not in factors:
                            factors.append(fac)
    except Exception:
        pass
    return factors


def assumption_text(fac: sp.Expr) -> str:
    """Hypothèse « facteur ≠ 0 » écrite pour ``assumptions=`` : ``a - 1`` donne ``"a != 1"``."""
    cond = Condition.from_zero_expr(fac, is_zero=False)
    lhs, rhs = cond.neqs[0]
    return f"{sp.sstr(lhs)} != {sp.sstr(rhs)}"


def case_limit_error(
    *,
    limit: str,
    value: int,
    reached: int,
    factors: Iterable[sp.Expr],
    condition: Condition,
    argument: str | None,
) -> CaseLimitError:
    """Erreur de plafond de discussion par cas, avec un message qui dit quoi faire.

    ``limit`` vaut ``"max_cases"`` (nombre de cas ouverts) ou ``"max_depth"`` (cas
    emboîtés) ; ``argument`` est le nom du paramètre de la procédure qui règle ce
    plafond (``None`` si seule la configuration le règle).
    """
    facs: list[sp.Expr] = []
    for f in factors:
        if f not in facs:
            facs.append(f)
    config_attr = "max_cases" if limit == "max_cases" else "max_case_depth"
    new_value = max(2 * value, reached) if limit == "max_cases" else value + 1
    if limit == "max_cases":
        head = (
            f"Discussion par cas arrêtée : elle demande au moins {reached} branches, "
            f"au-delà du plafond max_cases={value}."
        )
    else:
        head = (
            f"Discussion par cas arrêtée : elle demande plus de {value} niveau{'x' if value > 1 else ''} de cas emboîtés "
            f"(plafond max_depth={value})."
        )
    lines = [head]
    if facs:
        lines.append("Facteurs qui ouvrent des cas : " + ", ".join(pretty_expr(f) for f in facs) + ".")
    if not condition.is_trivial:
        lines.append(f"Branche en cours : {condition.format_text()}.")
    suggestion = assumption_text(facs[0]) if facs else None
    raise_cap = f"{argument}={new_value}, ou config.{config_attr} = {new_value}" if argument else f"config.{config_attr} = {new_value}"
    if suggestion:
        lines.append(
            f'Pour poursuivre : précisez des hypothèses sur les paramètres, par exemple assumptions="{suggestion}", '
            f"ou relevez le plafond ({raise_cap})."
        )
    else:
        lines.append(f"Pour poursuivre : relevez le plafond ({raise_cap}).")
    return CaseLimitError(
        "\n".join(lines),
        limit=limit,
        value=value,
        reached=reached,
        factors=tuple(facs),
        condition=condition,
        suggested_assumption=suggestion,
    )


class ZeroOracle:
    """Oracle de nullité formel suivant la stratégie en 5 étapes de la décision D3."""

    def decide(
        self,
        e: Any,
        assumptions: AssumptionsType = None,
        *,
        trace_level3: bool = True,
    ) -> ZeroDecision:
        """Détermine si l'expression e est nulle, non nulle, conditionnelle ou indécidable."""
        expr = to_exact(e) if not isinstance(e, sp.Expr) else e
        cond = _normalize_assumptions(assumptions)

        # Valeurs interdites par les dénominateurs, avant que la simplification ne les efface
        domain = Condition.true()
        for fac in _denominator_factors(expr):
            status = cond.implies_zero(fac)
            if status is True:
                return ZeroDecision(verdict=Verdict.UNKNOWN, condition=None, method="undefined")
            if status is None:
                domain = domain & Condition.from_zero_expr(fac, is_zero=False)
        if domain.is_trivial:
            return self._decide(expr, cond, trace_level3=trace_level3)
        dec = self._decide(expr, cond & domain, trace_level3=trace_level3)
        return replace(dec, domain=domain)

    def _decide(self, expr: sp.Expr, cond: Condition, *, trace_level3: bool) -> ZeroDecision:
        # Application des substitutions d'égalités connues dans le contexte (ex. a = 1)
        subs_map = cond.substitutions()
        if subs_map:
            expr = expr.xreplace(subs_map)

        # Si l'expression contient une fonction non interprétée (AppliedUndef), c'est indécidable
        if expr.atoms(sp.core.function.AppliedUndef):
            return ZeroDecision(verdict=Verdict.UNKNOWN, condition=None, method="unknown")

        free_syms = expr.free_symbols

        # Étape 1 : Domaine exact (Q ou Q(params))
        if not free_syms and expr.is_Rational:
            verdict = Verdict.ZERO if expr == 0 else Verdict.NONZERO
            decision = ZeroDecision(verdict=verdict, condition=None, method="domain")
            if trace_level3 and verdict == Verdict.ZERO:
                emit_core_event("CHECK", "zero.domain_zero", 3, expr=expr)
            return decision

        if free_syms:
            # Vérifier si la condition courante tranche directement l'expression
            direct_status = cond.implies_zero(expr)
            if direct_status is True:
                if trace_level3:
                    emit_core_event("CHECK", "zero.domain_zero", 3, expr=expr)
                return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="domain")
            if direct_status is False:
                return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="domain")

            # Si les hypothèses SymPy sur les symboles (ou la positivité sur R) garantissent non-zéro
            if (
                expr.is_zero is False
                or expr.is_nonzero is True
                or expr.is_positive is True
                or expr.is_negative is True
            ):
                return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="domain")

            is_rat = expr.is_rational_function(*free_syms)
            factors = _extract_factors(expr)
            if factors:
                if factors == [sp.Integer(0)]:
                    if trace_level3:
                        emit_core_event("CHECK", "zero.domain_zero", 3, expr=expr)
                    return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="domain")

                # Filtrer les facteurs déjà connus non nuls via cond
                active_factors: list[sp.Expr] = []
                for fac in factors:
                    if (
                        fac.is_zero is False
                        or fac.is_nonzero is True
                        or fac.is_positive is True
                        or fac.is_negative is True
                    ):
                        continue
                    if len(fac.free_symbols) >= 2:
                        certificate = strict_sign(fac)
                        if certificate is not None:
                            if trace_level3:
                                emit_core_event(
                                    "CHECK",
                                    "zero.sign_definite",
                                    3,
                                    expr=fac,
                                    certificate=certificate[1] if certificate[0] > 0 else f"−({certificate[1]})",
                                    sign=">" if certificate[0] > 0 else "<",
                                )
                            continue
                    status = cond.implies_zero(fac)
                    if status is True:
                        if is_rat:
                            if trace_level3:
                                emit_core_event("CHECK", "zero.domain_zero", 3, expr=expr)
                            return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="domain")
                        # Pour une expression avec radicaux, vérifier que l'annulation du facteur annule expr
                        if sp.simplify(expr) == 0:
                            return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="domain")
                    if status is None:
                        active_factors.append(fac)

                if not active_factors:
                    return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="domain")

                # Vérifier si les facteurs s'annulent sur R (et éliminer les racines parasites d'unrad)
                real_factors: list[sp.Expr] = []
                for fac in active_factors:
                    if len(fac.free_symbols) == 1:
                        sym = next(iter(fac.free_symbols))
                        try:
                            real_roots = sp.solve(fac, sym)
                            if not real_roots:
                                continue
                            if not is_rat:
                                valid_roots = [
                                    r
                                    for r in real_roots
                                    if sp.simplify(expr.xreplace({sym: r})) == 0
                                ]
                                if not valid_roots:
                                    continue
                                if len(valid_roots) < len(real_roots):
                                    for vr in valid_roots:
                                        lin_fac = sym - vr
                                        st = cond.implies_zero(lin_fac)
                                        if st is True:
                                            return ZeroDecision(
                                                verdict=Verdict.ZERO,
                                                condition=None,
                                                method="domain",
                                            )
                                        if st is None and lin_fac not in real_factors:
                                            real_factors.append(lin_fac)
                                    continue
                        except Exception:
                            pass
                    if fac not in real_factors:
                        real_factors.append(fac)

                if not real_factors:
                    return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="domain")

                zero_cases = tuple(
                    Condition.from_zero_expr(fac, is_zero=True) for fac in real_factors
                )
                return ZeroDecision(
                    verdict=Verdict.CONDITIONAL,
                    condition=zero_cases[0],
                    method="domain",
                    factors=tuple(real_factors),
                    cases=zero_cases,
                )

        # Étape 2 : Nombres algébriques (radicaux sans paramètres)
        if not free_syms and expr.is_algebraic_expr():
            try:
                x_dummy = sp.Dummy("x")
                minpoly = sp.minimal_polynomial(expr, x_dummy)
                if minpoly == x_dummy:
                    if trace_level3:
                        emit_core_event("CHECK", "zero.minpoly_zero", 3, expr=expr)
                    return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="minpoly")
                return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="minpoly")
            except Exception:
                pass

        # Étape 3 : Simplification (radsimp, simplify, equals)
        try:
            s1 = sp.radsimp(expr)
            if s1 == 0:
                if trace_level3:
                    emit_core_event("CHECK", "zero.simplify_zero", 3, expr=expr)
                return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="simplify")
            s2 = sp.simplify(s1)
            if s2 == 0:
                if trace_level3:
                    emit_core_event("CHECK", "zero.simplify_zero", 3, expr=expr)
                return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="simplify")
            if (
                s2.is_zero is False
                or s2.is_nonzero is True
                or s2.is_positive is True
                or s2.is_negative is True
            ):
                return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="simplify")
            if not free_syms and s2.equals(0) is True:
                if trace_level3:
                    emit_core_event("CHECK", "zero.simplify_zero", 3, expr=expr)
                return ZeroDecision(verdict=Verdict.ZERO, condition=None, method="simplify")
        except Exception:
            s2 = expr

        # Si après simplification on retrouve une fraction rationnelle en des paramètres
        if s2 != expr and s2.free_symbols and s2.is_rational_function(*s2.free_symbols):
            return self.decide(s2, cond, trace_level3=trace_level3)

        # Étape 4 : Contrôle numérique en haute précision (evalf(50))
        # Ne conclut jamais seul à ZERO, mais peut confirmer NONZERO (sans paramètres)
        if not free_syms:
            try:
                val50 = expr.evalf(50)
                if val50.is_Number and abs(val50) > sp.Float("1e-35", 50):
                    return ZeroDecision(verdict=Verdict.NONZERO, condition=None, method="numeric")
            except Exception:
                pass

        # Étape 5 : Sinon UNKNOWN
        return ZeroDecision(verdict=Verdict.UNKNOWN, condition=None, method="unknown")

    def is_zero(self, e: Any, assumptions: AssumptionsType = None) -> bool:
        """Renvoie True si e == 0, False si e != 0, ou lève UndecidableZeroError."""
        dec = self.decide(e, assumptions=assumptions)
        if dec.verdict == Verdict.ZERO:
            return True
        if dec.verdict == Verdict.NONZERO:
            return False
        raise UndecidableZeroError(e)


oracle = ZeroOracle()


def decide_all_zero(exprs: Iterable[Any], assumptions: AssumptionsType = None) -> bool | CaseSplit[bool]:
    """Décide si toutes les expressions sont nulles, avec une discussion de cas disjoints et exhaustifs.

    Sur un verdict conditionnel, on sépare comme Gauss-Jordan : tous les facteurs
    non nuls (branche générique), puis le facteur i nul et les précédents non nuls.
    """
    items = [to_exact(e) if not isinstance(e, sp.Expr) else e for e in exprs]
    return _all_zero(items, _normalize_assumptions(assumptions), depth=0)


def _all_zero(exprs: list[sp.Expr], cond: Condition, *, depth: int) -> bool | CaseSplit[bool]:
    # Une composante non nulle tranche tout de suite, sans discussion inutile
    decisions: list[ZeroDecision] = []
    for e in exprs:
        dec = oracle.decide(e, assumptions=cond)
        if dec.verdict == Verdict.NONZERO:
            return False
        decisions.append(dec)
    for e, dec in zip(exprs, decisions):
        if dec.verdict == Verdict.UNKNOWN:
            oracle.is_zero(e, assumptions=cond)  # lève UndecidableZeroError
        if dec.verdict != Verdict.CONDITIONAL:
            continue
        if depth >= config.max_case_depth:
            raise case_limit_error(
                limit="max_depth",
                value=config.max_case_depth,
                reached=depth + 1,
                factors=dec.factors,
                condition=cond,
                argument=None,
            )
        sub_conds = [cond]
        for fac in dec.factors:
            sub_conds[0] = sub_conds[0] & Condition.from_zero_expr(fac, is_zero=False)
        prefix = cond
        for fac in dec.factors:
            sub_conds.append(prefix & Condition.from_zero_expr(fac, is_zero=True))
            prefix = prefix & Condition.from_zero_expr(fac, is_zero=False)
        branches: list[Branch[bool]] = []
        for sub in sub_conds:
            if sub.is_contradictory:
                continue
            res = _all_zero(exprs, sub, depth=depth + 1)
            if isinstance(res, CaseSplit):
                branches.extend(res.branches)
            else:
                branches.append(Branch(condition=sub, result=res))
        return CaseSplit(branches=tuple(branches))
    return True
