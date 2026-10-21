"""Mesure des cas des campagnes du bac à sable : temps, nombre de branches, taille des expressions.

Étape 3.1 du plan v6 : base de comparaison pour le moteur d'élimination (phase 4) et les
méthodes dédiées aux familles structurées (phase 9). Les cas sont ceux de ``tests/campagnes.py``.

Usage (depuis n'importe quel dossier) :

    python scripts/mesurer_performances.py                 # tous les cas, 1 exécution chacun
    python scripts/mesurer_performances.py --repetitions 3 # médiane de 3 exécutions
    python scripts/mesurer_performances.py --rapide        # sans les cas marqués « lent »
    python scripts/mesurer_performances.py --json mesures.json
    python scripts/mesurer_performances.py t4_fleche_6x6 t3_5_pivot_quadratique

La taille est le nombre d'opérations SymPy (``count_ops``) dans les matrices réduites de toutes
les branches : elle suit la croissance des expressions indépendamment de la machine.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE))

import sympy as sp  # noqa: E402

from linalg_pedagopy import CaseSplit, PedagopyError, __version__  # noqa: E402
from tests.campagnes import CAS_CAMPAGNES, taille  # noqa: E402


def mesurer(nom: str, repetitions: int) -> dict[str, object]:
    cas = CAS_CAMPAGNES[nom]
    durees: list[float] = []
    branches: int | None = None
    erreur: str | None = None
    ops: int | None = None
    for _ in range(repetitions):
        t0 = time.perf_counter()
        try:
            res = cas.calcul()
        except PedagopyError as err:
            durees.append(time.perf_counter() - t0)
            erreur = str(err).split(".")[0]
            continue
        durees.append(time.perf_counter() - t0)
        branches = len(res.branches) if isinstance(res, CaseSplit) else 1
        ops = taille(res)
    return {
        "cas": nom,
        "carnet": cas.carnet,
        "lent": cas.lent,
        "temps_s": round(statistics.median(durees), 2),
        "branches": branches,
        "taille": ops,
        "erreur": erreur,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cas", nargs="*", help="noms des cas (défaut : tous)")
    parser.add_argument("--repetitions", type=int, default=1, help="nombre d'exécutions par cas (médiane)")
    parser.add_argument("--rapide", action="store_true", help="sans les cas marqués « lent »")
    parser.add_argument("--json", type=Path, help="fichier où écrire les mesures")
    args = parser.parse_args()

    inconnus = [n for n in args.cas if n not in CAS_CAMPAGNES]
    if inconnus:
        print(f"Cas inconnus : {', '.join(inconnus)}. Cas disponibles : {', '.join(sorted(CAS_CAMPAGNES))}")
        return 2
    noms = args.cas or sorted(CAS_CAMPAGNES)
    if args.rapide:
        noms = [n for n in noms if not CAS_CAMPAGNES[n].lent]

    print(f"{'cas':40s} {'temps':>8s} {'branches':>9s} {'taille':>8s}  remarque")
    mesures = []
    for nom in noms:
        r = mesurer(nom, args.repetitions)
        mesures.append(r)
        branches = "—" if r["branches"] is None else str(r["branches"])
        ops = "—" if r["taille"] is None else str(r["taille"])
        remarque = r["erreur"] or ""
        print(f"{nom:40s} {r['temps_s']:>7.2f}s {branches:>9s} {ops:>8s}  {remarque}", flush=True)

    if args.json:
        contexte = {
            "linalg_pedagopy": __version__,
            "sympy": sp.__version__,
            "python": platform.python_version(),
            "machine": platform.platform(),
            "repetitions": args.repetitions,
        }
        args.json.write_text(json.dumps({"contexte": contexte, "mesures": mesures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nMesures écrites dans {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
