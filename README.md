# `linalg_pedagopy` v3.0 — Algèbre Linéaire Formelle et Pédagogique

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: Pytest](https://img.shields.io/badge/tests-61%20passed%20%7C%20Hypothesis-brightgreen.svg)]()
[![Documentation](https://img.shields.io/badge/docs-exhaustive%20v3.0-orange.svg)](docs/index.md)

`linalg_pedagopy` est un package Python orienté objet conçu pour **l'enseignement et l'apprentissage actif de l'algèbre linéaire par le calcul formel exact** en Licence 1–2, CPGE et écoles d'ingénieurs.

Fondé sur le manuel de référence international **Stephen Boyd & Lieven Vandenberghe**, *Introduction to Applied Linear Algebra — Vectors, Matrices, and Least Squares (VMLS)* (Cambridge University Press), complété par les approches de Lay et Strang, le package combine l'exactitude symbolique sans arrondi, la discussion automatique des cas paramétriques (`CaseSplit`), une traçabilité hiérarchique à granularité variable, et un **Tuteur intelligent interactif inviolable** pour les 35 fiches officielles de VMLS.

---

## 📚 Documentation complète

Une documentation exhaustive et détaillée est disponible dans le dossier [`docs/`](docs/index.md) :

- 📖 [**Portail d'accueil et Guide de démarrage**](docs/index.md)
- 🧮 [**01. Noyau formel et Calcul Symbolique Exact**](docs/01_core_and_formal_computation.md) : `to_exact`, `float_policy`, `symbols(real=True)`, `ZeroOracle` à 4 verdicts, simplification `unrad`, `Condition`, `CaseSplit` et commutation.
- 📐 [**02. Vecteurs, Matrices et Métriques VMLS**](docs/02_vectors_and_matrices.md) : Objets immuables, produit scalaire, norme, angle, RMS, écart type, corrélation, les 4 vues du produit matriciel, matrices par blocs, rref, rang, noyau et inverse formelle.
- ⚙️ [**03. Algorithmes fondamentaux et Traçabilité hiérarchique**](docs/03_algorithms_and_step_tracing.md) : `Tracer` à 4 niveaux, `GaussJordan`, `ForwardSubstitution`, `BackSubstitution`, `GramSchmidt`, `QR` (exacte et rationnelle, par Gram-Schmidt), et `LeastSquares` (QR rationnelle, QR, équations normales).
- 🎓 [**04. Le Tuteur Interactif VMLS (`tutor` / `tuteur`)**](docs/04_vmls_tutor.md) : Coffres-forts `_LOCK_VAULT`, proxies verrouillés, catalogue des 35 fiches, indices gradués sans fuite, exercice jumeau `twin`, laboratoire `lab`, et panneau interactif JupyterLab `panel`.
- 🧪 [**05. Exercices pédagogiques et Sessions interactives**](docs/05_pedagogical_exercises_and_sessions.md) : Générateurs à résultats propres (matrices unimodulaires, RREF entière, QR rationnelle, Cayley), générateurs d'exercices jumeaux, sessions interactives pas-à-pas et catalogue d'erreurs étudiantes.
- 📊 [**06. Rendu, Visualisation et Comparaison Numérique**](docs/06_rendering_visualization_and_numerics.md) : Moteurs de rendu (Markdown/MathJax, LaTeX, Unicode), géométrie 2D/3D Matplotlib, et banc de test `compare` (matrices de Läuchli et Hilbert).
- 📑 [**07. Référence complète de l'API**](docs/07_api_reference.md) : Dictionnaire exhaustif des classes, méthodes, fonctions, exceptions et table de correspondance bilingue.

---

## ✨ Fonctionnalités phares

1. **Exactitude formelle absolue** : Aucun nombre flottant masqué. Coercition explicite des flottants (`float_policy="rationalize"` par défaut, `"reject"` ou `"keep"`). Symboles réels automatiques (`real=True`).
2. **Oracle de nullité (`ZeroOracle`) & Arbre de cas (`CaseSplit`)** : Traitement déterministe des paramètres via 4 verdicts (`ZERO`, `NONZERO`, `CONDITIONAL`, `UNKNOWN`), résolution des radicaux (`unrad`), et partitionnement disjoint par préfixes d'inégalités.
3. **Traçabilité hiérarchique à 4 niveaux** : chaque résultat conserve sa trace complète et `result.explain(level=0..3)` adapte le degré de détail des explications au niveau des étudiants (du simple résultat jusqu'aux contrôles élémentaires) ; le context manager `tracing(level=...)` regroupe les traces de plusieurs calculs.
4. **Tuteur VMLS anti-triche** : données d'exercice isolées dans des coffres privés (`WeakKeyDictionary`) et objets verrouillés à `__slots__ = ("__weakref__",)`, ce qui empêche l'extraction directe des données ou de la cible par simple introspection dans Jupyter (ce n'est pas une protection cryptographique).
5. **Nomenclature bilingue transparente** : API primaire en anglais standard (`linalg_pedagopy.tutor`, `.statement()`, `.hint()`, `.verify()`) et alias francophones complets (`linalg_pedagopy.tuteur`, `.enonce()`, `.indice()`, `.verifier()`).

---

## 🚀 Installation

```bash
# Installation standard
pip install -e .

# Avec support du tuteur graphique JupyterLab
pip install -e ".[tuteur]"

# Avec rendu graphique 2D/3D (Matplotlib)
pip install -e ".[plot]"

# Avec comparaison numérique NumPy
pip install -e ".[compare]"

# Installation de développement complète (avec tests de propriétés Hypothesis)
pip install -e ".[dev,tuteur,plot,compare]"
```

---

## 💡 Exemples d'utilisation

### 1. Discussion automatique selon un paramètre réel

```python
from linalg_pedagopy import Matrix, Vector, symbols, GaussJordan

# Déclaration de symboles réels
a, = symbols("a")
A = Matrix([
    [1, 1, 1],
    [1, a, 1],
    [1, 1, a]
])
b = Vector([1, 2, 3])

res = GaussJordan(A, b).run()

# Affiche l'arbre des cas (a ≠ 1 : solution unique ; a = 1 : système incompatible)
print(res.explain(level=2))

# Spécialisation instantanée en un point du paramètre
print("Cas a = 1 :", res.at(a=1).solution)   # EmptySolution(ligne L2 : 0 = 1)
print("Cas a = 0 :", res.at(a=0).solution)   # UniqueSolution(x=(4, -1, -2))
```

### 2. Régression des Moindres Carrés et vérification géométrique

```python
from linalg_pedagopy import Matrix, Vector, LeastSquares

A = Matrix([
    [1, 0],
    [1, 1],
    [1, 2],
    [1, 3]
])
y = Vector([1, 2, 2, 4])

ls = LeastSquares(A, y).run()
print("Paramètres estimés x_hat :", ls.x_hat)
print("Prédiction y_hat :", ls.y_hat)
print("Résidu r_hat :", ls.r_hat)
print("Contrôle A^T r_hat == 0 :")
print(ls.verify())   # Explanation détaillant le contrôle colonne par colonne
```

### 3. Séance guidée avec le Tuteur VMLS

```python
from linalg_pedagopy.tutor import exercise
from linalg_pedagopy import Matrix

# Chargement de la fiche d'exercice 6.4 (écart à la moyenne glissante : d = A p)
ex = exercise("6.4")

# Énoncé avec formules LaTeX
print(ex.statement())

# Demande d'un indice de niveau 1 (conceptuel)
print(ex.hint())

# Étude de l'exercice jumeau résolu
print(ex.twin().solution_summary)

# Soumission d'une réponse étudiante candidate (ici fausse)
rep = Matrix.zeros(3, 6)
rapport = ex.verify(rep)
print("Réponse valide :", rapport.valid)        # False
print("Diagnostic :", rapport.diagnostic)
```

---

## 🧪 Tests et validation continue

Le package est rigoureusement testé par une suite complète combinant tests unitaires et tests de propriétés stochastiques sous **Hypothesis** :

```bash
# Exécution de la suite complète de tests (61 fonctions de test)
pytest tests/ -v
```

Les tests valident notamment :
- La partition disjointe de l'espace des paramètres.
- La commutation stricte de la spécialisation `CaseSplit.at(**p) == Solve(A.subs(p), b.subs(p))`.
- La résolution exacte des radicaux paramétriques.
- L'inviolabilité des coffres-forts du tuteur face à l'introspection Python.
- La validation croisée des 35 fiches d'exercices VMLS.

---

## 📜 Licence

Projet distribué sous licence MIT. Voir le fichier [`LICENSE`](LICENSE) pour plus de détails.
