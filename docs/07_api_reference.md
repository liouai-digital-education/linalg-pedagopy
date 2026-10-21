# 07. Référence complète de l'API

Ce document constitue la référence des modules, classes, fonctions et exceptions publics du package `linalg_pedagopy`. Les signatures sont celles du code source (`src/linalg_pedagopy`).

Tous les noms ci-dessous sont importables depuis `linalg_pedagopy` (sauf mention d'un sous-module).

---

## 1. Table de correspondance bilingue (Anglais / Français)

Le package privilégie une **nomenclature primaire anglaise** tout en garantissant des **alias français** :

| API Primaire (Anglais) | Alias Français | Module d'origine |
| :--- | :--- | :--- |
| `tutor` | `tuteur` | `linalg_pedagopy` |
| `tutor.catalog(theme=None)` | `tuteur.catalogue(theme=None)` | `linalg_pedagopy.tutor` |
| `tutor.themes()` | `tuteur.themes()` | `linalg_pedagopy.tutor` |
| `tutor.reload_catalog()` | `tuteur.recharger_catalogue()` | `linalg_pedagopy.tutor` |
| `tutor.exercise(id)` | `tuteur.exercice(id)` | `linalg_pedagopy.tutor` |
| `tutor.list_exercises()` | `tuteur.lister_exercices()` | `linalg_pedagopy.tutor` |
| `tutor.validate_sheet(id)` | `tuteur.valider_fiche(id)` | `linalg_pedagopy.tutor` |
| `tutor.glossary(term)` | `tuteur.glossaire(term)` | `linalg_pedagopy.tutor` |
| `tutor.mode("teacher")` | `tuteur.mode("enseignant")` | `linalg_pedagopy.tutor` |
| `tutor.build_panel(ex)` | `tuteur.build_panneau(ex)` | `linalg_pedagopy.tutor` |
| `tutor.verify_matrix(...)`, `verify_value(...)`… | `tuteur.verifier_matrice(...)`, `verifier_valeur(...)`… | `linalg_pedagopy.tutor` |
| `ExerciseSession` | `ExerciceSession` | `linalg_pedagopy.tutor` |
| `ex.statement()` | `ex.enonce()` | `ExerciseSession` |
| `ex.data` | `ex.donnees` | `ExerciseSession` |
| `ex.hint(level=None)` | `ex.indice(niveau=None)` | `ExerciseSession` |
| `ex.twin()` | `ex.jumeau()` | `ExerciseSession` |
| `ex.predict(...)` | `ex.predire(...)` | `ExerciseSession` |
| `ex.lab()` | `ex.labo()` | `ExerciseSession` |
| `ex.verify(...)` | `ex.verifier(...)` | `ExerciseSession` |
| `ex.summary()` | `ex.bilan()` | `ExerciseSession` |
| `ex.reset()` | `ex.recommencer()` | `ExerciseSession` |
| `ex.title`, `ex.number`, `ex.level` | `ex.titre`, `ex.numero`, `ex.niveau` | `ExerciseSession` |
| `ex.panel()` | `ex.panneau()` | `ExerciseSession` |
| `ex.teacher_sheet()` | `ex.fiche_enseignant()` | `ExerciseSession` |
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
Fait correspondre les clés d'un dictionnaire de substitution (symboles ou noms) aux symboles libres, par leur nom.

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
├── SingularMatrixError       (ArithmeticError)
├── LinearDependenceError     (ArithmeticError)
├── RankDeficientError        (ArithmeticError)
├── UndecidableZeroError      (ArithmeticError)
├── UndefinedOperationError   (ArithmeticError)
├── LockedExerciseDataError   (PermissionError)
└── UnknownExerciseError      (LookupError)
```

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
- `det(*, method="auto", assumptions=None) -> Expr` : déterminant exact factorisé, via `Determinant` (voir § 4.6).

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
GaussJordan(A, b=None, *, pivot_strategy="simplest", strict=False, max_depth=None,
            max_cases=None, assumptions=None, compute_inverse=False)
```
- `pivot_strategy` : `"simplest"`, `"first"` ou `"partial"`.
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
- `method` : `"auto"` (Bareiss si la matrice contient des paramètres, élimination sinon), `"bareiss"`, `"elimination"` (sans dilatation ; `PedagopyError` sur un pivot conditionnel), `"cofactors"` ($n \le 4$, sinon `PedagopyError`) ou `"sarrus"` ($n = 3$, sinon `DimensionMismatchError`).
- `.run()` → `DetResult` (jamais de `CaseSplit` : le déterminant d'une matrice paramétrée est un polynôme en les paramètres).
- Champs de `DetResult` : `A`, `value` (forme factorisée), `method`, `factors` (couples `(facteur, multiplicité)`), `condition` (hypothèses et domaine de définition).
- `zeros(*, split=False)` : conditions d'annulation (`tuple[Condition, ...]`, disjonction) ; avec `split=True`, « inversible ? » sous forme de `bool` ou de `CaseSplit[bool]`.
- `verify()` : contrôle par un calcul indépendant (algorithme de Berkowitz).

---

## 5. Traçabilité et rendu

- `tracing(level=None)` : context manager ouvrant un `Tracer` (accessible par `as tr`, arbre `tr.tree`).
- `suspend_tracing()` : suspend l'enregistrement.
- `section(message_key, *, level=1, ...)`, `record(kind, message_key, *, level=1, ...)` : primitives d'enregistrement pour écrire de nouvelles procédures.
- `Step`, `StepKind`, `Highlight` : nœuds de l'arbre de trace.
- `Explanation` : `to_text(level=None)`, `to_latex(level=None)`, `to_markdown(level=None)`, `to_html(level=None)`, `save(path, *, fmt=None)` ; rendu automatique dans Jupyter.

---

## 6. Module `linalg_pedagopy.tutor` / `tuteur`

### 6.1 Catalogue

#### `catalog(theme=None) -> ExerciseCatalog` (alias `catalogue`)
Table des exercices (tuple de dictionnaires `numero`, `id`, `titre`, `theme`, `type`, `niveau`, `notions`), rendue en tableau Markdown dans JupyterLab et groupée par thème avec `print`. `theme` filtre sur une partie du nom du thème.

#### `themes() -> list[str]`
Les thèmes, dans l'ordre du cours (constante `THEMES`).

#### `list_exercises(theme=None) -> list[str]` (alias `lister_exercices`)
Identifiants des exercices dans l'ordre du catalogue.

#### `exercise(ref, *, journal_path=None) -> ExerciseSession` (alias `exercice`)
Ouvre une séance. `ref` est un identifiant (`"moyenne-glissante"`), un numéro (`16` ou `"16"`) ou un titre exact. Lève `UnknownExerciseError` (avec suggestions) si l'exercice n'existe pas.

#### `validate_sheet(ref) -> ValidationReport` (alias `valider_fiche`)
Valide une fiche (champs, métadonnées, numéro unique, vérificateur, jumeau, absence de fuite, contrôle croisé) sans écrire dans le journal. `ValidationReport` : `valid`, `target_ok`, `twin_ok`, `hints_leak_free`, `source_ok` (métadonnées de catalogue), `cross_check_ok`, `errors` (alias `valide`, `cible_ok`, `jumeau_ok`, `indices_sans_fuite`, `erreurs`).

#### `reload_catalog()` (alias `recharger_catalogue`)
Relit les fiches sur le disque.

#### `glossary(term=None) -> str` (alias `glossaire`)
Définition d'un terme (anglais ou français, recherche partielle) ; sans argument, la liste des 40 termes. Lève `KeyError` avec des suggestions si le terme est absent.

#### `mode(new_mode=None) -> str`
Lit ou fixe `config.tutor_mode` (`"student"`, `"teacher"`, `"etudiant"`, `"enseignant"`).

### 6.2 Classe `ExerciseSession` (alias `ExerciceSession`)

- Attributs : `id`, `number`/`numero`, `title`/`titre`, `theme`, `level`/`niveau`, `type`, `notions`, `text`/`texte` (énoncé brut), `data`/`donnees` (`LockedNamespace`), `journal` (`ExerciseJournal`), `predictions`.
- `statement() -> MarkdownText` (alias `enonce`) : titre, thème, type, niveau, énoncé et notions.
- `hint(level=None, *, niveau=None) -> MarkdownText` (alias `indice`) : palier suivant (1 à 4) ou relecture d'un palier débloqué ; récapitulatif quand tout est débloqué.
- `twin() -> TwinExercise` (alias `jumeau`) : exercice analogue résolu (`title`, `statement`, `solution_summary`, `explanation`).
- `predict(*args, **kwargs) -> MarkdownText` (alias `predire`) : enregistre une prédiction (obligatoire avant `lab()`).
- `lab() -> CounterexampleLab` (alias `labo`) ; `lab.test(**instances) -> LabReport` (`hypotheses_satisfied`, `results_by_part`, `found_counterexample`, `message`).
- `verify(response) -> VerificationResult` (alias `verifier`) : `valid`, `diagnostic`, `simplicity_note` (alias `valide`, `note_simplicite`). Une réponse de forme inattendue donne un diagnostic, jamais une exception.
- `summary() -> MarkdownText` (alias `bilan`) : bilan de la séance.
- `reset() -> MarkdownText` (alias `recommencer`) : efface la progression sur l'exercice.
- `panel()` (alias `panneau`) : panneau `ipywidgets` (ou `PanelFallback`).
- `teacher_sheet() -> TeacherSheet` (alias `fiche_enseignant`) : fiche complète, mode enseignant uniquement (`PermissionError` sinon).

---

## 7. Modules `exercises`, `compare` et `plot`

- `linalg_pedagopy.exercises` : `generate_unimodular_matrix`, `generate_integer_rref_matrix`, `generate_rational_qr_matrix`, `generate_clean_least_squares`, `generate_parametric_system`, `cayley_orthogonal`, `generators` / `generateurs`, `TwinExercise` (20 générateurs, voir le guide 05), `InteractiveSession(procedure, *, mode="autonomous", mask_ratio=0.5)`, `check_row_operation`, `check_gram_schmidt_step`, `OperationFeedback` (voir [guide 05](05_pedagogical_exercises_and_sessions.md)).
- `linalg_pedagopy.compare` (extra `compare`, NumPy) : `compare(procedure, inputs=None) -> ComparisonReport`, `build_lauchli_matrix(n=3, epsilon=1/10**8)`, `build_hilbert_matrix(n)`, `lauchli_gram_schmidt_experiment`, `lauchli_least_squares_experiment`, `hilbert_conditioning_experiment`, `explicit_inverse_vs_solve_experiment` (voir [guide 06](06_rendering_visualization_and_numerics.md)).
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
| `max_cases` | nombre maximal de branches | `8` |
| `factor_policy` | `"real_radicals"` : résultats d'une branche factorisés avec les radicaux $\sqrt d$ de sa condition ; `"rational"` : factorisation sur $\mathbb{Q}$ | `"real_radicals"` |
| `tutor_mode` | `"student"`, `"teacher"`, `"etudiant"`, `"enseignant"` | `"student"` |
| `hint_min_attempts` | tentatives minimales entre deux indices | `0` |
| `hint_min_delay_seconds` | délai minimal entre deux indices (s) | `0` |
| `journal_path` | chemin du journal du tuteur | `.linalg_pedagopy_journal.json` |

- `using_config(**overrides)` (= `config.override(...)`) : context manager de modification temporaire.
- `config.reset()` : restaure les valeurs par défaut ; `config.state` : instantané immuable de la configuration.
