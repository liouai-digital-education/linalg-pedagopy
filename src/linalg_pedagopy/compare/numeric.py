"""Comparaison exact vs virgule flottante (NumPy) et expériences numériques classiques."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import sympy as sp

from linalg_pedagopy.algorithms.gauss_jordan import GaussJordan
from linalg_pedagopy.algorithms.gram_schmidt import GramSchmidt
from linalg_pedagopy.algorithms.least_squares import LeastSquares
from linalg_pedagopy.algorithms.qr import QR
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing

# numpy est une dépendance optionnelle (option « compare ») : son absence ne doit pas empêcher
# d'importer linalg_pedagopy ; seules les comparaisons numériques l'exigent.
try:
    import numpy as np
except ImportError:  # pragma: no cover - dépend de l'installation
    np = None  # type: ignore[assignment, unused-ignore]


def _exiger_numpy() -> None:
    if np is None:
        raise ImportError(
            "Les comparaisons numériques demandent numpy : pip install \"linalg_pedagopy[compare]\"."
        )


def _to_numpy_float(obj: Matrix | Vector) -> np.ndarray:
    if isinstance(obj, Vector):
        return np.array([float(e.evalf()) for e in obj.entries], dtype=np.float64)
    return np.array(
        [[float(obj[i, j].evalf()) for j in range(obj.cols)] for i in range(obj.rows)],
        dtype=np.float64,
    )


def build_lauchli_matrix(n: int = 3, epsilon: Any = sp.Rational(1, 10**8)) -> Matrix:
    """Construit la matrice de Läuchli de taille (n+1) x n : [1...1 ; eps * I_n]."""
    eps = sp.sympify(epsilon)
    rows: list[list[sp.Expr]] = [[sp.Integer(1)] * n]
    for i in range(n):
        row = [eps if i == j else sp.Integer(0) for j in range(n)]
        rows.append(row)
    return Matrix._from_exact_rows(rows)


def build_hilbert_matrix(n: int) -> Matrix:
    """Construit la matrice de Hilbert exacte H_(i,j) = 1 / (i + j + 1)."""
    rows = [
        [sp.Rational(1, i + j + 1) for j in range(n)]
        for i in range(n)
    ]
    return Matrix._from_exact_rows(rows)


@dataclass(frozen=True)
class ComparisonReport:
    """Rapport de comparaison entre un calcul exact et son homologue flottant NumPy."""

    procedure_name: str
    exact_result: Any
    float_result: np.ndarray
    max_abs_error: float
    orthogonality_defect_float: float | None = None
    summary: str = ""

    def __str__(self) -> str:
        return self.summary


@dataclass(frozen=True)
class LauchliGSReport:
    """Résultat de l'expérience de Gram-Schmidt classique vs modifié vs exact sur Läuchli."""

    epsilon: float
    exact_orthogonality_error: int
    cgs_orthogonality_error: float
    mgs_orthogonality_error: float
    Q_exact: Matrix
    Q_cgs: np.ndarray
    Q_mgs: np.ndarray
    summary: str

    def __str__(self) -> str:
        return self.summary


@dataclass(frozen=True)
class LauchliLSReport:
    """Résultat de l'expérience Équations normales vs QR sur la matrice de Läuchli."""

    epsilon: float
    ata_exact: Matrix
    ata_float: np.ndarray
    ata_float_rank: int
    normal_equations_singular_in_float: bool
    x_exact: Vector
    x_qr_float: np.ndarray
    qr_relative_error: float
    summary: str

    def __str__(self) -> str:
        return self.summary


@dataclass(frozen=True)
class HilbertEntry:
    n: int
    condition_number: float
    relative_error: float


@dataclass(frozen=True)
class HilbertReport:
    """Résultat de l'expérience sur les matrices de Hilbert."""

    entries: tuple[HilbertEntry, ...]
    summary: str

    def __str__(self) -> str:
        return self.summary


@dataclass(frozen=True)
class InverseVsSolveReport:
    """Résultat de la comparaison entre inversion explicite A^(-1) b et résolution directe."""

    n: int
    solve_flops: int
    inverse_flops: int
    flop_ratio: float
    exact_solution: Vector
    solve_error: float
    inverse_error: float
    summary: str

    def __str__(self) -> str:
        return self.summary


def _classical_gram_schmidt_float(A_np: np.ndarray) -> np.ndarray:
    """Gram-Schmidt classique en flottant double précision (projette toujours a_i initial sur q_j)."""
    m, n = A_np.shape
    Q = np.zeros((m, n), dtype=np.float64)
    for i in range(n):
        a_i = A_np[:, i].copy()
        q_tilde = a_i.copy()
        for j in range(i):
            r_ji = float(np.dot(Q[:, j], a_i))
            q_tilde = q_tilde - r_ji * Q[:, j]
        Q[:, i] = q_tilde / np.linalg.norm(q_tilde)
    return Q


def _modified_gram_schmidt_float(A_np: np.ndarray) -> np.ndarray:
    """Gram-Schmidt modifié en flottant double précision (met à jour le vecteur à chaque projection)."""
    m, n = A_np.shape
    Q = np.zeros((m, n), dtype=np.float64)
    for i in range(n):
        v = A_np[:, i].copy()
        for j in range(i):
            r_ji = float(np.dot(Q[:, j], v))
            v = v - r_ji * Q[:, j]
        Q[:, i] = v / np.linalg.norm(v)
    return Q


def compare(procedure: Any, inputs: Any = None) -> ComparisonReport:
    """Exécute un algorithme en exact et en flottant (NumPy) et mesure l'écart."""
    _exiger_numpy()
    if isinstance(procedure, type) and inputs is not None:
        if isinstance(inputs, tuple):
            proc_inst = procedure(*inputs)
        else:
            proc_inst = procedure(inputs)
    else:
        proc_inst = procedure

    with suspend_tracing():
        exact_res = proc_inst.run()

    if isinstance(proc_inst, (GramSchmidt, QR)):
        Q_ex = exact_res.Q
        A_mat = proc_inst.A if isinstance(proc_inst, QR) else Matrix.from_columns(proc_inst.vectors)
        A_np = _to_numpy_float(A_mat)
        Q_cgs = _classical_gram_schmidt_float(A_np)
        Q_ex_np = _to_numpy_float(Q_ex)
        err = float(np.max(np.abs(Q_cgs - Q_ex_np)))
        defect = float(np.max(np.abs(Q_cgs.T @ Q_cgs - np.eye(A_mat.cols))))
        return ComparisonReport(
            procedure_name=type(proc_inst).__name__,
            exact_result=exact_res,
            float_result=Q_cgs,
            max_abs_error=err,
            orthogonality_defect_float=defect,
            summary=(
                f"{type(proc_inst).__name__} : erreur max flottant vs exact = {err:.3e}, "
                f"défaut d'orthogonalité max |Q^T Q - I| = {defect:.3e} (0 en exact)."
            ),
        )

    if isinstance(proc_inst, LeastSquares):
        x_ex = exact_res.x_hat
        A_np = _to_numpy_float(proc_inst.A)
        b_np = _to_numpy_float(proc_inst.b)
        x_fl, *_ = np.linalg.lstsq(A_np, b_np, rcond=None)
        x_ex_np = _to_numpy_float(x_ex)
        err = float(np.max(np.abs(x_fl - x_ex_np)))
        return ComparisonReport(
            procedure_name="LeastSquares",
            exact_result=exact_res,
            float_result=x_fl,
            max_abs_error=err,
            summary=f"LeastSquares : écart max |x_float - x_exact| = {err:.3e}.",
        )

    if isinstance(proc_inst, GaussJordan):
        A_np = _to_numpy_float(proc_inst.A)
        if proc_inst.b is not None and isinstance(proc_inst.b, Vector):
            b_np = _to_numpy_float(proc_inst.b)
            x_fl = np.linalg.solve(A_np, b_np)
            x_ex_np = _to_numpy_float(exact_res.solution.x)
            err = float(np.max(np.abs(x_fl - x_ex_np)))
            return ComparisonReport(
                procedure_name="GaussJordan",
                exact_result=exact_res,
                float_result=x_fl,
                max_abs_error=err,
                summary=f"GaussJordan : écart max |x_float - x_exact| = {err:.3e}.",
            )

    raise TypeError(f"Procédure non supportée par compare() : {type(proc_inst).__name__}")


def lauchli_gram_schmidt_experiment(
    epsilon: Any = sp.Rational(1, 10**8),
    n: int = 3,
) -> LauchliGSReport:
    """Expérience 1 : Gram-Schmidt classique vs modifié vs exact sur la matrice de Läuchli."""
    _exiger_numpy()
    A = build_lauchli_matrix(n=n, epsilon=epsilon)
    with suspend_tracing():
        gs_res = GramSchmidt(A.columns(), normalize="end").run()
        Q_exact = gs_res.Q  # type: ignore[union-attr]

    A_np = _to_numpy_float(A)
    Q_cgs = _classical_gram_schmidt_float(A_np)
    Q_mgs = _modified_gram_schmidt_float(A_np)

    ident = np.eye(n, dtype=np.float64)
    cgs_defect = float(np.max(np.abs(Q_cgs.T @ Q_cgs - ident)))
    mgs_defect = float(np.max(np.abs(Q_mgs.T @ Q_mgs - ident)))

    summary = (
        f"Matrice de Läuchli ({n + 1}x{n}, ε = {float(sp.sympify(epsilon).evalf()):.1e}) :\n"
        f"- Exact (SymPy)              : max |q_i^T q_j - δ_ij| = 0\n"
        f"- Gram-Schmidt classique     : max |q_i^T q_j - δ_ij| = {cgs_defect:.4f} (perte totale d'orthogonalité)\n"
        f"- Gram-Schmidt modifié (MGS) : max |q_i^T q_j - δ_ij| = {mgs_defect:.2e}"
    )
    return LauchliGSReport(
        epsilon=float(sp.sympify(epsilon).evalf()),
        exact_orthogonality_error=0,
        cgs_orthogonality_error=cgs_defect,
        mgs_orthogonality_error=mgs_defect,
        Q_exact=Q_exact,
        Q_cgs=Q_cgs,
        Q_mgs=Q_mgs,
        summary=summary,
    )


def lauchli_least_squares_experiment(
    epsilon: Any = sp.Rational(1, 10**8),
    n: int = 3,
) -> LauchliLSReport:
    """Expérience 2 : Équations normales vs QR sur la matrice de Läuchli (1 + ε^2 == 1 en machine)."""
    _exiger_numpy()
    A = build_lauchli_matrix(n=n, epsilon=epsilon)
    b = Vector([sp.Integer(1)] + [sp.Integer(i + 1) for i in range(n)])

    with suspend_tracing():
        ata_exact = A.gram()
        ls_exact = LeastSquares(A, b, method="rational_qr").run()
        x_exact = ls_exact.x_hat  # type: ignore[union-attr]

    A_np = _to_numpy_float(A)
    b_np = _to_numpy_float(b)
    ata_float = A_np.T @ A_np
    ata_rank = int(np.linalg.matrix_rank(ata_float))
    is_singular = bool(ata_rank < n or np.allclose(ata_float, np.ones((n, n))))

    # Résolution par QR NumPy (Householder)
    Q_np, R_np = np.linalg.qr(A_np, mode="reduced")
    x_qr_float = np.linalg.solve(R_np, Q_np.T @ b_np)
    x_ex_np = _to_numpy_float(x_exact)
    rel_err = float(np.linalg.norm(x_qr_float - x_ex_np) / np.linalg.norm(x_ex_np))

    summary = (
        f"Moindres carrés sur Läuchli (ε = {float(sp.sympify(epsilon).evalf()):.1e}) :\n"
        f"- En flottant, 1 + ε^2 == 1 : A^T A est arrondie en une matrice de 1 (rang {ata_rank} < {n}, singulière !).\n"
        f"- Les équations normales échouent en flottant, tandis que QR réussit (erreur relative = {rel_err:.2e})."
    )
    return LauchliLSReport(
        epsilon=float(sp.sympify(epsilon).evalf()),
        ata_exact=ata_exact,
        ata_float=ata_float,
        ata_float_rank=ata_rank,
        normal_equations_singular_in_float=is_singular,
        x_exact=x_exact,
        x_qr_float=x_qr_float,
        qr_relative_error=rel_err,
        summary=summary,
    )


def hilbert_conditioning_experiment(
    sizes: Sequence[int] = (3, 5, 7, 9),
) -> HilbertReport:
    """Expérience 3 : Croissance du conditionnement et erreur relative sur les matrices de Hilbert."""
    _exiger_numpy()
    entries: list[HilbertEntry] = []
    lines = ["Matrices de Hilbert H_n :"]
    for n in sizes:
        H = build_hilbert_matrix(n)
        x_true = Vector.ones(n)
        with suspend_tracing():
            b = H @ x_true
            sol_ex = GaussJordan(H, b).run().solution.x  # type: ignore[union-attr]
            assert sol_ex == x_true
        H_np = _to_numpy_float(H)
        b_np = _to_numpy_float(b)
        cond_num = float(np.linalg.cond(H_np))
        x_fl = np.linalg.solve(H_np, b_np)
        x_true_np = np.ones(n, dtype=np.float64)
        rel_err = float(np.linalg.norm(x_fl - x_true_np) / np.linalg.norm(x_true_np))
        entries.append(
            HilbertEntry(n=n, condition_number=cond_num, relative_error=rel_err)
        )
        lines.append(
            f"- n = {n:2d} : cond(H_n) ≈ {cond_num:.2e}, erreur relative flottante ≈ {rel_err:.2e} (exact : 0)"
        )
    return HilbertReport(entries=tuple(entries), summary="\n".join(lines))


def explicit_inverse_vs_solve_experiment(n: int = 6) -> InverseVsSolveReport:
    """Expérience 4 : Coût en flops et erreur supplémentaire de A^(-1) b face à une résolution directe."""
    _exiger_numpy()
    H = build_hilbert_matrix(n)
    x_true = Vector([sp.Integer((-1) ** i * (i + 1)) for i in range(n)])
    with suspend_tracing():
        b = H @ x_true

    H_np = _to_numpy_float(H)
    b_np = _to_numpy_float(b)

    x_solve = np.linalg.solve(H_np, b_np)
    x_inv = np.linalg.inv(H_np) @ b_np

    err_solve = float(np.linalg.norm(H_np @ x_solve - b_np))
    err_inv = float(np.linalg.norm(H_np @ x_inv - b_np))

    # Résolution d'un système ~ (2/3) n^3 flops, inversion complète ~ (8/3) n^3 ou 2 n^3 flops
    solve_flops = int(round((2.0 / 3.0) * (n**3) + 2 * (n**2)))
    inv_flops = int(round((8.0 / 3.0) * (n**3) + 2 * (n**2)))
    ratio = inv_flops / max(1, solve_flops)

    summary = (
        f"Inversion explicite A^(-1)b vs résolution directe (n = {n}) :\n"
        f"- Coût arithmétique : ~{inv_flops} flops pour A^(-1)b contre ~{solve_flops} flops (facteur ×{ratio:.1f}).\n"
        f"- Résidu ||A x - b|| : {err_solve:.2e} (solve direct) vs {err_inv:.2e} (via inv)."
    )
    return InverseVsSolveReport(
        n=n,
        solve_flops=solve_flops,
        inverse_flops=inv_flops,
        flop_ratio=ratio,
        exact_solution=x_true,
        solve_error=err_solve,
        inverse_error=err_inv,
        summary=summary,
    )
