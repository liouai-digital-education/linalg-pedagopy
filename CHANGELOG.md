# Changelog — `linalg_pedagopy`

## [Non publié] — branche `development`

### Phase 0 du plan v5 — filet de sécurité
- Python **3.10** minimum (`requires-python`, ruff, mypy, classificateurs).
- Tests de caractérisation : traces, discussions de cas et oracle (`tests/test_caracterisation_algorithmes.py`), énoncés, indices, jumeaux et diagnostics des 35 fiches (`tests/test_caracterisation_tuteur.py`), références dans `tests/references/` (régénération : `LP_MAJ_REFERENCES=1`).
- `tests/run_notebooks.py` : exécution des carnets maintenus (moteur Jupyter ou simple), journal du tuteur temporaire.
- `verifier_tout.py` et intégration continue GitHub Actions (`.github/workflows/tests.yml`) : tests et couverture sur Python 3.10 à 3.13, fiches, ruff, mypy (informatif), carnets.
- Configuration ruff (`E4`, `E7`, `E9`, `F`) et mypy (bibliothèques sans types ignorées) ; dépendances de développement : `nbformat`, `nbclient`, `ipykernel` (`syrupy`, inutilisé, retiré).
- Corrections de lint sans effet sur le comportement (imports inutilisés, annotation `Mapping` manquante, variable inutilisée).
- Documentation développeur : `docs/dev/tests_et_verifications.md`, `docs/dev/couverture.md`.

### Tuteur et exercices
- Les 35 exercices ont désormais un **identifiant lisible**, un **titre**, un **thème** (8 thèmes), un **niveau** (★ à ★★★) et un **numéro** ; plus aucune référence à un ouvrage ou recueil externe (fiches renommées `<identifiant>.yaml`, champs `page`, `source`, `ecart` supprimés).
- `tutor.catalog()` / `catalogue()` (tableau Markdown dans JupyterLab), `tutor.themes()`, `tutor.list_exercises(theme)`, `tutor.reload_catalog()`.
- `tutor.exercise()` accepte un identifiant, un numéro ou un titre ; `UnknownExerciseError` avec suggestion en cas de faute de frappe.
- Énoncé avec titre, thème, type et niveau ; `ex.title`, `ex.number`, `ex.theme`, `ex.level`.
- `ex.hint()` explique quand tous les paliers sont débloqués (au lieu d'un message de « niveau 5 ») ; nouvelle méthode `ex.reset()` / `ex.recommencer()`.
- `ex.verify()` ne lève plus d'exception sur une réponse mal formée : il indique la forme attendue. La réponse `None` n'est plus acceptée comme « invalide ».
- Bilan en Markdown (`ex.summary()`), panneau JupyterLab refait (énoncé rendu en LaTeX, relecture d'un palier, zone de réponse et bouton Vérifier).
- 9 nouveaux exercices jumeaux, adaptés au sujet de chaque fiche (matrice décrite par son effet, adjacence, puissance de matrice, mise à l'échelle diagonale, inverse d'un produit, système linéaire, produit par blocs, valeurs d'un polynôme, inégalité triangulaire) ; jumeau Gram-Schmidt détaillé.
- Glossaire étendu à 40 termes, recherche en français, liste avec `glossary()`.
- Messages sans références internes (« Principe 6 », « §7.5 », « D5 »…).

### Nouveautés
- Module `linalg_pedagopy.special` : `difference_matrix`, `running_sum_matrix`, `moving_average_matrix`, `vandermonde`, `convolution_matrix`, `convolution`, `selection_matrix`, `reversal_matrix` (avec alias français).

### Corrections
- Rendu texte des puissances (`a··2` → `a²`) et des racines (`√(1 − m²)`) ; conditions affichées en notation mathématique et factorisées (`b ≠ 1 et b ≠ −1`).
- Discussion de cas en Markdown, LaTeX et HTML : solutions rendues en LaTeX.
- `repr(CaseSplit)` concis (au lieu de la trace complète) ; `print(case_split)` affiche la discussion.
- Titre d'un exercice jumeau corrompu par une tabulation (`\text` non échappé).

### Documentation
- Documentation réécrite : nouveau guide du tuteur, catalogue des exercices (`docs/08_catalogue_exercices.md`, régénéré par `docs/generer_catalogue.py`), guide JupyterLab, matrices structurées, site HTML régénéré.
- `TUTORIAL.md` mis à jour ; le carnet tutoriel est désormais généré à partir de `TUTORIAL.md`.

### Corrections
- Fiches du tuteur : restauration des caractères accentués et des symboles perdus (`§`, `é`, `è`, `à`, `ô`, `⊥`, `≈`) dans les champs `source` et `ecart` des 35 fiches ; test de non-régression `test_fiches_source_ecart_sans_caracteres_corrompus`.
- `check_row_operation` : une opération qui écrase une ligne sans la conserver (ex. `L1 <- L2`) est désormais diagnostiquée comme `row_overwrite` (avec suggestion d'échange ou de transvection) au lieu d'être confondue avec une dilatation par 0.

### Documentation
- Correction de la documentation (`docs/*.md`, `README.md`, site HTML `docs/site/`) pour la rendre conforme à l'API réelle : exemples exécutables vérifiés, signatures et champs de résultats exacts, suppression des fonctionnalités non implémentées (QR Householder/Givens, locale anglaise, méthodes de projection, prédicats `is_*`…), liens relatifs vers le code source à la place des chemins absolus `file:///`.

## [3.0.0] — 2026-10-19

### Nouveautés majeures (Version 3.0)
- **Tuteur interactif pour VMLS (`linalg_pedagopy.tuteur`)** : accompagnement des étudiants de L1–L2 sur le recueil *Additional Exercises for Vectors, Matrices, and Least Squares* (Boyd & Vandenberghe, éd. 24 nov. 2020) sans jamais révéler la solution en mode étudiant.
- **8 principes pédagogiques du tuteur** :
  - Vérification par propriété plutôt que par corrigé figé ;
  - Diagnostic de ce que calcule la réponse de l'étudiant ;
  - Échelle d'indices gradués sur 4 niveaux (Orientation, Outil, Démarrage, Jumeau) ;
  - Exercice jumeau résolu avec trace complète au niveau 4 ;
  - Verrouillage des données d'exercice (`LockedVector`, `LockedMatrix`) jusqu'à validation ;
  - Prédiction obligatoire avant exploration au laboratoire de contre-exemples ;
  - Refus de confirmer un « toujours vrai » par de simples essais ;
  - Journal JSON local transparent et fonction `valider_fiche`.
- **Couverture du recueil VMLS** : 35 fiches d'exercices (33 exercices couverts complètement `●` + exercices `3.3` et `3.13` illustrant le laboratoire de contre-exemples), accompagnées d'un glossaire anglais–français intégré.
- **Architecture formelle complète (D1–D11)** :
  - Corps de travail $\mathbb{R}$ (`real=True`, D1) et politique de coercition des flottants (`float_policy`, D2) ;
  - Oracle de nullité à 4 verdicts (`ZERO`, `NONZERO`, `CONDITIONAL`, `UNKNOWN`, D3) et discussion par cas (`CaseSplit`, D4) ;
  - Objets `Vector` et `Matrix` immuables (D5) appuyés sur `DomainMatrix` (D10) ;
  - Traceur contextuel arborescent (`tracing`, `section`, `record`) à 4 niveaux (D6) et moteurs de rendu découplés (`text`, `latex`, `markdown`, `html`, D7) ;
  - Résultats typés (`GJResult`, `SolutionSet`, `GSResult`, `QRResult`, `LSResult`, D8) et pivot le plus simple (D11) ;
  - Modules `exercises` (générateurs exacts par matrices unimodulaires, transformée de Cayley, etc.), `compare` (exact vs flottant, matrice de Läuchli, Hilbert) et `plot` (figures 2D/3D).
