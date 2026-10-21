"""Messages des plafonds de discussion par cas (étape 3.4 du plan v6).

Quand ``max_cases`` ou ``max_depth`` arrête une discussion, ``CaseLimitError`` dit
quels facteurs ouvrent des cas, dans quelle branche on se trouve, et propose une
hypothèse et un plafond plus élevé qui permettent de poursuivre.
"""

from __future__ import annotations

import pytest

from linalg_pedagopy import (
    CaseLimitError,
    CaseSplit,
    GaussJordan,
    Matrix,
    PedagopyError,
    Vector,
    symbols,
    using_config,
)
from linalg_pedagopy.core.zero import _normalize_assumptions, assumption_text, decide_all_zero

a, b = symbols("a b")

BLOCS = Matrix([[a, 1, 0, 0], [1, a, 0, 0], [0, 0, b, 1], [0, 0, 1, b]])


def test_plafond_de_branches() -> None:
    with pytest.raises(CaseLimitError) as info:
        GaussJordan(BLOCS, compute_inverse=True).run()
    err = info.value
    assert isinstance(err, PedagopyError)  # compatibilité : les appelants qui attrapent PedagopyError
    assert err.limit == "max_cases" and err.value == 8 and err.reached == 9
    assert err.factors == (a - 1, a + 1, b - 1, b + 1)
    message = str(err)
    assert "au moins 9 branches, au-delà du plafond max_cases=8" in message
    assert "Facteurs qui ouvrent des cas : a − 1, a + 1, b − 1, b + 1." in message
    assert "Branche en cours : a = −1." in message
    assert 'assumptions="a != 1"' in message
    assert "max_cases=16, ou config.max_cases = 16" in message


def test_les_suggestions_permettent_de_poursuivre() -> None:
    with pytest.raises(CaseLimitError) as info:
        GaussJordan(BLOCS, compute_inverse=True).run()
    err = info.value
    assert isinstance(GaussJordan(BLOCS, compute_inverse=True, assumptions=err.suggested_assumption).run(), CaseSplit)
    assert isinstance(GaussJordan(BLOCS, compute_inverse=True, max_cases=16).run(), CaseSplit)
    with using_config(max_cases=16):
        assert isinstance(GaussJordan(BLOCS, compute_inverse=True).run(), CaseSplit)


def test_plafond_de_profondeur() -> None:
    with pytest.raises(CaseLimitError) as info:
        GaussJordan(Matrix([[a, 0], [0, b]]), Vector([1, 1]), max_depth=1).run()
    err = info.value
    assert err.limit == "max_depth" and err.value == 1
    message = str(err)
    assert "plus de 1 niveau de cas emboîtés (plafond max_depth=1)" in message
    assert "max_depth=2, ou config.max_case_depth = 2" in message
    assert err.factors == (a, b)


def test_plafond_de_l_oracle_sans_argument_de_procedure() -> None:
    with using_config(max_case_depth=1):
        with pytest.raises(CaseLimitError) as info:
            decide_all_zero([a * b, a - b])
    message = str(info.value)
    assert "Pour poursuivre" in message
    assert "relevez le plafond (config.max_case_depth = 2)" in message


@pytest.mark.parametrize("fac", [a - 1, a + 1, a, 2 * a - 1, a - b, a**2 - 3])
def test_hypothese_proposee_relisible(fac) -> None:  # type: ignore[no-untyped-def]
    cond = _normalize_assumptions(assumption_text(fac))
    assert cond.implies_zero(fac) is False
