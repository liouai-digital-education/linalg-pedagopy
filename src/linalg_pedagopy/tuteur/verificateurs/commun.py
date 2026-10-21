"""Résultat de vérification et outils communs aux vérificateurs du tuteur."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

import sympy as sp

from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan
from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.algorithms.least_squares import LeastSquares
from linalg_pedagopy.algorithms.qr import QR
from linalg_pedagopy.algorithms.triangular import BackSubstitution, ForwardSubstitution
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tuteur.evaluation_sure import evaluer, expression


def raison_illisible(texte: str, exc: BaseException | None = None) -> str:
    """Explique en français pourquoi une saisie ne peut pas être lue.

    Le message d'exception de SymPy ou de Python n'est jamais recopié : il est en
    anglais, peu lisible pour un étudiant et change d'une version à l'autre.
    """
    t = str(texte)
    if "\n" in t.strip() or re.search(r"[⎛-⎯─-╿]", t):
        return "écrivez la formule sur une seule ligne, en texte (pas une matrice ou une expression affichée)."
    if re.search(r"(?<![=!<>])=(?!=)", t):
        return "saisissez seulement l'expression, sans signe « = »."
    if t.count("(") != t.count(")") or t.count("[") != t.count("]"):
        return "les parenthèses ou les crochets ne sont pas équilibrés."
    if re.search(r"\d[A-Za-z_(]|\)\s*[(A-Za-z_\d]|[A-Za-z_]\w*\s+[A-Za-z_(]", t):
        return "chaque multiplication s'écrit avec * (par exemple 2*x ou (a + b)*c)."
    if isinstance(exc, NameError):
        nom = re.search(r"'(\w+)'", str(exc))
        return f"le nom « {nom.group(1)} » n'est pas connu ici." if nom else "un nom utilisé n'est pas connu ici."
    return "la syntaxe n'est pas valide (vérifiez les opérateurs : +, -, *, /, ** pour les puissances)."


class VerificationResult:
    """Résultat d'une vérification du tuteur (attributs en français et en anglais)."""

    __slots__ = ("valid", "diagnostic", "simplicity_note")

    def __init__(
        self,
        valid: bool | None = None,
        diagnostic: str = "",
        simplicity_note: str | None = None,
        *,
        valide: bool | None = None,
        note_simplicite: str | None = None,
    ) -> None:
        v = valid if valid is not None else bool(valide)
        note = simplicity_note if simplicity_note is not None else note_simplicite
        object.__setattr__(self, "valid", bool(v))
        object.__setattr__(self, "diagnostic", str(diagnostic))
        object.__setattr__(self, "simplicity_note", note)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("VerificationResult est immuable.")

    @property
    def valide(self) -> bool:
        return self.valid

    @property
    def note_simplicite(self) -> str | None:
        return self.simplicity_note

    def __bool__(self) -> bool:
        return self.valid

    def __str__(self) -> str:
        return self.diagnostic

    def __repr__(self) -> str:
        return self.diagnostic

    def _repr_markdown_(self) -> str:
        if self.valid:
            box = (
                f"<div style='padding: 12px 16px; border-left: 4px solid #16a34a; "
                f"background-color: #f0fdf4; border-radius: 4px; color: #166534; margin: 12px 0;'>\n"
                f"<strong style='font-size: 1.05em;'>✓ Réponse validée</strong>\n\n"
                f"{self.diagnostic}\n"
                f"</div>"
            )
            if self.simplicity_note:
                box += f"\n\n> *Note de simplicité* : {self.simplicity_note}"
            return box
        else:
            return (
                f"<div style='padding: 12px 16px; border-left: 4px solid #dc2626; "
                f"background-color: #fef2f2; border-radius: 4px; color: #991b1b; margin: 12px 0;'>\n"
                f"<strong style='font-size: 1.05em;'>✗ Diagnostic d'erreur</strong>\n\n"
                f"{self.diagnostic}\n"
                f"</div>"
            )


def _format_linear_comb(coeffs: Sequence[sp.Expr], var_name: str) -> str:
    """Écrit lisiblement la combinaison linéaire somme_j coeffs[j]·var_{j+1}."""
    pos_unit_terms: list[str] = []
    neg_frac_groups: dict[sp.Expr, list[str]] = {}
    other_terms: list[tuple[sp.Expr, str]] = []

    for j, c in enumerate(coeffs, start=1):
        v_j = f"{var_name}_{j}"
        if oracle.decide(c).verdict == Verdict.ZERO:
            continue
        if c == 1:
            pos_unit_terms.append(v_j)
        elif c.is_Rational and c < 0 and c.p == -1 and c.q > 1:
            denom = sp.Integer(c.q)
            neg_frac_groups.setdefault(denom, []).append(v_j)
        else:
            other_terms.append((c, v_j))

    if pos_unit_terms and len(neg_frac_groups) == 1 and not other_terms:
        denom, group_vars = next(iter(neg_frac_groups.items()))
        pos_str = " + ".join(pos_unit_terms)
        if len(group_vars) > 1:
            grp_str = " + ".join(group_vars)
            return f"{pos_str} - ({grp_str})/{denom}"
        return f"{pos_str} - {group_vars[0]}/{denom}"

    parts: list[str] = []
    for j, c in enumerate(coeffs, start=1):
        if oracle.decide(c).verdict == Verdict.ZERO:
            continue
        v_j = f"{var_name}_{j}"
        if not parts:
            if c == 1:
                parts.append(v_j)
            elif c == -1:
                parts.append(f"-{v_j}")
            else:
                parts.append(f"({c})·{v_j}" if not c.is_Integer else f"{c}·{v_j}")
        else:
            if c > 0:
                parts.append(f"+ {v_j}" if c == 1 else f"+ {c}·{v_j}")
            else:
                abs_c = -c
                parts.append(f"- {v_j}" if abs_c == 1 else f"- {abs_c}·{v_j}")
    return " ".join(parts) if parts else "0"


class _IndicesDepuisUn:
    """Vecteur de symboles indexé à partir de 1 dans les expressions des fiches (``p[1]``)."""

    def __init__(self, syms: Sequence[sp.Symbol]) -> None:
        self.syms = syms

    def __getitem__(self, idx: Any) -> sp.Symbol:
        return self.syms[int(idx) - 1]


def _parse_indexed_expr(
    expr_str: str,
    var_name: str,
    n: int,
    extra_locals: Mapping[str, Any] | None = None,
) -> tuple[sp.Expr, list[sp.Symbol]]:
    """Lit une expression indexée à partir de 1, comme 'p[4] - (p[1]+p[2]+p[3])/3', en expression SymPy."""
    vec_syms = [sp.Symbol(f"{var_name}_{k}", real=True) for k in range(1, n + 1)]
    local_env: dict[str, Any] = {
        f"{var_name}_{k}": vec_syms[k - 1] for k in range(1, n + 1)
    }
    if extra_locals:
        local_env.update(extra_locals)
    local_env[var_name] = _IndicesDepuisUn(vec_syms)
    parsed = expression(expr_str, local_env)
    return sp.expand(parsed), vec_syms


def _eval_data_expr(expr_str: str, raw_data: Mapping[str, Any]) -> Any:
    env: dict[str, Any] = dict(raw_data)
    env.update(
        {
            "Vector": Vector,
            "Matrix": Matrix,
            "sqrt": sp.sqrt,
            "Rational": sp.Rational,
            "GramSchmidt": GramSchmidt,
            "GaussJordan": GaussJordan,
            "QR": QR,
            "LeastSquares": LeastSquares,
            "BackSubstitution": BackSubstitution,
            "ForwardSubstitution": ForwardSubstitution,
        }
    )
    with suspend_tracing():
        return evaluer(expr_str, env)


def sans_seance(fonction: Any) -> Any:
    """Adapte un vérificateur ``f(réponse, spécification, données)`` à la signature du registre."""
    return lambda _session, response, spec, raw_data: fonction(response, spec, raw_data)
