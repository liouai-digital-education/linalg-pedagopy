"""Catalogue des exercices, séance ExerciseSession, glossaire et validation des fiches du tuteur."""

from __future__ import annotations

import difflib
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Mapping
from weakref import WeakKeyDictionary

import yaml

from linalg_pedagopy.config import TutorMode, config
from linalg_pedagopy.core.exceptions import PedagopyError, UnknownExerciseError
from linalg_pedagopy.exercises.generators import TwinExercise
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tutor.hints import HintLadder, evaluate_twin_spec
from linalg_pedagopy.tutor.journal import ExerciseJournal
from linalg_pedagopy.tutor.evaluation_sure import evaluer
from linalg_pedagopy.tutor.lab import CounterexampleLab
from linalg_pedagopy.tutor.lock import LockedNamespace, _get_namespace_raw_dict
from linalg_pedagopy.tutor.panel import build_panel
from linalg_pedagopy.tutor.registry import verifier_type
from linalg_pedagopy.tutor.verifiers import VerificationResult
import linalg_pedagopy.tutor.verifier_types  # noqa: F401  (enregistre les types de vérificateurs)

_PACKAGE_DIR = Path(__file__).resolve().parent.parent
_FICHES_DIR = _PACKAGE_DIR / "tuteur" / "fiches"
_GLOSSAIRE_PATH = _PACKAGE_DIR / "tuteur" / "glossaire.yaml"

# Private vault for ExerciseSession secrets so students cannot read _fiche, _verification_spec,
# or mutate _unlocked via attribute access or __dict__.
_SESSION_VAULT: WeakKeyDictionary[Any, dict[str, Any]] = WeakKeyDictionary()


def _is_teacher_mode() -> bool:
    return config.tutor_mode in ("teacher", "enseignant")


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


class TeacherSheet(dict):
    """Exercise sheet dictionary with rich Markdown and LaTeX math rendering in JupyterLab."""

    def _repr_markdown_(self) -> str:
        lines = [
            f"## Fiche enseignant — {self.get('titre', self.get('id', ''))}",
            f"**Identifiant** : `{self.get('id', '')}` | **N°** : {self.get('numero', '')} | "
            f"**Thème** : {self.get('theme', '')} | **Type** : {self.get('type', '')} | "
            f"**Niveau** : {_niveau_etoiles(self.get('niveau', 1))}",
            "",
            "### Énoncé",
            str(self.get("enonce", self.get("reformulation", ""))),
            "",
            "### Spécification de vérification",
            "```yaml",
            yaml.dump(self.get("verification", {}), allow_unicode=True).strip(),
            "```",
            "",
            "### Paliers d'indices",
        ]
        for i, ind in enumerate(self.get("indices", []), 1):
            lines.append(f"- **Palier {i}** : {ind}")
        if "jumeau" in self:
            lines.extend(["", "### Exercice jumeau", f"`{self.get('jumeau')}`"])
        return "\n".join(lines)


class ExerciseSession:
    """Séance de tutorat interactive sur un exercice du catalogue."""

    __slots__ = ("__weakref__",)

    def __init__(
        self,
        fiche: Mapping[str, Any],
        *,
        journal_path: Path | None = None,
        persist_journal: bool = True,
    ) -> None:
        fiche_copy = dict(fiche)
        ex_id = str(fiche_copy["id"])
        journal = ExerciseJournal(ex_id, path=journal_path, persist=persist_journal)
        initial_unlocked = bool(journal.solved)
        initial_preds: dict[str, str] = {}
        if journal.predictions:
            initial_preds = {str(k): str(v) for k, v in journal.predictions[-1].items()}

        state: dict[str, Any] = {
            "fiche": fiche_copy,
            "id": ex_id,
            "numero": int(fiche_copy.get("numero", 0) or 0),
            "titre": str(fiche_copy.get("titre", ex_id)),
            "theme": str(fiche_copy.get("theme", "")),
            "niveau": int(fiche_copy.get("niveau", 1) or 1),
            "type": str(fiche_copy.get("type", "calcul")),
            "enonce": str(fiche_copy.get("enonce", fiche_copy.get("reformulation", ""))).strip(),
            "notions": list(fiche_copy.get("notions", [])),
            "resumed": bool(journal.attempts or journal.hints_unlocked or journal.solved),
            "verification_spec": dict(fiche_copy.get("verification", {})),
            "unlocked": initial_unlocked,
            "predictions": initial_preds,
            "journal": journal,
        }
        _SESSION_VAULT[self] = state

        data_ns = LockedNamespace(
            dict(fiche_copy.get("donnees", {})),
            is_unlocked=lambda: bool(_SESSION_VAULT[self]["unlocked"]) or _is_teacher_mode(),
        )
        ladder = HintLadder(
            hints=tuple(str(h) for h in fiche_copy.get("indices", [])),
            twin_spec=fiche_copy.get("jumeau"),
            on_unlock=journal.record_hint,
            initial_unlocked_level=max(journal.hints_unlocked, default=0),
        )
        state["data"] = data_ns
        state["ladder"] = ladder

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("ExerciseSession est immuable et protégée par le tuteur.")

    def _state(self) -> dict[str, Any]:
        return _SESSION_VAULT[self]

    @property
    def id(self) -> str:
        return self._state()["id"]  # type: ignore[no-any-return]

    @property
    def number(self) -> int:
        """Numéro de l'exercice dans le catalogue."""
        return self._state()["numero"]  # type: ignore[no-any-return]

    numero = number

    @property
    def title(self) -> str:
        """Titre de l'exercice."""
        return self._state()["titre"]  # type: ignore[no-any-return]

    titre = title

    @property
    def theme(self) -> str:
        """Thème de l'exercice."""
        return self._state()["theme"]  # type: ignore[no-any-return]

    @property
    def level(self) -> int:
        """Niveau de difficulté (1 à 3)."""
        return self._state()["niveau"]  # type: ignore[no-any-return]

    niveau = level

    @property
    def type(self) -> str:
        return self._state()["type"]  # type: ignore[no-any-return]

    @property
    def text(self) -> str:
        """Texte brut de l'énoncé (Markdown + LaTeX)."""
        return self._state()["enonce"]  # type: ignore[no-any-return]

    texte = text

    @property
    def notions(self) -> list[str]:
        return list(self._state()["notions"])


    @property
    def journal(self) -> ExerciseJournal:
        return self._state()["journal"]  # type: ignore[no-any-return]

    @property
    def data(self) -> LockedNamespace:
        return self._state()["data"]  # type: ignore[no-any-return]

    @property
    def donnees(self) -> LockedNamespace:
        return self._state()["data"]  # type: ignore[no-any-return]

    @property
    def predictions(self) -> dict[str, str]:
        return dict(self._state()["predictions"])

    def statement(self) -> MarkdownText:
        """Affiche l'énoncé (titre, thème, niveau, texte et notions) avec formules LaTeX."""
        st = self._state()
        type_label = TYPE_LABELS.get(st["type"], st["type"])
        meta = f"*{st['theme']} · {type_label} · niveau {_niveau_etoiles(st['niveau'])}*"
        notions_str = f"\n\n**Notions** : {', '.join(st['notions'])}" if st["notions"] else ""
        return MarkdownText(
            f"### Exercice {st['numero']} — {st['titre']}\n\n{meta}\n\n{st['enonce']}{notions_str}"
        )

    def hint(self, level: int | None = None, *, niveau: int | None = None) -> MarkdownText:
        """Débloque et affiche le palier d'indice suivant (1 à 4), ou réaffiche un palier déjà débloqué."""
        st = self._state()
        lvl = level if level is not None else niveau
        ladder = st["ladder"]
        if lvl is None and ladder.unlocked_level >= 4:
            return MarkdownText(
                "**Tous les paliers d'aide sont déjà débloqués** (1 à 4"
                + (", lors d'une séance précédente" if st.get("resumed") else "")
                + ").\n\n"
                "- Relisez un palier avec `ex.hint(1)` … `ex.hint(4)` ;\n"
                "- étudiez l'exercice résolu analogue avec `ex.twin()` ;\n"
                "- pour repartir de zéro sur cet exercice, utilisez `ex.reset()`.\n\n"
                "Il n'y a pas de palier « solution » : transposez la méthode de l'exercice jumeau."
            )
        res = ladder.request_hint(
            level=lvl,
            current_attempts=st["journal"].attempts,
        )
        return MarkdownText(res)

    def reset(self) -> MarkdownText:
        """Remet à zéro la progression sur cet exercice (journal, indices, prédictions, verrou)."""
        st = self._state()
        st["journal"].reset()
        st["ladder"].unlocked_level = 0
        st["predictions"] = {}
        st["unlocked"] = False
        st["resumed"] = False
        return MarkdownText(f"Progression sur « {st['titre']} » remise à zéro.")

    def twin(self) -> TwinExercise | str:
        """Solves and displays the analogous twin exercise (palier 4)."""
        st = self._state()
        st["journal"].record_twin()
        st["ladder"].unlocked_level = max(st["ladder"].unlocked_level, 4)
        return evaluate_twin_spec(st["fiche"].get("jumeau"))

    def predict(self, *args: str, **kwargs: str) -> MarkdownText:
        """Records the student's prediction before opening the counterexample lab."""
        st = self._state()
        preds: dict[str, str] = st["predictions"]
        if args and not kwargs:
            preds["enonce"] = str(args[0])
        for k, v in kwargs.items():
            preds[str(k)] = str(v)
        if not preds:
            raise ValueError("Fournissez au moins une prédiction (ex. ex.predict('toujours vrai')).")
        st["journal"].record_prediction(preds)
        return MarkdownText(
            f"**Prédiction enregistrée** : `{preds}`.\n\n"
            "> Le laboratoire de contre-exemples est maintenant ouvert via `ex.lab()` / `ex.labo()`."
        )

    def lab(self) -> CounterexampleLab:
        """Opens the counterexample laboratory after recording a prediction."""
        st = self._state()
        return CounterexampleLab(
            st["verification_spec"],
            st["predictions"],
            on_test=st["journal"].record_lab_test,
        )

    def verify(self, response: Any) -> VerificationResult:
        """Verifies the student's response and produces a diagnostic without revealing the answer."""
        st = self._state()
        spec = st["verification_spec"]
        v_type = str(spec.get("type", "valeur"))
        raw_data = _get_namespace_raw_dict(st["data"])

        vtype = verifier_type(v_type)
        try:
            if vtype is None:
                raise ValueError(f"Type de vérificateur inconnu : {v_type!r}")
            res = vtype.verify(self, response, spec, raw_data)
        except PedagopyError as exc:
            res = VerificationResult(False, str(exc))
        except Exception:
            res = VerificationResult(
                False,
                "Votre réponse n'a pas la forme attendue : "
                + (vtype.expected_form if vtype is not None else "relisez l'énoncé."),
            )

        st["journal"].record_attempt(correct=res.valid, diagnostic=res.diagnostic)
        if res.valid:
            st["unlocked"] = True
        return res

    def summary(self) -> MarkdownText:
        """Renvoie le bilan de la séance (tentatives, indices, temps passé)."""
        st = self._state()
        return MarkdownText(st["journal"].format_summary(title=st["titre"]))

    def panel(self) -> Any:
        """Returns the interactive ipywidgets panel for JupyterLab."""
        return build_panel(self)

    def teacher_sheet(self) -> TeacherSheet:
        """Returns the full exercise sheet in teacher mode only."""
        if not _is_teacher_mode():
            raise PermissionError(
                "L'inspection de la fiche complète est réservée au mode enseignant (tutor.mode('teacher') / tuteur.mode('enseignant'))."
            )
        return TeacherSheet(self._state()["fiche"])

    # French backward-compatible method aliases
    enonce = statement
    indice = hint
    jumeau = twin
    predire = predict
    labo = lab
    verifier = verify
    bilan = summary
    panneau = panel
    fiche_enseignant = teacher_sheet
    recommencer = reset


ExerciceSession = ExerciseSession


def exercise(ex_id: str | int, *, journal_path: Path | None = None) -> ExerciseSession:
    """Ouvre une séance sur un exercice désigné par son identifiant, son numéro ou son titre."""
    fiche = _load_fiche_dict(ex_id)
    return ExerciseSession(fiche, journal_path=journal_path)


class ValidationReport:
    """Automatic validation report for an exercise sheet via validate_sheet."""

    __slots__ = (
        "id",
        "valid",
        "target_ok",
        "twin_ok",
        "hints_leak_free",
        "source_ok",
        "cross_check_ok",
        "errors",
    )

    def __init__(
        self,
        id: str,
        valid: bool,
        target_ok: bool,
        twin_ok: bool,
        hints_leak_free: bool,
        errors: tuple[str, ...] = (),
        *,
        source_ok: bool = True,
        cross_check_ok: bool = True,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "valid", bool(valid))
        object.__setattr__(self, "target_ok", bool(target_ok))
        object.__setattr__(self, "twin_ok", bool(twin_ok))
        object.__setattr__(self, "hints_leak_free", bool(hints_leak_free))
        object.__setattr__(self, "source_ok", bool(source_ok))
        object.__setattr__(self, "cross_check_ok", bool(cross_check_ok))
        object.__setattr__(self, "errors", tuple(errors))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("ValidationReport est immuable.")

    @property
    def valide(self) -> bool:
        return self.valid

    @property
    def cible_ok(self) -> bool:
        return self.target_ok

    @property
    def jumeau_ok(self) -> bool:
        return self.twin_ok

    @property
    def indices_sans_fuite(self) -> bool:
        return self.hints_leak_free

    @property
    def erreurs(self) -> tuple[str, ...]:
        return self.errors

    def __bool__(self) -> bool:
        return self.valid


def _cross_check_verifier(
    session: ExerciseSession,
    verif: Mapping[str, Any],
    raw_data: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    """Cross-checks the sheet's verifier by constructing a mathematical solution and testing acceptance/rejection."""
    vtype = verifier_type(str(verif.get("type", "")))
    if vtype is None:
        return True, []
    with suspend_tracing():
        try:
            errs = vtype.cross_check(session, verif, raw_data)
        except Exception as exc:
            errs = [f"Exception lors du cross-check : {exc}"]
    return (len(errs) == 0), errs


def validate_sheet(ex_id: str | int) -> ValidationReport:
    """Vérifie qu'une fiche est complète, sans fuite dans ses indices et cohérente avec le solveur."""
    fiche = _load_fiche_dict(ex_id)
    erreurs: list[str] = []

    for req_key in ("id", "type", "enonce", "verification", "indices"):
        if req_key not in fiche or not fiche[req_key]:
            erreurs.append(f"Champ obligatoire manquant ou vide : {req_key!r}")

    source_ok = True
    for meta_key in ("titre", "theme", "niveau", "numero"):
        if meta_key not in fiche or not str(fiche.get(meta_key, "")).strip():
            source_ok = False
            erreurs.append(f"Métadonnée de catalogue manquante ou vide : {meta_key!r}")
    try:
        if not 1 <= int(fiche.get("niveau", 0)) <= 3:
            source_ok = False
            erreurs.append("Le niveau doit être 1, 2 ou 3.")
    except (TypeError, ValueError):
        source_ok = False
        erreurs.append("Le niveau doit être un entier (1, 2 ou 3).")
    numeros = [int(f.get("numero", -1)) for f in _all_fiches()]
    if numeros.count(int(fiche.get("numero", -1))) > 1:
        source_ok = False
        erreurs.append(f"Numéro {fiche.get('numero')} utilisé par plusieurs fiches.")

    verif = dict(fiche.get("verification", {}))
    v_type = str(verif.get("type", ""))
    vtype = verifier_type(v_type)
    if vtype is None:
        erreurs.append(f"Type de vérificateur invalide : {v_type!r}")

    # 1. Target / verifier specification check
    cible_ok = True
    manque = vtype.missing_fields(v_type, verif) if vtype is not None else None
    if manque:
        cible_ok = False
        erreurs.append(manque)

    # 2. Twin generator check
    jumeau_ok = True
    jumeau_spec = fiche.get("jumeau")
    if jumeau_spec:
        twin_res = evaluate_twin_spec(str(jumeau_spec))
        if not isinstance(twin_res, TwinExercise) and "Erreur" in str(twin_res):
            jumeau_ok = False
            erreurs.append(f"Échec du générateur jumeau : {twin_res}")
    elif vtype is None or vtype.requires_twin:
        jumeau_ok = False
        erreurs.append("Champ 'jumeau' manquant.")

    # 3. Hint leak check (using persist_journal=False so validate_sheet never pollutes disk journal)
    indices_sans_fuite = True
    hints = [str(h) for h in fiche.get("indices", [])]
    if len(hints) < 3:
        erreurs.append("Une fiche doit comporter au moins 3 niveaux d'indices textuels.")
        indices_sans_fuite = False

    session = ExerciseSession(fiche, persist_journal=False)
    raw_cible_str = str(verif.get("cible", ""))
    for idx, h_text in enumerate(hints, start=1):
        if raw_cible_str and len(raw_cible_str) > 4 and raw_cible_str in h_text:
            indices_sans_fuite = False
            erreurs.append(f"L'indice {idx} contient littéralement la cible {raw_cible_str!r}.")
        if vtype is None or vtype.checks_hint_leak:
            try:
                check_h = session.verify(h_text)
                if check_h.valid:
                    indices_sans_fuite = False
                    erreurs.append(f"L'indice {idx} est accepté comme réponse valide par le vérificateur !")
            except Exception:
                pass
            # Also check if any Vector([...]) or Matrix([...]) literal inside the hint is accepted
            for lit_match in re.findall(r"(?:Vector|Matrix)\s*\(\s*\[[^\)]+\]\s*\)", h_text):
                try:
                    lit_obj = evaluer(lit_match, {"Vector": Vector, "Matrix": Matrix})
                    if session.verify(lit_obj).valid:
                        indices_sans_fuite = False
                        erreurs.append(f"L'indice {idx} divulgue une réponse explicite ({lit_match}) !")
                except Exception:
                    pass

    # 4. Cross-check verifier against the mathematical solver
    raw_data = _get_namespace_raw_dict(session.data)
    cross_check_ok, cc_errs = _cross_check_verifier(
        ExerciseSession(fiche, persist_journal=False),
        verif,
        raw_data,
    )
    if not cross_check_ok:
        erreurs.extend(cc_errs)

    valide = (
        cible_ok
        and jumeau_ok
        and indices_sans_fuite
        and source_ok
        and cross_check_ok
        and not erreurs
    )
    return ValidationReport(
        id=str(fiche.get("id", ex_id)),
        valid=valide,
        target_ok=cible_ok,
        twin_ok=jumeau_ok,
        hints_leak_free=indices_sans_fuite,
        source_ok=source_ok,
        cross_check_ok=cross_check_ok,
        errors=tuple(erreurs),
    )


# French backward-compatible function aliases
glossaire = glossary
lister_exercices = list_exercises
catalogue = catalog
recharger_catalogue = reload_catalog
exercice = exercise
valider_fiche = validate_sheet
