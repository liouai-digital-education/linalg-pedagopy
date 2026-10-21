"""Structures de données immuables pour l'arbre de trace."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Iterator, Mapping


class StepKind(Enum):
    """Catégories d'étapes dans l'arbre de trace."""

    SECTION = auto()
    INFO = auto()
    WARNING = auto()
    ROW_SWAP = auto()
    ROW_SCALE = auto()
    ROW_ADD = auto()
    DOT = auto()
    NORM = auto()
    PROJECTION = auto()
    SUBTRACT = auto()
    NORMALIZE = auto()
    BACK_SUBSTITUTION = auto()
    CASE_SPLIT = auto()
    CHECK = auto()
    RESULT = auto()


@dataclass(frozen=True)
class Highlight:
    """Mise en évidence visuelle pour les matrices augmentées et pivots."""

    pivot: tuple[int, int] | None = None  # indices 0-based (row, col)
    rows: tuple[int, ...] = ()  # indices 0-based des lignes modifiées
    cols: tuple[int, ...] = ()  # indices 0-based des colonnes mises en évidence
    augmented_split: int | None = None  # nombre de colonnes à gauche de la barre '|'
    operation_latex: str | None = None  # opération affichée au-dessus de la flèche


@dataclass(frozen=True)
class Step:
    """Nœud immuable de l'arbre de trace."""

    kind: StepKind
    level: int
    message_key: str
    params: Mapping[str, Any] = field(default_factory=dict)
    snapshot: Mapping[str, Any] = field(default_factory=dict)
    highlight: Highlight | None = None
    children: tuple[Step, ...] = ()

    def filter_level(self, max_level: int) -> Step | None:
        """Renvoie une copie de l'arbre filtrée jusqu'au niveau max_level.

        Une section plus détaillée que ``max_level`` disparaît, mais ses étapes visibles
        remontent à sa place : les opérations de lignes (niveau 1), rangées dans les sections
        de colonne (niveau 2), restent affichées au niveau 1.
        """
        if self.message_key != "trace.root" and self.level > max_level:
            return None
        return replace(self, children=self._filtered_children(max_level))

    def _filtered_children(self, max_level: int) -> tuple[Step, ...]:
        kept: list[Step] = []
        for child in self.children:
            if child.level <= max_level:
                kept.append(replace(child, children=child._filtered_children(max_level)))
            else:
                kept.extend(child._filtered_children(max_level))
        return tuple(kept)

    def __iter__(self) -> Iterator[Step]:
        return iter(self.children)

    def __len__(self) -> int:
        return len(self.children)

    def __getitem__(self, index: int) -> Step:
        return self.children[index]

    def _repr_markdown_(self) -> str:
        """Rendu Markdown avec formules LaTeX dans Jupyter."""
        from linalg_pedagopy.render.markdown import render_step_markdown

        return render_step_markdown(self)
