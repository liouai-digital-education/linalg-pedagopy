"""Échelle d'indices gradués sur 4 niveaux et politique de déblocage (§7.5)."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable, Sequence

from linalg_pedagopy.config import config
from linalg_pedagopy.exercises.generators import TwinExercise, generateurs

LEVEL_TITLES: dict[int, str] = {
    1: "Niveau 1 — Orientation",
    2: "Niveau 2 — Outil",
    3: "Niveau 3 — Démarrage",
    4: "Niveau 4 — Exercice jumeau résolu",
}


def evaluate_twin_spec(jumeau_spec: str | None) -> TwinExercise | str:
    """Évalue l'expression de générateur jumeau d'une fiche YAML (ex: 'generateurs.moyenne_glissante(fenetre=2, n=5)')."""
    if not jumeau_spec:
        return generateurs.statistiques_vecteur()
    spec = jumeau_spec.strip()
    if spec.startswith("generateurs."):
        try:
            res = eval(spec, {"__builtins__": {}}, {"generateurs": generateurs})  # noqa: S307
            if isinstance(res, TwinExercise):
                return res
            return str(res)
        except Exception as exc:
            return f"Exercice jumeau : {spec} ({exc})"
    return spec


@dataclass
class HintLadder:
    """Gestionnaire de l'échelle d'indices à 4 niveaux d'un exercice (§7.5)."""

    hints: tuple[str, ...]
    jumeau_spec: str | None = None
    on_unlock: Callable[[int], None] | None = None

    def __post_init__(self) -> None:
        self.unlocked_level: int = 0
        self._last_unlock_time: float = 0.0
        self._attempts_at_last_unlock: int = 0

    def request_hint(
        self,
        *,
        level: int | None = None,
        current_attempts: int = 0,
    ) -> str:
        """Débloque et renvoie l'indice du niveau suivant (ou du niveau demandé <= débloqué + 1)."""
        target = (self.unlocked_level + 1) if level is None else level
        if target < 1:
            target = 1
        if target > 4:
            return (
                "Il n'existe pas de niveau 5 (« solution ») en mode étudiant (§7.5). "
                "Appuyez-vous sur l'exercice jumeau résolu au niveau 4 pour transposer la méthode !"
            )

        # Si l'étudiant demande un niveau supérieur à unlocked_level + 1, on débloque séquentiellement
        if target > self.unlocked_level + 1:
            target = self.unlocked_level + 1

        if target > self.unlocked_level:
            # Contrôle de la politique de déblocage (tentatives et délai configurés par l'enseignant)
            min_att = config.hint_min_attempts
            min_delay = config.hint_min_delay_seconds

            if self.unlocked_level > 0 and min_att > 0:
                delta_att = current_attempts - self._attempts_at_last_unlock
                if delta_att < min_att:
                    rem_att = min_att - delta_att
                    return (
                        f"Déblocage différé : effectuez au moins {rem_att} tentative(s) "
                        f"avec ex.verifier(...) avant de débloquer le niveau {target}."
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
        """Formate le contenu d'un niveau d'indice (1 à 4)."""
        title = LEVEL_TITLES.get(level, f"Niveau {level}")
        if 1 <= level <= 3:
            idx = level - 1
            body = (
                self.hints[idx]
                if idx < len(self.hints)
                else "Relisez les définitions du chapitre correspondant dans VMLS."
            )
            return f"[{title}]\n{body}"

        # Niveau 4 : Exercice jumeau résolu (ou 4e indice si explicite)
        twin = evaluate_twin_spec(self.jumeau_spec)
        if isinstance(twin, TwinExercise):
            extra = f"\n{self.hints[3]}" if len(self.hints) >= 4 else ""
            return f"[{title}]\n{twin.format_text()}{extra}"
        return f"[{title}]\n{twin}"
