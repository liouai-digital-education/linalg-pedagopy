"""Générateur du notebook Jupyter tutoriel_linalg_pedagopy.ipynb avec validation stricte."""

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

    # 1. Header
    nb["cells"].append(
        md_cell(
            """# Tutoriel interactif — `linalg_pedagopy` v3.0

Ce notebook propose une prise en main complète et interactive du package **`linalg_pedagopy` v3.0**.
Il est fondé sur l'ouvrage *Introduction to Applied Linear Algebra — Vectors, Matrices, and Least Squares (VMLS)* de Stephen Boyd et Lieven Vandenberghe.

---

### Objectifs d'apprentissage :
1. **Comprendre le calcul formel exact sur $\\mathbb{R}$** sans perte de précision, avec l'oracle de nullité à 4 verdicts (`ZeroOracle`).
2. **Manipuler les vecteurs et matrices immuables** (`Vector`, `Matrix`) et leurs métriques pédagogiques (RMS, moyenne, centrage, écart-type VMLS, angle avec Cauchy-Schwarz).
3. **Explorer les 4 points de vue du produit matriciel** (coefficients, lignes, colonnes, produits extérieurs).
4. **Résoudre des systèmes linéaires** par réduction de Gauss-Jordan (`GaussJordan`), avec choix du pivot le plus simple et extraction d'ensembles de solutions typés (`UniqueSolution`, `AffineSolution`, `EmptySolution`).
5. **Maîtriser la discussion automatique selon des paramètres** (`CaseSplit`).
6. **Effectuer des résolutions triangulaires** par substitution arrière (`BackSubstitution`) et avant (`ForwardSubstitution`).
7. **Orthogonaliser des familles de vecteurs** par Gram-Schmidt rationnel ou normalisé (`GramSchmidt`), détecter les liaisons linéaires avec témoin exact, et factoriser sous forme $A = QR$ (`QR`).
8. **Résoudre des problèmes de moindres carrés** (`LeastSquares`) en arithmétique rationnelle exacte et vérifier la condition géométrique $A^T \\hat{r} = 0$.
9. **Tester les limites du calcul flottant machine** face au calcul exact avec le module `compare` (matrice de Läuchli, conditionnement de Hilbert).
10. **Pratiquer sur les exercices du recueil officiel de VMLS** grâce au **Tuteur interactif** (`tuteur`)."""
        )
    )

    # 2. Imports & Configuration
    nb["cells"].append(
        md_cell(
            """## 1. Importation et Configuration du Package

Nous importons les composants de `linalg_pedagopy` ainsi que les utilitaires d'affichage riche de Jupyter (`display`, `Markdown`, `Latex`).
Dans Jupyter, `display(...)` combiné aux objets du package active le rendu natif en **Markdown** et **LaTeX MathJax**."""
        )
    )

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

display(Markdown(f"**`linalg_pedagopy` initialisé avec succès !** Version / État : `{config.state}`"))
'''
        )
    )

    # 3. Vecteurs
    nb["cells"].append(
        md_cell(
            """## 2. Vecteurs et Métriques de VMLS (`Vector`)

Les objets `Vector` représentent des vecteurs colonnes $n \\times 1$ strictement **immuables** à coefficients exacts.
Ils s'affichent automatiquement sous forme de matrice colonne LaTeX MathJax dans Jupyter."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 2.1 Construction de vecteurs à coefficients exacts (fractions, radicaux)
v1 = Vector([1, "1/3", Fraction(5, 2), sp.sqrt(2)])

display(Markdown(r"**Vecteur $v_1$ (rendu LaTeX MathJax) :**"))
display(v1)
display(Markdown(f"- **Taille :** {len(v1)}\n- **Forme matricielle :** `{v1.shape}`"))

# Vecteurs canoniques et particuliers
zero_3 = Vector.zeros(3)
ones_3 = Vector.ones(3)
e2 = Vector.unit(1, 4)  # 2e vecteur canonique dans R^4 (indice 0-based)

display(Markdown(r"**Vecteur canonique $e_2 \in \mathbb{R}^4$ :**"))
display(e2)
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 2.2 Opérations algébriques et combinaisons linéaires
a = Vector([1, 2, 3])
b = Vector([4, -1, 2])

display(Markdown(r"**Addition $a + b$ :**"))
display(a + b)

display(Markdown(r"**Multiplication par un scalaire $3a$ :**"))
display(3 * a)

# Combinaison linéaire tracée : 2*a - 3*b
comb = Vector.combination([a, b], [2, -3])
display(Markdown(r"**Combinaison linéaire $2a - 3b$ :**"))
display(comb)
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 2.3 Métriques statistiques et géométriques de VMLS (ch. 1 & 3)
x = Vector([1, -2, 3, 2])
y = Vector([2, 1, 0, 1])

display(Markdown(f"""### Métriques statistiques de $x$ (VMLS ch. 1 & 3)
- **Moyenne arithmétique $\\mathrm{{avg}}(x)$ :** ${sp.latex(x.avg())}$
- **Vecteur centré $\\tilde{{x}} = \\mathrm{{demean}}(x)$ :**"""))
display(x.demean())

display(Markdown(f"""- **Norme euclidienne $\\|x\\|$ :** ${sp.latex(x.norm())}$
- **Moyenne quadratique $\\mathrm{{rms}}(x)$ :** ${sp.latex(x.rms())}$
- **Écart-type VMLS $\\mathrm{{std}}(x)$ :** ${sp.latex(x.std())}$

### Relations géométriques entre $x$ et $y$
- **Produit scalaire $x^T y$ :** ${sp.latex(x.dot(y))}$
- **Distance $\\|x - y\\|$ :** ${sp.latex(x.distance(y))}$
- **Angle $\\theta$ :** ${sp.latex(x.angle(y))} \\text{{ rad}}$
- **Coefficient de corrélation $\\rho(x, y)$ :** ${sp.latex(x.correlation(y))}$"""))
'''
        )
    )

    # 4. Matrices et les 4 vues
    nb["cells"].append(
        md_cell(
            """## 3. Matrices et les 4 Points de Vue du Produit Matriciel (`Matrix`)

Dans le chapitre 10 de VMLS, le produit de matrices $A B$ est interprété de 4 manières équivalentes et complémentaires :
1. **Par coefficients** (`entries`) : produits scalaires ligne · colonne.
2. **Par lignes** (`rows`) : chaque ligne de $A B$ est combinaison linéaire des lignes de $B$.
3. **Par colonnes** (`columns`) : chaque colonne de $A B$ est combinaison linéaire des colonnes de $A$.
4. **Par produits extérieurs** (`outer`) : somme de $k$ matrices de rang 1 $a_i b_i^T$."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 3.1 Création et produit de matrices
A = Matrix([
    [1, 2],
    [3, 4],
    [5, 6]
])

B = Matrix([
    [2, -1],
    [0, 3]
])

display(Markdown(r"**Matrice $A$ ($3 \times 2$) :**"))
display(A)
display(Markdown(r"**Matrice $B$ ($2 \times 2$) :**"))
display(B)
display(Markdown(r"**Produit matriciel $A B$ ($3 \times 2$) :**"))
display(A @ B)
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 3.2 Visualisation des 4 vues pédagogiques du produit matriciel
for vue in ("entries", "rows", "columns", "outer"):
    with tracing(level=2) as t:
        _ = A.matmul(B, view=vue)
    display(Markdown(f"### Vue : `{vue}`"))
    display(t.tree)
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 3.3 Transposée, Matrice de Gram et Blocs
display(Markdown(r"**Transposée $A^T$ :**"))
display(A.T)

# Matrice de Gram G = A^T A (VMLS ch. 10)
G = A.gram()
display(Markdown(r"**Matrice de Gram $G = A^T A$ :**"))
display(G)

# Matrice par blocs
M_bloc = Matrix.block([
    [B, Matrix.zeros(2, 2)],
    [Matrix.identity(2), B]
])
display(Markdown(r"**Matrice par blocs $4 \times 4$ :**"))
display(M_bloc)
'''
        )
    )

    # 5. Gauss-Jordan
    nb["cells"].append(
        md_cell(
            """## 4. Systèmes Linéaires et Élimination de Gauss-Jordan (`GaussJordan`)

`GaussJordan` réduit une matrice augmentée $[A \\mid b]$ à sa forme échelonnée réduite, avec :
- Le choix du **pivot le plus simple** (±1, petit entier, rationnel de petite hauteur) (**D11**) ;
- Des résultats rigoureusement typés : `UniqueSolution`, `AffineSolution` ou `EmptySolution` (**D8**) ;
- Des vérifications automatiques *a posteriori* (`res.verify()`)."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 4.1 Système avec solution unique
A = Matrix([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
b = Vector([8, -11, -3])

res_gj = GaussJordan(A, b).run()

display(Markdown(f"""### Résultat de Gauss-Jordan :
- **Rang de $A$ :** {res_gj.rank}
- **Colonnes pivots :** {res_gj.pivots}"""))
display(res_gj.solution)

display(Markdown("### Trace complète de la réduction (niveau 2 — pas à pas) :"))
display(res_gj.explain(level=2))

display(Markdown("### Contrôle a posteriori :"))
display(res_gj.verify())
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 4.2 Système sous-déterminé (Ensemble affine de solutions)
A_aff = Matrix([[1, 2, -1], [2, 4, -2]])
b_aff = Vector([3, 6])

res_aff = GaussJordan(A_aff, b_aff).run()

display(Markdown(f"**Type de solution :** `{type(res_aff.solution).__name__}`"))
display(res_aff.solution)

# Évaluation d'une solution pour des paramètres donnés t1=2, t2=1
x_part = res_aff.solution.at_params(2, 1)
display(Markdown(r"**Solution particulière pour $t_1 = 2, t_2 = 1$ :**"))
display(x_part)
ok_part = (A_aff @ x_part == b_aff)
display(Markdown(f"- **Vérification $A x_\\text{{part}} == b$ :** `{ok_part}`"))
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 4.3 Système incompatible (Ensemble vide)
A_inc = Matrix([[1, 2], [2, 4]])
b_inc = Vector([3, 7])

res_inc = GaussJordan(A_inc, b_inc).run()
display(res_inc.solution)
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 4.4 Inversion formelle d'une matrice
A_inv = Matrix([[1, 2], [3, 5]])
inv_result = A_inv.inv()

display(Markdown(r"**Matrice initiale $A$ :**"))
display(A_inv)
display(Markdown(r"**Matrice inverse $A^{-1}$ :**"))
display(inv_result)
is_id = (A_inv @ inv_result == Matrix.identity(2))
display(Markdown(f"- **Vérification $A A^{{-1}} == I_2$ :** `{is_id}`"))
'''
        )
    )

    # 6. CaseSplit
    nb["cells"].append(
        md_cell(
            """## 5. Discussion Automatique selon des Paramètres (`CaseSplit`)

Lorsqu'un pivot ou un test de compatibilité dépend d'un paramètre, l'algorithme produit un objet `CaseSplit`
qui distingue automatiquement les cas génériques et les cas particuliers (**D4**)."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Déclaration d'un paramètre formel réel 'a'
a, = symbols("a")

A_param = Matrix([
    [1, 1, 1],
    [1, a, 1],
    [1, 1, a]
])
b_param = Vector([1, 2, 3])

cs = GaussJordan(A_param, b_param).run()

# Rendu Markdown automatique de la discussion par cas
display(cs)
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Spécialisation numérique du CaseSplit
# Pour a = 2 (branche générique a ≠ 1)
sol_a2 = cs.at(a=2)
display(Markdown(r"**Pour $a = 2$ (branche générique $a \neq 1$) :**"))
display(sol_a2.solution)

# Pour a = 1 (branche particulière d'incompatibilité)
sol_a1 = cs.at(a=1)
display(Markdown(r"**Pour $a = 1$ (branche particulière) :**"))
display(sol_a1.solution)
'''
        )
    )

    # 7. Triangular
    nb["cells"].append(
        md_cell(
            """## 6. Substitutions Triangulaires (`BackSubstitution`, `ForwardSubstitution`)

VMLS résout les systèmes échelonnés triangulaires sans jamais inverser de matrice,
via une remontée (`BackSubstitution`) ou une descente (`ForwardSubstitution`) tracée pas à pas."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# Résolution de R x = c avec R triangulaire supérieure
R = Matrix([
    [2, -1, 3],
    [0, 4, 2],
    [0, 0, -2]
])
c = Vector([9, 8, -6])

res_back = BackSubstitution(R, c).run()

display(Markdown(r"**Solution $x$ :**"))
display(res_back.x)
display(Markdown("### Trace pas à pas de la substitution arrière :"))
display(res_back)
'''
        )
    )

    # 8. Gram-Schmidt & QR
    nb["cells"].append(
        md_cell(
            """## 7. Orthogonalisation de Gram-Schmidt et Factorisation QR

Deux variantes de Gram-Schmidt sont implémentées :
1. `normalize="end"` (défaut) : orthogonalisation rationnelle $\\tilde{q}_i = a_i - \\sum \\tilde{r}_{ji} \\tilde{q}_j$, entièrement dans $\\mathbb{Q}$.
2. `normalize="each"` : algorithme classique de VMLS qui normalise à chaque étape."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 7.1 Gram-Schmidt rationnel et normalisé
a1 = Vector([1, 1, 0])
a2 = Vector([1, 0, 1])
a3 = Vector([0, 1, 1])

gs = GramSchmidt([a1, a2, a3], normalize="end")
res_gs = gs.run()

display(Markdown(f"""### Orthogonalisation de Gram-Schmidt :
- **Famille libre :** `{res_gs.independent}`
- **Vecteurs orthogonaux rationnels $\\tilde{{q}}_i$ :**"""))
for i, q_t in enumerate(res_gs.orthogonal, 1):
    display(Markdown(f"$$\\tilde{{q}}_{{{i}}} = {q_t._repr_latex_().strip('$')}$$"))

display(Markdown("- **Vecteurs orthonormés finaux $q_i$ :**"))
for i, q in enumerate(res_gs.orthonormal, 1):
    display(Markdown(f"$$q_{{{i}}} = {q._repr_latex_().strip('$')}$$"))
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 7.2 Détection automatique de dépendance linéaire et témoin exact
v1 = Vector([1, 2, -1])
v2 = Vector([2, 0, 1])
v3 = 2 * v1 - 3 * v2  # Combinaison linéaire

res_dep = GramSchmidt([v1, v2, v3], strict=False).run()
display(Markdown(f"""### Famille liée détectée :
- **Famille libre ?** `{res_dep.independent}`
- **Indice du premier vecteur lié :** $a_{{{res_dep.dependent_index + 1}}}$
- **Témoin exact d'interdépendance :** ${sp.latex(res_dep.witness)}$"""))
'''
        )
    )

    nb["cells"].append(
        code_cell(
            r'''# 7.3 Factorisation QR complète : A = QR
A_mat = Matrix([
    [1, 1],
    [1, 0],
    [0, 1]
])

res_qr = QR(A_mat).run()

display(Markdown(r"**Matrice $Q$ (colonnes orthonormées) :**"))
display(res_qr.Q)
display(Markdown(r"**Matrice $R$ (triangulaire supérieure à diagonale $> 0$) :**"))
display(res_qr.R)
display(Markdown(r"**Matrice $\tilde{Q}$ rationnelle :**"))
display(res_qr.Q_tilde)

display(Markdown(r"### Contrôle a posteriori ($Q^T Q = I_2$ et $Q R = A$) :"))
display(res_qr.verify())
'''
        )
    )

    # 9. LeastSquares
    nb["cells"].append(
        md_cell(
            """## 8. Moindres Carrés Linéaires (`LeastSquares`)

Pour un problème surdéterminé $A x \\approx b$ ($m \\ge n$ avec $A$ de rang plein en colonnes),
`LeastSquares` résout $\\min \\|A x - b\\|^2$.

Par défaut, la méthode `"rational_qr"` résout $\\tilde{R} \\hat{x} = D^{-2} \\tilde{Q}^T b$ **entièrement dans $\\mathbb{Q}$ sans aucune racine carrée**."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''A = Matrix([
    [1, 0],
    [1, 1],
    [1, 2],
    [1, 3]
])
b = Vector([1, 2, 2, 4])

ls = LeastSquares(A, b, method="rational_qr").run()

display(Markdown(r"### Solution des Moindres Carrés :"))
display(Markdown(r"- **Solution optimale $\hat{x}$ :**"))
display(ls.x_hat)

display(Markdown(r"- **Projection $\hat{y} = A \hat{x}$ :**"))
display(ls.y_hat)

display(Markdown(r"- **Résidu $\hat{r} = A \hat{x} - b$ :**"))
display(ls.r_hat)

display(Markdown(f"- **Norme du résidu $\\|\\hat{{r}}\\|$ :** ${sp.latex(ls.residual_norm)}$"))
display(Markdown(f"- **RMS du résidu $\\mathrm{{rms}}(\\hat{{r}})$ :** ${sp.latex(ls.residual_rms)}$"))

display(Markdown(r"### Contrôle d'orthogonalité du résidu ($A^T \hat{r} = 0$) :"))
display(ls.verify())
'''
        )
    )

    # 10. Moteurs de rendu
    nb["cells"].append(
        md_cell(
            """## 9. Moteurs de Rendu et Traçabilité (`Explanation`)

Tout résultat algorithmique fournit `.explain()`, renvoyant une instance de `Explanation`
capable d'exporter le raisonnement dans différents formats."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''exp = ls.explain(level=1)

display(Markdown("### Rendu interactif (Markdown + LaTeX) :"))
display(exp)

display(Markdown("### Extrait du code source LaTeX exportable :"))
print(exp.to_latex()[:350] + "\n...")
'''
        )
    )

    # 11. Exercices et interactivité
    nb["cells"].append(
        md_cell(
            """## 10. Exercices Interactifs et Détection des Erreurs Fréquentes

L'élève peut être guidé dans la réduction pas à pas d'un système. Le vérificateur d'opérations
analyse les propositions et détecte les erreurs classiques répertoriées dans l'Annexe C."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''A_inter = Matrix([[1, 2], [3, 5]])
b_inter = Vector([5, 13])

session = GaussJordan(A_inter, b_inter).interactive()

# 1. Proposition valide et utile
fb1 = session.propose("L2 <- L2 - 3*L1")
display(Markdown(f"**Proposition 1 (`L2 <- L2 - 3*L1`) :** {fb1.message}"))

# 2. Détection d'erreur classique : dilatation par 0
fb_err = session.propose("L2 <- 0*L2")
display(Markdown(f"**Proposition 2 (`L2 <- 0*L2`) :** <span style='color:red;'>{fb_err.message}</span>"))

# 3. Demande de conseil sans donner la solution
display(Markdown(f"**Conseil du tuteur :** *{session.hint()}*"))
'''
        )
    )

    # 12. Compare
    nb["cells"].append(
        md_cell(
            """## 11. Comparaison Exact vs Flottant (`compare`)

Le module `compare` met en lumière les défaillances numériques du calcul en virgule flottante
sur les problèmes mal conditionnés de VMLS."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''from linalg_pedagopy.compare import (
    lauchli_gram_schmidt_experiment,
    lauchli_least_squares_experiment,
    hilbert_conditioning_experiment
)

# 1. Perte d'orthogonalité sur la matrice de Läuchli (eps = 1e-8)
display(Markdown(f"```text\n{lauchli_gram_schmidt_experiment()}\n```"))

# 2. Échec des équations normales en flottant
display(Markdown(f"```text\n{lauchli_least_squares_experiment()}\n```"))
'''
        )
    )

    # 13. Tuteur VMLS
    nb["cells"].append(
        md_cell(
            """## 12. Le Tuteur Interactif pour le Recueil de VMLS (`tuteur`)

Le module `tuteur` permet de s'entraîner sur les 136 exercices du recueil officiel de VMLS
(*Additional Exercises for VMLS*, Boyd & Vandenberghe).

### Les 8 principes pédagogiques :
1. **Vérification par propriété** : accepte toute réponse mathématiquement valide.
2. **Diagnostic explicatif** : montre ce que calcule la réponse de l'étudiant sans afficher la cible.
3. **Indices gradués sur 4 niveaux** (Orientation $\\to$ Outil $\\to$ Démarrage $\\to$ Exercice jumeau résolu).
4. **Exercice jumeau résolu** au niveau 4 pour transposer la méthode.
5. **Verrou des données** : `ex.donnees` bloque les calculs automatiques tant qu'aucune réponse n'a été soumise.
6. **Engagement avant exploration** : prédiction obligatoire (`ex.predire(...)`) pour ouvrir le laboratoire.
7. **Refus de confirmer par de simples essais** : un essai numérique ne vaut pas preuve.
8. **Journal local transparent** : historique et synthèse via `ex.bilan()`."""
        )
    )

    # 14. Exercices pratiques
    nb["cells"].append(
        md_cell(
            """## 13. Exercices Pratiques Pas à Pas

Résolvons maintenant 5 exercices représentatifs du recueil VMLS avec le tuteur."""
        )
    )

    # Exercice 1
    nb["cells"].append(
        md_cell(
            """### Exercice Pratique 1 : Modélisation d'une moyenne glissante (Recueil VMLS 6.4)

**Énoncé** :
$p \\in \\mathbb{R}^6$ est une série temporelle de prix sur 6 jours.
$d \\in \\mathbb{R}^3$ mesure, à partir du 4e jour ($i = 1, 2, 3$), l'écart entre le prix du jour ($p_{i+3}$)
et la moyenne des 3 jours précédents :
$$d_i = p_{i+3} - \\frac{p_i + p_{i+1} + p_{i+2}}{3}$$
Trouver la matrice $A$ telle que $d = A p$."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''ex64 = exercice("6.4")
display(Markdown(f"**Énoncé :**\n>{ex64.enonce()}\n\n**Indice 1 :** {ex64.indice()}"))

# Test avec une matrice contenant une erreur sur la ligne 2 :
t = Fraction(1, 3)
A_err = Matrix([
    [-t, -t, -t, 1, 0, 0],
    [-t, -t, -t, 1, 0, 0],  # Erreur : recopie de la ligne 1
    [0, 0, -t, -t, -t, 1]
])
diag_err = ex64.verifier(A_err)
display(Markdown(f"**Diagnostic sur réponse erronée :**\n> {diag_err}"))

# Soumission de la matrice exacte :
A_ok = Matrix([
    [-t, -t, -t, 1, 0, 0],
    [0, -t, -t, -t, 1, 0],
    [0, 0, -t, -t, -t, 1]
])
diag_ok = ex64.verifier(A_ok)
display(Markdown(f"**Validation de la matrice exacte :**\n> {diag_ok}"))
display(Markdown(f"```text\n{ex64.bilan()}\n```"))
'''
        )
    )

    # Exercice 2
    nb["cells"].append(
        md_cell(
            """### Exercice Pratique 2 : Vrai/Faux au Laboratoire de Contre-Exemples (Recueil VMLS 3.3)

**Énoncé** :
Soient $a, b, c \\in \\mathbb{R}^n$ tels que $a \\perp c$ et $b \\perp c$.
(a) A-t-on toujours $a \\perp b$ ?
(b) A-t-on toujours $(a + b) \\perp c$ ?
(c) A-t-on toujours $(a - b) \\perp (a + b)$ ?"""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''ex33 = exercice("3.3")

# Étape 1 : S'engager en enregistrant sa prédiction
ex33.predire(a="peut être faux", b="toujours vrai", c="peut être faux")

# Étape 2 : Ouvrir le laboratoire et tester une instance dans R^3
lab = ex33.labo()
rep = lab.tester(
    a=Vector([1, 0, 0]),
    b=Vector([1, 1, 0]),
    c=Vector([0, 0, 1])
)

display(Markdown(f"**Résultat du test au laboratoire :**\n\n{rep.message}"))
'''
        )
    )

    # Exercice 3
    nb["cells"].append(
        md_cell(
            """### Exercice Pratique 3 : Recherche de deux Inverses à Droite (Recueil VMLS 11.11)

**Énoncé** :
Pour la matrice large $A = \\begin{pmatrix} 1 & -1 & 2 \\\\ 0 & 1 & 1 \\end{pmatrix}$,
trouver deux matrices inverses à droite distinctes $B_1$ et $B_2$ ($3 \\times 2$)
telles que $A B_1 = I_2$, $A B_2 = I_2$ et $B_1 \\neq B_2$."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''ex1111 = exercice("11.11")

# Construction de deux inverses à droite distinctes
B1 = Matrix([[1, 1], [0, 1], [0, 0]])
B2 = Matrix([[-2, 1], [-1, 1], [1, 0]])

display(Markdown(r"**Matrice $B_1$ :**"))
display(B1)
display(Markdown(r"**Matrice $B_2$ :**"))
display(B2)

# Soumission du couple (B1, B2)
resultat = ex1111.verifier((B1, B2))
display(Markdown(f"**Diagnostic :** {resultat.diagnostic}"))
'''
        )
    )

    # Exercice 4
    nb["cells"].append(
        md_cell(
            """### Exercice Pratique 4 : Détecteurs d'Erreurs Typiques et Verrou (Recueil VMLS 3.9)

Cet exercice illustre le **verrou de données** (`ex.donnees`) et les **détecteurs d'erreurs typiques**
(norme au lieu de RMS, écart-type en $n-1$, carré de la distance, angle au lieu de corrélation)."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''ex39 = exercice("3.9")

# 1. Tentative de calcul direct sur les données verrouillées :
try:
    ex39.donnees.x.rms()
except Exception as e:
    display(Markdown(f"**Tentative interceptée par le verrou :** `{type(e).__name__}`"))

x = Vector([1, -2, 3, 2])

# 2. Erreur typique 1 : soumettre ||x|| au lieu de rms(x)
diag_e1 = ex39.verifier(x.norm()).diagnostic
display(Markdown(f"**Test Erreur typique 1 :** {diag_e1}"))

# 3. Soumission de la bonne valeur : déverrouille ex.donnees.x !
diag_ok = ex39.verifier(x.rms()).diagnostic
display(Markdown(f"**Soumission exacte :** {diag_ok}"))
display(Markdown(f"- Données déverrouillées, calcul direct autorisé : **${sp.latex(ex39.donnees.x.rms())}$**"))
'''
        )
    )

    # Exercice 5
    nb["cells"].append(
        md_cell(
            """### Exercice Pratique 5 : Optimisation de Norme Minimale et Système KKT (Recueil VMLS 20.11)

**Énoncé** :
Trouver le vecteur $x \\in \\mathbb{R}^3$ minimisant $\\|x\\|^2$ sous la contrainte $C x = d$ avec :
$$C = \\begin{pmatrix} 1 & 1 & 0 \\\\ 0 & 1 & 1 \\end{pmatrix}, \\quad d = \\begin{pmatrix} 1 \\\\ 1 \\end{pmatrix}$$"""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''ex2011 = exercice("20.11")
display(Markdown(f"**Énoncé :**\n>{ex2011.enonce()}"))

# Solution analytique du système KKT : x* = C^T (C C^T)^(-1) d
x_opt = Vector([Fraction(1, 3), Fraction(2, 3), Fraction(1, 3)])

display(Markdown(r"**Vecteur optimal $x^*$ :**"))
display(x_opt)

res_kkt = ex2011.verifier(x_opt)
display(Markdown(f"**Diagnostic :** {res_kkt.diagnostic}"))
'''
        )
    )

    # Glossaire
    nb["cells"].append(
        md_cell(
            """## 14. Glossaire Anglais-Français Intégré

La fonction `glossaire(terme)` permet d'obtenir la définition et la traduction française d'un concept clé de VMLS."""
        )
    )

    nb["cells"].append(
        code_cell(
            r'''mots = ("least squares", "root-mean-square", "de-meaned vector", "running average", "gram matrix")
lignes = [f"- **{glossaire(m)}**" for m in mots]
display(Markdown("### Extraits du Glossaire bilingue VMLS :\n" + "\n".join(lignes)))
'''
        )
    )

    # Écriture du fichier notebook
    target_path = Path("tutoriel_linalg_pedagopy.ipynb")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)

    print(f"Notebook généré et validé avec succès : {target_path.resolve()}")


if __name__ == "__main__":
    create_notebook()
