"""YAML sheet catalog, ExerciseSession, glossary, and cross-checking validate_sheet (§7.7, §7.8, §7.9, v4 Phase 0)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Mapping
from weakref import WeakKeyDictionary

import sympy as sp
import yaml

from linalg_pedagopy.config import TutorMode, config
from linalg_pedagopy.exercises.generators import TwinExercise
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing
from linalg_pedagopy.tutor.hints import HintLadder, evaluate_twin_spec
from linalg_pedagopy.tutor.journal import ExerciseJournal
from linalg_pedagopy.tutor.lab import CounterexampleLab, _eval_math_predicate, _structured_vector_candidates
from linalg_pedagopy.tutor.lock import LockedNamespace, _get_namespace_raw_dict
from linalg_pedagopy.tutor.panel import build_panel
from linalg_pedagopy.tutor.verifiers import (
    VerificationResult,
    _eval_data_expr,
    _parse_indexed_expr,
    verify_counterexample,
    verify_dimensions,
    verify_equalities,
    verify_formula,
    verify_inner_product,
    verify_matrix,
    verify_property,
    verify_value,
)

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


def glossary(term: str) -> str:
    """Translates and explains in French an English VMLS term (§7.2)."""
    terms = _load_glossaire()
    key = term.strip().lower()
    if key in terms:
        entry = terms[key]
        return f"{term} → {entry['fr']} : {entry['definition']}"
    for k, entry in terms.items():
        if key in k or key in entry.get("fr", "").lower():
            return f"{k} → {entry['fr']} : {entry['definition']}"
    raise KeyError(
        f"Terme {term!r} absent du glossaire. Termes disponibles : {sorted(terms.keys())}"
    )


def mode(new_mode: TutorMode | None = None) -> TutorMode:
    """Gets or sets the tutor mode ('student'/'etudiant' or 'teacher'/'enseignant', §7.9)."""
    if new_mode is not None:
        config.tutor_mode = new_mode
    return config.tutor_mode


def list_exercises() -> list[str]:
    """Returns the sorted list of available exercise IDs."""
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
            f"Exercices disponibles : {list_exercises()}"
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"La fiche {path} est mal formée.")
    return data


class MarkdownText(str):
    """Subclass of str with rich Markdown and LaTeX math rendering in JupyterLab."""

    def _repr_markdown_(self) -> str:
        return str(self)


class TeacherSheet(dict):
    """Exercise sheet dictionary with rich Markdown and LaTeX math rendering in JupyterLab."""

    def _repr_markdown_(self) -> str:
        lines = [
            f"## Fiche Enseignant — Exercice {self.get('id', '')}",
            f"**Type** : `{self.get('type', '')}` | **Page VMLS** : {self.get('page', '')}",
            f"**Source** : *{self.get('source', '')}*",
            f"**Écart VMLS** : *{self.get('ecart', '')}*",
            "",
            "### Énoncé",
            str(self.get("reformulation", "")),
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
            lines.extend([
                "",
                "### Exercice jumeau",
                f"`{self.get('jumeau')}`",
            ])
        return "\n".join(lines)


class ExerciseSession:
    """Interactive tutoring session for an exercise from VMLS Additional Exercises (§7.8, v4 Phase 0)."""

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
            "page": fiche_copy.get("page"),
            "type": str(fiche_copy.get("type", "calcul")),
            "reformulation": str(fiche_copy.get("reformulation", "")).strip(),
            "notions": list(fiche_copy.get("notions", [])),
            "source": str(fiche_copy.get("source", "")),
            "ecart": str(fiche_copy.get("ecart", "")),
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
    def page(self) -> Any:
        return self._state()["page"]

    @property
    def type(self) -> str:
        return self._state()["type"]  # type: ignore[no-any-return]

    @property
    def reformulation(self) -> str:
        return self._state()["reformulation"]  # type: ignore[no-any-return]

    @property
    def notions(self) -> list[str]:
        return list(self._state()["notions"])

    @property
    def source(self) -> str:
        return self._state()["source"]  # type: ignore[no-any-return]

    @property
    def ecart(self) -> str:
        return self._state()["ecart"]  # type: ignore[no-any-return]

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
        """Displays the French short reformulation and page reference to the VMLS companion with LaTeX math (§7.2, §7.8)."""
        page_ref = f", page {self.page}" if self.page is not None else ""
        notions_str = f"\n\n**Notions** : *{', '.join(self.notions)}*" if self.notions else ""
        source_str = f"\n\n*Source : {self.source}*" if self.source else ""
        return MarkdownText(
            f"### [Exercice {self.id} — Recueil Additional Exercises de VMLS{page_ref}]\n\n"
            f"{self.reformulation}{notions_str}{source_str}"
        )

    def hint(self, level: int | None = None, *, niveau: int | None = None) -> MarkdownText:
        """Unlocks and displays the next hint level (1 to 4) with LaTeX math (§7.5, §7.8)."""
        st = self._state()
        lvl = level if level is not None else niveau
        res = st["ladder"].request_hint(
            level=lvl,
            current_attempts=st["journal"].attempts,
        )
        return MarkdownText(res)

    def twin(self) -> TwinExercise | str:
        """Solves and displays the analogous twin exercise (level 4 help, §7.3 Principle 4)."""
        st = self._state()
        st["journal"].record_twin()
        st["ladder"].unlocked_level = max(st["ladder"].unlocked_level, 4)
        return evaluate_twin_spec(st["fiche"].get("jumeau"))

    def predict(self, *args: str, **kwargs: str) -> MarkdownText:
        """Records the student's prediction before opening the counterexample lab (§7.3 Principle 6, §7.8)."""
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
        """Opens the counterexample laboratory after recording a prediction (§7.8)."""
        st = self._state()
        return CounterexampleLab(
            st["verification_spec"],
            st["predictions"],
            on_test=st["journal"].record_lab_test,
        )

    def verify(self, response: Any) -> VerificationResult:
        """Verifies the student's response and produces a diagnostic without revealing the answer (§7.6, §7.8)."""
        st = self._state()
        spec = st["verification_spec"]
        v_type = str(spec.get("type", "valeur"))
        raw_data = _get_namespace_raw_dict(st["data"])

        if v_type in ("produit_scalaire", "inner_product"):
            res = verify_inner_product(response, spec, raw_data)
        elif v_type in ("matrice", "matrix"):
            res = verify_matrix(response, spec, raw_data)
        elif v_type in ("formule", "formula"):
            res = verify_formula(response, spec, raw_data)
        elif v_type in ("valeur", "value"):
            res = verify_value(response, spec, raw_data)
        elif v_type in ("propriete", "property"):
            res = verify_property(response, spec, raw_data)
        elif v_type in ("contre_exemple", "counterexample"):
            res = verify_counterexample(response, spec, raw_data)
        elif v_type in ("egalites", "equalities"):
            res = verify_equalities(response, spec, raw_data)
        elif v_type == "dimensions":
            res = verify_dimensions(response, spec, raw_data)
        elif v_type in ("labo", "lab"):
            if isinstance(response, Mapping):
                lab_inst = self.lab()
                rep = lab_inst.test(**response)
                res = VerificationResult(rep.found_counterexample, rep.message)
            else:
                res = VerificationResult(
                    False,
                    "Pour cet exercice vrai/faux, enregistrez votre prédiction avec ex.predict(...) / ex.predire(...) "
                    "puis explorez avec lab = ex.lab() ; lab.test(...).",
                )
        else:
            raise ValueError(f"Type de vérificateur inconnu : {v_type!r}")

        st["journal"].record_attempt(correct=res.valid, diagnostic=res.diagnostic)
        if res.valid:
            st["unlocked"] = True
        return res

    def summary(self) -> MarkdownText:
        """Returns the readable summary of the exercise journal (§7.8, §7.9)."""
        return MarkdownText(self._state()["journal"].format_summary())

    def panel(self) -> Any:
        """Returns the interactive ipywidgets panel for JupyterLab (§7.8)."""
        return build_panel(self)

    def teacher_sheet(self) -> TeacherSheet:
        """Returns the full exercise sheet in teacher mode only (§7.9)."""
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


ExerciceSession = ExerciseSession


def exercise(ex_id: str, *, journal_path: Path | None = None) -> ExerciseSession:
    """Loads the sheet for `ex_id` and starts an ExerciseSession (§7.8)."""
    fiche = _load_fiche_dict(ex_id)
    return ExerciseSession(fiche, journal_path=journal_path)


class ValidationReport:
    """Automatic validation report for an exercise sheet via validate_sheet (§7.9, v4 Phase 0)."""

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


_VALID_VERIFIER_TYPES = {
    "produit_scalaire",
    "inner_product",
    "matrice",
    "matrix",
    "formule",
    "formula",
    "valeur",
    "value",
    "propriete",
    "property",
    "contre_exemple",
    "counterexample",
    "labo",
    "lab",
    "egalites",
    "equalities",
    "dimensions",
}


def _cross_check_verifier(
    session: ExerciseSession,
    verif: Mapping[str, Any],
    raw_data: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    """Cross-checks the sheet's verifier by constructing a mathematical solution and testing acceptance/rejection."""
    errs: list[str] = []
    v_type = str(verif.get("type", ""))
    with suspend_tracing():
        try:
            if v_type in ("produit_scalaire", "inner_product"):
                var_name = str(verif.get("inconnue", verif.get("unknown", "x")))
                n = int(verif.get("taille", verif.get("size", raw_data.get("n", 4))))
                cible_str = str(verif.get("cible", verif.get("target")))
                target_expr, vec_syms = _parse_indexed_expr(cible_str, var_name, n, raw_data)
                coeffs = [sp.diff(target_expr, s) for s in vec_syms]
                sol_vec = Vector(coeffs)
                if not session.verify(sol_vec).valid:
                    errs.append("Cross-check échoué : le vecteur reconstruit par dérivation formelle est rejeté.")
                wrong_vec = Vector.ones(n) if sol_vec != Vector.ones(n) else Vector.zeros(n)
                if session.verify(wrong_vec).valid:
                    errs.append("Cross-check échoué : un vecteur erroné est accepté.")

            elif v_type in ("matrice", "matrix"):
                var_name = str(verif.get("inconnue", verif.get("unknown", "x")))
                n = int(verif.get("taille_entree", verif.get("input_size", raw_data.get("n", 6))))
                rows_list: list[list[sp.Expr]] = []
                if "lignes_cibles" in verif:
                    for line_s in verif["lignes_cibles"]:
                        rhs_part = line_s.split("=", 1)[1].strip() if "=" in line_s else line_s
                        ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, raw_data)
                        rows_list.append([sp.diff(ex_i, s) for s in vec_syms])
                else:
                    cible_str = str(verif.get("cible", verif.get("target")))
                    rhs_part = cible_str.split("=", 1)[1].strip() if "=" in cible_str else cible_str
                    m = int(verif.get("taille_sortie", verif.get("output_size", raw_data.get("m", 3))))
                    for i_val in range(1, m + 1):
                        local_d = dict(raw_data)
                        local_d["i"] = i_val
                        ex_i, vec_syms = _parse_indexed_expr(rhs_part, var_name, n, local_d)
                        rows_list.append([sp.diff(ex_i, s) for s in vec_syms])
                sol_mat = Matrix(rows_list)
                if not session.verify(sol_mat).valid:
                    errs.append("Cross-check échoué : la matrice reconstruite formellement est rejetée.")

            elif v_type in ("formule", "formula"):
                cible = verif.get("cible", verif.get("target"))
                if not session.verify(cible).valid:
                    errs.append("Cross-check échoué : la formule cible est rejetée.")

            elif v_type in ("valeur", "value"):
                calcul = verif.get("calcul", verif.get("compute"))
                if isinstance(calcul, Mapping):
                    sol_dict = {k: _eval_data_expr(str(v), raw_data) for k, v in calcul.items()}
                    if not session.verify(sol_dict).valid:
                        errs.append("Cross-check échoué : le dictionnaire de valeurs exactes est rejeté.")
                else:
                    sol_val = _eval_data_expr(str(calcul), raw_data)
                    if not session.verify(sol_val).valid:
                        errs.append("Cross-check échoué : la valeur calculée est rejetée.")

            elif v_type == "dimensions":
                if not session.verify(verif["attendu"]).valid:
                    errs.append("Cross-check échoué : les dimensions attendues sont rejetées.")

            elif v_type in ("propriete", "property"):
                prop = str(verif.get("propriete", ""))
                if prop == "left_right_inverse_row":
                    A = raw_data["A"]
                    # Construct a right inverse via A^T (A A^T)^{-1}
                    aat_inv = (A @ A.T).inv(strict=True)
                    assert isinstance(aat_inv, Matrix)
                    B_right = A.T @ aat_inv
                    if not session.verify(B_right).valid:
                        errs.append("Cross-check échoué : la pseudo-inverse à droite A^T(AA^T)^-1 est rejetée.")
                elif prop == "square_inverse":
                    A = raw_data["A"]
                    A_inv = A.inv(strict=True)
                    assert isinstance(A_inv, Matrix)
                    if not session.verify(A_inv @ A_inv).valid:
                        errs.append("Cross-check échoué : (A^-1)^2 est rejetée.")
                elif prop == "linear_system_solution":
                    A = raw_data["A"]
                    b = raw_data["b"]
                    sol = A.solve(b)
                    if not session.verify(sol.x).valid:
                        errs.append("Cross-check échoué : la solution de A.solve(b) est rejetée.")
                elif prop == "two_right_inverses":
                    B1 = Matrix([[1, 1], [0, 1], [0, 0]])
                    B2 = Matrix([[-2, -2], [-1, 0], [1, 1]])
                    if not session.verify((B1, B2)).valid:
                        errs.append("Cross-check échoué : deux inverses à droite valides sont rejetées.")
                elif prop == "kkt_minimum_norm":
                    C = raw_data["C"]
                    d = raw_data["d"]
                    cct_inv = (C @ C.T).inv(strict=True)
                    assert isinstance(cct_inv, Matrix)
                    x_opt = C.T @ (cct_inv @ d)
                    if not session.verify(x_opt).valid:
                        errs.append("Cross-check échoué : la solution KKT est rejetée.")

            elif v_type in ("contre_exemple", "counterexample"):
                cas = str(verif.get("cas", ""))
                if cas == "non_linearite_2_2":
                    if not session.verify({"x": Vector([1, 0]), "y": Vector([0, 1]), "alpha": 1, "beta": 1}).valid:
                        errs.append("Cross-check échoué sur non_linearite_2_2.")
                elif cas == "ordre_gram_schmidt_5_2":
                    if not session.verify((Vector([1, 0]), Vector([1, 1]))).valid:
                        errs.append("Cross-check échoué sur ordre_gram_schmidt_5_2.")
                elif cas == "inverse_matrice_positive_11_12":
                    if not session.verify(Matrix([[2, 1], [1, 2]])).valid:
                        errs.append("Cross-check échoué sur inverse_matrice_positive_11_12.")

            elif v_type in ("egalites", "equalities"):
                if session.verify(["0", "0"]).valid:
                    errs.append("Cross-check échoué : la chaîne triviale ['0', '0'] est acceptée.")

            elif v_type in ("labo", "lab"):
                cands = _structured_vector_candidates()
                for h in verif.get("hypotheses", []):
                    _eval_math_predicate(str(h), cands[0])
        except Exception as exc:
            errs.append(f"Exception lors du cross-check : {exc}")

    return (len(errs) == 0), errs


def validate_sheet(ex_id: str) -> ValidationReport:
    """Verifies that a YAML sheet is coherent, source-documented, leak-free, and passes solver cross-check (§7.9, v4 Phase 0)."""
    fiche = _load_fiche_dict(ex_id)
    erreurs: list[str] = []

    for req_key in ("id", "type", "reformulation", "verification", "indices"):
        if req_key not in fiche or not fiche[req_key]:
            erreurs.append(f"Champ obligatoire manquant ou vide : {req_key!r}")

    source_ok = True
    for meta_key in ("source", "ecart"):
        if meta_key not in fiche or not str(fiche.get(meta_key, "")).strip():
            source_ok = False
            erreurs.append(f"Champ de traçabilité VMLS manquant ou vide : {meta_key!r}")

    verif = dict(fiche.get("verification", {}))
    v_type = str(verif.get("type", ""))
    if v_type not in _VALID_VERIFIER_TYPES:
        erreurs.append(f"Type de vérificateur invalide : {v_type!r}")

    # 1. Target / verifier specification check
    cible_ok = True
    if v_type in ("produit_scalaire", "inner_product", "formule", "formula") and "cible" not in verif:
        cible_ok = False
        erreurs.append(f"Le vérificateur {v_type!r} requiert un champ 'cible'.")
    elif v_type in ("matrice", "matrix") and "cible" not in verif and "lignes_cibles" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'matrice' requiert 'cible' ou 'lignes_cibles'.")
    elif v_type in ("valeur", "value") and "calcul" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'valeur' requiert un champ 'calcul'.")
    elif v_type in ("propriete", "property") and "propriete" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'propriete' requiert un champ 'propriete'.")
    elif v_type in ("contre_exemple", "counterexample") and "cas" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'contre_exemple' requiert un champ 'cas'.")
    elif v_type == "dimensions" and "attendu" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'dimensions' requiert un champ 'attendu'.")
    elif v_type in ("labo", "lab") and "enonce" not in verif and "affirmations" not in verif:
        cible_ok = False
        erreurs.append("Le vérificateur 'labo' requiert 'enonce' ou 'affirmations'.")

    # 2. Twin generator check
    jumeau_ok = True
    jumeau_spec = fiche.get("jumeau")
    if jumeau_spec:
        twin_res = evaluate_twin_spec(str(jumeau_spec))
        if not isinstance(twin_res, TwinExercise) and "Erreur" in str(twin_res):
            jumeau_ok = False
            erreurs.append(f"Échec du générateur jumeau : {twin_res}")
    elif v_type not in ("labo", "lab"):
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
        if v_type not in ("labo", "lab"):
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
                    lit_obj = eval(lit_match, {"__builtins__": {}}, {"Vector": Vector, "Matrix": Matrix})  # noqa: S307
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
exercice = exercise
valider_fiche = validate_sheet
