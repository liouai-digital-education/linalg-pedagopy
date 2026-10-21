"""Séance de tutorat (ExerciseSession) : énoncé, indices, jumeau, vérification, bilan, panneau."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from weakref import WeakKeyDictionary

import yaml

from linalg_pedagopy.config import config
from linalg_pedagopy.core.exceptions import PedagopyError
from linalg_pedagopy.exercises.generators import TwinExercise
from linalg_pedagopy.tuteur.indices import HintLadder, evaluate_twin_spec
from linalg_pedagopy.tuteur.journal import ExerciseJournal
from linalg_pedagopy.tuteur.labo import CounterexampleLab
from linalg_pedagopy.tuteur.verrou import LockedNamespace, _get_namespace_raw_dict
from linalg_pedagopy.tuteur.panneau import build_panel
from linalg_pedagopy.tuteur.registre import verifier_type
from linalg_pedagopy.tuteur.verificateurs import VerificationResult  # l'import enregistre les types
from linalg_pedagopy.tuteur.catalogue import (
    TYPE_LABELS,
    MarkdownText,
    _load_fiche_dict,
    _niveau_etoiles,
)


# Private vault for ExerciseSession secrets so students cannot read _fiche, _verification_spec,
# or mutate _unlocked via attribute access or __dict__.
_SESSION_VAULT: WeakKeyDictionary[Any, dict[str, Any]] = WeakKeyDictionary()


def _is_teacher_mode() -> bool:
    return config.tutor_mode in ("teacher", "enseignant")


class TeacherSheet(dict):
    """Fiche d'exercice (dictionnaire) affichée en Markdown, avec formules LaTeX, dans JupyterLab."""

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
                "- Relisez un palier avec `ex.indice(1)` … `ex.indice(4)` ;\n"
                "- étudiez l'exercice résolu analogue avec `ex.jumeau()` ;\n"
                "- pour repartir de zéro sur cet exercice, utilisez `ex.recommencer()`.\n\n"
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
        """Résout et affiche l'exercice jumeau analogue (palier 4)."""
        st = self._state()
        st["journal"].record_twin()
        st["ladder"].unlocked_level = max(st["ladder"].unlocked_level, 4)
        return evaluate_twin_spec(st["fiche"].get("jumeau"))

    def predict(self, *args: str, **kwargs: str) -> MarkdownText:
        """Enregistre la prédiction de l'étudiant avant d'ouvrir le laboratoire de contre-exemples."""
        st = self._state()
        preds: dict[str, str] = st["predictions"]
        if args and not kwargs:
            preds["enonce"] = str(args[0])
        for k, v in kwargs.items():
            preds[str(k)] = str(v)
        if not preds:
            raise ValueError("Fournissez au moins une prédiction (par exemple ex.predire('toujours vrai')).")
        st["journal"].record_prediction(preds)
        return MarkdownText(
            f"**Prédiction enregistrée** : `{preds}`.\n\n"
            "> Le laboratoire de contre-exemples est maintenant ouvert via `ex.labo()`."
        )

    def lab(self) -> CounterexampleLab:
        """Ouvre le laboratoire de contre-exemples, une fois la prédiction enregistrée."""
        st = self._state()
        return CounterexampleLab(
            st["verification_spec"],
            st["predictions"],
            on_test=st["journal"].record_lab_test,
        )

    def verify(self, response: Any) -> VerificationResult:
        """Vérifie la réponse de l'étudiant et donne un diagnostic sans révéler la solution."""
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
        """Renvoie le panneau interactif (ipywidgets) pour JupyterLab."""
        return build_panel(self)

    def teacher_sheet(self) -> TeacherSheet:
        """Renvoie la fiche complète, en mode enseignant seulement."""
        if not _is_teacher_mode():
            raise PermissionError(
                "L'inspection de la fiche complète est réservée au mode enseignant (tuteur.mode('enseignant'))."
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

exercice = exercise
