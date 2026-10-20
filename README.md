# `linalg_pedagopy` — algèbre linéaire formelle et pédagogique

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Licence : MIT](https://img.shields.io/badge/licence-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/liouai-digital-education/linalg-pedagopy/actions/workflows/tests.yml/badge.svg)](https://github.com/liouai-digital-education/linalg-pedagopy/actions/workflows/tests.yml)
[![Documentation](https://img.shields.io/badge/docs-en%20ligne-orange.svg)](https://liouai-digital-education.github.io/linalg-pedagopy/)

`linalg_pedagopy` est un package Python orienté objet pour **enseigner et apprendre l'algèbre linéaire par le calcul formel exact**, en L1–L2, classes préparatoires et écoles d'ingénieurs.

- **Calcul exact** : fractions et radicaux exacts, symboles réels, aucun flottant caché.
- **Discussion de cas automatique** : quand un pivot dépend d'un paramètre, le calcul se sépare en cas disjoints (`CaseSplit`), affichés en clair (`a ≠ 1 et a ≠ −1`, `b²`…).
- **Déterminant exact** : `A.det()`, avec la trace de la méthode de Bareiss (sans discussion de cas même avec paramètres), de l'élimination, du développement par cofacteurs ou de la règle de Sarrus, et les valeurs du paramètre qui rendent la matrice singulière.
- **Explications pas à pas** : chaque résultat garde la trace de ses opérations ; `explain(level=0..3)` choisit le niveau de détail, en texte, LaTeX, Markdown ou HTML.
- **Tuteur interactif** : 39 exercices nommés, classés en 9 thèmes et 3 niveaux, avec indices gradués, exercice jumeau résolu, diagnostic des erreurs et laboratoire de contre-exemples — sans jamais donner la solution.

---

## Installation

```bash
pip install -e .                               # base
pip install -e ".[tuteur]"                     # + JupyterLab et panneau interactif
pip install -e ".[plot]"                       # + figures Matplotlib
pip install -e ".[compare]"                    # + comparaison avec NumPy
pip install -e ".[dev,tuteur,plot,compare]"    # tout, avec les outils de test
```

Le pas-à-pas pour JupyterLab (environnement conda, premières cellules, dépannage) est dans [docs/09_guide_jupyterlab.md](docs/09_guide_jupyterlab.md).

---

## Exemples

### Discussion selon un paramètre

```python
from linalg_pedagopy import Matrix, Vector, symbols, GaussJordan

a, = symbols("a")
A = Matrix([[1, 1, 1],
            [1, a, 1],
            [1, 1, a]])
res = GaussJordan(A, Vector([1, 2, 3])).run()

print(res)                                   # a ≠ 1 : solution unique ; a = 1 : système incompatible
print(res.at(a=0).solution)                  # UniqueSolution(x=(4, -1, -2))
print(res.explain(level=2))                  # avec le détail des opérations de lignes
```

### Moindres carrés

```python
from linalg_pedagopy import Matrix, Vector, LeastSquares

A = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]])
ls = LeastSquares(A, Vector([1, 2, 2, 4])).run()
print(ls.x_hat)          # (9/10, 9/10)
print(ls.r_hat)          # (-1/10, -1/5, 7/10, -2/5)
print(ls.verify())       # contrôle de A^T r_hat = 0, colonne par colonne
```

### Séance avec le tuteur

```python
from linalg_pedagopy import tutor, Matrix

print(tutor.catalog())                       # les 39 exercices, par thème

ex = tutor.exercise("moyenne-glissante")     # ou tutor.exercise(16)
print(ex.statement())
print(ex.hint())                             # palier 1 : orientation

rapport = ex.verify(Matrix.zeros(3, 6))      # une réponse fausse
print(rapport.valid)                         # False
print(rapport.diagnostic)                    # ce que calcule la réponse, et une question
```

Dans JupyterLab, `ex.panel()` ouvre un panneau avec les indices, l'exercice jumeau, une zone de réponse et le bilan.

---

## Documentation

La documentation complète est dans [`docs/`](docs/index.md) (version HTML : `docs/site/index.html`, régénérée par `python scripts/build_docs_site.py`) :

| Guide | Contenu |
| :--- | :--- |
| [01. Noyau formel](docs/01_core_and_formal_computation.md) | `to_exact`, `float_policy`, `symbols`, `ZeroOracle`, `Condition`, `CaseSplit` |
| [02. Vecteurs et matrices](docs/02_vectors_and_matrices.md) | `Vector`, `Matrix`, métriques, 4 vues du produit, matrices structurées |
| [03. Algorithmes](docs/03_algorithms_and_step_tracing.md) | trace à 4 niveaux, `GaussJordan`, `GramSchmidt`, `QR`, `LeastSquares` |
| [04. Tuteur](docs/04_tuteur.md) | catalogue, séance, panneau, mode enseignant, format des fiches |
| [05. Exercices et sessions](docs/05_pedagogical_exercises_and_sessions.md) | générateurs, exercices jumeaux, sessions interactives, diagnostic d'erreurs |
| [06. Rendu et numérique](docs/06_rendering_visualization_and_numerics.md) | `Explanation`, figures, comparaison exact / flottant |
| [07. Référence de l'API](docs/07_api_reference.md) | signatures, exceptions, alias français |
| [08. Catalogue des exercices](docs/08_catalogue_exercices.md) | les 39 exercices et leurs énoncés |
| [09. Guide JupyterLab](docs/09_guide_jupyterlab.md) | installation pas à pas et dépannage |

Le [tutoriel](TUTORIAL.md) parcourt l'ensemble du package ; le carnet `carnets/tutoriel_linalg_pedagopy.ipynb` en est généré par `python scripts/convert_tutorial_to_ipynb.py`. Le dossier [`carnets/`](carnets/) contient aussi les grands problèmes et le projet d'exploration ; les scripts qui génèrent les carnets et le site sont dans [`scripts/`](scripts/).

Le dossier [`exercices/`](exercices/) contient un cahier de **20 exercices de calcul sur les vecteurs et les matrices**, de difficulté croissante, avec vérification automatique et indices (`vecteurs_matrices.ipynb`), et son corrigé (`corrige_vecteurs_matrices.ipynb`).

---

## Tests

```bash
pytest tests/ -v                 # tests unitaires et de caractérisation
python verifier_tout.py          # tout : tests + couverture, fiches, ruff, mypy, carnets
```

Les tests couvrent notamment la partition disjointe des cas et la commutation `CaseSplit.at(**p)` = calcul direct en `p`, les radicaux paramétriques, la validation des 39 fiches (absence de fuite dans les indices, contrôle croisé avec le solveur), la robustesse du tuteur face aux réponses mal formées et l'impossibilité d'extraire les données verrouillées par introspection.

Les tests de caractérisation figent les traces et les diagnostics du tuteur dans `tests/references/` pour sécuriser les refactorisations ; voir [docs/dev/tests_et_verifications.md](docs/dev/tests_et_verifications.md).

---

## Sources et remerciements

Les exercices 1 à 35 du tuteur sont adaptés, traduits et reformulés en français, d'exercices du recueil *Additional Exercises for Vectors, Matrices, and Least Squares* de Stephen Boyd et Lieven Vandenberghe, compagnon de leur livre *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (Cambridge University Press, 2018). Le livre et le recueil sont disponibles sur [le site des auteurs](https://web.stanford.edu/~boyd/vmls/). Plusieurs conventions du package en viennent aussi, par exemple le résidu des moindres carrés r̂ = A x̂ − b et les deux variantes de Gram-Schmidt. Les exercices du thème « Déterminants » (numéros 36 à 39) sont originaux.

Les droits sur les exercices originaux appartiennent à leurs auteurs. `linalg_pedagopy` est un projet indépendant, sans lien avec les auteurs ni avec l'éditeur, qui ne l'approuvent pas formellement. Les énoncés des fiches ne citent pas leur source, pour que l'étudiant ne puisse pas aller chercher la solution à l'extérieur, d'où cette mention groupée.

---

## Licence

MIT — voir [`LICENSE`](LICENSE). La licence porte sur le code et les textes propres au projet, pas sur les œuvres citées ci-dessus.
