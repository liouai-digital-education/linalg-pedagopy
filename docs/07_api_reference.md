# 07. Référence complète de l'API

Ce document constitue la référence des modules, classes, fonctions et exceptions publics du package `linalg_pedagopy`. Les signatures sont celles du code source (`src/linalg_pedagopy`).

Tous les noms ci-dessous sont importables depuis `linalg_pedagopy` (sauf mention d'un sous-module).

---

## 1. Noms français et anglais

Le paquet emploie des noms anglais avec des alias français, sauf le **tuteur** (`linalg_pedagopy.tuteur`), qui s'utilise en français. Les noms anglais du tuteur (`linalg_pedagopy.tutor`, `tutor.exercise`, `ex.hint`…) restent disponibles sans avertissement en 0.3.1.2, avec un `DeprecationWarning` en 0.3.2.0, et disparaissent en 0.4.0.0.

**Tuteur** :

| Nom français | Nom anglais (jusqu'à 0.4.0.0) | Module |
| :--- | :--- | :--- |
| `tuteur` | `tutor` | `linalg_pedagopy` |
| `tuteur.catalogue(theme=None)` | `tutor.catalog(theme=None)` | `linalg_pedagopy.tuteur` |
| `tuteur.themes()` | `tutor.themes()` | `linalg_pedagopy.tuteur` |
| `tuteur.recharger_catalogue()` | `tutor.reload_catalog()` | `linalg_pedagopy.tuteur` |
| `tuteur.exercice(id)` | `tutor.exercise(id)` | `linalg_pedagopy.tuteur` |
| `tuteur.lister_exercices()` | `tutor.list_exercises()` | `linalg_pedagopy.tuteur` |
| `tuteur.valider_fiche(id)` | `tutor.validate_sheet(id)` | `linalg_pedagopy.tuteur` |
| `tuteur.glossaire(term)` | `tutor.glossary(term)` | `linalg_pedagopy.tuteur` |
| `tuteur.mode("enseignant")` | `tutor.mode("teacher")` | `linalg_pedagopy.tuteur` |
| `tuteur.build_panneau(ex)` | `tutor.build_panel(ex)` | `linalg_pedagopy.tuteur` |
| `tuteur.verifier_matrice(...)`, `verifier_valeur(...)`… | `tutor.verify_matrix(...)`, `verify_value(...)`… | `linalg_pedagopy.tuteur` |
| `ExerciceSession` | `ExerciseSession` | `linalg_pedagopy.tuteur` |
| `ex.enonce()` | `ex.statement()` | `ExerciseSession` |
| `ex.donnees` | `ex.data` | `ExerciseSession` |
| `ex.indice(level=None)` | `ex.hint(level=None)` | `ExerciseSession` |
| `ex.jumeau()` | `ex.twin()` | `ExerciseSession` |
| `ex.predire(...)` | `ex.predict(...)` | `ExerciseSession` |
| `ex.labo()` | `ex.lab()` | `ExerciseSession` |
| `ex.verifier(...)` | `ex.verify(...)` | `ExerciseSession` |
| `ex.bilan()` | `ex.summary()` | `ExerciseSession` |
| `ex.recommencer()` | `ex.reset()` | `ExerciseSession` |
| `ex.titre`, `ex.numero`, `ex.niveau` | `ex.title`, `ex.number`, `ex.level` | `ExerciseSession` |
| `ex.panneau()` | `ex.panel()` | `ExerciseSession` |
| `ex.fiche_enseignant()` | `ex.teacher_sheet()` | `ExerciseSession` |

**Reste du paquet** (alias français durables) :

| Nom anglais | Alias français | Module |
| :--- | :--- | :--- |
| `generators` | `generateurs` | `linalg_pedagopy.exercises` |
| `generators.moving_average(window, n)` | `generateurs.moyenne_glissante(fenetre, n)` | `linalg_pedagopy.exercises.generators` |
| `generators.gram_schmidt_example()` | `generateurs.gram_schmidt_exemple()` | `linalg_pedagopy.exercises.generators` |
| `generators.least_squares_example()` | `generateurs.moindres_carres_exemple()` | `linalg_pedagopy.exercises.generators` |
| `difference_matrix(n)`, `running_sum_matrix(n)`… | `matrice_differences(n)`, `matrice_somme_cumulee(n)`… | `linalg_pedagopy.special` |

La liste complète des générateurs d'exercices jumeaux figure dans le [guide 05](05_pedagogical_exercises_and_sessions.md).

---

## 2. Module `linalg_pedagopy.core`

### 2.1 Fonctions scalaires et symboliques

#### `to_exact(x, *, float_policy=None) -> sympy.Expr`
Convertit un entier, une `Fraction`, une chaîne (`"2/3"`, `"sqrt(2)"`), une expression SymPy ou un flottant en expression exacte, selon `float_policy` (par défaut `config.float_policy`).

#### `symbols(*names, **assumptions) -> tuple[sympy.Symbol, ...]`
Crée des symboles SymPy munis par défaut de l'hypothèse `real=True` (toujours un tuple : `a, = symbols("a")`).

#### `match_symbol_substitutions(free_syms, mapping) -> dict[sympy.Symbol, sympy.Expr]`
À importer depuis `linalg_pedagopy.core.field`. Fait correspondre les clés d'un dictionnaire de substitution (symboles ou noms) aux symboles libres, par leur nom.

#### `choose_domain(entries) -> Domain`
Choisit le domaine SymPy (`ZZ`, `QQ`, `EX`…) adapté aux coefficients, pour les calculs `DomainMatrix`.

### 2.2 Oracle de nullité (`ZeroOracle`)

#### `Verdict (Enum)`
- `Verdict.ZERO` : nullité formelle certaine.
- `Verdict.NONZERO` : non-nullité formelle certaine.
- `Verdict.CONDITIONAL` : nullité dépendant des valeurs des paramètres réels.
- `Verdict.UNKNOWN` : non décidable sans hypothèse supplémentaire.

#### `ZeroDecision (dataclass)`
- `verdict: Verdict`
- `condition: Condition | None` : condition d'annulation (verdict conditionnel).
- `method: str` : méthode de décision utilisée.
- `factors: tuple[sympy.Expr, ...]` : facteurs d'annulation.

#### `oracle.decide(e, assumptions=None, *, trace_level3=True) -> ZeroDecision`
Analyse la nullité d'une expression (avec élimination des radicaux par `sympy.unrad` et filtrage des racines parasites). `oracle` est l'instance globale de `ZeroOracle`.

#### `oracle.is_zero(e, assumptions=None) -> bool`
Renvoie `True` si l'expression est nulle, `False` si elle est non nulle. Lève [`UndecidableZeroError`](#24-hierarchie-des-exceptions) sinon.

### 2.3 Disjonction de cas (`Condition`, `Branch`, `CaseSplit`)

#### `Condition`
Ensemble d'égalités (`eqs`) et d'inégalités (`neqs`) sur les paramètres.
- `Condition.true()` : condition vide (toujours vraie).
- `Condition.eq(lhs, rhs=0)` / `Condition.neq(lhs, rhs=0)` : contrainte `lhs = rhs` / `lhs ≠ rhs`.
- `Condition.from_zero_expr(expr, *, is_zero)` : contrainte `expr = 0` ou `expr ≠ 0`.
- `and_with(other)` ou `c1 & c2` : conjonction.
- `substitutions() -> dict` : substitutions issues des égalités, avec clôture transitive.
- `implies_zero(expr) -> bool | None` : l'expression s'annule-t-elle modulo les égalités ?
- `is_satisfied(values) -> bool` : la condition est-elle vraie pour ces valeurs ?
- Propriétés : `is_contradictory`, `is_trivial`, `is_generic`, `free_symbols`.
- `format_text()`, `format_latex()` : affichage (`str(c)` donne par exemple `b ≠ 0 et a = 1`).

#### `Branch[T]`
Branche de calcul : `condition: Condition`, `result: T`, `trace: Step`.

#### `CaseSplit[T]`
Partition disjointe de l'espace des paramètres.
- `branches: tuple[Branch[T], ...]`, `parameters: tuple[Symbol, ...]`.
- `at(**valeurs) -> T` : résultat (spécialisé) de la branche contenant le point.
- `generic() -> T` : résultat de la branche générique.
- `explain(level=None, fmt="auto") -> Explanation` : discussion de cas rédigée.

### 2.4 Hiérarchie des exceptions

```text
PedagopyError (Exception)
├── DimensionMismatchError    (ValueError)
├── InexactInputError         (ValueError)
├── InvalidAssumptionError    (ValueError)
├── SingularMatrixError       (ArithmeticError)
├── LinearDependenceError     (ArithmeticError)
├── RankDeficientError        (ArithmeticError)
├── UndecidableZeroError      (ArithmeticError)
├── UndefinedOperationError   (ArithmeticError)
├── CaseLimitError
├── LockedExerciseDataError   (PermissionError)
└── UnknownExerciseError      (LookupError)

PedagogicalWarning (UserWarning)
```

- `InvalidAssumptionError` : hypothèse non reconnue (inégalité d'ordre comme `"a > 0"`, syntaxe inconnue).
- `CaseLimitError` : discussion par cas arrêtée par `max_cases` ou `max_depth` (attributs `limit`, `value`, `reached`, `factors`, `condition`, `suggested_assumption`).
- `PedagogicalWarning` : avertissement didactique (Gauss-Jordan sur une matrice à paramètres plus grande que `config.max_generic_dim`).

---

## 3. Module `linalg_pedagopy.objects`

### 3.1 Classe `Vector`

Vecteur colonne immuable $n \times 1$ à coefficients exacts. Constructeur : `Vector(entries)`.

#### Propriétés
- `entries: tuple[sympy.Expr, ...]`, `size: int`, `shape: tuple[int, int]` (`(n, 1)`), `rows`, `cols`.
- Protocoles : `len(v)`, `v[i]`, itération, `==`.

#### Opérations
- `v + w`, `v - w`, `-v`, `c * v`, `v * c`, `v / c`.

#### Métriques
- `dot(other) -> Expr` : produit scalaire.
- `norm_sq() -> Expr`, `norm() -> Expr` : carré de la norme, norme.
- `rms() -> Expr`, `avg() -> Expr`, `std() -> Expr` : valeur RMS, moyenne, écart type.
- `demean() -> Vector` : vecteur centré.
- `distance(other) -> Expr` : distance euclidienne.
- `angle(other) -> Expr` : angle en radians.
- `correlation(other) -> Expr` : coefficient de corrélation.
- `is_zero(assumptions=None) -> bool | CaseSplit[bool]`.

#### Constructeurs et conversions
- `Vector.zeros(n)`, `Vector.ones(n)`, `Vector.unit(i, n)` (indice 0-based).
- `Vector.combination(vs, cs) -> Vector` : $\sum_k c_k v_k$.
- `to_sympy() -> sympy.Matrix`, `to_domain_matrix() -> DomainMatrix`, `subs(mapping) -> Vector`.

---

### 3.2 Classe `Matrix`

Matrice immuable $m \times n$ à coefficients exacts. Constructeur : `Matrix(rows)` (liste de lignes).

#### Propriétés
- `rows: int`, `cols: int`, `shape: tuple[int, int]`.
- `entries_grid: tuple[tuple[Expr, ...], ...]`, `flat_entries`.
- `T: Matrix` : transposée.
- Protocoles : `A[i, j]`, `==`.

#### Opérations
- `A + B`, `A - B`, `-A`, `c * A`, `A * c`, `A / c`, `A @ B`, `A @ v` (pas d'opérateur `**`).
- `matmul(other, *, view="entries")` : produit avec trace selon la vue (`"entries"`, `"rows"`, `"columns"`, `"outer"`).
- `gram() -> Matrix` : $A^T A$.
- `has_orthonormal_columns(assumptions=None) -> bool | CaseSplit[bool]`.

#### Accès
- `row(i) -> Vector`, `col(j) -> Vector`, `columns() -> tuple[Vector, ...]`, `rows_as_vectors() -> tuple[Vector, ...]`.
- `augment(right) -> Matrix` : matrice augmentée $[A \mid B]$.
- `to_sympy()`, `to_domain_matrix()`, `subs(mapping)`.

#### Algèbre et sous-espaces (avec discussion paramétrique)
- `rref(*, assumptions=None) -> Matrix | CaseSplit[Matrix]`.
- `rank(*, assumptions=None) -> int | CaseSplit[int]`.
- `nullspace(*, assumptions=None) -> tuple[Vector, ...] | CaseSplit[...]`.
- `inv(*, assumptions=None, strict=True) -> Matrix | None | CaseSplit[Matrix | None]` : lève `SingularMatrixError` si `strict=True` et la matrice peut être singulière ; avec des paramètres, le message donne le déterminant et les valeurs singulières.
- `solve(b, *, assumptions=None, strict=False)` : résolution de $A x = b$ par Gauss-Jordan.
- `det(*, method="auto", assumptions=None) -> Expr | CaseSplit[Expr]` : déterminant exact factorisé, via `Determinant` (voir § 4.6) ; une discussion par cas seulement avec `method="elimination"` sur une matrice à paramètres.

#### Constructeurs
- `Matrix.identity(n)`, `Matrix.zeros(m, n=None)`, `Matrix.ones(m, n=None)`, `Matrix.diag(diagonal)`.
- `Matrix.from_columns(columns)`, `Matrix.from_rows(rows)`.
- `Matrix.block(blocks)` : grille de blocs (matrices, vecteurs ou entiers).

---

### 3.3 Module `linalg_pedagopy.special` (matrices structurées)

Indices comptés à partir de 0 ; toutes les fonctions sont aussi importables depuis `linalg_pedagopy`.

- `difference_matrix(n)` (alias `matrice_differences`) : $(n-1) \times n$, $(Dx)_i = x_{i+1} - x_i$.
- `running_sum_matrix(n)` (alias `matrice_somme_cumulee`) : $n \times n$, sommes cumulées.
- `moving_average_matrix(n, k)` (alias `matrice_moyenne_glissante`) : $(n-k+1) \times n$.
- `vandermonde(points, degree=None)` : ligne $i$ = $(1, t_i, \dots, t_i^{d})$.
- `convolution_matrix(b, n)` (alias `matrice_convolution`) : Toeplitz $T(b)$, $T(b)a = b * a$.
- `convolution(a, b) -> Vector` : produit de convolution.
- `selection_matrix(indices, n)` (alias `matrice_selection`), `reversal_matrix(n)` (alias `matrice_renversement`).

---

## 4. Module `linalg_pedagopy.algorithms`

Chaque procédure s'exécute par `.run()`, qui renvoie un résultat (ou un `CaseSplit` de résultats en présence de paramètres). Tout résultat possède `trace: Step`, `explain(level=None, fmt="auto") -> Explanation` et `verify() -> Explanation`. `procedure.interactive(mode=...)` ouvre une `InteractiveSession`.

### 4.1 `GaussJordan`

```text
GaussJordan(A, b=None, *, pivot_strategy="simplest", reduction="simultaneous", strict=False,
            max_depth=None, max_cases=None, assumptions=None, compute_inverse=False)
```
- `pivot_strategy` : `"simplest"`, `"first"`, `"partial"` ou `"sparse"` (ligne la plus creuse).
- `reduction` : `"simultaneous"` (Gauss-Jordan) ou `"back_substitution"` (échelonnement puis remontée).
- `strict=True` : `SingularMatrixError` pour un système incompatible ou une matrice non inversible (`compute_inverse=True`).
- `.run()` → `GJResult | CaseSplit[GJResult]`.
- Champs de `GJResult` : `A`, `b`, `rref`, `augmented_rref`, `pivots`, `rank`, `free_vars`, `nullspace_basis`, `solution`, `inverse`.
- `solution` est l'un des `SolutionSet` :
  - `UniqueSolution(x)` ;
  - `AffineSolution(x0, basis, free_vars)`, avec `at_params(*t)` ;
  - `EmptySolution(row, witness, inconsistent_rows)`.

  Tous ont les propriétés `is_consistent`, `is_unique` et la méthode `subs(mapping)`.

### 4.2 `ForwardSubstitution` & `BackSubstitution`

```text
ForwardSubstitution(L, c, *, assumptions=None)
BackSubstitution(R, c, *, assumptions=None)
```
- `.run()` → `TriangularResult` (`x`, `A`, `c`).

### 4.3 `GramSchmidt`

```text
GramSchmidt(vectors, *, normalize="end", strict=False, assumptions=None)
```
- `vectors` : suite de vecteurs (ou de listes) ou `Matrix` (ses colonnes).
- `normalize` : `"end"` (calcul rationnel, normalisation finale) ou `"each"` (normalisation à chaque étape).
- `strict=True` : `LinearDependenceError` si la famille est liée.
- `.run()` → `GSResult | CaseSplit[GSResult]`.
- Champs de `GSResult` : `independent`, `vectors`, `orthogonal`, `orthonormal`, `r_tilde`, `d_sq`, `dependent_index`, `witness` (`DependenceWitness(index, q_tilde_coeffs, a_coeffs, expression)`) ; propriétés `Q`, `Q_tilde`.

### 4.4 `QR`

```text
QR(A, *, strict=False, assumptions=None)
```
- Factorisation par Gram-Schmidt (pas de variante Householder ou Givens).
- `.run()` → `QRResult` : `A`, `Q`, `R`, `Q_tilde`, `R_tilde`, `D_sq`, `d_sq`, `full_rank`, `witness`.

### 4.5 `LeastSquares`

```text
LeastSquares(A, b, *, method="rational_qr", assumptions=None)
```
- `method` : `"rational_qr"` (défaut), `"qr"` ou `"normal"`.
- `.run()` → `LSResult | CaseSplit[LSResult]` : `A`, `b`, `x_hat`, `y_hat`, `r_hat` ($A\hat x - b$), `residual_norm`, `residual_rms`, `method`, `full_rank`, `witness` ; propriétés `residual`, `pseudoinverse`.

### 4.6 `Determinant`

```text
Determinant(A, *, method="auto", assumptions=None)
```
- `A` : matrice carrée (sinon `DimensionMismatchError`).
- `method` : `"auto"` (Bareiss si la matrice contient des paramètres, élimination sinon), `"bareiss"`, `"elimination"` (sans dilatation), `"cofactors"` ($n \le 4$, sinon `PedagopyError`) ou `"sarrus"` ($n = 3$, sinon `DimensionMismatchError`).
- `.run()` → `DetResult`. Avec `"elimination"`, un pivot qui dépend d'un paramètre et peut s'annuler ouvre une discussion : le résultat est alors un `CaseSplit[DetResult]`. Les autres méthodes renvoient toujours un `DetResult` (le déterminant d'une matrice paramétrée est un polynôme en les paramètres).
- Champs de `DetResult` : `A`, `value` (forme factorisée), `method`, `factors` (couples `(facteur, multiplicité)`), `condition` (hypothèses et domaine de définition).
- `zeros(*, split=False)` : conditions d'annulation (`tuple[Condition, ...]`, disjonction) ; avec `split=True`, « inversible ? » sous forme de `bool` ou de `CaseSplit[bool]`.
- `verify()` : contrôle par un calcul indépendant (algorithme de Berkowitz).

---

## 5. Traçabilité et rendu

- `tracing(level=None)` : context manager ouvrant un `Tracer` (accessible par `as tr`, arbre `tr.tree`).
- `suspend_tracing()` : suspend l'enregistrement.
- `section(message_key, *, level=1, ...)`, `record(kind, message_key, *, level=1, ...)` : primitives d'enregistrement pour écrire de nouvelles procédures.
- `Step`, `StepKind`, `Highlight` : nœuds de l'arbre de trace.
- `Explanation` : `to_text(level=None)`, `to_latex(level=None)`, `to_markdown(level=None)`, `to_html(level=None, *, standalone=True)` (page complète par défaut), `to_table(level=None)`, `save(path, *, fmt=None)` ; rendu automatique dans Jupyter.
- `TraceTable` (`render.table`), renvoyé par `to_table()` : `to_html(standalone=False)`, `to_markdown()`, `to_latex(standalone=False)`, `sections` (une par branche d'une discussion et par algorithme), `layout` de chaque section (`"elimination"`, `"gram_schmidt"`, `"substitution"`), `rows` de chaque section (`kind`, `number`, `column`, `pivot`, `subject`, `detail`, `operation_latex`, `text`, `matrix`) ; affichage HTML automatique dans Jupyter.

---

## 6. Module `linalg_pedagopy.tuteur` (noms anglais : `tutor`)

Les fonctions et méthodes sont données sous leur nom français ; le nom anglais, entre parenthèses, reste disponible jusqu'à 0.4.0.0.

Sous-modules : `catalogue` (fiches, thèmes, glossaire, mode), `seance` (`ExerciseSession`), `validation` (`validate_sheet`), `verificateurs/` (un module par type de vérification), `registre` (registre des types), `indices`, `journal`, `labo`, `verrou`, `panneau`, `evaluation_sure` (interpréteur sûr des expressions des fiches et des saisies). Les anciens chemins `linalg_pedagopy.tutor.catalog`, `.verifiers`… réexportent les mêmes noms jusqu'à 0.4.0.0.

### 6.1 Catalogue

#### `catalogue(theme=None) -> ExerciseCatalog` (anglais : `catalog`)
Table des exercices (tuple de dictionnaires `numero`, `id`, `titre`, `theme`, `type`, `niveau`, `notions`), rendue en tableau Markdown dans JupyterLab et groupée par thème avec `print`. `theme` filtre sur une partie du nom du thème.

#### `themes() -> list[str]`
Les thèmes, dans l'ordre du cours (constante `THEMES`).

#### `lister_exercices(theme=None) -> list[str]` (anglais : `list_exercises`)
Identifiants des exercices dans l'ordre du catalogue.

#### `exercice(ex_id, *, journal_path=None) -> ExerciseSession` (anglais : `exercise`)
Ouvre une séance. `ex_id` est un identifiant (`"moyenne-glissante"`), un numéro (`16` ou `"16"`) ou un titre exact. Lève `UnknownExerciseError` (avec suggestions) si l'exercice n'existe pas.

#### `valider_fiche(ex_id) -> ValidationReport` (anglais : `validate_sheet`)
Valide une fiche (champs, métadonnées, numéro unique, vérificateur, jumeau, absence de fuite, contrôle croisé) sans écrire dans le journal. `ValidationReport` : `valide`, `cible_ok`, `jumeau_ok`, `indices_sans_fuite`, `source_ok` (métadonnées de catalogue), `cross_check_ok`, `erreurs` (noms anglais : `valid`, `target_ok`, `twin_ok`, `hints_leak_free`, `errors`).

#### `recharger_catalogue()` (anglais : `reload_catalog`)
Relit les fiches sur le disque.

#### `glossaire(term=None) -> str` (anglais : `glossary`)
Définition d'un terme (anglais ou français, recherche partielle) ; sans argument, la liste des 40 termes. Lève `KeyError` avec des suggestions si le terme est absent.

#### `mode(new_mode=None) -> str`
Lit ou fixe `config.tutor_mode` (`"etudiant"` ou `"enseignant"` ; `"student"` et `"teacher"` sont acceptés).

### 6.2 Classe `ExerciceSession` (anglais : `ExerciseSession`)

- Attributs : `id`, `numero`, `titre`, `theme`, `niveau`, `type`, `notions`, `texte` (énoncé brut), `donnees` (`LockedNamespace`), `journal` (`ExerciseJournal`), `predictions` (noms anglais : `number`, `title`, `level`, `text`, `data`).
- `enonce() -> MarkdownText` (anglais : `statement`) : titre, thème, type, niveau, énoncé et notions.
- `indice(level=None, *, niveau=None) -> MarkdownText` (anglais : `hint`) : palier suivant (1 à 4) ou relecture d'un palier débloqué ; récapitulatif quand tout est débloqué.
- `jumeau() -> TwinExercise` (anglais : `twin`) : exercice analogue résolu (`title`, `statement`, `solution_summary`, `explanation`).
- `predire(*args, **kwargs) -> MarkdownText` (anglais : `predict`) : enregistre une prédiction (obligatoire avant `labo()`).
- `labo() -> CounterexampleLab` (anglais : `lab`) ; `lab.tester(**instances) -> LabReport` (anglais : `test`) : `hypotheses_satisfied`, `results_by_part`, `found_counterexample`, `message`.
- `verifier(reponse) -> VerificationResult` (anglais : `verify`) : `valide`, `diagnostic`, `note_simplicite` (noms anglais : `valid`, `simplicity_note`). Une réponse de forme inattendue donne un diagnostic, jamais une exception.
- `bilan() -> MarkdownText` (anglais : `summary`) : bilan de la séance.
- `recommencer() -> MarkdownText` (anglais : `reset`) : efface la progression sur l'exercice.
- `panneau()` (anglais : `panel`) : panneau `ipywidgets` (ou `PanneauFallback`).
- `fiche_enseignant() -> TeacherSheet` (anglais : `teacher_sheet`) : fiche complète, mode enseignant uniquement (`PermissionError` sinon).

---

## 7. Modules `exercises`, `compare` et `plot`

- `linalg_pedagopy.exercises` : `generate_unimodular_matrix`, `generate_integer_rref_matrix`, `generate_rational_qr_matrix`, `generate_clean_least_squares`, `generate_parametric_system`, `cayley_orthogonal`, `generators` / `generateurs`, `TwinExercise` (24 générateurs, voir le guide 05), `InteractiveSession(procedure, *, mode="autonomous", mask_ratio=0.5)`, `check_row_operation`, `check_gram_schmidt_step`, `OperationFeedback` (voir [guide 05](05_pedagogical_exercises_and_sessions.md)).
- `linalg_pedagopy.compare` (extra `compare`, NumPy ; importer avec `from linalg_pedagopy.compare import …`, car `linalg_pedagopy.compare` désigne aussi la fonction `compare`) : `compare(procedure, inputs=None) -> ComparisonReport`, `build_lauchli_matrix(n=3, epsilon=1/10**8)`, `build_hilbert_matrix(n)`, `lauchli_gram_schmidt_experiment`, `lauchli_least_squares_experiment`, `hilbert_conditioning_experiment`, `explicit_inverse_vs_solve_experiment` (voir [guide 06](06_rendering_visualization_and_numerics.md)).
- `linalg_pedagopy.plot` (extra `plot`, Matplotlib) : `plot_linear_combination_2d`, `plot_orthogonal_projection_2d`, `plot_gram_schmidt_2d`, `plot_least_squares_fit`, `plot_least_squares_geometry_3d`.

---

## 8. Module `linalg_pedagopy.config`

`config` est un objet global (par contexte) dont les attributs sont :

| Attribut | Valeurs | Défaut |
| :--- | :--- | :--- |
| `float_policy` | `"rationalize"`, `"reject"`, `"keep"` | `"rationalize"` |
| `locale` | code de langue (seul `"fr"` est fourni) | `"fr"` |
| `default_trace_level` | `0` à `3` | `1` |
| `max_case_depth` | profondeur maximale de la discussion de cas | `3` |
| `max_cases` | nombre maximal de branches (au-delà : `CaseLimitError`) | `8` |
| `max_generic_dim` | taille au-delà de laquelle Gauss-Jordan sur une matrice à paramètres émet un `PedagogicalWarning` ; `None` : jamais | `4` |
| `factor_policy` | `"real_radicals"` : résultats d'une branche factorisés avec les radicaux $\sqrt d$ de sa condition ; `"rational"` : factorisation sur $\mathbb{Q}$ | `"real_radicals"` |
| `tutor_mode` | `"student"`, `"teacher"`, `"etudiant"`, `"enseignant"` | `"student"` |
| `hint_min_attempts` | tentatives minimales entre deux indices | `0` |
| `hint_min_delay_seconds` | délai minimal entre deux indices (s) | `0` |
| `journal_path` | chemin du journal du tuteur | `.linalg_pedagopy_journal.json` |

- `using_config(**overrides)` (= `config.override(...)`) : context manager de modification temporaire.
- `config.reset()` : restaure les valeurs par défaut ; `config.state` : instantané immuable de la configuration.
