"""Hypothèses et configuration invalides : erreur claire au lieu d'un abandon silencieux."""

from __future__ import annotations

import pytest

from linalg_pedagopy import InvalidAssumptionError, Matrix, config, symbols, using_config
from linalg_pedagopy.core.cases import CaseSplit

(a,) = symbols("a")
M = Matrix([[1, a], [a, 1]])


@pytest.mark.parametrize("hypothese", ["a > 0", "a >= 0", "a < 1", "0 <= a"])
def test_inegalites_d_ordre_refusees(hypothese: str) -> None:
    with pytest.raises(InvalidAssumptionError, match="inégalités d'ordre"):
        M.rank(assumptions=hypothese)


@pytest.mark.parametrize("hypothese", ["a", "", 42, 1.5])
def test_hypotheses_non_reconnues(hypothese: object) -> None:
    with pytest.raises(InvalidAssumptionError, match="non reconnue"):
        M.rank(assumptions=hypothese)


def test_formes_acceptees() -> None:
    assert M.rank(assumptions="a != 1 ") != M.rank()
    assert M.rank(assumptions=["a != 1", "a != -1"]) == 2
    assert M.rank(assumptions={"a": 2}) == 2
    assert isinstance(M.rank(assumptions={"a": "!= 1"}), CaseSplit)
    assert M.rank(assumptions="a = 1") == 1
    assert issubclass(InvalidAssumptionError, ValueError)


@pytest.mark.parametrize(
    ("reglage", "valeur"),
    [
        ("factor_policy", "x"),
        ("float_policy", "round"),
        ("default_trace_level", 4),
        ("default_trace_level", True),
        ("max_cases", 0),
        ("max_case_depth", -1),
        ("max_generic_dim", 0),
        ("tutor_mode", "prof"),
        ("hint_min_attempts", -1),
    ],
)
def test_configuration_invalide(reglage: str, valeur: object) -> None:
    """La validation vaut pour using_config comme pour l'affectation."""
    avant = config.state
    with pytest.raises(ValueError, match=reglage), using_config(**{reglage: valeur}):
        pass
    if reglage != "hint_min_attempts":  # l'affectation ramène les négatifs à 0
        with pytest.raises(ValueError, match=reglage):
            setattr(config, reglage, valeur)
    assert config.state == avant


def test_configuration_valide() -> None:
    with using_config(max_generic_dim=None, tutor_mode="enseignant", max_cases=16):
        assert config.max_cases == 16
