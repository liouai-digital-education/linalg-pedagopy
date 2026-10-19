"""Script de démonstration de linalg_pedagopy : discussion paramétrique, comparaison numérique et tuteur."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys

# Ajout de src/ au chemin Python si le package n'est pas encore installé en mode editable
sys.path.insert(0, str(Path(__file__).parent / "src"))

from linalg_pedagopy import (
    GaussJordan,
    LeastSquares,
    Matrix,
    QR,
    Vector,
    symbols,
    tracing,
)
from linalg_pedagopy.compare import (
    lauchli_gram_schmidt_experiment,
    lauchli_least_squares_experiment,
)
from linalg_pedagopy.tuteur import exercice, glossaire


def main() -> None:
    print("=" * 76)
    print("DÉMONSTRATION — linalg_pedagopy v3.0")
    print("=" * 76)

    # 1. Discussion automatique selon un paramètre avec Gauss-Jordan
    print("\n--- 1. Discussion selon un paramètre ---")
    (a,) = symbols("a")
    A = Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]])
    b = Vector([1, 2, 3])

    with tracing(level=2):
        res_gj = GaussJordan(A, b).run()
    print(res_gj.explain(level=1))

    # 2. Factorisation QR rationnelle et normalisée
    print("\n--- 2. Factorisation QR et vérifications a posteriori ---")
    M = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]])
    qr_res = QR(M).run()
    print("Q_tilde (rationnel) =\n", qr_res.Q_tilde)
    print("R_tilde (rationnel) =\n", qr_res.R_tilde)
    print(qr_res.verify())

    # 3. Moindres carrés par QR rationnelle
    print("\n--- 3. Moindres carrés par QR rationnelle ---")
    y = Vector([1, 2, 2, 4])
    ls_res = LeastSquares(M, y).run()
    print("x_hat =", ls_res.x_hat)
    print("r_hat = A x_hat - b =", ls_res.r_hat)
    print(ls_res.verify())

    # 4. Comparaison exact vs flottant sur la matrice de Läuchli
    print("\n--- 4. Exact vs Flottant : Matrice de Läuchli ---")
    print(lauchli_gram_schmidt_experiment())
    print()
    print(lauchli_least_squares_experiment())

    # 5. Séance de tuteur
    print("\n--- 5. Séance de tuteur : « Écart à la moyenne glissante » et « Orthogonalité : vrai ou faux ? » ---")
    print(glossaire("running average"))
    t = Fraction(1, 3)
    ex64 = exercice("moyenne-glissante")
    print(ex64.enonce())
    print(ex64.indice())

    A_err = Matrix(
        [
            [-t, -t, -t, 1, 0, 0],
            [-t, -t, -t, 1, 0, 0],
            [0, 0, -t, -t, -t, 1],
        ]
    )
    print("\nDiagnostic sur une réponse erronée à la ligne 2 :")
    print(ex64.verifier(A_err))

    A_ok = Matrix(
        [
            [-t, -t, -t, 1, 0, 0],
            [0, -t, -t, -t, 1, 0],
            [0, 0, -t, -t, -t, 1],
        ]
    )
    print("\nValidation de la matrice corrigée :")
    print(ex64.verifier(A_ok))

    print("\nLaboratoire de contre-exemples sur « Orthogonalité : vrai ou faux ? » :")
    ex33 = exercice("orthogonalite-vrai-faux")
    ex33.predire(a="peut être faux", b="toujours vrai", c="peut être faux")
    lab = ex33.labo()
    print(lab.tester(a=Vector([1, 0, 0]), b=Vector([1, 1, 0]), c=Vector([0, 0, 1])))


if __name__ == "__main__":
    main()
