"""Générateur de site web de documentation académique pour linalg_pedagopy.

Convertit les fichiers Markdown de docs/ en un site HTML autonome au design sobre,
élégant et universitaire (style Oxford / Princeton / Booktabs / MathJax).
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
from bs4 import BeautifulSoup
import jinja2
import markdown

RACINE = Path(__file__).resolve().parent.parent
DOCS_DIR = RACINE / "docs"
OUTPUT_DIR = DOCS_DIR / "site"
ASSETS_DIR = OUTPUT_DIR / "assets"
CSS_DIR = ASSETS_DIR / "css"
JS_DIR = ASSETS_DIR / "js"


def _url_source_depot() -> str | None:
    """URL « Source » de [project.urls] dans pyproject.toml, sans « / » final, ou None."""
    try:
        import tomllib
    except ImportError:  # Python 3.10 : liens relatifs
        return None
    urls = tomllib.loads((RACINE / "pyproject.toml").read_text(encoding="utf-8"))
    url = urls.get("project", {}).get("urls", {}).get("Source")
    return url.rstrip("/") if url else None


def _version_paquet() -> str:
    """Version du paquet lue dans pyproject.toml (source unique), affichée dans la barre latérale."""
    texte = (RACINE / "pyproject.toml").read_text(encoding="utf-8")
    trouve = re.search(r'^version\s*=\s*"([^"]+)"', texte, re.MULTILINE)
    return trouve.group(1) if trouve else "?"

PAGES = [
    {"id": "index", "src": "index.md", "dst": "index.html", "title": "Accueil & démarrage",
     "subtitle": "Présentation, installation, démarrage rapide et principes", "badge": "Portail", "number": "00"},
    {"id": "01_core", "src": "01_core_and_formal_computation.md", "dst": "01_core_and_formal_computation.html",
     "title": "01. Noyau formel & calcul exact",
     "subtitle": "Scalaires exacts, ZeroOracle, conditions et discussion de cas", "badge": "Fondement", "number": "01"},
    {"id": "02_objects", "src": "02_vectors_and_matrices.md", "dst": "02_vectors_and_matrices.html",
     "title": "02. Vecteurs, matrices & métriques",
     "subtitle": "Métriques, 4 vues du produit matriciel, sous-espaces et matrices structurées", "badge": "Objets", "number": "02"},
    {"id": "03_algorithms", "src": "03_algorithms_and_step_tracing.md", "dst": "03_algorithms_and_step_tracing.html",
     "title": "03. Algorithmes & traçabilité",
     "subtitle": "Trace à 4 niveaux, Gauss-Jordan, Gram-Schmidt, QR et moindres carrés", "badge": "Algèbre", "number": "03"},
    {"id": "04_tutor", "src": "04_tuteur.md", "dst": "04_tuteur.html", "title": "04. Le tuteur interactif",
     "subtitle": "Catalogue nommé, indices gradués, jumeau, laboratoire et panneau", "badge": "Pédagogie", "number": "04"},
    {"id": "05_exercises", "src": "05_pedagogical_exercises_and_sessions.md", "dst": "05_pedagogical_exercises_and_sessions.html",
     "title": "05. Exercices & sessions guidées",
     "subtitle": "Générateurs propres, exercices jumeaux, sessions et diagnostic d'erreurs", "badge": "Didactique", "number": "05"},
    {"id": "06_rendering", "src": "06_rendering_visualization_and_numerics.md", "dst": "06_rendering_visualization_and_numerics.html",
     "title": "06. Rendu, géométrie & numérique",
     "subtitle": "Formats d'explication, figures 2D/3D, Läuchli et Hilbert", "badge": "Visuel", "number": "06"},
    {"id": "07_api", "src": "07_api_reference.md", "dst": "07_api_reference.html", "title": "07. Référence de l'API",
     "subtitle": "Signatures, exceptions et alias français", "badge": "Référence", "number": "07"},
    {"id": "08_catalogue", "src": "08_catalogue_exercices.md", "dst": "08_catalogue_exercices.html",
     "title": "08. Catalogue des exercices",
     "subtitle": "Les 39 exercices du tuteur par thème et par niveau", "badge": "Exercices", "number": "08"},
    {"id": "09_jupyterlab", "src": "09_guide_jupyterlab.md", "dst": "09_guide_jupyterlab.html",
     "title": "09. Guide JupyterLab",
     "subtitle": "Installation pas à pas, premières cellules et dépannage", "badge": "Pratique", "number": "09"},
]

ACADEMIC_CSS = """/* ==========================================================================
   Feuille de style universitaire et sobre — linalg_pedagopy
   Typographie sobre d'inspiration universitaire
   ========================================================================== */

:root {
  --font-serif: "Newsreader", "Charter", "Bitstream Charter", "Georgia", "Cambria", serif;
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace;

  /* Palette claire : Papier d'archive et Encre noble */
  --bg-page: #fbfaf8;
  --bg-surface: #ffffff;
  --bg-sidebar: #f5f2eb;
  --bg-subtle: #eeeadf;
  --bg-code: #f3f0e8;

  --border-subtle: #e5dfd3;
  --border-strong: #cfc5b4;
  --border-academic: #1b365d;

  --text-main: #1d2129;
  --text-secondary: #57606a;
  --text-muted: #7d8590;
  --text-lead: #343a40;

  --accent-primary: #1b365d;      /* Oxford Navy */
  --accent-hover: #0f2240;
  --accent-crimson: #7a1f2e;      /* Bordeaux universitaire */
  --accent-gold: #966600;         /* Ambre antique */
  --accent-sage: #1e5631;         /* Vert académique */

  --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.05);
  --shadow-academic: 0 4px 12px rgba(27, 54, 93, 0.08);

  --sidebar-width: 290px;
  --toc-width: 230px;
  --header-height: 64px;
}

[data-theme="dark"] {
  --bg-page: #131518;
  --bg-surface: #1a1d22;
  --bg-sidebar: #16181d;
  --bg-subtle: #22262e;
  --bg-code: #1e222a;

  --border-subtle: #2d333f;
  --border-strong: #404958;
  --border-academic: #4872ab;

  --text-main: #e6edf3;
  --text-secondary: #9da7b3;
  --text-muted: #6e7681;
  --text-lead: #cbd5e1;

  --accent-primary: #5c8ed1;
  --accent-hover: #7ba3dd;
  --accent-crimson: #d46b7a;
  --accent-gold: #e2b714;
  --accent-sage: #4ade80;

  --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-academic: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* Base reset */
*, *::before, *::after {
  box-sizing: border-box;
}

html {
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%;
}

body {
  margin: 0;
  padding: 0;
  font-family: var(--font-sans);
  background-color: var(--bg-page);
  color: var(--text-main);
  line-height: 1.7;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* En-tête supérieur institutionnel */
.site-header {
  position: sticky;
  top: 0;
  height: var(--header-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 100;
  box-shadow: var(--shadow-subtle);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  text-decoration: none;
  color: var(--text-main);
}

.brand-crest {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background: var(--accent-primary);
  color: #ffffff;
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 1.15rem;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.brand-title {
  font-family: var(--font-serif);
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: var(--text-main);
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 220px;
  padding: 0.45rem 0.75rem 0.45rem 2rem;
  font-size: 0.875rem;
  background: var(--bg-code);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-main);
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  width: 300px;
  background: var(--bg-surface);
  box-shadow: 0 0 0 3px rgba(27, 54, 93, 0.12);
}

.search-icon {
  position: absolute;
  left: 0.65rem;
  color: var(--text-muted);
  pointer-events: none;
}

.theme-toggle-btn {
  background: transparent;
  border: 1px solid var(--border-subtle);
  padding: 0.45rem 0.65rem;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.theme-toggle-btn:hover {
  background: var(--bg-subtle);
  color: var(--text-main);
}

/* Structure globale */
.layout-container {
  display: flex;
  flex: 1;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

/* Sidebar gauche */
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-subtle);
  height: calc(100vh - var(--header-height));
  position: sticky;
  top: var(--header-height);
  overflow-y: auto;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
}

.sidebar-heading {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
  padding-left: 0.5rem;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.75rem;
  text-decoration: none;
  font-size: 0.885rem;
  color: var(--text-secondary);
  border-radius: 6px;
  transition: all 0.15s ease;
  line-height: 1.35;
}

.nav-item a:hover {
  background: var(--bg-subtle);
  color: var(--text-main);
}

.nav-item.active a {
  background: var(--bg-surface);
  color: var(--accent-primary);
  font-weight: 600;
  box-shadow: var(--shadow-subtle);
  border-left: 3px solid var(--accent-primary);
}

.nav-badge {
  font-size: 0.65rem;
  padding: 0.15rem 0.4rem;
  background: var(--bg-subtle);
  color: var(--text-muted);
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 600;
}

.nav-item.active .nav-badge {
  background: var(--accent-primary);
  color: #ffffff;
}

/* Contenu principal */
.main-content {
  flex: 1;
  padding: 2.5rem 3.5rem;
  max-width: 920px;
  min-width: 0;
}

/* Typographie académique */
.article-header {
  border-bottom: 2px solid var(--border-subtle);
  padding-bottom: 1.5rem;
  margin-bottom: 2.5rem;
}

.article-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--accent-primary);
  margin-bottom: 0.5rem;
}

.article-title {
  font-family: var(--font-serif);
  font-size: 2.35rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--text-main);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.5px;
}

.article-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
  font-style: italic;
}

.markdown-body {
  font-family: var(--font-serif);
  font-size: 1.08rem;
  color: var(--text-main);
}

.markdown-body p {
  margin: 1.25rem 0;
  line-height: 1.78;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  font-family: var(--font-sans);
  color: var(--text-main);
  font-weight: 700;
  line-height: 1.35;
  margin-top: 2.2rem;
  margin-bottom: 0.85rem;
  scroll-margin-top: calc(var(--header-height) + 1.5rem);
}

.markdown-body h2 {
  font-size: 1.55rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.4rem;
}

.markdown-body h3 {
  font-size: 1.25rem;
}

.markdown-body h4 {
  font-size: 1.05rem;
}

.markdown-body a {
  color: var(--accent-primary);
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: color 0.15s;
}

.markdown-body a:hover {
  color: var(--accent-crimson);
}

/* Tableaux scientifiques style Booktabs */
.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.75rem 0;
  font-family: var(--font-sans);
  font-size: 0.925rem;
  border-top: 2px solid var(--text-main);    /* \\toprule */
  border-bottom: 2px solid var(--text-main); /* \\bottomrule */
}

.markdown-body th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-main);
  border-bottom: 1px solid var(--text-main); /* \\midrule */
  background: var(--bg-subtle);
}

.markdown-body td {
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: top;
}

.markdown-body tr:last-child td {
  border-bottom: none;
}

.markdown-body tr:hover td {
  background: rgba(27, 54, 93, 0.03);
}

/* Blocs de code & syntax highlighting */
.code-container {
  position: relative;
  margin: 1.5rem 0;
  border-radius: 6px;
  background: var(--bg-code);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  box-shadow: var(--shadow-subtle);
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.85rem;
  background: var(--bg-subtle);
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.copy-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  transition: all 0.15s;
}

.copy-btn:hover {
  background: var(--bg-surface);
  color: var(--text-main);
}

pre {
  margin: 0;
  padding: 1rem;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 0.885rem;
  line-height: 1.6;
}

code {
  font-family: var(--font-mono);
  font-size: 0.88em;
  padding: 0.15em 0.35em;
  border-radius: 4px;
  background: var(--bg-code);
  border: 1px solid var(--border-subtle);
}

pre code {
  padding: 0;
  border: none;
  background: transparent;
}

/* Callouts académiques */
.callout {
  margin: 1.75rem 0;
  padding: 1.2rem 1.4rem;
  border-radius: 0 6px 6px 0;
  border-left: 4px solid var(--accent-primary);
  background: var(--bg-subtle);
  font-size: 0.98rem;
}

.callout-title {
  font-family: var(--font-sans);
  font-weight: 700;
  font-size: 0.825rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.callout.callout-note {
  border-left-color: var(--accent-primary);
}
.callout.callout-note .callout-title {
  color: var(--accent-primary);
}

.callout.callout-tip {
  border-left-color: var(--accent-sage);
}
.callout.callout-tip .callout-title {
  color: var(--accent-sage);
}

.callout.callout-important {
  border-left-color: var(--accent-crimson);
  background: rgba(122, 31, 46, 0.05);
}
.callout.callout-important .callout-title {
  color: var(--accent-crimson);
}

.callout.callout-warning {
  border-left-color: var(--accent-gold);
}
.callout.callout-warning .callout-title {
  color: var(--accent-gold);
}

.callout.callout-caution {
  border-left-color: #b91c1c;
}
.callout.callout-caution .callout-title {
  color: #b91c1c;
}

/* Formules mathématiques */
.math-display {
  margin: 1.5rem 0;
  padding: 0.75rem 0;
  overflow-x: auto;
  text-align: center;
}

/* Diagrammes Mermaid */
.mermaid-wrapper {
  margin: 1.75rem 0;
  padding: 1.25rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  display: flex;
  justify-content: center;
}

/* Table des matières droite (TOC) */
.toc-sidebar {
  width: var(--toc-width);
  position: sticky;
  top: var(--header-height);
  height: calc(100vh - var(--header-height));
  overflow-y: auto;
  padding: 2.5rem 1rem;
}

.toc-heading {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--text-muted);
  margin-bottom: 0.85rem;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.825rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.toc-item a {
  color: var(--text-secondary);
  text-decoration: none;
  display: block;
  padding: 0.2rem 0;
  transition: color 0.15s;
  line-height: 1.35;
}

.toc-item a:hover {
  color: var(--accent-primary);
}

.toc-item.toc-h3 {
  padding-left: 0.85rem;
  font-size: 0.785rem;
}

/* Pied de page et pagination de chapitre */
.chapter-nav {
  display: flex;
  justify-content: space-between;
  margin-top: 3.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-subtle);
  gap: 1rem;
}

.chapter-nav-btn {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  padding: 0.85rem 1.2rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  transition: all 0.2s ease;
  min-width: 200px;
}

.chapter-nav-btn:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-academic);
}

.nav-direction {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
}

.nav-target {
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--accent-primary);
  margin-top: 0.2rem;
}

.site-footer {
  margin-top: auto;
  background: var(--bg-surface);
  border-top: 1px solid var(--border-subtle);
  padding: 2rem;
  text-align: center;
  font-size: 0.825rem;
  color: var(--text-muted);
}

.site-footer a {
  color: var(--text-secondary);
  text-decoration: underline;
}

/* Résultats de recherche popup */
.search-results-modal {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
}

.search-modal-content {
  background: var(--bg-surface);
  width: 90%;
  max-width: 650px;
  border-radius: 8px;
  border: 1px solid var(--border-strong);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.search-modal-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
}

.modal-search-input {
  width: 100%;
  border: none;
  font-size: 1.1rem;
  background: transparent;
  color: var(--text-main);
  outline: none;
}

.search-modal-body {
  max-height: 420px;
  overflow-y: auto;
  padding: 1rem;
}

.search-result-item {
  padding: 0.75rem;
  border-radius: 6px;
  text-decoration: none;
  display: block;
  margin-bottom: 0.4rem;
  transition: background 0.15s;
}

.search-result-item:hover {
  background: var(--bg-subtle);
}

.search-result-title {
  font-weight: 600;
  color: var(--accent-primary);
  font-size: 0.95rem;
}

.search-result-snippet {
  font-size: 0.825rem;
  color: var(--text-secondary);
  margin-top: 0.2rem;
}

/* Responsive */
@media (max-width: 1100px) {
  .toc-sidebar {
    display: none;
  }
  .main-content {
    max-width: 100%;
    padding: 2rem;
  }
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    padding: 1.5rem 1rem;
  }
  .chapter-nav {
    flex-direction: column;
  }
}
"""

ACADEMIC_JS = """// Gestion du thème sombre / clair, recherche instantanée et interactivité
(function () {
  // 1. Thème
  const themeBtn = document.getElementById("themeToggle");
  const currentTheme = localStorage.getItem("academic-theme") || "light";
  document.documentElement.setAttribute("data-theme", currentTheme);

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-theme");
      const nextTheme = activeTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("academic-theme", nextTheme);
    });
  }

  // 2. Copie du code
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.closest(".code-container").querySelector("pre code").innerText;
      navigator.clipboard.writeText(code).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = "<span>✓ Copié</span>";
        setTimeout(() => {
          btn.innerHTML = originalText;
        }, 2000);
      });
    });
  });

  // 3. Recherche instantanée
  const searchInput = document.getElementById("searchInput");
  const modal = document.getElementById("searchModal");
  const modalInput = document.getElementById("modalSearchInput");
  const modalResults = document.getElementById("modalSearchResults");
  let searchData = [];

  fetch("assets/js/search_index.json")
    .then((r) => r.json())
    .then((data) => {
      searchData = data;
    })
    .catch((err) => console.error("Index non chargé :", err));

  function openSearch() {
    if (modal) {
      modal.style.display = "flex";
      modalInput.focus();
    }
  }

  function closeSearch() {
    if (modal) {
      modal.style.display = "none";
    }
  }

  if (searchInput) {
    searchInput.addEventListener("focus", openSearch);
  }

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeSearch();
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeSearch();
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        openSearch();
      }
    });
  }

  if (modalInput) {
    modalInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q || !searchData.length) {
        modalResults.innerHTML = "<p style='color:var(--text-muted);font-size:0.875rem;'>Saisissez un terme à rechercher...</p>";
        return;
      }

      const results = searchData
        .filter((item) => item.title.toLowerCase().includes(q) || item.content.toLowerCase().includes(q))
        .slice(0, 10);

      if (!results.length) {
        modalResults.innerHTML = "<p style='color:var(--text-muted);font-size:0.875rem;'>Aucun résultat trouvé pour « " + q + " ».</p>";
        return;
      }

      modalResults.innerHTML = results
        .map((res) => {
          return `
            <a href="${res.url}" class="search-result-item" onclick="document.getElementById('searchModal').style.display='none'">
              <div class="search-result-title">${res.pageTitle} &rarr; ${res.title}</div>
              <div class="search-result-snippet">${res.snippet}</div>
            </a>
          `;
        })
        .join("");
    });
  }

  // 4. Surbrillance dynamique de la TOC lors du scroll
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          document.querySelectorAll(".toc-list a").forEach((a) => {
            if (a.getAttribute("href") === "#" + id) {
              a.style.color = "var(--accent-primary)";
              a.style.fontWeight = "600";
            } else {
              a.style.color = "";
              a.style.fontWeight = "";
            }
          });
        }
      });
    },
    { rootMargin: "0px 0px -70% 0px" }
  );

  document.querySelectorAll(".markdown-body h2, .markdown-body h3").forEach((h) => {
    observer.observe(h);
  });
})();
"""

PAGE_TEMPLATE = jinja2.Template("""<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ page.title }} — linalg_pedagopy</title>
  <meta name="description" content="{{ page.subtitle }}">

  <!-- Typographie Web Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400&display=swap" rel="stylesheet">

  <!-- Feuilles de style -->
  <link rel="stylesheet" href="assets/css/academic.css">

  <!-- MathJax pour les formules mathématiques exactes -->
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }
    };
  </script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

  <!-- Moteur de diagrammes Mermaid.js -->
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' });
  </script>
</head>
<body>

  <!-- En-tête institutionnel -->
  <header class="site-header">
    <a href="index.html" class="header-brand">
      <div class="brand-crest">LP</div>
      <div>
        <div class="brand-title">linalg_pedagopy</div>
        <div class="brand-subtitle">Algèbre linéaire formelle et pédagogique</div>
      </div>
    </a>

    <div class="header-actions">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" class="search-input" placeholder="Rechercher... (Ctrl+K)" readonly>
      </div>
      <button id="themeToggle" class="theme-toggle-btn" title="Changer de thème">🌓</button>
    </div>
  </header>

  <!-- Modal de recherche plein texte -->
  <div id="searchModal" class="search-results-modal">
    <div class="search-modal-content">
      <div class="search-modal-header">
        <input type="text" id="modalSearchInput" class="modal-search-input" placeholder="Rechercher une fonction, un théorème, un symbole...">
      </div>
      <div id="modalSearchResults" class="search-modal-body">
        <p style="color:var(--text-muted);font-size:0.875rem;">Saisissez un mot-clé...</p>
      </div>
    </div>
  </div>

  <div class="layout-container">
    <!-- Barre latérale gauche de navigation -->
    <aside class="sidebar">
      <div class="sidebar-heading">Sommaire de l'ouvrage</div>
      <ul class="nav-list">
        {% for p in pages %}
        <li class="nav-item {% if p.id == page.id %}active{% endif %}">
          <a href="{{ p.dst }}">
            <span>{{ p.title }}</span>
            <span class="nav-badge">{{ p.badge }}</span>
          </a>
        </li>
        {% endfor %}
      </ul>

      <div style="margin-top:auto; padding-top:1.5rem; border-top:1px solid var(--border-subtle); font-size:0.75rem; color:var(--text-muted);">
        <strong>Version {{ version }}</strong><br>
        Calcul exact · tuteur interactif
      </div>
    </aside>

    <!-- Corps de texte de l'article -->
    <main class="main-content">
      <header class="article-header">
        <span class="article-badge">Chapitre {{ page.number }} • {{ page.badge }}</span>
        <h1 class="article-title">{{ page.title }}</h1>
        <p class="article-subtitle">{{ page.subtitle }}</p>
      </header>

      <article class="markdown-body">
        {{ content_html }}
      </article>

      <!-- Navigation entre chapitres -->
      <nav class="chapter-nav">
        {% if prev_page %}
        <a href="{{ prev_page.dst }}" class="chapter-nav-btn">
          <span class="nav-direction">&larr; Chapitre précédent</span>
          <span class="nav-target">{{ prev_page.title }}</span>
        </a>
        {% else %}
        <div></div>
        {% endif %}

        {% if next_page %}
        <a href="{{ next_page.dst }}" class="chapter-nav-btn" style="text-align:right;">
          <span class="nav-direction">Chapitre suivant &rarr;</span>
          <span class="nav-target">{{ next_page.title }}</span>
        </a>
        {% endif %}
      </nav>
    </main>

    <!-- Barre latérale droite : Sommaire de la page (TOC) -->
    <aside class="toc-sidebar">
      <div class="toc-heading">Sur cette page</div>
      <ul class="toc-list">
        {% for h in toc_items %}
        <li class="toc-item {% if h.level == 3 %}toc-h3{% endif %}">
          <a href="#{{ h.id }}">{{ h.title }}</a>
        </li>
        {% endfor %}
      </ul>
    </aside>
  </div>

  <!-- Pied de page -->
  <footer class="site-footer">
    <p>
      <strong>linalg_pedagopy</strong> — Algèbre Linéaire Formelle &amp; Pédagogique.<br>
      Conçu pour l'enseignement de l'algèbre linéaire en L1–L2.<br>
      Documentation sous licence MIT. Code source ouvert.
    </p>
  </footer>

  <script src="assets/js/academic.js"></script>
</body>
</html>
""")


def _jeton(i: int) -> str:
    """Jeton qui remplace un bloc protégé (formule, diagramme) pendant la conversion Markdown.

    Uniquement des lettres et chiffres : un jeton comme « __X_1__ » serait mis en gras par
    Markdown (<strong>X_1</strong>) et ne serait plus retrouvé à la restitution. Le « Z »
    final évite que AcadTok1Z soit une sous-chaîne de AcadTok12Z.
    """
    return f"AcadTok{i}Z"


JETON_RESIDUEL = re.compile(r"AcadTok\d+Z|ACADEMIC_TOKEN")


def preprocess_markdown(text: str) -> tuple[str, list[str]]:
    """Protège les formules mathématiques et convertit les callouts et mermaid."""
    tokens: list[str] = []

    def save_token(payload: str) -> str:
        tokens.append(payload)
        return _jeton(len(tokens) - 1)

    # 1. Protéger les blocs de diagramme Mermaid
    def replace_mermaid(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        html = f'<div class="mermaid-wrapper"><pre class="mermaid">{body}</pre></div>'
        return save_token(html)

    text = re.sub(r"```mermaid\n([\s\S]*?)```", replace_mermaid, text)

    # 2. Protéger les blocs Math display $$ ... $$
    def replace_math_display(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        html = f'<div class="math-display">$${body}$$</div>'
        return save_token(html)

    text = re.sub(r"\$\$([\s\S]*?)\$\$", replace_math_display, text)

    # 3. Protéger les maths inline $ ... $
    def replace_math_inline(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        return save_token(f"${body}$")

    text = re.sub(r"(?<!\\)\$([^\$\n]+?)\$", replace_math_inline, text)

    # 4. Remplacer les callouts GitHub
    callout_map = {
        "NOTE": ("callout-note", "Note informative"),
        "TIP": ("callout-tip", "Conseil & Astuce"),
        "IMPORTANT": ("callout-important", "Principe Essentiel / Théorème"),
        "WARNING": ("callout-warning", "Attention / Piège"),
        "CAUTION": ("callout-caution", "Avertissement critique"),
    }

    def replace_callout(match: re.Match[str]) -> str:
        kind = match.group(1).upper()
        content = match.group(2).strip()
        cls, title = callout_map.get(kind, ("callout-note", kind))
        # Formatter les paragraphes du contenu
        paragraphs = [p.strip() for p in content.split("\n>") if p.strip()]
        body_html = "".join(f"<p>{p}</p>" for p in paragraphs)
        html = f'<div class="callout {cls}"><div class="callout-title">{title}</div>{body_html}</div>'
        return save_token(html)

    text = re.sub(
        r"> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]([\s\S]*?)(?=\n\n|\Z)",
        replace_callout,
        text,
    )

    # 5. Réajuster les liens .md en .html (avec ou sans ancre)
    text = re.sub(r"\(([\w_-]+)\.md(#[\w-]*)?\)", r"(\1.html\2)", text)

    # 6. Les liens relatifs vers le code source (../src/...) sont écrits depuis docs/.
    #    Site publié (URL « Source » dans pyproject.toml) : lien vers le fichier sur GitHub ;
    #    sinon, lien relatif depuis docs/site/, d'où un niveau supplémentaire.
    base_source = _url_source_depot()
    cible = rf"({base_source}/blob/main/\1)" if base_source else r"(../../\1)"
    text = re.sub(r"\(\.\./((?:src|tests)/[^)\s]*)\)", cible, text)

    return text, tokens


def postprocess_html(html: str, tokens: list[str]) -> str:
    """Restaure les jetons protégés et améliore les blocs de code."""
    # Ordre décroissant : la restitution d'un bloc ne peut pas réintroduire un jeton déjà traité
    for i in reversed(range(len(tokens))):
        html = html.replace(_jeton(i), tokens[i])
    # Les ancres des titres sont calculées par Markdown sur le texte à jetons : on en retire le jeton
    # (« …-colonnes-de-acadtok24z » devient « …-colonnes-de »), pour des ancres lisibles et stables.
    html = re.sub(r"-?acadtok\d+z", "", html)
    reste = JETON_RESIDUEL.search(html)
    if reste:
        raise RuntimeError(f"Jeton non restitué dans le HTML : {html[max(0, reste.start() - 60):reste.end() + 20]!r}")

    soup = BeautifulSoup(html, "html.parser")

    # Envelopper les blocs pre dans des .code-container avec boutons de copie
    for pre in soup.find_all("pre"):
        if pre.find_parent(class_="mermaid-wrapper") or "mermaid" in pre.get("class", []):
            continue
        code = pre.find("code")
        lang = "Code"
        if code and code.get("class"):
            for cls in code.get("class", []):
                if cls.startswith("language-"):
                    lang = cls.replace("language-", "").capitalize()
                    break

        wrapper = soup.new_tag("div", **{"class": "code-container"})
        header = soup.new_tag("div", **{"class": "code-header"})
        lang_span = soup.new_tag("span")
        lang_span.string = lang
        header.append(lang_span)

        copy_btn = soup.new_tag("button", **{"class": "copy-btn", "title": "Copier dans le presse-papiers"})
        copy_btn.string = "📋 Copier"
        header.append(copy_btn)

        pre.wrap(wrapper)
        wrapper.insert(0, header)

    return str(soup)


def extract_toc(html: str) -> list[dict[str, Any]]:
    """Extrait la hiérarchie des titres H2 et H3 pour la table des matières de page."""
    soup = BeautifulSoup(html, "html.parser")
    toc = []
    for h in soup.find_all(["h2", "h3"]):
        level = 2 if h.name == "h2" else 3
        title = h.get_text()
        # Assurer la présence d'un identifiant
        h_id = h.get("id")
        if not h_id:
            h_id = re.sub(r"[^\w\s-]", "", title).strip().lower().replace(" ", "-")
            h["id"] = h_id
        toc.append({"level": level, "title": title, "id": h_id})
    return toc


def build_site() -> None:
    """Génère le site web complet dans docs/site/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CSS_DIR.mkdir(parents=True, exist_ok=True)
    JS_DIR.mkdir(parents=True, exist_ok=True)

    # Écriture des assets statiques CSS et JS
    (CSS_DIR / "academic.css").write_text(ACADEMIC_CSS, encoding="utf-8")
    (JS_DIR / "academic.js").write_text(ACADEMIC_JS, encoding="utf-8")

    search_index = []

    for idx, page in enumerate(PAGES):
        src_path = DOCS_DIR / page["src"]
        if not src_path.exists():
            print(f"Avertissement : Fichier source manquant : {src_path}")
            continue

        raw_md = src_path.read_text(encoding="utf-8")

        # Prétraitement et protection
        preprocessed_md, tokens = preprocess_markdown(raw_md)

        # Conversion Markdown -> HTML
        content_html_raw = markdown.markdown(
            preprocessed_md,
            extensions=["tables", "fenced_code", "toc"],
        )

        # Post-traitement HTML
        content_html = postprocess_html(content_html_raw, tokens)

        # Extraction de la TOC
        toc_items = extract_toc(content_html)

        # Indexation pour la recherche plein texte
        soup = BeautifulSoup(content_html, "html.parser")
        for section in soup.find_all(["h2", "h3"]):
            title = section.get_text()
            s_id = section.get("id", "")
            # Prendre le texte suivant
            next_p = section.find_next("p")
            snippet = next_p.get_text()[:160] + "..." if next_p else ""
            search_index.append(
                {
                    "pageTitle": page["title"],
                    "title": title,
                    "url": f"{page['dst']}#{s_id}",
                    "snippet": snippet,
                    "content": title + " " + snippet,
                }
            )

        prev_page = PAGES[idx - 1] if idx > 0 else None
        next_page = PAGES[idx + 1] if idx < len(PAGES) - 1 else None

        rendered_html = PAGE_TEMPLATE.render(
            page=page,
            pages=PAGES,
            prev_page=prev_page,
            next_page=next_page,
            content_html=content_html,
            toc_items=toc_items,
            version=_version_paquet(),
        )

        dst_path = OUTPUT_DIR / page["dst"]
        dst_path.write_text(rendered_html, encoding="utf-8")
        print(f"Page générée : {dst_path}")

    # Écriture de l'index de recherche JSON
    (JS_DIR / "search_index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Index de recherche client généré : assets/js/search_index.json")
    print(f"Site web académique généré avec succès dans : {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    build_site()
