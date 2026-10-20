# Documentation de `linalg_pedagopy`

**`linalg_pedagopy`** est un package Python d'**algèbre linéaire formelle et pédagogique** pour l'enseignement en L1–L2 (licence, classes préparatoires, écoles d'ingénieurs). Il calcule en **arithmétique exacte**, **discute automatiquement les cas** quand un calcul dépend d'un paramètre, **explique chaque étape** au niveau de détail voulu, et propose un **tuteur** qui guide l'étudiant sur 39 exercices sans jamais donner la solution.

---

## Plan de la documentation

1. [**01. Noyau formel et calcul exact**](01_core_and_formal_computation.md)  
   Conversion exacte des scalaires (`to_exact`, `float_policy`), symboles réels (`symbols`), oracle de nullité à 4 verdicts (`ZeroOracle`), conditions et discussion de cas (`Condition`, `CaseSplit`, `Branch`).

2. [**02. Vecteurs, matrices et métriques**](02_vectors_and_matrices.md)  
   Objets immuables `Vector` et `Matrix`, métriques (norme, rms, moyenne, écart type, distance, angle, corrélation), les 4 vues du produit matriciel, matrices par blocs, `rref`, `rank`, `nullspace`, `inv`, `solve`, et matrices structurées (différences, sommes cumulées, moyenne glissante, Vandermonde, convolution).

3. [**03. Algorithmes et traçabilité**](03_algorithms_and_step_tracing.md)  
   Trace hiérarchique (`explain(level=0..3)`, `tracing`), `GaussJordan`, substitutions triangulaires, `GramSchmidt`, `QR` exacte et rationnelle, `LeastSquares`, déterminant (`Determinant` : Bareiss, élimination, cofacteurs, Sarrus).

4. [**04. Le tuteur interactif**](04_tuteur.md)  
   Catalogue nommé, séance pas à pas (énoncé, indices, exercice jumeau, vérification, laboratoire, bilan), panneau JupyterLab, mode enseignant, format des fiches et validation.

5. [**05. Exercices et sessions guidées**](05_pedagogical_exercises_and_sessions.md)  
   Générateurs à résultats propres, générateurs d'exercices jumeaux, sessions interactives (`InteractiveSession`) et diagnostic des erreurs d'opérations de lignes.

6. [**06. Rendu, visualisation et comparaison numérique**](06_rendering_visualization_and_numerics.md)  
   Formats texte, LaTeX, Markdown et HTML (`Explanation`), figures 2D/3D, comparaison exact / flottant (Läuchli, Hilbert).

7. [**07. Référence de l'API**](07_api_reference.md)  
   Classes, fonctions, signatures, exceptions et table des alias français.

8. [**08. Catalogue des exercices**](08_catalogue_exercices.md)  
   Les 39 exercices du tuteur, par thème et par niveau, avec leurs énoncés.

9. [**09. Utiliser le package dans JupyterLab**](09_guide_jupyterlab.md)  
   Installation pas à pas, premières cellules et dépannage.

---

## Démarrage rapide

### Installation

```bash
pip install -e .                               # installation de base
pip install -e ".[tuteur]"                     # + JupyterLab et panneau interactif
pip install -e ".[plot]"                       # + figures Matplotlib
pip install -e ".[compare]"                    # + comparaison avec NumPy
pip install -e ".[dev,tuteur,plot,compare]"    # installation complète (avec les tests)
```

Le pas-à-pas complet pour JupyterLab est dans le [guide 09](09_guide_jupyterlab.md).

### Premier calcul : un système avec paramètre

```python
from linalg_pedagopy import Matrix, Vector, symbols, GaussJordan

a, = symbols("a")
A = Matrix([[1, 1, 1],
            [1, a, 1],
            [1, 1, a]])
y = Vector([1, 2, 3])

result = GaussJordan(A, y).run()
print(result)
# Discussion selon a
# ├─ Cas a ≠ 1 (générique) : pivots non nuls, rang 3, solution unique
# │    x = ( (a − 4)/(a − 1), 1/(a − 1), 2/(a − 1) )
# └─ Cas a = 1 : L2 et L3 deviennent (0 0 0 | 1) et (0 0 0 | 2)
#      système incompatible (témoin : 0 = 1)

print(result.at(a=0).solution)   # UniqueSolution(x=(4, -1, -2))
```

### Première séance avec le tuteur

```python
from linalg_pedagopy import tutor, Matrix

print(tutor.catalog())                     # les 39 exercices, par thème

ex = tutor.exercise("moyenne-glissante")   # ou tutor.exercise(16)
print(ex.statement())                      # dans JupyterLab : ex.statement() suffit
print(ex.hint())                           # palier 1 : orientation

rapport = ex.verify(Matrix.zeros(3, 6))    # une réponse fausse
print(rapport.valid)                       # False
print(rapport.diagnostic)                  # ce que calcule la réponse, et une question
```

---

## Principes de conception

| Principe | Choix | Bénéfice pédagogique |
| :--- | :--- | :--- |
| **Exactitude** | Les flottants sont convertis en fractions (`float_policy="rationalize"`) ; les symboles sont réels (`real=True`). | Pas de `0.0000000001` au lieu de `0` : on manipule les vraies valeurs. |
| **Oracle de nullité à 4 verdicts** | `ZERO`, `NONZERO`, `CONDITIONAL`, `UNKNOWN`. | Jamais de division par une quantité qui pourrait être nulle. |
| **Discussion de cas automatique** | `CaseSplit` partitionne l'espace des paramètres en cas disjoints. | Les cas particuliers ($a = 1$…) apparaissent d'eux-mêmes. |
| **Immutabilité** | `Vector` et `Matrix` ne se modifient pas. | Pas d'effet de bord pendant les manipulations de lignes. |
| **Traçabilité à 4 niveaux** | Chaque résultat garde sa trace complète ; `explain(level=0..3)` choisit le détail. | L'enseignant adapte l'explication au public. |
| **Tuteur sans solution** | Indices gradués, jumeau résolu, diagnostic, données verrouillées. | L'étudiant cherche, et sait pourquoi sa réponse est fausse. |

---

## Noms anglais et alias français

L'API principale est en anglais ; chaque élément du tuteur a un alias français :

| Concept | API (anglais) | Alias français |
| :--- | :--- | :--- |
| Module | `from linalg_pedagopy import tutor` | `from linalg_pedagopy import tuteur` |
| Catalogue | `tutor.catalog()` | `tuteur.catalogue()` |
| Ouvrir un exercice | `tutor.exercise("moyenne-glissante")` | `tuteur.exercice("moyenne-glissante")` |
| Énoncé | `ex.statement()` | `ex.enonce()` |
| Indice | `ex.hint()` | `ex.indice()` |
| Exercice jumeau | `ex.twin()` | `ex.jumeau()` |
| Prédiction | `ex.predict(...)` | `ex.predire(...)` |
| Laboratoire | `ex.lab()` | `ex.labo()` |
| Vérification | `ex.verify(reponse)` | `ex.verifier(reponse)` |
| Bilan | `ex.summary()` | `ex.bilan()` |
| Repartir de zéro | `ex.reset()` | `ex.recommencer()` |
| Fiche enseignant | `ex.teacher_sheet()` | `ex.fiche_enseignant()` |
| Liste des identifiants | `tutor.list_exercises()` | `tuteur.lister_exercices()` |
| Valider une fiche | `tutor.validate_sheet(id)` | `tuteur.valider_fiche(id)` |
| Glossaire | `tutor.glossary(terme)` | `tuteur.glossaire(terme)` |
| Mode | `tutor.mode("teacher")` | `tuteur.mode("enseignant")` |
| Jumeaux | `generators.moving_average(...)` | `generateurs.moyenne_glissante(...)` |
| Matrices structurées | `difference_matrix(n)` | `matrice_differences(n)` |

---

## Sources et remerciements

Les exercices 1 à 35 du tuteur sont adaptés, traduits et reformulés en français, d'exercices du recueil *Additional Exercises for Vectors, Matrices, and Least Squares* de Stephen Boyd et Lieven Vandenberghe, compagnon de leur livre *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (Cambridge University Press, 2018), disponibles sur [le site des auteurs](https://web.stanford.edu/~boyd/vmls/). Plusieurs conventions du package en viennent aussi (résidu des moindres carrés r̂ = A x̂ − b, variantes de Gram-Schmidt). Les exercices du thème « Déterminants » (numéros 36 à 39) sont originaux.

Les droits sur les exercices originaux appartiennent à leurs auteurs ; `linalg_pedagopy` est un projet indépendant, sans lien avec les auteurs ni avec l'éditeur. Les énoncés des fiches ne citent pas leur source, pour que l'étudiant ne puisse pas aller chercher la solution à l'extérieur : cette page et le `README.md` en tiennent lieu.
