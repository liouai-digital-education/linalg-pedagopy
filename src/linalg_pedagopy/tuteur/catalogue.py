"""Chargement des fiches YAML, session d'exercice, glossaire et outil valider_fiche (§7.7, §7.8, §7.9)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Mapping

import yaml

from linalg_pedagopy.config import TutorMode, config
from linalg_pedagopy.exercises.generators import TwinExercise
from linalg_pedagopy.tuteur.indices import HintLadder, evaluate_twin_spec
from linalg_pedagopy.tuteur.journal import ExerciseJournal
from linalg_pedagopy.tuteur.labo import CounterexampleLab
from linalg_pedagopy.tuteur.panneau import build_panneau
from linalg_pedagopy.tuteur.verificateurs import (
    VerificationResult,
    verifier_contre_exemple,
    verifier_dimensions,
    verifier_egalites,
    verifier_formule,
    verifier_matrice,
    verifier_produit_scalaire,
    verifier_propriete,
    verifier_valeur,
)
from linalg_pedagopy.tuteur.verrou import LockedNamespace

_TUTEUR_DIR = Path(__file__).parent
_FICHES_DIR = _TUTEUR_DIR / "fiches"
_GLOSSAIRE_PATH = _TUTEUR_DIR / "glossaire.yaml"


@lru_cache(maxsize=1)
def _load_glossaire() -> dict[str, dict[str, str]]:
    if not _GLOSSAIRE_PATH.exists():
        return {}
    with _GLOSSAIRE_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if isinstance(data, dict) and isinstance(data.get("terms"), dict):
        return data["terms"]
    return {}


def glossaire(terme: str) -> str:
    """Traduit et explique en français un terme anglais de VMLS (§7.2)."""
    terms = _load_glossaire()
    key = terme.strip().lower()
    if key in terms:
        entry = terms[key]
        return f"{terme} → {entry['fr']} : {entry['definition']}"
    for k, entry in terms.items():
        if key in k or key in entry.get("fr", "").lower():
            return f"{k} → {entry['fr']} : {entry['definition']}"
    raise KeyError(
        f"Terme {terme!r} absent du glossaire. Termes disponibles : {sorted(terms.keys())}"
    )


def mode(nouveau_mode: TutorMode | None = None) -> TutorMode:
    """Consulte ou change le mode du tuteur ('etudiant' ou 'enseignant', §7.9)."""
    if nouveau_mode is not None:
        config.tutor_mode = nouveau_mode
    return config.tutor_mode


def lister_exercices() -> list[str]:
    """Renvoie la liste triée des identifiants d'exercices disponibles dans tuteur/fiches/."""
    if not _FICHES_DIR.exists():
        return []
    ids: list[str] = []
    for p in _FICHES_DIR.glob("*.yaml"):
        ids.append(p.stem)

    def _sort_key(s: str) -> tuple[int, int]:
        parts = s.split(".")
        try:
            return (int(parts[0]), int(parts[1]))
        except Exception:
            return (999, 999)

    return sorted(ids, key=_sort_key)


def _load_fiche_dict(ex_id: str) -> dict[str, Any]:
    norm_id = str(ex_id).strip()
    path = _FICHES_DIR / f"{norm_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Aucune fiche trouvée pour l'exercice {norm_id!r}. "
            f"Exercices disponibles : {lister_exercices()}"
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"La fiche {path} est mal formée.")
    return data


class ExerciceSession:
    """Séance interactive d'accompagnement sur un exercice du recueil VMLS (§7.8)."""

    def __init__(self, fiche: Mapping[str, Any], *, journal_path: Path | None = None) -> None:
        self._fiche = dict(fiche)
        self.id = str(fiche["id"])
        self.page = fiche.get("page")
        self.type = str(fiche.get("type", "calcul"))
        self.reformulation = str(fiche.get("reformulation", "")).strip()
        self.notions: list[str] = list(fiche.get("notions", []))
        self._verification_spec: dict[str, Any] = dict(fiche.get("verification", {}))
        self._unlocked: bool = False
        self.predictions: dict[str, str] = {}

        self.journal = ExerciseJournal(self.id, path=journal_path)
        self.donnees = LockedNamespace(
            dict(fiche.get("donnees", {})),
            is_unlocked=lambda: self._unlocked or config.tutor_mode == "enseignant",
        )
        self._ladder = HintLadder(
            hints=tuple(str(h) for h in fiche.get("indices", [])),
            jumeau_spec=fiche.get("jumeau"),
            on_unlock=self.journal.record_hint,
        )

    def enonce(self) -> str:
        """Affiche la reformulation courte en français et le renvoi à la page du recueil (§7.2, §7.8)."""
        page_ref = f", page {self.page}" if self.page is not None else ""
        notions_str = f"\nNotions : {', '.join(self.notions)}" if self.notions else ""
        return (
            f"[Exercice {self.id} — Recueil Additional Exercises de VMLS{page_ref}]\n"
            f"{self.reformulation}{notions_str}"
        )

    def indice(self, niveau: int | None = None) -> str:
        """Débloque et affiche le prochain niveau d'indice (1 à 4) (§7.5, §7.8)."""
        return self._ladder.request_hint(
            level=niveau,
            current_attempts=self.journal.attempts,
        )

    def jumeau(self) -> TwinExercise | str:
        """Résout et affiche l'exercice jumeau analogue (niveau 4 d'aide, §7.3 Principe 4)."""
        self.journal.record_twin()
        self._ladder.unlocked_level = max(self._ladder.unlocked_level, 4)
        return evaluate_twin_spec(self._fiche.get("jumeau"))

    def predire(self, *args: str, **kwargs: str) -> str:
        """Enregistre la prédiction de l'étudiant avant d'ouvrir le laboratoire (§7.3 Principe 6, §7.8)."""
        if args and not kwargs:
            self.predictions["enonce"] = str(args[0])
        for k, v in kwargs.items():
            self.predictions[str(k)] = str(v)
        if not self.predictions:
            raise ValueError("Fournissez au moins une prédiction (ex. ex.predire('toujours vrai')).")
        self.journal.record_prediction(self.predictions)
        return (
            f"Prédiction enregistrée : {self.predictions}. "
            "Le laboratoire de contre-exemples est maintenant ouvert via ex.labo()."
        )

    def labo(self) -> CounterexampleLab:
        """Ouvre le laboratoire de contre-exemples après enregistrement d'une prédiction (§7.8)."""
        return CounterexampleLab(
            self._verification_spec,
            self.predictions,
            on_test=self.journal.record_lab_test,
        )

    def verifier(self, reponse: Any) -> VerificationResult:
        """Vérifie la réponse de l'étudiant et produit un diagnostic sans révéler la solution (§7.6, §7.8)."""
        v_type = str(self._verification_spec.get("type", "valeur"))
        raw_data = self.donnees.raw_dict()

        if v_type == "produit_scalaire":
            res = verifier_produit_scalaire(reponse, self._verification_spec, raw_data)
        elif v_type == "matrice":
            res = verifier_matrice(reponse, self._verification_spec, raw_data)
        elif v_type == "formule":
            res = verifier_formule(reponse, self._verification_spec, raw_data)
        elif v_type == "valeur":
            res = verifier_valeur(reponse, self._verification_spec, raw_data)
        elif v_type == "propriete":
            res = verifier_propriete(reponse, self._verification_spec, raw_data)
        elif v_type == "contre_exemple":
            res = verifier_contre_exemple(reponse, self._verification_spec, raw_data)
        elif v_type == "egalites":
            res = verifier_egalites(reponse, self._verification_spec, raw_data)
        elif v_type == "dimensions":
            res = verifier_dimensions(reponse, self._verification_spec, raw_data)
        elif v_type == "labo":
            if isinstance(reponse, Mapping):
                lab = self.labo()
                rep = lab.tester(**reponse)
                res = VerificationResult(rep.found_counterexample, rep.message)
            else:
                res = VerificationResult(
                    False,
                    "Pour cet exercice vrai/faux, enregistrez votre prédiction avec ex.predire(...) "
                    "puis explorez avec lab = ex.labo() ; lab.tester(...).",
                )
        else:
            raise ValueError(f"Type de vérificateur inconnu : {v_type!r}")

        self.journal.record_attempt(correct=res.valide, diagnostic=res.diagnostic)
        if res.valide:
            self._unlocked = True
        return res

    def bilan(self) -> str:
        """Renvoie la synthèse lisible du journal de l'exercice (§7.8, §7.9)."""
        return self.journal.format_bilan()

    def panneau(self) -> Any:
        """Renvoie le panneau interactif ipywidgets pour JupyterLab (§7.8)."""
        return build_panneau(self)

    def fiche_enseignant(self) -> dict[str, Any]:
        """Renvoie la fiche complète en mode enseignant uniquement (§7.9)."""
        if config.tutor_mode != "enseignant":
            raise PermissionError(
                "L'inspection de la fiche complète est réservée au mode enseignant (tuteur.mode('enseignant'))."
            )
        return dict(self._fiche)


def exercice(ex_id: str, *, journal_path: Path | None = None) -> ExerciceSession:
    """Charge la fiche de l'exercice `ex_id` et démarre une séance du tuteur (§7.8)."""
    fiche = _load_fiche_dict(ex_id)
    return ExerciceSession(fiche, journal_path=journal_path)


@dataclass(frozen=True)
class ValidationReport:
    """Rapport de validation automatique d'une fiche d'exercice par valider_fiche (§7.9)."""

    id: str
    valide: bool
    cible_ok: bool
    jumeau_ok: bool
    indices_sans_fuite: bool
    erreurs: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valide


_VALID_VERIFIER_TYPES = {
    "produit_scalaire",
    "matrice",
    "formule",
    "valeur",
    "propriete",
    "contre_exemple",
    "labo",
    "egalites",
    "dimensions",
}


def valider_fiche(ex_id: str) -> ValidationReport:
    """Vérifie qu'une fiche YAML est cohérente : cible bien formée, jumeau résoluble, indices sans la réponse (§7.9)."""
    fiche = _load_fiche_dict(ex_id)
    erreurs: list[str] = []

    for req_key in ("id", "type", "reformulation", "verification", "indices"):
        if req_key not in fiche or not fiche[req_key]:
            erreurs.append(f"Champ obligatoire manquant ou vide : {req_key!r}")

    verif = dict(fiche.get("verification", {}))
    v_type = str(verif.get("type", ""))
    if v_type not in _VALID_VERIFIER_TYPES:
        erreurs.append(f"Type de vérificateur invalide : {v_type!r}")

    # 1. Contrôle de la cible / spécification du vérificateur
    cible_ok = True
    if v_type in ("produit_scalaire", "formule") and "cible" not in verif:
        cible_ok = False
        erreurs.append(f"Le vérificateur {v_type!r} requiert un champ 'cible'.")
    elif v_type == "matrice" and "cible" not in verif and "lignes_cibles" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'matrice' requiert 'cible' ou 'lignes_cibles'.")
    elif v_type == "valeur" and "calcul" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'valeur' requiert un champ 'calcul'.")
    elif v_type == "propriete" and "propriete" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'propriete' requiert un champ 'propriete'.")
    elif v_type == "contre_exemple" and "cas" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'contre_exemple' requiert un champ 'cas'.")
    elif v_type == "dimensions" and "attendu" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'dimensions' requiert un champ 'attendu'.")
    elif v_type == "labo" and "enonce" not in verif and "affirmations" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'labo' requiert 'enonce' ou 'affirmations'.")

    # 2. Contrôle du générateur jumeau
    jumeau_ok = True
    jumeau_spec = fiche.get("jumeau")
    if jumeau_spec:
        twin_res = evaluate_twin_spec(str(jumeau_spec))
        if not isinstance(twin_res, TwinExercise) and "Erreur" in str(twin_res):
            jumeau_ok = False
            erreurs.append(f"Échec du générateur jumeau : {twin_res}")
    elif v_type != "labo":
        jumeau_ok = False
        erreurs.append("Champ 'jumeau' manquant.")

    # 3. Contrôle d'absence de fuite de la réponse dans les indices
    indices_sans_fuite = True
    hints = [str(h) for h in fiche.get("indices", [])]
    if len(hints) < 3:
        erreurs.append("Une fiche doit comporter au moins 3 niveaux d'indices textuels.")
        indices_sans_fuite = False

    session = ExerciceSession(fiche)
    raw_cible_str = str(verif.get("cible", ""))
    for idx, h_text in enumerate(hints, start=1):
        if raw_cible_str and len(raw_cible_str) > 4 and raw_cible_str in h_text:
            indices_sans_fuite = False
            erreurs.append(f"L'indice {idx} contient littéralement la cible {raw_cible_str!r}.")
        # S'assurer qu'aucun indice passé tel quel au vérificateur n'est accepté comme bonne réponse
        if v_type != "labo":
            try:
                check_h = session.verifier(h_text)
                if check_h.valide:
                    indices_sans_fuite = False
                    erreurs.append(f"L'indice {idx} est accepté comme réponse valide par le vérificateur !")
            except Exception:
                pass

    valide = cible_ok and jumeau_ok and indices_sans_fuite and not erreurs
    return ValidationReport(
        id=str(fiche.get("id", ex_id)),
        valide=valide,
        cible_ok=cible_ok,
        jumeau_ok=jumeau_ok,
        indices_sans_fuite=indices_sans_fuite,
        erreurs=tuple(erreurs),
    )
