"""Script pour générer problemes_algebre_lineaire_pedagopy.ipynb."""

import json
from pathlib import Path

cells = []


def add_md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text})


def add_code(code):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": code,
    })


# -------------------------------------------------------------
# EN-TÊTE
# -------------------------------------------------------------
add_md("""# 5 Grands Problèmes d'Algèbre Linéaire avec `linalg_pedagopy`

Ce notebook propose **5 longs problèmes calculatoires et conceptuels d'algèbre linéaire**, conçus pour explorer l'ensemble des capacités du package **`linalg_pedagopy`** :

1. **Problème 1 — Système paramétrique et discussion de rang** : élimination de Gauss-Jordan avec bifurcation d'arbres de cas (`CaseSplit`, `Condition`), compatibilité au sens de Rouché-Fontené et sous-espaces affines de solutions.
2. **Problème 2 — Commutant d'un bloc de Jordan et racine carrée matricielle** : formulation d'équations matricielles linéaires $MN = NM$, extraction de base de noyau (`nullspace()`) et résolution de l'équation quadratique $X^2 = I + N$.
3. **Problème 3 — Chaîne de Markov et puissances asymptotiques** : matrices stochastiques, calcul de la distribution stationnaire par noyau, polynôme annulateur minimal scindé et division euclidienne pour le calcul de $P^n$.
4. **Problème 4 — Orthogonalisation de Gram-Schmidt et factorisation QR** : géométrie euclidienne dans $\\mathbb{R}^4$, décomposition $A = QR$, matrice de projection orthogonale $P_F = QQ^T$, idempotent symétrique et calcul de distance.
5. **Problème 5 — Moindres carrés et pseudoinverse de Moore-Penrose** : ajustement polynomial de données expérimentales, équations normales de Gauss, projection orthogonale du second membre, vérification d'orthogonalité du résidu et calcul de la pseudoinverse exacte.

---
### Importation des modules
""")

add_code("""import sympy as sp
from linalg_pedagopy import (
    Matrix,
    Vector,
    GaussJordan,
    GramSchmidt,
    QR,
    LeastSquares,
    symbols,
    Condition,
    tracing,
)

print("linalg_pedagopy chargé avec succès !")""")

# -------------------------------------------------------------
# PROBLEME 1
# -------------------------------------------------------------
add_md("""---
# Problème 1 : Système linéaire paramétrique et bifurcation de cas (`CaseSplit`)

### Contexte mathématique
On considère le système linéaire dépendant d'un paramètre réel $m \\in \\mathbb{R}$ et de deux constantes $(a, b) \\in \\mathbb{R}^2$ :

$$\\begin{cases}
x + y + m z = 1 \\\\
x + m y + z = a \\\\
m x + y + z = b
\\end{cases}$$

Ce système modélise par exemple l'équilibre des potentiels dans un réseau triangulaire à conductances réglables.

La matrice du système est :
$$A(m) = \\begin{pmatrix} 1 & 1 & m \\\\ 1 & m & 1 \\\\ m & 1 & 1 \\end{pmatrix}, \\qquad v = \\begin{pmatrix} 1 \\\\ a \\\\ b \\end{pmatrix}$$

---
### Questions :
1. **Définition symbolique** : Définir la matrice $A(m)$ et le second membre $v$ à l'aide de symboles formels.
2. **Échelonnement et discussion globale** : Appliquer `GaussJordan` sur $A(m)$ avec `strict=False` pour obtenir l'arbre complet de bifurcation (`CaseSplit`). Identifier les valeurs critiques de $m$ où le rang chute.
3. **Cas générique ($m \\neq 1$ et $m \\neq -2$)** : Extraire la branche générique, calculer la matrice inverse $A(m)^{-1}$ et vérifier la formule en calculant le produit $A(m) A(m)^{-1} = I_3$.
4. **Cas critique $m = -2$ (rang 2)** :
   * Déterminer le rang et une base du noyau $\\ker(A(-2))$.
   * Trouver la condition nécessaire et suffisante sur $(a, b)$ pour que le système admette au moins une solution (compatibilité).
5. **Cas critique $m = 1$ (rang 1)** :
   * Déterminer le rang et la dimension du noyau.
   * Donner la condition de compatibilité sur $(a, b)$.
   * Décrire géométriquement l'ensemble des solutions (plan affine) et vérifier une solution particulière.
""")

add_md("#### Q1.1 — Définition de la matrice et du second membre")
add_code("""m, a, b = symbols("m a b")

A_m = Matrix([[1, 1, m],
              [1, m, 1],
              [m, 1, 1]])

v_vec = Vector([1, a, b])

print("Matrice A(m) :")
display(A_m)
print("Second membre v :")
display(v_vec)""")

add_md("#### Q1.2 — Échelonnement de Gauss-Jordan et structure du `CaseSplit`")
add_code("""# Réduction sous condition avec Gauss-Jordan
gj_A = GaussJordan(A_m, strict=False)
res_split = gj_A.run()

print(f"Nombre de branches découvertes : {len(res_split.branches)}")
for i, branch in enumerate(res_split.branches, start=1):
    print(f"\\n--- Branche {i} ---")
    print(f"Condition : {branch.condition}")
    print(f"Rang      : {branch.result.rank}")
    print(f"Pivots    : {[p + 1 for p in branch.result.pivots]}")""")

add_md("#### Q1.3 — Cas générique : Calcul de l'inverse et vérification $A A^{-1} = I_3$")
add_code("""# Inversion avec l'hypothèse générique (liste de conditions)
cond_generique = ["m != 1", "m != -2"]
res_inv = A_m.inv(assumptions=cond_generique)

# Si une seule branche subsiste, res_inv est directement une Matrix
A_inv_gen = res_inv if isinstance(res_inv, Matrix) else res_inv.generic()
print("Inverse générique A(m)^(-1) :")
display(A_inv_gen)

# Vérification par produit matriciel
prod_identite = A_m @ A_inv_gen
print("Produit A(m) @ A(m)^(-1) :")
display(prod_identite)""")

add_md("#### Q1.4 — Étude du cas $m = -2$ (Rang 2, droite affine)")
add_code("""# Matrice pour m = -2
A_m2 = A_m.subs({"m": -2})
print("Matrice A(-2) :")
display(A_m2)

# Calcul du noyau
noyau_m2 = A_m2.nullspace()
print(f"Rang de A(-2) : {A_m2.rank()}")
print("Base du noyau ker(A(-2)) :", noyau_m2)

# Échelonnement du système complet augmenté [A(-2) | v]
v_m2 = Vector([1, a, b])
gj_sys_m2 = GaussJordan(A_m2, v_m2).run()

print("\\n--- Discussion de compatibilité pour m = -2 ---")
for i, br in enumerate(gj_sys_m2.branches, 1):
    print(f"\\nBranche {i} : Condition = {br.condition}")
    print("Matrice augmentée échelonnée réduite :")
    display(br.result.augmented_rref)
    print("Ensemble solution :", br.result.solution)""")

add_md("#### Q1.5 & Q1.6 — Étude du cas $m = 1$ (Rang 1, plan affine) et vérification")
add_code("""# Matrice pour m = 1
A_1 = A_m.subs({"m": 1})
print("Matrice A(1) :")
display(A_1)

# Calcul du noyau (espace de dimension 2)
noyau_1 = A_1.nullspace()
print(f"Rang de A(1) : {A_1.rank()}")
print("Base du noyau ker(A(1)) (2 vecteurs directeurs) :")
for idx, vec in enumerate(noyau_1, 1):
    print(f"  v_{idx} =", vec)

# Système augmenté pour m = 1
gj_sys_1 = GaussJordan(A_1, v_vec).run()

print("\\n--- Discussion de compatibilité pour m = 1 ---")
for i, br in enumerate(gj_sys_1.branches, 1):
    print(f"\\nBranche {i} : Condition = {br.condition}")
    print("Matrice augmentée :")
    display(br.result.augmented_rref)
    print("Solution :", br.result.solution)

# Si a = 1 et b = 1, la solution particulière est x0 = (1, 0, 0)
x0 = Vector([1, 0, 0])
print("\\nVérification de la solution particulière A(1) @ x0 :")
display(A_1 @ x0)""")

# -------------------------------------------------------------
# PROBLEME 2
# -------------------------------------------------------------
add_md("""---
# Problème 2 : Commutant d'un bloc de Jordan et racine carrée matricielle

### Contexte mathématique
Soit $N \\in \\mathcal{M}_3(\\mathbb{R})$ le bloc nilpotent standard de Jordan :
$$N = \\begin{pmatrix} 0 & 1 & 0 \\\\ 0 & 0 & 1 \\\\ 0 & 0 & 0 \\end{pmatrix}, \\qquad A = I_3 + N = \\begin{pmatrix} 1 & 1 & 0 \\\\ 0 & 1 & 1 \\\\ 0 & 0 & 1 \\end{pmatrix}$$

On s'intéresse à l'équation non-linéaire :
$$X^2 = A$$

L'approche classique consiste à remarquer que si $X^2 = A$, alors $X$ commute avec $A$, et donc avec $N = A - I_3$. On restreint ainsi la recherche de $X$ au **commutant** de $N$.

---
### Questions :
1. **Nilpotence** : Calculer $N^2$ et $N^3$. En déduire l'indice de nilpotence de $N$.
2. **Caractérisation du commutant** : Poser une matrice générale $M = (m_{i,j})_{1 \\le i,j \\le 3}$ comportant 9 inconnues réelles. Calculer le commutateur $[M, N] = MN - NM$.
3. **Dimension et base du commutant** : Résoudre le système linéaire $[M, N] = 0$ via `nullspace()`. En déduire qu'une matrice commute avec $N$ si et seulement si elle est de la forme :
   $$M = \\alpha I_3 + \\beta N + \\gamma N^2$$
4. **Équation de la racine carrée** : En cherchant $X$ sous cette forme, développer formellement $X^2$ en fonction de $(\\alpha, \\beta, \\gamma)$ et de la base $(I_3, N, N^2)$.
5. **Résolution et vérification** : Identifier avec $A = I_3 + N$, trouver les valeurs de $(\\alpha, \\beta, \\gamma)$ et vérifier avec `linalg_pedagopy` que la matrice $X$ trouvée vérifie exactement $X^2 = A$.
""")

add_md("#### Q2.1 — Calcul des puissances de $N$")
add_code("""N = Matrix([[0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]])

I3 = Matrix.identity(3)
A_jordan = I3 + N

print("N =")
display(N)
print("N^2 =")
display(N @ N)
print("N^3 =")
display(N @ N @ N)
print("N est bien nilpotente d'indice 3.")""")

add_md("#### Q2.2 & Q2.3 — Commutant $\\mathcal{C}(N) = \\{M \\in \\mathcal{M}_3(\\mathbb{R}) \\mid MN = NM\\}$")
add_code("""# Matrice générale 3x3 avec 9 variables symboliques
var_names = [f"m_{i}_{j}" for i in range(1, 4) for j in range(1, 4)]
syms = symbols(" ".join(var_names))
M_sym = Matrix([[syms[i*3 + j] for j in range(3)] for i in range(3)])

print("Matrice M symbolique :")
display(M_sym)

# Commutateur MN - NM
comm = M_sym @ N - N @ M_sym
print("Commutateur [M, N] = M @ N - N @ M :")
display(comm)

# Système d'équations en les 9 variables
eqs = comm.flat_entries
M_mat_sys, _ = sp.linear_eq_to_matrix(eqs, syms)
base_comm = Matrix(M_mat_sys.tolist()).nullspace()

print(f"Dimension du commutant : {len(base_comm)}")
print("Vecteurs de base dans R^9 :")
for k, v in enumerate(base_comm, 1):
    mat_k = Matrix([[v[i*3 + j] for j in range(3)] for i in range(3)])
    print(f"Matrice de base B_{k} :")
    display(mat_k)
print("-> Les 3 matrices de base sont proportionnelles à I_3, N et N^2 !")""")

add_md("#### Q2.4 & Q2.5 — Résolution de $X^2 = I_3 + N$ et vérification")
add_code("""# Posons X = alpha * I + beta * N + gamma * N^2
# Par nilpotence N^3 = 0, on a :
# X^2 = alpha^2 * I + 2*alpha*beta * N + (2*alpha*gamma + beta^2) * N^2
# On identifie avec A = I + N :
# 1) alpha^2 = 1  =>  alpha = 1 (en choisissant la racine positive)
# 2) 2*alpha*beta = 1  =>  beta = 1/2
# 3) 2*alpha*gamma + beta^2 = 0  =>  2*gamma + 1/4 = 0  =>  gamma = -1/8

alpha = sp.Integer(1)
beta = sp.Rational(1, 2)
gamma = sp.Rational(-1, 8)

X = alpha * I3 + beta * N + gamma * (N @ N)
print("Matrice racine carrée candidate X :")
display(X)

# Calcul du carré X^2
X_carre = X @ X
print("Calcul de X^2 :")
display(X_carre)

print("Vérification formelle X^2 == A :", X_carre == A_jordan)""")

# -------------------------------------------------------------
# PROBLEME 3
# -------------------------------------------------------------
add_md("""---
# Problème 3 : Chaîne de Markov, distribution stationnaire et puissances $P^n$

### Contexte mathématique
On considère un système dynamique à 3 états (par exemple : 1 = En service, 2 = Dégradé, 3 = En maintenance) dont la matrice de transition stochastique par colonnes est :

$$P = \\begin{pmatrix} 1/2 & 1/3 & 0 \\\\ 1/2 & 1/3 & 1/2 \\\\ 0 & 1/3 & 1/2 \\end{pmatrix}$$

Chaque colonne $j$ représente la loi de transition sachant que le système est dans l'état $j$.

---
### Questions :
1. **Propriété stochastique** : Vérifier que la somme des coefficients de chaque colonne de $P$ vaut exactement 1.
2. **Évolution à court terme** : Calculer $P^2$ et $P^3$. Interpréter la probabilité de se trouver dans l'état 1 après 2 étapes en partant de l'état 3.
3. **Distribution stationnaire** :
   * Justifier que 1 est valeur propre de $P$.
   * Résoudre $(P - I_3) \\pi = 0$ via `nullspace()`.
   * Normaliser le vecteur obtenu pour que la somme de ses composantes vaille 1 : c'est l'unique distribution stationnaire $\\pi$.
4. **Polynôme annulateur** :
   * Déterminer les trois valeurs propres exactes $\\lambda_1, \\lambda_2, \\lambda_3$ de $P$.
   * Vérifier que le polynôme $(X - \\lambda_1)(X - \\lambda_2)(X - \\lambda_3)$ est un polynôme annulateur de $P$.
5. **Comportement asymptotique $P^n$** :
   * Exprimer la limite $\\lim_{n \\to \\infty} P^n$.
   * Vérifier que cette limite est la matrice dont chaque colonne est égale à $\\pi$.
""")

add_md("#### Q3.1 — Définition et vérification stochastique")
add_code("""P = Matrix([
    [sp.Rational(1, 2), sp.Rational(1, 3), 0],
    [sp.Rational(1, 2), sp.Rational(1, 3), sp.Rational(1, 2)],
    [0,                 sp.Rational(1, 3), sp.Rational(1, 2)]
])

print("Matrice de transition P :")
display(P)

for j in range(3):
    somme_col = sum(P[i, j] for i in range(3))
    print(f"Somme de la colonne {j + 1} : {somme_col}")""")

add_md("#### Q3.2 — Puissances $P^2$ et $P^3$ (avec la vue pédagogique par colonnes)")
add_code("""# Produit tracé avec la vue 'columns' (chaque colonne est l'image d'un état)
P2 = P.matmul(P, view="columns")
print("Matrice P^2 :")
display(P2)

P3 = P2 @ P
print("Matrice P^3 :")
display(P3)

p_3_to_1_step2 = P2[0, 2]
print(f"Probabilité de transition État 3 -> État 1 en 2 étapes : {p_3_to_1_step2}")""")

add_md("#### Q3.3 — Distribution stationnaire $\\pi$ par calcul de noyau")
add_code("""# Résolution de (P - I_3) * pi = 0
I3 = Matrix.identity(3)
ker_stat = (P - I3).nullspace()

print("Base du noyau ker(P - I_3) :", ker_stat)
v_stat = ker_stat[0]

# Normalisation pour obtenir une loi de probabilité (somme = 1)
somme_coords = sum(v_stat[i] for i in range(3))
pi_vect = [v_stat[i] / somme_coords for i in range(3)]

print(f"Distribution stationnaire pi = ({pi_vect[0]}, {pi_vect[1]}, {pi_vect[2]})")

# Vérification : P @ pi == pi
pi_col = Matrix([[pi_vect[0]], [pi_vect[1]], [pi_vect[2]]])
print("Vérification P @ pi :")
display(P @ pi_col)""")

add_md("#### Q3.4 — Polynôme annulateur minimal scindé")
add_code("""# Les valeurs propres sont 1, 1/2 et -1/6
lam1 = sp.Integer(1)
lam2 = sp.Rational(1, 2)
lam3 = sp.Rational(-1, 6)

# Produit annulateur (P - lam1*I)(P - lam2*I)(P - lam3*I)
ann_P = (P - lam1 * I3) @ (P - lam2 * I3) @ (P - lam3 * I3)
print("Évaluation de (P - I)(P - 1/2 I)(P + 1/6 I) :")
display(ann_P)
print("Le polynôme annulateur s'annule exactement sur P !")""")

add_md("#### Q3.5 — Limite asymptotique et comparaison avec $\\pi$")
add_code("""# Calcul de P^20 pour illustrer la convergence
P_n = I3
for _ in range(20):
    P_n = P_n @ P

print("Matrice P^20 (approximation de la limite) :")
display(P_n)

# Matrice théorique de rang 1 dont chaque colonne est pi
P_inf = Matrix([
    [pi_vect[0], pi_vect[0], pi_vect[0]],
    [pi_vect[1], pi_vect[1], pi_vect[1]],
    [pi_vect[2], pi_vect[2], pi_vect[2]]
])
print("Matrice limite théorique [pi | pi | pi] :")
display(P_inf)""")

# -------------------------------------------------------------
# PROBLEME 4
# -------------------------------------------------------------
add_md("""---
# Problème 4 : Orthogonalisation de Gram-Schmidt, factorisation QR et projection

### Contexte mathématique
Dans l'espace euclidien standard $\\mathbb{R}^4$ muni du produit scalaire canonique $\\langle x, y \\rangle = x^T y$, on considère le sous-espace vectoriel $F = \\text{Vect}(v_1, v_2, v_3)$ engendré par :

$$v_1 = \\begin{pmatrix} 1 \\\\ 1 \\\\ 1 \\\\ 1 \\end{pmatrix}, \\qquad v_2 = \\begin{pmatrix} 1 \\\\ 0 \\\\ 0 \\\\ 1 \\end{pmatrix}, \\qquad v_3 = \\begin{pmatrix} 0 \\\\ 2 \\\\ 1 \\\\ 0 \\end{pmatrix}$$

On pose $A = (v_1 \\mid v_2 \\mid v_3) \\in \\mathcal{M}_{4,3}(\\mathbb{R})$.

---
### Questions :
1. **Indépendance linéaire** : Déterminer le rang de $A$. Vérifier que $(v_1, v_2, v_3)$ forme une base de $F$.
2. **Orthogonalisation de Gram-Schmidt** : Appliquer l'algorithme `GramSchmidt(A)`. Inspecter la base orthogonale $(u_1, u_2, u_3)$ et vérifier les produits scalaires mutuels $\\langle u_i, u_j \\rangle = 0$ pour $i \\neq j$.
3. **Factorisation QR** : Obtenir la décomposition $A = QR$ avec `QR(A)`.
   * Vérifier que les colonnes de $Q$ sont orthonormales : $Q^T Q = I_3$.
   * Vérifier que $R$ est triangulaire supérieure inversible et que $Q R = A$.
4. **Matrice de projection orthogonale** :
   * Exprimer la matrice de projection orthogonale $P_F \\in \\mathcal{M}_4(\\mathbb{R})$ sur le sous-espace $F$ à l'aide de $Q$ : $P_F = Q Q^T$.
   * Vérifier que $P_F^2 = P_F$ (idempotence) et $P_F^T = P_F$ (symétrie).
5. **Projection et distance d'un point cible** : Soit le vecteur cible $y = (2, 3, -1, 4)^T \\in \\mathbb{R}^4$.
   * Calculer sa projection orthogonale $p = P_F y$.
   * Calculer le vecteur résidu $r = y - p$.
   * Vérifier que $r$ est orthogonal à chaque vecteur de la base $v_1, v_2, v_3$ ($A^T r = 0$).
   * Calculer la distance euclidienne $d(y, F) = \\|r\\|$.
""")

add_md("#### Q4.1 — Rang et matrice $A$")
add_code("""v1 = Vector([1, 1, 1, 1])
v2 = Vector([1, 0, 0, 1])
v3 = Vector([0, 2, 1, 0])

A_geo = Matrix.from_columns([v1, v2, v3])
print("Matrice A (colonnes v1, v2, v3) :")
display(A_geo)
print(f"Rang de A : {A_geo.rank()} -> La famille (v1, v2, v3) est libre.")""")

add_md("#### Q4.2 — Algorithme de Gram-Schmidt")
add_code("""gs_res = GramSchmidt(A_geo).run()

print("Base orthogonale u1, u2, u3 (non normalisée) :")
for idx, u in enumerate(gs_res.orthogonal, 1):
    print(f"  u_{idx} =", u)

# Vérification des produits scalaires croisés
u1, u2, u3 = gs_res.orthogonal
print(f"\\n<u1, u2> = {u1.dot(u2)}")
print(f"<u1, u3> = {u1.dot(u3)}")
print(f"<u2, u3> = {u2.dot(u3)}")""")

add_md("#### Q4.3 — Factorisation $A = QR$")
add_code("""qr_res = QR(A_geo).run()
Q_mat = qr_res.Q
R_mat = qr_res.R

print("Matrice Q (orthonormale 4x3) :")
display(Q_mat)
print("Matrice R (triangulaire supérieure 3x3) :")
display(R_mat)

print("Vérification Q^T @ Q = I_3 :")
display(Q_mat.T @ Q_mat)

print("Vérification Q @ R == A :", Q_mat @ R_mat == A_geo)""")

add_md("#### Q4.4 — Projecteur orthogonal $P_F = Q Q^T$")
add_code("""P_F = Q_mat @ Q_mat.T

print("Matrice du projecteur orthogonal P_F (4x4) :")
display(P_F)

print("P_F^2 == P_F (idempotent) :", P_F @ P_F == P_F)
print("P_F^T == P_F (symétrique) :", P_F.T == P_F)""")

add_md("#### Q4.5 — Projection, résidu et distance euclidienne")
add_code("""y_target = Vector([2, 3, -1, 4])
print("Vecteur cible y :", y_target)

# Projection orthogonale p = P_F * y
p_proj = P_F @ y_target
print("Projection p = P_F @ y :", p_proj)

# Vecteur résidu r = y - p
r_res = y_target - p_proj
print("Résidu r = y - p :", r_res)

# Orthogonalité de r avec les colonnes de A : A^T @ r = 0
print("Produit A^T @ r (doit être le vecteur nul) :", A_geo.T @ r_res)

# Distance euclidienne ||r|| = sqrt(<r, r>)
dist_carre = r_res.dot(r_res)
dist_exacte = sp.sqrt(dist_carre)
print(f"Distance au carré ||r||^2 = {dist_carre}")
print(f"Distance euclidienne d(y, F) = {dist_exacte} ≈ {float(dist_exacte):.4f}")""")

# -------------------------------------------------------------
# PROBLEME 5
# -------------------------------------------------------------
add_md("""---
# Problème 5 : Régression polynomiale par les moindres carrés et pseudoinverse

### Contexte mathématique
On dispose de 5 points de mesures expérimentales $(x_i, y_i)_{1 \\le i \\le 5}$ :
$$(-2, 4), \\quad (-1, 2), \\quad (0, 1), \\quad (1, 2), \\quad (2, 5)$$

On souhaite ajuster un modèle parabolique :
$$y(x) = c_0 + c_1 x + c_2 x^2$$

Ce problème se traduit par le système linéaire surdéterminé $A c \\approx y$ :
$$\\begin{pmatrix} 1 & -2 & 4 \\\\ 1 & -1 & 1 \\\\ 1 & 0 & 0 \\\\ 1 & 1 & 1 \\\\ 1 & 2 & 4 \\end{pmatrix} \\begin{pmatrix} c_0 \\\\ c_1 \\\\ c_2 \\end{pmatrix} = \\begin{pmatrix} 4 \\\\ 2 \\\\ 1 \\\\ 2 \\\\ 5 \\end{pmatrix}$$

---
### Questions :
1. **Matrice de Vandermonde** : Construire la matrice $A \\in \\mathcal{M}_{5,3}(\\mathbb{R})$ et le vecteur de mesures $y$. Vérifier que $A$ est de rang plein (rang 3).
2. **Équations normales de Gauss** :
   * Former la matrice de Gram $A^T A$ et le second membre projeté $A^T y$.
   * Vérifier que $A^T A$ est une matrice symétrique inversible.
3. **Résolution des équations normales** : Résoudre $(A^T A) c = A^T y$ via `GaussJordan`. En déduire les coefficients optimaux $(c_0^*, c_1^*, c_2^*)$.
4. **Procédure `LeastSquares` & Pseudoinverse** :
   * Résoudre directement avec `LeastSquares(A, y)` de `linalg_pedagopy`.
   * Inspecter la solution $\\hat{x}$, le vecteur ajusté $\\hat{y} = A \\hat{x}$, et la pseudoinverse de Moore-Penrose $A^+ = (A^T A)^{-1} A^T$.
5. **Propriétés du résidu et théorème de Pythagore** :
   * Vérifier l'orthogonalité du résidu : $A^T r^* = 0$.
   * Calculer la somme des résidus au carré $\\|r^*\\|^2$.
   * Vérifier l'identité de Pythagore : $\\|y\\|^2 = \\|\\hat{y}\\|^2 + \\|r^*\\|^2$.
""")

add_md("#### Q5.1 — Modélisation et rang plein")
add_code("""x_points = [-2, -1, 0, 1, 2]
y_points = [4, 2, 1, 2, 5]

A_vander = Matrix([[1, x, x**2] for x in x_points])
y_obs = Vector(y_points)

print("Matrice de Vandermonde A (5x3) :")
display(A_vander)
print("Vecteur d'observations y :", y_obs)
print(f"Rang de A : {A_vander.rank()} (rang plein 3)")""")

add_md("#### Q5.2 & Q5.3 — Équations normales de Gauss $(A^T A) c = A^T y$")
add_code("""# Matrice de Gram et second membre projeté
Gram = A_vander.T @ A_vander
At_y = A_vander.T @ y_obs

print("Matrice de Gram A^T @ A :")
display(Gram)
print("Second membre A^T @ y :", At_y)

# Résolution exacte par Gauss-Jordan
gj_norm = GaussJordan(Gram, At_y).run()
c_etoile = gj_norm.solution.x
print("\\nCoefficients optimaux (c0*, c1*, c2*) :", c_etoile)
print(f"Modèle optimal : y(x) = {c_etoile[0]} + ({c_etoile[1]})*x + ({c_etoile[2]})*x^2")""")

add_md("#### Q5.4 — Procédure automatique `LeastSquares` et Pseudoinverse de Moore-Penrose")
add_code("""# Résolution via la procédure dédiée de linalg_pedagopy
ls_proc = LeastSquares(A_vander, y_obs).run()

print("Solution x_hat :", ls_proc.x_hat)
print("Valeurs ajustées y_hat = A @ x_hat :", ls_proc.y_hat)
print("Vecteur résidu r* = y - y_hat :", ls_proc.residual)

print("\\nPseudoinverse de Moore-Penrose A^+ :")
display(ls_proc.pseudoinverse)

# Vérification : x_hat == A^+ @ y
x_pseudo = ls_proc.pseudoinverse @ y_obs
print("Vérification x_hat == A^+ @ y :", ls_proc.x_hat == x_pseudo)""")

add_md("#### Q5.5 — Orthogonalité du résidu et théorème de Pythagore")
add_code("""r_star = ls_proc.residual

# 1. Vérification de l'orthogonalité fondamentale : A^T @ r* = 0
print("A^T @ r* (orthogonalité) :", A_vander.T @ r_star)

# 2. Somme des carrés des résidus
norm_r2 = r_star.dot(r_star)
print(f"Norme au carré du résidu ||r*||^2 : {norm_r2} (≈ {float(norm_r2):.4f})")

# 3. Vérification du théorème de Pythagore : ||y||^2 == ||y_hat||^2 + ||r*||^2
y_hat = ls_proc.y_hat
norm_y2 = y_obs.dot(y_obs)
norm_yhat2 = y_hat.dot(y_hat)

print(f"||y||^2     = {norm_y2}")
print(f"||y_hat||^2 = {norm_yhat2}")
print(f"||y_hat||^2 + ||r*||^2 = {norm_yhat2 + norm_r2}")
print("Théorème de Pythagore vérifié :", norm_y2 == norm_yhat2 + norm_r2)""")

# -------------------------------------------------------------
# ENREGISTREMENT DU NOTEBOOK
# -------------------------------------------------------------
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

output_path = Path(__file__).resolve().parent.parent / "carnets" / "problemes_algebre_lineaire_pedagopy.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Notebook généré avec succès : {output_path}")
print(f"Nombre total de cellules : {len(cells)}")
