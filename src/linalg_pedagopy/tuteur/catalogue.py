"""Catalogue des exercices du tuteur : fiches, thèmes, glossaire, mode d'usage."""

from __future__ import annotations

import difflib
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml

from linalg_pedagopy.config import TutorMode, config
from linalg_pedagopy.core.exceptions import UnknownExerciseError


_PACKAGE_DIR = Path(__file__).resolve().parent.parent

_FICHES_DIR = _PACKAGE_DIR / "tuteur" / "fiches"

_GLOSSAIRE_PATH = _PACKAGE_DIR / "tuteur" / "glossaire.yaml"


@lru_cache(maxsize=1)
def _load_glossaire() -> dict[str, dict[str, str]]:
    if not _GLOSSAIRE_PATH.exists():
        return {}
    with _GLOSSAIRE_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if isinstance(data, dict) and isinstance(data.get("terms"), dict):
        return data["terms"]
    return {}


def glossary(term: str | None = None) -> str:
    """Traduit et définit un terme d'algèbre linéaire (anglais ou français).

    Sans argument, renvoie la liste des termes disponibles.
    """
    terms = _load_glossaire()
    if term is None:
        lignes = [f"- **{k}** → {v['fr']}" for k, v in sorted(terms.items())]
        return MarkdownText("**Glossaire anglais → français**\n\n" + "\n".join(lignes))
    key = term.strip().lower()
    if key in terms:
        entry = terms[key]
        return MarkdownText(f"**{key}** → {entry['fr']} : {entry['definition']}")
    for k, entry in terms.items():
        if key in k or key in entry.get("fr", "").lower():
            return MarkdownText(f"**{k}** → {entry['fr']} : {entry['definition']}")
    proches = difflib.get_close_matches(key, list(terms), n=3)
    suggestion = f" Termes proches : {proches}." if proches else ""
    raise KeyError(
        f"Terme {term!r} absent du glossaire.{suggestion} Appelez glossary() pour la liste complète."
    )


def mode(new_mode: TutorMode | None = None) -> TutorMode:
    """Gets or sets the tutor mode ('student'/'etudiant' or 'teacher'/'enseignant')."""
    if new_mode is not None:
        config.tutor_mode = new_mode
    return config.tutor_mode


THEMES: tuple[str, ...] = (
    "Vecteurs et produit scalaire",
    "Normes, distances et angles",
    "Orthogonalisation",
    "Matrices et applications linéaires",
    "Convolution",
    "Produit matriciel",
    "Inverses et systèmes linéaires",
    "Moindres carrés et optimisation",
    "Déterminants",
)


TYPE_LABELS: dict[str, str] = {
    "calcul": "calcul",
    "modelisation": "modélisation",
    "dimensions": "dimensions",
    "justification": "justification",
    "contre_exemple": "contre-exemple",
    "vrai_faux": "vrai ou faux",
}


def _niveau_etoiles(niveau: Any) -> str:
    try:
        n = max(1, min(3, int(niveau)))
    except Exception:
        n = 1
    return "★" * n + "☆" * (3 - n)


@lru_cache(maxsize=1)
def _all_fiches() -> tuple[dict[str, Any], ...]:
    """Charge toutes les fiches YAML, triées par numéro."""
    if not _FICHES_DIR.exists():
        return ()
    fiches = []
    for p in _FICHES_DIR.glob("*.yaml"):
        with p.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict):
            data.setdefault("id", p.stem)
            fiches.append(data)
    return tuple(sorted(fiches, key=lambda d: (int(d.get("numero", 999)), str(d["id"]))))


def reload_catalog() -> None:
    """Relit les fiches sur le disque (utile après avoir modifié ou ajouté une fiche)."""
    _all_fiches.cache_clear()


def themes() -> list[str]:
    """Renvoie la liste ordonnée des thèmes du catalogue."""
    present = {str(f.get("theme", "")) for f in _all_fiches()}
    ordered = [th for th in THEMES if th in present]
    return ordered + sorted(present - set(ordered))


def list_exercises(theme: str | None = None) -> list[str]:
    """Renvoie les identifiants des exercices, dans l'ordre du catalogue (éventuellement filtrés par thème)."""
    return [str(f["id"]) for f in _all_fiches() if theme is None or _theme_matches(f, theme)]


def _theme_matches(fiche: Mapping[str, Any], theme: str) -> bool:
    return theme.strip().lower() in str(fiche.get("theme", "")).lower()


class ExerciseCatalog(tuple):
    """Table des exercices (tuple de dictionnaires) avec rendu Markdown dans JupyterLab."""

    def _repr_markdown_(self) -> str:
        lignes = ["| N° | Exercice | Identifiant | Thème | Type | Niveau |", "|---:|:---|:---|:---|:---|:---|"]
        for row in self:
            lignes.append(
                f"| {row['numero']} | {row['titre']} | `{row['id']}` | {row['theme']} | "
                f"{row['type']} | {_niveau_etoiles(row['niveau'])} |"
            )
        return "\n".join(lignes)

    def __str__(self) -> str:
        lignes = []
        theme_courant = None
        for row in self:
            if row["theme"] != theme_courant:
                theme_courant = row["theme"]
                lignes.append(f"\n{theme_courant}")
            lignes.append(
                f"  {row['numero']:>2}. {row['titre']}  [{row['id']}]  "
                f"({row['type']}, {_niveau_etoiles(row['niveau'])})"
            )
        return "\n".join(lignes).lstrip("\n")


def catalog(theme: str | None = None) -> ExerciseCatalog:
    """Renvoie le catalogue des exercices : numéro, titre, identifiant, thème, type et niveau."""
    rows = []
    for f in _all_fiches():
        if theme is not None and not _theme_matches(f, theme):
            continue
        rows.append(
            {
                "numero": int(f.get("numero", 0)),
                "id": str(f["id"]),
                "titre": str(f.get("titre", f["id"])),
                "theme": str(f.get("theme", "")),
                "type": TYPE_LABELS.get(str(f.get("type", "")), str(f.get("type", ""))),
                "niveau": int(f.get("niveau", 1)),
                "notions": list(f.get("notions", [])),
            }
        )
    return ExerciseCatalog(rows)


def _resolve_exercise(ref: Any) -> dict[str, Any]:
    """Retrouve une fiche par identifiant, numéro (int ou chaîne de chiffres) ou titre."""
    fiches = _all_fiches()
    if isinstance(ref, bool):
        ref = str(ref)
    if isinstance(ref, int) or (isinstance(ref, str) and ref.strip().isdigit()):
        num = int(ref)
        for f in fiches:
            if int(f.get("numero", -1)) == num:
                return dict(f)
        raise UnknownExerciseError(
            f"Aucun exercice n° {num}. Les numéros vont de 1 à {len(fiches)} : voir tutor.catalog()."
        )
    key = str(ref).strip()
    low = key.lower()
    for f in fiches:
        if str(f["id"]).lower() == low or str(f.get("titre", "")).lower() == low:
            return dict(f)
    ids = [str(f["id"]) for f in fiches]
    titres = {str(f.get("titre", "")).lower(): str(f["id"]) for f in fiches}
    proches = difflib.get_close_matches(low, ids, n=3, cutoff=0.5)
    proches += [titres[t] for t in difflib.get_close_matches(low, list(titres), n=3, cutoff=0.5)]
    proches = list(dict.fromkeys(proches))
    suggestion = f" Vouliez-vous dire : {', '.join(proches)} ?" if proches else ""
    raise UnknownExerciseError(
        f"Exercice {key!r} introuvable.{suggestion} Consultez la liste avec tutor.catalog()."
    )


def _load_fiche_dict(ex_id: Any) -> dict[str, Any]:
    return _resolve_exercise(ex_id)


class MarkdownText(str):
    """Subclass of str with rich Markdown and LaTeX math rendering in JupyterLab."""

    def _repr_markdown_(self) -> str:
        return str(self)

# French backward-compatible function aliases
glossaire = glossary

lister_exercices = list_exercises

catalogue = catalog

recharger_catalogue = reload_catalog
