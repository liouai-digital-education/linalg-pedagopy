# 07. Référence complète de l'API

Ce document constitue la référence exhaustive de l'ensemble des modules, classes, fonctions, constantes et exceptions du package `linalg_pedagopy` v3.0.

---

## 1. Table de correspondance bilingue (Anglais / Français)

Le package privilégie une **nomenclature primaire anglaise** tout en garantissant des **alias français complets** :

| API Primaire (Anglais) | Alias Français | Module d'origine |
| :--- | :--- | :--- |
| `tutor.exercise(id)` | `tuteur.exercice(id)` | `linalg_pedagopy.tutor` |
| `tutor.list_exercises()` | `tuteur.lister_exercices()` | `linalg_pedagopy.tutor` |
| `tutor.validate_sheet(id)` | `tuteur.valider_fiche(id)` | `linalg_pedagopy.tutor` |
| `tutor.glossary()` | `tuteur.glossaire()` | `linalg_pedagopy.tutor` |
| `ex.statement()` | `ex.enonce()` | `ExerciseSession` |
| `ex.hint()` | `ex.indice()` | `ExerciseSession` |
| `ex.twin()` | `ex.jumeau()` | `ExerciseSession` |
| `ex.predict(...)` | `ex.predire(...)` | `ExerciseSession` |
| `ex.lab()` | `ex.labo()` | `ExerciseSession` |
| `ex.verify(...)` | `ex.verifier(...)` | `ExerciseSession` |
| `ex.summary()` | `ex.resume()` | `ExerciseSession` |
| `ex.teacher_sheet()` | `ex.fiche_enseignant()` | `ExerciseSession` |
| `generators.difference_matrix(n)` | `generateurs.matrice_differences(n)` | `linalg_pedagopy.exercises.generators` |
| `generators.running_sum_matrix(n)` | `generateurs.matrice_somme_cumulee(n)` | `linalg_pedagopy.exercises.generators` |
| `generators.moving_average(n, k)` | `generateurs.moyenne_mobile(n, k)` | `linalg_pedagopy.exercises.generators` |
| `generators.gram_matrix(V)` | `generateurs.matrice_gram(V)` | `linalg_pedagopy.exercises.generators` |

---

## 2. Module `linalg_pedagopy.core`

### 2.1 Fonctions scalaires et symboliques

#### `to_exact(value: Any) -> sympy.Expr`
Convertit un entier, une fraction, une chaîne de caractères ou un flottant en expression symbolique exacte selon `config.float_policy`.

#### `symbols(names: str | Sequence[str], **assumptions: Any) -> tuple[sympy.Symbol, ...] | sympy.Symbol`
Instancie un ou plusieurs symboles SymPy en leur attribuant par défaut l'hypothèse fondamentale `real=True`.

#### `match_symbol_substitutions(target_expr: Any, subs: Mapping[Any, Any]) -> dict[sympy.Symbol, Any]`
Fait correspondre les symboles d'un dictionnaire de substitution par leur nom textuel pour garantir l'indépendance de contexte.

### 2.2 Oracle de nullité (`ZeroOracle`)

#### `Verdict (Enum)`
- `Verdict.ZERO` : Nullité formelle certaine.
- `Verdict.NONZERO` : Non-nullité formelle certaine.
- `Verdict.CONDITIONAL` : Nullité dépendante des valeurs de paramètres réels.
- `Verdict.UNKNOWN` : Non décidable sans hypothèse supplémentaire.

#### `ZeroDecision (Dataclass)`
- `verdict: Verdict` : Résultat de l'analyse.
- `factors: list[sympy.Expr]` : Facteurs d'annulation extraits en cas de verdict conditionnel.

#### `oracle.decide(expr: Any, assumptions: Condition | None = None) -> ZeroDecision`
Analyse la nullité d'une expression formelle et simplifie les radicaux par `unrad`.

#### `oracle.is_zero(expr: Any, assumptions: Condition | None = None) -> bool`
Renvoie `True` si l'expression est nulle, `False` si non nulle. Lève [`UndecidableZeroError`](#24-hiérarchie-des-exceptions) si le verdict est conditionnel ou inconnu.

### 2.3 Disjonction de cas (`Condition`, `CaseSplit`)

#### `Equality(lhs: Expr, rhs: Expr)` / `Inequality(lhs: Expr, rhs: Expr)`
Représentations immuables de contraintes formelles $f(p) = 0$ ou $f(p) \neq 0$.

#### `Condition`
Ensemble cohérent d'égalités et d'inégalités.
- `and_with(other: Condition) -> Condition` : Conjonction logique avec élagage automatique des tautologies.
- `is_contradictory() -> bool` : Détecte les contradictions strictes (ex: $a = 1 \land a \neq 1$).
- `implies_zero(expr: Expr) -> bool` : Déduit si une expression s'annule modulo les égalités de la condition.
- `substitutions: dict[Symbol, Expr]` : Dictionnaire des égalités avec clôture transitive résolue.

#### `Branch[T]`
Branche de calcul associant une `condition: Condition`, un résultat `result: T` et une trace `trace: Step`.

#### `CaseSplit[T]`
Partition disjointe de l'espace des paramètres regroupant un tuple de `branches: tuple[Branch[T], ...]`.
- `at(**parameter_values) -> T` : Évalue et renvoie le résultat de la branche correspondant au point spécifié.

### 2.4 Hiérarchie des Exceptions

```
PedagopyError (Exception de base)
├── DimensionMismatchError
├── SingularMatrixError
├── IncompatibleSystemError
├── UndecidableZeroError
├── InexactInputError
├── LinearDependenceError
├── RankDeficientError
├── UndefinedOperationError
└── tutor / tuteur
    ├── LockedExerciseDataError
    ├── CheatAttemptError
    ├── ExerciseNotFoundError
    └── VerificationError
```

---

## 3. Module `linalg_pedagopy.objects`

### 3.1 Classe `Vector`

Vecteur colonne immuable $n \times 1$.

#### Attributs et Propriétés
- `size: int` : Nombre de composantes $n$.
- `shape: tuple[int, int]` : Toujours `(n, 1)`.
- `entries: tuple[sympy.Expr, ...]` : Composantes exactes.
- `is_zero: bool` : Teste si le vecteur est nul.

#### Métriques VMLS
- `dot(other: Vector) -> sympy.Expr` : Produit scalaire $\langle v, w \rangle$ (alias opérateur `@`).
- `norm() -> sympy.Expr` : Norme euclidienne exacte $\|v\|$.
- `norm_sq() -> sympy.Expr` : Carré de la norme $\|v\|^2$.
- `unit_vector() -> Vector` : Vecteur normalisé $\frac{v}{\|v\|}$.
- `dist(other: Vector) -> sympy.Expr` : Distance euclidienne $\|v - w\|$.
- `rms() -> sympy.Expr` : Valeur efficace $\frac{\|v\|}{\sqrt{n}}$.
- `mean() -> sympy.Expr` : Moyenne arithmétique.
- `std() -> sympy.Expr` : Écart-type.
- `angle(other: Vector) -> sympy.Expr` : Angle non orienté en radians.
- `correlation(other: Vector) -> sympy.Expr` : Coefficient de corrélation.
- `project_onto(other: Vector) -> Vector` : Projection orthogonale sur $\text{Vect}(w)$.
- `orthogonal_complement(other: Vector) -> Vector` : Composante orthogonale $v - \text{proj}_w(v)$.

#### Usines et Utilitaires
- `Vector.zeros(n: int) -> Vector`
- `Vector.ones(n: int) -> Vector`
- `Vector.unit(index: int, n: int) -> Vector`
- `Vector.block(vectors: Sequence[Vector]) -> Vector`
- `to_matrix() -> Matrix`
- `to_sympy() -> sympy.Matrix`
- `subs(*args, **kwargs) -> Vector`

---

### 3.2 Classe `Matrix`

Matrice immuable $m \times n$.

#### Attributs et Propriétés
- `nrows: int` : Nombre de lignes $m$.
- `ncols: int` : Nombre de colonnes $n$.
- `shape: tuple[int, int]` : Dimensions `(m, n)`.
- `is_square: bool` : `nrows == ncols`.
- `is_symmetric: bool` : $A = A^T$.
- `is_orthogonal: bool` : $A^T A = I$.
- `trace() -> sympy.Expr` : Somme des éléments diagonaux.
- `det() -> sympy.Expr` : Déterminant exact.
- `T: Matrix` : Matrice transposée $A^T$.

#### Algèbre et Sous-espaces
- `inv(strict: bool = True) -> Matrix | CaseSplit[Matrix]` : Inverse formelle par pivot de Gauss.
- `rref(assumptions: Any = None) -> tuple[Matrix, tuple[int, ...]]` : Forme échelonnée réduite et indices des pivots.
- `rank(assumptions: Any = None) -> int | CaseSplit[int]` : Rang formel.
- `nullspace(assumptions: Any = None) -> tuple[Vector, ...]` : Base du noyau ($\text{Ker } A$).
- `col_space() -> tuple[Vector, ...]` : Base de l'espace des colonnes ($\text{Im } A$).
- `row_space() -> tuple[Vector, ...]` : Base de l'espace des lignes.

#### Usines
- `Matrix.identity(n: int) -> Matrix`
- `Matrix.zeros(m: int, n: int) -> Matrix`
- `Matrix.ones(m: int, n: int) -> Matrix`
- `Matrix.diagonal(entries: Sequence[Any]) -> Matrix`
- `Matrix.from_columns(columns: Sequence[Vector]) -> Matrix`
- `Matrix.from_rows(rows: Sequence[Vector | Sequence[Any]]) -> Matrix`
- `Matrix.block(blocks: Sequence[Sequence[Matrix]]) -> Matrix`

---

## 4. Module `linalg_pedagopy.algorithms`

### 4.1 `GaussJordan`

```python
GaussJordan(A: Matrix, b: Vector | Matrix | None = None, *, assumptions: Condition | None = None, strict: bool = True, compute_inverse: bool = False)
```
- Méthode `.run()` -> `GJResult | CaseSplit[GJResult]`.
- Propriétés de `GJResult` : `solution` (`UniqueSolution`, `AffineSolution`, `EmptySolution`), `rref_matrix`, `pivots`, `inverse`, `trace`, `explain()`.

### 4.2 `ForwardSubstitution` & `BackSubstitution`

```python
ForwardSubstitution(L: Matrix, b: Vector)
BackSubstitution(U: Matrix, b: Vector)
```
- Méthode `.run()` -> `TriangularResult`.
- Propriétés : `x: Vector`, `trace: Step`, `explain()`.

### 4.3 `GramSchmidt`

```python
GramSchmidt(vectors: Sequence[Vector], *, assumptions: Condition | None = None, normalize: bool = True)
```
- Méthode `.run()` -> `GSResult | CaseSplit[GSResult]`.
- Propriétés de `GSResult` : `orthogonal: tuple[Vector, ...]`, `orthonormal: tuple[Vector, ...]`, `norms: tuple[sympy.Expr, ...]`, `trace`, `explain()`.

### 4.4 `QR`

```python
QR(A: Matrix, *, method: Literal["gram_schmidt", "householder", "givens"] = "gram_schmidt")
```
- Méthode `.run()` -> `QRResult`.
- Propriétés : `Q: Matrix`, `R: Matrix`, `trace`, `explain()`.

### 4.5 `LeastSquares`

```python
LeastSquares(A: Matrix, b: Vector, *, method: Literal["qr", "normal_equations"] = "qr")
```
- Méthode `.run()` -> `LSResult | CaseSplit[LSResult]`.
- Propriétés de `LSResult` : `x_hat: Vector`, `y_hat: Vector`, `r_hat: Vector`, `residual_norm_sq: sympy.Expr`, `verify() -> bool`, `trace`, `explain()`.

---

## 5. Module `linalg_pedagopy.tutor` / `tuteur`

### 5.1 Fonctions du catalogue

#### `exercise(id: str) -> ExerciseSession` (alias `exercice`)
Charge une séance de travail sur la fiche VMLS d'identifiant `id`.

#### `list_exercises(category: str | None = None) -> list[dict[str, Any]]` (alias `lister_exercices`)
Renvoie la liste des 35 fiches disponibles avec leurs métadonnées.

#### `validate_sheet(sheet_id: str) -> ValidationReport` (alias `valider_fiche`)
Effectue la validation croisée d'intégrité de la fiche sans polluer le journal étudiant.

#### `glossary(term: str | None = None) -> dict[str, str] | str` (alias `glossaire`)
Consulte le lexique des définitions mathématiques VMLS.

### 5.2 Classe `ExerciseSession`

- `statement() -> str` : Énoncé complet.
- `hint() -> str` : Débloque le niveau d'indice suivant (1 à 4).
- `twin() -> TwinExercise` : Exercice jumeau résolu.
- `predict(**kwargs) -> str` : Validation d'étape intermédiaire.
- `lab() -> CounterexampleLab` : Laboratoire de tests de conjectures.
- `verify(answer: Any) -> VerificationResult` : Validation de la solution.
- `summary() -> dict[str, Any]` : Bilan de la session de travail.
- `panel() -> Any` : Panneau graphique interactif JupyterLab (`ipywidgets`).
- `teacher_sheet() -> TeacherSheet` : Solution complète réservée au mode enseignant.

---

## 6. Module `linalg_pedagopy.config`

- `config.float_policy: Literal["rationalize", "reject", "keep"]`
- `config.locale: str` (`"fr"` ou `"en"`)
- `config.default_trace_level: int` (`0` à `3`)
- `config.tutor_mode: Literal["student", "teacher"]`
- `config.journal_path: Path`
- `using_config(**overrides)` : Context manager pour modification temporaire.
