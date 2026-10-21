# Contribuer à `linalg_pedagopy`

Ce guide réunit les règles du projet. Le détail est dans [`docs/dev/`](docs/dev/) : [architecture du paquet](docs/dev/architecture.md) (couches, registres, moteur d'élimination) et [tests et vérifications](docs/dev/tests_et_verifications.md).

## Langue

Tout est en français : code (noms publics du tuteur, messages, traces), docstrings, documentation, messages de commit et descriptions de PR. Le reste du package garde ses noms anglais, avec des alias français durables.

## Installation pour contribuer

```bash
pip install -e ".[dev,docs,tuteur,plot,compare]"
git config filter.carnets.clean "python scripts/nettoyer_carnets.py --filtre"   # carnets commités sans sorties
git config filter.carnets.smudge cat
```

## Branches, PR et versions

- Une branche par lot de travail, partie de `development` à jour ; la PR vise `development`.
- `main` n'avance qu'avec l'accord du mainteneur, par fusion de `development`.
- Versions numérotées `0.3.x.y`, étiquettes `v0.3.x.y`. Le paquet n'est pas publié sur PyPI.
- Chaque PR a sa ligne dans la section « Non publié » du [`CHANGELOG.md`](CHANGELOG.md).

## Commits

Format `type(portée): résumé`, avec un corps qui explique **pourquoi** :

```
fix(gauss-jordan): Matrix.solve(I) renvoie la solution au lieu de None

Avec un second membre égal à I_n, GaussJordan activait d'office le mode
« inverse »… (cause, correction, ce qui ne change pas)
```

Types courants : `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `build`, `chore`.

## Avant chaque commit

```bash
python verifier_tout.py --rapide        # tests (sans les cas « lent ») et fiches
ruff check src tests scripts
python tests/run_notebooks.py           # si un carnet est concerné
python scripts/build_docs_site.py       # si un .md de docs/ ou docs/dev/, le CHANGELOG ou ce fichier change
```

`python verifier_tout.py` (sans option) ajoute la couverture, mypy et les carnets ; l'intégration continue lance tout, sur Python 3.10 à 3.13.

## Références de caractérisation

Les tests de caractérisation figent des sorties complètes (traces, discussions, diagnostics du tuteur) dans `tests/references/`.

- Une **refactorisation** laisse les références identiques.
- Un **changement de sortie voulu** a son propre commit : régénérez avec `LP_MAJ_REFERENCES=1 pytest`, relisez `git diff tests/references`, et résumez ce diff dans le message de commit.

## Documentation

- Les blocs ```` ```python ```` du README, de l'accueil, des guides et du tutoriel sont **exécutés** par les tests. Après un `print(...)`, une ligne `#> texte` est une sortie exacte, comparée ; `# texte` est un commentaire libre. Convention complète : [tests et vérifications](docs/dev/tests_et_verifications.md#exemples-de-la-documentation).
- Trois fichiers sont **générés puis versionnés** ; régénérez-les et commitez-les avec leur source :

  ```bash
  python docs/generer_catalogue.py              # docs/08_catalogue_exercices.md, depuis les fiches
  python scripts/build_docs_site.py             # docs/site/, depuis docs/*.md, docs/dev/, CHANGELOG et CONTRIBUTING
  python scripts/convert_tutorial_to_ipynb.py   # carnets/tutoriel_linalg_pedagopy.ipynb, depuis TUTORIAL.md
  ```

  Le job « Documentation à jour » de la CI échoue s'ils ne correspondent pas à leurs sources.
- Le titre d'un guide est son H1, repris tel quel par le README, l'accueil et le site ; les liens relatifs doivent viser des fichiers existants. Des tests le vérifient.

## Tuteur

- L'API d'usage est française : `linalg_pedagopy.tuteur`. `linalg_pedagopy.tutor` réexporte les noms anglais (sans avertissement en 0.3.1.2, avec un `DeprecationWarning` en 0.3.2.0, supprimé en 0.4.0.0). Dans `tutor/__init__.py`, les sous-modules de compatibilité se chargent **avant** `from tuteur import *`, sinon `tutor.catalog()` est masqué par le module.
- **Lecture de texte** : jamais d'`eval`, d'`exec` ni de `sympify` sur une chaîne dans `tuteur/`, `tutor/` ou `exercises/`. Passez par `tuteur/evaluation_sure.py` (`evaluer`, `expression`, `en_expression`, `lire_donnee`) ; un test le vérifie.
- Une nouvelle fiche doit passer `tuteur.valider_fiche(id)` (aucune fuite de la cible dans les indices, contrôle croisé avec le solveur).
- Les exemples du tuteur écrivent leur journal, `.linalg_pedagopy_journal.json`, dans le répertoire courant ; ce fichier est ignoré par git.

## Où placer un nouveau code

Une couche n'importe jamais une couche plus haute (configuration → noyau → trace → objets → rendu → algorithmes → usages). Une nouvelle procédure tracée hérite de `Procedure` et renvoie un `Result` ; une nouvelle clé de trace va dans `render/locales/fr.yaml`. Voir [l'architecture](docs/dev/architecture.md).
