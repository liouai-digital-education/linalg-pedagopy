# `linalg_pedagopy` v3.0 — Algèbre linéaire formelle et pédagogique

`linalg_pedagopy` est un package Python orienté objet conçu pour **enseigner et apprendre l'algèbre linéaire par le calcul formel** en L1–L2. Il s'appuie sur *Introduction to Applied Linear Algebra — Vectors, Matrices, and Least Squares (VMLS)* de Stephen Boyd et Lieven Vandenberghe, complété par la réduction de Gauss-Jordan (Lay, Strang) et un **tuteur interactif** pour le recueil d'exercices officiel de VMLS.

## Points forts

1. **Exactitude garantie** : rationnels, radicaux et fractions rationnelles en des paramètres réels (`real=True`), avec politique explicite de coercition des flottants (`float_policy`) et oracle de nullité à quatre verdicts (`ZERO`, `NONZERO`, `CONDITIONAL`, `UNKNOWN`).
2. **Discussion automatique selon un paramètre (`CaseSplit`)** : lorsqu'un pivot ou un test de compatibilité dépend d'un paramètre, l'algorithme construit automatiquement l'arbre des cas génériques et particuliers.
3. **Traçabilité hiérarchique contextuelle** : chaque procédure (`GaussJordan`, `BackSubstitution`, `ForwardSubstitution`, `GramSchmidt`, `QR`, `LeastSquares`) enregistre un arbre d'étapes consultable à 4 niveaux de détail (`0` à `3`) en texte Unicode, LaTeX, Markdown ou HTML.
4. **Tuteur VMLS (`linalg_pedagopy.tuteur`)** : accompagne l'étudiant sur les exercices du recueil *Additional Exercises for VMLS* dans JupyterLab avec indices gradués (niveaux 1 à 4), exercice jumeau résolu, laboratoire de contre-exemples et diagnostics ciblés **sans jamais dévoiler la solution en mode étudiant**.

## Exemple rapide

```python
from linalg_pedagopy import Matrix, Vector, symbols, tracing, GaussJordan, LeastSquares
from linalg_pedagopy.tuteur import exercice

# 1. Discussion automatique selon un paramètre
a, = symbols("a")
A = Matrix([[1, 1, 1], [1, a, 1], [1, 1, a]])
b = Vector([1, 2, 3])

with tracing(level=2):
    res = GaussJordan(A, b).run()
print(res.explain())

# 2. Moindres carrés par factorisation QR rationnelle
M = Matrix([[1, 0], [1, 1], [1, 2], [1, 3]])
y = Vector([1, 2, 2, 4])
ls = LeastSquares(M, y).run()
print(ls.x_hat)
print(ls.verify())

# 3. Séance avec le tuteur VMLS
ex = exercice("6.4")
print(ex.enonce())
print(ex.indice())
```

## Licence

Distribué sous licence MIT.
