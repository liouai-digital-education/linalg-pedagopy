"""Génère le carnet d'exercices et son corrigé à partir de cahier_vecteurs_matrices.py.

Usage (depuis ce dossier) : python generer_vecteurs_matrices.py
Produit :
- vecteurs_matrices.ipynb           (carnet de l'étudiant : énoncés, réponses, vérification, indices)
- corrige_vecteurs_matrices.ipynb   (corrigé pour l'enseignant : solutions rédigées et calculs)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "src"))
sys.path.insert(0, str(ICI))

import cahier_vecteurs_matrices as cahier  # noqa: E402

NIVEAUX = {
    1: ("Niveau 1 — Calculs sur les vecteurs", "Combinaisons linéaires, produit scalaire, norme, angle et statistiques d'un vecteur."),
    2: ("Niveau 2 — Produits de matrices", "Produit matrice-vecteur, produit matriciel, transposée, matrice de Gram, décomposition d'un vecteur."),
    3: ("Niveau 3 — Systèmes, rang et inverse", "Élimination de Gauss-Jordan, rang et noyau, inverse, ensembles de solutions, matrice d'une projection."),
    4: ("Niveau 4 — Paramètres, orthogonalisation et moindres carrés", "Discussion selon un paramètre, Gram-Schmidt, QR, moindres carrés et puissances de matrices."),
}

INIT = '''import sys
from pathlib import Path

# Accès au package depuis le dépôt (inutile si linalg_pedagopy est installé avec pip install -e .)
for chemin in (Path.cwd().parent / "src", Path.cwd()):
    if chemin.exists() and str(chemin) not in sys.path:
        sys.path.insert(0, str(chemin))

from fractions import Fraction
import sympy as sp
from linalg_pedagopy import Vector, Matrix, symbols

from cahier_vecteurs_matrices import verifier, indice, bilan'''


def _lines(text: str) -> list[str]:
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text.strip())}


def code(text: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _lines(text.strip())}


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def entete_exercice(ex: cahier.Exercice) -> str:
    etoiles = "★" * ex.niveau + "☆" * (4 - ex.niveau)
    return f"### Exercice {ex.numero} — {ex.titre}  <small>{etoiles}</small>\n\n{ex.enonce}\n\n*Réponse attendue :* {ex.forme}."


def carnet_etudiant() -> dict:
    cells = [
        md(
            """# Calcul sur les vecteurs et les matrices — 20 exercices

Ce carnet propose **20 exercices de difficulté croissante**, répartis en 4 niveaux :

| Niveau | Thème | Exercices |
| :---: | :--- | :---: |
| ★ | Calculs sur les vecteurs | 1 à 5 |
| ★★ | Produits de matrices | 6 à 10 |
| ★★★ | Systèmes, rang et inverse | 11 à 15 |
| ★★★★ | Paramètres, orthogonalisation, moindres carrés | 16 à 20 |

**Comment travailler**

1. Cherchez chaque exercice **à la main**, sur papier.
2. Saisissez votre résultat dans la cellule `reponse_k = ...` (remplacez `None`).
3. Exécutez la cellule `verifier(k, reponse_k)` : elle dit si c'est juste et, sinon, **ce qui cloche** — sans donner la solution.
4. Bloqué ? Exécutez `indice(k)` : chaque nouvel appel donne un indice de plus.

**Saisie des réponses** : vecteurs `Vector([1, -2, 3])`, matrices `Matrix([[1, 2], [3, 4]])`, fractions `Fraction(2, 3)` ou `"2/3"`, racines `sp.sqrt(2)`, π `sp.pi`. Les calculs sont exacts : pas de nombres à virgule.

> Le module `cahier_vecteurs_matrices.py` contient les vérifications… et donc les réponses. Ne l'ouvrez pas avant d'avoir cherché !"""
        ),
        code(INIT),
    ]
    niveau = 0
    for k, ex in cahier.EXERCICES.items():
        if ex.niveau != niveau:
            niveau = ex.niveau
            titre, desc = NIVEAUX[niveau]
            cells.append(md(f"---\n\n## {titre}\n\n{desc}"))
        cells.append(md(entete_exercice(ex)))
        gabarit = "\n".join("# " + ligne for ligne in ex.gabarit.split("\n"))
        cells.append(code(f"# Forme attendue :\n{gabarit}\nreponse_{k} = None"))
        cells.append(code(f"verifier({k}, reponse_{k})"))
        cells.append(code(f"# Besoin d'aide ? Exécutez cette cellule (plusieurs fois pour plus d'indices).\nindice({k})"))
    cells.append(md("---\n\n## Bilan de la séance"))
    cells.append(code("bilan()"))
    return notebook(cells)


def corrige() -> dict:
    cells = [
        md(
            """# Corrigé — Calcul sur les vecteurs et les matrices

Corrigé des 20 exercices du carnet `vecteurs_matrices.ipynb`, destiné à l'enseignant. Chaque exercice comporte la solution rédigée, puis le calcul avec `linalg_pedagopy` et la vérification de la réponse de référence."""
        ),
        code(INIT + "\nfrom cahier_vecteurs_matrices import EXERCICES"),
    ]
    niveau = 0
    for k, ex in cahier.EXERCICES.items():
        if ex.niveau != niveau:
            niveau = ex.niveau
            titre, desc = NIVEAUX[niveau]
            cells.append(md(f"---\n\n## {titre}\n\n{desc}"))
        cells.append(md(entete_exercice(ex) + f"\n\n**Solution.** {ex.solution}"))
        if ex.solution_code:
            cells.append(code(ex.solution_code))
        cells.append(code(f"verifier({k}, EXERCICES[{k}].reference)"))
    return notebook(cells)


def main() -> None:
    problemes = cahier._auto_test()
    if problemes:
        raise SystemExit("Auto-test du cahier en échec :\n- " + "\n- ".join(problemes))
    for nom, nb in (("vecteurs_matrices.ipynb", carnet_etudiant()), ("corrige_vecteurs_matrices.ipynb", corrige())):
        (ICI / nom).write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{nom} : {len(nb['cells'])} cellules")


if __name__ == "__main__":
    main()
