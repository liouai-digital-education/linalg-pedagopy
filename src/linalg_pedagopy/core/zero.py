"""Oracle de nullité à quatre verdicts (§5.1.2, D3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Mapping

import sympy as sp

from linalg_pedagopy.core.cases import Condition
from linalg_pedagopy.core.exceptions import UndecidableZeroError
from linalg_pedagopy.core.field import emit_core_event, symbols, to_exact


class Verdict(Enum):
    """Les quatre verdicts possibles de l'oracle de nullité (D3)."""

    ZERO = auto()
    NONZERO = auto()
    CONDITIONAL = auto()
    UNKNOWN = auto()


AssumptionsType = Condition | Mapping[str | sp.Symbol, Any] | None


@dataclass(frozen=True)
class ZeroDecision:
    """Résultat détaillé d'une décision de l'oracle de nullité."""

    verdict: Verdict
    condition: Condition | None = None
    method: str = ""
    factors: tuple[sp.Expr, ...] = ()


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

                first_cond = Condition.from_zero_expr(real_factors[0], is_zero=True)
                return ZeroDecision(
                    verdict=Verdict.CONDITIONAL,
                    condition=first_cond,
                    method="domain",
                    factors=tuple(real_factors),
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
