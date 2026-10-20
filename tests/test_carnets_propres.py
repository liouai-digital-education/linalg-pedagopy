"""Les carnets du dépôt sont versionnés sans sorties (voir scripts/nettoyer_carnets.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CARNETS = sorted(p for d in ("carnets", "exercices") for p in (RACINE / d).glob("*.ipynb"))


def test_les_carnets_sont_trouves() -> None:
    assert len(CARNETS) >= 6


@pytest.mark.parametrize("carnet", CARNETS, ids=lambda p: p.name)
def test_carnet_sans_sorties(carnet: Path) -> None:
    nb = json.loads(carnet.read_text(encoding="utf-8"))
    sales = [
        i
        for i, c in enumerate(nb["cells"])
        if c["cell_type"] == "code" and (c.get("outputs") or c.get("execution_count") is not None)
    ]
    assert not sales, f"cellules avec sorties {sales} : lancez python scripts/nettoyer_carnets.py"
    assert "widgets" not in nb.get("metadata", {})
