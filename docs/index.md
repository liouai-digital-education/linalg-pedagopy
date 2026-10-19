# Documentation officielle de `linalg_pedagopy` v3.0

Bienvenue dans la documentation complète et de référence de **`linalg_pedagopy`**, le package Python d'algèbre linéaire formelle et pédagogique conçu pour l'enseignement supérieur (Licence 1–2, CPGE, parcours informatique et mathématiques appliquées).

Inspiré de l'ouvrage classique de référence **Stephen Boyd & Lieven Vandenberghe**, *Introduction to Applied Linear Algebra — Vectors, Matrices, and Least Squares (VMLS)* (Cambridge University Press), complété par les approches pédagogiques de David Lay et Gilbert Strang, `linalg_pedagopy` allie la **rigueur du calcul symbolique exact** à une **didactique active et interactive**.

---

## 🧭 Plan général de la documentation

La documentation est structurée en 7 guides thématiques approfondis et une référence complète de l'API :

1. [**01. Noyau formel et Calcul Symbolique Exact**](01_core_and_formal_computation.md)  
   Types de données exacts, politique des flottants (`float_policy`), symboles réels (`symbols`), oracle de nullité à 4 verdicts (`ZeroOracle`), simplification des radicaux réels (`unrad`), partitionnement disjoint de l'espace des paramètres (`CaseSplit`, `Condition`, `Branch`), clôture transitive des substitutions et détection de contradictions.

2. [**02. Vecteurs, Matrices et Métriques VMLS**](02_vectors_and_matrices.md)  
   Objets immuables `Vector` et `Matrix`, initialisation, métriques VMLS (norme euclidienne, angle, corrélation, distance RMS, projection orthogonale), les 4 vues du produit matriciel (combinaison linéaire des colonnes, produit scalaire ligne-colonne, somme de produits externes, décomposition par blocs), propriétés matricielles (rang, noyau, image, rref, déterminant, inverse, détection de singularité).

3. [**03. Algorithmes fondamentaux et Traçabilité hiérarchique**](03_algorithms_and_step_tracing.md)  
   Architecture de traçabilité (`Tracer`, context manager `tracing()`, niveaux de détail 0 à 3, `Highlight`, `Step`), élimination de Gauss-Jordan (`GaussJordan`, pivotage formel, opérations élémentaires, calcul simultané d'inverses), substitutions triangulaires (`ForwardSubstitution`, `BackSubstitution`), orthogonalisation de Gram-Schmidt (`GramSchmidt`), factorisation QR (`QR`, Householder, Givens) et régression par moindres carrés (`LeastSquares`, équations normales, QR, projection orthogonale).

4. [**04. Le Tuteur Interactif VMLS (`tutor` / `tuteur`)**](04_vmls_tutor.md)  
   Architecture anti-triche et coffre-fort d'isolation (`_LOCK_VAULT`, `WeakKeyDictionary`, `__slots__ = ("__weakref__",)`), objets verrouillés (`LockedVector`, `LockedMatrix`), catalogue des 35 fiches d'exercices VMLS officielles (`exercise`), système d'indices gradués (niveaux 1 à 4) sans divulgation, exercice jumeau résolu (`twin`), prédiction d'étape (`predict`), laboratoire de contre-exemples (`lab`), vérificateurs formels de solutions (`verify`), journal persistant et atomique (`ExerciseJournal`), interface interactive JupyterLab (`panel`), et modes étudiant/enseignant.

5. [**05. Exercices pédagogiques et Sessions interactives**](05_pedagogical_exercises_and_sessions.md)  
   Générateurs d'exercices à résultats propres (`generators.py` : matrices de différence, moyennes mobiles, sommes cumulées, Vandermonde, matrices unimodulaires, orthogonales de Cayley, etc.), sessions interactives guidées (`InteractiveSession`, modes `read`, `predict_reveal`, `completion`, `autonomous`), et diagnostic automatique des erreurs étudiantes types (Annexe C).

6. [**06. Rendu, Visualisation et Comparaison Numérique**](06_rendering_visualization_and_numerics.md)  
   Moteurs de rendu multi-formats (`Explanation`, LaTeX, Markdown, HTML, texte Unicode), localisation multilingue (`locales/fr.yaml`, `locales/en.yaml`), figures géométriques 2D et 3D avec Matplotlib (`plot`), et comparaison du calcul exact avec les bibliothèques numériques flottantes (`compare` avec NumPy/SciPy, matrices de Hilbert, matrices de Läuchli, perte d'orthogonalité, conditionnement).

7. [**07. Référence complète de l'API**](07_api_reference.md)  
   Index alphabétique exhaustif de toutes les classes, méthodes, fonctions, exceptions et paramètres du package, avec tableau de correspondance bilingue (nomenclature primaire anglaise et alias français).

---

## ⚡ Démarrage rapide en 5 minutes

### Installation

```bash
# Installation de base
pip install -e .

# Avec support du tuteur graphique JupyterLab
pip install -e ".[tuteur]"

# Avec visualisation graphique 2D/3D (Matplotlib)
pip install -e ".[plot]"

# Avec comparaison numérique NumPy
pip install -e ".[compare]"

# Installation complète pour développement et tests
pip install -e ".[dev,tuteur,plot,compare]"
```

### Premier script : Résolution formelle et discussion paramétrique

```python
from linalg_pedagopy import Matrix, Vector, symbols, tracing, GaussJordan

# Déclaration de symboles réels
a, b = symbols("a b")

# Définition de la matrice et du second membre
A = Matrix([
    [1, 1, 1],
    [1, a, 1],
    [1, 1, a]
])
y = Vector([1, 2, 3])

# Exécution avec traçabilité pédagogique (niveau 2 : détail des opérations)
with tracing(level=2):
    result = GaussJordan(A, y).run()

# Affichage de la discussion de cas (CaseSplit)
print(result.explain())
```

### Première session avec le Tuteur VMLS

```python
from linalg_pedagopy.tutor import exercise

# Chargement d'un exercice VMLS (ex: projection orthogonale)
ex = exercise("6.4")

# Consultation de l'énoncé mathématique
print(ex.statement())

# Demande d'un indice progressif (sans divulgation de la solution)
print(ex.hint())

# Étude de l'exercice jumeau résolu
print(ex.twin().statement)
print(ex.twin().solution_summary)

# Test d'une réponse candidate
from linalg_pedagopy import Vector
reponse_etudiant = Vector([1, 2, 3])
rapport = ex.verify(reponse_etudiant)
print(rapport)
```

---

## 🎯 Philosophie et Choix de Conception

`linalg_pedagopy` a été conçu autour de 6 principes directeurs fondamentaux :

| Principe | Décision de Conception | Bénéfice Pédagogique |
| :--- | :--- | :--- |
| **Exactitude stricte** | Aucun nombre flottant non converti (`float_policy="rationalize"`). Symboles dotés de `real=True`. | Supprime les artéfacts numériques (ex: `0.0000000000000001` au lieu de `0`) et force la manipulation exacte. |
| **Oracle de nullité à 4 verdicts** | `Verdict.ZERO`, `Verdict.NONZERO`, `Verdict.CONDITIONAL`, `Verdict.UNKNOWN`. Simplification par `unrad`. | Empêche les divisions sauvages par une quantité formelle potentiellement nulle. |
| **Branchement paramétrique automatique** | Arbre de cas `CaseSplit` avec partition disjointe et propagation des contraintes (`Condition`). | L'étudiant visualise la géométrie des sous-espaces exceptionnels ($a = 1$, $a = -2$). |
| **Immutabilité rigoureuse** | Les instances de `Vector` et `Matrix` sont immuables. | Évite les effets de bord sournois pendant les algorithmes de manipulation de lignes/colonnes. |
| **Traçabilité hiérarchique** | Arbre de trace contextuel (`Tracer`) avec 4 niveaux de zoom (0 : résultat, 1 : macro, 2 : micro, 3 : arithmétique). | L'enseignant choisit le niveau d'explication adapté au niveau des étudiants. |
| **Isolation du tuteur (Anti-triche)** | Coffres-forts privés `WeakKeyDictionary` avec `__slots__ = ("__weakref__",)`. | Les étudiants ne peuvent pas extraire la solution par introspection Python (`ex.data.A`). |

---

## 🌐 Nomenclature bilingue (Anglais primaire / Alias français)

Le package adopte une **nomenclature anglaise primaire** standardisée au niveau international, tout en offrant un ensemble complet d'alias français transparents pour les cours francophones :

| Concept | API Primaire (Anglais) | Alias Rétrocompatible (Français) |
| :--- | :--- | :--- |
| Module Tuteur | `from linalg_pedagopy import tutor` | `from linalg_pedagopy import tuteur` |
| Chargement d'exercice | `tutor.exercise("6.4")` | `tuteur.exercice("6.4")` |
| Énoncé | `ex.statement()` | `ex.enonce()` |
| Indice | `ex.hint()` | `ex.indice()` |
| Exercice jumeau | `ex.twin()` | `ex.jumeau()` |
| Prédiction d'étape | `ex.predict(reponse)` | `ex.predire(reponse)` |
| Laboratoire | `ex.lab()` | `ex.labo()` |
| Vérification | `ex.verify(reponse)` | `ex.verifier(reponse)` |
| Fiche enseignant | `ex.teacher_sheet()` | `ex.fiche_enseignant()` |
| Liste des exercices | `tutor.list_exercises()` | `tuteur.lister_exercices()` |
| Validation d'une fiche | `tutor.validate_sheet("6.4")` | `tuteur.valider_fiche("6.4")` |
| Glossaire | `tutor.glossary()` | `tuteur.glossaire()` |
| Mode d'exécution | `config.tutor_mode = "student"` | `config.tutor_mode = "etudiant"` |
| Générateurs | `generators.moving_average(...)` | `generateurs.moyenne_mobile(...)` |
