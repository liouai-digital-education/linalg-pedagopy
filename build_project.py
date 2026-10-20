"""Générateur du projet d'exploration ouvert en algèbre linéaire."""

import json

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


# ==============================================================================
# EN-TÊTE DU PROJET
# ==============================================================================
add_md("""# Projet d'Exploration Ouvert : Algèbre Linéaire des Réseaux Complexes
### *Topologie, Équilibres, Marches Aléatoires (PageRank) et Optimisation Euclidienne*
---

### Présentation générale du projet

L'étude des réseaux interconnectés (réseaux électriques de Kirchhoff, réseaux de distribution d'eau, réseaux informatiques ou graphes du Web) constitue l'un des domaines les plus féconds où dialoguent toutes les branches de l'algèbre linéaire :
* **Algèbre des matrices et systèmes linéaires** : lois de Kirchhoff, flots et potentiels.
* **Théorie spectrale et bifurcation paramétrique** : déconnexion de clusters, analyse de rang critique et espaces de solutions via `CaseSplit`.
* **Processus stochastiques et puissances de matrices** : marches aléatoires, diffusion d'information et algorithme PageRank de Google.
* **Géométrie euclidienne et factorisation QR** : dualité fondamentale entre l'espace des coupures (*cut space*) et l'espace des cycles (*cycle space*).
* **Optimisation par moindres carrés et pseudoinverse** : calibration et filtrage de données bruitées mesurées sur le réseau.

Ce projet guidé est structuré en **5 grandes étapes progressives**, suivies de **3 défis ouverts** à explorer.
Toutes les explorations calculatoires sont réalisées à l'aide du package pédagogique **`linalg_pedagopy`**.
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

print("Package linalg_pedagopy prêt pour l'exploration du projet !")""")

# ==============================================================================
# PARTIE 1
# ==============================================================================
add_md("""---
## Partie 1 : Topologie du Réseau et Opérateur Laplacien

### 1.1 Modélisation du réseau
On considère un réseau composé de $n = 4$ sommets (nœuds) et $m = 4$ arêtes orientées (branches) :
* Arête $e_1$ reliant le sommet 1 au sommet 2 ($1 \\to 2$)
* Arête $e_2$ reliant le sommet 2 au sommet 3 ($2 \\to 3$)
* Arête $e_3$ reliant le sommet 3 au sommet 4 ($3 \\to 4$)
* Arête $e_4$ reliant le sommet 2 au sommet 4 ($2 \\to 4$)

La **matrice d'incidence arête-sommet** $B \\in \\mathcal{M}_{4,4}(\\mathbb{R})$ est définie par :
$$B_{k, i} = \\begin{cases} -1 & \\text{si l'arête } k \\text{ part du sommet } i \\\\ +1 & \\text{si l'arête } k \\text{ arrive au sommet } i \\\\ 0 & \\text{sinon} \\end{cases}$$

La **matrice Laplacienne** du réseau s'exprime par le produit fondamental :
$$L = B^T B$$
""")

add_code("""# Définition de la matrice d'incidence B
B = Matrix([
    [-1,  1,  0,  0],  # e1 : 1 -> 2
    [ 0, -1,  1,  0],  # e2 : 2 -> 3
    [ 0,  0, -1,  1],  # e3 : 3 -> 4
    [ 0, -1,  0,  1]   # e4 : 2 -> 4
])

print("Matrice d'incidence B (4 arêtes x 4 sommets) :")
display(B)

# Calcul du Laplacien L = B^T @ B
L = B.T @ B
print("\\nMatrice Laplacienne L = B^T @ B :")
display(L)""")

add_md("""### 1.2 Théorème de Kirchhoff et noyau du Laplacien
Pour tout vecteur de potentiels $x = (x_1, x_2, x_3, x_4)^T$, le vecteur $B x$ représente les différences de potentiel sur chaque branche :
$$B x = \\begin{pmatrix} x_2 - x_1 \\\\ x_3 - x_2 \\\\ x_4 - x_3 \\\\ x_4 - x_2 \\end{pmatrix}$$
L'énergie de dissipation de Dirichlet dans le réseau est :
$$\\mathcal{E}(x) = \\frac{1}{2} x^T L x = \\frac{1}{2} \\|B x\\|^2 = \\frac{1}{2} \\sum_{(i,j) \\in E} (x_j - x_i)^2$$
On en déduit immédiatement que $L x = 0 \\iff B x = 0 \\iff x_1 = x_2 = x_3 = x_4$.
Le noyau $\\ker(L)$ est donc de dimension 1, engendré par le vecteur constant $\\mathbf{1} = (1, 1, 1, 1)^T$.
""")

add_code("""# Calcul du noyau et du rang de L
noyau_L = L.nullspace()
rang_L = L.rank()

print(f"Rang du Laplacien L : {rang_L}")
print(f"Dimension du noyau : {len(noyau_L)}")
print("Base du noyau ker(L) :", noyau_L)

# Vérification : L @ 1 == 0
un_vec = Vector([1, 1, 1, 1])
print("Vérification L @ (1, 1, 1, 1)^T :", L @ un_vec)""")

add_md("""### 1.3 Équation de Poisson sur le réseau : $L x = b$
On injecte des courants externes aux sommets représentés par le vecteur $b = (b_1, b_2, b_3, b_4)^T$.
La loi des nœuds de Kirchhoff s'écrit :
$$L x = b$$
Puisque $\\ker(L) = \\text{Vect}(\\mathbf{1})$ et que $L$ est symétrique ($L = L^T$), le théorème de Rouché-Fontené indique que le système admet des solutions si et seulement si :
$$b \\in \\text{Im}(L) = (\\ker L)^\\perp \\iff \\sum_{i=1}^4 b_i = 0$$
(conservation globale de la charge / du flux entrant et sortant).
""")

add_code("""b1, b2, b3 = symbols("b1 b2 b3")
# On force b4 = -(b1 + b2 + b3) pour assurer la compatibilité
b_flux = Vector([b1, b2, b3, -(b1 + b2 + b3)])

print("Second membre conservatif b :", b_flux)

# Résolution avec GaussJordan
gj_poisson = GaussJordan(L, b_flux).run()
print("\\nRésolution de L x = b :")
print("Solution :", gj_poisson.solution)""")

# ==============================================================================
# PARTIE 2
# ==============================================================================
add_md("""---
## Partie 2 : Transition de Phase et Déconnexion Paramétrique (`CaseSplit`)

### 2.1 Réseau avec liaison réglable
On suppose maintenant que la conductance de l'arête reliant le sommet 1 au sommet 2 est modulable par un paramètre réel $\\alpha \\ge 0$ (par exemple une vanne ou un transistor).
Quand $\\alpha > 0$, le réseau est connexe.
Quand $\\alpha = 0$, le sommet 1 est totalement isolé du reste du graphe $\{2, 3, 4\}$.

La matrice Laplacienne paramétrique s'écrit :
$$L(\\alpha) = \\begin{pmatrix} \\alpha & -\\alpha & 0 & 0 \\\\ -\\alpha & \\alpha + 2 & -1 & -1 \\\\ 0 & -1 & 2 & -1 \\\\ 0 & -1 & -1 & 2 \\end{pmatrix}$$
""")

add_code("""alpha = symbols("alpha")[0]

L_alpha = Matrix([
    [alpha, -alpha, 0, 0],
    [-alpha, alpha + 2, -1, -1],
    [0, -1, 2, -1],
    [0, -1, -1, 2]
])

print("Laplacien paramétrique L(alpha) :")
display(L_alpha)""")

add_md("""### 2.2 Analyse de la bifurcation de rang avec `CaseSplit`
On applique `GaussJordan` sur la matrice symbolique $L(\\alpha)$ avec `strict=False` pour découvrir automatiquement l'arbre des régimes physiques :
""")

add_code("""gj_alpha = GaussJordan(L_alpha, strict=False)
res_alpha = gj_alpha.run()

print(f"Nombre de branches découvertes : {len(res_alpha.branches)}")
for i, br in enumerate(res_alpha.branches, start=1):
    print(f"\\n=== Branche {i} ===")
    print(f"Condition sur alpha : {br.condition}")
    print(f"Rang du Laplacien   : {br.result.rank}")
    print(f"Pivots colonnes     : {[p + 1 for p in br.result.pivots]}")""")

add_md("""### 2.3 Interprétation spectrale de la déconnexion
* **Pour $\\alpha \\neq 0$** : rang 3, $\\dim \\ker L(\\alpha) = 1$. Le réseau est connexe.
* **Pour $\\alpha = 0$** : le rang chute à 2 ! La dimension du noyau devient $4 - 2 = 2$.
D'après le théorème spectral des graphes, **la multiplicité de la valeur propre 0 est égale au nombre de composantes connexes**.
Calculons explicitement la base du noyau en $\\alpha = 0$ :
""")

add_code("""L_0 = L_alpha.subs({"alpha": 0})
print("Matrice Laplacienne L(0) :")
display(L_0)

noyau_L0 = L_0.nullspace()
print(f"Rang de L(0) : {L_0.rank()}")
print(f"Base de ker(L(0)) (dimension {len(noyau_L0)}) :")
for idx, v in enumerate(noyau_L0, 1):
    print(f"  v_{idx} =", v)

print("\\n-> v_1 = (1, 0, 0, 0) est l'indicatrice du sommet isolé {1}")
print("-> v_2 = (0, 1, 1, 1) est l'indicatrice du cluster connecté {2, 3, 4} !")""")

# ==============================================================================
# PARTIE 3
# ==============================================================================
add_md("""---
## Partie 3 : Marches Aléatoires, Diffusion et Algorithme PageRank

### 3.1 Matrice de transition stochastique
Considérons maintenant le réseau comme un graphe de pages Web orientées :
* Page 1 ne pointe que vers la page 2 ($1 \\to 2$).
* Page 2 pointe vers 1, 3 et 4 (3 liens sortants, probabilité $1/3$ chacun).
* Page 3 pointe vers 2 et 4 (2 liens sortants, probabilité $1/2$ chacun).
* Page 4 pointe vers 2 et 3 (2 liens sortants, probabilité $1/2$ chacun).

La matrice de transition $P$ (stochastique en colonnes : $\\sum_{i} P_{i,j} = 1$) est :
$$P = \\begin{pmatrix} 0 & 1/3 & 0 & 0 \\\\ 1 & 0 & 1/2 & 1/2 \\\\ 0 & 1/3 & 0 & 1/2 \\\\ 0 & 1/3 & 1/2 & 0 \\end{pmatrix}$$
""")

add_code("""P = Matrix([
    [0, sp.Rational(1, 3), 0, 0],
    [1, 0, sp.Rational(1, 2), sp.Rational(1, 2)],
    [0, sp.Rational(1, 3), 0, sp.Rational(1, 2)],
    [0, sp.Rational(1, 3), sp.Rational(1, 2), 0]
])

print("Matrice de transition P :")
display(P)

# Vérification stochastique
for col in range(4):
    s = sum(P[row, col] for row in range(4))
    print(f"Somme colonne {col + 1} : {s}")""")

add_md("""### 3.2 Calcul des puissances avec différentes vues pédagogiques
Calculons $P^2$ et $P^3$ avec la méthode `.matmul()` en mode `view="columns"` pour observer comment chaque état se diffuse :
""")

add_code("""# Vue par colonnes : P^2 = P * P
P2 = P.matmul(P, view="columns")
print("P^2 (probabilités de transition en 2 étapes) :")
display(P2)

P3 = P2 @ P
print("P^3 (probabilités de transition en 3 étapes) :")
display(P3)""")

add_md("""### 3.3 Score PageRank exact (Distribution stationnaire $\\pi$)
La distribution stationnaire $\\pi = (\\pi_1, \\pi_2, \\pi_3, \\pi_4)^T$ vérifie :
$$P \\pi = \\pi \\iff (P - I_4) \\pi = 0 \\quad \\text{avec} \\quad \\sum_{i=1}^4 \\pi_i = 1$$
Résolvons ce problème exactement avec `.nullspace()` :
""")

add_code("""I4 = Matrix.identity(4)
ker_P = (P - I4).nullspace()

print("Base du noyau ker(P - I_4) :", ker_P)
v_raw = ker_P[0]

# Normalisation probabiliste
somme_pi = sum(v_raw[i] for i in range(4))
pi_score = [v_raw[i] / somme_pi for i in range(4)]

print("\\n=== Vecteur PageRank exact ===")
for i, score in enumerate(pi_score, start=1):
    pct = float(score) * 100
    print(f"Page {i} : score = {score}  ({pct:.2f} %)")

# Vérification formelle P @ pi = pi
pi_mat = Matrix([[p] for p in pi_score])
print("\\nVérification P @ pi == pi :")
display(P @ pi_mat)""")

# ==============================================================================
# PARTIE 4
# ==============================================================================
add_md("""---
## Partie 4 : Géométrie Euclidienne, Factorisation QR et Espaces de Cycles

### 4.1 Décomposition orthogonale du réseau
Revenons à la matrice d'incidence $B \\in \\mathcal{M}_{4,4}(\\mathbb{R})$.
Ses colonnes 1, 2, 3 sont linéairement indépendantes (la 4ème étant combinaison des 3 premières car $B \\mathbf{1} = 0$).
Considérons la sous-matrice de rang plein $A = B[:, :3] \\in \\mathcal{M}_{4,3}(\\mathbb{R})$ :
$$A = \\begin{pmatrix} -1 & 1 & 0 \\\\ 0 & -1 & 1 \\\\ 0 & 0 & -1 \\\\ 0 & -1 & 0 \\end{pmatrix}$$
L'image $\\text{Im}(A)$ correspond à l'espace des différences de potentiel admissibles (**espace des coupures**).
Son orthogonal $(\\text{Im} A)^\\perp = \\ker(A^T)$ correspond à l'**espace des cycles** de Kirchhoff !
""")

add_code("""A_inc = Matrix([[B[i, j] for j in range(3)] for i in range(4)])
print("Sous-matrice de rang plein A (4x3) :")
display(A_inc)
print(f"Rang de A : {A_inc.rank()}")""")

add_md("""### 4.2 Factorisation $A = QR$
Appliquons la procédure `QR` de `linalg_pedagopy` :
""")

add_code("""qr_proj = QR(A_inc).run()
Q = qr_proj.Q
R = qr_proj.R

print("Matrice Q (colonnes orthonormales) :")
display(Q)
print("Matrice R (triangulaire supérieure) :")
display(R)

print("Vérification Q^T @ Q = I_3 :")
display(Q.T @ Q)
print("Vérification Q @ R == A :", Q @ R == A_inc)""")

add_md("""### 4.3 Projecteur sur l'espace des coupures et sur l'espace des cycles
1. Le projecteur orthogonal sur l'espace des coupures $\\text{Im}(A)$ est :
   $$P_{\\text{cut}} = Q Q^T$$
2. Le projecteur orthogonal sur l'espace des cycles est son complémentaire :
   $$P_{\\text{cycle}} = I_4 - P_{\\text{cut}}$$
""")

add_code("""P_cut = Q @ Q.T
print("Projecteur orthogonal sur l'espace des coupures P_cut (4x4) :")
display(P_cut)

I4 = Matrix.identity(4)
P_cycle = I4 - P_cut
print("Projecteur orthogonal sur l'espace des cycles P_cycle (4x4) :")
display(P_cycle)

print(f"Rang de P_cycle : {P_cycle.rank()}")
print("Base de l'espace des cycles :", P_cycle.nullspace())
print("\\n-> Le vecteur directeur du cycle est (0, 1, 1, -1), ce qui correspond exactement à la maille fermée : e2 + e3 - e4 = 0 !")""")

# ==============================================================================
# PARTIE 5
# ==============================================================================
add_md("""---
## Partie 5 : Calibration de Réseau par Moindres Carrés et Pseudoinverse

### 5.1 Données expérimentales bruitées
On effectue des mesures de tensions électriques sur les 4 branches du réseau à l'aide de voltmètres.
À cause du bruit de mesure, les valeurs mesurées ne respectent pas exactement la loi des mailles :
$$y_{\\text{mes}} = \\begin{pmatrix} 2 \\\\ 1 \\\\ 2 \\\\ 4 \\end{pmatrix}$$
On cherche le vecteur de potentiels nodaux $\\hat{x} = (x_1, x_2, x_3)^T$ qui minimise l'erreur quadratique :
$$\\|A x - y_{\\text{mes}}\\|^2 \\longrightarrow \\min$$
""")

add_code("""y_mes = Vector([2, 1, 2, 4])
print("Mesures de tensions bruitées y_mes :", y_mes)""")

add_md("""### 5.2 Résolution avec la procédure `LeastSquares`
Exécutons la procédure `LeastSquares(A, y)` :
""")

add_code("""ls_net = LeastSquares(A_inc, y_mes).run()

print("Potentiels nodaux optimaux x_hat :", ls_net.x_hat)
print("Tensions corrigées ajustées y_hat = A @ x_hat :", ls_net.y_hat)
print("Vecteur résidu r* = y_mes - y_hat :", ls_net.residual)""")

add_md("""### 5.3 Propriété physique fondamentale du résidu
Calculons le résidu $r^* = y_{\\text{mes}} - \\hat{y}$ :
$$r^* = \\begin{pmatrix} 0 \\\\ 1/3 \\\\ 1/3 \\\\ -1/3 \\end{pmatrix} = \\frac{1}{3} \\begin{pmatrix} 0 \\\\ 1 \\\\ 1 \\\\ -1 \\end{pmatrix}$$
**Le résidu de moindres carrés appartient exactement à l'espace des cycles !**
L'écart entre la mesure et le modèle physique est précisément la circulation de tension non nulle autour du cycle.
Vérifions également l'orthogonalité $A^T r^* = 0$ et le théorème de Pythagore :
""")

add_code("""r_star = ls_net.residual
print("Orthogonalité A^T @ r* (doit être nul) :", A_inc.T @ r_star)

# Vérification de Pythagore ||y||^2 = ||y_hat||^2 + ||r*||^2
y_hat = ls_net.y_hat
norm_y2 = y_mes.dot(y_mes)
norm_yhat2 = y_hat.dot(y_hat)
norm_r2 = r_star.dot(r_star)

print(f"\\n||y_mes||^2 = {norm_y2}")
print(f"||y_hat||^2 = {norm_yhat2}")
print(f"||r*||^2    = {norm_r2}")
print("Pythagore : ||y||^2 == ||y_hat||^2 + ||r*||^2 :", norm_y2 == norm_yhat2 + norm_r2)""")

add_md("""### 5.4 Pseudoinverse de Moore-Penrose $A^+$
La pseudoinverse $A^+ = (A^T A)^{-1} A^T$ permet de projeter directement n'importe quel vecteur de mesure sur la solution optimale :
""")

add_code("""print("Pseudoinverse de Moore-Penrose A^+ :")
display(ls_net.pseudoinverse)

# Vérification x_hat = A^+ @ y_mes
x_calc = ls_net.pseudoinverse @ y_mes
print("x_hat via pseudoinverse :", x_calc)
print("Identique à la solution :", x_calc == ls_net.x_hat)""")

# ==============================================================================
# DEFIS OUVERTS
# ==============================================================================
add_md("""---
## Défis Ouverts et Pistes de Recherche Personnelle

Pour aller plus loin dans votre exploration avec `linalg_pedagopy`, voici trois axes d'investigation :

### Défi 1 : Réseau à deux communautés bipolaires
* Construire un réseau à 6 sommets formé de deux triangles $\{1, 2, 3\}$ et $\{4, 5, 6\}$, reliés uniquement par une arête pont entre 3 et 4 de conductance $\\beta$.
* Calculer le Laplacien $L(\\beta)$ et observer comment la deuxième plus petite valeur propre (connectivité algébrique de Fiedler) évolue avec $\\beta$.

### Défi 2 : Régularisation de Tikhonov du Laplacien
* Pour inverser un Laplacien singulier $L$, on introduit souvent la perturbation régularisée $L_\\mu = L + \\mu I_n$ avec $\\mu > 0$.
* Avec `linalg_pedagopy`, inverser formellement $L_\\mu$ en fonction de $\\mu$ et étudier le comportement de $(L + \\mu I)^{-1} b$ quand $\\mu \\to 0$ pour un vecteur source $b$ compatible ($\\sum b_i = 0$).

### Défi 3 : PageRank avec facteur de téléportation $d$
* Modifier la matrice de transition $P$ en introduisant le facteur de téléportation de Brin & Page :
  $$G(d) = d P + \\frac{1-d}{4} J_4$$
  où $J_4$ est la matrice remplie de 1.
* Calculer formellement avec `symbols("d")` la distribution stationnaire $\\pi(d)$ et observer comment les scores des pages convergent vers $1/4$ lorsque $d \\to 0$.
""")

# ==============================================================================
# SAUVEGARDE DU FICHIER NOTEBOOK
# ==============================================================================
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

output_path = "projet_exploration_algebre_lineaire.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Projet généré avec succès dans : {output_path}")
print(f"Nombre total de cellules : {len(cells)}")
