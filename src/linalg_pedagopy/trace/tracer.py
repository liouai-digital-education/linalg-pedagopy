"""Traceur contextuel arborescent à 4 niveaux via contextvars."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

from linalg_pedagopy.config import config
from linalg_pedagopy.core.field import register_trace_hook
from linalg_pedagopy.trace.step import Highlight, Step, StepKind


@dataclass
class _MutableNode:
    kind: StepKind
    level: int
    message_key: str
    params: dict[str, Any] = field(default_factory=dict)
    snapshot: dict[str, Any] = field(default_factory=dict)
    highlight: Highlight | None = None
    children: list[_MutableNode] = field(default_factory=list)

    def freeze(self) -> Step:
        return Step(
            kind=self.kind,
            level=self.level,
            message_key=self.message_key,
            params=dict(self.params),
            snapshot=dict(self.snapshot),
            highlight=self.highlight,
            children=tuple(c.freeze() for c in self.children),
        )


class Tracer:
    """Traceur actif dans un contexte d'exécution."""

    def __init__(self, level: int = 1) -> None:
        if not (0 <= level <= 3):
            raise ValueError("Le niveau de trace doit être compris entre 0 et 3.")
        self.level = level
        self._root = _MutableNode(
            kind=StepKind.SECTION,
            level=0,
            message_key="trace.root",
        )
        self._stack: list[_MutableNode] = [self._root]
        self._suppressed_depth: int = 0

    @property
    def is_suppressed(self) -> bool:
        """Vrai à l'intérieur d'une section filtrée (niveau trop détaillé) : rien n'y est enregistré."""
        return self._suppressed_depth > 0

    def push_section(
        self,
        message_key: str,
        *,
        level: int = 1,
        snapshot: Mapping[str, Any] | None = None,
        highlight: Highlight | None = None,
        **params: Any,
    ) -> bool:
        """Ouvre une section ; renvoie False si elle est filtrée (niveau trop détaillé), et ses étapes le sont aussi."""
        if self._suppressed_depth > 0 or level > self.level:
            self._suppressed_depth += 1
            return False
        node = _MutableNode(
            kind=StepKind.SECTION,
            level=level,
            message_key=message_key,
            params=dict(params),
            snapshot=dict(snapshot) if snapshot else {},
            highlight=highlight,
        )
        self._stack[-1].children.append(node)
        self._stack.append(node)
        return True

    def pop_section(self, pushed: bool) -> None:
        """Ferme la section ouverte par ``push_section`` (``pushed`` : sa valeur de retour)."""
        if not pushed:
            self._suppressed_depth = max(0, self._suppressed_depth - 1)
        elif len(self._stack) > 1:
            self._stack.pop()

    def record(
        self,
        kind: StepKind,
        message_key: str,
        *,
        level: int = 1,
        snapshot: Mapping[str, Any] | None = None,
        highlight: Highlight | None = None,
        children: tuple[Step, ...] = (),
        **params: Any,
    ) -> None:
        """Enregistre une étape dans la section courante, sauf si elle est filtrée par son niveau."""
        if self._suppressed_depth > 0 or level > self.level:
            return
        node = _MutableNode(
            kind=kind,
            level=level,
            message_key=message_key,
            params=dict(params),
            snapshot=dict(snapshot) if snapshot else {},
            highlight=highlight,
        )
        for child_step in children:
            node.children.append(_step_to_mutable(child_step))
        self._stack[-1].children.append(node)

    @property
    def tree(self) -> Step:
        """Renvoie l'arbre immuable complet enregistré par ce traceur."""
        return self._root.freeze()


def _step_to_mutable(step: Step) -> _MutableNode:
    return _MutableNode(
        kind=step.kind,
        level=step.level,
        message_key=step.message_key,
        params=dict(step.params),
        snapshot=dict(step.snapshot),
        highlight=step.highlight,
        children=[_step_to_mutable(c) for c in step.children],
    )


_active_tracer: ContextVar[Tracer | None] = ContextVar(
    "linalg_pedagopy_active_tracer", default=None
)


def current_tracer() -> Tracer | None:
    """Renvoie le traceur actif du contexte courant, ou None."""
    return _active_tracer.get()


@contextmanager
def tracing(level: int | None = None) -> Iterator[Tracer]:
    """Ouvre un contexte de traçage au niveau indiqué (0 à 3)."""
    eff_level = level if level is not None else config.default_trace_level
    tracer = Tracer(level=eff_level)
    token = _active_tracer.set(tracer)
    try:
        yield tracer
    finally:
        _active_tracer.reset(token)


@contextmanager
def suspend_tracing() -> Iterator[None]:
    """Suspend temporairement l'enregistrement de trace pour des calculs auxiliaires."""
    token = _active_tracer.set(None)
    try:
        yield
    finally:
        _active_tracer.reset(token)


@contextmanager
def section(
    message_key: str,
    *,
    level: int = 1,
    snapshot: Mapping[str, Any] | None = None,
    highlight: Highlight | None = None,
    **params: Any,
) -> Iterator[None]:
    """Ouvre une section parente dans la trace si un traceur est actif."""
    tracer = _active_tracer.get()
    if tracer is None:
        yield
        return
    pushed = tracer.push_section(
        message_key,
        level=level,
        snapshot=snapshot,
        highlight=highlight,
        **params,
    )
    try:
        yield
    finally:
        tracer.pop_section(pushed)


def record(
    kind: StepKind,
    message_key: str,
    *,
    level: int = 1,
    snapshot: Mapping[str, Any] | None = None,
    highlight: Highlight | None = None,
    children: tuple[Step, ...] = (),
    **params: Any,
) -> None:
    """Enregistre une étape élémentaire dans le traceur actif (sans effet hors contexte)."""
    tracer = _active_tracer.get()
    if tracer is None:
        return
    tracer.record(
        kind,
        message_key,
        level=level,
        snapshot=snapshot,
        highlight=highlight,
        children=children,
        **params,
    )


def _core_hook(kind_name: str, message_key: str, level: int, params: dict[str, Any]) -> None:
    kind = getattr(StepKind, kind_name, StepKind.INFO)
    record(kind, message_key, level=level, **params)


register_trace_hook(_core_hook)
