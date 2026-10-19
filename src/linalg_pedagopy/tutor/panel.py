"""Interactive ipywidgets panel for JupyterLab (§7.8, v4 Phase 0)."""

from __future__ import annotations

import html
from typing import Any


class PanelFallback:
    """HTML/Markdown representation of the panel when ipywidgets is not installed."""

    def __init__(self, session: Any) -> None:
        self.session = session

    def _repr_html_(self) -> str:
        stmt = html.escape(self.session.statement())
        summ = html.escape(self.session.summary())
        return (
            f"<div style='border:1px solid #ccc; border-radius:8px; padding:12px;'>"
            f"<h4>Tuteur VMLS — Exercice {html.escape(self.session.id)}</h4>"
            f"<p>{stmt}</p>"
            f"<pre style='background:#f8f9fa; padding:8px;'>{summ}</pre>"
            f"<small>Actions : <code>ex.hint()</code>, <code>ex.verify(...)</code>, "
            f"<code>ex.twin()</code>, <code>ex.summary()</code></small>"
            f"</div>"
        )

    def _repr_markdown_(self) -> str:
        return (
            f"### Tuteur VMLS — Exercice {self.session.id}\n\n"
            f"{self.session.statement()}\n\n```\n{self.session.summary()}\n```"
        )

    def __str__(self) -> str:
        return f"{self.session.statement()}\n\n{self.session.summary()}"


def build_panel(session: Any) -> Any:
    """Builds the interactive ipywidgets panel for an ExerciseSession (§7.8)."""
    try:
        import ipywidgets as widgets  # type: ignore[import-not-found]
    except ImportError:
        return PanelFallback(session)

    header = widgets.HTML(
        value=f"<h3>Tuteur VMLS — Exercice {html.escape(session.id)}</h3>"
        f"<p>{html.escape(session.statement())}</p>"
    )
    output_area = widgets.Textarea(
        value="Utilisez les boutons ci-dessous ou appelez ex.verify(...) / ex.verifier(...) dans une cellule.",
        layout=widgets.Layout(width="100%", height="180px"),
        disabled=True,
    )

    btn_hint = widgets.Button(description="Indice suivant (1–4)", button_style="info")
    btn_twin = widgets.Button(description="Exercice jumeau", button_style="warning")
    btn_summary = widgets.Button(description="Bilan", button_style="success")

    def _on_hint(_b: Any) -> None:
        output_area.value = session.hint()

    def _on_twin(_b: Any) -> None:
        output_area.value = str(session.twin())

    def _on_summary(_b: Any) -> None:
        output_area.value = session.summary()

    btn_hint.on_click(_on_hint)
    btn_twin.on_click(_on_twin)
    btn_summary.on_click(_on_summary)

    toolbar = widgets.HBox([btn_hint, btn_twin, btn_summary])
    return widgets.VBox([header, toolbar, output_area])


PanneauFallback = PanelFallback
build_panneau = build_panel
