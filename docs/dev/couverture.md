# Couverture des tests — état au 20 octobre 2026 (phase 0)

Ce document consigne la couverture de la suite de tests avant les refactorisations des phases 1 à 3 du plan v5, et les zones où une modification pourrait passer inaperçue.

## Méthode

La couverture « officielle » se mesure avec coverage.py :

```bash
pip install -e ".[dev]"
python -m coverage run -m pytest
python -m coverage report --sort=cover
python -m coverage html        # rapport détaillé dans htmlcov/index.html
```

Les chiffres ci-dessous ont été mesurés le 20 octobre 2026 sans coverage.py (indisponible hors ligne), avec un traceur de lignes équivalent fondé sur `sys.monitoring` (Python 3.13, SymPy 1.14). Ils sont proches de ceux de coverage.py en mode « lignes », à quelques points près : comptez-les comme des ordres de grandeur, et remplacez-les par le rapport de la CI dès qu'il est disponible.

## Résultats

« Avant » : les 71 tests existants. « Après » : avec les tests de caractérisation de la phase 0 (`tests/test_caracterisation_algorithmes.py` et `tests/test_caracterisation_tuteur.py`).

| Module | Lignes | Avant | Après | Concerné par |
|:---|---:|---:|---:|:---|
| `algorithms/gauss_jordan.py` | 550 | 87,1 % | **94,7 %** | phase 1 |
| `core/zero.py` (oracle) | 274 | 62,4 % | 68,2 % | phase 1 |
| `core/cases.py` | 328 | 87,8 % | 87,8 % | phase 1 |
| `objects/matrix.py` | 597 | 83,8 % | 86,3 % | phase 2 |
| `algorithms/gram_schmidt.py` | 320 | 78,1 % | 91,2 % | — |
| `algorithms/least_squares.py` | 236 | 75,0 % | 81,8 % | — |
| `algorithms/qr.py` | 156 | 78,2 % | 85,9 % | — |
| `algorithms/triangular.py` | 182 | 79,1 % | 79,1 % | — |
| `exercises/checkers.py` | 259 | 64,5 % | **90,7 %** | phase 1 (sessions) |
| `exercises/interactive.py` | 136 | 64,0 % | 86,0 % | phase 1 (sessions) |
| `render/latex.py` | 120 | 67,5 % | 90,8 % | — |
| `render/html.py` | 73 | 68,5 % | 97,3 % | — |
| `tutor/verifiers.py` | 824 | 72,5 % | **81,7 %** | phase 3 |
| `tutor/catalog.py` | 667 | 81,0 % | 87,3 % | phase 3 |
| `tutor/lab.py` | 184 | 78,8 % | 82,6 % | phase 3 |
| `tutor/hints.py` | 92 | 76,1 % | 76,1 % | phase 3 |
| `tutor/lock.py` | 209 | 66,0 % | 66,0 % | phase 3 |
| `tutor/panel.py` | 82 | 24,4 % | 24,4 % | phase 3 |
| `plot/geometry.py` | 146 | 0 % | 0 % | — |
| **Total** | **7 949** | **78,7 %** | **84,3 %** | |

La suite compte désormais **145 tests** (71 tests unitaires + 74 tests de caractérisation, dont un par fiche du tuteur).

## Zones faibles et décisions

| Zone | Constat | Décision |
|:---|:---|:---|
| `core/zero.py` (68 %) | Les branches non couvertes sont surtout l'analyse des hypothèses données sous forme de chaînes ou de dictionnaires, et les étapes « polynôme minimal », « simplification » et « contrôle numérique » de l'oracle. Le moteur d'élimination de la phase 1 appelle l'oracle mais ne le modifie pas. | Suffisant pour la phase 1 ; à compléter en même temps que la phase 4 (le déterminant sollicitera davantage l'oracle). |
| `tutor/lock.py` (66 %) | Les méthodes d'accès des proxys verrouillés après déverrouillage sont peu testées. | À compléter **avant** la phase 3 (tests de déverrouillage : `ex.data.x.rms()` après une réponse juste, matrice et espace de noms). |
| `tutor/hints.py` (76 %) | Les délais et nombres minimaux de tentatives (`hint_min_attempts`, `hint_min_delay_seconds`) ne sont pas testés. | À compléter avant la phase 3. |
| `tutor/panel.py` (24 %) | Le panneau exige ipywidgets ; seule la version de repli est testée. | Tester avec des widgets simulés lors de la phase 3. |
| `plot/geometry.py` (0 %) | Aucune figure n'est testée. | Hors du périmètre des refactorisations ; ajouter un test « la figure se construit » avec le moteur Agg de Matplotlib plus tard. |
| Alias `tuteur/*.py` (0 %) | Modules de réexportation jamais importés par les tests. | Un test d'import suffira en phase 3, quand ces alias seront revus. |

## Comportements relevés pendant la caractérisation

Les tests de caractérisation figent le comportement **actuel**, y compris ces particularités, qui ne sont pas corrigées pendant la phase 0 :

1. ~~`explain(level=0)` renvoie un texte vide, alors que la documentation présente le niveau 0 comme « résultat seul ».~~ Corrigé (tâche 1.3 du plan v5) : le niveau 0 affiche le résumé du résultat.
2. ~~Pour `a*b`, l'oracle renvoie bien les deux facteurs (`a`, `b`), mais sa `condition` ne mentionne que `a = 0`.~~ Corrigé (tâche 1.2 du plan v5) : `ZeroDecision.cases` donne la disjonction complète ; `Vector.is_zero` et `has_orthonormal_columns`, qui en dépendaient, discutent maintenant des cas disjoints et exhaustifs.
3. ~~Pour `(a**2 - 1)/(a - 1)`, l'oracle simplifie d'abord et ne retient que le facteur `a + 1` (la valeur interdite `a = 1` n'apparaît pas).~~ Corrigé (tâche 1.1 du plan v5) : la valeur interdite figure dans `ZeroDecision.domain`.
4. ~~Quand une réponse de formule ne peut pas être lue (par exemple une matrice affichée en caractères graphiques), le diagnostic du tuteur recopie le message brut de SymPy et de Python (« Sympify of expression … SyntaxError: … »). Ce texte, en anglais, change d'une version de Python à l'autre (3.10 et 3.13 diffèrent) : le test de caractérisation le remplace par `<message d'erreur de SymPy>` et ne fige que la phrase d'aide. À remplacer par un message en français propre au tuteur.~~ Corrigé (tâche 1.4 du plan v5) : diagnostic en français (`raison_illisible`), indépendant de la version de Python ; le test de caractérisation ne masque plus rien.
5. `mypy --strict` signale environ 215 erreurs, dont 161 `attr-defined` dues aux classes immuables à `__slots__` (attributs posés par `object.__setattr__`). L'étape mypy reste donc informative.

Chaque correction future de ces points se fera par un commit dédié, en régénérant les références concernées (`LP_MAJ_REFERENCES=1`) et en relisant le diff.
