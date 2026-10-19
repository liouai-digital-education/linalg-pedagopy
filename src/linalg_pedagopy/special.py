"""Matrices structurées classiques, construites exactement.

Ces constructeurs fournissent les matrices que l'on rencontre dans tout cours
d'algèbre linéaire appliquée : différences, sommes cumulées, moyennes glissantes,
Vandermonde, convolution (Toeplitz), sélection et renversement de composantes.

Les indices de composantes sont comptés à partir de 0, comme ``Vector.unit``.
Chaque fonction possède un alias français.
"""

from __future__ import annotations

from typing import Any, Sequence

import sympy as sp

from linalg_pedagopy.core.field import to_exact
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector

__all__ = [
    "convolution",
    "convolution_matrix",
    "difference_matrix",
    "matrice_convolution",
    "matrice_differences",
    "matrice_moyenne_glissante",
    "matrice_renversement",
    "matrice_selection",
    "matrice_somme_cumulee",
    "moving_average_matrix",
    "reversal_matrix",
    "running_sum_matrix",
    "selection_matrix",
    "vandermonde",
]


def _check_size(n: int, minimum: int = 1, name: str = "n") -> int:
    n = int(n)
    if n < minimum:
        raise ValueError(f"{name} doit être un entier ≥ {minimum} (reçu : {n}).")
    return n


def difference_matrix(n: int) -> Matrix:
    """Matrice des différences premières D, de taille (n−1)×n : (D x)_i = x_{i+1} − x_i."""
    n = _check_size(n, 2)
    rows = [[sp.Integer(0)] * n for _ in range(n - 1)]
    for i in range(n - 1):
        rows[i][i] = sp.Integer(-1)
        rows[i][i + 1] = sp.Integer(1)
    return Matrix._from_exact_rows(rows)


def running_sum_matrix(n: int) -> Matrix:
    """Matrice des sommes cumulées S, triangulaire inférieure n×n : (S x)_i = x_1 + … + x_i."""
    n = _check_size(n)
    rows = [[sp.Integer(1 if j <= i else 0) for j in range(n)] for i in range(n)]
    return Matrix._from_exact_rows(rows)


def moving_average_matrix(n: int, k: int) -> Matrix:
    """Matrice de moyenne glissante sur k valeurs, de taille (n−k+1)×n.

    La ligne i calcule (x_i + x_{i+1} + … + x_{i+k−1}) / k.
    """
    n = _check_size(n)
    k = _check_size(k, 1, "k")
    if k > n:
        raise ValueError(f"La fenêtre k = {k} dépasse la taille n = {n}.")
    w = sp.Rational(1, k)
    rows = [[w if i <= j < i + k else sp.Integer(0) for j in range(n)] for i in range(n - k + 1)]
    return Matrix._from_exact_rows(rows)


def vandermonde(points: Sequence[Any], degree: int | None = None) -> Matrix:
    """Matrice de Vandermonde : la ligne i vaut (1, t_i, t_i², …, t_i^degree).

    Par défaut ``degree = len(points) − 1`` (matrice carrée). Multiplier par le vecteur
    des coefficients c d'un polynôme donne ses valeurs aux points t_i.
    """
    ts = [to_exact(t) for t in points]
    if not ts:
        raise ValueError("Il faut au moins un point.")
    d = len(ts) - 1 if degree is None else _check_size(degree, 0, "degree")
    rows = [[sp.expand(t**p) for p in range(d + 1)] for t in ts]
    return Matrix._from_exact_rows(rows)


def convolution_matrix(b: Vector | Sequence[Any], n: int) -> Matrix:
    """Matrice de Toeplitz T(b), de taille (n+m−1)×n, telle que T(b) a = b * a pour a ∈ R^n."""
    b_entries = list(b.entries) if isinstance(b, Vector) else [to_exact(x) for x in b]
    m = len(b_entries)
    n = _check_size(n)
    if m == 0:
        raise ValueError("Le vecteur b ne doit pas être vide.")
    rows = [[sp.Integer(0)] * n for _ in range(n + m - 1)]
    for j in range(n):
        for i, bi in enumerate(b_entries):
            rows[i + j][j] = bi
    return Matrix._from_exact_rows(rows)


def convolution(a: Vector | Sequence[Any], b: Vector | Sequence[Any]) -> Vector:
    """Produit de convolution c = a * b : c_k = Σ_{i+j=k} a_i b_j (taille n+m−1)."""
    a_entries = list(a.entries) if isinstance(a, Vector) else [to_exact(x) for x in a]
    b_entries = list(b.entries) if isinstance(b, Vector) else [to_exact(x) for x in b]
    if not a_entries or not b_entries:
        raise ValueError("Les deux vecteurs doivent être non vides.")
    c = [sp.Integer(0)] * (len(a_entries) + len(b_entries) - 1)
    for i, ai in enumerate(a_entries):
        for j, bj in enumerate(b_entries):
            c[i + j] += ai * bj
    return Vector([sp.expand(x) for x in c])


def selection_matrix(indices: Sequence[int], n: int) -> Matrix:
    """Matrice de sélection : la ligne r vaut e_{indices[r]}ᵀ (indices comptés à partir de 0)."""
    n = _check_size(n)
    rows = []
    for idx in indices:
        if not 0 <= int(idx) < n:
            raise ValueError(f"Indice {idx} hors de [0, {n - 1}].")
        rows.append([sp.Integer(1 if j == int(idx) else 0) for j in range(n)])
    if not rows:
        raise ValueError("Il faut sélectionner au moins une composante.")
    return Matrix._from_exact_rows(rows)


def reversal_matrix(n: int) -> Matrix:
    """Matrice de renversement n×n : (R x) = (x_n, …, x_1)."""
    n = _check_size(n)
    return selection_matrix(list(range(n - 1, -1, -1)), n)


# Alias français
matrice_differences = difference_matrix
matrice_somme_cumulee = running_sum_matrix
matrice_moyenne_glissante = moving_average_matrix
matrice_convolution = convolution_matrix
matrice_selection = selection_matrix
matrice_renversement = reversal_matrix
