"""Cahier d'exercices « Calcul sur les vecteurs et les matrices » : 20 exercices de difficulté croissante.

Ce module accompagne le carnet ``vecteurs_matrices.ipynb`` :

- ``verifier(k, reponse)`` contrôle la réponse à l'exercice k et explique ce qui ne va pas ;
- ``indice(k)`` affiche l'indice suivant de l'exercice k (2 ou 3 indices par exercice) ;
- ``bilan()`` récapitule les exercices réussis.

Les vérifications s'appuient sur linalg_pedagopy (calcul exact). Le module contient aussi les
réponses de référence (pour l'enseignant et les tests) : ne le lisez pas avant d'avoir cherché !
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable

import sympy as sp

from linalg_pedagopy import Matrix, Vector, symbols, to_exact

# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------


class FormeInattendue(Exception):
    """La réponse n'a pas la forme demandée (type ou taille)."""


@dataclass
class Retour:
    """Résultat d'une vérification, affiché en couleur dans JupyterLab."""

    ok: bool
    message: str

    def _repr_markdown_(self) -> str:
        if self.ok:
            return (
                "<div style='padding:10px 14px;border-left:4px solid #16a34a;background:#f0fdf4;"
                "color:#166534;border-radius:4px'>\n\n**✓ Bravo, c'est juste.**\n\n"
                f"{self.message}\n\n</div>"
            )
        return (
            "<div style='padding:10px 14px;border-left:4px solid #dc2626;background:#fef2f2;"
            "color:#991b1b;border-radius:4px'>\n\n**✗ Pas encore.**\n\n"
            f"{self.message}\n\n</div>"
        )

    def __str__(self) -> str:
        return ("✓ " if self.ok else "✗ ") + self.message

    def __bool__(self) -> bool:
        return self.ok


def _num(x: Any) -> sp.Expr:
    if isinstance(x, (Vector, Matrix, list, tuple, dict)) or x is None or x is ...:
        raise FormeInattendue("un nombre était attendu")
    return to_exact(x)


def _egal(a: Any, b: Any) -> bool:
    try:
        return sp.simplify(_num(a) - _num(b)) == 0
    except FormeInattendue:
        return False


def _vec(x: Any, n: int) -> Vector:
    if isinstance(x, Matrix) and x.cols == 1:
        x = Vector([x[i, 0] for i in range(x.rows)])
    if isinstance(x, (list, tuple)) and all(not isinstance(t, (list, tuple, Vector, Matrix)) for t in x):
        x = Vector(list(x))
    if not isinstance(x, Vector):
        raise FormeInattendue(f"un vecteur de taille {n} était attendu, par exemple Vector([...])")
    if len(x) != n:
        raise FormeInattendue(f"votre vecteur a {len(x)} composantes au lieu de {n}")
    return x


def _mat(x: Any, m: int, n: int) -> Matrix:
    if isinstance(x, (list, tuple)) and x and all(isinstance(r, (list, tuple)) for r in x):
        x = Matrix([list(r) for r in x])
    if not isinstance(x, Matrix):
        raise FormeInattendue(f"une matrice {m}×{n} était attendue, par exemple Matrix([[...], [...]])")
    if x.shape != (m, n):
        raise FormeInattendue(f"votre matrice est de taille {x.rows}×{x.cols} au lieu de {m}×{n}")
    return x


def _tuple(x: Any, k: int, quoi: str) -> tuple:
    if not isinstance(x, (tuple, list)) or len(x) != k:
        raise FormeInattendue(f"un tuple de {k} éléments était attendu : {quoi}")
    return tuple(x)


def _vec_egal(u: Vector, v: Vector) -> bool:
    return len(u) == len(v) and all(_egal(a, b) for a, b in zip(u.entries, v.entries))


def _mat_egal(A: Matrix, B: Matrix) -> bool:
    return A.shape == B.shape and all(_egal(a, b) for a, b in zip(A.flat_entries, B.flat_entries))


def _fmt(x: Any) -> str:
    if isinstance(x, Vector):
        return "(" + ", ".join(sp.sstr(e) for e in x.entries) + ")"
    if isinstance(x, Matrix):
        return "[" + "; ".join(" ".join(sp.sstr(e) for e in row) for row in x.entries_grid) + "]"
    return sp.sstr(x)


# ---------------------------------------------------------------------------
# Description d'un exercice
# ---------------------------------------------------------------------------


@dataclass
class Exercice:
    numero: int
    titre: str
    niveau: int
    enonce: str
    forme: str
    gabarit: str
    indices: list[str]
    controle: Callable[[Any], Retour]
    reference: Any
    erreurs_types: list[Any] = field(default_factory=list)
    solution: str = ""
    solution_code: str = ""


EXERCICES: dict[int, Exercice] = {}


def _exercice(**kw: Any) -> Callable[[Callable[[Any], Retour]], Callable[[Any], Retour]]:
    def deco(f: Callable[[Any], Retour]) -> Callable[[Any], Retour]:
        EXERCICES[kw["numero"]] = Exercice(controle=f, **kw)
        return f

    return deco


# ---------------------------------------------------------------------------
# Niveau 1 — Calculs sur les vecteurs
# ---------------------------------------------------------------------------

_u1, _v1 = Vector([1, -2, 3]), Vector([4, 0, -1])


@_exercice(
    numero=1, titre="Combinaison linéaire", niveau=1,
    enonce=r"Soient $u = (1, -2, 3)$ et $v = (4, 0, -1)$ dans $\mathbb{R}^3$. Calculer le vecteur $w = 2u - 3v$.",
    forme="un vecteur, par exemple `Vector([a, b, c])`",
    gabarit="reponse_1 = Vector([..., ..., ...])",
    indices=[
        "On calcule composante par composante : $w_i = 2u_i - 3v_i$.",
        "Première composante : $2 \\times 1 - 3 \\times 4$. Attention au signe des produits.",
    ],
    reference=Vector([-10, -4, 9]),
    erreurs_types=[Vector([14, -4, 3]), Vector([-10, -4, 3])],
    solution=r"$w = 2(1, -2, 3) - 3(4, 0, -1) = (2, -4, 6) - (12, 0, -3) = (-10, -4, 9)$.",
    solution_code="u, v = Vector([1, -2, 3]), Vector([4, 0, -1])\nVector.combination([u, v], [2, -3])",
)
def _c1(r: Any) -> Retour:
    w = _vec(r, 3)
    ref = 2 * _u1 - 3 * _v1
    if _vec_egal(w, ref):
        return Retour(True, f"$w = {sp.latex(sp.Matrix(ref.entries).T)}$.")
    if _vec_egal(w, 2 * _u1 + 3 * _v1):
        return Retour(False, "Vous avez calculé $2u + 3v$ : relisez le signe devant $3v$.")
    faux = [i + 1 for i in range(3) if not _egal(w.entries[i], ref.entries[i])]
    return Retour(False, f"Composante(s) {faux} incorrecte(s). Recalculez $2u_i - 3v_i$ pour ces indices "
                         "(attention à $-3 \\times (-1)$).")


@_exercice(
    numero=2, titre="Produit scalaire et carré de la norme", niveau=1,
    enonce=r"Avec $u = (1, -2, 3)$ et $v = (4, 0, -1)$, calculer le produit scalaire $u^T v$ et le carré de la norme $\|u\|^2$.",
    forme="un tuple `(produit_scalaire, norme_au_carre)`",
    gabarit="reponse_2 = (..., ...)",
    indices=[
        "$u^T v = u_1 v_1 + u_2 v_2 + u_3 v_3$.",
        "$\\|u\\|^2 = u^T u$ : c'est la somme des carrés des composantes, sans racine carrée.",
    ],
    reference=(1, 14),
    erreurs_types=[(1, sp.sqrt(14)), (7, 14)],
    solution=r"$u^T v = 4 + 0 - 3 = 1$ et $\|u\|^2 = 1 + 4 + 9 = 14$.",
    solution_code="u, v = Vector([1, -2, 3]), Vector([4, 0, -1])\nu.dot(v), u.norm_sq()",
)
def _c2(r: Any) -> Retour:
    ps, n2 = _tuple(r, 2, "(produit scalaire, norme au carré)")
    msgs = []
    if not _egal(ps, 1):
        if _egal(ps, 7):
            msgs.append("Produit scalaire : vous avez oublié le signe de $3 \\times (-1)$.")
        else:
            msgs.append(f"Produit scalaire : {sp.sstr(_num(ps))} est faux ; additionnez les produits $u_i v_i$.")
    if not _egal(n2, 14):
        if _egal(n2, sp.sqrt(14)):
            msgs.append("Vous avez donné la norme $\\|u\\|$ ; on demande son **carré**.")
        else:
            msgs.append("Carré de la norme : additionnez les carrés $u_i^2$ (un carré est toujours positif).")
    return Retour(not msgs, "Les deux valeurs sont justes." if not msgs else " ".join(msgs))


_w3 = Vector([2, -1, 2])


@_exercice(
    numero=3, titre="Norme et vecteur unitaire", niveau=1,
    enonce=r"Soit $w = (2, -1, 2)$. Calculer $\|w\|$, puis le vecteur unitaire $\dfrac{w}{\|w\|}$ de même direction et même sens.",
    forme="un tuple `(norme, Vector([...]))`",
    gabarit="reponse_3 = (..., Vector([..., ..., ...]))",
    indices=[
        "$\\|w\\| = \\sqrt{w_1^2 + w_2^2 + w_3^2}$ : ici le résultat est un entier.",
        "Divisez chaque composante de $w$ par $\\|w\\|$ ; vérifiez que le résultat est de norme 1.",
    ],
    reference=(3, Vector([Fraction(2, 3), Fraction(-1, 3), Fraction(2, 3)])),
    erreurs_types=[(9, Vector([Fraction(2, 9), Fraction(-1, 9), Fraction(2, 9)])), (3, Vector([2, -1, 2]))],
    solution=r"$\|w\| = \sqrt{4 + 1 + 4} = 3$, donc $\dfrac{w}{\|w\|} = \left(\tfrac{2}{3}, -\tfrac{1}{3}, \tfrac{2}{3}\right)$.",
    solution_code="w = Vector([2, -1, 2])\nw.norm(), w / w.norm()",
)
def _c3(r: Any) -> Retour:
    n, e = _tuple(r, 2, "(norme, vecteur unitaire)")
    e = _vec(e, 3)
    msgs = []
    if not _egal(n, 3):
        msgs.append("La norme est fausse" + (" : vous avez oublié la racine carrée." if _egal(n, 9) else "."))
    if not _vec_egal(e, _w3 / 3):
        if _egal(e.norm_sq(), 1):
            msgs.append("Votre vecteur est bien unitaire mais n'a pas la direction ou le sens de $w$.")
        else:
            msgs.append(f"Votre vecteur n'est pas unitaire : sa norme vaut ${sp.latex(e.norm())}$.")
    return Retour(not msgs, "Norme et vecteur unitaire justes." if not msgs else " ".join(msgs))


@_exercice(
    numero=4, titre="Angle entre deux vecteurs", niveau=1,
    enonce=r"Soient $a = (1, 1, 0)$ et $b = (1, 0, 1)$. Calculer $\cos\theta$, où $\theta$ est l'angle entre $a$ et $b$, puis $\theta$ (en radians, valeur exacte).",
    forme="un tuple `(cos_theta, theta)` ; utilisez `sp.pi` pour π",
    gabarit="reponse_4 = (..., ...)   # par exemple sp.pi/4",
    indices=[
        "$\\cos\\theta = \\dfrac{a^T b}{\\|a\\|\\,\\|b\\|}$.",
        "$a^T b = 1$ et $\\|a\\| = \\|b\\| = \\sqrt{2}$. Quel angle de $[0, \\pi]$ a ce cosinus ?",
    ],
    reference=(Fraction(1, 2), sp.pi / 3),
    erreurs_types=[(Fraction(1, 2), 60), (1, 0)],
    solution=r"$a^T b = 1$, $\|a\| = \|b\| = \sqrt 2$, donc $\cos\theta = \tfrac{1}{2}$ et $\theta = \tfrac{\pi}{3}$.",
    solution_code="a, b = Vector([1, 1, 0]), Vector([1, 0, 1])\na.dot(b) / (a.norm() * b.norm()), a.angle(b)",
)
def _c4(r: Any) -> Retour:
    c, t = _tuple(r, 2, "(cos θ, θ)")
    msgs = []
    if not _egal(c, Fraction(1, 2)):
        msgs.append("Le cosinus est faux : n'oubliez pas de diviser par le produit des normes.")
    if not _egal(t, sp.pi / 3):
        if _egal(t, 60):
            msgs.append("L'angle est demandé en **radians** : 60° = ?")
        else:
            msgs.append("L'angle est faux : cherchez $\\theta \\in [0, \\pi]$ tel que $\\cos\\theta$ vaille votre cosinus.")
    return Retour(not msgs, "Cosinus et angle justes." if not msgs else " ".join(msgs))


_x5 = Vector([2, 4, 4, 4, 5, 5, 7, 9])


@_exercice(
    numero=5, titre="Moyenne, moyenne quadratique et écart type", niveau=1,
    enonce=(
        r"Soit $x = (2, 4, 4, 4, 5, 5, 7, 9) \in \mathbb{R}^8$. Calculer la moyenne $\mathrm{avg}(x)$, "
        r"la moyenne quadratique $\mathrm{rms}(x) = \|x\| / \sqrt{n}$ et l'écart type "
        r"$\mathrm{std}(x) = \mathrm{rms}(x - \mathrm{avg}(x)\,\mathbf{1})$."
    ),
    forme="un tuple `(avg, rms, std)` (valeurs exactes, `sp.sqrt(...)` si besoin)",
    gabarit="reponse_5 = (..., ..., ...)",
    indices=[
        "La somme des composantes vaut 40 et la somme de leurs carrés 232.",
        "Pour l'écart type, centrez d'abord : $x - 5\\cdot\\mathbf{1} = (-3, -1, -1, -1, 0, 0, 2, 4)$. On divise par $n = 8$ (et non $n - 1$).",
    ],
    reference=(5, sp.sqrt(29), 2),
    erreurs_types=[(5, sp.sqrt(29), sp.sqrt(sp.Rational(32, 7))), (5, sp.sqrt(232), 2)],
    solution=r"$\mathrm{avg}(x) = 40/8 = 5$, $\mathrm{rms}(x) = \sqrt{232/8} = \sqrt{29}$, $\mathrm{std}(x) = \sqrt{32/8} = 2$.",
    solution_code="x = Vector([2, 4, 4, 4, 5, 5, 7, 9])\nx.avg(), x.rms(), x.std()",
)
def _c5(r: Any) -> Retour:
    a, q, s = _tuple(r, 3, "(avg, rms, std)")
    msgs = []
    if not _egal(a, 5):
        msgs.append("Moyenne fausse : somme des composantes divisée par 8.")
    if not _egal(q, sp.sqrt(29)):
        msgs.append("rms faux" + (" : vous avez donné $\\|x\\|$, il faut encore diviser par $\\sqrt 8$." if _egal(q, sp.sqrt(232)) else " : $\\sqrt{(\\text{somme des carrés})/8}$."))
    if not _egal(s, 2):
        msgs.append("Écart type faux" + (" : vous avez divisé par $n - 1$ ; ici on divise par $n$." if _egal(s, sp.sqrt(sp.Rational(32, 7))) else " : calculez le rms du vecteur centré."))
    return Retour(not msgs, "Les trois statistiques sont justes." if not msgs else " ".join(msgs))


# ---------------------------------------------------------------------------
# Niveau 2 — Produits de matrices
# ---------------------------------------------------------------------------

_A6, _x6 = Matrix([[1, 2, 0], [-1, 3, 2]]), Vector([2, -1, 1])


@_exercice(
    numero=6, titre="Produit matrice-vecteur", niveau=2,
    enonce=r"Calculer $A x$ pour $A = \begin{bmatrix} 1 & 2 & 0 \\ -1 & 3 & 2 \end{bmatrix}$ et $x = (2, -1, 1)$.",
    forme="un vecteur",
    gabarit="reponse_6 = Vector([..., ...])",
    indices=[
        "$A$ est $2 \\times 3$ et $x \\in \\mathbb{R}^3$ : le résultat a 2 composantes.",
        "La composante $i$ de $A x$ est le produit scalaire de la ligne $i$ de $A$ avec $x$ (ou : $A x = 2 a_1 - a_2 + a_3$ avec les colonnes).",
    ],
    reference=Vector([0, -3]),
    erreurs_types=[Vector([0, -3, 2]), Vector([4, -3])],
    solution=r"Ligne 1 : $2 - 2 + 0 = 0$ ; ligne 2 : $-2 - 3 + 2 = -3$. Donc $A x = (0, -3)$.",
    solution_code="A, x = Matrix([[1, 2, 0], [-1, 3, 2]]), Vector([2, -1, 1])\nA.matmul(x, view='columns')",
)
def _c6(r: Any) -> Retour:
    y = _vec(r, 2)
    ref = _A6 @ _x6
    if _vec_egal(y, ref):
        return Retour(True, "$A x = (0, -3)$.")
    faux = [i + 1 for i in range(2) if not _egal(y.entries[i], ref.entries[i])]
    return Retour(False, f"Composante(s) {faux} fausse(s) : refaites le produit scalaire ligne $i$ · $x$.")


_A7, _B7 = Matrix([[1, 2], [3, 4]]), Matrix([[0, 1], [1, 0]])


@_exercice(
    numero=7, titre="Produit matriciel et non-commutativité", niveau=2,
    enonce=(
        r"Avec $A = \begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}$ et $B = \begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}$, "
        r"calculer $AB$. (Calculez aussi $BA$ au brouillon : est-ce la même matrice ?)"
    ),
    forme="la matrice $AB$",
    gabarit="reponse_7 = Matrix([[..., ...], [..., ...]])",
    indices=[
        "Le coefficient $(i, j)$ de $AB$ est le produit scalaire de la ligne $i$ de $A$ par la colonne $j$ de $B$.",
        "Multiplier **à droite** par $B$ agit sur les colonnes de $A$ ; multiplier à gauche agirait sur les lignes.",
    ],
    reference=Matrix([[2, 1], [4, 3]]),
    erreurs_types=[Matrix([[3, 4], [1, 2]])],
    solution=r"$AB = \begin{bmatrix} 2 & 1 \\ 4 & 3 \end{bmatrix}$ (colonnes de $A$ échangées) alors que $BA = \begin{bmatrix} 3 & 4 \\ 1 & 2 \end{bmatrix}$ (lignes échangées) : $AB \neq BA$.",
    solution_code="A, B = Matrix([[1, 2], [3, 4]]), Matrix([[0, 1], [1, 0]])\nA @ B, B @ A",
)
def _c7(r: Any) -> Retour:
    M = _mat(r, 2, 2)
    if _mat_egal(M, _A7 @ _B7):
        return Retour(True, "$AB$ échange les colonnes de $A$, alors que $BA$ échangerait ses lignes : $AB \\neq BA$.")
    if _mat_egal(M, _B7 @ _A7):
        return Retour(False, "Vous avez calculé $BA$. L'ordre compte : dans $AB$, on prend les **lignes de $A$** et les **colonnes de $B$**.")
    return Retour(False, "Reprenez chaque coefficient : ligne $i$ de $A$ · colonne $j$ de $B$.")


_A8, _B8 = Matrix([[1, 0, 2], [0, 1, -1]]), Matrix([[1, 1], [2, 0], [0, 3]])


@_exercice(
    numero=8, titre="Transposée d'un produit", niveau=2,
    enonce=(
        r"Soient $A = \begin{bmatrix} 1 & 0 & 2 \\ 0 & 1 & -1 \end{bmatrix}$ ($2 \times 3$) et "
        r"$B = \begin{bmatrix} 1 & 1 \\ 2 & 0 \\ 0 & 3 \end{bmatrix}$ ($3 \times 2$). Calculer $(AB)^T$."
    ),
    forme="une matrice",
    gabarit="reponse_8 = Matrix([[..., ...], [..., ...]])",
    indices=[
        "Quelle est la taille de $AB$ ? et celle de $(AB)^T$ ?",
        "Deux méthodes : calculer $AB$ puis transposer, ou utiliser $(AB)^T = B^T A^T$ (l'ordre s'inverse).",
    ],
    reference=Matrix([[1, 2], [7, -3]]),
    erreurs_types=[Matrix([[1, 7], [2, -3]])],
    solution=r"$AB = \begin{bmatrix} 1 & 7 \\ 2 & -3 \end{bmatrix}$ donc $(AB)^T = \begin{bmatrix} 1 & 2 \\ 7 & -3 \end{bmatrix} = B^T A^T$.",
    solution_code="A = Matrix([[1, 0, 2], [0, 1, -1]])\nB = Matrix([[1, 1], [2, 0], [0, 3]])\n(A @ B).T, B.T @ A.T",
)
def _c8(r: Any) -> Retour:
    if isinstance(r, Matrix) and r.shape == (3, 3):
        return Retour(False, "Votre matrice est $3 \\times 3$ : c'est la taille de $A^T B^T$. Or $(AB)^T = B^T A^T$, de taille $2 \\times 2$.")
    M = _mat(r, 2, 2)
    if _mat_egal(M, (_A8 @ _B8).T):
        return Retour(True, "$(AB)^T = B^T A^T$.")
    if _mat_egal(M, _A8 @ _B8):
        return Retour(False, "C'est $AB$ : il reste à transposer (échanger lignes et colonnes).")
    return Retour(False, "Recalculez $AB$ coefficient par coefficient, puis transposez.")


_A9 = Matrix([[1, 1], [1, -1], [2, 0]])


@_exercice(
    numero=9, titre="Matrice de Gram", niveau=2,
    enonce=r"Pour $A = \begin{bmatrix} 1 & 1 \\ 1 & -1 \\ 2 & 0 \end{bmatrix}$, calculer la matrice de Gram $G = A^T A$. Que dire des colonnes de $A$ ?",
    forme="la matrice $G$",
    gabarit="reponse_9 = Matrix([[..., ...], [..., ...]])",
    indices=[
        "$G$ est $2 \\times 2$ : son coefficient $(i, j)$ est le produit scalaire $a_i^T a_j$ des colonnes $i$ et $j$ de $A$.",
        "Les coefficients diagonaux sont les carrés des normes des colonnes.",
    ],
    reference=Matrix([[6, 0], [0, 2]]),
    erreurs_types=[Matrix([[2, 0, 2], [0, 2, 2], [2, 2, 4]])],
    solution=r"$G = \begin{bmatrix} 6 & 0 \\ 0 & 2 \end{bmatrix}$ : le coefficient hors diagonale est nul, les colonnes de $A$ sont **orthogonales**.",
    solution_code="A = Matrix([[1, 1], [1, -1], [2, 0]])\nA.gram()",
)
def _c9(r: Any) -> Retour:
    if isinstance(r, Matrix) and r.shape == (3, 3):
        return Retour(False, "Votre matrice est $3 \\times 3$ : c'est $A A^T$. La matrice de Gram est $A^T A$ ($2 \\times 2$).")
    M = _mat(r, 2, 2)
    if _mat_egal(M, _A9.T @ _A9):
        return Retour(True, "Le coefficient hors diagonale est nul : les colonnes de $A$ sont orthogonales.")
    return Retour(False, "Calculez $a_1^T a_1$, $a_1^T a_2$ et $a_2^T a_2$ à partir des colonnes de $A$.")


@_exercice(
    numero=10, titre="Décomposer un vecteur", niveau=2,
    enonce=r"Trouver les réels $\alpha, \beta$ tels que $\alpha\,(1, 2) + \beta\,(3, -1) = (7, 0)$.",
    forme="un tuple `(alpha, beta)`",
    gabarit="reponse_10 = (..., ...)",
    indices=[
        "Écrivez l'égalité composante par composante : vous obtenez un système de 2 équations à 2 inconnues.",
        "La seconde équation $2\\alpha - \\beta = 0$ donne $\\beta$ en fonction de $\\alpha$.",
    ],
    reference=(1, 2),
    erreurs_types=[(2, 1)],
    solution=r"$\alpha + 3\beta = 7$ et $2\alpha - \beta = 0$, donc $\beta = 2\alpha$, $7\alpha = 7$ : $\alpha = 1$, $\beta = 2$.",
    solution_code="from linalg_pedagopy import GaussJordan\nGaussJordan(Matrix.from_columns([Vector([1, 2]), Vector([3, -1])]), Vector([7, 0])).run().solution",
)
def _c10(r: Any) -> Retour:
    a, b = _tuple(r, 2, "(alpha, beta)")
    a, b = _num(a), _num(b)
    w = a * Vector([1, 2]) + b * Vector([3, -1])
    if _vec_egal(w, Vector([7, 0])):
        return Retour(True, "$1\\cdot(1, 2) + 2\\cdot(3, -1) = (7, 0)$.")
    return Retour(False, f"Avec vos valeurs, $\\alpha(1,2) + \\beta(3,-1) = {_fmt(w)}$ au lieu de $(7, 0)$.")


# ---------------------------------------------------------------------------
# Niveau 3 — Systèmes, rang, inverse
# ---------------------------------------------------------------------------

_A11, _b11 = Matrix([[1, 1, 1], [2, -1, 1], [1, 2, -1]]), Vector([6, 3, 2])


@_exercice(
    numero=11, titre="Résoudre un système 3 × 3", niveau=3,
    enonce=r"Résoudre le système $\begin{cases} x + y + z = 6 \\ 2x - y + z = 3 \\ x + 2y - z = 2 \end{cases}$",
    forme="le vecteur solution `Vector([x, y, z])`",
    gabarit="reponse_11 = Vector([..., ..., ...])",
    indices=[
        "Éliminez $x$ des équations 2 et 3 à l'aide de la première ($L_2 \\leftarrow L_2 - 2L_1$, $L_3 \\leftarrow L_3 - L_1$).",
        "Vous obtenez un système $2 \\times 2$ en $y, z$ ; résolvez-le puis remontez à $x$.",
    ],
    reference=Vector([1, 2, 3]),
    erreurs_types=[Vector([3, 2, 1])],
    solution=r"Par élimination : $-3y - z = -9$ et $y - 2z = -4$, d'où $z = 3$, $y = 2$, puis $x = 1$.",
    solution_code="from linalg_pedagopy import GaussJordan\nres = GaussJordan(Matrix([[1, 1, 1], [2, -1, 1], [1, 2, -1]]), Vector([6, 3, 2])).run()\nres.explain(level=1)",
)
def _c11(r: Any) -> Retour:
    x = _vec(r, 3)
    res = _A11 @ x - _b11
    faux = [i + 1 for i in range(3) if not _egal(res.entries[i], 0)]
    if not faux:
        return Retour(True, "$(x, y, z) = (1, 2, 3)$ vérifie les trois équations.")
    return Retour(False, f"Votre vecteur ne vérifie pas l'équation (ou les équations) {faux}. Reprenez l'élimination.")


_A12 = Matrix([[1, 2, 0, 1], [2, 4, 1, 3], [3, 6, 1, 4]])


@_exercice(
    numero=12, titre="Rang et noyau", niveau=3,
    enonce=(
        r"Soit $A = \begin{bmatrix} 1 & 2 & 0 & 1 \\ 2 & 4 & 1 & 3 \\ 3 & 6 & 1 & 4 \end{bmatrix}$. "
        r"Déterminer le rang de $A$ et une base du noyau $\ker A = \{x \in \mathbb{R}^4 : A x = 0\}$."
    ),
    forme="un tuple `(rang, [v1, v2, ...])` avec une liste de vecteurs",
    gabarit="reponse_12 = (..., [Vector([...]), ...])",
    indices=[
        "Remarquez une relation entre les lignes de $A$. Échelonnez la matrice.",
        "Rang + dimension du noyau = nombre de colonnes (théorème du rang).",
        "Exprimez les inconnues pivots en fonction des inconnues libres, puis donnez à chaque inconnue libre la valeur 1 (les autres 0).",
    ],
    reference=(2, [Vector([-2, 1, 0, 0]), Vector([-1, 0, -1, 1])]),
    erreurs_types=[(3, [Vector([-2, 1, 0, 0])]), (2, [Vector([-2, 1, 0, 0]), Vector([-4, 2, 0, 0])])],
    solution=r"$L_3 = L_1 + L_2$ : rang 2. Les pivots sont $x_1, x_3$ ; avec $x_2 = s$, $x_4 = t$ : $x_3 = -t$, $x_1 = -2s - t$. Base : $(-2, 1, 0, 0)$, $(-1, 0, -1, 1)$.",
    solution_code="A = Matrix([[1, 2, 0, 1], [2, 4, 1, 3], [3, 6, 1, 4]])\nA.rank(), A.nullspace()",
)
def _c12(r: Any) -> Retour:
    rg, base = _tuple(r, 2, "(rang, liste de vecteurs)")
    if not isinstance(base, (list, tuple)):
        raise FormeInattendue("la base du noyau doit être une liste de vecteurs")
    vs = [_vec(v, 4) for v in base]
    msgs = []
    if not _egal(rg, 2):
        msgs.append("Le rang est faux : cherchez une ligne combinaison des autres.")
    for k, v in enumerate(vs, 1):
        if not _vec_egal(_A12 @ v, Vector.zeros(3)):
            msgs.append(f"Le vecteur n° {k} n'est pas dans le noyau ($A v \\neq 0$).")
    if vs and not msgs:
        if Matrix.from_columns(vs).rank() != len(vs):
            msgs.append("Vos vecteurs sont liés : une base doit être formée de vecteurs indépendants.")
        elif len(vs) != 2:
            msgs.append(f"Le noyau est de dimension $4 - 2 = 2$ : il faut 2 vecteurs, vous en donnez {len(vs)}.")
    return Retour(not msgs, "Rang 2 et base du noyau correcte (d'autres bases sont possibles)." if not msgs else " ".join(msgs))


_A13 = Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]])


@_exercice(
    numero=13, titre="Inverse d'une matrice 3 × 3", niveau=3,
    enonce=r"Calculer l'inverse de $A = \begin{bmatrix} 1 & 2 & 3 \\ 0 & 1 & 4 \\ 5 & 6 & 0 \end{bmatrix}$.",
    forme="la matrice $A^{-1}$",
    gabarit="reponse_13 = Matrix([[..., ..., ...], [..., ..., ...], [..., ..., ...]])",
    indices=[
        "Méthode de Gauss-Jordan : réduisez $[A \\mid I_3]$ jusqu'à obtenir $[I_3 \\mid A^{-1}]$.",
        "Le déterminant de $A$ vaut 1 : tous les coefficients de l'inverse sont entiers.",
        "Vérifiez votre résultat en calculant $A A^{-1}$.",
    ],
    reference=Matrix([[-24, 18, 5], [20, -15, -4], [-5, 4, 1]]),
    erreurs_types=[Matrix([[-24, 20, -5], [18, -15, 4], [5, -4, 1]])],
    solution=r"$A^{-1} = \begin{bmatrix} -24 & 18 & 5 \\ 20 & -15 & -4 \\ -5 & 4 & 1 \end{bmatrix}$ (et l'on vérifie $A A^{-1} = I_3$).",
    solution_code="from linalg_pedagopy import GaussJordan\nA = Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]])\nres = GaussJordan(A, compute_inverse=True).run()\nres.inverse",
)
def _c13(r: Any) -> Retour:
    M = _mat(r, 3, 3)
    P = _A13 @ M
    if _mat_egal(P, Matrix.identity(3)):
        return Retour(True, "$A A^{-1} = I_3$.")
    if _mat_egal(M, _A13.inv().T):
        return Retour(False, "Vous avez donné la **transposée** de l'inverse (oubli de transposer la comatrice ?).")
    faux = [(i + 1, j + 1) for i in range(3) for j in range(3) if not _egal(P[i, j], 1 if i == j else 0)]
    return Retour(False, f"$A \\times$ votre matrice n'est pas $I_3$ (coefficients {faux[:4]}{'…' if len(faux) > 4 else ''} faux).")


_A14, _b14 = Matrix([[1, 2, -1], [2, 4, 1], [3, 6, 0]]), Vector([1, 5, 6])


@_exercice(
    numero=14, titre="Infinité de solutions", niveau=3,
    enonce=(
        r"Résoudre $\begin{cases} x + 2y - z = 1 \\ 2x + 4y + z = 5 \\ 3x + 6y = 6 \end{cases}$ "
        r"et écrire l'ensemble des solutions sous la forme $\{x_0 + t\,v,\ t \in \mathbb{R}\}$."
    ),
    forme="un tuple `(x0, v)` : une solution particulière et un vecteur directeur",
    gabarit="reponse_14 = (Vector([..., ..., ...]), Vector([..., ..., ...]))",
    indices=[
        "La troisième équation est la somme des deux premières : il reste 2 équations pour 3 inconnues.",
        "En combinant les deux premières équations, on trouve $z$ ; puis $x = 2 - 2y$ avec $y$ libre.",
        "$x_0$ vérifie $A x_0 = b$ ; $v$ est un vecteur non nul tel que $A v = 0$.",
    ],
    reference=(Vector([2, 0, 1]), Vector([-2, 1, 0])),
    erreurs_types=[(Vector([2, 0, 1]), Vector([0, 0, 0])), (Vector([0, 0, 0]), Vector([-2, 1, 0]))],
    solution=r"$L_2 - 2L_1$ : $3z = 3$, $z = 1$, puis $x + 2y = 2$. Avec $y = t$ : $(x, y, z) = (2, 0, 1) + t(-2, 1, 0)$.",
    solution_code="from linalg_pedagopy import GaussJordan\nGaussJordan(Matrix([[1, 2, -1], [2, 4, 1], [3, 6, 0]]), Vector([1, 5, 6])).run().solution",
)
def _c14(r: Any) -> Retour:
    x0, v = _tuple(r, 2, "(x0, v)")
    x0, v = _vec(x0, 3), _vec(v, 3)
    msgs = []
    if not _vec_egal(_A14 @ x0, _b14):
        msgs.append("$x_0$ n'est pas solution : $A x_0 \\neq b$.")
    if _vec_egal(v, Vector.zeros(3)):
        msgs.append("Le vecteur directeur doit être **non nul**.")
    elif not _vec_egal(_A14 @ v, Vector.zeros(3)):
        msgs.append("$v$ ne dirige pas l'ensemble des solutions : il faut $A v = 0$.")
    return Retour(not msgs, "Bonne description de la droite des solutions (d'autres $x_0$, $v$ conviennent)." if not msgs else " ".join(msgs))


@_exercice(
    numero=15, titre="Matrice d'une projection orthogonale", niveau=3,
    enonce=(
        r"Dans $\mathbb{R}^2$, on note $p(x)$ la projection orthogonale de $x$ sur la droite $D$ d'équation $y = x$. "
        r"Trouver la matrice $P$ telle que $p(x) = P x$. Vérifier ensuite (au brouillon) que $P^2 = P$."
    ),
    forme="une matrice $2 \\times 2$",
    gabarit="reponse_15 = Matrix([[..., ...], [..., ...]])",
    indices=[
        "La colonne $j$ de $P$ est l'image du vecteur $e_j$. Que valent $p(1, 1)$ et $p(1, -1)$ ?",
        "Avec $u = (1, 1)$ : $p(x) = \\dfrac{u^T x}{u^T u}\\,u$, soit $P = \\dfrac{u u^T}{u^T u}$.",
    ],
    reference=Matrix([[Fraction(1, 2), Fraction(1, 2)], [Fraction(1, 2), Fraction(1, 2)]]),
    erreurs_types=[Matrix([[1, 1], [1, 1]]), Matrix([[0, 1], [1, 0]])],
    solution=r"$u = (1, 1)$, $P = \dfrac{u u^T}{u^T u} = \tfrac{1}{2}\begin{bmatrix} 1 & 1 \\ 1 & 1 \end{bmatrix}$ ; on vérifie $P^2 = P$ et $P^T = P$.",
    solution_code="u = Vector([1, 1])\nP = Matrix.from_columns([u]) @ Matrix.from_rows([u]) / u.norm_sq()\nP, P @ P == P",
)
def _c15(r: Any) -> Retour:
    P = _mat(r, 2, 2)
    a = P @ Vector([1, 1])
    b = P @ Vector([1, -1])
    msgs = []
    if not _vec_egal(a, Vector([1, 1])):
        msgs.append(f"Un vecteur de $D$ doit être inchangé, or $P(1, 1) = {_fmt(a)}$.")
    if not _vec_egal(b, Vector([0, 0])):
        msgs.append(f"Un vecteur orthogonal à $D$ doit être envoyé sur 0, or $P(1, -1) = {_fmt(b)}$.")
    if _mat_egal(P, Matrix([[0, 1], [1, 0]])):
        msgs.append("(C'est la matrice de la **symétrie** par rapport à $D$, pas de la projection.)")
    return Retour(not msgs, "$P$ fixe la droite $D$ et annule sa direction orthogonale ; $P^2 = P$." if not msgs else " ".join(msgs))


# ---------------------------------------------------------------------------
# Niveau 4 — Paramètres, orthogonalisation, moindres carrés
# ---------------------------------------------------------------------------


@_exercice(
    numero=16, titre="Inversibilité selon un paramètre", niveau=4,
    enonce=(
        r"Pour quelles valeurs du réel $a$ la matrice $A(a) = \begin{bmatrix} a & 1 & 1 \\ 1 & a & 1 \\ 1 & 1 & a \end{bmatrix}$ "
        r"n'est-elle **pas** inversible ?"
    ),
    forme="la liste des valeurs, par exemple `[..., ...]`",
    gabarit="reponse_16 = [...]",
    indices=[
        "Essayez $a = 1$ : que remarquez-vous sur les lignes ?",
        "La somme des colonnes vaut $(a + 2)(1, 1, 1)$. Que se passe-t-il pour $a = -2$ ?",
        r"Calculez $\det A(a)$ (développement suivant une ligne ou règle de Sarrus), puis factorisez : "
        r"$A(a)$ est inversible si et seulement si $\det A(a) \neq 0$.",
    ],
    reference=[1, -2],
    erreurs_types=[[1], [-2, 1, 2]],
    solution=r"$\det A(a) = (a - 1)^2(a + 2)$ : $A(a)$ n'est pas inversible pour $a = 1$ (trois lignes égales) et $a = -2$ (la somme des colonnes est nulle).",
    solution_code=(
        "from linalg_pedagopy import symbols, Determinant\n"
        "a, = symbols('a')\n"
        "A = Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]])\n"
        "print(A.det())                                        # (a - 1)**2*(a + 2)\n"
        "print([str(c) for c in Determinant(A).run().zeros()])  # valeurs singulières : a = −2, a = 1\n"
        "A.rank()   # discussion de cas automatique du rang"
    ),
)
def _c16(r: Any) -> Retour:
    if not isinstance(r, (list, tuple, set)):
        raise FormeInattendue("une liste de valeurs était attendue")
    vals = {sp.nsimplify(_num(v)) for v in r}
    attendu = {sp.Integer(1), sp.Integer(-2)}
    manquent, trop = attendu - vals, vals - attendu
    if not manquent and not trop:
        return Retour(True, "$\\det A(a) = (a - 1)^2 (a + 2)$ s'annule exactement pour $a = 1$ et $a = -2$.")
    msgs = []
    if trop:
        msgs.append(f"Pour {sorted(trop, key=float)}, la matrice est inversible.")
    if manquent:
        msgs.append(f"Il manque {len(manquent)} valeur(s).")
    return Retour(False, " ".join(msgs))


_a17 = [Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([0, 1, 1])]


@_exercice(
    numero=17, titre="Orthonormalisation de Gram-Schmidt", niveau=4,
    enonce=(
        r"Appliquer le procédé de Gram-Schmidt à $a_1 = (1, 1, 0)$, $a_2 = (1, 0, 1)$, $a_3 = (0, 1, 1)$ "
        r"(dans cet ordre) pour obtenir une base orthonormée $(q_1, q_2, q_3)$."
    ),
    forme="un tuple `(q1, q2, q3)` de vecteurs (utilisez `sp.sqrt`)",
    gabarit="reponse_17 = (Vector([...]), Vector([...]), Vector([...]))",
    indices=[
        "$q_1 = a_1 / \\|a_1\\|$. Ensuite $\\tilde q_2 = a_2 - (q_1^T a_2)\\,q_1$, puis on normalise.",
        "Vous devez trouver $\\tilde q_2$ proportionnel à $(1, -1, 2)$ et $\\tilde q_3$ proportionnel à $(-1, 1, 1)$.",
        "Contrôle : les $q_i$ sont de norme 1 et deux à deux orthogonaux.",
    ],
    reference=(Vector([1, 1, 0]) / sp.sqrt(2), Vector([1, -1, 2]) / sp.sqrt(6), Vector([-1, 1, 1]) / sp.sqrt(3)),
    erreurs_types=[(Vector([1, 1, 0]), Vector([1, -1, 2]), Vector([-1, 1, 1]))],
    solution=(
        r"$q_1 = \tfrac{1}{\sqrt 2}(1, 1, 0)$ ; $\tilde q_2 = a_2 - \tfrac12(1, 1, 0) = \tfrac12(1, -1, 2)$, "
        r"$q_2 = \tfrac{1}{\sqrt 6}(1, -1, 2)$ ; $\tilde q_3 = a_3 - \tfrac12(1,1,0) - \tfrac16(1,-1,2) = \tfrac23(-1, 1, 1)$, "
        r"$q_3 = \tfrac{1}{\sqrt 3}(-1, 1, 1)$."
    ),
    solution_code="from linalg_pedagopy import GramSchmidt\nres = GramSchmidt([Vector([1, 1, 0]), Vector([1, 0, 1]), Vector([0, 1, 1])]).run()\nres.orthonormal",
)
def _c17(r: Any) -> Retour:
    qs = [_vec(q, 3) for q in _tuple(r, 3, "(q1, q2, q3)")]
    msgs = []
    for i, q in enumerate(qs, 1):
        if not _egal(q.norm_sq(), 1):
            msgs.append(f"$q_{i}$ n'est pas de norme 1 (norme au carré : ${sp.latex(sp.simplify(q.norm_sq()))}$).")
    for i in range(3):
        for j in range(i + 1, 3):
            if not _egal(qs[i].dot(qs[j]), 0):
                msgs.append(f"$q_{i+1}$ et $q_{j+1}$ ne sont pas orthogonaux.")
    if msgs:
        return Retour(False, " ".join(msgs))
    # même drapeau : q_k ∈ vect(a_1..a_k) et q_k^T a_k > 0
    for k in range(3):
        if Matrix.from_columns(_a17[: k + 1] + [qs[k]]).rank() != k + 1:
            return Retour(False, f"Base orthonormée, mais $q_{k+1}$ n'est pas dans $\\mathrm{{Vect}}(a_1, \\dots, a_{k+1})$ : respectez l'ordre des $a_i$.")
        if not sp.simplify(qs[k].dot(_a17[k])) > 0:
            return Retour(False, f"$q_{k+1}$ a le mauvais sens : Gram-Schmidt donne $q_{k+1}^T a_{k+1} > 0$.")
    return Retour(True, "Base orthonormée obtenue par Gram-Schmidt dans l'ordre demandé.")


_A18 = Matrix([[1, 1], [1, 0], [0, 1]])


@_exercice(
    numero=18, titre="Factorisation QR", niveau=4,
    enonce=(
        r"Calculer la factorisation $A = QR$ de $A = \begin{bmatrix} 1 & 1 \\ 1 & 0 \\ 0 & 1 \end{bmatrix}$, où $Q$ ($3 \times 2$) a des colonnes "
        r"orthonormées et $R$ ($2 \times 2$) est triangulaire supérieure à diagonale positive."
    ),
    forme="un tuple `(Q, R)`",
    gabarit="reponse_18 = (Matrix([[..., ...], [..., ...], [..., ...]]), Matrix([[..., ...], [0, ...]]))",
    indices=[
        "Les colonnes de $Q$ s'obtiennent par Gram-Schmidt sur les colonnes de $A$.",
        "$R = Q^T A$ : ses coefficients sont $r_{ij} = q_i^T a_j$.",
        "Vous devez trouver $r_{11} = \\sqrt 2$ et $r_{12} = 1/\\sqrt 2$.",
    ],
    reference=(
        Matrix.from_columns([Vector([1, 1, 0]) / sp.sqrt(2), Vector([1, -1, 2]) / sp.sqrt(6)]),
        Matrix([[sp.sqrt(2), 1 / sp.sqrt(2)], [0, sp.sqrt(6) / 2]]),
    ),
    erreurs_types=[(Matrix([[1, 1], [1, 0], [0, 1]]), Matrix.identity(2))],
    solution=(
        r"$q_1 = \tfrac{1}{\sqrt2}(1, 1, 0)$, $\tilde q_2 = a_2 - \tfrac12 a_1 = \tfrac12(1, -1, 2)$, $q_2 = \tfrac{1}{\sqrt 6}(1, -1, 2)$ ; "
        r"$R = \begin{bmatrix} \sqrt 2 & 1/\sqrt 2 \\ 0 & \sqrt{6}/2 \end{bmatrix}$."
    ),
    solution_code="from linalg_pedagopy import QR\nres = QR(Matrix([[1, 1], [1, 0], [0, 1]])).run()\nres.Q, res.R",
)
def _c18(r: Any) -> Retour:
    Q, R = _tuple(r, 2, "(Q, R)")
    Q, R = _mat(Q, 3, 2), _mat(R, 2, 2)
    msgs = []
    if not _mat_egal(Q.T @ Q, Matrix.identity(2)):
        msgs.append("Les colonnes de $Q$ ne sont pas orthonormées ($Q^T Q \\neq I$).")
    if not _egal(R[1, 0], 0):
        msgs.append("$R$ doit être triangulaire supérieure.")
    if not (sp.simplify(_num(R[0, 0])) > 0 and sp.simplify(_num(R[1, 1])) > 0):
        msgs.append("La diagonale de $R$ doit être strictement positive.")
    if not msgs and not _mat_egal(Q @ R, _A18):
        msgs.append("$Q$ et $R$ ont la bonne forme mais $QR \\neq A$.")
    return Retour(not msgs, "$Q^T Q = I$, $R$ triangulaire à diagonale positive et $QR = A$." if not msgs else " ".join(msgs))


_A19, _b19 = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]]), Vector([1, 3, 4, 4])


@_exercice(
    numero=19, titre="Droite des moindres carrés", niveau=4,
    enonce=(
        r"On cherche la droite $y = c_0 + c_1 t$ qui approche au mieux, au sens des moindres carrés, les points "
        r"$(0, 1)$, $(1, 3)$, $(2, 4)$, $(3, 4)$. Calculer $\hat c = (c_0, c_1)$."
    ),
    forme="le vecteur `Vector([c0, c1])`",
    gabarit="reponse_19 = Vector([..., ...])",
    indices=[
        "Écrivez le problème sous la forme $\\min \\|A c - y\\|^2$ : une ligne de $A$ par point, $(1, t_i)$.",
        "Résolvez les équations normales $A^T A\\,\\hat c = A^T y$ : ici $A^T A = \\begin{bmatrix} 4 & 6 \\\\ 6 & 14 \\end{bmatrix}$.",
        "Contrôle : le résidu $A\\hat c - y$ est orthogonal aux colonnes de $A$.",
    ],
    reference=Vector([Fraction(3, 2), 1]),
    erreurs_types=[Vector([1, 2]), Vector([1, 1])],
    solution=r"$A^T A = \begin{bmatrix} 4 & 6 \\ 6 & 14 \end{bmatrix}$, $A^T y = (12, 23)$, d'où $\hat c = (3/2,\ 1)$ : la droite $y = 3/2 + t$.",
    solution_code="from linalg_pedagopy import LeastSquares\nls = LeastSquares(Matrix([[1, 0], [1, 1], [1, 2], [1, 3]]), Vector([1, 3, 4, 4])).run()\nls.x_hat, ls.verify()",
)
def _c19(r: Any) -> Retour:
    c = _vec(r, 2)
    g = _A19.T @ (_A19 @ c - _b19)
    if _vec_egal(g, Vector.zeros(2)):
        return Retour(True, "$\\hat c = (3/2, 1)$ : le résidu est orthogonal aux colonnes de $A$.")
    return Retour(False, f"Votre $c$ ne vérifie pas les équations normales : $A^T(Ac - y) = {_fmt(g)} \\neq 0$. "
                         "(Une droite ne passe pas par les 4 points : on minimise la somme des carrés des écarts.)")


_n = symbols("n")[0]


@_exercice(
    numero=20, titre="Puissances d'une matrice", niveau=4,
    enonce=(
        r"Soit $A = \begin{bmatrix} 2 & 1 \\ 0 & 2 \end{bmatrix}$. Exprimer $A^n$ en fonction de l'entier $n \ge 0$ "
        r"(utilisez le symbole `n = symbols('n')[0]`)."
    ),
    forme="une matrice contenant le symbole `n`",
    gabarit="n = symbols('n')[0]\nreponse_20 = Matrix([[..., ...], [..., ...]])",
    indices=[
        "Calculez $A^2$ et $A^3$ : quelle forme voyez-vous apparaître ?",
        "Écrivez $A = 2I + N$ avec $N = \\begin{bmatrix} 0 & 1 \\\\ 0 & 0 \\end{bmatrix}$ : que vaut $N^2$ ?",
        "$2I$ et $N$ commutent : la formule du binôme s'applique et s'arrête au terme en $N$.",
    ],
    reference=Matrix([[2**_n, _n * 2 ** (_n - 1)], [0, 2**_n]]),
    erreurs_types=[Matrix([[2**_n, _n], [0, 2**_n]]), Matrix([[2**_n, 2**_n], [0, 2**_n]])],
    solution=r"$A = 2I + N$ avec $N^2 = 0$, donc $A^n = 2^n I + n\,2^{n-1} N = \begin{bmatrix} 2^n & n\,2^{n-1} \\ 0 & 2^n \end{bmatrix}$.",
    solution_code="A = Matrix([[2, 1], [0, 2]])\n[A @ A, A @ A @ A]   # on devine la forme, puis on la démontre",
)
def _c20(r: Any) -> Retour:
    M = _mat(r, 2, 2)
    A = Matrix([[2, 1], [0, 2]])
    P = Matrix.identity(2)
    for k in range(0, 8):
        Mk = M.subs({_n: k}) if M.to_sympy().free_symbols else M
        if not _mat_egal(Mk, P):
            if not M.to_sympy().free_symbols:
                return Retour(False, "Votre matrice ne dépend pas de $n$ : elle ne peut pas valoir $A^n$ pour tout $n$.")
            return Retour(False, f"Votre formule est fausse pour $n = {k}$ : elle donne {_fmt(Mk)} au lieu de {_fmt(P)}.")
        P = P @ A
    return Retour(True, "Formule juste pour $n = 0, \\dots, 7$ ; démontrez-la par récurrence ou avec le binôme.")


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

_INDICES_VUS: dict[int, int] = {}
_REUSSIS: set[int] = set()


def _get(k: int) -> Exercice:
    if k not in EXERCICES:
        raise KeyError(f"Il n'y a pas d'exercice {k} : les exercices vont de 1 à {len(EXERCICES)}.")
    return EXERCICES[k]


def verifier(k: int, reponse: Any) -> Retour:
    """Vérifie la réponse à l'exercice k et renvoie un diagnostic (sans donner la solution)."""
    ex = _get(k)
    if reponse is None or reponse is ...:
        return Retour(False, f"Complétez d'abord la cellule de réponse. Forme attendue : {ex.forme}.")
    try:
        retour = ex.controle(reponse)
    except FormeInattendue as err:
        retour = Retour(False, f"Forme inattendue : {err}. Forme attendue : {ex.forme}.")
    except Exception as err:  # noqa: BLE001
        retour = Retour(False, f"Réponse illisible ({type(err).__name__} : {err}). Forme attendue : {ex.forme}.")
    if retour.ok:
        _REUSSIS.add(k)
    return retour


def indice(k: int) -> Retour | Any:
    """Affiche l'indice suivant de l'exercice k (rappel des précédents)."""
    ex = _get(k)
    vus = min(_INDICES_VUS.get(k, 0) + 1, len(ex.indices))
    _INDICES_VUS[k] = vus
    lignes = [f"**Indice {i} / {len(ex.indices)}** — {ex.indices[i - 1]}" for i in range(1, vus + 1)]
    if vus == len(ex.indices):
        lignes.append("*C'était le dernier indice de cet exercice.*")
    return _Md("\n\n".join(lignes))


def bilan() -> Any:
    """Récapitule les exercices réussis pendant la séance."""
    lignes = ["| N° | Exercice | Niveau | Réussi |", "|---:|:---|:---:|:---:|"]
    for k, ex in EXERCICES.items():
        lignes.append(f"| {k} | {ex.titre} | {'★' * ex.niveau} | {'✓' if k in _REUSSIS else ''} |")
    lignes.append(f"\n**{len(_REUSSIS)} / {len(EXERCICES)}** exercices réussis.")
    return _Md("\n".join(lignes))


class _Md(str):
    def _repr_markdown_(self) -> str:
        return str(self)


def _auto_test() -> list[str]:
    """Vérifie que chaque réponse de référence est acceptée et chaque erreur type refusée."""
    problemes = []
    for k, ex in EXERCICES.items():
        if not ex.controle(ex.reference).ok:
            problemes.append(f"exercice {k} : la référence est refusée")
        for faux in ex.erreurs_types:
            try:
                if ex.controle(faux).ok:
                    problemes.append(f"exercice {k} : l'erreur type {faux!r} est acceptée")
            except FormeInattendue:
                pass
    return problemes


__all__ = ["EXERCICES", "bilan", "indice", "verifier"]
