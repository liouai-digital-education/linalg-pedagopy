"""Mesure la couverture des docstrings des éléments publics du paquet.

Un élément public est un module, une classe, une fonction ou une méthode dont le nom ne commence
pas par « _ », dans un module public (aucun dossier ni fichier en « _ », sauf ``__init__.py``).
Les surcharges ``@overload`` et les accesseurs ``@x.setter`` sont ignorés : la docstring est portée
par la définition principale. Le test ``tests/test_docstrings.py`` exige que chacun en ait une.

Usage (depuis la racine du dépôt) :
    python scripts/mesurer_docstrings.py            # bilan par sous-paquet
    python scripts/mesurer_docstrings.py --liste    # et la liste des éléments sans docstring
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAQUET = RACINE / "src" / "linalg_pedagopy"


def _ignore(noeud: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for d in noeud.decorator_list:
        if isinstance(d, ast.Name) and d.id == "overload":
            return True
        if isinstance(d, ast.Attribute) and d.attr in ("setter", "deleter", "overload"):
            return True
    return False


def elements_publics(paquet: Path = PAQUET) -> list[tuple[str, bool]]:
    """(nom qualifié « chemin:Classe.methode », a une docstring) pour chaque élément public."""
    elements: list[tuple[str, bool]] = []
    for fichier in sorted(paquet.rglob("*.py")):
        rel = fichier.relative_to(paquet)
        if any(partie.startswith("_") and partie != "__init__.py" for partie in rel.parts):
            continue
        nom_fichier = rel.as_posix()
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
        elements.append((nom_fichier, ast.get_docstring(arbre) is not None))

        def visiter(corps: list[ast.stmt], prefixe: str) -> None:
            for n in corps:
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if n.name.startswith("_"):
                    continue
                if not isinstance(n, ast.ClassDef) and _ignore(n):
                    continue
                elements.append((f"{nom_fichier}:{prefixe}{n.name}", ast.get_docstring(n) is not None))
                if isinstance(n, ast.ClassDef):
                    visiter(n.body, f"{prefixe}{n.name}.")

        visiter(arbre.body, "")
    return elements


def sans_docstring(paquet: Path = PAQUET) -> list[str]:
    """Noms qualifiés des éléments publics sans docstring."""
    return [nom for nom, documente in elements_publics(paquet) if not documente]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--liste", action="store_true", help="liste les éléments sans docstring")
    args = parser.parse_args()

    elements = elements_publics()
    totaux: Counter[str] = Counter()
    manques: Counter[str] = Counter()
    for nom, documente in elements:
        chemin = nom.split(":")[0]
        sous_paquet = chemin.split("/")[0] if "/" in chemin else "(racine)"
        totaux[sous_paquet] += 1
        manques[sous_paquet] += not documente
    for sous_paquet in sorted(totaux):
        n, m = totaux[sous_paquet], manques[sous_paquet]
        print(f"{sous_paquet:12s} {n:4d} éléments, {m:4d} sans docstring ({100 * m / n:5.1f} %)")
    n, m = sum(totaux.values()), sum(manques.values())
    print(f"{'total':12s} {n:4d} éléments, {m:4d} sans docstring ({100 * m / n:5.1f} %)")
    if args.liste:
        for nom in sans_docstring():
            print(" ", nom)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
