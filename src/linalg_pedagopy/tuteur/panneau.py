"""Backward-compatible re-export of linalg_pedagopy.tutor.panel."""

from __future__ import annotations

from linalg_pedagopy.tutor.panel import (
    PanelFallback,
    PanneauFallback,
    build_panel,
    build_panneau,
)

__all__ = ["PanelFallback", "PanneauFallback", "build_panel", "build_panneau"]
