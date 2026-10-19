# 08. Catalogue des exercices

Le tuteur propose **35 exercices** répartis en 8 thèmes, du plus simple (★☆☆) au plus exigeant (★★★).
Chaque exercice s'ouvre par son identifiant, son numéro ou son titre :

```python
from linalg_pedagopy import tutor

ex = tutor.exercise("moyenne-glissante")   # ou tutor.exercise(16)
ex.statement()
```

Ce tableau est produit par `python docs/generer_catalogue.py` à partir des fiches ; dans un carnet, `tutor.catalog()` affiche la même liste.

## Vue d'ensemble

| N° | Exercice | Identifiant | Type | Niveau |
|---:|:---|:---|:---|:---:|
| | **Vecteurs et produit scalaire** | | | |
| 1 | [Sélectionner des composantes par un produit scalaire](#selection-composantes) | `selection-composantes` | modélisation | ★☆☆ |
| 2 | [Notations vectorielles : valides ou non ?](#validite-notations) | `validite-notations` | dimensions | ★☆☆ |
| 3 | [La recette du week-end](#recette-week-end) | `recette-week-end` | modélisation | ★☆☆ |
| 4 | [Valeurs centrales contre valeurs extrêmes](#centre-moins-extremes) | `centre-moins-extremes` | modélisation | ★★☆ |
| 5 | [L'étendue n'est pas linéaire](#etendue-non-lineaire) | `etendue-non-lineaire` | contre-exemple | ★★☆ |
| | **Normes, distances et angles** | | | |
| 6 | [Distance entre deux vecteurs](#distance-deux-vecteurs) | `distance-deux-vecteurs` | calcul | ★☆☆ |
| 7 | [Angle et distance](#angle-et-distance) | `angle-et-distance` | calcul | ★☆☆ |
| 8 | [Moyenne, rms et écart type d'un vecteur](#statistiques-vecteur) | `statistiques-vecteur` | calcul | ★★☆ |
| 9 | [Que signifie x² pour un vecteur ?](#notation-x-carre) | `notation-x-carre` | dimensions | ★☆☆ |
| 10 | [Le théorème de Pythagore](#pythagore) | `pythagore` | justification | ★★☆ |
| 11 | [rms d'une différence de vecteurs orthogonaux](#rms-difference-orthogonale) | `rms-difference-orthogonale` | justification | ★★☆ |
| 12 | [Orthogonalité : vrai ou faux ?](#orthogonalite-vrai-faux) | `orthogonalite-vrai-faux` | vrai ou faux | ★★☆ |
| 13 | [Inégalité triangulaire à trois vecteurs](#inegalite-triangulaire-trois) | `inegalite-triangulaire-trois` | vrai ou faux | ★★★ |
| | **Orthogonalisation** | | | |
| 14 | [Gram-Schmidt dépend-il de l'ordre ?](#ordre-gram-schmidt) | `ordre-gram-schmidt` | contre-exemple | ★★☆ |
| 15 | [Tester l'indépendance avec Gram-Schmidt](#independance-gram-schmidt) | `independance-gram-schmidt` | calcul | ★★★ |
| | **Matrices et applications linéaires** | | | |
| 16 | [Écart à la moyenne glissante](#moyenne-glissante) | `moyenne-glissante` | modélisation | ★★☆ |
| 17 | [Répéter un vecteur](#vecteur-repete) | `vecteur-repete` | modélisation | ★☆☆ |
| 18 | [Renverser l'ordre des composantes](#renverser-vecteur) | `renverser-vecteur` | modélisation | ★☆☆ |
| 19 | [Matrice d'une application du plan](#matrice-application-plan) | `matrice-application-plan` | modélisation | ★☆☆ |
| 20 | [Interpolation d'Hermite](#interpolation-hermite) | `interpolation-hermite` | modélisation | ★★★ |
| | **Convolution** | | | |
| 21 | [Convolution de deux vecteurs](#convolution-vecteurs) | `convolution-vecteurs` | calcul | ★☆☆ |
| 22 | [Produit de polynômes par convolution](#produit-polynomes) | `produit-polynomes` | calcul | ★★☆ |
| | **Produit matriciel** | | | |
| 23 | [Tailles des produits matriciels](#dimensions-produits) | `dimensions-produits` | dimensions | ★☆☆ |
| 24 | [Sommer les composantes d'un vecteur](#somme-composantes) | `somme-composantes` | modélisation | ★☆☆ |
| 25 | [Un réseau d'amitié](#reseau-amitie) | `reseau-amitie` | modélisation | ★★☆ |
| 26 | [Dynamique linéaire : trois pas de temps](#dynamique-trois-pas) | `dynamique-trois-pas` | modélisation | ★★☆ |
| 27 | [Mise à l'échelle par matrices diagonales](#mise-echelle-diagonale) | `mise-echelle-diagonale` | modélisation | ★★☆ |
| 28 | [Une identité par blocs](#identite-par-blocs) | `identite-par-blocs` | justification | ★★☆ |
| | **Inverses et systèmes linéaires** | | | |
| 29 | [Inverse à droite d'une matrice ligne](#inverse-droite-ligne) | `inverse-droite-ligne` | calcul | ★☆☆ |
| 30 | [Inverse d'un carré](#inverse-carre) | `inverse-carre` | justification | ★★☆ |
| 31 | [Retrouver un flux de trésorerie](#flux-tresorerie) | `flux-tresorerie` | calcul | ★★☆ |
| 32 | [Deux inverses à droite](#deux-inverses-droite) | `deux-inverses-droite` | calcul | ★★★ |
| 33 | [Les signes des coefficients d'une inverse](#inverse-signes) | `inverse-signes` | contre-exemple | ★★☆ |
| | **Moindres carrés et optimisation** | | | |
| 34 | [Mesures de sommes de paires](#sommes-de-paires) | `sommes-de-paires` | modélisation | ★★☆ |
| 35 | [Solution de norme minimale](#norme-minimale) | `norme-minimale` | calcul | ★★★ |

## Énoncés

### Vecteurs et produit scalaire

<a id="selection-composantes"></a>

#### 1. Sélectionner des composantes par un produit scalaire

*Identifiant* `selection-composantes` · *type* modélisation · *niveau* ★☆☆ · *réponse attendue* : un vecteur $a$ (forme $a^T x$)

Pour un vecteur $x \in \mathbb{R}^5$, déterminer le vecteur $a \in \mathbb{R}^5$ tel que le produit scalaire $a^T x$ soit égal à $x_2 - x_4$.

**Notions** : produit scalaire

<a id="validite-notations"></a>

#### 2. Notations vectorielles : valides ou non ?

*Identifiant* `validite-notations` · *type* dimensions · *niveau* ★☆☆ · *réponse attendue* : validité et tailles (dictionnaire ou mot)

Soient $a$ et $b$ deux vecteurs de $\mathbb{R}^n$ ($n > 1$) et $\alpha$ un scalaire. Indiquer pour chacune des notations (a) $a + b$, (b) $a + \alpha$, (c) $a^T b$, (d) $a b$ si elle est valide ou invalide.

**Notions** : notations vectorielles, dimensions

<a id="recette-week-end"></a>

#### 3. La recette du week-end

*Identifiant* `recette-week-end` · *type* modélisation · *niveau* ★☆☆ · *réponse attendue* : un vecteur $a$ (forme $a^T x$)

Un vecteur $c \in \mathbb{R}^7$ représente les recettes quotidiennes d'un magasin du lundi ($c_1$) au dimanche ($c_7$). Donner le vecteur $a \in \mathbb{R}^7$ tel que $a^T c$ représente la recette totale du week-end (samedi $c_6$ et dimanche $c_7$).

**Notions** : produit scalaire, sélection et somme de composantes

<a id="centre-moins-extremes"></a>

#### 4. Valeurs centrales contre valeurs extrêmes

*Identifiant* `centre-moins-extremes` · *type* modélisation · *niveau* ★★☆ · *réponse attendue* : un vecteur $a$ (forme $a^T x$)

Soit $f : \mathbb{R}^4 \to \mathbb{R}$ la fonction linéaire qui associe à $x$ l'écart entre sa valeur centrale $\frac{x_2 + x_3}{2}$ et la moyenne de ses valeurs extrêmes $\frac{x_1 + x_4}{2}$. Trouver le vecteur $a \in \mathbb{R}^4$ tel que $f(x) = a^T x$.

**Notions** : fonction linéaire, représentation par produit scalaire

<a id="etendue-non-lineaire"></a>

#### 5. L'étendue n'est pas linéaire

*Identifiant* `etendue-non-lineaire` · *type* contre-exemple · *niveau* ★★☆ · *réponse attendue* : un contre-exemple

On considère la fonction $f : \mathbb{R}^n \to \mathbb{R}$ définie par l'étendue (*spread*) $f(x) = \max_k x_k - \min_k x_k$. Montrer que $f$ n'est pas linéaire en fournissant un contre-exemple explicite {'x': Vector(...), 'y': Vector(...), 'alpha': 1, 'beta': 1}.

**Notions** : superposition et linéarité, contre-exemple

### Normes, distances et angles

<a id="distance-deux-vecteurs"></a>

#### 6. Distance entre deux vecteurs

*Identifiant* `distance-deux-vecteurs` · *type* calcul · *niveau* ★☆☆ · *réponse attendue* : une valeur exacte (ou un dictionnaire de valeurs)

On donne $x = (1, 2, -1)$ et $y = (2, 0, 1)$ dans $\mathbb{R}^3$. Calculer la distance euclidienne $\|x - y\|$ entre $x$ et $y$.

**Notions** : distance euclidienne, plus proche voisin

<a id="angle-et-distance"></a>

#### 7. Angle et distance

*Identifiant* `angle-et-distance` · *type* calcul · *niveau* ★☆☆ · *réponse attendue* : une valeur exacte (ou un dictionnaire de valeurs)

On considère les vecteurs $x = (1, 0, -1)$ et $y = (0, 1, 1)$ de $\mathbb{R}^3$. Calculer leur distance euclidienne $\|x - y\|$ (ou un dictionnaire {'dist': ..., 'angle': ...}).

**Notions** : angle et distance entre vecteurs

<a id="statistiques-vecteur"></a>

#### 8. Moyenne, rms et écart type d'un vecteur

*Identifiant* `statistiques-vecteur` · *type* calcul · *niveau* ★★☆ · *réponse attendue* : une valeur exacte (ou un dictionnaire de valeurs)

On considère les vecteurs $x = (1, -2, 3, 2)$ et $y = (2, 1, 0, 1)$ de $\mathbb{R}^4$. Calculer $\text{rms}(x)$ (ou fournir un dictionnaire {'rms': ..., 'avg': ..., 'std': ..., 'corr': ..., 'dist': ...}).

**Notions** : rms, avg, std, corrélation, distance

<a id="notation-x-carre"></a>

#### 9. Que signifie x² pour un vecteur ?

*Identifiant* `notation-x-carre` · *type* dimensions · *niveau* ★☆☆ · *réponse attendue* : validité et tailles (dictionnaire ou mot)

Pour un vecteur colonne $x \in \mathbb{R}^n$ ($n > 1$), la notation $x^2$ (au sens du produit $x x$) est-elle valide ou invalide ? Comment s'écrit correctement le carré de la norme $\|x\|^2$ en notation matricielle/vectorielle ?

**Notions** : validité des notations vectorielles, produit scalaire x^T x

<a id="pythagore"></a>

#### 10. Le théorème de Pythagore

*Identifiant* `pythagore` · *type* justification · *niveau* ★★☆ · *réponse attendue* : une formule (chaîne)

Soient $u$ et $v$ deux vecteurs orthogonaux de $\mathbb{R}^n$ ($u \perp v$). Exprimer $\|u + v\|^2$ en fonction de norm_u (représentant $\|u\|$) et norm_v (représentant $\|v\|$) (théorème de Pythagore).

**Notions** : norme d'une somme orthogonale, théorème de Pythagore

<a id="rms-difference-orthogonale"></a>

#### 11. rms d'une différence de vecteurs orthogonaux

*Identifiant* `rms-difference-orthogonale` · *type* justification · *niveau* ★★☆ · *réponse attendue* : une formule (chaîne)

Soient $u$ et $v$ deux vecteurs orthogonaux de $\mathbb{R}^n$ ($u \perp v$). Exprimer $\text{rms}(u - v)^2$ en fonction de rms_u (représentant $\text{rms}(u)$) et rms_v (représentant $\text{rms}(v)$).

**Notions** : rms d'une différence orthogonale, orthogonalité

<a id="orthogonalite-vrai-faux"></a>

#### 12. Orthogonalité : vrai ou faux ?

*Identifiant* `orthogonalite-vrai-faux` · *type* vrai ou faux · *niveau* ★★☆ · *réponse attendue* : prédiction puis essais au laboratoire

Soient $a, b, c$ trois vecteurs de $\mathbb{R}^n$ tels que $a \perp c$ et $b \perp c$. Pour chacune des affirmations (a) $a \perp b$, (b) $(a + b) \perp c$, (c) $(a - b) \perp (a + b)$, prédire si elle est « toujours vrai » ou « peut être faux », puis tester au laboratoire.

**Notions** : orthogonalité, distributivité du produit scalaire

<a id="inegalite-triangulaire-trois"></a>

#### 13. Inégalité triangulaire à trois vecteurs

*Identifiant* `inegalite-triangulaire-trois` · *type* vrai ou faux · *niveau* ★★★ · *réponse attendue* : prédiction puis essais au laboratoire

A-t-on $\|a + b + c\| \le \|a\| + \|b\| + \|c\|$ pour tous vecteurs $a, b, c$ ? Justifier, ou donner un contre-exemple.

**Notions** : inégalité triangulaire, norme euclidienne

### Orthogonalisation

<a id="ordre-gram-schmidt"></a>

#### 14. Gram-Schmidt dépend-il de l'ordre ?

*Identifiant* `ordre-gram-schmidt` · *type* contre-exemple · *niveau* ★★☆ · *réponse attendue* : un contre-exemple

L'algorithme de Gram-Schmidt dépend-il de l'ordre des vecteurs d'entrée ? Donner deux vecteurs indépendants $(a_1, a_2)$ de $\mathbb{R}^2$ tels que Gram-Schmidt appliqué à $(a_1, a_2)$ puis à $(a_2, a_1)$ produise deux bases orthonormées différentes.

**Notions** : algorithme de Gram-Schmidt, influence de l'ordre des vecteurs

<a id="independance-gram-schmidt"></a>

#### 15. Tester l'indépendance avec Gram-Schmidt

*Identifiant* `independance-gram-schmidt` · *type* calcul · *niveau* ★★★ · *réponse attendue* : une valeur exacte (ou un dictionnaire de valeurs)

On donne les vecteurs $a_1 = (1, 2, -1)$, $a_2 = (2, 0, 1)$ et $a_3 = (0, 4, -3)$ de $\mathbb{R}^3$. En appliquant Gram-Schmidt, déterminer le résidu orthogonal $\tilde{q}_3$ obtenu à la 3ᵉ étape (ou indiquer son carré de norme \|\tilde{q}_3\|^2 pour tester l'indépendance).

**Notions** : test d'indépendance linéaire par Gram-Schmidt

### Matrices et applications linéaires

<a id="moyenne-glissante"></a>

#### 16. Écart à la moyenne glissante

*Identifiant* `moyenne-glissante` · *type* modélisation · *niveau* ★★☆ · *réponse attendue* : une matrice

$p \in \mathbb{R}^6$ est une série de prix. $d \in \mathbb{R}^3$ mesure, à partir du 4ᵉ jour, l'écart entre le prix du jour et la moyenne des trois jours précédents. Trouver la matrice $A$ telle que $d = A p$ (donner sa taille et ses coefficients).

**Notions** : matrice comme application linéaire

<a id="vecteur-repete"></a>

#### 17. Répéter un vecteur

*Identifiant* `vecteur-repete` · *type* modélisation · *niveau* ★☆☆ · *réponse attendue* : une matrice

Pour un vecteur $x \in \mathbb{R}^2$, on forme le vecteur $y = (x, x, x) \in \mathbb{R}^6$ obtenu en répétant trois fois le vecteur $x$. Donner la matrice $A$ de taille $6 \times 2$ telle que $y = A x$.

**Notions** : matrices par blocs, répétition d'un vecteur

<a id="renverser-vecteur"></a>

#### 18. Renverser l'ordre des composantes

*Identifiant* `renverser-vecteur` · *type* modélisation · *niveau* ★☆☆ · *réponse attendue* : une matrice

Pour un vecteur $x \in \mathbb{R}^4$, l'application linéaire renverse l'ordre des composantes : $y = (x_4, x_3, x_2, x_1)$. Donner la matrice $A$ de taille $4 \times 4$ telle que $y = A x$.

**Notions** : matrices décrites par leur effet sur un vecteur, matrice de retournement (reverser)

<a id="matrice-application-plan"></a>

#### 19. Matrice d'une application du plan

*Identifiant* `matrice-application-plan` · *type* modélisation · *niveau* ★☆☆ · *réponse attendue* : une matrice

Soit l'application linéaire $f : \mathbb{R}^2 \to \mathbb{R}^2$ qui à $x = (x_1, x_2)$ associe $y = (y_1, y_2)$ avec $y_1 = 2 x_2 - x_1$ et $y_2 = x_1 + 3 x_2$. Donner la matrice $A$ ($2 \times 2$) telle que $y = A x$.

**Notions** : applications linéaires de R^2 dans R^2, représentation matricielle

<a id="interpolation-hermite"></a>

#### 20. Interpolation d'Hermite

*Identifiant* `interpolation-hermite` · *type* modélisation · *niveau* ★★★ · *réponse attendue* : une matrice

Soit $p(t) = c_1 + c_2 t + c_3 t^2 + c_4 t^3$ un polynôme de degré 3 de vecteur de coefficients $c \in \mathbb{R}^4$. Écrire sous la forme $y = A c$ le vecteur des 4 quantités : $y_1 = p(0)$, $y_2 = p'(0)$, $y_3 = p(1)$, $y_4 = p'(1)$. Donner la matrice $A$ ($4 \times 4$).

**Notions** : système d'équations linéaires A c = b, interpolation d'Hermite d'un polynôme

### Convolution

<a id="convolution-vecteurs"></a>

#### 21. Convolution de deux vecteurs

*Identifiant* `convolution-vecteurs` · *type* calcul · *niveau* ★☆☆ · *réponse attendue* : une valeur exacte (ou un dictionnaire de valeurs)

Calculer le produit de convolution $c = a * b$ des vecteurs $a = (1, 0, -1)$ et $b = (2, 1, -1)$ de $\mathbb{R}^3$.

**Notions** : convolution de deux vecteurs, matrice de Toeplitz

<a id="produit-polynomes"></a>

#### 22. Produit de polynômes par convolution

*Identifiant* `produit-polynomes` · *type* calcul · *niveau* ★★☆ · *réponse attendue* : une valeur exacte (ou un dictionnaire de valeurs)

Soient les deux polynômes $p(t) = 1 - 2t + t^2$ (vecteur de coefficients $a = (1, -2, 1)$) et $q(t) = 2 + t$ (vecteur $b = (2, 1)$). Calculer le vecteur $c \in \mathbb{R}^4$ des coefficients du polynôme produit $r(t) = p(t) q(t)$ par convolution $c = a * b$.

**Notions** : produit de convolution, multiplication de polynômes

### Produit matriciel

<a id="dimensions-produits"></a>

#### 23. Tailles des produits matriciels

*Identifiant* `dimensions-produits` · *type* dimensions · *niveau* ★☆☆ · *réponse attendue* : validité et tailles (dictionnaire ou mot)

Soient $A$ de taille $3 \times 4$, $B$ de taille $4 \times 2$ et $C$ de taille $3 \times 2$. Donner pour chacune des expressions (a) $A B + C$, (b) $A^T C$, (c) $B A$ la dimension $(m, n)$ du résultat ou "invalide" si l'opération n'est pas définie.

**Notions** : produit matriciel, compatibilité des dimensions

<a id="somme-composantes"></a>

#### 24. Sommer les composantes d'un vecteur

*Identifiant* `somme-composantes` · *type* modélisation · *niveau* ★☆☆ · *réponse attendue* : une matrice

Pour tout vecteur $v \in \mathbb{R}^3$, on veut calculer la somme de ses composantes $v_1 + v_2 + v_3$ par un produit matriciel $B v$. Donner la matrice $B$ de taille $1 \times 3$.

**Notions** : somme des coefficients d'une matrice, multiplication par le vecteur 1

<a id="reseau-amitie"></a>

#### 25. Un réseau d'amitié

*Identifiant* `reseau-amitie` · *type* modélisation · *niveau* ★★☆ · *réponse attendue* : une matrice

On considère un réseau d'amitié entre 4 personnes : 1 est amie avec 2 et 3 ; 2 est amie avec 1, 3 et 4 ; 3 est amie avec 1, 2 et 4 ; 4 est amie avec 2 et 3. Pour un vecteur de caractéristiques $x \in \mathbb{R}^4$, le vecteur $y$ donne pour chaque personne la somme des caractéristiques de ses amis. Donner la matrice $F$ ($4 \times 4$) telle que $y = F x$.

**Notions** : matrice d'adjacence d'un graphe, produit matrice-vecteur

<a id="dynamique-trois-pas"></a>

#### 26. Dynamique linéaire : trois pas de temps

*Identifiant* `dynamique-trois-pas` · *type* modélisation · *niveau* ★★☆ · *réponse attendue* : une matrice

Un système dynamique linéaire évolue selon $x_{t+1} = A x_t$ avec $A = \begin{bmatrix} 1 & 1 \\ 0 & 1 \end{bmatrix}$. Exprimer l'état à l'instant $t + 3$ sous la forme $x_{t+3} = M x_t$ en donnant la matrice $M = A^3$ de taille $2 \times 2$.

**Notions** : puissances d'une matrice, évolution à t + 3

<a id="mise-echelle-diagonale"></a>

#### 27. Mise à l'échelle par matrices diagonales

*Identifiant* `mise-echelle-diagonale` · *type* modélisation · *niveau* ★★☆ · *réponse attendue* : une formule (chaîne)

Soit $A$ une matrice $m \times n$, $D = \text{diag}(d_1, \dots, d_m)$ une matrice diagonale $m \times m$ et $E = \text{diag}(e_1, \dots, e_n)$ une matrice diagonale $n \times n$. Exprimer le coefficient $(i, j)$ du produit $D A E$ en fonction de $d_i$, $a_{ij}$ (représentant $A_{i,j}$) et $e_j$.

**Notions** : multiplication par des matrices diagonales D A E, mise à l'échelle des lignes et colonnes

<a id="identite-par-blocs"></a>

#### 28. Une identité par blocs

*Identifiant* `identite-par-blocs` · *type* justification · *niveau* ★★☆ · *réponse attendue* : une chaîne d'égalités (liste de chaînes)

Vérifier par une chaîne d'égalités matricielles par blocs l'identité : $\begin{bmatrix} A & B \\ C & D \end{bmatrix} \begin{bmatrix} I & 0 \\ 0 & I \end{bmatrix} = \begin{bmatrix} A & B \\ C & D \end{bmatrix}$ (soumettre la liste des maillons simplifiés).

**Notions** : identités sur les matrices par blocs, produit matriciel par blocs

### Inverses et systèmes linéaires

<a id="inverse-droite-ligne"></a>

#### 29. Inverse à droite d'une matrice ligne

*Identifiant* `inverse-droite-ligne` · *type* calcul · *niveau* ★☆☆ · *réponse attendue* : l'objet demandé (vérifié par sa propriété)

On considère la matrice ligne $A = \begin{bmatrix} 1 & 2 & -1 \end{bmatrix}$ de taille $1 \times 3$. Trouver une matrice colonne $B$ de taille $3 \times 1$ qui soit une inverse à droite de $A$ (c'est-à-dire telle que $A B = [1]$).

**Notions** : inverses à gauche et à droite d'un vecteur ligne

<a id="inverse-carre"></a>

#### 30. Inverse d'un carré

*Identifiant* `inverse-carre` · *type* justification · *niveau* ★★☆ · *réponse attendue* : l'objet demandé (vérifié par sa propriété)

Soit $A = \begin{bmatrix} 1 & 2 \\ 0 & 1 \end{bmatrix}$ une matrice carrée inversible d'inverse $B = A^{-1}$. Donner la matrice inverse de $A^2$ (ou son expression en fonction de $B$).

**Notions** : inverse d'un carré de matrice, inverse d'un produit

<a id="flux-tresorerie"></a>

#### 31. Retrouver un flux de trésorerie

*Identifiant* `flux-tresorerie` · *type* calcul · *niveau* ★★☆ · *réponse attendue* : l'objet demandé (vérifié par sa propriété)

Un flux de trésorerie sur 3 périodes $c = (c_1, c_2, c_3)$ a une valeur actuelle nette (VAN) égale à $2$ au taux $r = 0$ ($c_1 + c_2 + c_3 = 2$), égale à $1$ pour un facteur d'actualisation $\frac{1}{2}$ ($c_1 + \frac{c_2}{2} + \frac{c_3}{4} = 1$), et vérifie $c_1 = 0$. Retrouver le vecteur de flux de trésorerie $c \in \mathbb{R}^3$.

**Notions** : flux de trésorerie (cash flow) depuis la VAN, résolution de système linéaire

<a id="deux-inverses-droite"></a>

#### 32. Deux inverses à droite

*Identifiant* `deux-inverses-droite` · *type* calcul · *niveau* ★★★ · *réponse attendue* : l'objet demandé (vérifié par sa propriété)

On considère la matrice large $A = \begin{bmatrix} 1 & -1 & 2 \\ 0 & 1 & 1 \end{bmatrix}$ de taille $2 \times 3$. Trouver deux matrices inverses à droite distinctes $B_1$ et $B_2$ (de taille $3 \times 2$) telles que $A B_1 = I_2$, $A B_2 = I_2$ et $B_1 \neq B_2$, et les soumettre sous la forme $(B_1, B_2)$.

**Notions** : inverses à droite multiples, systèmes sous-déterminés

<a id="inverse-signes"></a>

#### 33. Les signes des coefficients d'une inverse

*Identifiant* `inverse-signes` · *type* contre-exemple · *niveau* ★★☆ · *réponse attendue* : un contre-exemple

L'inverse d'une matrice carrée inversible à coefficients strictement positifs ($> 0$) a-t-elle toujours ses coefficients positifs ? Fournir une matrice $A$ de taille $2 \times 2$ à coefficients $> 0$ qui soit inversible et dont l'inverse $A^{-1}$ comporte au moins un coefficient strictement négatif.

**Notions** : inverse d'une matrice 2×2, signe des coefficients de l'inverse

### Moindres carrés et optimisation

<a id="sommes-de-paires"></a>

#### 34. Mesures de sommes de paires

*Identifiant* `sommes-de-paires` · *type* modélisation · *niveau* ★★☆ · *réponse attendue* : une matrice

On cherche à estimer $x \in \mathbb{R}^3$ à partir des 6 mesures bruitées de toutes les paires : $y_1 \approx x_1 + x_2$, $y_2 \approx x_1 + x_3$, $y_3 \approx x_2 + x_3$, et des 3 mesures individuelles $y_4 \approx x_1$, $y_5 \approx x_2$, $y_6 \approx x_3$. Donner la matrice de conception $A$ de taille $6 \times 3$ telle que le problème s'écrive $\min_x \|A x - y\|^2$.

**Notions** : formulation des moindres carrés ||A x - b||^2, mesures de sommes de paires

<a id="norme-minimale"></a>

#### 35. Solution de norme minimale

*Identifiant* `norme-minimale` · *type* calcul · *niveau* ★★★ · *réponse attendue* : l'objet demandé (vérifié par sa propriété)

On considère le problème de norme minimale : minimiser $\|x\|^2$ sous la contrainte $C x = d$, avec $C = \begin{bmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \end{bmatrix}$ (taille $2 \times 3$) et $d = (1, 1)$. Trouver la solution optimale $x \in \mathbb{R}^3$ à l'aide des conditions KKT.

**Notions** : solution de norme minimale, système KKT
