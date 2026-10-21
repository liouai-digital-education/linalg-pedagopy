"""Échelle d'indices à 4 paliers et politique de déblocage du tuteur."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

from linalg_pedagopy.config import config
from linalg_pedagopy.exercises.generators import TwinExercise, generators, generateurs
from linalg_pedagopy.tutor.evaluation_sure import evaluer

LEVEL_TITLES: dict[int, str] = {
    1: "Niveau 1 — Orientation",
    2: "Niveau 2 — Outil",
    3: "Niveau 3 — Démarrage",
    4: "Niveau 4 — Exercice jumeau résolu",
}


def evaluate_twin_spec(twin_spec: str | None) -> TwinExercise | str:
    """Evaluates the twin exercise generator expression from a YAML sheet."""
    if not twin_spec:
        return generators.vector_statistics()
    spec = twin_spec.strip()
    if spec.startswith(("generateurs.", "generators.")):
        try:
            res = evaluer(spec, {"generateurs": generateurs, "generators": generators})
            if isinstance(res, TwinExercise):
                return res
            return str(res)
        except Exception as exc:
            return f"Erreur dans l'exercice jumeau : {spec} ({exc})"
    return spec


@dataclass
class HintLadder:
    """Manager for the 4-level hint ladder of an exercise."""

    hints: tuple[str, ...]
    twin_spec: str | None = None
    on_unlock: Callable[[int], None] | None = None
    initial_unlocked_level: int = 0

    def __post_init__(self) -> None:
        self.unlocked_level: int = max(0, int(self.initial_unlocked_level))
        self._last_unlock_time: float = 0.0
        self._attempts_at_last_unlock: int = 0

    @property
    def jumeau_spec(self) -> str | None:
        return self.twin_spec

    def request_hint(
        self,
        *,
        level: int | None = None,
        current_attempts: int = 0,
    ) -> str:
        """Unlocks and returns the next hint level (or requested level <= unlocked + 1)."""
        target = (self.unlocked_level + 1) if level is None else level
        if target < 1:
            target = 1
        if target > 4:
            return (
                "Il n'existe pas de palier 5 « solution » en mode étudiant. "
                "Appuyez-vous sur l'exercice jumeau résolu au niveau 4 pour transposer la méthode !"
            )

        if target > self.unlocked_level + 1:
            target = self.unlocked_level + 1

        if target > self.unlocked_level:
            min_att = config.hint_min_attempts
            min_delay = config.hint_min_delay_seconds

            if self.unlocked_level > 0 and min_att > 0:
                delta_att = current_attempts - self._attempts_at_last_unlock
                if delta_att < min_att:
                    rem_att = min_att - delta_att
                    return (
                        f"Déblocage différé : effectuez au moins {rem_att} tentative(s) "
                        f"avec ex.verify(...) / ex.verifier(...) avant de débloquer le niveau {target}."
                    )

            if self.unlocked_level > 0 and min_delay > 0:
                elapsed = time.time() - self._last_unlock_time
                if elapsed < min_delay:
                    rem_sec = int(round(min_delay - elapsed))
                    return (
                        f"Déblocage différé : veuillez patienter encore {rem_sec} s "
                        f"avant de débloquer le niveau {target}."
                    )

            self.unlocked_level = target
            self._last_unlock_time = time.time()
            self._attempts_at_last_unlock = current_attempts
            if self.on_unlock is not None:
                self.on_unlock(target)

        return self.format_level(target)

    def format_level(self, level: int) -> str:
        """Formats the content of a hint level (1 to 4)."""
        title = LEVEL_TITLES.get(level, f"Niveau {level}")
        if 1 <= level <= 3:
            idx = level - 1
            body = (
                self.hints[idx]
                if idx < len(self.hints)
                else "Relisez les définitions des notions indiquées dans l'énoncé."
            )
            return f"**[{title}]**\n\n{body}"

        twin = evaluate_twin_spec(self.twin_spec)
        if isinstance(twin, TwinExercise):
            extra = f"\n\n{self.hints[3]}" if len(self.hints) >= 4 else ""
            twin_md = twin._repr_markdown_() if hasattr(twin, "_repr_markdown_") else twin.format_text()
            return f"**[{title}]**\n\n{twin_md}{extra}"
        return f"**[{title}]**\n\n{twin}"
