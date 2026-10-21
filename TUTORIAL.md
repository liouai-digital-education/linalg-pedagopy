# Tutoriel — `linalg_pedagopy`

Ce tutoriel fait le tour de **`linalg_pedagopy`**, un package Python d'algèbre linéaire formelle et pédagogique conçu pour l'enseignement en L1–L2. Chaque bloc de code s'exécute tel quel ; le carnet `carnets/tutoriel_linalg_pedagopy.ipynb` est généré à partir de ce fichier par `python scripts/convert_tutorial_to_ipynb.py`.

---

## Table des matières

1. [Philosophie et principes fondamentaux](#1-philosophie-et-principes-fondamentaux)
2. [Installation et configuration](#2-installation-et-configuration)
3. [Vecteurs et métriques (`Vector`)](#3-vecteurs-et-métriques-vector)
4. [Matrices et les 4 vues du produit matriciel (`Matrix`)](#4-matrices-et-les-4-vues-du-produit-matriciel-matrix)
5. [Systèmes linéaires et Gauss-Jordan (`GaussJordan`)](#5-systèmes-linéaires-et-gauss-jordan-gaussjordan)
6. [Discussion automatique selon des paramètres (`CaseSplit`)](#6-discussion-automatique-selon-des-paramètres-casesplit)
7. [Substitutions triangulaires (`BackSubstitution`, `ForwardSubstitution`)](#7-substitutions-triangulaires-backsubstitution-forwardsubstitution)
8. [Orthogonalisation de Gram-Schmidt et factorisation QR](#8-orthogonalisation-de-gram-schmidt-et-factorisation-qr)
9. [Moindres carrés linéaires (`LeastSquares`)](#9-moindres-carrés-linéaires-leastsquares)
10. [Moteurs de rendu et traçabilité (`Explanation`)](#10-moteurs-de-rendu-et-traçabilité-explanation)
11. [Générateurs à résultats propres et mode interactif](#11-générateurs-à-résultats-propres-et-mode-interactif)
12. [Comparaison Exact vs Flottant (`compare`)](#12-comparaison-exact-vs-flottant-compare)
13. [Le tuteur interactif (`tuteur`)](#13-le-tuteur-interactif-tuteur)
14. [Exercices pratiques guidés pas à pas](#14-exercices-pratiques-guidés-pas-à-pas)

---

## 1. Philosophie et principes fondamentaux

`linalg_pedagopy` se distingue des bibliothèques numériques classiques (comme NumPy ou SciPy) par trois exigences majeures :

1. **Exactitude formelle sur $\mathbb{R}$** :
   - Aucun arrondi intempestif : fractions rationnelles exactes, radicaux algébriques et paramètres réels sont préservés.
   - Tous les symboles créés portent automatiquement l'hypothèse `real=True`.
   - Les flottants saisis sont interceptés selon la politique déclarée `float_policy` (`"rationalize"` par défaut, `"reject"` ou `"keep"`).
2. **Oracle de nullité à 4 verdicts (`ZeroOracle`)** :
   - Tester l'égalité à zéro renvoie `ZERO`, `NONZERO`, `CONDITIONAL` ou `UNKNOWN`.
   - Si la nullité dépend d'un paramètre, l'algorithme ne choisit pas arbitrairement : il produit un embranchement formel (**`CaseSplit`**).
3. **Immutabilité et traçabilité hiérarchique** :
   - Les objets mathématiques `Vector` et `Matrix` sont strictement immuables.
   - Les algorithmes produisent un arbre d'étapes consultable à plusieurs niveaux de détail (niveau 0 : résultat seul, 1 : grandes étapes, 2 : sous-calculs, 3 : arithmétique élémentaire).
4. **Pédagogie active** :
   - Des sessions interactives permettent à l'élève de proposer des opérations de ligne, prédire des étapes, et recevoir un diagnostic ciblé sur ses erreurs.
   - Un **tuteur** accompagne la résolution de 39 exercices nommés sans jamais divulguer la solution en mode étudiant.

---

## 2. Installation et configuration

### Import des composants principaux

```python
from linalg_pedagopy import (
    Vector, Matrix, symbols, to_exact,
    GaussJordan, BackSubstitution, ForwardSubstitution,
    GramSchmidt, QR, LeastSquares,
    tracing, section, record, config, using_config,
    compare
)
from linalg_pedagopy.tuteur import exercice, glossaire
```

### Configuration globale et contextuelle

La configuration peut être inspectée ou ajustée globalement ou temporairement dans un bloc `with` :

```python
# Modification temporaire de la politique des flottants
with using_config(float_policy="reject"):
    # to_exact(0.1) lèvera une InexactInputError
    pass

# Changement global du niveau de trace par défaut
config.default_trace_level = 2
```

---

## 3. Vecteurs et métriques (`Vector`)

### 3.1 Création d'un vecteur

Un `Vector` représente un vecteur colonne $n \times 1$. Il accepte des entiers, des chaînes de fractions ou de racines, des fractions exactes ou des expressions SymPy :

```python
import sympy as sp
from fractions import Fraction
from linalg_pedagopy import Vector

v = Vector([1, "1/3", Fraction(5, 2), sp.sqrt(2)])
print(v)          # (1, 1/3, 5/2, sqrt(2))
print(v.size)     # 4
print(v.shape)    # (4, 1) - vu comme une colonne

# Vecteurs remarquables
z = Vector.zeros(3)      # (0, 0, 0)
u = Vector.ones(3)       # (1, 1, 1)
e2 = Vector.unit(1, 4)   # (0, 1, 0, 0) - indice 0-based
```

### 3.2 Opérations algébriques et combinaisons linéaires

```python
a = Vector([1, 2, 3])
b = Vector([4, -1, 2])

# Addition, soustraction, mise à l'échelle
print(a + b)     # (5, 1, 5)
print(a - b)     # (-3, 3, 1)
print(3 * a)     # (3, 6, 9)

# Combinaison linéaire tracée : 2*a - 3*b
comb = Vector.combination([a, b], [2, -3])
print(comb)      # (-10, 7, 0)
```

### 3.3 Métriques statistiques et géométriques

Ces métriques relient géométrie et statistiques :

```python
x = Vector([1, -2, 3, 2])

# Moyenne arithmétique : avg(x) = (1/n) * sum(x_i)
print("Moyenne :", x.avg())  # 1

# Vecteur centré (de-meaned) : x_tilde = x - avg(x)*1
print("Vecteur centré :", x.demean())  # (0, -3, 2, 1)

# Norme euclidienne : ||x|| = sqrt(sum(x_i^2))
print("Norme :", x.norm())  # 3*sqrt(2)

# Moyenne quadratique (RMS) : rms(x) = ||x|| / sqrt(n)
print("RMS :", x.rms())  # 3*sqrt(2)/2 = 3/sqrt(2)

# Écart type : std(x) = rms(x - avg(x)*1) (avec dénominateur sqrt(n))
print("Écart-type :", x.std())  # sqrt(14)/2

# Distance et Angle
y = Vector([2, 1, 0, 1])
print("Distance ||x - y|| :", x.distance(y))
print("Angle (rad) :", x.angle(y))
print("Corrélation :", x.correlation(y))
```

---

## 4. Matrices et les 4 vues du produit matriciel (`Matrix`)

### 4.1 Construction de matrices

```python
from linalg_pedagopy import Matrix, Vector

# Par liste de lignes
A = Matrix([
    [1, 2, 3],
    [4, 5, 6]
])

# À partir de colonnes ou de lignes
c1 = Vector([1, 0])
c2 = Vector([2, 3])
B = Matrix.from_columns([c1, c2])

# Matrices usuelles
I3 = Matrix.identity(3)
Z = Matrix.zeros(2, 4)
D = Matrix.diag([2, -1, 5])

# Matrices par blocs
M = Matrix.block([
    [B, Matrix.zeros(2, 2)],
    [Matrix.identity(2), B]
])
```

### 4.2 Les 4 points de vue du produit matriciel

Le produit $A B$ ou $A v$ n'est pas qu'un simple algorithme mécanique ; il s'interprète selon 4 points de vue fondamentaux :

```python
from linalg_pedagopy import Matrix, tracing

A = Matrix([[1, 2], [3, 4], [5, 6]])
B = Matrix([[2, -1], [0, 3]])

# 1. Vue par coefficients : (AB)_(i,j) = row_i(A) . col_j(B)
with tracing(level=2) as t1:
    res1 = A.matmul(B, view="entries")
print(t1.tree.children[0].message_key)  # matrix.matmul.entries

# 2. Vue par lignes : la ligne i de AB est une combinaison linéaire des lignes de B
res2 = A.matmul(B, view="rows")

# 3. Vue par colonnes : la colonne j de AB est une combinaison linéaire des colonnes de A
res3 = A.matmul(B, view="columns")

# 4. Vue par produits extérieurs : AB = sum_k col_k(A) @ row_k(B)
res4 = A.matmul(B, view="outer")
```

### 4.3 Transposée et Matrice de Gram

```python
# Transposée
print(A.T)

# Matrice de Gram G = A^T A (dont le coefficient (i, j) est a_i^T a_j)
G = A.gram()
print("Matrice de Gram :\n", G)
print("Colonnes orthonormées ?", G == Matrix.identity(A.cols))
```

---

### 4.4 Matrices structurées classiques

```python
from linalg_pedagopy import difference_matrix, running_sum_matrix, vandermonde, convolution

D = difference_matrix(4)                 # (D x)_i = x_{i+1} - x_i
S = running_sum_matrix(4)                # sommes cumulées
print(D @ S)                             # D « défait » S
print(vandermonde([0, 1, 2]))            # valeurs d'un polynôme de degré 2 en 0, 1, 2
print(convolution([1, -2, 1], [2, 1]))   # produit de polynômes : (2, -3, 0, 1)
```

---

## 5. Systèmes linéaires et Gauss-Jordan (`GaussJordan`)

`GaussJordan` réduit une matrice augmentée $[A \mid b]$ à sa forme échelonnée réduite (RREF), identifie les pivots, calcule le rang, extrait la base du noyau $\ker(A)$ et caractérise l'ensemble des solutions.

### 5.1 Solution unique

```python
from linalg_pedagopy import Matrix, Vector, GaussJordan

A = Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
b = Vector([8, -11, -3])

gj = GaussJordan(A, b)
res = gj.run()

print("Rang :", res.rank)            # 3
print("Colonnes pivots :", res.pivots) # (0, 1, 2)
print("Solution unique :", res.solution.x) # (2, 3, -1)

# Contrôle a posteriori tracé
print(res.verify())
```

### 5.2 Système indéterminé (Ensemble affine de solutions)

```python
A = Matrix([[1, 2, -1], [2, 4, -2]])
b = Vector([3, 6])

res = GaussJordan(A, b).run()
print("Type de solution :", type(res.solution)) # AffineSolution
print("Solution particulière x0 :", res.solution.x0)
print("Base du noyau :", res.solution.basis)

# Évaluation d'une solution particulière pour des valeurs des variables libres
x_part = res.solution.at_params(2, 1)
print("Vérification A @ x_part == b :", A @ x_part == b) # True
```

### 5.3 Système incompatible

```python
A = Matrix([[1, 2], [2, 4]])
b = Vector([3, 7])

res = GaussJordan(A, b).run()
print("Compatible ?", res.solution.is_consistent) # False
print("Ligne témoin d'incompatibilité : L", res.solution.row + 1)
print("Témoin (0 = c) :", res.solution.witness)   # 1
```

### 5.4 Inversion de matrice

```python
A = Matrix([[1, 2], [3, 5]])
inv_A = A.inv()
print("A^(-1) =\n", inv_A)
print("Vérification A @ A^(-1) == I :", A @ inv_A == Matrix.identity(2))
```

### 5.5 Déterminant

`A.det()` renvoie le déterminant exact. La procédure `Determinant` en donne la trace, avec la méthode de Bareiss (défaut en présence de paramètres : aucune division risquée), l'élimination, le développement par cofacteurs ou la règle de Sarrus, et `zeros()` les valeurs du paramètre qui rendent la matrice singulière.

```python
from linalg_pedagopy import Determinant

a, = symbols("a")
A = Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]])
print("det A =", A.det())

res = Determinant(A).run()
print(res.explain(level=1))
print("Singulière pour :", [str(c) for c in res.zeros()])

# Développement par cofacteurs suivant la ligne ou la colonne la plus creuse
print(Determinant(Matrix([[1, 0, 2], [3, 0, 4], [5, 6, 7]]), method="cofactors").run().explain(level=2))
```

---

## 6. Discussion automatique selon des paramètres (`CaseSplit`)

La fonctionnalité la plus distinctive de `linalg_pedagopy` est la discussion formelle automatique :

```python
from linalg_pedagopy import Matrix, Vector, symbols, tracing, GaussJordan

# Création du paramètre réel 'a'
a, = symbols("a")

A = Matrix([
    [1, 1, 1],
    [1, a, 1],
    [1, 1, a]
])
b = Vector([1, 2, 3])

with tracing(level=2):
    res = GaussJordan(A, b).run()

# res est une instance de CaseSplit[GJResult]
print(res.explain(level=1))
```

Sortie générée automatiquement :
```text
Discussion selon a
├─ Cas a ≠ 1 (générique) : pivots non nuls, rang 3, solution unique
│    x = ( (a − 4)/(a − 1), 1/(a − 1), 2/(a − 1) )
└─ Cas a = 1 : L2 et L3 deviennent (0 0 0 | 1) et (0 0 0 | 2)
     système incompatible (témoin : 0 = 1)
```

### Spécialisation numérique d'un `CaseSplit`

```python
# Cas générique pour a = 3
sol_a3 = res.at(a=3)
print("Pour a = 3, solution :", sol_a3.solution.x) # (-1/2, 1/2, 1)

# Cas particulier a = 1
sol_a1 = res.at(a=1)
print("Pour a = 1, compatible ?", sol_a1.solution.is_consistent) # False
```

---

## 7. Substitutions triangulaires (`BackSubstitution`, `ForwardSubstitution`)

Les systèmes triangulaires se résolvent sans jamais inverser de matrice :

```python
from linalg_pedagopy import Matrix, Vector, BackSubstitution, ForwardSubstitution

# Système triangulaire supérieur R x = c
R = Matrix([
    [2, -1, 3],
    [0, 4, 2],
    [0, 0, -2]
])
c = Vector([9, 8, -6])

res_back = BackSubstitution(R, c).run()
print("Solution par substitution arrière :", res_back.x)
print(res_back.explain())
```

---

## 8. Orthogonalisation de Gram-Schmidt et factorisation QR

### 8.1 Gram-Schmidt rationnel vs normalisé

Deux variantes sont disponibles :
- `normalize="end"` (par défaut) : calcule des vecteurs orthogonaux $\tilde{q}_i$ restant entièrement dans $\mathbb{Q}$, puis normalise à la toute fin.
- `normalize="each"` : algorithme classique qui normalise à chaque étape (avec apparition de radicaux).

```python
from linalg_pedagopy import Vector, GramSchmidt

a1 = Vector([1, 1, 0])
a2 = Vector([1, 0, 1])
a3 = Vector([0, 1, 1])

gs = GramSchmidt([a1, a2, a3], normalize="end")
res_gs = gs.run()

print("Vecteurs orthogonaux rationnels :", res_gs.orthogonal)
print("Vecteurs orthonormés finaux :", res_gs.orthonormal)
print("Famille libre ?", res_gs.independent) # True
```

### 8.2 Détection de dépendance linéaire et témoin

Si la famille est liée, `GramSchmidt` isole l'indice fautif et calcule le témoin exact de liaison :

```python
v1 = Vector([1, 2, -1])
v2 = Vector([2, 0, 1])
v3 = 3 * v1 - 2 * v2 # Vecteur dépendant

res_dep = GramSchmidt([v1, v2, v3], strict=False).run()
print("Famille libre ?", res_dep.independent) # False
print("Indice du vecteur lié : a_", res_dep.dependent_index + 1)
print("Témoin :", res_dep.witness) # a_3 = 3·a_1 - 2·a_2
```

### 8.3 Factorisation QR ($A = QR$)

```python
from linalg_pedagopy import Matrix, QR

A = Matrix([
    [1, 1],
    [1, 0],
    [0, 1]
])

qr_res = QR(A).run()
print("Q =\n", qr_res.Q)
print("R =\n", qr_res.R)
print("Q_tilde (rationnelle) =\n", qr_res.Q_tilde)

# Vérification formelle Q^T Q = I et Q R = A
print(qr_res.verify())
```

---

## 9. Moindres carrés linéaires (`LeastSquares`)

Pour un système surdéterminé $A x \approx b$ ($m \ge n$ avec $A$ de rang plein en colonnes), `LeastSquares` minimise $\|A x - b\|^2$.

Trois méthodes sont proposées :
1. `"rational_qr"` (par défaut) : résout $\tilde{R} \hat{x} = D^{-2} \tilde{Q}^T b$ par substitution arrière. **Tout le calcul reste dans $\mathbb{Q}$ sans racine carrée**.
2. `"qr"` : résolution par QR normalisée $R \hat{x} = Q^T b$.
3. `"normal"` : formation des équations normales $(A^T A) \hat{x} = A^T b$.

```python
from linalg_pedagopy import Matrix, Vector, LeastSquares

A = Matrix([
    [1, 0],
    [1, 1],
    [1, 2],
    [1, 3]
])
b = Vector([1, 2, 2, 4])

ls = LeastSquares(A, b, method="rational_qr").run()

print("Solution optimale x_hat :", ls.x_hat) # (9/10, 9/10)
print("Projection y_hat = A x_hat :", ls.y_hat)
print("Résidu r_hat = A x_hat - b :", ls.r_hat) # (-1/10, -1/5, 7/10, -2/5)
print("Norme du résidu :", ls.residual_norm)
print("RMS du résidu :", ls.residual_rms)

# Orthogonalité du résidu vérifiée colonne par colonne (A^T r_hat = 0)
print(ls.verify())
```

---

## 10. Moteurs de rendu et traçabilité (`Explanation`)

Tout résultat d'algorithme (`res.explain()`, `res.verify()`) renvoie un objet `Explanation` capable d'exporter la trace sous 4 formats :

```python
exp = ls.explain(level=1)

# 1. Rendu texte Unicode pour terminal
print(exp.to_text())

# 2. Rendu LaTeX complet avec matrices augmentées et pivots encadrés
latex_code = exp.to_latex()

# 3. Rendu Markdown pour notebooks et rapports
markdown_code = exp.to_markdown()

# 4. Rendu HTML interactif repliable avec MathJax
html_code = exp.to_html(standalone=True)

# Sauvegarde directe dans un fichier selon l'extension
exp.save("moindres_carres.html")
exp.save("moindres_carres.tex")
```

---

## 11. Générateurs à résultats propres et mode interactif

### 11.1 Générateurs de matrices « propres »

Pour créer des exercices sans fractions incontrôlables ni radicaux inutiles :

```python
from linalg_pedagopy.exercises import (
    generate_unimodular_matrix,
    generate_integer_rref_matrix,
    generate_rational_qr_matrix,
    generate_clean_least_squares,
    generate_parametric_system
)

# 1. Matrice unimodulaire (inverse entière garantie)
U = generate_unimodular_matrix(3, seed=42)

# 2. Matrice et sa RREF entière
A, R = generate_integer_rref_matrix(3, 4, rank=2, seed=42)

# 3. Famille orthogonale rationnelle par transformée de Cayley
A_qr, Q, R_qr = generate_rational_qr_matrix(3, seed=42)

# 4. Moindres carrés à solution entière et résidu exact dans ker(A^T)
A_ls, b_ls, x_true, r_true = generate_clean_least_squares(4, 2, seed=42)
```

### 11.2 Résolution interactive par l'élève

L'élève peut conduire lui-même la réduction de Gauss-Jordan :

```python
from linalg_pedagopy import Matrix, Vector, GaussJordan

A = Matrix([[1, 2], [3, 5]])
b = Vector([5, 13])

session = GaussJordan(A, b).interactive(mode="autonomous")

# L'élève propose une opération élémentaire
fb = session.propose("L2 <- L2 - 3*L1")
print(fb.message)
# "Valide. Le coefficient (2,1) est maintenant nul : progression vers la forme échelonnée."

# Détection automatique d'erreur (ex. dilatation par 0)
fb_err = session.propose("L2 <- 0*L2")
print(fb_err.message)
# "Invalide : une dilatation par 0 n'est pas une opération élémentaire..."

# Demander une suggestion sans dévoiler la réponse
print(session.hint())
```

---

## 12. Comparaison Exact vs Flottant (`compare`)

Le module `compare` illustre les limites fondamentales du calcul machine en virgule flottante :

```python
from linalg_pedagopy.compare import (
    lauchli_gram_schmidt_experiment,
    lauchli_least_squares_experiment,
    hilbert_conditioning_experiment
)

# 1. Perte d'orthogonalité sur la matrice de Läuchli (eps = 1e-8)
print(lauchli_gram_schmidt_experiment())

# 2. Échec des équations normales face à QR sur la matrice de Läuchli
print(lauchli_least_squares_experiment())

# 3. Explosion du conditionnement sur les matrices de Hilbert
print(hilbert_conditioning_experiment(sizes=[3, 5, 7]))
```

---

## 13. Le tuteur interactif (`tuteur`)

Le tuteur accompagne l'étudiant sur **39 exercices nommés**, classés en 9 thèmes et 3 niveaux, sans jamais donner la solution.

### Les 8 principes pédagogiques
1. **Vérification par propriété** : le tuteur ne stocke pas de corrigé figé. Il vérifie que la réponse satisfait la définition mathématique ($A B = I$, résidu orthogonal, etc.).
2. **Diagnostic explicatif** : il décrit ce que calcule la réponse de l'étudiant et pose une question guidée.
3. **Échelle d'indices sur 4 niveaux** (orientation $\to$ outil $\to$ démarrage $\to$ exercice jumeau résolu). Il n'y a pas de niveau « solution ».
4. **Exercice jumeau résolu** : au niveau 4, l'étudiant étudie un problème de même structure avec d'autres données.
5. **Verrou des données** : les données d'un exercice (`ex.donnees`) refusent de calculer à la place de l'étudiant tant qu'aucune réponse n'a été validée.
6. **Engagement avant exploration** : pour un vrai/faux, il faut enregistrer une prédiction (`ex.predire(...)`) avant d'ouvrir le laboratoire (`ex.labo()`).
7. **Un essai n'est pas une preuve** : si un énoncé est vrai sur une instance testée, le tuteur demande une justification.
8. **Transparence** : un journal JSON local garde la progression, sans note (`ex.bilan()`).

### Le catalogue

```python
from linalg_pedagopy import tuteur

tuteur.catalogue()                      # tableau : n°, titre, identifiant, thème, type, niveau
print(tuteur.themes())
ex = tuteur.exercice("moyenne-glissante")   # ou tuteur.exercice(16), ou par son titre
ex.enonce()
```

---

## 14. Exercices pratiques guidés pas à pas

Voici 5 exercices complets résolus et commentés illustrant l'ensemble du workflow.

### Exercice 1 : Écart à la moyenne glissante (`moyenne-glissante`)

**Énoncé** :
$p \in \mathbb{R}^6$ est une série temporelle de prix sur 6 jours. $d \in \mathbb{R}^3$ mesure, à partir du 4ᵉ jour ($i = 1, 2, 3$), l'écart entre le prix du jour ($p_{i+3}$) et la moyenne des trois jours précédents :
$$d_i = p_{i+3} - \frac{p_i + p_{i+1} + p_{i+2}}{3}$$
Trouver la matrice $A$ de taille $3 \times 6$ telle que $d = A p$.

**Démarche pas à pas** :
1. L'inconnue $p$ a 6 composantes, et la sortie $d$ en a 3. La matrice $A$ est donc de dimension $3 \times 6$.
2. Écrivons chaque ligne en ordonnant les coefficients devant $p_1, \dots, p_6$ :
   - Pour $i = 1$ : $d_1 = p_4 - \frac{1}{3}p_1 - \frac{1}{3}p_2 - \frac{1}{3}p_3 \implies L_1 = \begin{pmatrix} -\frac{1}{3} & -\frac{1}{3} & -\frac{1}{3} & 1 & 0 & 0 \end{pmatrix}$.
   - Pour $i = 2$ : $d_2 = p_5 - \frac{1}{3}p_2 - \frac{1}{3}p_3 - \frac{1}{3}p_4 \implies L_2 = \begin{pmatrix} 0 & -\frac{1}{3} & -\frac{1}{3} & -\frac{1}{3} & 1 & 0 \end{pmatrix}$.
   - Pour $i = 3$ : $d_3 = p_6 - \frac{1}{3}p_3 - \frac{1}{3}p_4 - \frac{1}{3}p_5 \implies L_3 = \begin{pmatrix} 0 & 0 & -\frac{1}{3} & -\frac{1}{3} & -\frac{1}{3} & 1 \end{pmatrix}$.

**Validation avec le tuteur** :

```python
from fractions import Fraction
from linalg_pedagopy import Matrix
from linalg_pedagopy.tuteur import exercice

ex = exercice("moyenne-glissante")
print(ex.enonce())
print(ex.indice()) # Indice 1

# Si l'étudiant se trompe sur la ligne 2 (en recopiant la ligne 1) :
t = Fraction(1, 3)
A_fausse = Matrix([
    [-t, -t, -t, 1, 0, 0],
    [-t, -t, -t, 1, 0, 0],
    [0, 0, -t, -t, -t, 1]
])
retour = ex.verifier(A_fausse)
print(retour.diagnostic)
# Retour du tuteur :
# "Taille correcte (3 x 6). Lignes 1 et 3 correctes.
#  Votre ligne 2 calcule d_2 = p_4 - (p_1 + p_2 + p_3)/3.
#  Relisez la définition de d_2 : quel est le prix « du jour » pour i = 2 ?"

# Soumission de la matrice exacte :
A_juste = Matrix([
    [-t, -t, -t, 1, 0, 0],
    [0, -t, -t, -t, 1, 0],
    [0, 0, -t, -t, -t, 1]
])
print(ex.verifier(A_juste))
# "Taille correcte (3 x 6). Toutes les lignes de votre matrice calculent exactement d = A p."
```

---

### Exercice 2 : Orthogonalité : vrai ou faux ? (`orthogonalite-vrai-faux`)

**Énoncé** :
Soient $a, b, c \in \mathbb{R}^n$ tels que $a \perp c$ et $b \perp c$. Les affirmations suivantes sont-elles toujours vraies ou peuvent-elles être fausses ?
(a) $a \perp b$
(b) $(a + b) \perp c$
(c) $(a - b) \perp (a + b)$

**Démarche pas à pas** :
1. $a \perp c$ et $b \perp c$ signifient $a^T c = 0$ et $b^T c = 0$.
2. Pour (b) : $(a + b)^T c = a^T c + b^T c = 0 + 0 = 0$. L'affirmation (b) est **toujours vraie**.
3. Pour (a) : Deux vecteurs orthogonaux à un troisième ne sont pas forcément orthogonaux entre eux (par exemple dans le plan $xy$ orthogonal à l'axe $z$). L'affirmation (a) **peut être fausse**.
4. Pour (c) : $(a - b)^T (a + b) = \|a\|^2 - \|b\|^2$. Cela n'est nul que si $\|a\| = \|b\|$. Si les normes diffèrent, c'est faux. L'affirmation (c) **peut être fausse**.

**Session avec le tuteur** :

```python
from linalg_pedagopy import Vector
from linalg_pedagopy.tuteur import exercice

ex = exercice("orthogonalite-vrai-faux")

# Étape obligatoire : s'engager sur une prédiction
ex.predire(a="peut être faux", b="toujours vrai", c="peut être faux")

# Ouverture du laboratoire
lab = ex.labo()

# Test avec des vecteurs simples respectant a ⊥ c et b ⊥ c
rep = lab.tester(
    a=Vector([1, 0, 0]),
    b=Vector([1, 1, 0]),
    c=Vector([0, 0, 1])
)
print(rep.message)
# "Hypothèses vérifiées : a ⊥ c et b ⊥ c.
#  (a) est faux sur votre instance : c'est un contre-exemple valide.
#  (b) est vrai sur votre instance.
#  (c) est faux sur votre instance : c'est un contre-exemple valide.
#  Pour (b), des essais ne suffisent pas : rédigez une justification."
```

---

### Exercice 3 : Deux inverses à droite (`deux-inverses-droite`)

**Énoncé** :
On considère la matrice large $A = \begin{pmatrix} 1 & -1 & 2 \\ 0 & 1 & 1 \end{pmatrix}$.
Trouver deux matrices inverses à droite distinctes $B_1$ et $B_2$ ($3 \times 2$) telles que $A B_1 = I_2$, $A B_2 = I_2$ et $B_1 \neq B_2$.

**Démarche pas à pas** :
1. Une inverse à droite $B$ de taille $3 \times 2$ possède deux colonnes $b_1, b_2$ telles que $A b_1 = e_1 = \begin{pmatrix} 1 \\ 0 \end{pmatrix}$ et $A b_2 = e_2 = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$.
2. Résolvons le système augmenté avec Gauss-Jordan :
   $$[A \mid I_2] = \begin{pmatrix} 1 & -1 & 2 & \bigm| & 1 & 0 \\ 0 & 1 & 1 & \bigm| & 0 & 1 \end{pmatrix} \xrightarrow{L_1 \leftarrow L_1 + L_2} \begin{pmatrix} 1 & 0 & 3 & \bigm| & 1 & 1 \\ 0 & 1 & 1 & \bigm| & 0 & 1 \end{pmatrix}$$
3. Les deux premières colonnes sont pivots ; la 3e colonne correspond à une variable libre :
   - Pour la première colonne de $B$ : en posant la 3e composante égale à $0$, on a $b_{11} = 1, b_{21} = 0, b_{31} = 0$.
   - Pour la deuxième colonne de $B$ : en posant la 3e composante égale à $0$, on a $b_{12} = 1, b_{22} = 1, b_{32} = 0$.
   Cela donne une première inverse à droite :
   $$B_1 = \begin{pmatrix} 1 & 1 \\ 0 & 1 \\ 0 & 0 \end{pmatrix}$$
4. Pour former une deuxième inverse à droite $B_2 \neq B_1$, choisissons par exemple la 3e composante égale à $1$ pour la première colonne :
   $b_{11} + 3(1) = 1 \implies b_{11} = -2$, et $b_{21} + 1(1) = 0 \implies b_{21} = -1$.
   En gardant la même seconde colonne :
   $$B_2 = \begin{pmatrix} -2 & 1 \\ -1 & 1 \\ 1 & 0 \end{pmatrix}$$

**Validation par propriété avec le tuteur** :

```python
from linalg_pedagopy import Matrix
from linalg_pedagopy.tuteur import exercice

ex = exercice("deux-inverses-droite")

B1 = Matrix([[1, 1], [0, 1], [0, 0]])
B2 = Matrix([[-2, 1], [-1, 1], [1, 0]])

# Soumission du couple (B1, B2)
resultat = ex.verifier((B1, B2))
print(resultat.diagnostic)
# "Bravo ! A B1 = I_2, A B2 = I_2 et B1 ≠ B2 : vos deux inverses à droite sont valides."
```

---

### Exercice 4 : Ajustement par moindres carrés rationnels

**Énoncé** :
On cherche à ajuster une droite $y = x_1 + x_2 t$ sur 4 points expérimentaux $(t_i, y_i)$ :
$(0, 1), (1, 2), (2, 2), (3, 4)$.
Calculer la solution optimale $\hat{x}$ par factorisation QR rationnelle et vérifier l'orthogonalité du résidu.

**Démarche pas à pas** :
1. Posons la matrice de conception $A$ et le vecteur d'observations $b$ :
   $$A = \begin{pmatrix} 1 & 0 \\ 1 & 1 \\ 1 & 2 \\ 1 & 3 \end{pmatrix}, \quad b = \begin{pmatrix} 1 \\ 2 \\ 2 \\ 4 \end{pmatrix}$$
2. Orthogonalisons les colonnes de $A$ sans racine carrée :
   - $\tilde{q}_1 = a_1 = \begin{pmatrix} 1 & 1 & 1 & 1 \end{pmatrix}^T$, avec $\|\tilde{q}_1\|^2 = 4$.
   - Projection de $a_2$ sur $\tilde{q}_1$ : $\tilde{r}_{12} = \frac{\tilde{q}_1^T a_2}{\|\tilde{q}_1\|^2} = \frac{0 + 1 + 2 + 3}{4} = \frac{6}{4} = \frac{3}{2}$.
   - $\tilde{q}_2 = a_2 - \frac{3}{2}\tilde{q}_1 = \begin{pmatrix} -\frac{3}{2} & -\frac{1}{2} & \frac{1}{2} & \frac{3}{2} \end{pmatrix}^T$, avec $\|\tilde{q}_2\|^2 = \frac{9+1+1+9}{4} = 5$.
3. La matrice triangulaire supérieure unitaire est $\tilde{R} = \begin{pmatrix} 1 & \frac{3}{2} \\ 0 & 1 \end{pmatrix}$.
4. Calculons le second membre réduit $c = D^{-2} \tilde{Q}^T b$ :
   - $\tilde{q}_1^T b = 1 + 2 + 2 + 4 = 9 \implies c_1 = \frac{9}{4}$.
   - $\tilde{q}_2^T b = -\frac{3}{2}(1) - \frac{1}{2}(2) + \frac{1}{2}(2) + \frac{3}{2}(4) = \frac{9}{2} \implies c_2 = \frac{9/2}{5} = \frac{9}{10}$.
5. Résolution par remontée de $\tilde{R} \hat{x} = c$ :
   - $\hat{x}_2 = c_2 = \frac{9}{10}$.
   - $\hat{x}_1 = c_1 - \frac{3}{2}\hat{x}_2 = \frac{9}{4} - \frac{27}{20} = \frac{45 - 27}{20} = \frac{18}{20} = \frac{9}{10}$.
6. Le résidu est $\hat{r} = A \hat{x} - b = \begin{pmatrix} -1/10 & -1/5 & 7/10 & -2/5 \end{pmatrix}^T$.
   Vérification :
   $$a_1^T \hat{r} = -\frac{1}{10} - \frac{2}{10} + \frac{7}{10} - \frac{4}{10} = 0$$
   $$a_2^T \hat{r} = 0\left(-\frac{1}{10}\right) + 1\left(-\frac{2}{10}\right) + 2\left(\frac{7}{10}\right) + 3\left(-\frac{4}{10}\right) = \frac{-2 + 14 - 12}{10} = 0$$

**Exécution avec `LeastSquares`** :

```python
from linalg_pedagopy import Matrix, Vector, LeastSquares

A = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]])
b = Vector([1, 2, 2, 4])

res = LeastSquares(A, b, method="rational_qr").run()
print("x_hat :", res.x_hat)        # (9/10, 9/10)
print("r_hat :", res.r_hat)        # (-1/10, -1/5, 7/10, -2/5)
print(res.verify().to_text())       # Confirme A^T r_hat = 0
```

---

### Exercice 5 : Solution de norme minimale (`norme-minimale`)

**Énoncé** :
On cherche le vecteur $x \in \mathbb{R}^3$ de **norme minimale** $\|x\|^2 = x_1^2 + x_2^2 + x_3^2$ satisfaisant la contrainte linéaire $C x = d$ avec :
$$C = \begin{pmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \end{pmatrix}, \quad d = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$$

**Démarche pas à pas** :
1. Le problème de norme minimale sous contrainte linéaire a pour conditions d'optimalité le système KKT :
   $$2 x + C^T z = 0 \quad \text{et} \quad C x = d$$
2. De la première équation, $x = -\frac{1}{2} C^T z \in \text{Im}(C^T)$.
3. En multipliant par $C$ à gauche :
   $$C x = -\frac{1}{2} C C^T z = d \implies -\frac{1}{2} z = (C C^T)^{-1} d$$
4. On en déduit la formule explicite de la solution :
   $$x^* = C^T (C C^T)^{-1} d$$
5. Calculons $C C^T$ :
   $$C C^T = \begin{pmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \end{pmatrix} \begin{pmatrix} 1 & 0 \\ 1 & 1 \\ 0 & 1 \end{pmatrix} = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$$
   Son inverse est :
   $$(C C^T)^{-1} = \frac{1}{3} \begin{pmatrix} 2 & -1 \\ -1 & 2 \end{pmatrix}$$
6. Multiplions par $d = \begin{pmatrix} 1 \\ 1 \end{pmatrix}$ :
   $$(C C^T)^{-1} d = \frac{1}{3} \begin{pmatrix} 1 \\ 1 \end{pmatrix}$$
7. Enfin, multiplions par $C^T$ :
   $$x^* = \begin{pmatrix} 1 & 0 \\ 1 & 1 \\ 0 & 1 \end{pmatrix} \begin{pmatrix} 1/3 \\ 1/3 \end{pmatrix} = \begin{pmatrix} 1/3 \\ 2/3 \\ 1/3 \end{pmatrix}$$
   Vérification de la contrainte :
   - Ligne 1 : $1/3 + 2/3 = 1 = d_1$ (vérifié).
   - Ligne 2 : $2/3 + 1/3 = 1 = d_2$ (vérifié).
   Sa norme au carré est $\|x^*\|^2 = (1/9) + (4/9) + (1/9) = 6/9 = 2/3$. Tout autre vecteur vérifiant $C x = d$ (par exemple $x = (1, 0, 1)^T$) a une norme strictement supérieure ($\|x\|^2 = 2 > 2/3$).

**Validation avec le tuteur** :

```python
from fractions import Fraction
from linalg_pedagopy import Vector
from linalg_pedagopy.tuteur import exercice

ex = exercice("norme-minimale")
x_opt = Vector([Fraction(1, 3), Fraction(2, 3), Fraction(1, 3)])
print(ex.verifier(x_opt))
# "Exact ! Votre vecteur x vérifie C x = d et les conditions KKT de norme minimale."
```

---

## 15. Synthèse des commandes rapides

| Action | Commande |
|---|---|
| Créer des symboles réels | `a, b = symbols("a b")` |
| Coercition exacte d'une valeur | `val = to_exact("1/3")` |
| Réduction de Gauss-Jordan | `res = GaussJordan(A, b).run()` |
| Déterminant (et valeurs singulières) | `A.det()` ; `res = Determinant(A).run() ; res.zeros()` |
| Discussion selon un paramètre | `res.explain(level=1)` ou `res.at(a=2)` |
| Gram-Schmidt rationnel | `res = GramSchmidt(vectors, normalize="end").run()` |
| Factorisation QR | `res = QR(A).run()` |
| Moindres carrés rationnels | `res = LeastSquares(A, b).run()` |
| Trace et explication multi-format | `exp = res.explain() ; exp.save("trace.html")` |
| Expérience numérique de Läuchli | `lauchli_least_squares_experiment()` (module `linalg_pedagopy.compare`) |
| Catalogue des exercices | `tuteur.catalogue()` |
| Séance de tuteur | `ex = exercice("moyenne-glissante") ; ex.enonce() ; ex.indice() ; ex.verifier(...)` |
| Repartir de zéro sur un exercice | `ex.recommencer()` |
| Glossaire anglais $\to$ français | `glossaire("least squares")` |
| Lancer les tests | `python -m pytest tests/ -v` |
| Lancer la démonstration | `python scripts/demo.py` |
