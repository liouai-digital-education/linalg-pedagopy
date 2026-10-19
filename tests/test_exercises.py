"""Tests des générateurs d'exercices (§5.6.1) et de la validation d'opérations (§5.6.3, Annexe C)."""

from __future__ import annotations

import sympy as sp

from linalg_pedagopy import (
    CaseSplit,
    GaussJordan,
    LeastSquares,
    Matrix,
    QR,
    Vector,
    cayley_orthogonal,
    check_gram_schmidt_step,
    check_row_operation,
    generate_clean_least_squares,
    generate_integer_rref_matrix,
    generate_parametric_system,
    generate_rational_qr_matrix,
    generate_unimodular_matrix,
    symbols,
)


def test_cayley_orthogonal_verified_example_from_plan() -> None:
    """Vérifie l'exemple explicite de la page 16 du plan v3."""
    S = Matrix([[0, 1, 2], [-1, 0, "1/2"], [-2, "-1/2", 0]])
    Q = cayley_orthogonal(S)
    expected = sp.Rational(1, 25) * Matrix(
        [[-15, -16, -12], [0, 15, -20], [20, -12, -9]]
    )
    assert Q == expected
    assert (Q.T @ Q) == Matrix.identity(3)


def test_five_clean_generators_properties() -> None:
    # 1. Matrice unimodulaire entière -> inverse entière
    U = generate_unimodular_matrix(3, seed=42)
    U_inv = U.inv()
    assert isinstance(U_inv, Matrix)
    assert all(e.is_Integer for e in U_inv.flat_entries)

    # 2. Forme échelonnée réduite entière
    A_rref, R_target = generate_integer_rref_matrix(3, 4, rank=2, seed=42)
    assert A_rref.rref() == R_target
    assert all(e.is_Integer for e in R_target.flat_entries)

    # 3. QR rationnelle sans radicaux
    A_qr, Q_expected, R_expected = generate_rational_qr_matrix(3, seed=42)
    qr_res = QR(A_qr).run()
    assert all(e.is_Rational for e in qr_res.Q.flat_entries)  # type: ignore[union-attr]
    assert all(e.is_Rational for e in qr_res.R.flat_entries)  # type: ignore[union-attr]
    assert qr_res.Q == Q_expected  # type: ignore[union-attr]
    assert qr_res.R == R_expected  # type: ignore[union-attr]

    # 4. Moindres carrés à solution entière choisie
    A_ls, b_ls, x_hat_true, r_hat_true = generate_clean_least_squares(4, 2, seed=42)
    ls_res = LeastSquares(A_ls, b_ls).run()
    assert ls_res.x_hat == x_hat_true  # type: ignore[union-attr]
    assert ls_res.r_hat == r_hat_true  # type: ignore[union-attr]

    # 5. Système paramétré à valeur critique rationnelle
    A_p, b_p, param, crit = generate_parametric_system(3, param_name="a", critical_value=2, seed=42)
    gj_p = GaussJordan(A_p, b_p).run()
    assert isinstance(gj_p, CaseSplit)
    assert gj_p.at(a=2).rank < 3


def test_interactive_session_and_annexe_c_errors() -> None:
    A = Matrix([[1, 2], [3, 5]])
    b = Vector([5, 13])
    s = GaussJordan(A, b).interactive()

    # 1. Opération valide et utile (§5.6.3)
    fb1 = s.propose("L2 <- L2 - 3*L1")
    assert fb1.status == "valid_useful"
    assert "Le coefficient (2,1) est maintenant nul" in fb1.message

    # 2. Dilatation par 0 (Annexe C)
    fb_zero = s.propose("L2 <- 0*L2")
    assert fb_zero.status == "invalid"
    assert fb_zero.error_code == "zero_scaling"

    # 3. Transvection d'une ligne par elle-même (Annexe C)
    fb_self = s.propose("L2 <- L2 - L2")
    assert fb_self.status == "invalid"
    assert fb_self.error_code == "self_transvection"

    # 4. Opération appliquée à A mais pas au second membre (Annexe C)
    fb_lhs = s.propose("L2 <- -L2", only_lhs=True)
    assert fb_lhs.status == "invalid"
    assert fb_lhs.error_code == "only_lhs"

    # 5. Erreur de signe dans le coefficient de transvection (Annexe C)
    aug_test = Matrix([[1, 2, 5], [3, 5, 13]])
    fb_sign = check_row_operation(aug_test, "L2 <- L2 + 3*L1", num_lhs_cols=2)
    assert fb_sign.error_code == "sign_error"

    # 6. Division par un pivot dépendant d'un paramètre sans discussion (Annexe C)
    (a,) = symbols("a")
    aug_param = Matrix([[1, 0, 1], [0, a - 1, 2]])
    fb_param = check_row_operation(aug_param, "L2 <- (1/(a - 1))*L2", num_lhs_cols=2)
    assert fb_param.status == "invalid"
    assert fb_param.error_code == "parameter_division_without_discussion"

    # 7 & 8. Erreurs Gram-Schmidt (oubli de diviser par q_tilde^T q_tilde, et normalisation précoce)
    q1 = Vector([1, 1])  # ||q1||^2 = 2
    a2 = Vector([2, 0])
    fb_gs_div = check_gram_schmidt_step(a2, [q1], a2 - q1.dot(a2) * q1)
    assert fb_gs_div.error_code == "missing_norm_sq_division"

    fb_gs_early = check_gram_schmidt_step(a2, [q1], Vector([1, -1]), normalized_early=True)
    assert fb_gs_early.error_code == "early_normalization"

    assert "Suggestion" in s.hint()
