"""Tests propres au moteur d'élimination (étape 4.6 du plan v6).

Le moteur est surtout couvert par les tests de caractérisation de Gauss-Jordan et du
déterminant ; ces tests vérifient directement ses briques et ses options : choix du pivot,
opérations de lignes tracées, modes réduit et triangulaire, arrêt sur une colonne nulle,
comptage des échanges, discussion par cas, ``SplitRequest`` et plafonds.
"""

from __future__ import annotations

from typing import Any, Iterator

from hypothesis import given, settings, strategies as st
import pytest
import sympy as sp

from linalg_pedagopy import CaseLimitError, CaseSplit, Condition, symbols, tracing
from linalg_pedagopy.algorithms.elimination import (
    EliminationEngine,
    EliminationSetup,
    EliminationState,
    RowOps,
    SplitRequest,
    _choose_pivot,
)
from linalg_pedagopy.trace.step import Step

a, b = symbols("a b")


def _etapes(step: Step) -> Iterator[Step]:
    for child in step.children:
        yield child
        yield from _etapes(child)


def _cles(step: Step) -> list[str]:
    return [s.message_key for s in _etapes(step)]


def _grille(rows: list[list[Any]]) -> list[list[sp.Expr]]:
    return [[sp.sympify(x) for x in row] for row in rows]


# --- Choix du pivot


def test_choix_du_pivot() -> None:
    cands = [(0, sp.Integer(3)), (1, sp.Integer(-1)), (2, sp.Integer(7))]
    assert _choose_pivot(cands, "simplest") == (1, -1)
    assert _choose_pivot(cands, "partial") == (2, 7)
    assert _choose_pivot(cands, "first") == (0, 3)


# --- Opérations de lignes tracées


def test_operations_de_lignes() -> None:
    ops = RowOps("gj", split_col=2)
    g = _grille([[2, 4, 6], [1, a, 1]])
    with tracing(level=3) as t:
        ops.swap(g, 0, 1, col=0)
        assert g == _grille([[1, a, 1], [2, 4, 6]])
        ops.add_multiple(g, 1, 0, sp.Integer(2), col=0)
        assert g[1] == [0, 4 - 2 * a, 4]
        scale = ops.scale(g, 1, col=1)
        assert sp.simplify(scale - 1 / (4 - 2 * a)) == 0 and g[1][1] == 1
    etapes = list(_etapes(t.tree))
    assert [s.message_key for s in etapes] == ["gj.row_swap", "gj.row_add", "gj.row_scale"]
    assert etapes[1].params["sign"] == "−" and etapes[1].params["lam_txt"] == "2"
    assert etapes[0].highlight is not None and etapes[0].highlight.augmented_split == 2
    assert "augmented_matrix" in etapes[0].snapshot


def test_transvection_signee_et_parenthesee() -> None:
    g = _grille([[1, 0], [a - 1, 1]])
    with tracing(level=3) as t:
        RowOps("gj").add_multiple(g, 1, 0, a - 1, col=0)
        RowOps("gj").add_multiple(g, 1, 0, -a, col=0)
    signee, negative = list(_etapes(t.tree))
    assert (signee.params["sign"], signee.params["lam_txt"]) == ("−", "(a − 1)")
    assert negative.params["sign"] == "+"


def test_transvection_non_signee_du_determinant() -> None:
    g = _grille([[2, 1], [4, 3]])
    with tracing(level=3) as t:
        RowOps("det", snapshot_key="matrix", signed_add=False).add_multiple(g, 1, 0, sp.Integer(2), col=0)
    (etape,) = list(_etapes(t.tree))
    assert etape.message_key == "det.row_add"
    assert etape.params == {"i": 2, "j": 1, "lam": 2}
    assert "matrix" in etape.snapshot
    assert g[1] == [0, 1]


def test_etape_de_bareiss() -> None:
    g = _grille([[2, 1, 1], [1, 3, 2], [1, 0, 0]])
    ops = RowOps("det", snapshot_key="matrix")
    with tracing(level=3):
        ops.bareiss_step(g, 0, sp.Integer(1))
        ops.bareiss_step(g, 1, sp.Integer(2))
    # Le dernier coefficient diagonal est le déterminant (aucun échange ici)
    assert g[2][2] == sp.Matrix([[2, 1, 1], [1, 3, 2], [1, 0, 0]]).det()


# --- Moteur


def _moteur(rows: list[list[Any]], **options: Any) -> tuple[EliminationEngine[Any], list[EliminationState]]:
    """Moteur sur une grille fixe ; ``on_complete`` renvoie l'état final (enregistré dans ``fins``)."""
    fins: list[EliminationState] = []

    def setup(cond: Condition) -> EliminationSetup:
        subs = cond.substitutions()
        grid = [[sp.sympify(x).xreplace(subs) for x in row] for row in rows]
        return EliminationSetup(grid=grid, n_cols=len(rows[0]))

    class Fin:
        def __init__(self, st: EliminationState) -> None:
            self.st = st

    def on_complete(st: EliminationState) -> Fin:
        fins.append(st)
        return Fin(st)

    options.setdefault("max_depth", 3)
    options.setdefault("max_cases", 8)
    return EliminationEngine(prefix="gj", setup=setup, on_complete=on_complete, **options), fins


def test_forme_reduite() -> None:
    M = [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]
    engine, fins = _moteur(M)
    engine.run(Condition.true())
    (st,) = fins
    assert sp.Matrix(st.grid) == sp.Matrix(M).rref()[0]
    assert st.pivots == [0, 1, 2]


def test_triangulation_sans_dilatation_et_echanges() -> None:
    M = [[0, 2, 1], [3, 1, 2], [1, 1, 1]]
    engine, fins = _moteur(M, reduce_above=False, normalize_pivots=False)
    engine.run(Condition.true())
    (st,) = fins
    produit = sp.Mul(*(st.grid[k][k] for k in range(3)))
    assert (-1) ** st.swaps * produit == sp.Matrix(M).det()
    assert st.swaps >= 1
    assert all(st.grid[i][j] == 0 for i in range(3) for j in range(i))  # triangulaire supérieure


def test_arret_sur_colonne_nulle() -> None:
    engine, fins = _moteur(
        [[1, 2, 3], [2, 4, 6], [0, 0, 1]], reduce_above=False, normalize_pivots=False, stop_on_zero_column=True
    )
    with tracing(level=3) as t:
        engine.run(Condition.true())
    (st,) = fins
    assert st.pivots == [0]
    assert "gj.zero_column" in _cles(t.tree)
    assert "gj.col_zero" not in _cles(t.tree)


def test_options_de_presentation() -> None:
    engine, _ = _moteur([[0, 1], [1, 0]], start_section=False, column_sections=False)
    with tracing(level=3) as t:
        engine.run(Condition.true())
    cles = _cles(t.tree)
    assert "gj.start" not in cles and "gj.column_step" not in cles and "gj.pivot_chosen" not in cles
    assert cles.index("gj.row_swap") < cles.index("gj.pivot")  # pivot annoncé après l'échange

    engine, _ = _moteur([[0, 1], [1, 0]])
    with tracing(level=3) as t:
        engine.run(Condition.true())
    cles = _cles(t.tree)
    assert {"gj.start", "gj.column_step", "gj.pivot_chosen"} <= set(cles)
    assert cles.index("gj.pivot_chosen") < cles.index("gj.row_swap")


def test_discussion_par_cas() -> None:
    engine, fins = _moteur([[a, 1], [0, b]])
    res = engine.run(Condition.true())
    assert isinstance(res, CaseSplit)
    assert [br.condition.format_text() for br in res.branches] == [
        "a ≠ 0 et b ≠ 0",
        "a ≠ 0 et b = 0",
        "a = 0",
    ]
    assert [len(st.pivots) for st in fins] == [2, 1, 1]
    assert all(br.trace is not None for br in res.branches)


def test_split_request_de_on_complete() -> None:
    """``on_complete`` peut demander une discussion (ex. compatibilité d'un second membre)."""

    def setup(cond: Condition) -> EliminationSetup:
        val = (a - 1).xreplace(cond.substitutions())
        return EliminationSetup(grid=[[sp.Integer(1), val]], n_cols=1, context=val)

    def on_complete(st: EliminationState) -> Any:
        val = st.setup.context
        if val.free_symbols and st.cond.implies_zero(val) is None:
            return SplitRequest(factors=(val,), row=0, col=1, expr=val)
        return type("Fin", (), {"val": val})()

    engine: EliminationEngine[Any] = EliminationEngine(
        prefix="gj", setup=setup, on_complete=on_complete, max_depth=3, max_cases=8
    )
    res = engine.run(Condition.true())
    assert isinstance(res, CaseSplit)
    assert [br.condition.format_text() for br in res.branches] == ["a ≠ 1", "a = 1"]
    assert res.branches[1].result.val == 0


def test_plafonds_avec_et_sans_arguments() -> None:
    engine, _ = _moteur([[a, 0], [0, b]], max_cases=1)
    with pytest.raises(CaseLimitError, match=r"max_cases=2, ou config.max_cases = 2"):
        engine.run(Condition.true())
    engine, _ = _moteur([[a, 0], [0, b]], max_cases=1, limit_arguments=False)
    with pytest.raises(CaseLimitError, match=r"relevez le plafond \(config.max_cases = 2\)"):
        engine.run(Condition.true())
    engine, _ = _moteur([[a, 0], [0, b]], max_depth=1)
    with pytest.raises(CaseLimitError) as info:
        engine.run(Condition.true())
    assert info.value.limit == "max_depth" and info.value.factors == (a, b)


# --- Étape 4.9 : pivot creux et remontée


def test_pivot_creux_markowitz() -> None:
    g = _grille([[1, 1, 1, 1], [1, 0, 0, 0], [-1, 1, 1, 0]])
    cands = [(0, sp.Integer(1)), (1, sp.Integer(1)), (2, sp.Integer(-1))]
    assert _choose_pivot(cands, "sparse", g, 0) == (1, 1)  # ligne la plus creuse
    assert _choose_pivot(cands, "simplest", g, 0) == (0, 1)


def test_remontee_trace_et_resultat() -> None:
    from linalg_pedagopy import GaussJordan, Matrix, Vector

    A = Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
    rhs = Vector([8, -11, -3])
    res = GaussJordan(A, rhs, reduction="back_substitution").run()
    assert res.solution == GaussJordan(A, rhs).run().solution
    (remontee,) = [s for s in _etapes(res.trace) if s.message_key == "gj.back_substitution"]
    montantes = [s for s in _etapes(remontee) if s.message_key == "gj.row_add"]
    toutes = [s for s in _etapes(res.trace) if s.message_key == "gj.row_add"]
    descendantes = [s for s in toutes if s not in montantes]
    # Descente : transvections sous le pivot ; remontée : au-dessus
    assert descendantes and all(s.params["i"] > s.params["j"] for s in descendantes)
    assert montantes and all(s.params["i"] < s.params["j"] for s in montantes)


@pytest.mark.parametrize("option", [{"pivot_strategy": "rarest"}, {"reduction": "upward"}])
def test_options_invalides(option: dict[str, str]) -> None:
    from linalg_pedagopy import GaussJordan, Matrix

    with pytest.raises(ValueError):
        GaussJordan(Matrix([[1, 2], [3, 4]]), **option)  # type: ignore[arg-type]


@settings(max_examples=40, deadline=None)
@given(
    st.integers(1, 4).flatmap(
        lambda m: st.integers(1, 4).flatmap(
            lambda n: st.lists(st.lists(st.integers(-3, 3), min_size=n, max_size=n), min_size=m, max_size=m)
        )
    ),
    st.sampled_from(["simplest", "sparse"]),
)
def test_meme_forme_reduite_quelle_que_soit_la_methode(lignes: list[list[int]], strategie: str) -> None:
    from linalg_pedagopy import GaussJordan, Matrix

    M = Matrix(lignes)
    attendue = sp.Matrix(lignes).rref()[0]
    for reduction in ("simultaneous", "back_substitution"):
        res = GaussJordan(M, pivot_strategy=strategie, reduction=reduction).run()  # type: ignore[arg-type]
        assert sp.Matrix(res.rref.entries_grid) == attendue
