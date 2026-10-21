"""Les exemples de la documentation s'exécutent et affichent ce qu'ils annoncent.

Chaque bloc ```python des pages listées dans ``PAGES`` est exécuté, dans l'ordre, avec un état
partagé entre les blocs d'une même page (comme dans un carnet), dans un répertoire temporaire
et avec ``MPLBACKEND=Agg``. Le test échoue si un bloc lève une exception.

Convention de marquage des sorties (voir docs/dev/tests_et_verifications.md) :

- ``# texte`` : commentaire libre, jamais comparé ;
- ``#> texte`` : ligne de sortie exacte. Les lignes ``#>`` qui suivent immédiatement une
  instruction ``print(...)`` sont comparées, ligne à ligne, à ce qu'elle affiche
  (espaces de fin ignorés ; ``#>`` seul désigne une ligne vide) ;
- ``#> …`` en dernière ligne : la sortie doit seulement commencer par les lignes données ;
- ``<!-- exemple: non exécuté -->`` sur la ligne non vide qui précède le bloc : bloc ignoré.
"""

from __future__ import annotations

import ast
import contextlib
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
PAGES = [
    "README.md",
    "docs/index.md",
    *sorted(
        str(p.relative_to(RACINE)).replace("\\", "/")
        for p in (RACINE / "docs").glob("0*.md")
        if not p.name.startswith(("07", "08"))
    ),
    "TUTORIAL.md",
]
# Pages dont l'exécution dépasse 5 s : écartées par « pytest -m "not lent" ».
LENTES: set[str] = set()

MARQUEUR_IGNORE = "<!-- exemple: non exécuté -->"
SORTIE = re.compile(r"^#>(?: (.*))?$")
TRONQUE = "…"


@dataclass
class Bloc:
    page: str
    ligne: int  # ligne de la page où commence le code (après la clôture ```python)
    code: str


def extraire_blocs(page: str) -> list[Bloc]:
    """Blocs ```python de ``page``, hors blocs précédés du marqueur « non exécuté »."""
    lignes = (RACINE / page).read_text(encoding="utf-8").splitlines()
    blocs: list[Bloc] = []
    precedente = ""
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        if ligne.strip() == "```python":
            debut = i + 1
            fin = debut
            while fin < len(lignes) and lignes[fin].strip() != "```":
                fin += 1
            if precedente.strip() != MARQUEUR_IGNORE:
                blocs.append(Bloc(page, debut + 1, "\n".join(lignes[debut:fin]) + "\n"))
            i = fin + 1
            precedente = ""
            continue
        if ligne.strip():
            precedente = ligne
        i += 1
    return blocs


def _sortie_attendue(lignes: list[str], apres: int) -> list[str] | None:
    """Lignes ``#>`` qui suivent immédiatement la ligne ``apres`` (index 0) du bloc."""
    attendu: list[str] = []
    for ligne in lignes[apres + 1 :]:
        m = SORTIE.match(ligne.strip())
        if not m:
            break
        attendu.append((m.group(1) or "").rstrip())
    return attendu or None


def _est_print(instruction: ast.stmt) -> bool:
    return (
        isinstance(instruction, ast.Expr)
        and isinstance(instruction.value, ast.Call)
        and isinstance(instruction.value.func, ast.Name)
        and instruction.value.func.id == "print"
    )


def executer_bloc(bloc: Bloc, espace: dict[str, object]) -> None:
    """Exécute ``bloc`` instruction par instruction et compare les sorties marquées ``#>``."""
    arbre = ast.parse(bloc.code, filename=bloc.page)
    ast.increment_lineno(arbre, bloc.ligne - 1)
    lignes = bloc.code.splitlines()
    for instruction in arbre.body:
        attendu = None
        if _est_print(instruction):
            assert instruction.end_lineno is not None
            attendu = _sortie_attendue(lignes, instruction.end_lineno - bloc.ligne)
        code = compile(ast.Module(body=[instruction], type_ignores=[]), bloc.page, "exec")
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            exec(code, espace)  # noqa: S102 - exemples de la documentation du dépôt
        if attendu is None:
            continue
        obtenu = [ligne.rstrip() for ligne in tampon.getvalue().rstrip("\n").split("\n")]
        if attendu[-1] == TRONQUE:
            attendu = attendu[:-1]
            obtenu = obtenu[: len(attendu)]
        if obtenu != attendu:
            pytest.fail(
                f"{bloc.page}:{instruction.lineno} : sortie différente de la documentation\n"
                + "attendu :\n"
                + "\n".join(f"  {ligne}" for ligne in attendu)
                + "\nobtenu :\n"
                + "\n".join(f"  {ligne}" for ligne in obtenu)
            )


def _parametres() -> list[object]:
    return [
        pytest.param(page, marks=[pytest.mark.lent] if page in LENTES else [], id=page)
        for page in PAGES
    ]


def test_toutes_les_pages_existent() -> None:
    for page in PAGES:
        assert (RACINE / page).is_file(), page


def test_la_convention_de_sortie_est_appliquee() -> None:
    espace: dict[str, object] = {}
    executer_bloc(Bloc("essai.md", 1, 'print("a\\n\\nb")\n#> a\n#>\n#> b\n'), espace)
    executer_bloc(Bloc("essai.md", 1, 'print("a\\nb\\nc")\n#> a\n#> …\n# libre\n'), espace)
    executer_bloc(Bloc("essai.md", 1, 'print("a")\n# commentaire libre, non comparé\n'), espace)
    with pytest.raises(pytest.fail.Exception, match="essai.md:2 : sortie différente"):
        executer_bloc(Bloc("essai.md", 1, 'x = 1\nprint(x + 1)\n#> 3\n'), espace)


@pytest.mark.filterwarnings("ignore:FigureCanvasAgg is non-interactive")
@pytest.mark.parametrize("page", _parametres())
def test_exemples_de_la_page(page: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MPLBACKEND", "Agg")
    if "matplotlib" in sys.modules:
        import matplotlib

        matplotlib.use("Agg")
    espace: dict[str, object] = {"__name__": "__exemples__"}
    try:
        for bloc in extraire_blocs(page):
            executer_bloc(bloc, espace)
    finally:
        if "matplotlib.pyplot" in sys.modules:
            import matplotlib.pyplot as plt

            plt.close("all")
