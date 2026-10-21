"""Counterexample laboratory for true/false exercises."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from weakref import WeakKeyDictionary

import sympy as sp

from linalg_pedagopy.core.exceptions import PedagopyError
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tutor.evaluation_sure import evaluer

_LAB_VAULT: WeakKeyDictionary[Any, dict[str, Any]] = WeakKeyDictionary()


def _eval_math_predicate(expr_str: str, env: Mapping[str, Any]) -> bool:
    """Evaluates a mathematical predicate (==, <=, >=, <, >) on Vector/Matrix in exact arithmetic."""
    local_env: dict[str, Any] = dict(env)
    local_env.update(
        {
            "norm": lambda v: v.norm(),
            "rms": lambda v: v.rms(),
            "avg": lambda v: v.avg(),
            "std": lambda v: v.std(),
            "demean": lambda v: v.demean(),
            "dot": lambda u, v: u.dot(v),
            "dist": lambda u, v: u.distance(v),
            "sqrt": sp.sqrt,
            "abs": abs,
            "Vector": Vector,
            "Matrix": Matrix,
        }
    )

    with suspend_tracing():
        if "<=" in expr_str:
            lhs_s, rhs_s = expr_str.split("<=", 1)
            lhs = evaluer(lhs_s, local_env)
            rhs = evaluer(rhs_s, local_env)
            diff = sp.simplify(rhs - lhs)
            if oracle.decide(diff).verdict == Verdict.ZERO:
                return True
            return bool(diff.evalf(30) >= -sp.Float("1e-25", 30))

        if ">=" in expr_str:
            lhs_s, rhs_s = expr_str.split(">=", 1)
            lhs = evaluer(lhs_s, local_env)
            rhs = evaluer(rhs_s, local_env)
            diff = sp.simplify(lhs - rhs)
            if oracle.decide(diff).verdict == Verdict.ZERO:
                return True
            return bool(diff.evalf(30) >= -sp.Float("1e-25", 30))

        if "==" in expr_str:
            lhs_s, rhs_s = expr_str.split("==", 1)
            lhs = evaluer(lhs_s, local_env)
            rhs = evaluer(rhs_s, local_env)
            if isinstance(lhs, (Vector, Matrix)) and isinstance(rhs, (Vector, Matrix)):
                return bool(lhs == rhs)
            if isinstance(lhs, Vector) and rhs == 0:
                return bool(lhs.is_zero() is True)
            return oracle.decide(sp.simplify(lhs - rhs)).verdict == Verdict.ZERO

        if "!=" in expr_str:
            lhs_s, rhs_s = expr_str.split("!=", 1)
            return not _eval_math_predicate(f"{lhs_s} == {rhs_s}", env)

        val = evaluer(expr_str, local_env)
        return bool(val)


def _structured_vector_candidates() -> list[dict[str, Vector]]:
    """Structured families of vectors in R^2 and R^3 (zero, canonical, collinear, orthogonal)."""
    e1 = Vector([1, 0, 0])
    e2 = Vector([0, 1, 0])
    e3 = Vector([0, 0, 1])
    v110 = Vector([1, 1, 0])
    v1m10 = Vector([1, -1, 0])
    v210 = Vector([2, -1, 0])
    z3 = Vector([0, 0, 0])
    return [
        {"a": e1, "b": v110, "c": e3},
        {"a": e1, "b": e1, "c": e2},
        {"a": e1, "b": -e1, "c": e2},
        {"a": v110, "b": v1m10, "c": e3},
        {"a": v210, "b": e2, "c": e3},
        {"a": e1, "b": e2, "c": e3},
        {"a": z3, "b": e1, "c": e2},
    ]


@dataclass(frozen=True)
class LabReport:
    """Result of an instance test in the counterexample laboratory."""

    hypotheses_satisfied: bool
    results_by_part: Mapping[str, bool]
    found_counterexample: bool
    message: str

    def __str__(self) -> str:
        return self.message


class CounterexampleLab:
    """Exploration and counterexample testing laboratory."""

    __slots__ = ("__weakref__",)

    def __init__(
        self,
        verification_spec: Mapping[str, Any],
        predictions: Mapping[str, str],
        *,
        on_test: Callable[[], None] | None = None,
    ) -> None:
        if not predictions:
            raise PedagopyError(
                "Engagez-vous avant d'explorer : enregistrez d'abord "
                "votre prédiction avec ex.predict(...) / ex.predire(...), puis ouvrez le laboratoire."
            )
        _LAB_VAULT[self] = {
            "spec": dict(verification_spec),
            "predictions": dict(predictions),
            "on_test": on_test,
        }

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("CounterexampleLab est immuable.")

    @property
    def predictions(self) -> dict[str, str]:
        return dict(_LAB_VAULT[self]["predictions"])

    def _has_internal_counterexample(self, pred_expr: str, hypotheses: list[str]) -> bool:
        """Internal search on structured families without ever disclosing the counterexample."""
        for cand in _structured_vector_candidates():
            try:
                if all(_eval_math_predicate(h, cand) for h in hypotheses):
                    if not _eval_math_predicate(pred_expr, cand):
                        return True
            except Exception:
                continue
        return False

    def test(self, **instances: Any) -> LabReport:
        """Tests a student-provided instance against the exercise hypotheses and claims."""
        st = _LAB_VAULT[self]
        on_test = st["on_test"]
        if on_test is not None:
            on_test()

        spec = st["spec"]
        predictions = st["predictions"]

        env: dict[str, Any] = {}
        for k, v in instances.items():
            if isinstance(v, (Vector, Matrix)):
                env[k] = v
            elif isinstance(v, list) and v and isinstance(v[0], list):
                env[k] = Matrix(v)
            elif isinstance(v, (list, tuple)):
                env[k] = Vector(v)
            else:
                env[k] = v

        hypotheses: list[str] = list(spec.get("hypotheses", []))
        hyp_text: str = spec.get("hypotheses_texte", "")

        for hyp in hypotheses:
            if not _eval_math_predicate(hyp, env):
                msg = (
                    f"Hypothèses non satisfaites sur votre instance (condition requise : {hyp_text or hyp}). "
                    "Modifiez vos vecteurs pour respecter les hypothèses de l'énoncé."
                )
                return LabReport(
                    hypotheses_satisfied=False,
                    results_by_part={},
                    found_counterexample=False,
                    message=msg,
                )

        lines: list[str] = []
        if hypotheses:
            desc = hyp_text if hyp_text else " et ".join(hypotheses)
            lines.append(f"Hypothèses vérifiées : {desc}.")

        affirmations: dict[str, str] = {}
        if "affirmations" in spec and isinstance(spec["affirmations"], Mapping):
            affirmations = {str(k): str(v) for k, v in spec["affirmations"].items()}
        elif "enonce" in spec:
            affirmations = {"enonce": str(spec["enonce"])}

        results: dict[str, bool] = {}
        true_parts: list[str] = []
        found_ce = False

        for part_key, expr_str in affirmations.items():
            is_true = _eval_math_predicate(expr_str, env)
            results[part_key] = is_true
            if part_key == "enonce":
                if not is_true:
                    found_ce = True
                    lines.append("L'énoncé est faux sur votre instance : c'est un contre-exemple valide.")
                else:
                    lines.append(
                        "L'énoncé est vrai sur votre instance. "
                        "Des essais ne suffisent pas à prouver qu'un énoncé est toujours vrai : rédigez une justification."
                    )
                    pred_val = str(next(iter(predictions.values()), "")).lower()
                    if ("vrai" in pred_val or "true" in pred_val) and self._has_internal_counterexample(
                        expr_str, hypotheses
                    ):
                        lines.append(
                            "Indice du laboratoire : vous avez prédit « vrai », mais il existe des contre-exemples !"
                        )
            else:
                if not is_true:
                    found_ce = True
                    lines.append(f"({part_key}) est faux sur votre instance : c'est un contre-exemple valide.")
                else:
                    true_parts.append(part_key)
                    lines.append(f"({part_key}) est vrai sur votre instance.")
                    pred_val = str(predictions.get(part_key, "")).lower()
                    if ("vrai" in pred_val or "true" in pred_val) and self._has_internal_counterexample(
                        expr_str, hypotheses
                    ):
                        lines.append(
                            f"Attention pour ({part_key}) : vous avez prédit « toujours vrai », "
                            "mais le laboratoire a détecté qu'il existe au moins un contre-exemple."
                        )

        if true_parts:
            parts_fmt = ", ".join(f"({p})" for p in true_parts)
            lines.append(f"Pour {parts_fmt}, des essais ne suffisent pas : rédigez une justification.")

        return LabReport(
            hypotheses_satisfied=True,
            results_by_part=results,
            found_counterexample=found_ce,
            message="\n".join(lines),
        )

    tester = test
