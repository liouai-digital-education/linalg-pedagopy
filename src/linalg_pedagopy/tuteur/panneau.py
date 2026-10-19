"""Panneau interactif ipywidgets pour JupyterLab (§7.8)."""

from __future__ import annotations

import html
from typing import Any


class PanneauFallback:
    """Représentation HTML/Markdown du panneau lorsque ipywidgets n'est pas installé."""

    def __init__(self, session: Any) -> None:
        self.session = session

    def _repr_html_(self) -> str:
        enonce = html.escape(self.session.enonce())
        bilan = html.escape(self.session.bilan())
        return (
            f"<div style='border:1px solid #ccc; border-radius:8px; padding:12px;'>"
            f"<h4>Tuteur VMLS — Exercice {html.escape(self.session.id)}</h4>"
            f"<p>{enonce}</p>"
            f"<pre style='background:#f8f9fa; padding:8px;'>{bilan}</pre>"
            f"<small>Actions : <code>ex.indice()</code>, <code>ex.verifier(...)</code>, "
            f"<code>ex.jumeau()</code>, <code>ex.bilan()</code></small>"
            f"</div>"
        )

    def _repr_markdown_(self) -> str:
        return f"### Tuteur VMLS — Exercice {self.session.id}\n\n{self.session.enonce()}\n\n```\n{self.session.bilan()}\n```"

    def __str__(self) -> str:
        return f"{self.session.enonce()}\n\n{self.session.bilan()}"


def build_panneau(session: Any) -> Any:
    """Construit le panneau interactif ipywidgets pour une ExerciceSession (§7.8)."""
    try:
        import ipywidgets as widgets  # type: ignore[import-not-found]
    except ImportError:
        return PanneauFallback(session)

    header = widgets.HTML(
        value=f"<h3>Tuteur VMLS — Exercice {html.escape(session.id)}</h3>"
        f"<p>{html.escape(session.enonce())}</p>"
    )
    output_area = widgets.Textarea(
        value="Utilisez les boutons ci-dessous ou appelez ex.verifier(...) dans une cellule.",
        layout=widgets.Layout(width="100%", height="180px"),
        disabled=True,
    )

    btn_indice = widgets.Button(description="Indice suivant (1–4)", button_style="info")
    btn_jumeau = widgets.Button(description="Exercice jumeau", button_style="warning")
    btn_bilan = widgets.Button(description="Bilan", button_style="success")

    def _on_indice(_b: Any) -> None:
        output_area.value = session.indice()

    def _on_jumeau(_b: Any) -> None:
        output_area.value = str(session.jumeau())

    def _on_bilan(_b: Any) -> None:
        output_area.value = session.bilan()

    btn_indice.on_click(_on_indice)
    btn_jumeau.on_click(_on_jumeau)
    btn_bilan.on_click(_on_bilan)

    toolbar = widgets.HBox([btn_indice, btn_jumeau, btn_bilan])
    return widgets.VBox([header, toolbar, output_area])
