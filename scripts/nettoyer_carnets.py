"""Retire les sorties et les compteurs d'exécution des carnets Jupyter, sans dépendance externe.

Les carnets du dépôt sont versionnés sans sorties : les diffs ne montrent que le contenu,
et le lecteur n'hérite pas d'une exécution partielle. La CI les exécute de toute façon.

Usage (depuis n'importe quel dossier) :

    python scripts/nettoyer_carnets.py              # nettoie les carnets suivis (carnets/, exercices/)
    python scripts/nettoyer_carnets.py a.ipynb ...  # nettoie les carnets indiqués
    python scripts/nettoyer_carnets.py --verifier   # échoue si un carnet suivi a encore des sorties
    python scripts/nettoyer_carnets.py --filtre     # filtre git : carnet sur stdin, carnet nettoyé sur stdout

Filtre git automatique (facultatif, à activer une fois par clone) :

    git config filter.carnets.clean "python scripts/nettoyer_carnets.py --filtre"
    git config filter.carnets.smudge cat

``.gitattributes`` associe ce filtre aux ``*.ipynb`` : les carnets sont alors nettoyés à chaque
commit, tout en gardant leurs sorties sur le disque. Sans cette configuration, git ignore le filtre.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent.parent
DOSSIERS = ("carnets", "exercices")
# Métadonnées de carnet propres à une exécution (état des widgets) : retirées
METADONNEES_EXECUTION = ("widgets",)


def carnets_suivis() -> list[Path]:
    """Les carnets maintenus du dépôt."""
    return sorted(p for d in DOSSIERS for p in (RACINE / d).glob("*.ipynb"))


def nettoyer(nb: dict[str, Any]) -> bool:
    """Retire sorties, compteurs et état des widgets ; renvoie True si le carnet a changé."""
    change = False
    for cle in METADONNEES_EXECUTION:
        if cle in nb.get("metadata", {}):
            del nb["metadata"][cle]
            change = True
    for cellule in nb.get("cells", []):
        if cellule.get("cell_type") != "code":
            continue
        if cellule.get("outputs"):
            cellule["outputs"] = []
            change = True
        if cellule.get("execution_count") is not None:
            cellule["execution_count"] = None
            change = True
    return change


def a_des_sorties(nb: dict[str, Any]) -> bool:
    return any(
        c.get("outputs") or c.get("execution_count") is not None
        for c in nb.get("cells", [])
        if c.get("cell_type") == "code"
    ) or any(cle in nb.get("metadata", {}) for cle in METADONNEES_EXECUTION)


def _indentation(brut: str) -> int:
    """Indentation du JSON d'origine (Jupyter écrit 1 espace), pour garder des diffs minimaux."""
    lignes = brut.splitlines()
    if len(lignes) > 1:
        return len(lignes[1]) - len(lignes[1].lstrip(" ")) or 1
    return 1


def serialiser(nb: dict[str, Any], brut: str) -> bytes:
    """JSON avec l'indentation et les fins de ligne (LF ou CRLF) du carnet d'origine."""
    texte = json.dumps(nb, ensure_ascii=False, indent=_indentation(brut)) + "\n"
    if "\r\n" in brut:
        texte = texte.replace("\n", "\r\n")
    return texte.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("carnets", nargs="*", type=Path, help="carnets à nettoyer (par défaut : carnets suivis)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verifier", action="store_true", help="échoue si un carnet a encore des sorties")
    mode.add_argument("--filtre", action="store_true", help="filtre git : lit stdin, écrit stdout")
    args = parser.parse_args()

    if args.filtre:
        brut = sys.stdin.buffer.read().decode("utf-8")
        nb = json.loads(brut)
        nettoyer(nb)
        sys.stdout.buffer.write(serialiser(nb, brut))
        return 0

    chemins = args.carnets or carnets_suivis()
    if args.verifier:
        sales = [p for p in chemins if a_des_sorties(json.loads(p.read_bytes().decode("utf-8")))]
        for p in sales:
            print(f"Sorties présentes : {p}  (python scripts/nettoyer_carnets.py)")
        return 1 if sales else 0

    for p in chemins:
        brut = p.read_bytes().decode("utf-8")
        nb = json.loads(brut)
        if nettoyer(nb):
            p.write_bytes(serialiser(nb, brut))
            print(f"Nettoyé : {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
