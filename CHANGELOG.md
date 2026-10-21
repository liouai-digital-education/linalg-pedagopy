# Changelog — `linalg_pedagopy`

## [Non publié] — branche `development`

### Refactorisation — phase 4 du plan v6 (moteur d'élimination)
- 4.1 : nouveau module `algorithms/elimination.py` qui regroupe les fonctions pures communes à Gauss-Jordan et au déterminant : simplification des coefficients (`_simplify_entry`), critère et choix du pivot (`_pivot_complexity_key`, nouvelle fonction `_choose_pivot`), mise en forme des résultats d'une branche (`_result_entry`, `_factor_with_radicals`). `gauss_jordan.py`, `determinant.py`, `gram_schmidt.py`, `qr.py`, `triangular.py` et `least_squares.py` les importent de là. Aucune sortie modifiée.
- 4.2 : opérations élémentaires tracées regroupées dans `RowOps` (`algorithms/elimination.py`) : échange, dilatation, transvection et étape de Bareiss, avec le préfixe des clés de trace (`gj`, `det`), le nom de l'instantané et l'écriture des transvections propres à chaque procédure. Gauss-Jordan et le déterminant n'enregistrent plus eux-mêmes ces opérations. Traces identiques ; six cas de déterminant ajoutés aux tests de caractérisation.

### Corrections — traces de Gauss-Jordan
- Transvections (`gj.row_add`) : un multiplicateur somme est parenthésé et le signe est le « − » typographique, en texte, LaTeX, Markdown et HTML. La trace affichait « L2 ← L2 - a − 1·L1 », qui change le sens de l'opération, au lieu de « L2 ← L2 − (a − 1)·L1 ».
- Système incompatible (`gj.inconsistent`, `EmptySolution._repr_markdown_`) : la parenthèse « (témoin : 0 = 1) », ajoutée même quand la ligne donne 0 = 2 ou 0 = 2 − a, est retirée ; le message annonce seulement « la ligne L3 donne 0 = 2 ».
- Références de caractérisation régénérées ; exemple du guide 05 mis à jour.

## [0.3.1.1] — 2026-10-21

Numéro de version : `0.3.1.1` (étiquette `v0.3.1.1`), au lieu de `3.1.1` prévu par le plan v6. Le préfixe « v » est réservé à l'étiquette git : la norme PEP 440 le retire de la version du paquet. Attention, `0.3.1.1` est inférieur, pour pip, aux versions déjà étiquetées `3.0.1` et `3.1.0`.

Phase 3 du plan v6 : correctifs issus des campagnes de tests du bac à sable (factorisation cohérente avec la condition, réduction par la condition de la branche, facteurs de signe constant à plusieurs paramètres, messages de plafond, avertissement de taille).

### Nouveautés — étape 3.5 du plan v6
- **Avertissement didactique de taille** : Gauss-Jordan sur une matrice à paramètres de taille supérieure à `config.max_generic_dim` (4 par défaut) émet un `PedagogicalWarning` (nouvelle classe, sous-classe de `UserWarning`), une fois par calcul, qui invite à chercher une structure remarquable. Le calcul est toujours mené à terme ; `config.max_generic_dim = None` supprime l'avertissement. Concerne aussi `Matrix.rref()`, `rank()`, `nullspace()`, `inv()` et `solve()`, qui s'appuient sur Gauss-Jordan.
- Les références des campagnes enregistrent les avertissements émis : 7 cas de taille 5 ou 6 en portent un (`t4_*`), sans autre changement. Tests dans `tests/test_avertissement_taille.py` ; guide 03 (§ 2.1), référence de l'API.

### Corrections — étape 3.4 du plan v6
- **Messages de plafond didactiques** : nouvelle exception `CaseLimitError` (sous-classe de `PedagopyError`, donc compatible avec le code qui attrapait cette dernière) levée quand `max_cases` ou `max_depth` arrête une discussion par cas, dans Gauss-Jordan comme dans `decide_all_zero`. Le message nomme les facteurs qui ouvrent des cas, la branche en cours, propose une hypothèse prête à l'emploi (`assumptions="a != 1"`) et un plafond plus élevé (`max_cases=16, ou config.max_cases = 16`) ; mêmes informations en attributs (`limit`, `value`, `reached`, `factors`, `condition`, `suggested_assumption`). Remplace « Nombre maximal de branches dépassé (max_cases=8). Fournissez des hypothèses… ».
- Références régénérées et relues : `t2_blocs_4x4_inverse`, `t2_circulante_3_parametres_inverse`, `t4_bloc_triangulaire_6x6` (message d'erreur seul). Tests dans `tests/test_plafonds.py` ; guide 03 (§ 2.1).

### Corrections — étape 3.3 du plan v6
- **Oracle : facteurs de signe constant à plusieurs paramètres.** Un polynôme de degré 2 en plusieurs paramètres réels est écrit, en complétant les carrés, comme une somme de carrés et d'une constante ; si la constante est strictement positive, il ne s'annule jamais sur ℝ et n'ouvre plus de branche impossible (`a² + a·b + b² + 1 = (a + b/2)² + 3/4·b² + 1 > 0`). Il est aussi écarté des valeurs interdites des dénominateurs. Étape de trace de niveau 3 (`zero.sign_definite`) avec la décomposition. Nouvelles fonctions `sum_of_squares` et `strict_sign` dans `core.zero`. Auparavant, seules les sommes de carrés déjà explicites (`a² + b² + 1`) étaient reconnues.
- Aucune référence modifiée ; la permutée cyclique 5 × 5 (`t4_permutee_cyclique_5x5`) reste sans branche parasite. Tests dans `tests/test_signe_constant.py` ; guide 01 (§ 3.4).

### Corrections — étape 3.2 du plan v6
- **Factorisation cohérente avec la condition** : nouvelle option `config.factor_policy`, `"real_radicals"` par défaut. Quand la condition d'une branche s'affiche avec des radicaux (« a ≠ √2 et a ≠ −√2 »), la solution, l'inverse et la base du noyau sont factorisés avec ces mêmes radicaux : `(a − 2)/((a − 1)·(a − √2)·(a + √2))` au lieu de `(a − 2)/((a − 1)·(a² − 2))`. Seuls les facteurs irréductibles sur ℚ sont décomposés ; `"rational"` rétablit l'ancienne écriture. Nouvelle méthode `Condition.radicals()`.
- **Réduction par la condition de la branche** : dans une branche définie par une égalité non linéaire en un paramètre (a² − 3 = 0), les coefficients de la forme réduite sont remplacés par leur reste dans la division par ce polynôme, avec une étape de trace de niveau 2 (`gj.reduce_by_condition`). Le témoin d'incompatibilité de la tridiagonale 5 × 5 s'écrit `0 = 2` au lieu de `0 = a⁴ − 3a² + 2`. Nouvelles méthodes `Condition.reduce()` et `Condition.nonlinear_equations()`.
- Références régénérées et relues : `t3_5_pivot_quadratique`, `t2_asymetrie_factorisation_inverse`, `t4_tridiagonale_5x5` (seules sorties modifiées). Tests dans `tests/test_factorisation.py`. Documentation : guide 03 (§ 2.4), référence de l'API (§ 8).

### Tests — étape 3.1 du plan v6
- Campagnes du bac à sable figées en tests de caractérisation : 21 cas reconstruits d'après le rapport d'évaluation des carnets `tests2` à `test4` (tests limites, grosses matrices pleines et creuses, plafonds de branches) dans `tests/campagnes.py`, références dans `tests/references/campagnes/`, constats et reconstitution dans `docs/dev/campagnes.md`.
- Marque pytest `lent` pour les cas de plus de 5 s, écartés par `pytest -m "not lent"` et `verifier_tout.py --rapide`.
- `scripts/mesurer_performances.py` : temps, nombre de branches et taille des expressions de chaque cas ; mesures de référence de la version 3.1.0 dans `docs/dev/mesures/campagnes_3.1.0.json`.

### Documentation développeur
- Plan de développement v6 (`docs/dev/plans/plan_developpement_v6.md`), qui remplace le plan v5 à partir de 3.1.0 : correctifs issus des campagnes de tests du bac à sable (0.3.1.1), moteur d'élimination avec noyau tracé et fusion des branches, bases et sous-espaces avant les valeurs propres (0.3.2.0), valeurs propres (0.3.3.0), familles de matrices structurées (0.3.4.0). Relecture critique du rapport d'évaluation des carnets et du référentiel bases et noyau, dont les erreurs relevées.

## [3.1.0] — 2026-10-21

Phase 2 du plan v5 : déterminant exact tracé, thème « Déterminants » du tuteur, annonce des cas singuliers dans `Matrix.inv()`.

### Nouveautés — phase 2 du plan v5 (déterminant)
- **Déterminant exact tracé** : `Determinant(A, method=...)` et `Matrix.det()`. Méthodes `bareiss` (défaut avec paramètres : divisions exactes, aucune discussion de cas), `elimination` (sans dilatation ; arrêt expliqué sur un pivot conditionnel), `cofactors` (n ≤ 4, ligne ou colonne la plus creuse) et `sarrus` (n = 3). `DetResult` : valeur factorisée, facteurs, `zeros()` (valeurs singulières du paramètre), `zeros(split=True)` (inversible / non inversible), `verify()` (contrôle par l'algorithme de Berkowitz). Messages de trace en français.
- Documentation : section 7 du guide 03, § 4.4 du guide 02, référence de l'API (§ 4.6), tutoriel (§ 5.5), README.
- **Tuteur : thème « Déterminants »** (exercices 36 à 39, originaux) : règle de Sarrus, matrice triangulaire par blocs, valeurs d'un paramètre rendant une matrice singulière, effet des opérations élémentaires ; chacun avec trois paliers d'indices, un exercice jumeau résolu (générateurs `determinant_sarrus`, `determinant_blocs`, `parametre_singulier`, `determinant_operations`) et le diagnostic de ses erreurs typiques.
- Vérificateur `valeur` : liste facultative `erreurs` d'erreurs typiques propres à une fiche (`valeur`, `diagnostic`), contrôlée par la validation (aucune ne doit coïncider avec la bonne réponse).
- Nouveau vérificateur `ensemble_valeurs` (`verify_value_set`, alias `verifier_ensemble_valeurs`) : valeurs d'un paramètre qui annulent une expression, comparées aux racines réelles ; diagnostics pour une valeur qui ne convient pas, des valeurs manquantes, une liste vide ou une expression donnée à la place des valeurs.
- Catalogue : 39 exercices en 9 thèmes ; `docs/generer_catalogue.py` compte exercices et thèmes au lieu de les écrire en dur.
- `Matrix.inv()` avec paramètres et `strict=True` : le message de `SingularMatrixError` annonce le déterminant et les valeurs qui rendent la matrice singulière (« det A = -(a - 1)*(a + 1) s'annule pour a = 1 ou a = −1 »), ou un déterminant identiquement nul, au lieu de « La matrice 2x2 est singulière (rang 1 < 2) », qui laissait croire la matrice singulière pour toute valeur.
- Cahier d'exercices, exercice 16 : le dernier indice invite à calculer et factoriser $\det A(a)$ au lieu d'en donner la valeur ; le corrigé utilise `A.det()` et `Determinant(A).run().zeros()`. Les générateurs de carnets (tutoriel, cahier) calculent les identifiants de cellule à partir du contenu : régénération reproductible.

### Corrections
- Site de documentation : 54 formules s'affichaient comme `ACADEMIC_TOKEN_n` (pages, sommaires « Sur cette page », index de recherche). Les jetons de protection `__…__` étaient mis en gras par Markdown et n'étaient plus restitués ; ils sont remplacés par des jetons alphanumériques (`AcadTok6Z`), retirés des ancres de titres, et la génération échoue s'il en reste. Nouveau test `tests/test_site_documentation.py`.

## [3.0.1] — 2026-10-21

Première version publique : fin de la phase 1 du plan v5 (corrections relevées par les tests de caractérisation, préparation et publication du dépôt). Dépôt : https://github.com/liouai-digital-education/linalg-pedagopy ; documentation : https://liouai-digital-education.github.io/linalg-pedagopy/.

### Phase 1 du plan v5 — corrections
- Oracle de nullité : les valeurs interdites par les dénominateurs sont relevées **avant** toute simplification et rendues dans le nouveau champ `ZeroDecision.domain` (pour `(a**2 - 1)/(a - 1)` : domaine `a ≠ 1`, au lieu de perdre la valeur interdite). Le verdict est décidé sur ce domaine ; sous une hypothèse qui annule un dénominateur, l'oracle répond `UNKNOWN` avec la méthode `undefined`.
- Gauss-Jordan (et donc `rref`, `rank`, `nullspace`, `inv`, `solve`) tient compte du domaine de définition des coefficients : les valeurs interdites par leurs dénominateurs restreignent toutes les branches (pour `[[(a²−1)/(a−1), 1], [1, 1]]`, la branche générique devient « a ≠ 1 et a ≠ 0 »), la trace l'annonce (`gj.domain`), et des hypothèses incompatibles lèvent une `PedagopyError` explicite. Nouvelle fonction `domain_of` dans `core.zero`.
- Oracle : la condition d'annulation d'un verdict conditionnel est complète. Le nouveau champ `ZeroDecision.cases` donne une alternative par facteur, et `format_cases()` l'affiche (`a*b` : « a = 0 ou b = 0 ») ; `condition` reste la première alternative. Le vérificateur d'opérations élémentaires affiche la condition complète.
- `Vector.is_zero()` et `Matrix.has_orthonormal_columns()` discutent désormais des cas disjoints et exhaustifs (nouvelle fonction `decide_all_zero`). Auparavant, `Vector([a*b, 0]).is_zero()` répondait faux en a = 1, b = 0, et `Vector([a, b - 1]).is_zero()` ne couvrait pas a = 0, b = 2.
- `explain(level=0)` affiche enfin le **résultat seul** (rang, solution, inverse…), en texte, LaTeX, Markdown et HTML, au lieu d'un texte vide ; c'est le résumé déjà utilisé pour les branches d'une discussion par cas. Tableau des niveaux du guide 03 corrigé.
- Tuteur : une réponse illisible n'affiche plus le message brut de SymPy ou de Python (en anglais, variable selon la version), mais une raison en français (formule sur plusieurs lignes ou matrice affichée, signe « = », parenthèses déséquilibrées, multiplication sans `*`, nom inconnu, syntaxe invalide) : vérificateur de formule, chaînes d'égalités et panneau JupyterLab (`raison_illisible`). Une matrice ou un vecteur donné à un exercice de formule reçoit le message de forme attendue, avec les variables de l'exercice.
- mypy : attributs de `Matrix` et `Vector` (classes à `__slots__`) annotés, quelques retours `Any` explicités. `mypy --strict` ne signale plus aucune erreur sur `core`, `algorithms`, `objects`, `render`, `trace`, `plot`, `config.py` et `special.py` (périmètre `files` de `[tool.mypy]`), désormais **bloquant** dans la CI et `verifier_tout.py` ; sur tout le paquet, 71 erreurs au lieu de 212 (tuteur, exercices, `compare`), vérifiées à titre informatif.

### Phase 1 du plan v5 — préparation de la publication
- Manuel « Algèbre linéaire et géométrie vectorielle » (PDF de 28 Mo, ouvrage protégé) retiré de **tout l'historique** git avant la première publication : les empreintes de tous les commits ont changé ; dépôt de 26 Mo ramené à 1,5 Mo. Le fichier reste disponible localement, ignoré par git (`.gitignore` : ce fichier, dossier `ressources/`, vidages `*.stackdump`).
- Section **Sources et remerciements** dans le `README.md` et l'accueil de la documentation : les 35 exercices du tuteur sont adaptés du recueil *Additional Exercises for Vectors, Matrices, and Least Squares* (Boyd et Vandenberghe) ; droits des auteurs rappelés ; la licence MIT ne porte que sur le code et les textes propres au projet. Les fiches elles-mêmes ne citent toujours pas leur source (pour ne pas orienter vers les solutions).
- Site HTML régénéré : il rattrape aussi Python 3.10 minimum (guide JupyterLab) et la description du niveau 0 (guide 03).
- Racine du dépôt rangée : scripts de génération dans `scripts/` (ancrés sur la racine du dépôt, utilisables depuis n'importe quel dossier), carnets dans `carnets/` (ils trouvent `src/` depuis leur dossier ou la racine), plans dans `docs/dev/plans/`. Chemins mis à jour dans le README, le tutoriel, le guide JupyterLab, `tests/run_notebooks.py` ; ruff vérifie aussi `scripts/` (imports inutilisés supprimés).
- Carnets d'essai `essai1` à `essai4` sortis du dépôt (conservés localement dans `archives/`, ignoré) ; `essai1` et `essai2`, qui contenaient un énoncé du recueil en clair, retirés de **tout l'historique** : les empreintes de tous les commits ont de nouveau changé.
- Carnets versionnés **sans sorties** : `scripts/nettoyer_carnets.py` (sans dépendance ; modes `--verifier` et `--filtre`), filtre git facultatif `carnets` déclaré dans `.gitattributes`, test `tests/test_carnets_propres.py`. Les 6 carnets suivis sont nettoyés : seules leurs sorties, souvent issues d'exécutions partielles, sont retirées.
- Métadonnées du paquet : statut **Beta** (au lieu de « Production/Stable ») tant que l'API du tuteur évolue, classificateurs « Natural Language :: French » et « Topic :: Education ». Les URL du dépôt et de la documentation viendront avec la publication.
- Publication préparée : URL du dépôt `liouai-digital-education/linalg-pedagopy` et de la documentation (GitHub Pages) dans `[project.urls]`, badges du README ; workflow `documentation.yml` qui publie `docs/site/` ; les liens du site vers le code source visent GitHub quand l'URL « Source » est connue ; chemins locaux retirés de l'ancien plan d'implémentation ; branche `master` renommée `main`.
- Dépôt public `liouai-digital-education/linalg-pedagopy` : historique publié avec l'adresse e-mail du projet, CI verte sur `main` et `development` (Python 3.10 à 3.13), documentation en ligne ; relance manuelle possible du workflow Tests. Version lue dans `pyproject.toml` par le site ; test de cohérence avec `__version__`.

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
