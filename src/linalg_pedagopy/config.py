"""Configuration centralisée et contextuelle de linalg_pedagopy."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterator, Literal

FloatPolicy = Literal["rationalize", "reject", "keep"]
TutorMode = Literal["student", "teacher", "etudiant", "enseignant"]
FactorPolicy = Literal["rational", "real_radicals"]


@dataclass(frozen=True)
class ConfigState:
    """État immuable de la configuration du package."""

    float_policy: FloatPolicy = "rationalize"
    locale: str = "fr"
    default_trace_level: int = 1
    max_case_depth: int = 3
    max_cases: int = 8
    factor_policy: FactorPolicy = "real_radicals"
    max_generic_dim: int | None = 4
    tutor_mode: TutorMode = "student"
    hint_min_attempts: int = 0
    hint_min_delay_seconds: int = 0
    journal_path: Path = Path(".linalg_pedagopy_journal.json")


def _entier(nom: str, valeur: Any, minimum: int) -> None:
    if isinstance(valeur, bool) or not isinstance(valeur, int) or valeur < minimum:
        raise ValueError(f"{nom} invalide : {valeur!r} (entier ≥ {minimum} attendu).")


def _valider(etat: ConfigState) -> None:
    """Refuse une configuration incohérente, qu'elle vienne d'une affectation ou de using_config."""
    if etat.float_policy not in ("rationalize", "reject", "keep"):
        raise ValueError(f"float_policy invalide : {etat.float_policy!r} (rationalize, reject ou keep).")
    if etat.factor_policy not in ("rational", "real_radicals"):
        raise ValueError(f"factor_policy invalide : {etat.factor_policy!r} (rational ou real_radicals).")
    if etat.tutor_mode not in ("student", "teacher", "etudiant", "enseignant"):
        raise ValueError(f"tutor_mode invalide : {etat.tutor_mode!r} (etudiant ou enseignant).")
    if isinstance(etat.default_trace_level, bool) or etat.default_trace_level not in (0, 1, 2, 3):
        raise ValueError(
            f"default_trace_level invalide : {etat.default_trace_level!r} (0, 1, 2 ou 3)."
        )
    _entier("max_case_depth", etat.max_case_depth, 1)
    _entier("max_cases", etat.max_cases, 1)
    _entier("hint_min_attempts", etat.hint_min_attempts, 0)
    _entier("hint_min_delay_seconds", etat.hint_min_delay_seconds, 0)
    if etat.max_generic_dim is not None:
        _entier("max_generic_dim", etat.max_generic_dim, 1)
    if not isinstance(etat.locale, str) or not etat.locale:
        raise ValueError(f"locale invalide : {etat.locale!r}.")


_config_var: ContextVar[ConfigState] = ContextVar(
    "linalg_pedagopy_config", default=ConfigState()
)


class ConfigProxy:
    """Proxy d'accès et de modification de la configuration active."""

    @property
    def state(self) -> ConfigState:
        """État de configuration actif (immuable), propre au contexte courant."""
        return _config_var.get()

    @property
    def float_policy(self) -> FloatPolicy:
        """Traitement des flottants : ``rationalize`` (défaut), ``reject`` ou ``keep``."""
        return _config_var.get().float_policy

    @float_policy.setter
    def float_policy(self, value: FloatPolicy) -> None:
        self._set(float_policy=value)

    @property
    def locale(self) -> str:
        """Langue des messages de trace (``fr`` par défaut)."""
        return _config_var.get().locale

    @locale.setter
    def locale(self, value: str) -> None:
        self._set(locale=value)

    @property
    def default_trace_level(self) -> int:
        """Niveau de détail de ``explain()`` sans argument (0 à 3, 1 par défaut)."""
        return _config_var.get().default_trace_level

    @default_trace_level.setter
    def default_trace_level(self, value: int) -> None:
        self._set(default_trace_level=value)

    @property
    def max_case_depth(self) -> int:
        """Profondeur maximale des discussions par cas imbriquées."""
        return _config_var.get().max_case_depth

    @max_case_depth.setter
    def max_case_depth(self, value: int) -> None:
        self._set(max_case_depth=value)

    @property
    def max_cases(self) -> int:
        """Nombre maximal de branches d'une discussion par cas."""
        return _config_var.get().max_cases

    @max_cases.setter
    def max_cases(self, value: int) -> None:
        self._set(max_cases=value)

    @property
    def max_generic_dim(self) -> int | None:
        """Taille au-delà de laquelle Gauss-Jordan sur une matrice à paramètres émet un PedagogicalWarning (None : jamais)."""
        return _config_var.get().max_generic_dim

    @max_generic_dim.setter
    def max_generic_dim(self, value: int | None) -> None:
        self._set(max_generic_dim=value)

    @property
    def factor_policy(self) -> FactorPolicy:
        """Factorisation des résultats : sur Q ("rational") ou avec les radicaux de la condition ("real_radicals")."""
        return _config_var.get().factor_policy

    @factor_policy.setter
    def factor_policy(self, value: FactorPolicy) -> None:
        self._set(factor_policy=value)

    @property
    def tutor_mode(self) -> TutorMode:
        """Mode du tuteur : ``etudiant`` ou ``enseignant`` (``student`` / ``teacher`` acceptés)."""
        return _config_var.get().tutor_mode

    @tutor_mode.setter
    def tutor_mode(self, value: TutorMode) -> None:
        self._set(tutor_mode=value)

    @property
    def hint_min_attempts(self) -> int:
        """Nombre de tentatives exigées avant de débloquer un nouvel indice."""
        return _config_var.get().hint_min_attempts

    @hint_min_attempts.setter
    def hint_min_attempts(self, value: int) -> None:
        self._set(hint_min_attempts=max(0, int(value)))

    @property
    def hint_min_delay_seconds(self) -> int:
        """Délai minimal, en secondes, entre deux indices."""
        return _config_var.get().hint_min_delay_seconds

    @hint_min_delay_seconds.setter
    def hint_min_delay_seconds(self, value: int) -> None:
        self._set(hint_min_delay_seconds=max(0, int(value)))

    @property
    def journal_path(self) -> Path:
        """Fichier du journal de progression du tuteur."""
        return _config_var.get().journal_path

    @journal_path.setter
    def journal_path(self, value: Path | str) -> None:
        self._set(journal_path=Path(value))

    def _set(self, **kwargs: Any) -> None:
        etat = replace(_config_var.get(), **kwargs)
        _valider(etat)
        _config_var.set(etat)

    def reset(self) -> None:
        """Réinitialise la configuration aux valeurs par défaut."""
        _config_var.set(ConfigState())

    @contextmanager
    def override(self, **kwargs: Any) -> Iterator[ConfigState]:
        """Modifie temporairement la configuration dans un bloc with."""
        current = _config_var.get()
        if "journal_path" in kwargs and isinstance(kwargs["journal_path"], str):
            kwargs["journal_path"] = Path(kwargs["journal_path"])
        new_state = replace(current, **kwargs)
        _valider(new_state)
        token = _config_var.set(new_state)
        try:
            yield new_state
        finally:
            _config_var.reset(token)


config = ConfigProxy()
using_config = config.override
