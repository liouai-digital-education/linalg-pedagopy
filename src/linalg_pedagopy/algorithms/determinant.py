"""Déterminant exact tracé : Bareiss, élimination, développement par cofacteurs, règle de Sarrus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

import sympy as sp

from linalg_pedagopy.algorithms.base import Procedure, Result
from linalg_pedagopy.algorithms.elimination import (
    EliminationEngine,
    EliminationSetup,
    EliminationState,
    RowOps,
    _simplify_entry,
)
from linalg_pedagopy.config import config
from linalg_pedagopy.core.cases import Branch, CaseSplit, Condition
from linalg_pedagopy.core.exceptions import DimensionMismatchError, PedagopyError
from linalg_pedagopy.core.zero import (
    AssumptionsType,
    Verdict,
    _normalize_assumptions,
    decide_all_zero,
    domain_of,
    oracle,
)
from linalg_pedagopy.objects.matrix import Matrix, register_procedure
from linalg_pedagopy.trace.step import StepKind
from linalg_pedagopy.trace.tracer import record, section

DetMethod = Literal["auto", "bareiss", "elimination", "cofactors", "sarrus"]
_METHODES = ("auto", "bareiss", "elimination", "cofactors", "sarrus")
# Noms affichés dans les traces et les résumés
NOMS_METHODES = {
    "bareiss": "Bareiss",
    "elimination": "élimination",
    "cofactors": "cofacteurs",
    "sarrus": "Sarrus",
}
COFACTEURS_TAILLE_MAX = 4
# Opérations de lignes tracées du déterminant : clés det.*, transvections « L_i ← L_i − (λ)·L_j »
_OPS = RowOps("det", snapshot_key="matrix", signed_add=False)


def _finaliser(expr: Any) -> sp.Expr:
    """Forme lisible du déterminant : fraction rationnelle factorisée, ou expression simplifiée."""
    e = _simplify_entry(sp.sympify(expr))
    if e.free_symbols and e.is_rational_function(*e.free_symbols):
        return sp.factor(e)
    return e


def _est_nul(expr: sp.Expr, cond: Condition) -> bool | None:
    """True si nul, False si non nul, None si l'annulation dépend des paramètres."""
    dec = oracle.decide(expr, assumptions=cond)
    if dec.verdict == Verdict.ZERO:
        return True
    if dec.verdict == Verdict.NONZERO:
        return False
    if dec.verdict == Verdict.UNKNOWN:
        oracle.is_zero(expr, assumptions=cond)  # lève UndecidableZeroError
    return None


@dataclass(frozen=True)
class DetResult(Result):
    """Résultat typé du calcul d'un déterminant."""

    A: Matrix = Matrix([])
    value: sp.Expr = sp.Integer(0)
    method: str = ""
    factors: tuple[tuple[sp.Expr, int], ...] = ()
    condition: Condition = field(default_factory=Condition.true)

    def subs(self, mapping: Mapping[Any, Any]) -> DetResult:
        valeur = _finaliser(self.value.subs(mapping))
        return DetResult(
            trace=self.trace,
            A=self.A.subs(mapping),
            value=valeur,
            method=self.method,
            factors=_facteurs(valeur),
            condition=self.condition,
        )

    def zeros(self, *, split: bool = False) -> tuple[Condition, ...] | bool | CaseSplit[bool]:
        """Valeurs des paramètres qui annulent le déterminant.

        Sans ``split`` : la disjonction des conditions d'annulation (``(a = 1, a = −2)``) ;
        ``()`` si le déterminant ne s'annule jamais, ``(toujours,)`` s'il est identiquement nul.
        Avec ``split=True`` : la matrice est-elle inversible ? (``bool`` ou ``CaseSplit[bool]``).
        """
        if split:
            nul = decide_all_zero([self.value], self.condition)
            if isinstance(nul, bool):
                return not nul
            return CaseSplit(
                branches=tuple(Branch(b.condition, not b.result, b.trace) for b in nul.branches)
            )
        dec = oracle.decide(self.value, assumptions=self.condition)
        if dec.verdict == Verdict.ZERO:
            return (Condition.true(),)
        if dec.verdict == Verdict.NONZERO:
            return ()
        if dec.verdict == Verdict.UNKNOWN:
            oracle.is_zero(self.value, assumptions=self.condition)
        return dec.cases

    def _branch_summary_lines(self) -> list[str]:
        return [f"det A = {sp.sstr(self.value)} (méthode : {NOMS_METHODES.get(self.method, self.method)})"]

    def _run_verification(self) -> None:
        # Contrôle indépendant : algorithme de Berkowitz de SymPy, sans division
        temoin = sp.Matrix(self.A.entries_grid).det(method="berkowitz")
        ecart = sp.simplify(sp.sympify(temoin) - self.value)
        record(
            StepKind.CHECK,
            "det.verify",
            level=1,
            method=NOMS_METHODES.get(self.method, self.method),
            ok="résultat confirmé"
            if oracle.decide(ecart, assumptions=self.condition).verdict == Verdict.ZERO
            else "ÉCART DÉTECTÉ",
        )


def _facteurs(valeur: sp.Expr) -> tuple[tuple[sp.Expr, int], ...]:
    """Facteurs non constants du numérateur, avec leur multiplicité."""
    if not valeur.free_symbols:
        return ()
    try:
        num, _den = sp.fraction(sp.together(valeur))
        _, liste = sp.factor_list(num)
    except Exception:
        return ()
    return tuple((f, int(m)) for f, m in liste if f.free_symbols)


class Determinant(Procedure[DetResult]):
    """Calcul tracé du déterminant d'une matrice carrée, en arithmétique exacte."""

    def __init__(
        self,
        A: Matrix,
        *,
        method: DetMethod = "auto",
        assumptions: AssumptionsType = None,
    ) -> None:
        if not isinstance(A, Matrix):
            A = Matrix(A)
        if A.rows != A.cols:
            raise DimensionMismatchError(
                f"Le déterminant n'est défini que pour une matrice carrée (reçu {A.rows}×{A.cols})."
            )
        if method not in _METHODES:
            raise ValueError(f"Méthode de déterminant inconnue : {method!r} (attendu : {', '.join(_METHODES)}).")
        if method == "sarrus" and A.rows != 3:
            raise DimensionMismatchError(
                f"La règle de Sarrus ne s'applique qu'aux matrices 3×3 (reçu {A.rows}×{A.cols})."
            )
        if method == "cofactors" and A.rows > COFACTEURS_TAILLE_MAX:
            raise PedagopyError(
                f"Le développement par cofacteurs est limité aux matrices {COFACTEURS_TAILLE_MAX}×"
                f"{COFACTEURS_TAILLE_MAX} (reçu {A.rows}×{A.cols}) : utilisez method='bareiss'."
            )
        self.A = A
        self.method: DetMethod = method
        self.assumptions = _normalize_assumptions(assumptions)

    def _execute(self) -> DetResult | CaseSplit[DetResult]:
        cond = self.assumptions
        domaine = domain_of(self.A.flat_entries, cond)
        if not domaine.is_trivial:
            cond = cond & domaine
            if cond.is_contradictory:
                raise PedagopyError(
                    f"Les coefficients ne sont pas définis sous les hypothèses données : ils exigent {domaine}."
                )
            record(StepKind.INFO, "det.domain", level=1, domain=domaine)

        subs_map = cond.substitutions()
        A_cur = self.A.subs(subs_map) if subs_map else self.A
        n = A_cur.rows
        methode = self.method
        if methode == "auto":
            methode = "bareiss" if any(e.free_symbols for e in A_cur.flat_entries) else "elimination"

        grille = [[_simplify_entry(A_cur[i, j]) for j in range(n)] for i in range(n)]
        with section("det.start", level=1, snapshot={"matrix": A_cur}, n=n, method=NOMS_METHODES[methode]):
            if self.method == "auto":
                record(StepKind.INFO, "det.auto", level=2, method=NOMS_METHODES[methode])
            if methode == "elimination" and n > 0:
                # Moteur d'élimination : discussion par cas si un pivot peut s'annuler
                return self._elimination(cond)
            if n == 0:
                brut: sp.Expr = sp.Integer(1)
            elif methode == "bareiss":
                brut = self._bareiss(grille, cond)
            elif methode == "cofactors":
                brut = self._cofacteurs(grille, cond, profondeur=0)
            else:
                brut = self._sarrus(grille)
            return self._resultat(A_cur, brut, methode, cond)

    @staticmethod
    def _resultat(A_cur: Matrix, brut: sp.Expr, methode: str, cond: Condition) -> DetResult:
        valeur = _finaliser(brut)
        record(StepKind.RESULT, "det.result", level=1, value=valeur)
        return DetResult(
            A=A_cur, value=valeur, method=methode, factors=_facteurs(valeur), condition=cond
        )

    # --- Bareiss -------------------------------------------------------------------------

    @staticmethod
    def _bareiss(M: list[list[sp.Expr]], cond: Condition) -> sp.Expr:
        n = len(M)
        signe = 1
        echanges = 0
        precedent: sp.Expr = sp.Integer(1)
        record(StepKind.INFO, "det.bareiss_intro", level=1)
        for k in range(n - 1):
            if _est_nul(M[k][k], cond) is True:
                # Un pivot n'est évité que s'il est identiquement nul (en tant que polynôme)
                autre = next((i for i in range(k + 1, n) if _est_nul(M[i][k], cond) is not True), None)
                if autre is None:
                    record(StepKind.INFO, "det.zero_column", level=1, col=k + 1)
                    return sp.Integer(0)
                signe = -signe
                echanges += 1
                _OPS.swap(M, k, autre, col=k)
            pivot = M[k][k]
            _OPS.bareiss_step(M, k, precedent)
            precedent = pivot
        resultat = M[n - 1][n - 1] if signe == 1 else -M[n - 1][n - 1]
        record(StepKind.INFO, "det.bareiss_last", level=1, value=M[n - 1][n - 1], swaps=echanges)
        return resultat

    # --- Élimination sans dilatation --------------------------------------------------------

    def _elimination(self, cond: Condition) -> DetResult | CaseSplit[DetResult]:
        """Triangulation sans dilatation sur le moteur : det A = (−1)^échanges × produit des pivots.

        Un pivot qui peut s'annuler selon les paramètres ouvre une discussion par cas ;
        une colonne sans pivot non nul arrête le calcul (déterminant nul).
        """
        engine: EliminationEngine[DetResult] = EliminationEngine(
            prefix="det",
            setup=self._setup_elimination,
            on_complete=self._fin_elimination,
            reduce_above=False,
            normalize_pivots=False,
            snapshot_key="matrix",
            signed_add=False,
            start_section=False,
            column_sections=False,
            stop_on_zero_column=True,
            limit_arguments=False,
            max_depth=config.max_case_depth,
            max_cases=config.max_cases,
        )
        return engine.run(cond)

    def _setup_elimination(self, cond: Condition) -> EliminationSetup:
        subs_map = cond.substitutions()
        A_cur = self.A.subs(subs_map) if subs_map else self.A
        n = A_cur.rows
        grille = [[_simplify_entry(A_cur[i, j]) for j in range(n)] for i in range(n)]
        return EliminationSetup(grid=grille, n_cols=n, context=A_cur)

    def _fin_elimination(self, st: EliminationState) -> DetResult:
        n = st.setup.n_cols
        if len(st.pivots) < n:
            brut: sp.Expr = sp.Integer(0)  # colonne sans pivot : déjà annoncée par det.zero_column
        else:
            pivots = [st.grid[k][k] for k in range(n)]
            produit = sp.Mul(*pivots)
            pair = st.swaps % 2 == 0
            record(
                StepKind.INFO,
                "det.product",
                level=1,
                pivots=tuple(pivots),
                sign="+" if pair else "−",
                swaps=st.swaps,
            )
            brut = produit if pair else -produit
        return self._resultat(st.setup.context, brut, "elimination", st.cond)

    # --- Cofacteurs ---------------------------------------------------------------------------

    @classmethod
    def _cofacteurs(cls, M: list[list[sp.Expr]], cond: Condition, *, profondeur: int) -> sp.Expr:
        n = len(M)
        niveau = min(1 + profondeur, 3)
        if n == 1:
            return M[0][0]
        if n == 2:
            valeur = _simplify_entry(M[0][0] * M[1][1] - M[0][1] * M[1][0])
            record(
                StepKind.INFO,
                "det.two_by_two",
                level=niveau,
                a=M[0][0], b=M[0][1], c=M[1][0], d=M[1][1], value=valeur,
            )
            return valeur
        nuls = [[_est_nul(M[i][j], cond) is True for j in range(n)] for i in range(n)]
        par_ligne = [sum(nuls[i]) for i in range(n)]
        par_colonne = [sum(nuls[i][j] for i in range(n)) for j in range(n)]
        if max(par_colonne) > max(par_ligne):
            axe, indice = "colonne", par_colonne.index(max(par_colonne))
            positions = [(i, indice) for i in range(n)]
        else:
            axe, indice = "ligne", par_ligne.index(max(par_ligne))
            positions = [(indice, j) for j in range(n)]
        total: sp.Expr = sp.Integer(0)
        with section("det.cofactor_expansion", level=niveau, axis=axe, index=indice + 1, n=n):
            for i, j in positions:
                coef = M[i][j]
                if nuls[i][j]:
                    record(StepKind.INFO, "det.cofactor_skip", level=min(niveau + 1, 3), i=i + 1, j=j + 1)
                    continue
                mineur_lignes = [[M[r][c] for c in range(n) if c != j] for r in range(n) if r != i]
                with section(
                    "det.minor",
                    level=min(niveau + 1, 3),
                    snapshot={"matrix": Matrix._from_exact_rows(mineur_lignes)},
                    i=i + 1,
                    j=j + 1,
                ):
                    mineur = cls._cofacteurs(mineur_lignes, cond, profondeur=profondeur + 1)
                signe = "+" if (i + j) % 2 == 0 else "−"
                terme = coef * mineur if (i + j) % 2 == 0 else -coef * mineur
                record(
                    StepKind.INFO,
                    "det.cofactor_term",
                    level=niveau,
                    i=i + 1, j=j + 1, sign=signe, coef=coef, minor=_simplify_entry(mineur),
                )
                total += terme
        return _simplify_entry(total)

    # --- Sarrus -------------------------------------------------------------------------------

    @staticmethod
    def _sarrus(M: list[list[sp.Expr]]) -> sp.Expr:
        (a, b, c), (d, e, f), (g, h, i) = M
        plus = (a * e * i, b * f * g, c * d * h)
        moins = (c * e * g, a * f * h, b * d * i)
        record(StepKind.INFO, "det.sarrus_plus", level=1, terms=tuple(_simplify_entry(t) for t in plus))
        record(StepKind.INFO, "det.sarrus_minus", level=1, terms=tuple(_simplify_entry(t) for t in moins))
        return _simplify_entry(sp.Add(*plus) - sp.Add(*moins))


register_procedure("determinant", Determinant)
