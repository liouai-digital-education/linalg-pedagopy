"""Vérificateur « propriete » : objet qui doit vérifier une propriété (inverse, solution…)."""

from __future__ import annotations

from typing import Any, Mapping

from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tuteur.registre import VerifierType, register_verifier, requires
from linalg_pedagopy.tuteur.verificateurs.commun import (
    VerificationResult,
    sans_seance,
)


def verify_property(
    response: Any,
    spec: Mapping[str, Any],
    data: Mapping[str, Any],
) -> VerificationResult:
    """Vérifie une réponse par sa propriété caractéristique, sans corrigé stocké."""
    prop_kind = str(spec.get("propriete", spec.get("property", "right_inverse")))

    with suspend_tracing():
        if prop_kind == "two_right_inverses":
            A = data["A"]
            if not isinstance(response, (tuple, list)) or len(response) != 2:
                return VerificationResult(
                    False,
                    "Fournissez un couple (B1, B2) de deux matrices inverses à droite distinctes.",
                )
            try:
                B1 = response[0] if isinstance(response[0], Matrix) else Matrix(response[0])
                B2 = response[1] if isinstance(response[1], Matrix) else Matrix(response[1])
            except Exception:
                return VerificationResult(
                    False,
                    "B1 et B2 doivent être deux matrices valides.",
                )
            expected_shape = (A.cols, A.rows)
            for idx, B in enumerate((B1, B2), start=1):
                if B.shape != expected_shape:
                    return VerificationResult(
                        False,
                        f"B{idx} a la taille {B.shape}, alors qu'une inverse à droite de A ({A.shape}) doit être de taille {expected_shape}.",
                    )
                prod = A @ B
                if prod != Matrix.identity(A.rows):
                    return VerificationResult(
                        False,
                        f"Pour B{idx}, le produit A B{idx} vaut {prod} ≠ I_{A.rows}.",
                    )
            if B1 == B2:
                return VerificationResult(
                    False,
                    "A B1 = I et A B2 = I sont vérifiées, mais vos deux matrices B1 et B2 sont identiques ! "
                    "Choisissez deux valeurs différentes pour la variable libre.",
                )
            return VerificationResult(
                True,
                f"Bravo ! A B1 = I_{A.rows}, A B2 = I_{A.rows} et B1 ≠ B2 : vos deux inverses à droite sont valides.",
            )

        if prop_kind == "left_right_inverse_row":
            A = data["A"]
            try:
                B = response if isinstance(response, Matrix) else Matrix(response)
            except Exception:
                return VerificationResult(False, "Votre réponse doit être une matrice colonne B.")
            if B.shape != (A.cols, 1):
                return VerificationResult(
                    False,
                    f"Pour une matrice ligne A de taille {A.shape}, une inverse à droite B doit être de taille ({A.cols}, 1).",
                )
            prod = A @ B
            if prod == Matrix.identity(1):
                return VerificationResult(
                    True,
                    "Exact ! A B = [1] : votre colonne B est bien une inverse à droite de A (et A n'a pas d'inverse à gauche car ses colonnes sont liées).",
                )
            return VerificationResult(
                False,
                f"Avec votre matrice B, le produit A B vaut {prod} au lieu de [1].",
            )

        if prop_kind == "linear_system_solution":
            A = data["A"]
            b = data["b"]
            try:
                c_vec = response if isinstance(response, Vector) else Vector(response)
            except Exception:
                return VerificationResult(False, "Votre réponse doit être un vecteur.")
            if len(c_vec) != A.cols:
                return VerificationResult(
                    False,
                    f"Votre vecteur est de taille {len(c_vec)}, attendu {A.cols}.",
                )
            calc_b = A @ c_vec
            if calc_b == b:
                return VerificationResult(
                    True,
                    "Exact ! Votre vecteur de flux de trésorerie reproduit toutes les valeurs actuelles nettes annoncées.",
                )
            return VerificationResult(
                False,
                f"Avec votre vecteur c, les VAN obtenues sont A c = {calc_b} (attendu : {b}).",
            )

        if prop_kind == "square_inverse":
            A = data["A"]
            B_inv = A.inv(strict=True)
            assert isinstance(B_inv, Matrix)
            if isinstance(response, str):
                cleaned = response.replace(" ", "")
                if cleaned in ("B@B", "B**2", "B^2", "(A^-1)^2", "A^-2"):
                    return VerificationResult(
                        True,
                        "Exact ! Comme A² B² = A (A B) B = A I B = A B = I, l'inverse de A² est B² = (A⁻¹)².",
                    )
            try:
                mat_stu = response if isinstance(response, Matrix) else Matrix(response)
            except Exception:
                return VerificationResult(False, "Fournissez la formule ('B^2') ou la matrice inverse de A².")
            prod = (A @ A) @ mat_stu
            if prod == Matrix.identity(A.rows):
                return VerificationResult(
                    True,
                    "Exact ! Le produit A² · X vaut bien I : votre matrice est l'inverse de A².",
                )
            return VerificationResult(
                False,
                f"Le produit A² par votre matrice donne {prod} ≠ I.",
            )

        if prop_kind == "kkt_minimum_norm":
            C = data["C"]
            d = data["d"]
            try:
                x_stu = response if isinstance(response, Vector) else Vector(response)
            except Exception:
                return VerificationResult(False, "Votre réponse doit être un vecteur x.")
            if len(x_stu) != C.cols:
                return VerificationResult(
                    False,
                    f"Votre vecteur x est de taille {len(x_stu)}, attendu {C.cols}.",
                )
            cx = C @ x_stu
            if cx != d:
                return VerificationResult(
                    False,
                    f"Votre vecteur ne satisfait pas la contrainte C x = d : C x = {cx} ≠ {d}.",
                )
            cct_inv = (C @ C.T).inv(strict=True)
            assert isinstance(cct_inv, Matrix)
            x_opt = C.T @ (cct_inv @ d)
            if x_stu == x_opt:
                return VerificationResult(
                    True,
                    "Exact ! Votre vecteur x vérifie C x = d et les conditions KKT de norme minimale.",
                )
            return VerificationResult(
                False,
                f"Votre vecteur vérifie C x = d (||x||² = {x_stu.norm_sq()}), mais n'est pas de norme minimale "
                "(2x + C^T z = 0 n'est pas satisfait).",
            )

    return VerificationResult(False, f"Propriété {prop_kind!r} non reconnue.")


def _cross_check_property(session: Any, verif: Mapping[str, Any], raw_data: Mapping[str, Any]) -> list[str]:
    prop = str(verif.get("propriete", ""))
    if prop == "left_right_inverse_row":
        A = raw_data["A"]
        # Construct a right inverse via A^T (A A^T)^{-1}
        aat_inv = (A @ A.T).inv(strict=True)
        assert isinstance(aat_inv, Matrix)
        if not session.verify(A.T @ aat_inv).valid:
            return ["Cross-check échoué : la pseudo-inverse à droite A^T(AA^T)^-1 est rejetée."]
    elif prop == "square_inverse":
        A_inv = raw_data["A"].inv(strict=True)
        assert isinstance(A_inv, Matrix)
        if not session.verify(A_inv @ A_inv).valid:
            return ["Cross-check échoué : (A^-1)^2 est rejetée."]
    elif prop == "linear_system_solution":
        sol = raw_data["A"].solve(raw_data["b"])
        if not session.verify(sol.x).valid:
            return ["Cross-check échoué : la solution de A.solve(b) est rejetée."]
    elif prop == "two_right_inverses":
        B1 = Matrix([[1, 1], [0, 1], [0, 0]])
        B2 = Matrix([[-2, -2], [-1, 0], [1, 1]])
        if not session.verify((B1, B2)).valid:
            return ["Cross-check échoué : deux inverses à droite valides sont rejetées."]
    elif prop == "kkt_minimum_norm":
        C = raw_data["C"]
        cct_inv = (C @ C.T).inv(strict=True)
        assert isinstance(cct_inv, Matrix)
        if not session.verify(C.T @ (cct_inv @ raw_data["d"])).valid:
            return ["Cross-check échoué : la solution KKT est rejetée."]
    return []


register_verifier(
    VerifierType(
        "propriete",
        ("property",),
        sans_seance(verify_property),
        "l'objet demandé par l'énoncé (vecteur, matrice ou couple de matrices).",
        requires("propriete", message="Le vérificateur 'propriete' requiert un champ 'propriete'."),
        _cross_check_property,
    )
)
