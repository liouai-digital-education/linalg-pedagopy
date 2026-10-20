"""Génère le carnet tutoriel_linalg_pedagopy.ipynb à partir de TUTORIAL.md.

TUTORIAL.md est la source unique : chaque bloc ```python devient une cellule de code,
le texte entre les blocs devient des cellules Markdown. Une cellule d'initialisation
est ajoutée en tête (accès à src/ si le package n'est pas installé, outils d'affichage).

Usage : python scripts/convert_tutorial_to_ipynb.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "TUTORIAL.md"
TARGET = RACINE / "carnets" / "tutoriel_linalg_pedagopy.ipynb"

INIT_CELL = '''import sys
from pathlib import Path

# Permet d'utiliser le package depuis le dépôt sans installation (pip install -e . reste recommandé) :
# on cherche src/ dans le dossier courant puis ses parents (carnet ouvert depuis carnets/ ou la racine).
for _base in (Path.cwd(), *Path.cwd().parents):
    if (_base / "src" / "linalg_pedagopy").is_dir():
        if str(_base / "src") not in sys.path:
            sys.path.insert(0, str(_base / "src"))
        break

from IPython.display import Markdown, display

import linalg_pedagopy
print("linalg_pedagopy", linalg_pedagopy.__version__)'''


def _lines(text: str) -> list[str]:
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text.strip())}


def _code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _lines(text.strip("\n")),
    }


def build_cells(markdown: str) -> list[dict]:
    cells: list[dict] = []
    pos = 0
    for m in re.finditer(r"```python\n(.*?)```", markdown, re.S):
        before = markdown[pos : m.start()].strip()
        # Une cellule Markdown par section de niveau 2 pour garder un carnet lisible
        for chunk in re.split(r"\n(?=## )", before):
            chunk = chunk.strip().strip("-").strip()
            if chunk:
                cells.append(_md(chunk))
        cells.append(_code(m.group(1)))
        pos = m.end()
    tail = markdown[pos:].strip()
    for chunk in re.split(r"\n(?=## )", tail):
        chunk = chunk.strip().strip("-").strip()
        if chunk:
            cells.append(_md(chunk))
    return cells


def create_notebook() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    cells = build_cells(text)
    cells.insert(1, _code(INIT_CELL))
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    TARGET.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    n_code = sum(c["cell_type"] == "code" for c in cells)
    print(f"Carnet généré : {TARGET} ({len(cells)} cellules dont {n_code} de code)")


if __name__ == "__main__":
    create_notebook()
