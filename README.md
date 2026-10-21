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
pip install -e ".[docs]"                       # + génération du site et du catalogue (contributeurs)
pip install -e ".[dev,tuteur,plot,compare]"    # tout, avec les outils de test
```

Le pas-à-pas pour JupyterLab (environnement conda, premières cellules, dépannage) est dans [docs/09_guide_jupyterlab.md](docs/09_guide_jupyterlab.md).

---

## Exemple : un système qui dépend d'un paramètre

```python
from linalg_pedagopy import Matrix, Vector, symbols, GaussJordan

a, = symbols("a")
A = Matrix([[1, 1, 1],
            [1, a, 1],
            [1, 1, a]])
res = GaussJordan(A, Vector([1, 2, 3])).run()

print(res)
#> Discussion selon a
#> ├─ Cas a ≠ 1 (générique) : pivots non nuls, rang 3, solution unique
#> │    x = ( (a − 4)/(a − 1), 1/(a − 1), 2/(a − 1) )
#> └─ Cas a = 1 : L2 et L3 deviennent (0 0 0 | 1) et (0 0 0 | 2)
#>      système incompatible (témoin : 0 = 1)
print(res.at(a=0).solution)
#> UniqueSolution(x=(4, -1, -2))
```

`res.explain(level=2)` détaille chaque opération de lignes. La [page d'accueil de la documentation](docs/index.md) montre aussi une première séance avec le tuteur.

---

## Documentation

La documentation complète est dans [`docs/`](docs/index.md) (version HTML : `docs/site/index.html`, régénérée par `python scripts/build_docs_site.py` après `pip install -e ".[docs]"`) :

| Guide | Contenu |
| :--- | :--- |
| [01. Noyau formel et calcul exact](docs/01_noyau_calcul_formel.md) | `to_exact`, `float_policy`, `symbols`, `ZeroOracle`, `Condition`, `CaseSplit` |
| [02. Vecteurs, matrices et métriques](docs/02_vecteurs_matrices.md) | `Vector`, `Matrix`, métriques, 4 vues du produit, matrices structurées |
| [03. Algorithmes et traçabilité](docs/03_algorithmes_traces.md) | trace à 4 niveaux, `GaussJordan`, `GramSchmidt`, `QR`, `LeastSquares` |
| [04. Le tuteur interactif](docs/04_tuteur.md) | catalogue, séance, panneau, mode enseignant, format des fiches |
| [05. Exercices et sessions guidées](docs/05_exercices_sessions.md) | générateurs, exercices jumeaux, sessions interactives, diagnostic d'erreurs |
| [06. Rendu, visualisation et comparaison numérique](docs/06_rendu_visualisation_numerique.md) | `Explanation`, figures, comparaison exact / flottant |
| [07. Référence de l'API](docs/07_api_reference.md) | signatures, exceptions, alias français |
| [08. Catalogue des exercices](docs/08_catalogue_exercices.md) | les 39 exercices et leurs énoncés |
| [09. Utiliser le package dans JupyterLab](docs/09_guide_jupyterlab.md) | installation pas à pas et dépannage |

Le [tutoriel](TUTORIAL.md) parcourt l'ensemble du package ; le carnet `carnets/tutoriel_linalg_pedagopy.ipynb` en est généré par `python scripts/convert_tutorial_to_ipynb.py`. Le dossier [`carnets/`](carnets/) contient aussi les grands problèmes et le projet d'exploration ; les scripts qui génèrent les carnets et le site sont dans [`scripts/`](scripts/).

Le dossier [`exercices/`](exercices/) contient un cahier de **20 exercices de calcul sur les vecteurs et les matrices**, de difficulté croissante, avec vérification automatique et indices (`vecteurs_matrices.ipynb`), et son corrigé (`corrige_vecteurs_matrices.ipynb`).

---

## Tests

```bash
python verifier_tout.py          # tout : tests + couverture, fiches, ruff, mypy, carnets
```

Familles de tests, références de caractérisation et conventions : [docs/dev/tests_et_verifications.md](docs/dev/tests_et_verifications.md).

---

## Sources et remerciements

Les exercices 1 à 35 du tuteur sont adaptés, traduits et reformulés en français, d'exercices du recueil *Additional Exercises for Vectors, Matrices, and Least Squares* de Stephen Boyd et Lieven Vandenberghe, compagnon de leur livre *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (Cambridge University Press, 2018). Le livre et le recueil sont disponibles sur [le site des auteurs](https://web.stanford.edu/~boyd/vmls/). Plusieurs conventions du package en viennent aussi, par exemple le résidu des moindres carrés r̂ = A x̂ − b et les deux variantes de Gram-Schmidt. Les exercices du thème « Déterminants » (numéros 36 à 39) sont originaux.

Les droits sur les exercices originaux appartiennent à leurs auteurs. `linalg_pedagopy` est un projet indépendant, sans lien avec les auteurs ni avec l'éditeur, qui ne l'approuvent pas formellement. Les énoncés des fiches ne citent pas leur source, pour que l'étudiant ne puisse pas aller chercher la solution à l'extérieur, d'où cette mention groupée.

---

## Licence

MIT — voir [`LICENSE`](LICENSE). La licence porte sur le code et les textes propres au projet, pas sur les œuvres citées ci-dessus.
