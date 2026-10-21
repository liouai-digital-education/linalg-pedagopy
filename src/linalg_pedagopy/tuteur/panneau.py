"""Panneau interactif ipywidgets pour JupyterLab (avec repli sans ipywidgets)."""

from __future__ import annotations

import html
from typing import Any


def _parse_answer(text: str) -> Any:
    """Interprète une réponse saisie dans le panneau (Vector, Matrix, nombre, liste, dictionnaire…).

    L'interpréteur sûr (``evaluation_sure``) n'accepte que Vector, Matrix, sqrt, Rational, pi,
    les nombres, listes, n-uplets, dictionnaires et chaînes.
    """
    import sympy as sp

    from linalg_pedagopy.objects.matrix import Matrix
    from linalg_pedagopy.objects.vector import Vector
    from linalg_pedagopy.tuteur.evaluation_sure import evaluer

    names = {"Vector": Vector, "Matrix": Matrix, "sqrt": sp.sqrt, "Rational": sp.Rational, "pi": sp.pi}
    return evaluer(text, names)


class PanelFallback:
    """Représentation du panneau quand ipywidgets n'est pas installé."""

    def __init__(self, session: Any) -> None:
        self.session = session

    def _repr_markdown_(self) -> str:
        return (
            f"{self.session.statement()}\n\n---\n\n{self.session.summary()}\n\n"
            "> Panneau graphique indisponible (installez `ipywidgets`). "
            "Utilisez `ex.indice()`, `ex.jumeau()`, `ex.verifier(...)` et `ex.bilan()`."
        )

    def _repr_html_(self) -> str:
        return (
            "<div style='border:1px solid #ccc; border-radius:8px; padding:12px;'>"
            f"<pre style='white-space:pre-wrap'>{html.escape(str(self.session.statement()))}</pre>"
            f"<pre style='white-space:pre-wrap'>{html.escape(str(self.session.summary()))}</pre>"
            "<small>Installez ipywidgets pour le panneau interactif. Actions : "
            "<code>ex.indice()</code>, <code>ex.jumeau()</code>, <code>ex.verifier(...)</code>, "
            "<code>ex.bilan()</code></small></div>"
        )

    def __str__(self) -> str:
        return f"{self.session.statement()}\n\n{self.session.summary()}"


def build_panel(session: Any) -> Any:
    """Construit le panneau interactif d'une séance : énoncé, indices, jumeau, réponse et bilan."""
    try:
        import ipywidgets as widgets  # type: ignore[import-not-found]
        from IPython.display import Markdown, display  # type: ignore[import-not-found]
    except ImportError:
        return PanelFallback(session)

    statement_out = widgets.Output()
    with statement_out:
        display(Markdown(str(session.statement())))

    feedback_out = widgets.Output(layout=widgets.Layout(border="1px solid #ddd", padding="6px", min_height="60px"))

    def _show(md: Any) -> None:
        feedback_out.clear_output()
        with feedback_out:
            display(Markdown(str(md)))

    btn_hint = widgets.Button(description="Indice suivant", button_style="info", icon="lightbulb-o")
    level_pick = widgets.Dropdown(options=[("Relire le palier…", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4)], value=0,
                                  layout=widgets.Layout(width="160px"))
    btn_twin = widgets.Button(description="Exercice jumeau", button_style="warning", icon="book")
    btn_summary = widgets.Button(description="Bilan", button_style="success", icon="list")
    answer = widgets.Text(placeholder="Votre réponse, ex. Matrix([[1, 0], [0, 1]]) ou Vector([1, 2])",
                          layout=widgets.Layout(width="70%"))
    btn_verify = widgets.Button(description="Vérifier", button_style="primary", icon="check")

    def _on_hint(_b: Any) -> None:
        _show(session.hint())

    def _on_pick(change: Any) -> None:
        if change.get("name") == "value" and change.get("new"):
            _show(session.hint(int(change["new"])))
            level_pick.value = 0

    def _on_twin(_b: Any) -> None:
        tw = session.twin()
        _show(tw._repr_markdown_() if hasattr(tw, "_repr_markdown_") else tw)

    def _on_summary(_b: Any) -> None:
        _show(session.summary())

    def _on_verify(_b: Any) -> None:
        text = answer.value.strip()
        if not text:
            _show("Saisissez une réponse avant de vérifier.")
            return
        try:
            obj = _parse_answer(text)
        except Exception as exc:  # noqa: BLE001
            from linalg_pedagopy.tuteur.verificateurs import raison_illisible

            _show(f"Réponse illisible : {raison_illisible(text, exc)} Exemple attendu : `Vector([1, 2])`.")
            return
        res = session.verify(obj)
        _show(res._repr_markdown_() if hasattr(res, "_repr_markdown_") else res)

    btn_hint.on_click(_on_hint)
    level_pick.observe(_on_pick, names="value")
    btn_twin.on_click(_on_twin)
    btn_summary.on_click(_on_summary)
    btn_verify.on_click(_on_verify)

    return widgets.VBox(
        [
            statement_out,
            widgets.HBox([btn_hint, level_pick, btn_twin, btn_summary]),
            widgets.HBox([answer, btn_verify]),
            feedback_out,
        ]
    )


PanneauFallback = PanelFallback
build_panneau = build_panel
