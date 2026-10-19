"""Générateurs d'exercices reproductibles à résultats « propres » et jumeaux résolus."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import random
from typing import Any

import sympy as sp

from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan
from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.algorithms.least_squares import LeastSquares
from linalg_pedagopy.algorithms.qr import QR
from linalg_pedagopy.core.field import symbols, to_exact
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.render.explanation import Explanation
from linalg_pedagopy.trace.tracer import suspend_tracing, tracing


def cayley_orthogonal(S: Matrix) -> Matrix:
    """Construit une matrice orthogonale rationnelle par transformée de Cayley Q = (I - S)(I + S)^(-1).

    S doit être antisymétrique (S^T = -S).
    """
    if S.rows != S.cols:
        raise ValueError("La matrice S doit être carrée.")
    with suspend_tracing():
        if S.T != -S:
            raise ValueError("La matrice S doit être antisymétrique (S^T = -S).")
        ident = Matrix.identity(S.rows)
        inv_plus = (ident + S).inv(strict=True)
        if not isinstance(inv_plus, Matrix):
            raise ValueError("I + S n'est pas inversible.")
        return (ident - S) @ inv_plus


def generate_unimodular_matrix(
    n: int = 3,
    *,
    seed: int | None = None,
    difficulty: int = 1,
) -> Matrix:
    """Génère une matrice entière unimodulaire (det = ±1) dont l'inverse est entière."""
    rng = random.Random(seed)
    max_coeff = max(1, min(4, difficulty + 1))
    num_ops = max(n + 1, n * (difficulty + 1))

    grid = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for _ in range(num_ops):
        i, j = rng.sample(range(n), 2)
        k = rng.choice([-1, 1]) * rng.randint(1, max_coeff)
        grid[i] = [grid[i][c] + k * grid[j][c] for c in range(n)]

    if rng.random() < 0.5 and n >= 2:
        r0, r1 = rng.sample(range(n), 2)
        grid[r0], grid[r1] = grid[r1], grid[r0]

    return Matrix(grid)


def generate_integer_rref_matrix(
    m: int = 3,
    n: int = 4,
    rank: int = 2,
    *,
    seed: int | None = None,
    difficulty: int = 1,
) -> tuple[Matrix, Matrix]:
    """Génère un couple (A, R) où R = rref(A) est à coefficients entiers."""
    if not (0 <= rank <= min(m, n)):
        raise ValueError(f"Rang {rank} invalide pour une matrice {m}x{n}.")
    rng = random.Random(seed)
    max_val = max(2, difficulty + 2)

    pivot_cols = sorted(rng.sample(range(n), rank))
    r_grid = [[0] * n for _ in range(m)]
    for row_idx, p_col in enumerate(pivot_cols):
        r_grid[row_idx][p_col] = 1
        for c in range(p_col + 1, n):
            if c not in pivot_cols:
                r_grid[row_idx][c] = rng.randint(-max_val, max_val)

    R = Matrix(r_grid)
    P = generate_unimodular_matrix(m, seed=rng.randint(0, 10**6), difficulty=difficulty)
    with suspend_tracing():
        A = P @ R
    return A, R


def generate_rational_qr_matrix(
    n: int = 3,
    *,
    seed: int | None = None,
    difficulty: int = 1,
) -> tuple[Matrix, Matrix, Matrix]:
    """Génère un triplet (A, Q, R) rationnel exact via la transformée de Cayley."""
    rng = random.Random(seed)
    s_grid = [[sp.Integer(0)] * n for _ in range(n)]
    choices = [Fraction(1, 2), Fraction(1, 1), Fraction(2, 1), Fraction(-1, 1), Fraction(-2, 1)]
    for i in range(n):
        for j in range(i + 1, n):
            val = to_exact(rng.choice(choices))
            s_grid[i][j] = val
            s_grid[j][i] = -val
    S = Matrix._from_exact_rows(s_grid)
    Q = cayley_orthogonal(S)

    # Pour avoir Q * R sans dénominateurs compliqués, on peut multiplier la diagonale de R par le PPCM des dénominateurs de Q
    denoms = [int(sp.fraction(e)[1]) for e in Q.flat_entries]
    scale_lcm = 1
    for d in denoms:
        scale_lcm = int(sp.ilcm(scale_lcm, d))

    r_grid = [[sp.Integer(0)] * n for _ in range(n)]
    for i in range(n):
        r_grid[i][i] = sp.Integer(scale_lcm * rng.randint(1, max(2, difficulty + 1)))
        for j in range(i + 1, n):
            r_grid[i][j] = sp.Integer(scale_lcm * rng.randint(-difficulty - 1, difficulty + 1))

    R = Matrix._from_exact_rows(r_grid)
    with suspend_tracing():
        A = Q @ R
    return A, Q, R


def generate_clean_least_squares(
    m: int = 4,
    n: int = 2,
    *,
    seed: int | None = None,
    difficulty: int = 1,
) -> tuple[Matrix, Vector, Vector, Vector]:
    """Génère (A, b, x_hat, r_hat) où x_hat est entier et r_hat in ker(A^T).

    Convention : r_hat = A x_hat - b, soit b = A x_hat - r_hat.
    """
    if m <= n:
        raise ValueError("Il faut m > n pour un système surdéterminé avec résidu non nul.")
    rng = random.Random(seed)

    # Construction d'une matrice A de rang plein en colonnes
    while True:
        a_rows = [[rng.randint(-2, 3) for _ in range(n)] for _ in range(m)]
        A = Matrix(a_rows)
        with suspend_tracing():
            if A.rank() == n:
                ns = A.T.nullspace()
                if isinstance(ns, tuple) and len(ns) > 0:
                    break

    x_hat = Vector([rng.randint(-3, 4) or 1 for _ in range(n)])
    # Combinaison entière/rationnelle des vecteurs du noyau de A^T
    basis = ns  # type: ignore[assignment]
    coeffs = [rng.choice([1, -1, 2]) for _ in range(len(basis))]
    with suspend_tracing():
        r_raw = Vector.combination(basis, coeffs)
        # Mise à l'échelle pour rendre r_hat entier
        denoms = [int(sp.fraction(e)[1]) for e in r_raw.entries]
        lcm_d = 1
        for d in denoms:
            lcm_d = int(sp.ilcm(lcm_d, d))
        r_hat = r_raw * lcm_d
        b = (A @ x_hat) - r_hat

    return A, b, x_hat, r_hat


def generate_parametric_system(
    n: int = 3,
    *,
    param_name: str = "a",
    critical_value: Any = 1,
    seed: int | None = None,
    difficulty: int = 1,
) -> tuple[Matrix, Vector, sp.Symbol, sp.Expr]:
    """Génère un système paramétré (A(a), b, a, a_crit) dont le déterminant s'annule en a_crit."""
    rng = random.Random(seed)
    param_sym = symbols(param_name)[0]
    crit_expr = to_exact(critical_value)

    P = generate_unimodular_matrix(n, seed=rng.randint(0, 10**6), difficulty=difficulty)
    # Matrice triangulaire supérieure dont le dernier coefficient diagonal est (param - crit)
    u_grid = [[sp.Integer(1 if i == j else 0) for j in range(n)] for i in range(n)]
    for i in range(n - 1):
        for j in range(i + 1, n):
            u_grid[i][j] = sp.Integer(rng.choice([-1, 1, 2]))
    u_grid[n - 1][n - 1] = param_sym - crit_expr
    U = Matrix._from_exact_rows(u_grid)

    with suspend_tracing():
        A_param = P @ U
    b_vec = Vector([rng.randint(1, 4) for _ in range(n)])
    return A_param, b_vec, param_sym, crit_expr


def _matrix_to_latex(mat: Matrix) -> str:
    """Formate une Matrix en environnement LaTeX bmatrix."""
    rows_str = [" & ".join(sp.latex(mat[i, j]) for j in range(mat.cols)) for i in range(mat.rows)]
    return "\\begin{bmatrix} " + " \\\\ ".join(rows_str) + " \\end{bmatrix}"


def _vector_to_latex(vec: Vector) -> str:
    """Formate un Vector en environnement LaTeX bmatrix colonne."""
    rows_str = [sp.latex(e) for e in vec.entries]
    return "\\begin{bmatrix} " + " \\\\ ".join(rows_str) + " \\end{bmatrix}"


@dataclass(frozen=True)
class TwinExercise:
    """Exercice jumeau résolu de bout en bout pour le niveau 4 d'indice du tuteur."""

    title: str
    statement: str
    solution_summary: str
    explanation: Explanation | None = None

    def format_text(self) -> str:
        lines = [
            f"=== Exercice jumeau résolu : {self.title} ===",
            f"Énoncé analogue : {self.statement}",
            f"Résolution pas à pas :\n{self.solution_summary}",
        ]
        if self.explanation is not None:
            exp_txt = self.explanation.to_text(level=2)
            if exp_txt:
                lines.append(exp_txt)
        return "\n".join(lines)

    def _repr_markdown_(self) -> str:
        lines = [
            f"### Exercice jumeau résolu : {self.title}",
            f"**Énoncé analogue** :\n\n{self.statement}",
            f"**Résolution pas à pas** :\n\n{self.solution_summary}",
        ]
        if self.explanation is not None:
            exp_md = self.explanation.to_markdown(level=2)
            if exp_md:
                lines.append(f"**Détail des étapes formelles** :\n\n{exp_md}")
        return "\n\n".join(lines)

    def __str__(self) -> str:
        return self.format_text()


class _TwinGeneratorNamespace:
    """Catalogue de générateurs d'exercices jumeaux appelables depuis les fiches YAML."""

    @staticmethod
    def moyenne_glissante(fenetre: int = 2, n: int = 5) -> TwinExercise:
        """Jumeau écart à la moyenne glissante sur une fenêtre donnée."""
        m = n - fenetre
        frac = sp.Rational(1, fenetre)
        rows = []
        for i in range(m):
            row = [sp.Integer(0)] * n
            for k in range(fenetre):
                row[i + k] = -frac
            row[i + fenetre] = sp.Integer(1)
            rows.append(row)
        A_twin = Matrix._from_exact_rows(rows)
        stmt = (
            f"$p \\in \\mathbb{{R}}^{{{n}}}$ est une série de prix. $d \\in \\mathbb{{R}}^{{{m}}}$ mesure, à partir du jour {fenetre + 1}, "
            f"l'écart entre le prix du jour et la moyenne des {fenetre} jours précédents :\n\n"
            f"$$d_i = p_{{i+{fenetre}}} - \\frac{{1}}{{{fenetre}}} \\sum_{{k=0}}^{{{fenetre - 1}}} p_{{i+k}}$$\n\n"
            f"Construire la matrice $A$ telle que $d = A p$."
        )
        sol = (
            f"1. **Taille** : $d$ possède {m} composantes et $p$ en a {n}, donc $A$ est de taille ${m} \\times {n}$.\n"
            f"2. **Ligne 1 ($i=1$)** : $d_1 = p_{{{fenetre + 1}}} - \\frac{{1}}{{{fenetre}}}(p_1 + \\dots + p_{{{fenetre}}})$, "
            f"ce qui donne la ligne 1 : {_vector_to_latex(A_twin.row(0))}^T.\n"
            f"3. En décalant d'une colonne à chaque ligne, on obtient la matrice $A$ :\n\n"
            f"$$A = {_matrix_to_latex(A_twin)}$$"
        )
        return TwinExercise(
            title=f"Écart à la moyenne glissante (fenêtre $k={fenetre}$, $n={n}$)",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def produit_scalaire_selection(n: int = 5, indices: tuple[int, ...] = (1, 4)) -> TwinExercise:
        """Jumeau pour les exercices de modélisation par produit scalaire a^T x."""
        coeffs = [sp.Integer(1 if (k + 1) in indices else 0) for k in range(n)]
        a_vec = Vector._from_exact(coeffs)
        terms = " + ".join(f"x_{idx}" for idx in indices)
        stmt = f"Pour $x \\in \\mathbb{{R}}^{{{n}}}$, écrire la somme ${terms}$ sous la forme $a^T x$."
        sol = (
            f"On identifie le coefficient devant chaque composante $x_k$ ($k = 1, \\dots, {n}$) :\n"
            f"- Les composantes sélectionnées sont {indices} (coefficient 1) et les autres ont un coefficient 0.\n"
            f"- On obtient le vecteur $a$ :\n\n"
            f"$$a = {_vector_to_latex(a_vec)}$$"
        )
        return TwinExercise(
            title="Modélisation sous la forme $a^T x$",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def statistiques_vecteur(values: tuple[int, ...] = (2, -1, 5, 2)) -> TwinExercise:
        """Jumeau pour les calculs de norm, avg, rms, std, distance."""
        v = Vector(values)
        with tracing(level=2) as t:
            avg_v = v.avg()
            rms_v = v.rms()
            std_v = v.std()
        exp = Explanation(t.tree, level=2)
        stmt = f"Pour le vecteur $x = {_vector_to_latex(v)}$ dans $\\mathbb{{R}}^{{{len(v)}}}$, calculer $\\text{{avg}}(x)$, $\\text{{rms}}(x)$ et $\\text{{std}}(x)$."
        sol = (
            f"- **Moyenne** : $\\text{{avg}}(x) = {sp.latex(avg_v)}$\n"
            f"- **Moyenne quadratique** : $\\text{{rms}}(x) = \\frac{{\\|x\\|}}{{\\sqrt{{{len(v)}}}}} = {sp.latex(rms_v)}$\n"
            f"- **Vecteur centré** : $x - \\text{{avg}}(x) \\mathbf{{1}} = {_vector_to_latex(v.demean())}$\n"
            f"- **Écart type** : $\\text{{std}}(x) = \\text{{rms}}(x - \\text{{avg}}(x) \\mathbf{{1}}) = {sp.latex(std_v)}$"
        )
        return TwinExercise(
            title="Moyenne, moyenne quadratique ($\\text{rms}$) et écart type ($\\text{std}$)",
            statement=stmt,
            solution_summary=sol,
            explanation=exp,
        )

    @staticmethod
    def combinaison_orthogonale(c1: int = 2, c2: int = -3) -> TwinExercise:
        """Jumeau pour la norme ou rms d'une combinaison de vecteurs orthogonaux."""
        stmt = (
            f"Soient $u$ et $v$ deux vecteurs orthogonaux de $\\mathbb{{R}}^n$ ($u \\perp v$). "
            f"Exprimer $\\|{c1} u + ({c2}) v\\|^2$ en fonction de $\\|u\\|$ et $\\|v\\|$."
        )
        sol = (
            f"1. On développe le produit scalaire :\n\n"
            f"   $$\\|{c1} u + ({c2}) v\\|^2 = ({c1} u + ({c2}) v)^T ({c1} u + ({c2}) v)$$\n"
            f"   $$= {c1**2} \\|u\\|^2 + 2 \\cdot ({c1 * c2}) (u^T v) + {c2**2} \\|v\\|^2$$\n\n"
            f"2. Comme $u \\perp v$, le produit scalaire est nul : $u^T v = 0$.\n"
            f"3. Conclusion :\n\n"
            f"   $$\\|{c1} u + ({c2}) v\\|^2 = {c1**2} \\|u\\|^2 + {c2**2} \\|v\\|^2$$"
        )
        return TwinExercise(
            title="Norme d'une combinaison de vecteurs orthogonaux",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def dimensions_expressions() -> TwinExercise:
        """Jumeau pour l'analyse de validité et dimensions d'expressions."""
        stmt = (
            "Soient $A \\in \\mathbb{R}^{3 \\times 4}$, $B \\in \\mathbb{R}^{4 \\times 2}$ et $x \\in \\mathbb{R}^4$. "
            "Les expressions (a) $A x$, (b) $B^T x$, (c) $A B + B$ sont-elles bien définies ? "
            "Si oui, donner leur dimension."
        )
        sol = (
            "- **(a)** $A$ ($3 \\times 4$) et $x$ ($4 \\times 1$) : les dimensions internes ($4 = 4$) coïncident $\\implies$ **valide**, dimension $3 \\times 1$ (vecteur de $\\mathbb{R}^3$).\n"
            "- **(b)** $B^T$ est de dimension $2 \\times 4$ et $x$ est $4 \\times 1$ : ($4 = 4$) $\\implies$ **valide**, dimension $2 \\times 1$.\n"
            "- **(c)** $A B$ est de dimension $3 \\times 2$ tandis que $B$ est $4 \\times 2$ : addition de dimensions différentes ($3 \\times 2 \\neq 4 \\times 2$) $\\implies$ **invalide**."
        )
        return TwinExercise(
            title="Analyse de compatibilité des dimensions",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def contre_exemple_guide(famille: str = "\\mathbb{R}^2, \\text{coefficients dans } \\{-1, 0, 1\\}") -> TwinExercise:
        """Jumeau d'orientation pour la recherche de contre-exemple."""
        stmt = (
            "Comment construire méthodiquement un contre-exemple simple en petite dimension ?"
        )
        sol = (
            f"**Indication d'existence** : un contre-exemple existe dans ${famille}$.\n\n"
            "**Méthode** :\n"
            "1. Choisir la plus petite dimension autorisée par l'énoncé (souvent $n = 2$).\n"
            "2. Tester des vecteurs de la base canonique $e_1 = (1, 0)$, $e_2 = (0, 1)$ ou $(1, 1)$ "
            "qui vérifient les hypothèses.\n"
            "3. Calculer les deux membres de l'affirmation et vérifier qu'ils diffèrent."
        )
        return TwinExercise(
            title="Méthode de construction d'un contre-exemple",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def convolution_polynomes(a_vals: tuple[int, ...] = (1, 2), b_vals: tuple[int, ...] = (3, -1, 1)) -> TwinExercise:
        """Jumeau pour le produit de convolution."""
        m, n = len(a_vals), len(b_vals)
        size = m + n - 1
        c = [0] * size
        for i in range(m):
            for j in range(n):
                c[i + j] += a_vals[i] * b_vals[j]
        stmt = (
            f"Calculer le produit de convolution $c = a * b$ des vecteurs "
            f"$a = {_vector_to_latex(Vector(a_vals))}$ et $b = {_vector_to_latex(Vector(b_vals))}$."
        )
        sol = (
            f"1. La dimension de $c = a * b$ est $m + n - 1 = {m} + {n} - 1 = {size}$.\n"
            f"2. Pour chaque $k \\in \\{{1, \\dots, {size}\\}}$ : $c_k = \\sum_{{i+j=k+1}} a_i b_j$ :\n\n"
            f"   $$c = {_vector_to_latex(Vector(c))}$$"
        )
        return TwinExercise(
            title="Produit de convolution de deux vecteurs",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def inverse_droite_exemple() -> TwinExercise:
        """Jumeau pour le calcul d'inverses à droite ou à gauche."""
        A = Matrix([[1, 0, 2], [0, 1, -1]])
        B1 = Matrix([[1, 0], [0, 1], [0, 0]])
        B2 = Matrix([[-1, 2], [1, 0], [1, -1]])
        stmt = (
            f"Pour la matrice $A = {_matrix_to_latex(A)}$ de taille $2 \\times 3$ (lignes indépendantes), "
            "trouver deux inverses à droite $B$ distinctes (telles que $A B = I_2$)."
        )
        sol = (
            "Une matrice $B \\in \\mathbb{R}^{3 \\times 2}$ vérifie $A B = I_2$ si ses deux colonnes $b_1, b_2$ "
            "satisfont $A b_1 = e_1$ et $A b_2 = e_2$ :\n\n"
            f"- En fixant la 3ᵉ composante libre à 0, on obtient :\n\n"
            f"  $$B_1 = {_matrix_to_latex(B1)}$$\n\n"
            f"- En fixant la 3ᵉ composante à $(1, -1)$, on obtient :\n\n"
            f"  $$B_2 = {_matrix_to_latex(B2)}$$\n\n"
            "Dans les deux cas, on vérifie $A B_1 = I_2$ et $A B_2 = I_2$ avec $B_1 \\neq B_2$."
        )
        return TwinExercise(
            title="Construction de plusieurs inverses à droite",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def gram_schmidt_exemple() -> TwinExercise:
        """Jumeau pour l'orthogonalisation de Gram-Schmidt."""
        a1 = Vector([1, 1, 0])
        a2 = Vector([1, 0, 1])
        a3 = Vector([2, 1, 1])
        with tracing(level=2) as t:
            res = GramSchmidt([a1, a2, a3]).run()
        exp = Explanation(t.tree, level=2)
        stmt = f"Appliquer Gram-Schmidt à la famille $a_1 = {_vector_to_latex(a1)}$, $a_2 = {_vector_to_latex(a2)}$, $a_3 = {_vector_to_latex(a3)}$."
        lignes = []
        for k, q in enumerate(getattr(res, "orthogonal", ()), start=1):
            lignes.append(f"- $\\tilde q_{k} = {_vector_to_latex(q)}$")
        sol = (
            "On orthogonalise successivement : $\\tilde q_k = a_k - \\sum_{j<k} \\frac{\\tilde q_j^T a_k}{\\|\\tilde q_j\\|^2} \\tilde q_j$.\n\n"
            + "\n".join(lignes)
            + "\n\n"
            + (
                f"À l'étape {res.dependent_index + 1}, le résidu est nul : la famille est **liée** "
                f"car {res.witness}."
                if not getattr(res, "independent", True)
                else "Aucun résidu n'est nul : la famille est **libre**."
            )
        )
        return TwinExercise(
            title="Test d'indépendance par Gram-Schmidt",
            statement=stmt,
            solution_summary=sol,
            explanation=exp,
        )

    @staticmethod
    def moindres_carres_exemple() -> TwinExercise:
        """Jumeau pour la mise sous forme ||A x - b||^2."""
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        b = Vector([2, 3, 6])
        with tracing(level=2) as t:
            res = LeastSquares(A, b).run()
        exp = Explanation(t.tree, level=2)
        stmt = (
            "On dispose de 3 mesures bruitées de $x_1$, de $x_2$ et de $x_1 + x_2$ : "
            "$y_1 = 2$, $y_2 = 3$, $y_3 = 6$. Écrire le problème sous la forme $\\min_x \\|A x - b\\|^2$."
        )
        x_hat_tex = _vector_to_latex(res.x_hat) if hasattr(res, 'x_hat') else ''
        sol = (
            "Chaque mesure correspond à une ligne du système $A x \\approx b$ :\n\n"
            "- Ligne 1 : $1 \\cdot x_1 + 0 \\cdot x_2 \\approx 2$\n"
            "- Ligne 2 : $0 \\cdot x_1 + 1 \\cdot x_2 \\approx 3$\n"
            "- Ligne 3 : $1 \\cdot x_1 + 1 \\cdot x_2 \\approx 6$\n\n"
            f"D'où les matrices du problème :\n\n"
            f"$$A = {_matrix_to_latex(A)}, \\quad b = {_vector_to_latex(b)}$$\n\n"
            f"L'estimateur des moindres carrés est $\\hat{{x}} = {x_hat_tex}$."
        )
        return TwinExercise(
            title="Modélisation par moindres carrés $\\min \\|A x - b\\|^2$",
            statement=stmt,
            solution_summary=sol,
            explanation=exp,
        )

    @staticmethod
    def kkt_norme_minimale() -> TwinExercise:
        """Jumeau pour le système KKT d'un problème sous contrainte C x = d."""
        stmt = (
            "Exprimer les conditions d'optimalité KKT du problème de norme minimale :\n\n"
            "$$\\min_x \\|x\\|^2 \\quad \\text{sous la contrainte} \\quad C x = d$$"
        )
        sol = (
            "1. C'est un problème de moindres carrés sous contrainte avec $A = I_n$ et $b = 0$.\n"
            "2. Le lagrangien est $L(x, z) = \\|x\\|^2 + z^T (C x - d)$.\n"
            "3. En annulant le gradient par rapport à $x$ : $2 x + C^T z = 0$, avec $C x = d$.\n"
            "4. Sous forme matricielle par blocs :\n\n"
            "   $$\\begin{bmatrix} 2 I & C^T \\\\ C & 0 \\end{bmatrix} \\begin{bmatrix} x \\\\ z \\end{bmatrix} = \\begin{bmatrix} 0 \\\\ d \\end{bmatrix}$$"
        )
        return TwinExercise(
            title="Système KKT et solution de norme minimale",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def matrice_par_effet() -> TwinExercise:
        """Jumeau : trouver la matrice d'une application linéaire décrite par son effet sur x."""
        A = Matrix([[0, 1], [1, 1], [2, 0]])
        stmt = (
            "Pour $x = (x_1, x_2) \\in \\mathbb{R}^2$, on définit $y \\in \\mathbb{R}^3$ par "
            "$y_1 = x_2$, $y_2 = x_1 + x_2$, $y_3 = 2 x_1$. Trouver la matrice $A$ telle que $y = A x$."
        )
        sol = (
            "1. **Taille** : l'entrée est dans $\\mathbb{R}^2$ et la sortie dans $\\mathbb{R}^3$, "
            "donc $A$ est de taille $3 \\times 2$.\n"
            "2. **Méthode des colonnes** : la colonne $j$ de $A$ est l'image du vecteur de base $e_j$.\n"
            "   - $x = e_1 = (1, 0)$ donne $y = (0, 1, 2)$ : c'est la colonne 1.\n"
            "   - $x = e_2 = (0, 1)$ donne $y = (1, 1, 0)$ : c'est la colonne 2.\n"
            "3. **Méthode des lignes** (équivalente) : la ligne $i$ contient les coefficients de $y_i$ "
            "devant $x_1, x_2$.\n\n"
            f"$$A = {_matrix_to_latex(A)}$$"
        )
        return TwinExercise(
            title="Matrice d'une application décrite par son effet",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def evaluation_polynome() -> TwinExercise:
        """Jumeau : valeurs et dérivées d'un polynôme comme produit matrice-vecteur."""
        A = Matrix([[1, 0, 0], [1, 1, 1], [0, 1, 2]])
        stmt = (
            "Soit $p(t) = c_1 + c_2 t + c_3 t^2$, de vecteur de coefficients $c \\in \\mathbb{R}^3$. "
            "Écrire $y = (p(0), p(1), p'(1))$ sous la forme $y = A c$."
        )
        sol = (
            "1. $p(0) = c_1$, d'où la ligne $(1, 0, 0)$.\n"
            "2. $p(1) = c_1 + c_2 + c_3$, d'où la ligne $(1, 1, 1)$.\n"
            "3. $p'(t) = c_2 + 2 c_3 t$, donc $p'(1) = c_2 + 2 c_3$, d'où la ligne $(0, 1, 2)$.\n\n"
            f"$$A = {_matrix_to_latex(A)}$$"
        )
        return TwinExercise(
            title="Valeurs et dérivées d'un polynôme",
            statement=stmt,
            solution_summary=sol,
        )

    @staticmethod
    def puissance_matrice() -> TwinExercise:
        """Jumeau : état d'un système dynamique linéaire après plusieurs pas (puissance de matrice)."""
        A = Matrix([[1, 0], [2, 1]])
        A2 = A @ A
        stmt = (
            f"Un système évolue selon $x_{{t+1}} = A x_t$ avec $A = {_matrix_to_latex(A)}$. "
            "Exprimer $x_{t+2}$ en fonction de $x_t$."
        )
        sol = (
            "1. $x_{t+2} = A x_{t+1} = A (A x_t) = A^2 x_t$ : on applique deux fois la matrice.\n"
            "2. On calcule le produit $A^2 = A A$ (ligne de gauche · colonne de droite) :\n\n"
            f"$$A^2 = {_matrix_to_latex(A)} {_matrix_to_latex(A)} = {_matrix_to_latex(A2)}$$\n\n"
            "3. Donc $x_{t+2} = A^2 x_t$. Pour trois pas, on calculerait de même $A^3 = A^2 A$."
        )
        return TwinExercise(title="Deux pas d'un système dynamique", statement=stmt, solution_summary=sol)

    @staticmethod
    def matrice_adjacence() -> TwinExercise:
        """Jumeau : matrice d'adjacence d'un petit graphe et produit F x."""
        F = Matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        stmt = (
            "Trois personnes sont liées ainsi : 1 est ami avec 2, et 2 est ami avec 3. "
            "Pour $x \\in \\mathbb{R}^3$, $y_i$ est la somme des $x_j$ sur les amis $j$ de $i$. "
            "Trouver $F$ telle que $y = F x$."
        )
        sol = (
            "1. $y_1 = x_2$, $y_2 = x_1 + x_3$, $y_3 = x_2$.\n"
            "2. La ligne $i$ de $F$ contient un 1 dans chaque colonne $j$ telle que $i$ et $j$ sont amis : "
            "c'est la matrice d'adjacence du graphe (symétrique, diagonale nulle).\n\n"
            f"$$F = {_matrix_to_latex(F)}$$"
        )
        return TwinExercise(title="Matrice d'adjacence d'un petit réseau", statement=stmt, solution_summary=sol)

    @staticmethod
    def mise_echelle_diagonale() -> TwinExercise:
        """Jumeau : effet de la multiplication par des matrices diagonales à gauche et à droite."""
        D = Matrix.diag([2, -1])
        A = Matrix([[1, 2], [3, 4]])
        E = Matrix.diag([1, 3])
        P = D @ A @ E
        stmt = (
            f"Avec $D = {_matrix_to_latex(D)}$, $A = {_matrix_to_latex(A)}$ et $E = {_matrix_to_latex(E)}$, "
            "calculer $D A E$ et décrire l'effet de $D$ et de $E$."
        )
        sol = (
            "1. Multiplier à gauche par $D$ multiplie la ligne 1 de $A$ par 2 et la ligne 2 par $-1$.\n"
            "2. Multiplier à droite par $E$ multiplie la colonne 1 par 1 et la colonne 2 par 3.\n"
            "3. Chaque coefficient est donc multiplié par le facteur de sa ligne et celui de sa colonne :\n\n"
            f"$$D A E = {_matrix_to_latex(P)}$$\n\n"
            "Par exemple, le coefficient $(2, 2)$ vaut $(-1) \\times 4 \\times 3 = -12$."
        )
        return TwinExercise(title="Mise à l'échelle des lignes et des colonnes", statement=stmt, solution_summary=sol)

    @staticmethod
    def inverse_produit() -> TwinExercise:
        """Jumeau : inverse d'un produit et d'une puissance de matrice."""
        A = Matrix([[1, 1], [0, 1]])
        A_inv = Matrix([[1, -1], [0, 1]])
        A2_inv = A_inv @ A_inv
        stmt = (
            f"Soit $A = {_matrix_to_latex(A)}$, dont l'inverse est $A^{{-1}} = {_matrix_to_latex(A_inv)}$. "
            "Calculer l'inverse de $A^2$ sans refaire de pivot de Gauss."
        )
        sol = (
            "1. Pour deux matrices inversibles, $(M N)^{-1} = N^{-1} M^{-1}$ (l'ordre s'inverse).\n"
            "2. Avec $M = N = A$ : $(A^2)^{-1} = A^{-1} A^{-1} = (A^{-1})^2$.\n"
            "3. On calcule donc le carré de l'inverse :\n\n"
            f"$$(A^2)^{{-1}} = {_matrix_to_latex(A2_inv)}$$\n\n"
            "4. Vérification : $A^2 (A^{-1})^2 = A (A A^{-1}) A^{-1} = A A^{-1} = I$."
        )
        return TwinExercise(title="Inverse d'un produit", statement=stmt, solution_summary=sol)

    @staticmethod
    def resolution_systeme() -> TwinExercise:
        """Jumeau : traduire des conditions en système linéaire puis le résoudre."""
        A = Matrix([[1, 1], [1, -1]])
        b = Vector([5, 1])
        with tracing(level=1) as t:
            res = GaussJordan(A, b).run()
        exp = Explanation(t.tree, level=1)
        x = res.solution.x if hasattr(res, "solution") and hasattr(res.solution, "x") else None
        stmt = (
            "Deux versements $c_1$ et $c_2$ totalisent 5 et leur différence $c_1 - c_2$ vaut 1. "
            "Retrouver $c = (c_1, c_2)$."
        )
        sol = (
            "1. Chaque condition donne une équation linéaire : $c_1 + c_2 = 5$ et $c_1 - c_2 = 1$.\n"
            f"2. Sous forme matricielle : $A c = b$ avec $A = {_matrix_to_latex(A)}$ et $b = {_vector_to_latex(b)}$.\n"
            "3. La réduction de Gauss-Jordan de $[A \\mid b]$ donne la solution unique "
            + (f"$c = {_vector_to_latex(x)}$." if x is not None else ".")
        )
        return TwinExercise(
            title="Des conditions à un système linéaire",
            statement=stmt,
            solution_summary=sol,
            explanation=exp,
        )

    @staticmethod
    def identite_blocs() -> TwinExercise:
        """Jumeau : produit de matrices par blocs."""
        stmt = (
            "Pour des blocs de tailles compatibles, calculer "
            "$\\begin{bmatrix} A & B \\\\ C & D \\end{bmatrix} \\begin{bmatrix} I \\\\ 0 \\end{bmatrix}$."
        )
        sol = (
            "1. On multiplie comme pour des coefficients, en respectant l'ordre des produits de blocs :\n\n"
            "$$\\begin{bmatrix} A & B \\\\ C & D \\end{bmatrix} \\begin{bmatrix} I \\\\ 0 \\end{bmatrix} "
            "= \\begin{bmatrix} A I + B 0 \\\\ C I + D 0 \\end{bmatrix}$$\n\n"
            "2. On simplifie chaque bloc : $A I = A$, $B 0 = 0$, etc.\n\n"
            "$$= \\begin{bmatrix} A \\\\ C \\end{bmatrix}$$\n\n"
            "3. Interprétation : multiplier à droite par $\\begin{bmatrix} I \\\\ 0 \\end{bmatrix}$ extrait "
            "le premier bloc de colonnes."
        )
        return TwinExercise(title="Produit par blocs", statement=stmt, solution_summary=sol)

    @staticmethod
    def inegalite_triangulaire() -> TwinExercise:
        """Jumeau : inégalité triangulaire pour deux vecteurs, sur un exemple puis en général."""
        a = Vector([3, 0])
        b = Vector([0, 4])
        stmt = (
            f"Avec $a = {_vector_to_latex(a)}$ et $b = {_vector_to_latex(b)}$, comparer $\\|a + b\\|$ et "
            "$\\|a\\| + \\|b\\|$, puis justifier l'inégalité en général."
        )
        sol = (
            f"1. Sur l'exemple : $\\|a + b\\| = {sp.latex((a + b).norm())}$ et $\\|a\\| + \\|b\\| = "
            f"{sp.latex(a.norm())} + {sp.latex(b.norm())} = {sp.latex(a.norm() + b.norm())}$.\n"
            "2. En général : $\\|a + b\\|^2 = \\|a\\|^2 + 2 a^T b + \\|b\\|^2 \\le \\|a\\|^2 + 2 \\|a\\| \\|b\\| + \\|b\\|^2 "
            "= (\\|a\\| + \\|b\\|)^2$, grâce à l'inégalité de Cauchy-Schwarz $a^T b \\le \\|a\\| \\|b\\|$.\n"
            "3. Un essai numérique illustre l'inégalité ; seule la preuve la justifie pour tous les vecteurs."
        )
        return TwinExercise(title="Inégalité triangulaire", statement=stmt, solution_summary=sol)

    # English aliases for twin exercise generators
    @staticmethod
    def moving_average(window: int = 2, n: int = 5, *, fenetre: int | None = None) -> TwinExercise:
        return _TwinGeneratorNamespace.moyenne_glissante(
            fenetre=fenetre if fenetre is not None else window,
            n=n,
        )

    inner_product_selection = produit_scalaire_selection
    vector_statistics = statistiques_vecteur
    orthogonal_combination = combinaison_orthogonale
    expression_dimensions = dimensions_expressions
    counterexample_guide = contre_exemple_guide
    polynomial_convolution = convolution_polynomes
    right_inverse_example = inverse_droite_exemple
    gram_schmidt_example = gram_schmidt_exemple
    least_squares_example = moindres_carres_exemple
    kkt_minimum_norm = kkt_norme_minimale
    matrix_from_action = matrice_par_effet
    polynomial_evaluation = evaluation_polynome
    matrix_power = puissance_matrice
    adjacency_matrix = matrice_adjacence
    diagonal_scaling = mise_echelle_diagonale
    product_inverse = inverse_produit
    system_solving = resolution_systeme
    block_product = identite_blocs
    triangle_inequality = inegalite_triangulaire


generators = _TwinGeneratorNamespace()
generateurs = generators
