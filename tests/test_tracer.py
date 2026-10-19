"""Tests du traceur contextuel trace/ (hiérarchie, niveaux 0..3, absence de trace hors contexte)."""

from __future__ import annotations

from linalg_pedagopy import StepKind, Vector, record, section, tracing
from linalg_pedagopy.trace import current_tracer


def test_no_tracer_outside_context() -> None:
    assert current_tracer() is None
    # record hors contexte ne fait rien et n'échoue pas
    record(StepKind.INFO, "test.noop", level=1)
    u = Vector([1, 2, 3])
    v = Vector([4, 5, 6])
    assert u.dot(v) == 32
    assert current_tracer() is None


def test_tracer_hierarchy_and_level_filtering() -> None:
    with tracing(level=3) as t:
        with section("gj.start", level=1, m=2, n=2):
            record(StepKind.ROW_SWAP, "gj.row_swap", level=1, i=1, j=2)
            with section("gj.column_step", level=2, col=1, row=1):
                record(StepKind.INFO, "zero.domain_zero", level=3, expr=0)

    tree = t.tree
    assert len(tree.children) == 1
    sec1 = tree.children[0]
    assert sec1.message_key == "gj.start"
    assert len(sec1.children) == 2

    # Filtrage au niveau 1 : la sous-section de niveau 2 disparaît
    lvl1 = tree.filter_level(1)
    assert lvl1 is not None
    assert len(lvl1.children[0].children) == 1
    assert lvl1.children[0].children[0].message_key == "gj.row_swap"

    # Filtrage au niveau 2 : l'étape de niveau 3 disparaît
    lvl2 = tree.filter_level(2)
    assert lvl2 is not None
    sec2 = lvl2.children[0].children[1]
    assert sec2.message_key == "gj.column_step"
    assert len(sec2.children) == 0


def test_tracing_recording_cutoff_at_open() -> None:
    with tracing(level=1) as t:
        u = Vector([1, 2])
        v = Vector([3, 4])
        _ = u + v  # l'addition de vecteurs est de niveau 2
    assert len(t.tree.children) == 0
