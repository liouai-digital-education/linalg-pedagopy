"""Modes d'usage interactifs : lecture, prédire/révéler, complétion et autonome (§5.6.2, §5.6.3)."""

from __future__ import annotations

from typing import Any, Literal

from linalg_pedagopy.algorithms.base import Procedure, register_interactive_session_hook
from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy.exercises.checkers import OperationFeedback, check_row_operation
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.render.text import translate
from linalg_pedagopy.trace.step import Step, StepKind
from linalg_pedagopy.trace.tracer import suspend_tracing

InteractiveMode = Literal["read", "predict_reveal", "completion", "autonomous"]


class InteractiveSession:
    """Session interactive sur une procédure algorithmique (§5.6.2, §5.6.3)."""

    def __init__(
        self,
        procedure: Procedure[Any],
        *,
        mode: InteractiveMode = "autonomous",
        mask_ratio: float = 0.5,
    ) -> None:
        if mode not in ("read", "predict_reveal", "completion", "autonomous"):
            raise ValueError(f"Mode interactif inconnu : {mode!r}")
        self.procedure = procedure
        self.mode: InteractiveMode = mode
        self.mask_ratio = mask_ratio
        self.history: list[tuple[str, OperationFeedback]] = []
        self.predictions: list[str] = []
        self._reveal_index: int = 0

        if isinstance(procedure, GaussJordan):
            self.num_lhs_cols = procedure.A.cols
            self.current_matrix = (
                procedure.A.augment(procedure.b)
                if procedure.b is not None
                else procedure.A
            )
            with suspend_tracing():
                self._target_result = procedure.run()
        else:
            self.num_lhs_cols = 0
            self.current_matrix = Matrix([])
            with suspend_tracing():
                self._target_result = procedure.run()

        self._flat_steps: list[Step] = []
        if hasattr(self._target_result, "trace") and isinstance(
            self._target_result.trace, Step
        ):
            self._collect_atomic_steps(self._target_result.trace)

    def _collect_atomic_steps(self, node: Step) -> None:
        if node.kind in (
            StepKind.ROW_SWAP,
            StepKind.ROW_SCALE,
            StepKind.ROW_ADD,
            StepKind.PROJECTION,
            StepKind.NORMALIZE,
            StepKind.BACK_SUBSTITUTION,
        ):
            self._flat_steps.append(node)
        for child in node.children:
            self._collect_atomic_steps(child)

    def propose(self, operation: str, *, only_lhs: bool = False) -> OperationFeedback:
        """Valide et applique une opération proposée par l'élève (§5.6.3)."""
        if not isinstance(self.procedure, GaussJordan):
            raise TypeError("propose() d'opérations de lignes est dédié à GaussJordan.")
        feedback = check_row_operation(
            self.current_matrix,
            operation,
            num_lhs_cols=self.num_lhs_cols,
            only_lhs=only_lhs,
        )
        self.history.append((operation, feedback))
        if feedback.is_valid and feedback.new_matrix is not None:
            self.current_matrix = feedback.new_matrix
        return feedback

    def hint(self) -> str:
        """Suggère la prochaine opération élémentaire utile sans l'effectuer (§5.6.3)."""
        if not isinstance(self.procedure, GaussJordan):
            if self._reveal_index < len(self._flat_steps):
                st = self._flat_steps[self._reveal_index]
                return translate(st.message_key, st.params)
            return "Calcul terminé."

        m = self.current_matrix.rows
        n = self.num_lhs_cols
        pivot_row = 0

        for col in range(n):
            if pivot_row >= m:
                break
            # Chercher un pivot non nul dans la colonne `col` à partir de `pivot_row`
            nz_rows = [
                r
                for r in range(pivot_row, m)
                if oracle.decide(self.current_matrix[r, col]).verdict == Verdict.NONZERO
            ]
            if not nz_rows:
                continue

            if pivot_row not in nz_rows:
                target_r = nz_rows[0]
                return (
                    f"Suggestion : amenez un pivot non nul en ({pivot_row + 1},{col + 1}) "
                    f"en échangeant L{pivot_row + 1} et L{target_r + 1}."
                )

            piv_val = self.current_matrix[pivot_row, col]
            # Vérifier s'il y a des coefficients sous ou au-dessus du pivot à annuler
            for r in range(m):
                if r != pivot_row:
                    val = self.current_matrix[r, col]
                    if oracle.decide(val).verdict == Verdict.NONZERO:
                        return (
                            f"Suggestion : annulez le coefficient ({r + 1},{col + 1}) = {val} "
                            f"à l'aide de la ligne pivot L{pivot_row + 1}."
                        )

            if oracle.decide(piv_val - 1).verdict != Verdict.ZERO:
                return (
                    f"Suggestion : normalisez le pivot ({pivot_row + 1},{col + 1}) = {piv_val} "
                    f"de la ligne L{pivot_row + 1} à 1."
                )

            pivot_row += 1

        return "La matrice est déjà sous forme échelonnée réduite !"

    def is_complete(self) -> bool:
        """Indique si la forme échelonnée réduite cible est atteinte."""
        if hasattr(self._target_result, "augmented_rref"):
            return bool(self.current_matrix == self._target_result.augmented_rref)
        return self._reveal_index >= len(self._flat_steps)

    def predict(self, prediction: str) -> str:
        """Enregistre la prédiction de l'élève avant de révéler l'étape suivante (mode predict_reveal)."""
        self.predictions.append(prediction)
        return "Prédiction enregistrée. Vous pouvez maintenant appeler reveal() pour afficher l'étape."

    def reveal(self) -> str:
        """Révèle la prochaine étape dans le mode 'predict_reveal' (§5.6.2)."""
        if self.mode == "predict_reveal" and len(self.predictions) <= self._reveal_index:
            return "Veuillez d'abord enregistrer votre prédiction avec predict(...) avant de révéler l'étape."
        if self._reveal_index >= len(self._flat_steps):
            return "Toutes les étapes ont été révélées."
        step = self._flat_steps[self._reveal_index]
        self._reveal_index += 1
        return translate(step.message_key, step.params)

    def completion_view(self) -> list[dict[str, Any]]:
        """Produit une liste d'étapes dont une proportion mask_ratio est masquée (mode completion, §5.6.2)."""
        total = len(self._flat_steps)
        if total == 0:
            return []
        num_masked = max(1, int(round(total * self.mask_ratio)))
        masked_indices = set(range(total - num_masked, total))
        out: list[dict[str, Any]] = []
        for idx, st in enumerate(self._flat_steps):
            is_masked = idx in masked_indices
            out.append(
                {
                    "step_number": idx + 1,
                    "masked": is_masked,
                    "description": "??? (étape à compléter)"
                    if is_masked
                    else translate(st.message_key, st.params),
                }
            )
        return out


register_interactive_session_hook(InteractiveSession)
