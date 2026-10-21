# Accueil de la documentation

**`linalg_pedagopy`** est un package Python d'**algèbre linéaire formelle et pédagogique** pour l'enseignement en L1–L2 (licence, classes préparatoires, écoles d'ingénieurs). Il calcule en **arithmétique exacte**, **discute automatiquement les cas** quand un calcul dépend d'un paramètre, **explique chaque étape** au niveau de détail voulu, et propose un **tuteur** qui guide l'étudiant sur 39 exercices sans jamais donner la solution.

---

## Plan de la documentation

1. [**01. Noyau formel et calcul exact**](01_noyau_calcul_formel.md)  
   Conversion exacte des scalaires (`to_exact`, `float_policy`), symboles réels (`symbols`), oracle de nullité à 4 verdicts (`ZeroOracle`), conditions et discussion de cas (`Condition`, `CaseSplit`, `Branch`).

2. [**02. Vecteurs, matrices et métriques**](02_vecteurs_matrices.md)  
   Objets immuables `Vector` et `Matrix`, métriques (norme, rms, moyenne, écart type, distance, angle, corrélation), les 4 vues du produit matriciel, matrices par blocs, `rref`, `rank`, `nullspace`, `inv`, `solve`, et matrices structurées (différences, sommes cumulées, moyenne glissante, Vandermonde, convolution).

3. [**03. Algorithmes et traçabilité**](03_algorithmes_traces.md)  
   Trace hiérarchique (`explain(level=0..3)`, `tracing`), `GaussJordan`, substitutions triangulaires, `GramSchmidt`, `QR` exacte et rationnelle, `LeastSquares`, déterminant (`Determinant` : Bareiss, élimination, cofacteurs, Sarrus).

4. [**04. Le tuteur interactif**](04_tuteur.md)  
   Catalogue nommé, séance pas à pas (énoncé, indices, exercice jumeau, vérification, laboratoire, bilan), panneau JupyterLab, mode enseignant, format des fiches et validation.

5. [**05. Exercices et sessions guidées**](05_exercices_sessions.md)  
   Générateurs à résultats propres, générateurs d'exercices jumeaux, sessions interactives (`InteractiveSession`) et diagnostic des erreurs d'opérations de lignes.

6. [**06. Rendu, visualisation et comparaison numérique**](06_rendu_visualisation_numerique.md)  
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
pip install -e .                               # base
pip install -e ".[tuteur]"                     # + JupyterLab et panneau interactif
pip install -e ".[plot]"                       # + figures Matplotlib
pip install -e ".[compare]"                    # + comparaison avec NumPy
pip install -e ".[docs]"                       # + génération du site et du catalogue (contributeurs)
pip install -e ".[dev,tuteur,plot,compare]"    # tout, avec les outils de test
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
#> Discussion selon a
#> ├─ Cas a ≠ 1 (générique) : pivots non nuls, rang 3, solution unique
#> │    x = ( (a − 4)/(a − 1), 1/(a − 1), 2/(a − 1) )
#> └─ Cas a = 1 : L2 et L3 deviennent (0 0 0 | 1) et (0 0 0 | 2)
#>      système incompatible (témoin : 0 = 1)

print(result.at(a=0).solution)
#> UniqueSolution(x=(4, -1, -2))
```

### Première séance avec le tuteur

```python
from linalg_pedagopy import tuteur, Matrix

print(tuteur.catalogue())                     # les 39 exercices, par thème

ex = tuteur.exercice("moyenne-glissante")   # ou tuteur.exercice(16)
print(ex.enonce())                      # dans JupyterLab : ex.enonce() suffit
print(ex.indice())                           # palier 1 au premier lancement (voir ci-dessous)

rapport = ex.verifier(Matrix.zeros(3, 6))    # une réponse fausse
print(rapport.valide)                       # False
print(rapport.diagnostic)                  # ce que calcule la réponse, et une question
```

Dans JupyterLab, `ex.panneau()` ouvre un panneau avec les indices, l'exercice jumeau, une zone de réponse et le bilan.

La progression est enregistrée dans un journal, `.linalg_pedagopy_journal.json`, créé dans le répertoire courant : en relançant l'exemple, `ex.indice()` donne le palier suivant. `ex.recommencer()` repart de zéro.

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

## Noms du tuteur : français et anglais

Le tuteur s'utilise avec des noms français ; les noms anglais restent disponibles jusqu'à la version 0.4.0.0 (avertissement à partir de 0.3.2.0) :

| Concept | Nom français | Nom anglais (jusqu'à 0.4.0.0) |
| :--- | :--- | :--- |
| Module | `from linalg_pedagopy import tuteur` | `from linalg_pedagopy import tutor` |
| Catalogue | `tuteur.catalogue()` | `tutor.catalog()` |
| Ouvrir un exercice | `tuteur.exercice("moyenne-glissante")` | `tutor.exercise("moyenne-glissante")` |
| Énoncé | `ex.enonce()` | `ex.statement()` |
| Indice | `ex.indice()` | `ex.hint()` |
| Exercice jumeau | `ex.jumeau()` | `ex.twin()` |
| Prédiction | `ex.predire(...)` | `ex.predict(...)` |
| Laboratoire | `ex.labo()` | `ex.lab()` |
| Vérification | `ex.verifier(reponse)` | `ex.verify(reponse)` |
| Bilan | `ex.bilan()` | `ex.summary()` |
| Repartir de zéro | `ex.recommencer()` | `ex.reset()` |
| Fiche enseignant | `ex.fiche_enseignant()` | `ex.teacher_sheet()` |
| Liste des identifiants | `tuteur.lister_exercices()` | `tutor.list_exercises()` |
| Valider une fiche | `tuteur.valider_fiche(id)` | `tutor.validate_sheet(id)` |
| Glossaire | `tuteur.glossaire(terme)` | `tutor.glossary(terme)` |
| Mode | `tuteur.mode("enseignant")` | `tutor.mode("teacher")` |

Le reste du package garde ses noms anglais, avec des alias français durables : `generators.moving_average(...)` / `generateurs.moyenne_glissante(...)`, `difference_matrix(n)` / `matrice_differences(n)`…

---

## Sources et remerciements

Les exercices 1 à 35 du tuteur sont adaptés, traduits et reformulés en français, d'exercices du recueil *Additional Exercises for Vectors, Matrices, and Least Squares* de Stephen Boyd et Lieven Vandenberghe, compagnon de leur livre *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (Cambridge University Press, 2018). Le livre et le recueil sont disponibles sur [le site des auteurs](https://web.stanford.edu/~boyd/vmls/). Plusieurs conventions du package en viennent aussi, par exemple le résidu des moindres carrés r̂ = A x̂ − b et les deux variantes de Gram-Schmidt. Les exercices du thème « Déterminants » (numéros 36 à 39) sont originaux.

Les droits sur les exercices originaux appartiennent à leurs auteurs. `linalg_pedagopy` est un projet indépendant, sans lien avec les auteurs ni avec l'éditeur, qui ne l'approuvent pas formellement. Les énoncés des fiches ne citent pas leur source, pour que l'étudiant ne puisse pas aller chercher la solution à l'extérieur, d'où cette mention groupée.
