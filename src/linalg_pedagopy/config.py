"""Configuration centralisée et contextuelle pour linalg_pedagopy v3.0."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterator, Literal

FloatPolicy = Literal["rationalize", "reject", "keep"]
TutorMode = Literal["student", "teacher", "etudiant", "enseignant"]


@dataclass(frozen=True)
class ConfigState:
    """État immuable de la configuration du package."""

    float_policy: FloatPolicy = "rationalize"
    locale: str = "fr"
    default_trace_level: int = 1
    max_case_depth: int = 3
    max_cases: int = 8
    tutor_mode: TutorMode = "student"
    hint_min_attempts: int = 0
    hint_min_delay_seconds: int = 0
    journal_path: Path = Path(".linalg_pedagopy_journal.json")


_config_var: ContextVar[ConfigState] = ContextVar(
    "linalg_pedagopy_config", default=ConfigState()
)


class ConfigProxy:
    """Proxy d'accès et de modification de la configuration active."""

    @property
    def state(self) -> ConfigState:
        return _config_var.get()

    @property
    def float_policy(self) -> FloatPolicy:
        return _config_var.get().float_policy

    @float_policy.setter
    def float_policy(self, value: FloatPolicy) -> None:
        if value not in ("rationalize", "reject", "keep"):
            raise ValueError(f"float_policy invalide : {value!r}")
        _config_var.set(replace(_config_var.get(), float_policy=value))

    @property
    def locale(self) -> str:
        return _config_var.get().locale

    @locale.setter
    def locale(self, value: str) -> None:
        _config_var.set(replace(_config_var.get(), locale=value))

    @property
    def default_trace_level(self) -> int:
        return _config_var.get().default_trace_level

    @default_trace_level.setter
    def default_trace_level(self, value: int) -> None:
        if not (0 <= value <= 3):
            raise ValueError("default_trace_level doit être compris entre 0 et 3.")
        _config_var.set(replace(_config_var.get(), default_trace_level=value))

    @property
    def max_case_depth(self) -> int:
        return _config_var.get().max_case_depth

    @max_case_depth.setter
    def max_case_depth(self, value: int) -> None:
        _config_var.set(replace(_config_var.get(), max_case_depth=value))

    @property
    def max_cases(self) -> int:
        return _config_var.get().max_cases

    @max_cases.setter
    def max_cases(self, value: int) -> None:
        _config_var.set(replace(_config_var.get(), max_cases=value))

    @property
    def tutor_mode(self) -> TutorMode:
        return _config_var.get().tutor_mode

    @tutor_mode.setter
    def tutor_mode(self, value: TutorMode) -> None:
        if value not in ("student", "teacher", "etudiant", "enseignant"):
            raise ValueError(f"tutor_mode invalide : {value!r}")
        _config_var.set(replace(_config_var.get(), tutor_mode=value))

    @property
    def hint_min_attempts(self) -> int:
        return _config_var.get().hint_min_attempts

    @hint_min_attempts.setter
    def hint_min_attempts(self, value: int) -> None:
        _config_var.set(replace(_config_var.get(), hint_min_attempts=max(0, int(value))))

    @property
    def hint_min_delay_seconds(self) -> int:
        return _config_var.get().hint_min_delay_seconds

    @hint_min_delay_seconds.setter
    def hint_min_delay_seconds(self, value: int) -> None:
        _config_var.set(
            replace(_config_var.get(), hint_min_delay_seconds=max(0, int(value)))
        )

    @property
    def journal_path(self) -> Path:
        return _config_var.get().journal_path

    @journal_path.setter
    def journal_path(self, value: Path | str) -> None:
        _config_var.set(replace(_config_var.get(), journal_path=Path(value)))

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
        token = _config_var.set(new_state)
        try:
            yield new_state
        finally:
            _config_var.reset(token)


config = ConfigProxy()
using_config = config.override
