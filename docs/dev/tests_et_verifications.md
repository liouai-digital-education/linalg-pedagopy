# Tests et vérifications

Guide pour les contributeurs : comment vérifier qu'une modification ne casse rien.

## En une commande

```bash
pip install -e ".[dev,plot,compare]"
python verifier_tout.py              # tests (+ couverture), fiches, ruff, mypy, carnets
python verifier_tout.py --rapide     # tests (sans les cas marqués « lent ») et fiches seulement
```

L'intégration continue (`.github/workflows/tests.yml`) exécute les mêmes étapes sur Python 3.10 à 3.13 à chaque envoi sur `main` ou `development`, une fois le dépôt publié sur GitHub.

## Les familles de tests

| Fichiers | Rôle |
|:---|:---|
| `tests/test_*.py` (hors caractérisation) | Tests unitaires : propriétés mathématiques, API, cas limites. |
| `tests/test_caracterisation_algorithmes.py` | Fige les traces (`explain` niveaux 0 à 3, Markdown, LaTeX, HTML), les discussions de cas et les décisions de l'oracle pour une trentaine de calculs représentatifs. |
| `tests/test_caracterisation_tuteur.py` | Fige, pour chacune des 39 fiches, l'énoncé, les paliers d'indices, le jumeau, les diagnostics de réponses fausses génériques et la fiche enseignant ; ainsi que le laboratoire, le catalogue, le glossaire et les 24 générateurs de jumeaux. |
| `tests/test_caracterisation_campagnes.py` | Fige les 21 cas des campagnes du bac à sable (`tests/campagnes.py`) : tests limites, grosses matrices pleines et creuses, plafonds de branches ; voir [campagnes.md](campagnes.md). Les 5 cas de plus de 5 s portent la marque `lent`. |
| `tests/test_exemples_documentation.py` | Exécute les blocs ```` ```python ```` du README, de l'accueil, des guides `docs/0*.md` (hors 07 et 08) et du tutoriel, et compare les sorties marquées `#>` (voir [Exemples de la documentation](#exemples-de-la-documentation)). |
| `tests/run_notebooks.py` | Exécute les carnets maintenus (tutoriel, problèmes, projet, cahier d'exercices et corrigé). |

## Tests de caractérisation : mode d'emploi

Un test de caractérisation compare une sortie complète au fichier `tests/references/<nom>.txt`, au caractère près. Il ne dit pas ce qui est juste : il signale **tout changement**.

- **Refactorisation** (phases 1 à 3) : les références ne doivent pas bouger. Un échec affiche le diff entre la référence et la sortie obtenue.
- **Changement voulu** (nouveau message, correction de trace) : régénérez puis relisez le diff git avant de commiter.

```bash
LP_MAJ_REFERENCES=1 pytest tests/test_caracterisation_algorithmes.py   # macOS / Linux
set LP_MAJ_REFERENCES=1 && pytest tests\test_caracterisation_tuteur.py   # Windows (cmd)
git diff tests/references                                               # relire chaque changement
```

Les références sont stables d'une exécution à l'autre (vérifié avec plusieurs valeurs de `PYTHONHASHSEED`). Elles dépendent de la version de SymPy, qui peut changer l'écriture de certaines expressions : après une mise à jour de SymPy, régénérez-les et vérifiez que seules des écritures ont changé.

Les cas longs portent la marque `lent` : `pytest -m "not lent"` (ou `python verifier_tout.py --rapide`) les écarte ; l'intégration continue les exécute tous.

Le fichier `.gitattributes` impose des fins de ligne LF pour `tests/references/`, afin que les comparaisons fonctionnent aussi sous Windows.

## Exemples de la documentation

`tests/test_exemples_documentation.py` exécute, page par page, tous les blocs ```` ```python ```` de `README.md`, `docs/index.md`, `docs/0*.md` (sauf 07 et 08) et `TUTORIAL.md`. Les blocs d'une même page partagent leurs variables, comme les cellules d'un carnet ; ils tournent dans un répertoire temporaire (le journal du tuteur y est écrit) avec `MPLBACKEND=Agg`. Une exception dans un bloc fait échouer le test de la page.

Les commentaires qui suivent un `print(...)` obéissent à une convention simple :

| Écriture | Sens |
|:---|:---|
| `# texte` | Commentaire libre (paraphrase, extrait, explication) : jamais comparé. |
| `#> texte` | Ligne de sortie **exacte**. Les lignes `#>` qui suivent immédiatement un `print(...)` sont comparées, ligne à ligne, à ce qu'il affiche ; les espaces de fin sont ignorés et `#>` seul désigne une ligne vide. |
| `#> …` (dernière ligne) | La sortie doit seulement **commencer** par les lignes `#>` qui précèdent. |
| `<!-- exemple: non exécuté -->` | Placé sur la ligne non vide qui précède un bloc : le bloc n'est pas exécuté (pseudo-code, affichage interactif). |

```python
print(P.rank())
#> Discussion selon a
#> ├─ Cas a ≠ 1 et a ≠ −1 (générique) : 2
#> └─ Cas a = 1 ou a = −1 : 1
```

N'écrivez `#>` que si la ligne est la sortie au caractère près ; un extrait, une sortie abrégée par « ... » ou une paraphrase restent en `#`. Les commentaires en fin de ligne (`print(x)  # True`) ne sont pas comparés. Une page dont l'exécution dépasse 5 s s'ajoute à `LENTES` dans le fichier de test, ce qui lui donne la marque `lent`.

## Fichiers générés de la documentation

Le catalogue des exercices (`docs/08_catalogue_exercices.md`) et le site HTML (`docs/site/`) sont générés puis versionnés. Après une modification d'une fiche du tuteur ou d'une page `.md` de `docs/`, régénérez-les, dans cet ordre (le site reprend le catalogue), et commitez le résultat :

```bash
pip install -e ".[docs]"            # markdown, jinja2, beautifulsoup4
python docs/generer_catalogue.py
python scripts/build_docs_site.py
```

Le job « Documentation à jour » de l'intégration continue refait ces deux générations et échoue si `git diff` montre un écart, ou si un fichier du site n'est pas versionné.

## Carnets

```bash
python tests/run_notebooks.py                       # moteur Jupyter si nbclient et ipykernel sont installés
python tests/run_notebooks.py --moteur simple       # sans Jupyter
python tests/run_notebooks.py exercices/vecteurs_matrices.ipynb
```

Chaque carnet est exécuté dans un dossier de travail temporaire, avec un journal du tuteur temporaire : les fichiers qu'il exporte n'atterrissent pas dans le dépôt, votre journal personnel n'est pas modifié, et les carnets eux-mêmes ne sont pas réécrits.

Les carnets sont versionnés **sans leurs sorties** : `tests/test_carnets_propres.py` le vérifie (donc la CI aussi). Pour nettoyer, sans dépendance externe :

```bash
python scripts/nettoyer_carnets.py              # nettoie les carnets de carnets/ et exercices/
python scripts/nettoyer_carnets.py --verifier   # échoue si un carnet a encore des sorties
```

Le plus simple est d'activer une fois, dans votre clone, le filtre git déclaré dans `.gitattributes` : les carnets sont alors nettoyés à chaque commit, tout en gardant leurs sorties sur votre disque.

```bash
git config filter.carnets.clean "python scripts/nettoyer_carnets.py --filtre"
git config filter.carnets.smudge cat
```

## Qualité du code

- `ruff check src tests scripts` : règles `E4`, `E7`, `E9`, `F` (bloquant).
- `mypy` (sans argument) : mode strict, **bloquant**, sur le périmètre `files` de `[tool.mypy]` dans `pyproject.toml` : `core`, `algorithms`, `objects`, `render`, `trace`, `plot`, `config.py`, `special.py`.
- `mypy src/linalg_pedagopy` : tout le paquet, informatif ; les erreurs restantes sont dans le tuteur, les exercices et `compare` (à typer en phase 5).
