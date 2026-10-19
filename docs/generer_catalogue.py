"""Régénère docs/08_catalogue_exercices.md à partir des fiches du tuteur.

Usage (depuis la racine du dépôt) : python docs/generer_catalogue.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from linalg_pedagopy import tutor  # noqa: E402
from linalg_pedagopy.tutor.catalog import TYPE_LABELS, _all_fiches, _niveau_etoiles  # noqa: E402

VERIF_LABELS = {
    "produit_scalaire": "un vecteur $a$ (forme $a^T x$)",
    "matrice": "une matrice",
    "formule": "une formule (chaîne)",
    "valeur": "une valeur exacte (ou un dictionnaire de valeurs)",
    "propriete": "l'objet demandé (vérifié par sa propriété)",
    "contre_exemple": "un contre-exemple",
    "labo": "prédiction puis essais au laboratoire",
    "egalites": "une chaîne d'égalités (liste de chaînes)",
    "dimensions": "validité et tailles (dictionnaire ou mot)",
}


def main() -> None:
    lines = [
        "# 08. Catalogue des exercices",
        "",
        "Le tuteur propose **35 exercices** répartis en 8 thèmes, du plus simple (★☆☆) au plus exigeant (★★★).",
        "Chaque exercice s'ouvre par son identifiant, son numéro ou son titre :",
        "",
        "```python",
        "from linalg_pedagopy import tutor",
        "",
        'ex = tutor.exercise("moyenne-glissante")   # ou tutor.exercise(16)',
        "ex.statement()",
        "```",
        "",
        "Ce tableau est produit par `python docs/generer_catalogue.py` à partir des fiches ; "
        "dans un carnet, `tutor.catalog()` affiche la même liste.",
        "",
        "## Vue d'ensemble",
        "",
        "| N° | Exercice | Identifiant | Type | Niveau |",
        "|---:|:---|:---|:---|:---:|",
    ]
    fiches = list(_all_fiches())
    theme = None
    for f in fiches:
        if f["theme"] != theme:
            theme = f["theme"]
            lines.append(f"| | **{theme}** | | | |")
        lines.append(
            f"| {f['numero']} | [{f['titre']}](#{f['id']}) | `{f['id']}` | "
            f"{TYPE_LABELS.get(f['type'], f['type'])} | {_niveau_etoiles(f['niveau'])} |"
        )
    lines += ["", "## Énoncés", ""]
    theme = None
    for f in fiches:
        if f["theme"] != theme:
            theme = f["theme"]
            lines += [f"### {theme}", ""]
        verif = str(f.get("verification", {}).get("type", ""))
        lines += [
            f'<a id="{f["id"]}"></a>',
            "",
            f"#### {f['numero']}. {f['titre']}",
            "",
            f"*Identifiant* `{f['id']}` · *type* {TYPE_LABELS.get(f['type'], f['type'])} · "
            f"*niveau* {_niveau_etoiles(f['niveau'])} · *réponse attendue* : {VERIF_LABELS.get(verif, verif)}",
            "",
            str(f.get("enonce", "")).strip(),
            "",
        ]
        if f.get("notions"):
            lines += [f"**Notions** : {', '.join(f['notions'])}", ""]
    out = ROOT / "docs" / "08_catalogue_exercices.md"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"{out} : {len(fiches)} exercices, {len(tutor.themes())} thèmes")


if __name__ == "__main__":
    main()
