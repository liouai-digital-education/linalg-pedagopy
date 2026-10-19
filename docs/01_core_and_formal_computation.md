# 01. Noyau formel et Calcul Symbolique Exact

Le module `linalg_pedagopy.core` constitue le socle mathématique fondamental du package. Il garantit la rigueur des calculs formels sur le corps des réels $\mathbb{R}$, empêche les erreurs de troncature numérique et gère de manière déterministe les discussions paramétriques.

---

## 1. Représentation des scalaires et coercition exacte

### 1.1 La fonction `to_exact`

En calcul formel didactique, manipuler des nombres à virgule flottante (`float`) conduit inévitablement à des artefacts déroutants pour l'étudiant (pivots non nuls valant `1e-16`, divisions par zéro masquées, etc.). 

La fonction [`to_exact`](src/linalg_pedagopy/core/field.py#L95-L140) convertit tout scalaire d'entrée en une expression symbolique exacte SymPy (`sympy.Expr`) selon la politique déclarée :

```python
from linalg_pedagopy import to_exact
import sympy as sp
from fractions import Fraction

# Entiers, fractions et chaînes de caractères
s1 = to_exact(3)           # sympy.Integer(3)
s2 = to_exact("2/3")       # sympy.Rational(2, 3)
s3 = to_exact(Fraction(5, 7)) # sympy.Rational(5, 7)

# Expressions algébriques et radicaux
s4 = to_exact("sqrt(2)")   # sympy.sqrt(2)
s5 = to_exact(sp.pi)       # sympy.pi
```

### 1.2 Politique de gestion des flottants (`float_policy`)

Le comportement face à l'introduction explicite d'un flottant standard (`float`) est régi par [`config.float_policy`](src/linalg_pedagopy/config.py#L43-L50) :

| Politique | Comportement | Cas d'usage |
| :--- | :--- | :--- |
| `"rationalize"` *(par défaut)* | Convertit automatiquement le flottant en fraction rationnelle approchée (`sp.Rational(str(x))`). | Saisie souple en TD ou console interactive (`0.25` devient `1/4`). |
| `"reject"` | Lève immédiatement une exception [`InexactInputError`](src/linalg_pedagopy/core/exceptions.py). | Contrôle d'examen ou mode d'exigence formelle stricte. |
| `"keep"` | Conserve le flottant SymPy (`sp.Float`). | Analyse des erreurs de troncature et comparaison avec le numérique. |

Exemple d'utilisation avec `using_config` :

```python
from linalg_pedagopy import to_exact, using_config, InexactInputError

# Par défaut : rationalisation
print(to_exact(0.1))  # 1/10

# Mode strict : rejet
with using_config(float_policy="reject"):
    try:
        to_exact(0.1)
    except InexactInputError as err:
        print(f"Entrée rejetée : {err}")
```

---

## 2. Déclaration et gestion des symboles réels (`symbols`)

### 2.1 Hypothèse `real=True` par défaut (Décision D1)

Dans les systèmes de calcul formel généralistes, un symbole non qualifié $a$ est supposé complexe ($a \in \mathbb{C}$), ce qui empêche de nombreuses simplifications élémentaires (par exemple $\sqrt{a^2} = |a|$ ou la factorisation de carrés).

Dans `linalg_pedagopy`, la fonction [`symbols`](src/linalg_pedagopy/core/field.py#L14-L43) munit systématiquement les symboles de l'hypothèse `real=True` :

```python
from linalg_pedagopy import symbols

# Déclaration de scalaires réels
a, b, m = symbols("a b m")
print(a.is_real)  # True

# Préservation d'hypothèses supplémentaires
x, y = symbols("x y", positive=True)
print(x.is_positive, x.is_real)  # True True
```

### 2.2 Préservation et correspondance des symboles

Lors des substitutions partielles ou complètes, la fonction [`match_symbol_substitutions`](src/linalg_pedagopy/core/field.py#L80-L92) fait correspondre les variables par leur nom textuel si nécessaire, évitant ainsi les incompatibilités entre symboles SymPy de mêmes noms mais créés dans des contextes distincts.

---

## 3. L'Oracle de nullité (`ZeroOracle`)

### 3.1 Pourquoi un oracle dédié ? (Décision D3)

En présence de paramètres symboliques, tester si un scalaire $v$ est nul (`v == 0`) ne peut pas être une simple opération booléenne :
- Si $v = a - 1$, la réponse dépend de la valeur de $a$.
- Si l'on répond aveuglément `False`, on risque de diviser par $a - 1$, rendant le pivotage invalide pour $a = 1$.
- Si l'on répond aveuglément `True`, on ignore le cas générique $a \neq 1$.

L'instance globale [`oracle`](src/linalg_pedagopy/core/zero.py#L249) évalue la nullité selon quatre verdicts :

```python
from linalg_pedagopy.core.zero import Verdict, oracle
from linalg_pedagopy import symbols

a, = symbols("a")

dec1 = oracle.decide(0)
print(dec1.verdict)  # Verdict.ZERO

dec2 = oracle.decide(3)
print(dec2.verdict)  # Verdict.NONZERO

dec3 = oracle.decide(a - 2)
print(dec3.verdict)  # Verdict.CONDITIONAL
print(dec3.factors)  # [a - 2]
```

### 3.2 Les 4 Verdicts

```mermaid
stateDiagram-v2
    [*] --> Evaluation
    Evaluation --> ZERO : Expression constante nulle
    Evaluation --> NONZERO : Expression constante non nulle
    Evaluation --> NONZERO : Symbole strictement positif / non nul
    Evaluation --> CONDITIONAL : Annulation pour certaines valeurs réelles
    Evaluation --> UNKNOWN : Indécidable sans hypothèse supplémentaire
```

1. **`Verdict.ZERO`** : L'expression se simplifie formellement en 0 de manière inconditionnelle.
2. **`Verdict.NONZERO`** : L'expression est inconditionnellement non nulle sur $\mathbb{R}$ (ex: $a^2 + 1$, $e^x$, ou constante non nulle).
3. **`Verdict.CONDITIONAL`** : L'expression peut s'annuler pour des valeurs réelles particulières des paramètres. L'oracle extrait les facteurs d'annulation (`dec.factors`).
4. **`Verdict.UNKNOWN`** : L'expression ne peut être décidée sans hypothèse explicite. L'appel à `oracle.is_zero(expr)` lèvera alors une [`UndecidableZeroError`](src/linalg_pedagopy/core/exceptions.py).

### 3.3 Traitement des radicaux paramétriques (`unrad`)

Les expressions contenant des racines carrées paramétriques (comme $\sqrt{1 - m^2}$ ou $\sqrt{a^2 + b^2}$) sont traitées via [`_extract_factors`](src/linalg_pedagopy/core/zero.py#L73-L143) :
1. L'oracle fait appel à `sympy.solvers.solvers.unrad` pour éliminer les radicaux de l'équation $f(m) = 0$.
2. Il résout la partie polynomiale sur $\mathbb{R}$.
3. **Filtrage des racines parasites** : Chaque racine candidate $r$ est réinjectée dans l'expression radicale initiale pour vérifier que $f(r) = 0$. Cela élimine les racines parasites introduites par l'élévation au carré de `unrad`.

---

## 4. Disjonction de cas paramétriques (`CaseSplit`)

### 4.1 La classe `Condition`

Une [`Condition`](src/linalg_pedagopy/core/cases.py#L29-L176) modélise l'ensemble des contraintes algébriques valables sur une branche de calcul :
- Des égalités formelles : $a = 1$, $b = 0$.
- Des inégalités strictes : $a \neq 1$, $a \neq -2$.

```python
from linalg_pedagopy.core.cases import Condition, Equality, Inequality
from linalg_pedagopy import symbols

a, b = symbols("a b")

c1 = Condition.from_equalities(Equality(a, 1))
c2 = Condition.from_inequalities(Inequality(b, 0))
c3 = c1.and_with(c2)
print(c3)  # {a = 1} ∧ {b ≠ 0}
```

### 4.2 Clôture transitive et détection de contradictions

La classe `Condition` implémente deux propriétés critiques :
1. **Clôture transitive des substitutions** ([`_compute_transitive_substitutions`](src/linalg_pedagopy/core/cases.py#L14-L26)) :  
   Si la condition contient $a = b$ et $b = 3$, la substitution résout automatiquement $a \mapsto 3$.
2. **Détection de contradictions et élagage des tautologies** ([`is_contradictory`](src/linalg_pedagopy/core/cases.py#L82-L97)) :  
   Si une branche tente de combiner $a = 1$ et $a \neq 1$, `c.is_contradictory()` renvoie `True` et la branche impossible est immédiatement abandonnée.
3. **Implication de nullité modulo la branche** ([`implies_zero`](src/linalg_pedagopy/core/cases.py#L99-L107)) :  
   Vérifie si une expression polynomiale s'annule en tenant compte des égalités déjà posées sur la branche.

### 4.3 Structure d'un `CaseSplit`

Un [`CaseSplit[T]`](src/linalg_pedagopy/core/cases.py#L194-L320) regroupe un ensemble fini de branches disjointes [`Branch[T]`](src/linalg_pedagopy/core/cases.py#L179-L191) couvrant la totalité de l'espace des paramètres :

```mermaid
flowchart TD
    CS["CaseSplit (Système avec paramètre a)"]
    CS --> B1["Branche générique : a ≠ 1 ∧ a ≠ -2<br/>Solution unique"]
    CS --> B2["Branche particulière : a = 1<br/>Infinité de solutions (droite affine)"]
    CS --> B3["Branche particulière : a = -2<br/>Système incompatible (ensemble vide)"]
```

### 4.4 Partitionnement disjoint par préfixes d'inégalités

Lorsqu'un pivot présente plusieurs facteurs d'annulation $(f_1, f_2, \dots, f_k)$, l'algorithme génère des branches mutuellement disjointes selon la méthode des préfixes d'inégalités :
- Branche 1 : $f_1 = 0$
- Branche 2 : $f_1 \neq 0 \land f_2 = 0$
- $\dots$
- Branche $k+1$ (générique) : $\bigwedge_{i=1}^k f_i \neq 0$

Cette construction garantit que chaque point de l'espace des paramètres appartient à une et une seule branche.

### 4.5 Commutation de la spécialisation (`at`)

Un résultat `CaseSplit` respecte le principe de commutation fondamentale :
$$\left( \text{Algorithme}(A(p), b(p)) \right) \Big|_{p = p_0} = \text{Algorithme}\left( A(p_0), b(p_0) \right)$$

On évalue un `CaseSplit` en un point donné grâce à la méthode [`at`](src/linalg_pedagopy/core/cases.py#L273-L302) :

```python
from linalg_pedagopy import Matrix, Vector, symbols, GaussJordan

a, = symbols("a")
A = Matrix([[1, a], [a, 1]])
b = Vector([1, 1])

res = GaussJordan(A, b).run()
# Spécialisation en a = 1
spec_1 = res.at(a=1)
print(spec_1)  # AffineSolution

# Spécialisation en a = 0 (cas générique)
spec_0 = res.at(a=0)
print(spec_0)  # UniqueSolution (x = [1, 1])
```
