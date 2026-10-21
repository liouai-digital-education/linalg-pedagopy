"""Tests du module compare/ (§5.7 : matrice de Läuchli, Hilbert, inversion vs solve)."""

from __future__ import annotations

from linalg_pedagopy import QR, compare
from linalg_pedagopy.compare import (
    build_lauchli_matrix,
    explicit_inverse_vs_solve_experiment,
    hilbert_conditioning_experiment,
    lauchli_gram_schmidt_experiment,
    lauchli_least_squares_experiment,
)


def test_lauchli_gram_schmidt_experiment() -> None:
    rep = lauchli_gram_schmidt_experiment()
    assert rep.exact_orthogonality_error == 0
    # En flottant, GS classique perd l'orthogonalité (~0.5) alors que MGS reste ~1e-8
    assert rep.cgs_orthogonality_error > 0.1
    assert rep.mgs_orthogonality_error < 1e-7
    assert rep.Q_exact.has_orthonormal_columns() is True


def test_lauchli_least_squares_experiment() -> None:
    rep = lauchli_least_squares_experiment()
    assert rep.normal_equations_singular_in_float is True
    assert rep.ata_float_rank == 1
    assert rep.qr_relative_error < 1e-6


def test_hilbert_and_inverse_vs_solve_experiments() -> None:
    h_rep = hilbert_conditioning_experiment(sizes=(3, 5, 7))
    assert len(h_rep.entries) == 3
    assert h_rep.entries[-1].condition_number > h_rep.entries[0].condition_number

    inv_rep = explicit_inverse_vs_solve_experiment(n=5)
    assert inv_rep.inverse_flops > inv_rep.solve_flops

    A = build_lauchli_matrix(n=3)
    c_rep = compare(QR(A))
    assert c_rep.orthogonality_defect_float is not None
    assert c_rep.orthogonality_defect_float > 0.1


def test_import_sans_numpy() -> None:
    """numpy est optionnel : le paquet s'importe sans lui, seules les comparaisons l'exigent."""
    import subprocess
    import sys

    code = (
        "import sys; sys.modules['numpy'] = None\n"
        "import linalg_pedagopy\n"
        "from linalg_pedagopy import tuteur, compare, Matrix\n"
        "assert tuteur.exercice('moyenne-glissante').verifier(Matrix.zeros(3, 6)).valide is False\n"
        "try:\n"
        "    compare('gram_schmidt', Matrix([[1, 0], [0, 1]]))\n"
        "except ImportError as e:\n"
        "    assert 'linalg_pedagopy[compare]' in str(e)\n"
        "else:\n"
        "    raise AssertionError('ImportError attendue')\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
