"""Lance toutes les vérifications du dépôt en une commande.

Usage (depuis la racine du dépôt, avec ``pip install -e ".[dev,plot,compare]"``) :

    python verifier_tout.py            # tout : tests (+ couverture), fiches, ruff, mypy, carnets
    python verifier_tout.py --rapide   # tests et fiches seulement
    python verifier_tout.py --sans-carnets

Étapes bloquantes : tests, validation des fiches, ruff, mypy sur le périmètre strict
(``files`` de ``[tool.mypy]`` dans pyproject.toml), carnets.
Étape informative : mypy sur tout le paquet (erreurs affichées, sans faire échouer la vérification).
Les outils absents sont signalés et l'étape est sautée.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent


def _present(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _lancer(titre: str, commande: list[str], *, bloquant: bool = True) -> bool:
    print(f"\n━━ {titre} ━━\n$ {' '.join(commande)}", flush=True)
    t0 = time.time()
    res = subprocess.run(commande, cwd=RACINE)
    ok = res.returncode == 0
    etat = "OK" if ok else ("ÉCHEC" if bloquant else "à améliorer (non bloquant)")
    print(f"→ {etat} ({time.time() - t0:.0f} s)", flush=True)
    return ok or not bloquant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rapide", action="store_true", help="tests et fiches seulement")
    parser.add_argument("--sans-carnets", action="store_true", help="ne pas exécuter les carnets")
    args = parser.parse_args()

    py = sys.executable
    resultats: dict[str, bool | None] = {}

    if _present("coverage") and not args.rapide:
        resultats["tests + couverture"] = _lancer("Tests et couverture", [py, "-m", "coverage", "run", "-m", "pytest"])
        subprocess.run([py, "-m", "coverage", "report", "--skip-covered", "--sort=cover"], cwd=RACINE)
    elif _present("pytest"):
        resultats["tests"] = _lancer("Tests", [py, "-m", "pytest"])
    else:
        print("pytest absent : pip install -e \".[dev]\"")
        resultats["tests"] = False

    code_fiches = (
        "import sys; sys.path.insert(0, 'src');"
        "from linalg_pedagopy import tutor;"
        "r = [(i, tutor.validate_sheet(i)) for i in tutor.list_exercises()];"
        "ko = [(i, x.errors) for i, x in r if not x.valid];"
        "print(f'{len(r) - len(ko)}/{len(r)} fiches valides');"
        "[print(' ', i, e) for i, e in ko];"
        "sys.exit(1 if ko else 0)"
    )
    resultats["fiches"] = _lancer("Validation des fiches du tuteur", [py, "-c", code_fiches])

    if not args.rapide:
        ruff = shutil.which("ruff")
        if ruff:
            resultats["ruff"] = _lancer("Ruff", [ruff, "check", "src", "tests", "scripts"])
        else:
            print("\nruff absent : étape sautée (pip install ruff)")
            resultats["ruff"] = None
        mypy = shutil.which("mypy")
        if mypy:
            version = f"{sys.version_info.major}.{sys.version_info.minor}"
            resultats["mypy"] = _lancer("Mypy (périmètre strict)", [mypy, "--python-version", version])
            _lancer("Mypy (paquet complet, informatif)", [mypy, "--python-version", version, "src/linalg_pedagopy"], bloquant=False)
        else:
            print("\nmypy absent : étape sautée (pip install mypy)")
            resultats["mypy"] = None
        if not args.sans_carnets:
            resultats["carnets"] = _lancer("Carnets", [py, "tests/run_notebooks.py"])

    print("\n━━ Bilan ━━")
    for nom, ok in resultats.items():
        print(f"  {'✓' if ok else ('–' if ok is None else '✗')} {nom}")
    echec = any(ok is False for ok in resultats.values())
    print("Tout est vert." if not echec else "Au moins une vérification a échoué.")
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
