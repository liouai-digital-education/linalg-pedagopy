"""Exécute les carnets maintenus du dépôt et échoue à la première erreur.

Usage (depuis la racine du dépôt) :
    python tests/run_notebooks.py               # tous les carnets maintenus
    python tests/run_notebooks.py exercices/vecteurs_matrices.ipynb
    python tests/run_notebooks.py --moteur simple  # sans Jupyter (exécution directe des cellules)

Moteurs :
- ``jupyter`` : nbclient + ipykernel, exécution réelle comme dans JupyterLab (par défaut s'ils sont installés) ;
- ``simple``  : exécution des cellules de code dans un même espace de noms, sans noyau Jupyter
  (les commandes magiques ``%`` et ``!`` sont ignorées, ``display`` est simulé si IPython est absent).

Chaque carnet est exécuté dans un dossier de travail temporaire (les fichiers qu'il exporte, comme
``moindres_carres.html``, n'atterrissent pas dans le dépôt), avec ``src/`` et le dossier du carnet
sur le chemin d'import, et
un journal du tuteur temporaire (le journal personnel n'est jamais modifié). Les fichiers des carnets
ne sont pas réécrits.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

CARNETS_MAINTENUS = [
    "tutoriel_linalg_pedagopy.ipynb",
    "problemes_exploratoires_linalg_pedagopy.ipynb",
    "problemes_algebre_lineaire_pedagopy.ipynb",
    "projet_exploration_algebre_lineaire.ipynb",
    "exercices/vecteurs_matrices.ipynb",
    "exercices/corrige_vecteurs_matrices.ipynb",
]


def _preambule(journal: Path, chemin: Path) -> str:
    return (
        "import sys as _sys\n"
        f"_sys.path.insert(0, {str(RACINE / 'src')!r})\n"
        f"_sys.path.insert(1, {str(chemin.parent)!r})\n"  # modules voisins du carnet
        "import matplotlib as _mpl\n_mpl.use('Agg')\n"
        "from linalg_pedagopy import config as _cfg\n"
        f"_cfg.journal_path = {str(journal)!r}\n"
    )


def _cellules_code(chemin: Path) -> list[str]:
    nb = json.loads(chemin.read_text(encoding="utf-8"))
    out = []
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            src = c["source"] if isinstance(c["source"], str) else "".join(c["source"])
            out.append(src)
    return out


def _installer_ipython_simule() -> object:
    """Installe un module IPython.display minimal (Markdown, Latex, HTML, Math, display)."""
    import types

    def display(*objs: object, **_: object) -> None:
        for o in objs:
            f = getattr(o, "_repr_markdown_", None) or getattr(o, "_repr_latex_", None)
            print(f() if f else repr(o))

    class _Rendu:
        def __init__(self, data: object = None, *_a: object, **_k: object) -> None:
            self.data = data

        def _repr_markdown_(self) -> str:
            return str(self.data)

    mod_ipy = types.ModuleType("IPython")
    mod_disp = types.ModuleType("IPython.display")
    for nom in ("Markdown", "Latex", "HTML", "Math"):
        setattr(mod_disp, nom, type(nom, (_Rendu,), {}))
    mod_disp.display = display  # type: ignore[attr-defined]
    mod_disp.clear_output = lambda *a, **k: None  # type: ignore[attr-defined]
    mod_ipy.display = mod_disp  # type: ignore[attr-defined]
    sys.modules.setdefault("IPython", mod_ipy)
    sys.modules.setdefault("IPython.display", mod_disp)
    return display


def executer_simple(chemin: Path, journal: Path, dossier: Path) -> tuple[bool, str]:
    """Exécute les cellules de code dans un espace de noms commun (sans Jupyter)."""
    try:
        from IPython.display import display  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - dépend de l'environnement
        display = _installer_ipython_simule()

    ns: dict[str, object] = {"__name__": "__main__", "display": display}
    ancien = os.getcwd()
    os.chdir(dossier)
    try:
        exec(_preambule(journal, chemin), ns)
        for i, src in enumerate(_cellules_code(chemin)):
            lignes = [l for l in src.split("\n") if not l.lstrip().startswith(("%", "!"))]
            code = "\n".join(lignes)
            try:
                arbre = ast.parse(code)
                dernier = None
                if arbre.body and isinstance(arbre.body[-1], ast.Expr):
                    dernier = ast.Expression(arbre.body.pop().value)
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(arbre, f"{chemin.name}[{i}]", "exec"), ns)
                    if dernier is not None:
                        valeur = eval(compile(dernier, f"{chemin.name}[{i}]", "eval"), ns)
                        if valeur is not None:
                            display(valeur)
            except Exception:  # noqa: BLE001
                return False, f"cellule de code n° {i + 1} :\n{src[:400]}\n\n{traceback.format_exc(limit=4)}"
        return True, ""
    finally:
        os.chdir(ancien)


def executer_jupyter(chemin: Path, journal: Path, dossier: Path, delai: int) -> tuple[bool, str]:
    """Exécute le carnet dans un vrai noyau Jupyter (nbclient)."""
    import nbformat  # type: ignore[import-not-found]
    from nbclient import NotebookClient  # type: ignore[import-not-found]
    from nbclient.exceptions import CellExecutionError  # type: ignore[import-not-found]

    nb = nbformat.read(str(chemin), as_version=4)
    nb.cells.insert(0, nbformat.v4.new_code_cell(_preambule(journal, chemin)))
    client = NotebookClient(nb, timeout=delai, kernel_name="python3", resources={"metadata": {"path": str(dossier)}})
    try:
        client.execute()
        return True, ""
    except CellExecutionError as err:
        return False, str(err)[-3000:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("carnets", nargs="*", help="carnets à exécuter (par défaut : les carnets maintenus)")
    parser.add_argument("--moteur", choices=["auto", "jupyter", "simple"], default="auto")
    parser.add_argument("--delai", type=int, default=600, help="délai maximal par cellule (moteur jupyter), en secondes")
    args = parser.parse_args(argv)

    moteur = args.moteur
    if moteur == "auto":
        try:
            import ipykernel  # noqa: F401  # type: ignore[import-not-found]
            import nbclient  # noqa: F401  # type: ignore[import-not-found]
            moteur = "jupyter"
        except ImportError:
            moteur = "simple"

    carnets = [RACINE / c for c in (args.carnets or CARNETS_MAINTENUS)]
    print(f"Moteur : {moteur} — {len(carnets)} carnet(s)")
    echecs = 0
    with tempfile.TemporaryDirectory() as tmp:
        journal = Path(tmp) / "journal_tests.json"
        for chemin in carnets:
            if not chemin.exists():
                print(f"  ✗ {chemin.relative_to(RACINE)} : introuvable")
                echecs += 1
                continue
            t0 = time.time()
            dossier = Path(tempfile.mkdtemp(dir=tmp))
            ok, detail = (executer_jupyter(chemin, journal, dossier, args.delai) if moteur == "jupyter"
                          else executer_simple(chemin, journal, dossier))
            duree = time.time() - t0
            print(f"  {'✓' if ok else '✗'} {chemin.relative_to(RACINE)} ({duree:.0f} s)")
            if not ok:
                echecs += 1
                print("    " + detail.replace("\n", "\n    "))
    print("Tous les carnets s'exécutent sans erreur." if not echecs else f"{echecs} carnet(s) en échec.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
