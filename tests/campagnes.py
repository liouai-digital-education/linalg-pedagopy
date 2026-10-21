"""Cas des campagnes de tests du bac à sable (carnets ``tests2`` à ``test4``).

Étape 3.1 du plan v6. Les carnets eux-mêmes ne sont pas dans le dépôt : les cas sont
reconstruits à partir du rapport d'évaluation du 21 octobre 2026.

- Les matrices de ``test4`` (tridiagonale, flèche, permutée cyclique, équicorrélation,
  Vandermonde) et celles de ``tests2`` sont celles du rapport ; seuls les seconds membres
  absents du rapport sont choisis ici.
- Les 9 tests limites de ``tests3`` sont reconstitués d'après leur description (même
  phénomène, mêmes conditions) ; le test 5 reproduit exactement la solution du rapport.
- La matrice bloc-triangulaire 6 × 6 n'est qu'esquissée dans le rapport (« 3 blocs 2 × 2
  diagonaux couplés supérieurement ») : les blocs choisis reproduisent le phénomène
  (saturation de ``max_cases=8``, plus de 8 branches avec ``max_cases=16``).

Ce module sert aux tests de caractérisation (``test_caracterisation_campagnes.py``) et au
script de mesure ``scripts/mesurer_performances.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import sympy as sp

from linalg_pedagopy import CaseSplit, GaussJordan, Matrix, Vector, symbols

a, b, c, m = symbols("a b c m")


@dataclass(frozen=True)
class Cas:
    """Un cas de campagne : ce qu'il illustre, le calcul, et s'il est lent (> 5 s)."""

    carnet: str
    description: str
    calcul: Callable[[], Any]
    lent: bool = False


def tridiagonale(n: int) -> Matrix:
    """a sur la diagonale, 1 sur les deux diagonales voisines."""
    return Matrix([[a if i == j else (1 if abs(i - j) == 1 else 0) for j in range(n)] for i in range(n)])


def fleche(n: int) -> Matrix:
    """Matrice flèche : a en (1, 1), des 1 sur la première ligne et la première colonne, 2 ailleurs sur la diagonale."""
    def coef(i: int, j: int) -> Any:
        if i == j:
            return a if i == 0 else 2
        return 1 if i == 0 or j == 0 else 0

    return Matrix([[coef(i, j) for j in range(n)] for i in range(n)])


def permutee_cyclique(n: int) -> Matrix:
    """-a sur la diagonale, 1 au-dessus et en bas à gauche : det = 1 - a**n (au signe près)."""
    return Matrix([[-a if i == j else (1 if j == (i + 1) % n else 0) for j in range(n)] for i in range(n)])


def equicorrelation(n: int) -> Matrix:
    """(a - b) I + b J : a sur la diagonale, b ailleurs."""
    return Matrix([[a if i == j else b for j in range(n)] for i in range(n)])


def bloc_triangulaire() -> Matrix:
    """Trois blocs 2 × 2 diagonaux (det (a²−1), (b²−1), (a−b)), des 1 au-dessus des blocs."""
    blocs = [[[a, 1], [1, a]], [[b, 1], [1, b]], [[a, b], [1, 1]]]
    M: list[list[Any]] = [[0] * 6 for _ in range(6)]
    for k, B in enumerate(blocs):
        for i in range(2):
            for j in range(2):
                M[2 * k + i][2 * k + j] = B[i][j]
    for i in range(6):
        for j in range(6):
            if j // 2 > i // 2:
                M[i][j] = 1
    return Matrix(M)


def vandermonde(*noeuds: Any) -> Matrix:
    n = len(noeuds)
    return Matrix([[x**k for k in range(n)] for x in noeuds])


def _gj(A: Matrix, rhs: Vector | None = None, **kw: Any) -> Callable[[], Any]:
    return lambda: GaussJordan(A, rhs, **kw).run()


def _inverse(A: Matrix, **kw: Any) -> Callable[[], Any]:
    return lambda: GaussJordan(A, compute_inverse=True, **kw).run()


CAS_CAMPAGNES: dict[str, Cas] = {
    # --- tests2 : inversion et plafonds de complexité
    "t2_circulante_3_parametres_inverse": Cas(
        "tests2", "circulante 3 × 3 en (a, b, c) : l'inversion dépasse les plafonds par défaut",
        _inverse(Matrix([[a, b, c], [c, a, b], [b, c, a]])), lent=True),
    "t2_blocs_4x4_inverse": Cas(
        "tests2", "matrice bloc-diagonale 4 × 4 creuse : l'inversion dépasse max_cases=8",
        _inverse(Matrix([[a, 1, 0, 0], [1, a, 0, 0], [0, 0, b, 1], [0, 0, 1, b]]))),
    "t2_asymetrie_factorisation_inverse": Cas(
        "tests2", "det (a − 1)(a² + a − 3) : condition en radicaux, inverse avec a² + a − 3 non factorisé",
        _inverse(Matrix([[a, 2, 1], [1, a, 1], [1, 1, a]]))),
    # --- tests3 : 9 tests limites de GaussJordan
    "t3_1_singuliere_partout": Cas(
        "tests3", "matrice singulière pour tout m ; compatible seulement si m = 2",
        _gj(Matrix([[1, 2], [2, 4]]), Vector([1, m]))),
    "t3_2_saut_de_rang_3_vers_1": Cas(
        "tests3", "det (a − 1)²(a + 2) : en a = 1 le rang tombe de 3 à 1",
        _gj(Matrix([[a, 1, 1], [1, a, 1], [1, 1, a]]), Vector([1, a, a**2]))),
    "t3_3_surdetermine_3x2": Cas(
        "tests3", "système 3 × 2 : la troisième ligne donne la condition de compatibilité m = 3",
        _gj(Matrix([[1, 1], [1, -1], [2, 1]]), Vector([2, 0, m]))),
    "t3_4_conditions_croisees": Cas(
        "tests3", "arbre emboîté : a ≠ b, puis a = b et b ≠ 1/2, puis a = b = 1/2",
        _gj(Matrix([[1, a], [1, b]]), Vector([1, 2 * b]))),
    "t3_5_pivot_quadratique": Cas(
        "tests3", "pivot a² − 2 : condition en ±√2, solution avec a² − 2 non factorisé (étape 3.2)",
        _gj(Matrix([[a**2 - 2, 1], [0, a - 1]]), Vector([1, 1]))),
    "t3_6_parametre_au_denominateur": Cas(
        "tests3", "coefficient 1/a : a ≠ 0 imposé par le domaine de définition",
        _gj(Matrix([[1 / a, 1], [1, 1]]), Vector([1, 2]))),
    "t3_7_rang_nul": Cas(
        "tests3", "m = 0 annule la matrice : la solution est R² tout entier",
        _gj(Matrix([[m, 0], [0, m]]), Vector([m, 2 * m]))),
    "t3_8_strategie_simplest": Cas(
        "tests3", "simplest échange L1 et L2 pour ne pas discuter sur le pivot a",
        _gj(Matrix([[a, 1], [1, 1]]), Vector([1, 2]))),
    "t3_9_homogene": Cas(
        "tests3", "système homogène : toujours compatible, dimension du noyau selon a",
        _gj(Matrix([[2, a, 1], [a, 2, 1], [1, 1, 1]]), Vector([0, 0, 0]))),
    # --- test4 : grosses matrices pleines et creuses
    "t4_tridiagonale_5x5": Cas(
        "test4", "pivots de Chebyshev ; la remontée remplit les zéros hors bande",
        _gj(tridiagonale(5), Vector([1, 0, 0, 0, 1]))),
    "t4_fleche_6x6": Cas(
        "test4", "matrice flèche : simplest choisit les pivots 2 et évite le remplissage",
        _gj(fleche(6), Vector([1, 0, 0, 0, 0, 0]))),
    "t4_bloc_triangulaire_6x6": Cas(
        "test4", "blocs indépendants : max_cases=8 saturé par le produit des singularités",
        _gj(bloc_triangulaire(), Vector([1] * 6)), lent=True),
    "t4_bloc_triangulaire_6x6_max16": Cas(
        "test4", "même matrice avec max_cases=16",
        _gj(bloc_triangulaire(), Vector([1] * 6), max_cases=16), lent=True),
    "t4_bloc_triangulaire_6x6_hypothese": Cas(
        "test4", "même matrice avec max_cases=16 et l'hypothèse a ≠ 1",
        _gj(bloc_triangulaire(), Vector([1] * 6), max_cases=16, assumptions="a!=1"), lent=True),
    "t4_permutee_cyclique_5x5": Cas(
        "test4", "det 1 − a⁵ : facteur a⁴ + a³ + a² + a + 1 sans racine réelle, aucune branche parasite",
        _gj(permutee_cyclique(5), Vector([1, 0, 0, 0, 0]))),
    "t4_equicorrelation_4x4": Cas(
        "test4", "(a − b) I + b J : fractions bivariées là où Sherman-Morrison suffirait",
        _gj(equicorrelation(4), Vector([1, 0, 0, 0]))),
    "t4_equicorrelation_5x5_hypothese": Cas(
        "test4", "même famille en 5 × 5, sous l'hypothèse a ≠ b",
        _gj(equicorrelation(5), Vector([1, 0, 0, 0, 0]), assumptions="a!=b"), lent=True),
    "t4_vandermonde_4x4": Cas(
        "test4", "V(1, 2, 3, a) : det 2(a − 1)(a − 2)(a − 3), puissances de a à simplifier",
        _gj(vandermonde(1, 2, 3, a), Vector([0, 0, 0, 1]))),
}


def resultats(res: Any) -> list[Any]:
    """Les résultats de chaque branche (ou le résultat seul)."""
    if isinstance(res, CaseSplit):
        return [br.result for br in res.branches]
    return [res]


def taille(res: Any) -> int:
    """Nombre d'opérations SymPy dans les matrices réduites de toutes les branches."""
    total = 0
    for r in resultats(res):
        M = getattr(r, "augmented_rref", None)
        if M is not None:
            total += sum(int(sp.count_ops(e)) for ligne in M.entries_grid for e in ligne)
    return total
