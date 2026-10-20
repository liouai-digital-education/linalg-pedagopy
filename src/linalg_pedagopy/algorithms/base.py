"""Classes de base Procedure, Result et SolutionSet pour les algorithmes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Mapping, TypeVar

import sympy as sp

from linalg_pedagopy.core.cases import CaseSplit
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.step import Step, StepKind
from linalg_pedagopy.trace.tracer import current_tracer, record, tracing

R = TypeVar("R")

_explain_step_hook: Callable[[Any, int, str], Any] | None = None
_interactive_session_hook: Callable[..., Any] | None = None


def register_explain_step_hook(hook: Callable[[Any, int, str], Any]) -> None:
    """Enregistre la fabrique d'Explanation pour Result.explain() et Result.verify()."""
    global _explain_step_hook
    _explain_step_hook = hook


def register_interactive_session_hook(hook: Callable[..., Any]) -> None:
    """Enregistre la fabrique de session interactive pour Procedure.interactive()."""
    global _interactive_session_hook
    _interactive_session_hook = hook


def make_explanation(tree: Any, level: int = 1, fmt: str = "auto") -> Any:
    """Fabrique une Explanation à partir d'une trace (ou d'un résultat, pour le niveau 0)."""
    if _explain_step_hook is None:
        raise RuntimeError("Le module render n'est pas initialisé.")
    return _explain_step_hook(tree, level, fmt)


@dataclass(frozen=True)
class Result:
    """Classe de base immuable pour les résultats typés des algorithmes."""

    trace: Step = field(
        default_factory=lambda: Step(StepKind.SECTION, 0, "trace.root"),
        repr=False,
        compare=False,
    )

    def explain(self, level: int | None = None, fmt: str = "auto") -> Any:
        """Renvoie un objet Explanation filtré au niveau de détail demandé (0 : résultat seul)."""
        from linalg_pedagopy.config import config

        lvl = level if level is not None else config.default_trace_level
        if lvl <= 0:
            return make_explanation(self, level=0, fmt=fmt)
        return make_explanation(self.trace, level=lvl, fmt=fmt)

    def verify(self) -> Any:
        """Exécute et trace les contrôles de validité a posteriori."""
        with tracing(level=2) as t:
            self._run_verification()
        return make_explanation(t.tree, level=2, fmt="auto")

    def _run_verification(self) -> None:
        record(StepKind.CHECK, "gj.verify", level=1)

    def _repr_markdown_(self) -> str:
        """Rendu Markdown avec formules LaTeX dans Jupyter."""
        from linalg_pedagopy.config import config

        lvl = max(config.default_trace_level, 2)
        return self.explain(level=lvl).to_markdown()

    def _repr_latex_(self) -> str:
        """Rendu LaTeX dans Jupyter."""
        from linalg_pedagopy.config import config

        lvl = max(config.default_trace_level, 2)
        return self.explain(level=lvl).to_latex()


class Procedure(ABC, Generic[R]):
    """Classe de base abstraite des procédures algorithmiques."""

    def run(self) -> R | CaseSplit[R]:
        """Exécute la procédure et enregistre la trace complète."""
        outer = current_tracer()
        capture_level = max(outer.level, 3) if outer is not None else 3
        with tracing(level=capture_level) as local_tracer:
            res = self._execute()
        recorded_tree = local_tracer.tree

        # Si un traceur englobant était actif, y rejouer les enfants enregistrés
        if outer is not None:
            for child in recorded_tree.children:
                outer.record(
                    child.kind,
                    child.message_key,
                    level=child.level,
                    snapshot=child.snapshot,
                    highlight=child.highlight,
                    children=child.children,
                    **child.params,
                )

        if isinstance(res, Result):
            object.__setattr__(res, "trace", recorded_tree)
        return res

    @abstractmethod
    def _execute(self) -> R | CaseSplit[R]:
        """Implémentation interne de l'algorithme."""

    def interactive(self, mode: str = "autonomous") -> Any:
        """Ouvre une session interactive sur cette procédure."""
        if _interactive_session_hook is None:
            raise RuntimeError("Le module exercises.interactive n'est pas initialisé.")
        return _interactive_session_hook(self, mode=mode)


class SolutionSet:
    """Ensemble des solutions d'un système linéaire A x = b."""

    Unique: type[UniqueSolution]
    Affine: type[AffineSolution]
    Empty: type[EmptySolution]

    def subs(self, mapping: Mapping[Any, Any]) -> SolutionSet:
        return self


@dataclass(frozen=True)
class UniqueSolution(SolutionSet):
    """Solution unique x d'un système linéaire compatible de rang plein en colonnes."""

    x: Vector | Matrix

    @property
    def is_consistent(self) -> bool:
        return True

    @property
    def is_unique(self) -> bool:
        return True

    def subs(self, mapping: Mapping[Any, Any]) -> UniqueSolution:
        return UniqueSolution(x=self.x.subs(mapping))

    def __str__(self) -> str:
        return f"UniqueSolution(x={self.x})"

    def _repr_markdown_(self) -> str:
        tex = getattr(self.x, "_repr_latex_", lambda: f"${sp.latex(self.x)}$")().strip("$")
        return f"**Solution unique :**\n\n$${tex}$$"


@dataclass(frozen=True)
class AffineSolution(SolutionSet):
    """Ensemble affine de solutions x_0 + sum_k t_k v_k."""

    x0: Vector
    basis: tuple[Vector, ...]
    free_vars: tuple[int, ...] = ()

    @property
    def is_consistent(self) -> bool:
        return True

    @property
    def is_unique(self) -> bool:
        return False

    def at_params(self, *t_values: Any) -> Vector:
        """Évalue une solution particulière pour des valeurs données des variables libres."""
        if len(t_values) != len(self.basis):
            raise ValueError(
                f"Attendu {len(self.basis)} paramètre(s) libre(s), reçu {len(t_values)}."
            )
        if not self.basis:
            return self.x0
        return self.x0 + Vector.combination(self.basis, t_values)

    def subs(self, mapping: Mapping[Any, Any]) -> AffineSolution:
        return AffineSolution(
            x0=self.x0.subs(mapping),
            basis=tuple(v.subs(mapping) for v in self.basis),
            free_vars=self.free_vars,
        )

    def __str__(self) -> str:
        basis_str = " + ".join(
            f"t_{idx + 1}·{v}" for idx, v in enumerate(self.basis)
        )
        return f"{self.x0} + {basis_str}" if basis_str else str(self.x0)

    def _repr_markdown_(self) -> str:
        x0_tex = self.x0._repr_latex_().strip("$")
        basis_parts = [
            f"t_{idx + 1} {v._repr_latex_().strip('$')}"
            for idx, v in enumerate(self.basis)
        ]
        formula = f"{x0_tex} + " + " + ".join(basis_parts) if basis_parts else x0_tex
        k = len(self.basis)
        return f"**Ensemble affine de solutions ({k} variable(s) libre(s)) :**\n\n$$x = {formula}$$"


@dataclass(frozen=True)
class EmptySolution(SolutionSet):
    """Ensemble vide de solutions (système incompatible, ligne 0 ... 0 | c avec c != 0)."""

    row: int  # indice 0-based de la première ligne incompatible
    witness: sp.Expr  # valeur non nulle c dans le second membre
    inconsistent_rows: tuple[tuple[int, sp.Expr], ...] = ()

    @property
    def is_consistent(self) -> bool:
        return False

    @property
    def is_unique(self) -> bool:
        return False

    def subs(self, mapping: Mapping[Any, Any]) -> EmptySolution:
        sym_map = {
            (sp.Symbol(k, real=True) if isinstance(k, str) else k): v
            for k, v in mapping.items()
        }
        return EmptySolution(
            row=self.row,
            witness=sp.simplify(self.witness.xreplace(sym_map)),
            inconsistent_rows=tuple(
                (r, sp.simplify(w.xreplace(sym_map)))
                for r, w in self.inconsistent_rows
            ),
        )

    def __str__(self) -> str:
        return f"EmptySolution(ligne L{self.row + 1} : 0 = {self.witness})"

    def _repr_markdown_(self) -> str:
        wit_tex = sp.latex(self.witness)
        return (
            f"**Système incompatible :** ensemble vide $\\emptyset$.\n\n"
            f"- Ligne $L_{{{self.row + 1}}}$ : $0 = {wit_tex}$ (témoin : $0 = 1$)."
        )


SolutionSet.Unique = UniqueSolution
SolutionSet.Affine = AffineSolution
SolutionSet.Empty = EmptySolution
