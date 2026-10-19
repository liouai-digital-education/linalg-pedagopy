"""Générateur du notebook Jupyter problemes_exploratoires_linalg_pedagopy.ipynb."""

from __future__ import annotations

import json
from pathlib import Path


def create_notebook() -> None:
    nb = {
        "cells": [],
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

    cell_counter = 0

    def md_cell(text: str) -> dict:
        nonlocal cell_counter
        cell_counter += 1
        lines = [line + "\n" for line in text.strip().split("\n")]
        if lines:
            lines[-1] = lines[-1].rstrip("\n")
        return {
            "cell_type": "markdown",
            "id": f"cell-md-{cell_counter}",
            "metadata": {},
            "source": lines,
        }

    def code_cell(code: str) -> dict:
        nonlocal cell_counter
        cell_counter += 1
        code_clean = code.strip()
        # Validation immédiate de la syntaxe Python
        compile(code_clean, f"cell_{cell_counter}", "exec")
        lines = [line + "\n" for line in code_clean.split("\n")]
        if lines:
            lines[-1] = lines[-1].rstrip("\n")
        return {
            "cell_type": "code",
            "execution_count": None,
            "id": f"cell-code-{cell_counter}",
            "metadata": {},
            "outputs": [],
            "source": lines,
        }

    # =========================================================================
    # TITRE PRINCIPAL & INTRODUCTION
    # =========================================================================
    nb["cells"].append(
        md_cell(
            """# Deux Grands Problèmes Exploratoires d'Algèbre Linéaire
### Modélisation, Calcul Formel Exact, Géométrie et Régularisation avec `linalg_pedagopy` v3.0

Ce notebook propose deux études de cas approfondies et complètes en algèbre linéaire appliquée,
directement inspirées des applications classiques de l'algèbre linéaire.

Chaque problème est une véritable enquête scientifique guidée pas à pas, combinant :
- La **modélisation matricielle** rigoureuse d'un phénomène physique ou informationnel ;
- Le **calcul exact dans $\\mathbb{Q}$** (sans aucune perte de précision numérique) ;
- La **traçabilité arborescente complète** des étapes d'élimination et de projection ;
- La **discussion automatique de cas selon des paramètres formels** (`CaseSplit`) ;
- La mise en évidence des **dangers du calcul flottant IEEE-754** sur des systèmes mal conditionnés.

---

## Sommaire des Problèmes :
1. **Problème 1 — Tomographie Discrète, Images Fantômes et Inversion Régularisée**
   * *Notions clés* : Matrices d'incidence, rang plein en colonnes/lignes, noyau $\\ker(A)$ et composantes non observables (« fantômes »), système sous-déterminé, reconstruction de norme minimale (KKT / pseudo-inverse), régularisation de Tikhonov avec opérateur Laplacien discret, sensibilité au bruit.
2. **Problème 2 — Identification d'un Système Dynamique, Filtrage Spatio-Temporel et Stabilité**
   * *Notions clés* : Séries temporelles et statistiques (RMS, moyenne, centrage, corrélation), matrice de Toeplitz/Hankel des retards, orthogonalisation de Gram-Schmidt rationnelle, factorisation QR exacte, moindres carrés et orthogonalité du résidu ($A^T \\hat{r} = 0$), discussion formelle selon un coefficient de frottement (`CaseSplit`), et rupture d'orthogonalité sur matrice de Läuchli."""
        )
    )

    # Cellule de configuration
    nb["cells"].append(
        code_cell(
            r'''import sys
from pathlib import Path
from fractions import Fraction
import sympy as sp
from IPython.display import display, Markdown, Latex

# Configuration du chemin d'accès vers src/ si non installé en mode éditable
src_path = str(Path.cwd() / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from linalg_pedagopy import (
    Vector, Matrix, symbols, to_exact,
    GaussJordan, BackSubstitution, ForwardSubstitution,
    GramSchmidt, QR, LeastSquares,
    tracing, section, record, config, using_config,
    compare
)
from linalg_pedagopy.tuteur import exercice, glossaire

display(Markdown(f"**Environnement initialisé avec succès.** État du moteur : `{config.state}`"))
'''
        )
    )

    # =========================================================================
    # PROBLÈME 1 : TOMOGRAPHIE DISCRÈTE
    # =========================================================================
    nb["cells"].append(
        md_cell(
            """# Problème 1 — Tomographie Discrète, Images Fantômes et Inversion Régularisée
*(matrices, inverses, moindres carrés, norme minimale)*

### Contexte physique :
Dans un scanner médical ou géophysique à rayons X, un faisceau traverse un milieu d'absorption inconnue.
La loi de Beer-Lambert indique que le logarithme de l'atténuation mesurée par un détecteur est égal à la somme des densités des zones traversées :
$$y_i = \\sum_{j \\in \\text{trajet } i} x_j$$

Nous modélisons un milieu bidimensionnel discrétisé sous la forme d'une grille carrée $3 \\times 3$, soit **9 pixels** numérotés de 1 à 9 :
$$\\begin{bmatrix}
x_1 & x_2 & x_3 \\\\
x_4 & x_5 & x_6 \\\\
x_7 & x_8 & x_9
\\end{bmatrix}$$

Le vecteur inconnu est $x = (x_1, x_2, \\dots, x_9)^T \\in \\mathbb{R}^9$.

Un jeu de capteurs mesure les projections le long de **8 rayons distincts** :
* 3 rayons horizontaux :
  * $R_1 = x_1 + x_2 + x_3$
  * $R_2 = x_4 + x_5 + x_6$
  * $R_3 = x_7 + x_8 + x_9$
* 3 rayons verticaux :
  * $C_1 = x_1 + x_4 + x_7$
  * $C_2 = x_2 + x_5 + x_8$
  * $C_3 = x_3 + x_6 + x_9$
* 2 rayons diagonaux principaux :
  * $D_1 = x_1 + x_5 + x_9$
  * $D_2 = x_3 + x_5 + x_7$

Le système d'observation est modélisé par :
$$A x = b, \\quad A \\in \\mathbb{R}^{8 \\times 9}, \\quad b \\in \\mathbb{R}^8$$"""
        )
    )

    # Problème 1 - Partie A
    nb["cells"].append(
        md_cell(
            """### Partie 1.A — Construction de la Matrice d'Observation $A$

Construisons la matrice d'incidence $A$ dont chaque ligne représente l'équation d'un rayon."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Construction de la matrice de tomographie A (8 mesures x 9 pixels)
# Pixels : 1  2  3  4  5  6  7  8  9
A_tomo = Matrix([
    [1, 1, 1, 0, 0, 0, 0, 0, 0],  # R1 (ligne 1)
    [0, 0, 0, 1, 1, 1, 0, 0, 0],  # R2 (ligne 2)
    [0, 0, 0, 0, 0, 0, 1, 1, 1],  # R3 (ligne 3)
    [1, 0, 0, 1, 0, 0, 1, 0, 0],  # C1 (colonne 1)
    [0, 1, 0, 0, 1, 0, 0, 1, 0],  # C2 (colonne 2)
    [0, 0, 1, 0, 0, 1, 0, 0, 1],  # C3 (colonne 3)
    [1, 0, 0, 0, 1, 0, 0, 0, 1],  # D1 (diagonale descendante)
    [0, 0, 1, 0, 1, 0, 1, 0, 0],  # D2 (diagonale montante)
])

display(Markdown(r"**Matrice d'observation tomographique $A \in \mathbb{R}^{8 \times 9}$ :**"))
display(A_tomo)
display(Markdown(f"- **Dimensions de $A$ :** `{A_tomo.shape}` (8 équations, 9 inconnues)"))
'''
        )
    )

    # Problème 1 - Partie B
    nb["cells"].append(
        md_cell(
            """### Partie 1.B — Réduction de Gauss-Jordan et « Images Fantômes » (Noyau $\\ker(A)$)

Une propriété fondamentale de la tomographie est l'existence éventuelle de **fantômes de tomographie** (*ghost components*) :
ce sont des motifs de densité non nuls $v \\in \\ker(A)$ tels que $A v = 0$.
Ces motifs sont **totalement invisibles** aux rayons X considérés.

Analysons la structure du noyau et le rang de $A$ via `GaussJordan` sur un second membre nul."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Analyse du système homogène A x = 0 pour trouver le noyau ker(A)
b_zero = Vector.zeros(8)
res_homogene = GaussJordan(A_tomo, b_zero).run()

display(Markdown(f"""### Analyse du rang et du noyau :
- **Nombre d'inconnues (pixels) :** $n = 9$
- **Rang de la matrice :** $\\operatorname{{rang}}(A) = {res_homogene.rank}$
- **Dimension du noyau (théorème du rang) :** $\\dim \\ker(A) = 9 - {res_homogene.rank} = {9 - res_homogene.rank}$
- **Colonnes pivots :** {res_homogene.pivots}"""))

display(res_homogene.solution)
'''
        )
    )

    nb["cells"].append(
        md_cell(
            """#### Interprétation physique des vecteurs de base du noyau :
Le noyau est de dimension 2. Visualisons ces deux vecteurs sous forme de grilles $3 \\times 3$ pour comprendre leur géométrie."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''v_ghost1, v_ghost2 = res_homogene.solution.basis

# Mise en forme 3x3 des deux fantômes
G1 = Matrix([
    [v_ghost1[0], v_ghost1[1], v_ghost1[2]],
    [v_ghost1[3], v_ghost1[4], v_ghost1[5]],
    [v_ghost1[6], v_ghost1[7], v_ghost1[8]]
])

G2 = Matrix([
    [v_ghost2[0], v_ghost2[1], v_ghost2[2]],
    [v_ghost2[3], v_ghost2[4], v_ghost2[5]],
    [v_ghost2[6], v_ghost2[7], v_ghost2[8]]
])

display(Markdown(r"**Premier fantôme de tomographie $G_1$ (grille $3 \times 3$) :**"))
display(G1)
display(Markdown(r"**Second fantôme de tomographie $G_2$ (grille $3 \times 3$) :**"))
display(G2)

# Vérifions explicitement que la projection de G1 sur tous les rayons est nulle :
rayons_G1 = A_tomo @ v_ghost1
display(Markdown(f"- **Vérification $A v_{{\\text{{ghost1}}}} = 0$ :** `{rayons_G1.is_zero()}`"))
'''
        )
    )

    # Problème 1 - Partie C
    nb["cells"].append(
        md_cell(
            """### Partie 1.C — Reconstruction d'une Image Test et Inversion de Norme Minimale

Supposons qu'un objet réel présente la distribution de densité suivante :
$$x_{\\text{vrai}} = \\begin{bmatrix}
2 & 0 & 1 \\\\
0 & 3 & 0 \\\\
1 & 0 & 2
\\end{bmatrix} \\implies x_{\\text{vrai}} = (2, 0, 1, 0, 3, 0, 1, 0, 2)^T$$

1. Calculons le vecteur de mesures exactes $b = A x_{\\text{vrai}}$.
2. Résolvons le système sous-déterminé $A x = b$.
3. Cherchons la **solution de norme minimale** :
   $$\\min_{x} \\|x\\|^2 \\quad \\text{sous la contrainte } A x = b$$
   Cette solution correspond à la pseudo-inverse et élimine toute composante superflue dans le noyau."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 1. Génération des mesures exactes
x_vrai = Vector([2, 0, 1, 0, 3, 0, 1, 0, 2])
b_mesure = A_tomo @ x_vrai

display(Markdown(r"**Densité réelle $x_{\text{vrai}}$ :**"))
display(Matrix([[2, 0, 1], [0, 3, 0], [1, 0, 2]]))

display(Markdown(r"**Vecteur de mesures $b = A x_{\text{vrai}} \in \mathbb{R}^8$ :**"))
display(b_mesure)

# 2. Résolution complète par Gauss-Jordan
res_tomo = GaussJordan(A_tomo, b_mesure).run()
display(Markdown("### Ensemble des solutions compatibles :"))
display(res_tomo.solution)
'''
        )
    )

    nb["cells"].append(
        md_cell(
            """#### Calcul de la solution de norme minimale via le système KKT :
Le problème d'optimisation quadratique sous contrainte d'égalité :
$$\\min_x \\frac{1}{2} \\|x\\|^2 \\quad \\text{s.c.} \\quad A x = b$$
admet les conditions d'optimalité KKT suivantes avec le multiplicateur de Lagrange $\\nu \\in \\mathbb{R}^8$ :
$$\\begin{cases}
x^* + A^T \\nu = 0 \\implies x^* = -A^T \\nu \\\\
A x^* = b \\implies -A A^T \\nu = b
\\end{cases}$$
Comme $A$ n'est pas de rang plein en lignes (rang 7 pour 8 lignes, car $\\sum R_i = \\sum C_i$),
la mesure $C_3$ (indice 5) est linéairement dépendante : $C_3 = (R_1 + R_2 + R_3) - (C_1 + C_2)$.
Les 7 lignes indépendantes sont obtenues par les pivots de $A^T$ : indices $(0, 1, 2, 3, 4, 6, 7)$."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Sélection des 7 lignes indépendantes de A via les pivots de A^T
pivots_rows = GaussJordan(A_tomo.T, Vector.zeros(9)).run().pivots
display(Markdown(f"**Indices des 7 lignes indépendantes de $A$ :** `{pivots_rows}`"))

A_sub = Matrix([A_tomo[i] for i in pivots_rows])
b_sub = Vector([b_mesure[i] for i in pivots_rows])

# Matrice de Gram des mesures : G_mes = A_sub @ A_sub.T (7x7 inversible)
G_mes = A_sub @ A_sub.T
G_mes_inv = G_mes.inv()

# Multiplicateur nu = G_mes_inv @ b_sub, puis x_min = A_sub.T @ nu
nu = G_mes_inv @ b_sub
x_min_norm = A_sub.T @ nu

display(Markdown(r"**Solution de norme minimale $x^* = A_{\text{sub}}^T (A_{\text{sub}} A_{\text{sub}}^T)^{-1} b_{\text{sub}}$ :**"))
display(x_min_norm)

display(Markdown(f"""- **Norme de la solution réelle $\\|x_{{\\text{{vrai}}}}\\|$ :** ${sp.latex(x_vrai.norm())} \\approx {float(x_vrai.norm()):.4f}$
- **Norme de la solution optimale $\\|x^*\\|$ :** ${sp.latex(x_min_norm.norm())} \\approx {float(x_min_norm.norm()):.4f}$
- **Vérification de la contrainte $A x^* = b$ sur les 8 rayons :** `{(A_tomo @ x_min_norm == b_mesure)}`"""))
'''
        )
    )

    # Problème 1 - Partie D
    nb["cells"].append(
        md_cell(
            """### Partie 1.D — Régularisation de Tikhonov et Lissage Spatial (Opérateur Laplacien)

Bien que $x^*$ vérifie parfaitement les équations de mesure $A x^* = b$, la solution de norme minimale présente
des valeurs fractionnaires et des oscillations typiques dues au manque de contrainte spatiale.

En pratique médicale, une image réelle est généralement **lisse** : deux pixels voisins ont des densités proches.
Pour pénaliser les fortes variations entre pixels adjacents, introduisons la matrice de différence spatiale $D$ (différences horizontales et verticales) :
* Pour chaque paire de voisins horizontaux $(x_j, x_{j+1})$ : $x_j - x_{j+1} \\approx 0$
* Pour chaque paire de voisins verticaux $(x_j, x_{j+3})$ : $x_j - x_{j+3} \\approx 0$

Il y a 6 paires horizontales et 6 paires verticales, soit 12 différences.
Le problème régularisé de Tikhonov s'écrit :
$$\\min_{x} \\|A x - b\\|^2 + \\lambda \\|D x\\|^2 = \\min_{x} \\left\\| \\begin{bmatrix} A \\\\ \\sqrt{\\lambda} D \\end{bmatrix} x - \\begin{bmatrix} b \\\\ 0 \\end{bmatrix} \\right\\|^2$$

Posons $\\lambda = 1$ ($\\,\\sqrt{\\lambda} = 1$). Résolvons ce problème par moindres carrés exacts via `LeastSquares` !"""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Matrice de différences spatiales D (12 contraintes de lissage x 9 pixels)
# Paires horizontales : (1,2), (2,3), (4,5), (5,6), (7,8), (8,9)
# Paires verticales   : (1,4), (2,5), (3,6), (4,7), (5,8), (6,9)

def diff_row(idx1, idx2):
    row = [0] * 9
    row[idx1 - 1] = 1
    row[idx2 - 1] = -1
    return row

D_lignes = [
    diff_row(1, 2), diff_row(2, 3),
    diff_row(4, 5), diff_row(5, 6),
    diff_row(7, 8), diff_row(8, 9),
    diff_row(1, 4), diff_row(2, 5), diff_row(3, 6),
    diff_row(4, 7), diff_row(5, 8), diff_row(6, 9),
]
D_smooth = Matrix(D_lignes)

# Matrice empilée A_reg = [A ; D] (20 lignes x 9 colonnes)
# Second membre empilé b_reg = [b ; 0] (20 composantes)
A_reg_rows = [A_tomo[i] for i in range(8)] + [D_smooth[j] for j in range(12)]
A_reg = Matrix(A_reg_rows)
b_reg = Vector([b_mesure[i] for i in range(8)] + [0] * 12)

display(Markdown(f"**Matrice de Tikhonov $A_{{\\text{{reg}}}}$ empilée :** taille `{A_reg.shape}`"))

# Résolution exacte par QR rationnelle sans radicaux
ls_tikhonov = LeastSquares(A_reg, b_reg, method="rational_qr").run()

display(Markdown(r"**Solution régularisée de Tikhonov $\hat{x}_{\text{smooth}}$ :**"))
display(ls_tikhonov.x_hat)

# Mise en forme sous forme de grille 3x3 :
x_hat_tomo = ls_tikhonov.x_hat
M_smooth = Matrix([
    [x_hat_tomo[0], x_hat_tomo[1], x_hat_tomo[2]],
    [x_hat_tomo[3], x_hat_tomo[4], x_hat_tomo[5]],
    [x_hat_tomo[6], x_hat_tomo[7], x_hat_tomo[8]]
])
display(Markdown(r"**Image reconstruite lissée (grille $3 \times 3$) :**"))
display(M_smooth)

display(Markdown("### Contrôle géométrique d'orthogonalité du résidu ($A_{\\text{reg}}^T \\hat{r} = 0$) :"))
display(ls_tikhonov.verify())
'''
        )
    )

    # Problème 1 - Synthèse
    nb["cells"].append(
        md_cell(
            """### Synthèse du Problème 1 :
1. **Sous-détermination & Rang** : Un système avec moins de mesures indépendantes que d'inconnues admet un espace de solutions affine.
2. **Fantômes** : Le noyau $\\ker(A)$ décrit exactement les structures imperceptibles aux capteurs.
3. **Optimisation sous contrainte** : Le critère de norme minimale $\\min \\|x\\|^2$ choisit l'antécédent orthogonal au noyau.
4. **Régularisation spatiale** : L'introduction d'un opérateur de lissage $D$ résout le compromis entre fidélité aux données et régularité physique."""
        )
    )

    # =========================================================================
    # PROBLÈME 2 : IDENTIFICATION DYNAMIQUE ET CONDITIONNEMENT
    # =========================================================================
    nb["cells"].append(
        md_cell(
            """---
# Problème 2 — Identification d'un Système Dynamique, Filtrage et Conditionnement
*(statistiques, convolution, produit matriciel, inverses, moindres carrés régularisés)*

### Contexte :
On observe l'évolution temporelle d'un système oscillant amorti soumis à un forçage extérieur.
L'état scalaire $y_t$ mesuré aux instants discrets $t = 1, 2, \\dots, T$ obéit à une loi autorégressive d'ordre 2 avec forçage :
$$y_t = \\alpha_1 y_{t-1} + \\alpha_2 y_{t-2} + \\beta \\cos(\\omega t) + c + \\varepsilon_t$$

Les paramètres physiques inconnus sont :
* $\\alpha_1, \\alpha_2$ : coefficients de la dynamique libre (amortissement et pulsation propre) ;
* $\\beta$ : amplitude de couplage avec le signal excitateur ;
* $c$ : niveau moyen ou dérive (*offset*).

Le vecteur des paramètres à estimer est :
$$\\theta = (\\alpha_1, \\alpha_2, \\beta, c)^T \\in \\mathbb{R}^4$$"""
        )
    )

    # Problème 2 - Partie A
    nb["cells"].append(
        md_cell(
            """### Partie 2.A — Série temporelle et métriques statistiques

Considérons une séquence de $T = 8$ observations exactes rationnelles :
$$y = (1, \\frac{3}{2}, 2, \\frac{7}{4}, 1, \\frac{1}{4}, 0, \\frac{1}{2})^T$$

Calculons les métriques statistiques avec `Vector`."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Série temporelle des observations réelles y (taille 8)
y_serie = Vector([1, Fraction(3, 2), 2, Fraction(7, 4), 1, Fraction(1, 4), 0, Fraction(1, 2)])

display(Markdown(f"""### Métriques statistiques de la série temporelle :
- **Moyenne arithmétique $\\operatorname{{avg}}(y)$ :** ${sp.latex(y_serie.avg())}$
- **Vecteur centré $\\tilde{{y}} = \\operatorname{{demean}}(y)$ :**"""))
display(y_serie.demean())

display(Markdown(f"""- **Norme euclidienne $\\|y\\|$ :** ${sp.latex(y_serie.norm())}$
- **Moyenne quadratique $\\operatorname{{rms}}(y)$ :** ${sp.latex(y_serie.rms())}$
- **Écart type $\\operatorname{{std}}(y) = \\operatorname{{rms}}(\\tilde{{y}})$ :** ${sp.latex(y_serie.std())}$"""))
'''
        )
    )

    # Problème 2 - Partie B
    nb["cells"].append(
        md_cell(
            """### Partie 2.B — Matrice de Régression Dynamique et Dépendance Linéaire

Pour estimer $\\theta$ aux instants $t = 3, 4, 5, 6, 7, 8$ ($N = 6$ observations effectives),
formons la matrice des caractéristiques $X \\in \\mathbb{R}^{6 \\times 4}$ et le second membre $y_{\\text{cible}} \\in \\mathbb{R}^6$ :
$$X_t = \\begin{bmatrix} y_{t-1} & y_{t-2} & \\cos(\\omega t) & 1 \\end{bmatrix}, \\quad y_{\\text{cible}, t} = y_t$$

Prenons pour la composante périodique $\\omega = \\pi/2$, de sorte que $\\cos(\\pi/2 \\cdot t)$ prend les valeurs périodiques exactes $(-1, 0, 1, 0)$.
Testons l'indépendance linéaire des colonnes avec `GramSchmidt`."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Construction de la matrice des descripteurs X pour t = 3, 4, 5, 6, 7, 8
# t=3: y2=3/2, y1=1,   cos(3*pi/2)=0,  1
# t=4: y3=2,   y2=3/2, cos(4*pi/2)=1,  1
# t=5: y4=7/4, y3=2,   cos(5*pi/2)=0,  1
# t=6: y5=1,   y4=7/4, cos(6*pi/2)=-1, 1
# t=7: y6=1/4, y5=1,   cos(7*pi/2)=0,  1
# t=8: y7=0,   y6=1/4, cos(8*pi/2)=1,  1

X_dyn = Matrix([
    [Fraction(3, 2), 1,              0, 1],
    [2,              Fraction(3, 2), 1, 1],
    [Fraction(7, 4), 2,              0, 1],
    [1,              Fraction(7, 4), -1, 1],
    [Fraction(1, 4), 1,              0, 1],
    [0,              Fraction(1, 4), 1, 1],
])

y_cible = Vector([2, Fraction(7, 4), 1, Fraction(1, 4), 0, Fraction(1, 2)])

display(Markdown(r"**Matrice des régresseurs $X \in \mathbb{R}^{6 \times 4}$ :**"))
display(X_dyn)

# Test de liberté des colonnes de X via Gram-Schmidt rationnel
colonnes_X = [Vector([X_dyn[i, j] for i in range(6)]) for j in range(4)]
res_gs = GramSchmidt(colonnes_X, normalize="end").run()

display(Markdown(f"""### Test de liberté par Gram-Schmidt :
- **Les 4 colonnes forment-elles une famille libre ?** `{res_gs.independent}`
- **Condition de rang plein en colonnes :** $\\operatorname{{rang}}(X) = 4$"""))
'''
        )
    )

    # Problème 2 - Partie C
    nb["cells"].append(
        md_cell(
            """### Partie 2.C — Factorisation QR et Ajustement aux Moindres Carrés

Puisque $X$ est de rang plein en colonnes, le problème des moindres carrés :
$$\\min_{\\theta} \\|X \\theta - y_{\\text{cible}}\\|^2$$
admet une solution unique $\\hat{\\theta} = (X^T X)^{-1} X^T y_{\\text{cible}}$.

Résolvons ce problème par la factorisation QR rationnelle (`method="rational_qr"`).
Cette méthode calcule la solution exacte dans $\\mathbb{Q}$ sans aucune racine carrée intermédiaire !"""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Résolution exacte par Moindres Carrés
ls_dyn = LeastSquares(X_dyn, y_cible, method="rational_qr").run()

theta_hat = ls_dyn.x_hat
display(Markdown(r"**Paramètres identifiés $\hat{\theta} = (\hat{\alpha}_1, \hat{\alpha}_2, \hat{\beta}, \hat{c})^T$ :**"))
display(theta_hat)

display(Markdown(f"""### Détail des coefficients physiques :
- $\\hat{{\\alpha}}_1$ (coefficient d'ordre 1) : **${sp.latex(theta_hat[0])}$**
- $\\hat{{\\alpha}}_2$ (coefficient d'ordre 2) : **${sp.latex(theta_hat[1])}$**
- $\\hat{{\\beta}}$ (amplitude du forçage) : **${sp.latex(theta_hat[2])}$**
- $\\hat{{c}}$ (constante / dérive) : **${sp.latex(theta_hat[3])}$**

### Qualité d'ajustement :
- **Norme du résidu $\\|\\hat{{r}}\\|$ :** ${sp.latex(ls_dyn.residual_norm)} \\approx {float(ls_dyn.residual_norm):.5f}$
- **Moyenne quadratique $\\operatorname{{rms}}(\\hat{{r}})$ :** ${sp.latex(ls_dyn.residual_rms)} \\approx {float(ls_dyn.residual_rms):.5f}$"""))

display(Markdown("### Vérification du principe d'orthogonalité ($X^T \\hat{r} = 0$) :"))
display(ls_dyn.verify())
'''
        )
    )

    # Problème 2 - Partie D
    nb["cells"].append(
        md_cell(
            """### Partie 2.D — Discussion Paramétrique selon un Coefficient de Frottement $a$ (`CaseSplit`)

Dans l'analyse physique, le coefficient de frottement du système n'est pas toujours constant : il dépend d'un paramètre réel $a$.
La matrice de transition dynamique du système simplifié s'écrit :
$$T(a) = \\begin{bmatrix}
1 & a & 0 \\\\
0 & 1 & a \\\\
a & 0 & 1
\\end{bmatrix}, \\quad b_{\\text{forc}} = \\begin{bmatrix} 1 \\\\ 0 \\\\ 1 \\end{bmatrix}$$

Le déterminant formel de cette matrice est :
$$\\det(T(a)) = 1 + a^3 = (1 + a)(1 - a + a^2)$$
Sur $\\mathbb{R}$, la matrice devient singulière lorsque $a = -1$.

Utilisons `GaussJordan` sur ce système symbolique pour obtenir la discussion automatique complète (`CaseSplit`)."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Déclaration formelle du paramètre réel 'a'
a, = symbols("a")

T_param = Matrix([
    [1, a, 0],
    [0, 1, a],
    [a, 0, 1]
])
b_param = Vector([1, 0, 1])

# Résolution avec capture des embranchements formels
cs_dyn = GaussJordan(T_param, b_param).run()

display(Markdown("### Discussion automatique complète selon le paramètre $a$ :"))
display(cs_dyn)
'''
        )
    )

    nb["cells"].append(
        md_cell(
            """#### Évaluation numérique sur chaque branche :
* **Branche générique ($a \\neq -1$)** : le système admet une solution unique dépendant rationnellement de $a$.
* **Branche singulière ($a = -1$)** : étudions la compatibilité."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Cas 1 : a = 2 (régime d'amortissement standard)
sol_regime2 = cs_dyn.at(a=2)
display(Markdown(r"**Solution pour $a = 2$ :**"))
display(sol_regime2.solution)

# Cas 2 : a = -1 (régime critique / résonance)
sol_critique = cs_dyn.at(a=-1)
display(Markdown(r"**Comportement au point critique $a = -1$ :**"))
display(sol_critique.solution)
'''
        )
    )

    # Problème 2 - Partie E
    nb["cells"].append(
        md_cell(
            r"""### Partie 2.E — Défaillance Catastrophique du Calcul Flottant sur Matrice Mal Conditionnée

Lorsque l'échantillonnage temporel devient très rapproché ($\Delta t \to 0$), les colonnes de la matrice des retards
deviennent presque proportionnelles. Cette situation est modélisée par la **matrice de Läuchli** :
$$A_\varepsilon = \begin{bmatrix}
1 & 1 & 1 \\
\varepsilon & 0 & 0 \\
0 & \varepsilon & 0 \\
0 & 0 & \varepsilon
\end{bmatrix}, \quad \varepsilon = 10^{-8}$$

En calcul flottant standard IEEE-754 (`float64`, environ 16 chiffres significatifs de précision) :
$$\varepsilon^2 = 10^{-16} \implies 1 + \varepsilon^2 = 1 \quad \text{(arrondi machine !)}$$

Comparons la méthode des équations normales ($A^T A x = A^T b$) en flottant avec l'inversion exacte de `linalg_pedagopy` :"""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Expérimentation comparative de l'échec numérique
from linalg_pedagopy.compare import lauchli_least_squares_experiment, lauchli_gram_schmidt_experiment

display(Markdown(r"### 1. Perte d'orthogonalité de Gram-Schmidt sur la matrice de Läuchli ($\varepsilon = 10^{-8}$) :"))
display(Markdown(f"```text\n{lauchli_gram_schmidt_experiment(epsilon=1e-8)}\n```"))

display(Markdown(r"### 2. Échec des équations normales en flottant vs QR exacte :"))
display(Markdown(f"```text\n{lauchli_least_squares_experiment(epsilon=1e-8)}\n```"))
'''
        )
    )

    # Problème 2 - Synthèse
    nb["cells"].append(
        md_cell(
            """### Synthèse du Problème 2 :
1. **Régression autorégressive** : L'ajustement AR($p$) se formule naturellement comme un problème de moindres carrés surdéterminé.
2. **Arithmétique rationnelle exacte** : La factorisation QR rationnelle évite les erreurs d'arrondi tout en garantissant $X^T \\hat{r} = 0$.
3. **Disjonction de cas formelle** : Les bifurcations physiques (amortissement vs résonance) sont révélées par l'analyse paramétrique `CaseSplit`.
4. **Précision machine** : Les équations normales $A^T A$ peuvent perdre tout leur rang en flottant (`float64`), alors que les méthodes formelles et QR conservent la solution exacte."""
        )
    )

    # Conclusion générale
    nb["cells"].append(
        md_cell(
            """---
## Conclusion Générale et Bilan Pédagogique

Ces deux problèmes illustrent comment `linalg_pedagopy` réconcilie :
* La **rigueur formelle** des mathématiques pures (démonstrations exactes, noyaux, conditions KKT, discussion de paramètres) ;
* La **puissance applicative** de l'algèbre linéaire moderne (imagerie tomographique, filtrage dynamique, moindres carrés régularisés) ;
* La **traçabilité pédagogique totale**, permettant à l'étudiant de comprendre chaque pivot, chaque projection et chaque résidu."""
        )
    )

    # Écriture du fichier notebook
    target_path = Path("problemes_exploratoires_linalg_pedagopy.ipynb")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)

    print(f"Notebook généré et validé avec succès : {target_path.resolve()}")


if __name__ == "__main__":
    create_notebook()
