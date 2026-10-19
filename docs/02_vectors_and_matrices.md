# 02. Vecteurs, Matrices et Métriques VMLS

Les classes [`Vector`](src/linalg_pedagopy/objects/vector.py#L31-L450) et [`Matrix`](src/linalg_pedagopy/objects/matrix.py#L35-L750) incarnent les structures de données fondamentales de `linalg_pedagopy`.

Conformément à la philosophie du package :
- **Immutabilité absolue** : Toute opération renvoie une nouvelle instance. Aucune modification en place n'est autorisée.
- **Exactitude symbolique** : Les coefficients sont convertis en expressions SymPy exactes (`sp.Expr`).
- **Protection anti-triche** : Les constructeurs rejettent les proxys verrouillés du tuteur pour empêcher les contournements.

---

## 1. La classe `Vector`

Un `Vector` représente un vecteur colonne de $\mathbb{R}^n$ (de dimension formelle $n \times 1$).

### 1.1 Initialisation et constructeurs d'usine

```python
from linalg_pedagopy import Vector
import sympy as sp
from fractions import Fraction

# Initialisation par une séquence de scalaires exacts
v = Vector([1, "2/3", Fraction(4, 5), sp.sqrt(3)])
print(v)          # (1, 2/3, 4/5, sqrt(3))
print(v.size)     # 4
print(v.shape)    # (4, 1)

# Constructeurs d'usine remarquables
z = Vector.zeros(3)          # Vecteur nul (0, 0, 0)
u = Vector.ones(4)           # Vecteur unitaire tout à 1 (1, 1, 1, 1)
e2 = Vector.unit(1, 4)       # 2e vecteur de la base canonique e₂ = (0, 1, 0, 0) (indice 0-based)
```

### 1.2 Opérations algébriques

```python
v1 = Vector([1, 2, 3])
v2 = Vector([4, 5, 6])

# Addition et soustraction
w1 = v1 + v2       # (5, 7, 9)
w2 = v1 - v2       # (-3, -3, -3)

# Multiplication scalaire (gauche et droite)
w3 = 3 * v1        # (3, 6, 9)
w4 = v1 * "1/2"    # (1/2, 1, 3/2)

# Négation
w5 = -v1           # (-1, -2, -3)
```

### 1.3 Métriques et géométrie VMLS

`linalg_pedagopy` implémente l'ensemble des métriques géométriques introduites dans les chapitres 1 à 3 de *VMLS* :

| Méthode | Définition Mathématique | Description VMLS |
| :--- | :--- | :--- |
| `v.dot(w)` ou `v @ w` | $\langle v, w \rangle = \sum_{i=1}^n v_i w_i$ | Produit scalaire standard. |
| `v.norm_sq()` | $\|v\|^2 = \sum_{i=1}^n v_i^2$ | Carré de la norme euclidienne (rationnel si $v \in \mathbb{Q}^n$). |
| `v.norm()` | $\|v\| = \sqrt{\langle v, v \rangle}$ | Norme euclidienne exacte. |
| `v.unit_vector()` | $\frac{v}{\|v\|}$ | Vecteur normalisé (direction). |
| `v.dist(w)` | $\|v - w\|$ | Distance euclidienne entre $v$ et $w$. |
| `v.rms()` | $\text{rms}(v) = \frac{\|v\|}{\sqrt{n}}$ | Valeur efficace (*Root-Mean-Square*). |
| `v.mean()` | $\bar{v} = \frac{1}{n} \sum_{i=1}^n v_i$ | Moyenne arithmétique des coefficients. |
| `v.std()` | $\sqrt{\frac{1}{n} \sum (v_i - \bar{v})^2}$ | Écart-type (écart quadratique moyen à la moyenne). |
| `v.angle(w)` | $\theta = \arccos\left(\frac{\langle v, w \rangle}{\|v\| \|w\|}\right)$ | Angle non orienté en radians. |
| `v.correlation(w)` | $\rho = \frac{\langle v - \bar{v}, w - \bar{w} \rangle}{\|v - \bar{v}\| \|w - \bar{w}\|}$ | Coefficient de corrélation de Pearson. |
| `v.project_onto(w)` | $\frac{\langle v, w \rangle}{\|w\|^2} w$ | Projection orthogonale de $v$ sur la droite $\text{Vect}(w)$. |
| `v.orthogonal_complement(w)` | $v - \text{proj}_w(v)$ | Composante orthogonale de $v$ par rapport à $w$. |

Exemple :

```python
a = Vector([1, 2, 2])
b = Vector([2, 0, 1])

print(a.norm())                   # 3
print(a.dot(b))                   # 4
print(a.angle(b))                 # acos(4*sqrt(5)/15)
print(a.project_onto(b))          # (8/5, 0, 4/5)
print(a.orthogonal_complement(b)) # (-3/5, 2, 6/5)
```

### 1.4 Vecteurs par blocs et conversions

```python
# Concaténation par blocs
v_block = Vector.block([Vector([1, 2]), Vector([3, 4, 5])])
print(v_block)  # (1, 2, 3, 4, 5)

# Conversion en Matrix ou SymPy Matrix
M = a.to_matrix()    # Matrix 3x1
sp_col = a.to_sympy() # sympy.Matrix 3x1
```

---

## 2. La classe `Matrix`

Une [`Matrix`](src/linalg_pedagopy/objects/matrix.py#L35-L750) représente une matrice $m \times n$ sur $\mathbb{R}$.

### 2.1 Initialisation et constructeurs d'usine

```python
from linalg_pedagopy import Matrix

# Initialisation par une liste de lignes
A = Matrix([
    [1, 2, 3],
    [4, 5, 6]
])
print(A.shape)   # (2, 3)
print(A.nrows)   # 2 (nombre de lignes)
print(A.ncols)   # 3 (nombre de colonnes)

# Constructeurs d'usine
I3 = Matrix.identity(3)        # Matrice identité 3x3
Z = Matrix.zeros(2, 4)         # Matrice nulle 2x4
D = Matrix.diagonal([2, -1, 5]) # Matrice diagonale diag(2, -1, 5)

# Construction à partir de colonnes ou de lignes
col1 = Vector([1, 0])
col2 = Vector([2, 3])
M = Matrix.from_columns([col1, col2])
```

### 2.2 Opérations matricielles usuelles

```python
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[2, 0], [1, 2]])

# Somme, différence et produit scalaire
C = A + B
D = A - B
E = 2 * A

# Produit matriciel (opérateur @)
P = A @ B          # Matrix([[4, 4], [10, 8]])

# Transposée
AT = A.T           # Matrix([[1, 3], [2, 4]])

# Puissance entière (matrices carrées)
A_cubed = A ** 3
```

---

## 3. Les 4 vues du produit matriciel (VMLS §10.1)

L'ouvrage *VMLS* insiste sur quatre interprétations équivalentes mais conceptuellement distinctes du produit matriciel $C = A B$. `linalg_pedagopy` propose des méthodes explicites pour illustrer chacune d'elles :

```mermaid
flowchart TD
    AB["Produit Matriciel C = AB"]
    AB --> V1["1. Combinaison linéaire des colonnes de A"]
    AB --> V2["2. Produits scalaires ligne-colonne"]
    AB --> V3["3. Somme de produits externes (Outer Products)"]
    AB --> V4["4. Multiplication par blocs"]
```

### 3.1 Vue 1 : Combinaisons linéaires des colonnes de $A$

Chaque colonne $c_j$ de $C$ est une combinaison linéaire des colonnes $a_1, \dots, a_n$ de $A$, avec pour coefficients les composantes de la $j$-ième colonne de $B$ :
$$c_j = A b_j = \sum_{i=1}^n b_{ij} a_i$$

### 3.2 Vue 2 : Produits scalaires ligne-colonne

Chaque coefficient $c_{ij}$ est le produit scalaire standard entre la $i$-ième ligne de $A$ et la $j$-ième colonne de $B$ :
$$c_{ij} = \text{row}_i(A) \cdot \text{col}_j(B) = \sum_{k=1}^n a_{ik} b_{kj}$$

### 3.3 Vue 3 : Somme de produits externes (*Outer Products*)

Le produit $A B$ est la somme de $n$ matrices de rang 1 formées par les produits externes des colonnes de $A$ et des lignes de $B$ :
$$A B = \sum_{k=1}^n a_k b_k^T$$

### 3.4 Vue 4 : Multiplication par blocs

La méthode statique [`Matrix.block`](src/linalg_pedagopy/objects/matrix.py#L380-L420) assemble une matrice à partir d'une grille de blocs sous-matriciels :

```python
A11 = Matrix([[1, 2], [3, 4]])
A12 = Matrix([[0], [0]])
A21 = Matrix([[5, 6]])
A22 = Matrix([[7]])

M_bloc = Matrix.block([
    [A11, A12],
    [A21, A22]
])
print(M_bloc)
# [1, 2, 0]
# [3, 4, 0]
# [5, 6, 7]
```

---

## 4. Analyse et Propriétés des Matrices

### 4.1 Tests structurels

```python
M = Matrix([[1, 0], [0, 1]])
print(M.is_square)        # True
print(M.is_symmetric)     # True
print(M.is_orthogonal)    # True (M.T @ M == I)
print(M.is_invertible())  # True
```

### 4.2 Inversion formelle (`inv`)

La méthode [`inv(strict=True)`](src/linalg_pedagopy/objects/matrix.py#L694-L715) calcule l'inverse symbolique exacte via la réduction de Gauss-Jordan augmentée :
- Si la matrice est numérique et singulière, elle lève une [`SingularMatrixError`](src/linalg_pedagopy/core/exceptions.py).
- Si la matrice contient des paramètres, elle renvoie automatiquement un [`CaseSplit`](src/linalg_pedagopy/core/cases.py#L194-L320) décrivant les conditions d'inversibilité et les inverses partielles.

```python
from linalg_pedagopy import Matrix, symbols

a, = symbols("a")
A = Matrix([[1, a], [0, 1]])
print(A.inv()) # Matrix([[1, -a], [0, 1]])
```

### 4.3 Réduction échelonnée, rang et sous-espaces fondamentaux

Les méthodes [`rref`](src/linalg_pedagopy/objects/matrix.py#L649-L656), [`rank`](src/linalg_pedagopy/objects/matrix.py#L658-L674) et [`nullspace`](src/linalg_pedagopy/objects/matrix.py#L676-L693) acceptent un paramètre `assumptions` pour spécifier des contraintes de branche :

```python
A = Matrix([
    [1, 2, 0, 1],
    [0, 1, 1, 0],
    [1, 3, 1, 1]
])

print(A.rank())        # 2
rref_mat, pivots = A.rref()
print(pivots)          # (0, 1)

# Base du noyau (Ker A)
ker = A.nullspace()
print(ker)             # Liste de vecteurs engendrant Ker(A)

# Base de l'image (Col A)
im = A.col_space()
print(im)              # Colonnes pivot de A
```
