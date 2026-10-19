"""Persistent and atomic JSON activity journal for the VMLS Tutor (§7.3 Principle 8, §7.9, v4 Phase 0)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Mapping

from linalg_pedagopy.config import config


class ExerciseJournal:
    """Activity journal for an exercise session with automatic disk reload and atomic writes (§7.9)."""

    def __init__(
        self,
        exercise_id: str,
        path: Path | None = None,
        *,
        persist: bool = True,
    ) -> None:
        self.exercise_id = exercise_id
        self._explicit_path = path
        self._persist_enabled = persist
        self.started_at = time.time()
        self._prior_elapsed_seconds: float = 0.0
        self.attempts: int = 0
        self.hints_unlocked: list[int] = []
        self.twin_opened: bool = False
        self.predictions: list[dict[str, Any]] = []
        self.lab_tests: int = 0
        self.solved: bool = False
        self.diagnostics: list[str] = []

        if self._persist_enabled:
            self._load_existing()

    @property
    def path(self) -> Path:
        return self._explicit_path if self._explicit_path is not None else config.journal_path

    @property
    def elapsed_seconds(self) -> float:
        return round(self._prior_elapsed_seconds + (time.time() - self.started_at), 2)

    def _load_existing(self) -> None:
        target = self.path
        try:
            if not target.exists():
                return
            raw = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return
            ex_map = raw.get("exercises")
            if not isinstance(ex_map, dict):
                return
            entry = ex_map.get(self.exercise_id)
            if not isinstance(entry, dict):
                return
            self.attempts = max(0, int(entry.get("attempts", 0)))
            self.solved = bool(entry.get("solved", False))
            self.hints_unlocked = [
                int(x) for x in entry.get("hints_unlocked", []) if isinstance(x, (int, str))
            ]
            self.twin_opened = bool(entry.get("twin_opened", False))
            preds = entry.get("predictions", [])
            if isinstance(preds, list):
                self.predictions = [dict(p) for p in preds if isinstance(p, Mapping)]
            self.lab_tests = max(0, int(entry.get("lab_tests", 0)))
            self._prior_elapsed_seconds = max(0.0, float(entry.get("elapsed_seconds", 0.0)))
            last_diag = entry.get("last_diagnostic", "")
            if last_diag:
                self.diagnostics = [str(last_diag)]
        except Exception:
            pass

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
        if not self._persist_enabled:
            return
        target = self.path
        try:
            if target.exists():
                try:
                    raw = json.loads(target.read_text(encoding="utf-8"))
                    data = raw if isinstance(raw, dict) else {"exercises": {}}
                except Exception:
                    data = {"exercises": {}}
            else:
                data = {"exercises": {}}
            if "exercises" not in data or not isinstance(data["exercises"], dict):
                data["exercises"] = {}
            data["exercises"][self.exercise_id] = self.to_dict()
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(data, ensure_ascii=False, indent=2)
            tmp_path = target.with_name(f"{target.name}.{os.getpid()}.tmp")
            try:
                tmp_path.write_text(payload, encoding="utf-8")
                tmp_path.replace(target)
            except Exception:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                target.write_text(payload, encoding="utf-8")
        except Exception:
            # In read-only environments, keep journal in memory without crashing the session
            pass

    def format_summary(self) -> str:
        """Produces a readable summary of the session (without automatic grading, §7.3 Principle 8)."""
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

    format_bilan = format_summary
