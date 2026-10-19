"""Journal local JSON de progression pour l'étudiant et l'enseignant (§7.3 Principe 8, §7.9)."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Mapping

from linalg_pedagopy.config import config


class ExerciseJournal:
    """Journal d'activité d'une séance sur un exercice donné (§7.9)."""

    def __init__(self, exercise_id: str, path: Path | None = None) -> None:
        self.exercise_id = exercise_id
        self._explicit_path = path
        self.started_at = time.time()
        self.attempts: int = 0
        self.hints_unlocked: list[int] = []
        self.twin_opened: bool = False
        self.predictions: list[dict[str, Any]] = []
        self.lab_tests: int = 0
        self.solved: bool = False
        self.diagnostics: list[str] = []

    @property
    def path(self) -> Path:
        return self._explicit_path if self._explicit_path is not None else config.journal_path

    @property
    def elapsed_seconds(self) -> float:
        return round(time.time() - self.started_at, 2)

    def record_attempt(self, *, correct: bool, diagnostic: str) -> None:
        self.attempts += 1
        if correct:
            self.solved = True
        self.diagnostics.append(diagnostic)
        self._persist()

    def record_hint(self, level: int) -> None:
        if level not in self.hints_unlocked:
            self.hints_unlocked.append(level)
        if level == 4:
            self.twin_opened = True
        self._persist()

    def record_twin(self) -> None:
        self.twin_opened = True
        if 4 not in self.hints_unlocked:
            self.hints_unlocked.append(4)
        self._persist()

    def record_prediction(self, prediction: Mapping[str, Any]) -> None:
        self.predictions.append(dict(prediction))
        self._persist()

    def record_lab_test(self) -> None:
        self.lab_tests += 1
        self._persist()

    def to_dict(self) -> dict[str, Any]:
        return {
            "exercise_id": self.exercise_id,
            "attempts": self.attempts,
            "solved": self.solved,
            "hints_unlocked": list(self.hints_unlocked),
            "twin_opened": self.twin_opened,
            "predictions": list(self.predictions),
            "lab_tests": self.lab_tests,
            "elapsed_seconds": self.elapsed_seconds,
            "last_diagnostic": self.diagnostics[-1] if self.diagnostics else "",
        }

    def _persist(self) -> None:
        target = self.path
        try:
            if target.exists():
                raw = json.loads(target.read_text(encoding="utf-8"))
                data = raw if isinstance(raw, dict) else {"exercises": {}}
            else:
                data = {"exercises": {}}
            if "exercises" not in data or not isinstance(data["exercises"], dict):
                data["exercises"] = {}
            data["exercises"][self.exercise_id] = self.to_dict()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # En environnement en lecture seule, le journal reste en mémoire sans interrompre la séance
            pass

    def format_bilan(self) -> str:
        """Produit une synthèse lisible de la séance (sans notation automatique, §7.3 Principe 8)."""
        statut = "Validé" if self.solved else "En cours"
        indices_str = (
            ", ".join(str(lvl) for lvl in self.hints_unlocked)
            if self.hints_unlocked
            else "aucun"
        )
        jumeau_str = "oui" if self.twin_opened else "non"
        lines = [
            f"=== Bilan de l'exercice {self.exercise_id} ===",
            f"- Statut               : {statut}",
            f"- Tentatives soumises  : {self.attempts}",
            f"- Indices consultés    : {indices_str}",
            f"- Exercice jumeau lu   : {jumeau_str}",
            f"- Essais au labo       : {self.lab_tests}",
            f"- Temps passé          : {self.elapsed_seconds:.1f} s",
        ]
        if self.predictions:
            lines.append(f"- Prédiction initiale  : {self.predictions[-1]}")
        return "\n".join(lines)
