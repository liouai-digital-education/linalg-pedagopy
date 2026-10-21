# Journal des modifications — `linalg_pedagopy`

## [Non publié] — branche `development`

### Corrections
- **`Matrix.solve(Matrix.identity(n))`** renvoyait `None` : avec un second membre égal à $I_n$,
  `GaussJordan` passait en mode « inverse » et ne calculait pas la solution. Un second membre fourni
  sans `compute_inverse` donne désormais la solution (ici $X = A^{-1}$), et l'inverse en plus ;
  `compute_inverse=True` (chemin de `Matrix.inv`) est inchangé.

### Corrections — lot 1 de la revue de la documentation
- **Niveaux de trace** : `explain(level=1)` de Gauss-Jordan n'affichait aucune opération de lignes,
  rangées dans les sections de colonne de niveau 2 et retirées avec elles. Une section plus
  détaillée que le niveau demandé disparaît désormais, mais ses étapes visibles remontent
  (`Step.filter_level`). Le niveau 1 montre les opérations et les matrices, comme l'annoncent le
  guide 03, le README et l'accueil. 16 références enrichies (lignes ajoutées seulement).
- **Substitutions triangulaires** : avec un coefficient diagonal qui peut s'annuler,
  `BackSubstitution` et `ForwardSubstitution` ne renvoyaient que la branche générique (`at(a=0)`
  échouait). La discussion ajoute les branches singulières, où le résultat le signale (`singular`,
  `singular_index`) au lieu de la solution.
- **Hypothèses** : une hypothèse non reconnue (« a > 0 », « a », type inconnu) était ignorée sans
  prévenir. Nouvelle exception `InvalidAssumptionError` (`PedagopyError`, `ValueError`), avec un
  message propre aux inégalités d'ordre, non prises en compte.
- **Configuration** : `using_config` acceptait des valeurs invalides (`factor_policy="x"`,
  `default_trace_level=4`), et `max_cases`, `max_case_depth` n'étaient jamais validés. Validation
  commune aux affectations et à `using_config`.
- **Tuteur** : les messages vus par l'étudiant ne citent plus que les noms français
  (`tuteur.catalogue()`, `ex.predire`, `ex.indice`, `lab.tester`…) ; les 37 docstrings encore en
  anglais sont traduites. Fiches : énoncé de « sommes de paires » corrigé (3 sommes de paires et 3
  mesures individuelles, « matrice du modèle ») ; formule de « indépendance par Gram-Schmidt »
  rendue en LaTeX.

### Documentation — lot 1 de la revue
- Guide 02 : les quatre vues du produit matriciel (`entries`, `rows`, `columns`, `outer`) corrigées,
  avec un exemple de trace ; sorties de `print(Matrix)` remplacées par `repr` ; discussion par cas
  de `rank()` ; indices des pivots à partir de 0.
- Guide 03 : tableau des niveaux de trace d'après les sorties réelles ; formes acceptées pour
  `assumptions` ; `GJResult` ou `CaseSplit` ; conditions des substitutions et branches singulières ;
  sorties regroupées du § 7.
- Guide 01 : `is_zero` lève `UndecidableZeroError` pour les verdicts `CONDITIONAL` et `UNKNOWN`.
- Guide 06 : écart à l'orthonormalité de Gram-Schmidt classique ≈ 1/2 (et non 1) ; installation des
  options `plot` et `compare` depuis le dépôt.
- Référence de l'API (07) : noms du tuteur en français d'abord ; `Determinant(method="elimination")`
  peut renvoyer un `CaseSplit` ; hiérarchie des exceptions complétée (`InvalidAssumptionError`,
  `CaseLimitError`, `PedagogicalWarning`) ; 24 générateurs ; import de `compare`.
- Guides 04 et 05 : noms français dans le texte, bilan cohérent avec l'exemple, journal du tuteur ;
  table des 24 générateurs de jumeaux (nom français d'abord, thème Déterminants compris).
- Tutoriel : témoin de dépendance de Gram-Schmidt (`witness.a_coeffs`). README et accueil : journal
  du tuteur créé dans le répertoire courant. Site : « 39 exercices ».

### Tests — lot 2 de la revue (documentation testée)
- **Exemples exécutés** : `tests/test_exemples_documentation.py` exécute les 158 blocs Python du
  README, de l'accueil, des guides 01 à 06 et 09 et du tutoriel (état partagé par page, répertoire
  temporaire, `MPLBACKEND=Agg`) ; une exception fait échouer le test.
- **Sorties vérifiées** : convention `#>` pour une ligne de sortie exacte après un `print(...)` (`#>
  …` pour une sortie tronquée, `<!-- exemple: non exécuté -->` pour écarter un bloc), documentée
  dans `docs/dev/tests_et_verifications.md`. 23 sorties passent en `#>` ; les 11 qui omettaient la
  première ligne de trace, citaient le message entre guillemets ou l'abrégeaient sont complétées
  d'après la sortie réelle.
- **Fichiers générés** : nouveau job d'intégration continue « Documentation à jour », qui régénère
  le catalogue des exercices et le site (`docs/site/`) et échoue si le résultat diffère des fichiers
  versionnés.
- **Option `docs`** (`pip install -e ".[docs]"`) : `markdown`, `jinja2` et `beautifulsoup4`,
  nécessaires pour régénérer le site ; citée dans le README et dans
  `docs/dev/tests_et_verifications.md`.
- **mypy figé** à la version 2.4.0 dans l'option `dev`. Le périmètre strict reste sans erreur ; le
  paquet complet compte 63 erreurs (informatif, en CI comme en local, et non zéro comme on le
  pensait : l'étape échoue sans faire échouer le job). `pyproject.toml` et
  `docs/dev/tests_et_verifications.md` le disent désormais.

### Documentation — lot 3a de la revue (contenu des guides)
- **Guide 01, § 5 « Concepts transversaux »** : les quatre formes d'hypothèses (`Condition`, chaîne,
  liste, dictionnaire) et le refus des inégalités d'ordre (`InvalidAssumptionError`) ; le tableau
  des réglages de `config` (défauts, valeurs admises, validation, portée de `using_config`) ; les
  indices à partir de 0 dans l'API et à partir de 1 dans les traces. Exemples vérifiés par `#>`.
- **Guide 01 allégé** : les mentions « Décision D1/D3 » et les fonctions privées
  (`_extract_factors`, `_compute_transitive_substitutions`, `match_symbol_substitutions`) passent
  dans `docs/dev/architecture.md` (§ « Noyau formel : décisions et fonctions internes ») ; le guide
  décrit le comportement (paramètres désignés par leur nom, radicaux, clôture transitive).
- **Trace en tableau** : `explain().to_table()` est présenté dans le guide 03 (§ 1.2, exemple
  vérifié), le guide 09 (cellule JupyterLab) et le tutoriel (§ 5.1 et synthèse des commandes), avec
  renvoi au guide 06 pour le détail des colonnes.
- **Carnet du tutoriel** régénéré depuis `TUTORIAL.md` : il n'avait pas reçu les sorties `#>` du
  lot 2. Le job « Documentation à jour » le régénère désormais lui aussi et échoue sur tout écart.
  `scripts/convert_tutorial_to_ipynb.py` termine le fichier par un saut de ligne, comme
  `scripts/nettoyer_carnets.py` : sa sortie ne dépend plus du filtre git `carnets`, absent en CI.
- **Guide 02** : `Matrix.from_rows` et `Matrix.ones` ; nouveau § 2.3 sur l'accès aux coefficients
  (indexation et tranches, `row`, `col`, `columns`, `rows_as_vectors`, `augment`, `entries_grid`,
  `flat_entries`, `subs`, `to_sympy`, `to_domain_matrix`) ; nouveau § 4.4 sur `Matrix.solve`
  (ensemble des solutions, discussion par cas, `assumptions`, second membre matriciel). Le
  déterminant passe au § 4.5.
- **Guide 03** : nouveau § 1.4 sur le contrat commun des résultats (`trace`, `explain`, `verify()`
  et ce que vérifie chaque résultat) ; au § 6, `LSResult.residual`, `pseudoinverse` et
  `RankDeficientError` (cas levés, attributs `rank` et `ncols`, `QR(strict=True)`) ; « (Décision D6)
  » retiré du titre du § 1.1, la décision est citée dans `docs/dev/architecture.md`.
- **Guide 06, matrices de Hilbert** : seul l'en-tête de la sortie est comparé (`#> …`). Les erreurs
  relatives flottantes changent selon la version de NumPy et faisaient échouer les tests sous Python
  3.11 et 3.13 après la fusion du lot 2.
- **Site** : les liens entre pages avec une ancre (`page.md#section`) sont convertis en
  `page.html#section` ; ils restaient en `.md`, donc cassés.

### Documentation — lot 3b de la revue (structure et cohérence)
- **Guides renommés en français** : `01_noyau_calcul_formel.md`, `02_vecteurs_matrices.md`,
  `03_algorithmes_traces.md`, `05_exercices_sessions.md`, `06_rendu_visualisation_numerique.md`
  (`git mv`, liens mis à jour). Sur le site, les anciennes adresses
  (`01_core_and_formal_computation.html`…) deviennent des pages de redirection, ancre comprise.
- **Titres alignés, un seul H1 par page** : le H1 de chaque guide est la seule source de son titre ;
  le générateur du site le reprend (onglet, navigation, recherche) et le retire du corps, qui
  n'affiche plus deux titres de niveau 1. H1, README, accueil et site emploient les mêmes titres
  (« 01. Noyau formel et calcul exact »…) ; `tests/test_titres_documentation.py` le vérifie.
- **README et accueil dédoublonnés** : le README devient une vitrine courte (présentation,
  installation, un exemple vérifié par `#>`, liens) ; les exemples du tuteur et des moindres carrés,
  le journal et le détail des tests sont dans l'accueil, les guides et `docs/dev/`. L'installation
  (option `docs` comprise) et les remerciements, présents dans les deux, sont identiques ;
  `tests/test_readme_accueil.py` le vérifie. L'accueil s'intitule « Accueil de la documentation ».
- **`CONTRIBUTING.md`** : langue, branches et PR, format des commits, vérifications avant commit,
  références de caractérisation, convention `#>` et fichiers générés de la documentation, règles du
  tuteur (API française, lecture de texte sans `eval`), où placer un nouveau code. Cité par le
  README et par `docs/dev/tests_et_verifications.md`.
- **Documents historiques** : un bandeau signale que `docs/dev/couverture.md`,
  `docs/dev/tuteur_etat_des_lieux.md`, le plan d'implémentation v3.0 et le plan v5 ne sont plus tenus à
  jour, et renvoie au document actuel.
- **CHANGELOG** : sections « Corrections » et « Documentation » en double fusionnées dans la 3.0.1 ;
  la 3.0.0 signale qu'elle n'a pas d'étiquette git ; lignes repliées à 100 caractères (rendu inchangé).
- **Liens vérifiés** : `tests/test_liens_documentation.py` échoue si un lien relatif d'une page
  Markdown versionnée vise un fichier absent, ou si le site garde un lien `.md` vers un guide.

### Site — lot 3c de la revue
- **Recherche sans `innerHTML`** : les résultats sont construits avec `textContent`. La saisie et le
  texte indexé ne sont plus interprétés comme du HTML (un extrait « a < b » cassait l'affichage ; une
  saisie `<img onerror=…>` était injectée dans la page). Le bouton « Copier » n'utilise plus
  `innerHTML` non plus.
- **Recherche en texte intégral** : l'index contient tout le texte de chaque section (h2 ou h3),
  code compris, et l'introduction de chaque page, au lieu du titre et des 160 premiers caractères du
  paragraphe suivant (200 Ko au lieu de 80). Les titres qui correspondent passent en premier ;
  l'extrait affiché entoure le terme trouvé ; la comparaison ignore casse et accents (« determinant »
  trouve « déterminant »).
- **MathJax et Mermaid figés** : `mathjax@3.2.2` et `mermaid@10.9.8` (au lieu de `@3` et `@10`, qui
  suivaient chaque nouvelle version), avec empreinte SRI ; Mermaid est chargé en script classique
  (le module ESM ne se prête pas au SRI) et passe en `securityLevel: 'strict'`. Rendu vérifié dans le
  navigateur (formules, diagrammes, sauts de ligne des libellés).
- **Section « Développement »** : le site publie `CONTRIBUTING.md`, l'architecture, les tests et
  vérifications, les campagnes de tests et ce journal (titre désormais en français), avec un renvoi
  depuis l'accueil. Les liens relatifs sont résolus depuis le dossier de chaque page : une page publiée
  devient son `.html`, tout autre fichier du dépôt un lien GitHub (`tree` pour un dossier). Le test
  « un seul H1 » couvre toutes les pages publiées. Ces fichiers sources demandent désormais de
  régénérer le site.

## [0.3.1.2] — 2026-10-21

Phases 4, 5 et 6 du plan v6, et traces en tableau. Pas de publication sur PyPI pour cette version
(reportée à une version ultérieure).

- **Moteur d'élimination commun** (phase 4) : Gauss-Jordan et le déterminant partagent
  `EliminationEngine` et `RowOps` ; déterminant par élimination avec paramètres ; base du noyau
  expliquée dans la trace ; branches identiques regroupées à l'affichage ; stratégie de pivot
  `"sparse"` et remontée `back_substitution`.
- **`Matrix` allégée** (phase 5) : registre de procédures, logique tracée déplacée dans
  `algorithms/products.py`.
- **Traces en tableau** : `explain().to_table()` pour Gauss-Jordan, l'inverse, le déterminant,
  Gram-Schmidt, QR et les systèmes triangulaires, en HTML, Markdown et LaTeX.
- **Tuteur** (phase 6) : registre des vérificateurs, un module par vérificateur, code dans `tuteur/`
  avec des noms français.
- **Sécurité** : les `eval` et les `sympify` de chaînes du tuteur, contournables (une fiche YAML
  pouvait exécuter du code), sont remplacés par un interpréteur sûr fondé sur `ast`.

**Mise à jour** : le tuteur s'importe désormais sous `linalg_pedagopy.tuteur` (sous-modules
`catalogue`, `seance`, `verificateurs`…). `linalg_pedagopy.tutor` et ses anciens sous-modules
restent disponibles sans avertissement dans cette version ; `DeprecationWarning` en 0.3.2.0,
suppression en 0.4.0.0. Comme pour 0.3.1.1, `0.3.1.2` est inférieur, pour pip, aux versions
étiquetées `3.0.1` et `3.1.0`.

### Corrections — installation de base
- `import linalg_pedagopy` échouait sans numpy, pourtant déclaré optionnel (option `compare`) :
  `compare/numeric.py` l'importait au chargement du paquet. numpy n'est plus importé qu'à l'usage ;
  sans lui, les comparaisons numériques (`compare`, expériences de Läuchli et de Hilbert, inverse
  contre résolution) lèvent une `ImportError` qui indique `pip install "linalg_pedagopy[compare]"`.
  Vérifié sur la roue 0.3.1.2 installée dans un environnement vierge (SymPy et PyYAML seuls) ; test
  `test_import_sans_numpy`.

### Phase 6 du plan v6 — tuteur
- 6.0 : état des lieux du tuteur (`docs/dev/tuteur_etat_des_lieux.md` : modules, couverture, origine
  des douze `eval`) ; tests de caractérisation de `verrou`, `indices` et `panneau`
  (`tests/test_tuteur_verrou_indices_panneau.py`, couverture de 55–70 % à 99–100 %) ; deux tests
  `xfail(strict=True)` documentent que `{"__builtins__": {}}` ne protège pas `eval` (accès par
  `__globals__`), à corriger à l'étape 6.4. Tests du tuteur valables avec et sans ipywidgets :
  - Tests du tuteur : `test_seance_type_6_4_from_section_7_8` et
    `test_phase0_english_nomenclature_api` échouaient quand l'option `tuteur` (ipywidgets) était
    installée, car `str()` d'un vrai `VBox` ne contient pas l'énoncé. Ces deux tests vérifient
    désormais le panneau de repli en simulant l'absence d'ipywidgets ; le nouveau test
    `test_panneau_ipywidgets_affiche_enonce` (ignoré sans ipywidgets) vérifie que le panneau
    graphique affiche l'énoncé et ses boutons.
  - CI : nouveau job « Tuteur avec ipywidgets », qui exécute `pytest tests/test_tuteur.py` avec
    l'option `tuteur` installée.
- 6.1 : registre des types de vérificateurs (`tutor/registry.py` : `VerifierType`,
  `register_verifier`, `verifier_type`) à la place des trois cascades `if v_type in (...)` de
  `catalog.py` (séance, champs obligatoires, contrôle croisé) et des tables `_EXPECTED_FORMS` et
  `_VALID_VERIFIER_TYPES`. Les contrôles croisés quittent `catalog.py`, qui passe de 951 à 716
  lignes. Diagnostics et références de caractérisation inchangés. Tests dans
  `tests/test_tuteur_registre.py` ; `docs/dev/architecture.md` explique comment ajouter un type.
- 6.2 : `tutor/verifiers.py` (1 193 lignes) devient le paquet `tutor/verifiers/` : un module par
  type de vérificateur (`valeur`, `matrice`, `labo`…, 43 à 212 lignes), qui réunit la vérification,
  son contrôle croisé et l'enregistrement du type avec sa forme attendue, plus `commun.py`
  (`VerificationResult`, lecture des expressions indexées). Les noms importés de `tutor.verifiers`
  sont inchangés. Le paquet rejoindra `tuteur/verificateurs/` à l'étape 6.6.
- 6.3 : `tutor/catalog.py` découpé en `catalog.py` (fiches, thèmes, glossaire, mode ; 223 lignes),
  `session.py` (`ExerciseSession`, `TeacherSheet`, `exercise` ; 320 lignes) et `validation.py`
  (`ValidationReport`, `validate_sheet`, contrôle croisé ; 211 lignes). L'API publique (`tutor`,
  `tuteur`) est inchangée ; le contrôle croisé par vérificateur est fait depuis 6.1–6.2.
- **6.4, 6.5, 6.7 (sécurité)** : interpréteur sûr `tutor/evaluation_sure.py`, fondé sur `ast` et une
  liste blanche de constructions, à la place des douze `eval` du tuteur et des `sympify` de chaînes.
  `{"__builtins__": {}}` ne protégeait pas : `__globals__` rendait toutes les fonctions intégrées,
  et une chaîne passée à `Vector`, `Matrix` ou `sympify` était exécutée ; une fiche YAML venue d'un
  tiers pouvait donc exécuter du code. Sont refusés : noms et attributs en `_`, attributs des cadres
  d'exécution et `format`, modules, fonctions anonymes, compréhensions, `:=`, f-chaînes,
  dépaquetage, chaînes contenant « ( » ou « __ » transmises à un calcul, puissances démesurées. Le
  champ `jumeau` ne voit que les générateurs (6.5) ; les données des fiches (`[1, a]`) passent par
  `lire_donnee` ; `exercises/checkers.py` lit les opérations sur les lignes avec l'interpréteur.
  Diagnostics et références inchangés. Tests d'évasion dans `tests/test_evaluation_sure.py` (6.7),
  qui interdit aussi le retour d'`eval` ou de `sympify` ; les deux tests en échec attendu de 6.0
  passent.
- 6.6 : le code du tuteur passe de `tutor/` à `tuteur/`, sous des noms de modules français :
  `catalogue.py`, `seance.py`, `validation.py`, `indices.py`, `journal.py`, `labo.py`, `verrou.py`,
  `panneau.py`, `registre.py`, `evaluation_sure.py`, `verificateurs/`. `linalg_pedagopy.tutor` et
  ses anciens sous-modules (`tutor.catalog`, `tutor.verifiers`…) réexportent les mêmes noms, sans
  avertissement en 0.3.1.2 ; `DeprecationWarning` en 0.3.2.0, suppression en 0.4.0.0 (décision
  15.1.13). Les sous-modules de compatibilité sont chargés avant les noms, pour qu'un import tardif
  de `tutor.catalog` ne masque pas la fonction `tutor.catalog()`. La CI et `verifier_tout.py`
  valident les fiches avec `tuteur.valider_fiche`.
- 6.6 (documentation) : exemples du README, du tutoriel (et du carnet généré), des guides 04, 08, 09
  et de l'accueil en noms français (`tuteur.exercice`, `ex.indice`, `ex.verifier`,
  `rapport.valide`…) ; la table des noms du tuteur de l'accueil place le nom français en premier ;
  la référence de l'API décrit les sous-modules de `tuteur` et le calendrier de retrait des noms
  anglais.

### Nouveautés — traces en tableau
- **`explain().to_table()`** pour Gauss-Jordan et le déterminant : une ligne par opération
  élémentaire (échange, dilatation, transvection, étape de Bareiss) avec les colonnes N°, Colonne,
  Pivot, Opération, But et Matrice obtenue (pivot encadré, lignes modifiées en couleur, barre de la
  matrice augmentée) ; lignes de commentaire pour les autres étapes visibles au niveau demandé ; un
  tableau par branche d'une discussion par cas. Rendus `to_html()` (affichage automatique dans
  JupyterLab), `to_markdown()` (sans « | » dans les cellules) et `to_latex()` (`longtable`) ; option
  `standalone` pour une page HTML ou un document LaTeX complets. Nouveau module `render/table.py`
  (`TraceTable`, `build_table`) ; clés de locale `table.*`. Les algorithmes ne changent pas : le
  tableau est tiré de la trace existante.
- Extension aux autres algorithmes, avec des colonnes propres à chacun (dispositions) : inverse
  (comme Gauss-Jordan) ; **Gram-Schmidt et QR** (N°, Vecteur traité, Coefficients, Opération, But,
  Vecteur obtenu : une ligne par orthogonalisation, une par normalisation, variantes `end` et
  `each`, famille liée) ; **systèmes triangulaires** (N°, Inconnue, Calcul, But, Valeur : formule
  avec les coefficients de la ligne, puis valeurs connues). Une trace qui enchaîne plusieurs
  algorithmes donne un tableau par algorithme (moindres carrés).
- Tests dans `tests/test_tableau.py` ; références de caractérisation `tableaux` et `tableaux_autres`
  ; guide 06 (§ 1.2), référence de l'API.

### Refactorisation — phase 5 du plan v6 (alléger `Matrix`)
- 5.1 : registre unique `_procedures` (`register_procedure`, `objects/matrix.py`) à la place des
  crochets `register_gauss_jordan_hook` et `register_determinant_hook` ; procédures enregistrées :
  `gauss_jordan`, `determinant`, `matmul`, `gram`, `orthonormal_check`, `singular_check`.
- 5.2 et 5.3 : la logique tracée sort de `Matrix` vers le nouveau module `algorithms/products.py` :
  produit matriciel selon une vue (`matmul(view=…)`), matrice de Gram, contrôle d'orthonormalité des
  colonnes, annonce des valeurs singulières avant `inv()`. Les méthodes de commodité (`rref`,
  `rank`, `nullspace`, `inv`, `det`, `solve`, `gram`, `has_orthonormal_columns`) sont regroupées
  dans une section délimitée et ne font plus que quelques lignes (projection d'un `CaseSplit`
  factorisée dans `_champ`). `matrix.py` passe de 836 à 599 lignes. API et traces inchangées (clés
  `matrix.*` conservées).
- 5.4 : `docs/dev/architecture.md` : couches du paquet et dépendances permises, crochets, règle de
  délégation de `Matrix` et registre des procédures, moteur d'élimination, traces et locales.

### Nouveautés — étape 4.9 du plan v6
- **Stratégie de pivot `"sparse"`** (critère de Markowitz, la colonne étant fixée) : le pivot de la
  ligne qui a le moins de coefficients non nuls, puis le plus simple.
- **`reduction="back_substitution"`** pour `GaussJordan` : échelonnement vers le bas, puis remontée
  de la dernière colonne pivot à la première (section de trace `gj.back_substitution`), au lieu de
  l'élimination simultanée au-dessus et au-dessous de chaque pivot. Même forme réduite.
- Mesures sur six cas des campagnes (`docs/dev/campagnes.md`) : de 10 à 25 % de temps en moins avec
  la remontée sur la tridiagonale et la bloc-triangulaire, expressions intermédiaires plus petites
  avec `sparse` sur l'équicorrélation ; mêmes branches et mêmes résultats. Gains modestes : les
  réglages par défaut (`simplest`, `simultaneous`) sont conservés, aucune sortie existante ne
  change. Tests dans `tests/test_elimination.py` (dont une propriété : même forme réduite que SymPy
  pour les quatre combinaisons) ; guide 03 (§ 2.1), référence de l'API.

### Nouveautés — étape 4.8 du plan v6 (révisée)
- **Branches identiques regroupées à l'affichage** : aux niveaux 0 et 1, les branches particulières
  d'une discussion dont le résumé est identique s'affichent ensemble (« Cas a = 3, a = 2 ou a = 1 :
  système incompatible » ; « Cas a = −2 ou a = 1 : det A = 0 »), en texte, LaTeX, Markdown et HTML.
  Le `CaseSplit` n'est pas modifié (`at()`, `branches`) ; à partir du niveau 2, chaque branche garde
  sa trace. Fonctions `group_branches`, `format_conditions_text` et `format_conditions_latex`
  (`render/text.py`).
- Révision du plan : la fusion véritable des branches (conditions disjonctives) est abandonnée après
  mesure : 4 branches sur 73 dans les cas de référence, et aucune sur la bloc-triangulaire 6 × 6,
  dont les 10 résultats sont distincts. Ce plafond relève de la méthode par blocs (étape 9.3).
- 7 références régénérées et relues (regroupements seuls). Tests dans `tests/test_regroupement.py` ;
  guide 01 (§ 4.2).

### Nouveautés — étape 4.7 du plan v6 (noyau tracé)
- **Base du noyau expliquée** dans la trace de niveau 2 : variables libres et principales, théorème
  du rang (`dim ker A = n − rg A`), système homogène équivalent, chaque vecteur de base (« en posant
  x2 = 1 et les autres variables libres nulles »), puis la sous-matrice identité des composantes
  libres, qui prouve que la famille est libre. Sans variable libre, une réduction sans second membre
  annonce `ker A = {0}`, de dimension 0, et sa base vide. Affichée pour une réduction sans second
  membre (`rref()`, `rank()`, `nullspace()`) et pour une solution affine ; pas pour un système
  incompatible ni pour un calcul d'inverse.
- `kernel_basis` et `trace_kernel` dans `algorithms/elimination.py` remplacent
  `GaussJordan._extract_nullspace` ; `Matrix.nullspace()` réduit `A` seule, sans colonne de zéros.
  Clés de locale `ker.*`.
- 14 références régénérées et relues : uniquement des lignes ajoutées (étapes du noyau), aucune
  ligne modifiée ou retirée. Tests dans `tests/test_noyau.py` (dont une propriété : `A·v = 0`, `n −
  rg A` vecteurs, bloc identité) ; guide 03 (§ 2.4).

### Nouveautés — étape 4.5 du plan v6
- **Déterminant par élimination avec paramètres** : `Determinant(A, method="elimination")` ne
  s'arrête plus sur un pivot qui peut s'annuler (« Élimination interrompue… ») ; comme Gauss-Jordan,
  il ouvre une discussion par cas, avec dans chaque branche le produit des pivots ou l'arrêt sur une
  colonne sans pivot (déterminant nul). `Matrix.det(method="elimination")` renvoie alors un
  `CaseSplit` des valeurs (surcharges de type : les autres méthodes renvoient toujours une
  expression). La méthode `auto` est inchangée (Bareiss dès qu'il y a des paramètres).
- La triangulation sans dilatation du déterminant est construite sur `EliminationEngine`
  (`reduce_above=False`, `normalize_pivots=False`), avec de nouvelles options de présentation de la
  trace (`start_section`, `column_sections`, `stop_on_zero_column`, `signed_add`, `limit_arguments`)
  et le comptage des échanges. Bareiss, qui n'ouvre jamais de discussion, garde sa boucle et partage
  `RowOps`. Les traces des déterminants sont identiques, hormis les cas qui s'arrêtaient en erreur.
  Clé de trace `det.elimination_conditional` remplacée par `det.case_split`. Nouveau cas de
  caractérisation `det_elimination_parametre` ; guide 03 (§ 7.3).

### Refactorisation — phase 4 du plan v6 (moteur d'élimination)
- 4.1 : nouveau module `algorithms/elimination.py` qui regroupe les fonctions pures communes à
  Gauss-Jordan et au déterminant : simplification des coefficients (`_simplify_entry`), critère et
  choix du pivot (`_pivot_complexity_key`, nouvelle fonction `_choose_pivot`), mise en forme des
  résultats d'une branche (`_result_entry`, `_factor_with_radicals`). `gauss_jordan.py`,
  `determinant.py`, `gram_schmidt.py`, `qr.py`, `triangular.py` et `least_squares.py` les importent
  de là. Aucune sortie modifiée.
- 4.2 : opérations élémentaires tracées regroupées dans `RowOps` (`algorithms/elimination.py`) :
  échange, dilatation, transvection et étape de Bareiss, avec le préfixe des clés de trace (`gj`,
  `det`), le nom de l'instantané et l'écriture des transvections propres à chaque procédure.
  Gauss-Jordan et le déterminant n'enregistrent plus eux-mêmes ces opérations. Traces identiques ;
  six cas de déterminant ajoutés aux tests de caractérisation.
- 4.3 : `EliminationEngine` (`algorithms/elimination.py`) porte la boucle d'élimination (analyse des
  candidats par l'oracle, choix du pivot, opérations de lignes) et la discussion par cas (branche
  générique puis branches particulières, plafonds `max_cases` et `max_depth`). La procédure lui
  fournit `setup` (grille de travail sous une condition) et `on_complete` (résultat d'une branche,
  ou `SplitRequest` pour une discussion supplémentaire). Options `reduce_above` et
  `normalize_pivots` pour la triangulation sans dilatation. `GaussJordan` est réécrit dessus :
  `gauss_jordan.py` passe de 683 à 496 lignes. Traces et discussions de cas identiques ; temps des
  campagnes inchangés.
- 4.6 : tests propres au moteur (`tests/test_elimination.py`) : choix du pivot, opérations de lignes
  tracées (transvections signées et parenthésées, variante du déterminant, étape de Bareiss), forme
  réduite, triangulation sans dilatation et comptage des échanges, arrêt sur une colonne nulle,
  options de présentation, discussion par cas, `SplitRequest`, plafonds avec et sans arguments de
  procédure.

### Corrections — traces de Gauss-Jordan
- Transvections (`gj.row_add`) : un multiplicateur somme est parenthésé et le signe est le « − »
  typographique, en texte, LaTeX, Markdown et HTML. La trace affichait « L2 ← L2 - a − 1·L1 », qui
  change le sens de l'opération, au lieu de « L2 ← L2 − (a − 1)·L1 ».
- Système incompatible (`gj.inconsistent`, `EmptySolution._repr_markdown_`) : la parenthèse «
  (témoin : 0 = 1) », ajoutée même quand la ligne donne 0 = 2 ou 0 = 2 − a, est retirée ; le message
  annonce seulement « la ligne L3 donne 0 = 2 ».
- Références de caractérisation régénérées ; exemple du guide 05 mis à jour.

## [0.3.1.1] — 2026-10-21

Numéro de version : `0.3.1.1` (étiquette `v0.3.1.1`), au lieu de `3.1.1` prévu par le plan v6. Le
préfixe « v » est réservé à l'étiquette git : la norme PEP 440 le retire de la version du paquet.
Attention, `0.3.1.1` est inférieur, pour pip, aux versions déjà étiquetées `3.0.1` et `3.1.0`.

Phase 3 du plan v6 : correctifs issus des campagnes de tests du bac à sable (factorisation cohérente
avec la condition, réduction par la condition de la branche, facteurs de signe constant à plusieurs
paramètres, messages de plafond, avertissement de taille).

### Nouveautés — étape 3.5 du plan v6
- **Avertissement didactique de taille** : Gauss-Jordan sur une matrice à paramètres de taille
  supérieure à `config.max_generic_dim` (4 par défaut) émet un `PedagogicalWarning` (nouvelle
  classe, sous-classe de `UserWarning`), une fois par calcul, qui invite à chercher une structure
  remarquable. Le calcul est toujours mené à terme ; `config.max_generic_dim = None` supprime
  l'avertissement. Concerne aussi `Matrix.rref()`, `rank()`, `nullspace()`, `inv()` et `solve()`,
  qui s'appuient sur Gauss-Jordan.
- Les références des campagnes enregistrent les avertissements émis : 7 cas de taille 5 ou 6 en
  portent un (`t4_*`), sans autre changement. Tests dans `tests/test_avertissement_taille.py` ;
  guide 03 (§ 2.1), référence de l'API.

### Corrections — étape 3.4 du plan v6
- **Messages de plafond didactiques** : nouvelle exception `CaseLimitError` (sous-classe de
  `PedagopyError`, donc compatible avec le code qui attrapait cette dernière) levée quand
  `max_cases` ou `max_depth` arrête une discussion par cas, dans Gauss-Jordan comme dans
  `decide_all_zero`. Le message nomme les facteurs qui ouvrent des cas, la branche en cours, propose
  une hypothèse prête à l'emploi (`assumptions="a != 1"`) et un plafond plus élevé (`max_cases=16,
  ou config.max_cases = 16`) ; mêmes informations en attributs (`limit`, `value`, `reached`,
  `factors`, `condition`, `suggested_assumption`). Remplace « Nombre maximal de branches dépassé
  (max_cases=8). Fournissez des hypothèses… ».
- Références régénérées et relues : `t2_blocs_4x4_inverse`, `t2_circulante_3_parametres_inverse`,
  `t4_bloc_triangulaire_6x6` (message d'erreur seul). Tests dans `tests/test_plafonds.py` ; guide 03
  (§ 2.1).

### Corrections — étape 3.3 du plan v6
- **Oracle : facteurs de signe constant à plusieurs paramètres.** Un polynôme de degré 2 en
  plusieurs paramètres réels est écrit, en complétant les carrés, comme une somme de carrés et d'une
  constante ; si la constante est strictement positive, il ne s'annule jamais sur ℝ et n'ouvre plus
  de branche impossible (`a² + a·b + b² + 1 = (a + b/2)² + 3/4·b² + 1 > 0`). Il est aussi écarté des
  valeurs interdites des dénominateurs. Étape de trace de niveau 3 (`zero.sign_definite`) avec la
  décomposition. Nouvelles fonctions `sum_of_squares` et `strict_sign` dans `core.zero`. Auparavant,
  seules les sommes de carrés déjà explicites (`a² + b² + 1`) étaient reconnues.
- Aucune référence modifiée ; la permutée cyclique 5 × 5 (`t4_permutee_cyclique_5x5`) reste sans
  branche parasite. Tests dans `tests/test_signe_constant.py` ; guide 01 (§ 3.4).

### Corrections — étape 3.2 du plan v6
- **Factorisation cohérente avec la condition** : nouvelle option `config.factor_policy`,
  `"real_radicals"` par défaut. Quand la condition d'une branche s'affiche avec des radicaux (« a ≠
  √2 et a ≠ −√2 »), la solution, l'inverse et la base du noyau sont factorisés avec ces mêmes
  radicaux : `(a − 2)/((a − 1)·(a − √2)·(a + √2))` au lieu de `(a − 2)/((a − 1)·(a² − 2))`. Seuls
  les facteurs irréductibles sur ℚ sont décomposés ; `"rational"` rétablit l'ancienne écriture.
  Nouvelle méthode `Condition.radicals()`.
- **Réduction par la condition de la branche** : dans une branche définie par une égalité non
  linéaire en un paramètre (a² − 3 = 0), les coefficients de la forme réduite sont remplacés par
  leur reste dans la division par ce polynôme, avec une étape de trace de niveau 2
  (`gj.reduce_by_condition`). Le témoin d'incompatibilité de la tridiagonale 5 × 5 s'écrit `0 = 2`
  au lieu de `0 = a⁴ − 3a² + 2`. Nouvelles méthodes `Condition.reduce()` et
  `Condition.nonlinear_equations()`.
- Références régénérées et relues : `t3_5_pivot_quadratique`, `t2_asymetrie_factorisation_inverse`,
  `t4_tridiagonale_5x5` (seules sorties modifiées). Tests dans `tests/test_factorisation.py`.
  Documentation : guide 03 (§ 2.4), référence de l'API (§ 8).

### Tests — étape 3.1 du plan v6
- Campagnes du bac à sable figées en tests de caractérisation : 21 cas reconstruits d'après le
  rapport d'évaluation des carnets `tests2` à `test4` (tests limites, grosses matrices pleines et
  creuses, plafonds de branches) dans `tests/campagnes.py`, références dans
  `tests/references/campagnes/`, constats et reconstitution dans `docs/dev/campagnes.md`.
- Marque pytest `lent` pour les cas de plus de 5 s, écartés par `pytest -m "not lent"` et
  `verifier_tout.py --rapide`.
- `scripts/mesurer_performances.py` : temps, nombre de branches et taille des expressions de chaque
  cas ; mesures de référence de la version 3.1.0 dans `docs/dev/mesures/campagnes_3.1.0.json`.

### Documentation développeur
- Plan de développement v6 (`docs/dev/plans/plan_developpement_v6.md`), qui remplace le plan v5 à
  partir de 3.1.0 : correctifs issus des campagnes de tests du bac à sable (0.3.1.1), moteur
  d'élimination avec noyau tracé et fusion des branches, bases et sous-espaces avant les valeurs
  propres (0.3.2.0), valeurs propres (0.3.3.0), familles de matrices structurées (0.3.4.0).
  Relecture critique du rapport d'évaluation des carnets et du référentiel bases et noyau, dont les
  erreurs relevées.

## [3.1.0] — 2026-10-21

Phase 2 du plan v5 : déterminant exact tracé, thème « Déterminants » du tuteur, annonce des cas
singuliers dans `Matrix.inv()`.

### Nouveautés — phase 2 du plan v5 (déterminant)
- **Déterminant exact tracé** : `Determinant(A, method=...)` et `Matrix.det()`. Méthodes `bareiss`
  (défaut avec paramètres : divisions exactes, aucune discussion de cas), `elimination` (sans
  dilatation ; arrêt expliqué sur un pivot conditionnel), `cofactors` (n ≤ 4, ligne ou colonne la
  plus creuse) et `sarrus` (n = 3). `DetResult` : valeur factorisée, facteurs, `zeros()` (valeurs
  singulières du paramètre), `zeros(split=True)` (inversible / non inversible), `verify()` (contrôle
  par l'algorithme de Berkowitz). Messages de trace en français.
- Documentation : section 7 du guide 03, § 4.4 du guide 02, référence de l'API (§ 4.6), tutoriel (§
  5.5), README.
- **Tuteur : thème « Déterminants »** (exercices 36 à 39, originaux) : règle de Sarrus, matrice
  triangulaire par blocs, valeurs d'un paramètre rendant une matrice singulière, effet des
  opérations élémentaires ; chacun avec trois paliers d'indices, un exercice jumeau résolu
  (générateurs `determinant_sarrus`, `determinant_blocs`, `parametre_singulier`,
  `determinant_operations`) et le diagnostic de ses erreurs typiques.
- Vérificateur `valeur` : liste facultative `erreurs` d'erreurs typiques propres à une fiche
  (`valeur`, `diagnostic`), contrôlée par la validation (aucune ne doit coïncider avec la bonne
  réponse).
- Nouveau vérificateur `ensemble_valeurs` (`verify_value_set`, alias `verifier_ensemble_valeurs`) :
  valeurs d'un paramètre qui annulent une expression, comparées aux racines réelles ; diagnostics
  pour une valeur qui ne convient pas, des valeurs manquantes, une liste vide ou une expression
  donnée à la place des valeurs.
- Catalogue : 39 exercices en 9 thèmes ; `docs/generer_catalogue.py` compte exercices et thèmes au
  lieu de les écrire en dur.
- `Matrix.inv()` avec paramètres et `strict=True` : le message de `SingularMatrixError` annonce le
  déterminant et les valeurs qui rendent la matrice singulière (« det A = -(a - 1)*(a + 1) s'annule
  pour a = 1 ou a = −1 »), ou un déterminant identiquement nul, au lieu de « La matrice 2x2 est
  singulière (rang 1 < 2) », qui laissait croire la matrice singulière pour toute valeur.
- Cahier d'exercices, exercice 16 : le dernier indice invite à calculer et factoriser $\det A(a)$ au
  lieu d'en donner la valeur ; le corrigé utilise `A.det()` et `Determinant(A).run().zeros()`. Les
  générateurs de carnets (tutoriel, cahier) calculent les identifiants de cellule à partir du
  contenu : régénération reproductible.

### Corrections
- Site de documentation : 54 formules s'affichaient sous la forme de leur jeton de protection brut
  (pages, sommaires « Sur cette page », index de recherche). Les jetons de protection `__…__` étaient
  mis en gras par Markdown et n'étaient plus restitués ; ils sont remplacés par des jetons faits
  seulement de lettres et de chiffres, retirés des ancres de titres, et la génération échoue s'il en
  reste. Nouveau test `tests/test_site_documentation.py`.

## [3.0.1] — 2026-10-21

Première version publique : fin de la phase 1 du plan v5 (corrections relevées par les tests de
caractérisation, préparation et publication du dépôt). Dépôt :
https://github.com/liouai-digital-education/linalg-pedagopy ; documentation :
https://liouai-digital-education.github.io/linalg-pedagopy/.

### Phase 1 du plan v5 — corrections
- Oracle de nullité : les valeurs interdites par les dénominateurs sont relevées **avant** toute
  simplification et rendues dans le nouveau champ `ZeroDecision.domain` (pour `(a**2 - 1)/(a - 1)` :
  domaine `a ≠ 1`, au lieu de perdre la valeur interdite). Le verdict est décidé sur ce domaine ;
  sous une hypothèse qui annule un dénominateur, l'oracle répond `UNKNOWN` avec la méthode
  `undefined`.
- Gauss-Jordan (et donc `rref`, `rank`, `nullspace`, `inv`, `solve`) tient compte du domaine de
  définition des coefficients : les valeurs interdites par leurs dénominateurs restreignent toutes
  les branches (pour `[[(a²−1)/(a−1), 1], [1, 1]]`, la branche générique devient « a ≠ 1 et a ≠ 0
  »), la trace l'annonce (`gj.domain`), et des hypothèses incompatibles lèvent une `PedagopyError`
  explicite. Nouvelle fonction `domain_of` dans `core.zero`.
- Oracle : la condition d'annulation d'un verdict conditionnel est complète. Le nouveau champ
  `ZeroDecision.cases` donne une alternative par facteur, et `format_cases()` l'affiche (`a*b` : « a
  = 0 ou b = 0 ») ; `condition` reste la première alternative. Le vérificateur d'opérations
  élémentaires affiche la condition complète.
- `Vector.is_zero()` et `Matrix.has_orthonormal_columns()` discutent désormais des cas disjoints et
  exhaustifs (nouvelle fonction `decide_all_zero`). Auparavant, `Vector([a*b, 0]).is_zero()`
  répondait faux en a = 1, b = 0, et `Vector([a, b - 1]).is_zero()` ne couvrait pas a = 0, b = 2.
- `explain(level=0)` affiche enfin le **résultat seul** (rang, solution, inverse…), en texte, LaTeX,
  Markdown et HTML, au lieu d'un texte vide ; c'est le résumé déjà utilisé pour les branches d'une
  discussion par cas. Tableau des niveaux du guide 03 corrigé.
- Tuteur : une réponse illisible n'affiche plus le message brut de SymPy ou de Python (en anglais,
  variable selon la version), mais une raison en français (formule sur plusieurs lignes ou matrice
  affichée, signe « = », parenthèses déséquilibrées, multiplication sans `*`, nom inconnu, syntaxe
  invalide) : vérificateur de formule, chaînes d'égalités et panneau JupyterLab
  (`raison_illisible`). Une matrice ou un vecteur donné à un exercice de formule reçoit le message
  de forme attendue, avec les variables de l'exercice.
- mypy : attributs de `Matrix` et `Vector` (classes à `__slots__`) annotés, quelques retours `Any`
  explicités. `mypy --strict` ne signale plus aucune erreur sur `core`, `algorithms`, `objects`,
  `render`, `trace`, `plot`, `config.py` et `special.py` (périmètre `files` de `[tool.mypy]`),
  désormais **bloquant** dans la CI et `verifier_tout.py` ; sur tout le paquet, 71 erreurs au lieu
  de 212 (tuteur, exercices, `compare`), vérifiées à titre informatif.

### Phase 1 du plan v5 — préparation de la publication
- Manuel « Algèbre linéaire et géométrie vectorielle » (PDF de 28 Mo, ouvrage protégé) retiré de
  **tout l'historique** git avant la première publication : les empreintes de tous les commits ont
  changé ; dépôt de 26 Mo ramené à 1,5 Mo. Le fichier reste disponible localement, ignoré par git
  (`.gitignore` : ce fichier, dossier `ressources/`, vidages `*.stackdump`).
- Section **Sources et remerciements** dans le `README.md` et l'accueil de la documentation : les 35
  exercices du tuteur sont adaptés du recueil *Additional Exercises for Vectors, Matrices, and Least
  Squares* (Boyd et Vandenberghe) ; droits des auteurs rappelés ; la licence MIT ne porte que sur le
  code et les textes propres au projet. Les fiches elles-mêmes ne citent toujours pas leur source
  (pour ne pas orienter vers les solutions).
- Site HTML régénéré : il rattrape aussi Python 3.10 minimum (guide JupyterLab) et la description du
  niveau 0 (guide 03).
- Racine du dépôt rangée : scripts de génération dans `scripts/` (ancrés sur la racine du dépôt,
  utilisables depuis n'importe quel dossier), carnets dans `carnets/` (ils trouvent `src/` depuis
  leur dossier ou la racine), plans dans `docs/dev/plans/`. Chemins mis à jour dans le README, le
  tutoriel, le guide JupyterLab, `tests/run_notebooks.py` ; ruff vérifie aussi `scripts/` (imports
  inutilisés supprimés).
- Carnets d'essai `essai1` à `essai4` sortis du dépôt (conservés localement dans `archives/`,
  ignoré) ; `essai1` et `essai2`, qui contenaient un énoncé du recueil en clair, retirés de **tout
  l'historique** : les empreintes de tous les commits ont de nouveau changé.
- Carnets versionnés **sans sorties** : `scripts/nettoyer_carnets.py` (sans dépendance ; modes
  `--verifier` et `--filtre`), filtre git facultatif `carnets` déclaré dans `.gitattributes`, test
  `tests/test_carnets_propres.py`. Les 6 carnets suivis sont nettoyés : seules leurs sorties,
  souvent issues d'exécutions partielles, sont retirées.
- Métadonnées du paquet : statut **Beta** (au lieu de « Production/Stable ») tant que l'API du
  tuteur évolue, classificateurs « Natural Language :: French » et « Topic :: Education ». Les URL
  du dépôt et de la documentation viendront avec la publication.
- Publication préparée : URL du dépôt `liouai-digital-education/linalg-pedagopy` et de la
  documentation (GitHub Pages) dans `[project.urls]`, badges du README ; workflow
  `documentation.yml` qui publie `docs/site/` ; les liens du site vers le code source visent GitHub
  quand l'URL « Source » est connue ; chemins locaux retirés de l'ancien plan d'implémentation ;
  branche `master` renommée `main`.
- Dépôt public `liouai-digital-education/linalg-pedagopy` : historique publié avec l'adresse e-mail
  du projet, CI verte sur `main` et `development` (Python 3.10 à 3.13), documentation en ligne ;
  relance manuelle possible du workflow Tests. Version lue dans `pyproject.toml` par le site ; test
  de cohérence avec `__version__`.

### Phase 0 du plan v5 — filet de sécurité
- Python **3.10** minimum (`requires-python`, ruff, mypy, classificateurs).
- Tests de caractérisation : traces, discussions de cas et oracle
  (`tests/test_caracterisation_algorithmes.py`), énoncés, indices, jumeaux et diagnostics des 35
  fiches (`tests/test_caracterisation_tuteur.py`), références dans `tests/references/` (régénération
  : `LP_MAJ_REFERENCES=1`).
- `tests/run_notebooks.py` : exécution des carnets maintenus (moteur Jupyter ou simple), journal du
  tuteur temporaire.
- `verifier_tout.py` et intégration continue GitHub Actions (`.github/workflows/tests.yml`) : tests
  et couverture sur Python 3.10 à 3.13, fiches, ruff, mypy (informatif), carnets.
- Configuration ruff (`E4`, `E7`, `E9`, `F`) et mypy (bibliothèques sans types ignorées) ;
  dépendances de développement : `nbformat`, `nbclient`, `ipykernel` (`syrupy`, inutilisé, retiré).
- Corrections de lint sans effet sur le comportement (imports inutilisés, annotation `Mapping`
  manquante, variable inutilisée).
- Documentation développeur : `docs/dev/tests_et_verifications.md`, `docs/dev/couverture.md`.

### Tuteur et exercices
- Les 35 exercices ont désormais un **identifiant lisible**, un **titre**, un **thème** (8 thèmes),
  un **niveau** (★ à ★★★) et un **numéro** ; plus aucune référence à un ouvrage ou recueil externe
  (fiches renommées `<identifiant>.yaml`, champs `page`, `source`, `ecart` supprimés).
- `tutor.catalog()` / `catalogue()` (tableau Markdown dans JupyterLab), `tutor.themes()`,
  `tutor.list_exercises(theme)`, `tutor.reload_catalog()`.
- `tutor.exercise()` accepte un identifiant, un numéro ou un titre ; `UnknownExerciseError` avec
  suggestion en cas de faute de frappe.
- Énoncé avec titre, thème, type et niveau ; `ex.title`, `ex.number`, `ex.theme`, `ex.level`.
- `ex.hint()` explique quand tous les paliers sont débloqués (au lieu d'un message de « niveau 5 »)
  ; nouvelle méthode `ex.reset()` / `ex.recommencer()`.
- `ex.verify()` ne lève plus d'exception sur une réponse mal formée : il indique la forme attendue.
  La réponse `None` n'est plus acceptée comme « invalide ».
- Bilan en Markdown (`ex.summary()`), panneau JupyterLab refait (énoncé rendu en LaTeX, relecture
  d'un palier, zone de réponse et bouton Vérifier).
- 9 nouveaux exercices jumeaux, adaptés au sujet de chaque fiche (matrice décrite par son effet,
  adjacence, puissance de matrice, mise à l'échelle diagonale, inverse d'un produit, système
  linéaire, produit par blocs, valeurs d'un polynôme, inégalité triangulaire) ; jumeau Gram-Schmidt
  détaillé.
- Glossaire étendu à 40 termes, recherche en français, liste avec `glossary()`.
- Messages sans références internes (« Principe 6 », « §7.5 », « D5 »…).

### Nouveautés
- Module `linalg_pedagopy.special` : `difference_matrix`, `running_sum_matrix`,
  `moving_average_matrix`, `vandermonde`, `convolution_matrix`, `convolution`, `selection_matrix`,
  `reversal_matrix` (avec alias français).

### Corrections
- Rendu texte des puissances (`a··2` → `a²`) et des racines (`√(1 − m²)`) ; conditions affichées en
  notation mathématique et factorisées (`b ≠ 1 et b ≠ −1`).
- Discussion de cas en Markdown, LaTeX et HTML : solutions rendues en LaTeX.
- `repr(CaseSplit)` concis (au lieu de la trace complète) ; `print(case_split)` affiche la
  discussion.
- Titre d'un exercice jumeau corrompu par une tabulation (`\text` non échappé).
- Fiches du tuteur : restauration des caractères accentués et des symboles perdus (`§`, `é`, `è`,
  `à`, `ô`, `⊥`, `≈`) dans les champs `source` et `ecart` des 35 fiches ; test de non-régression
  `test_fiches_source_ecart_sans_caracteres_corrompus`.
- `check_row_operation` : une opération qui écrase une ligne sans la conserver (ex. `L1 <- L2`) est
  désormais diagnostiquée comme `row_overwrite` (avec suggestion d'échange ou de transvection) au
  lieu d'être confondue avec une dilatation par 0.

### Documentation
- Documentation réécrite : nouveau guide du tuteur, catalogue des exercices
  (`docs/08_catalogue_exercices.md`, régénéré par `docs/generer_catalogue.py`), guide JupyterLab,
  matrices structurées, site HTML régénéré.
- `TUTORIAL.md` mis à jour ; le carnet tutoriel est désormais généré à partir de `TUTORIAL.md`.
- Correction de la documentation (`docs/*.md`, `README.md`, site HTML `docs/site/`) pour la rendre
  conforme à l'API réelle : exemples exécutables vérifiés, signatures et champs de résultats exacts,
  suppression des fonctionnalités non implémentées (QR Householder/Givens, locale anglaise, méthodes
  de projection, prédicats `is_*`…), liens relatifs vers le code source à la place des chemins
  absolus `file:///`.

## [3.0.0] — 2026-10-19

Version du commit initial `48bf2b7`, publiée sans étiquette git (les étiquettes commencent à
`v3.0.1`).

### Nouveautés majeures (Version 3.0)
- **Tuteur interactif pour VMLS (`linalg_pedagopy.tuteur`)** : accompagnement des étudiants de L1–L2
  sur le recueil *Additional Exercises for Vectors, Matrices, and Least Squares* (Boyd &
  Vandenberghe, éd. 24 nov. 2020) sans jamais révéler la solution en mode étudiant.
- **8 principes pédagogiques du tuteur** :
  - Vérification par propriété plutôt que par corrigé figé ;
  - Diagnostic de ce que calcule la réponse de l'étudiant ;
  - Échelle d'indices gradués sur 4 niveaux (Orientation, Outil, Démarrage, Jumeau) ;
  - Exercice jumeau résolu avec trace complète au niveau 4 ;
  - Verrouillage des données d'exercice (`LockedVector`, `LockedMatrix`) jusqu'à validation ;
  - Prédiction obligatoire avant exploration au laboratoire de contre-exemples ;
  - Refus de confirmer un « toujours vrai » par de simples essais ;
  - Journal JSON local transparent et fonction `valider_fiche`.
- **Couverture du recueil VMLS** : 35 fiches d'exercices (33 exercices couverts complètement `●` +
  exercices `3.3` et `3.13` illustrant le laboratoire de contre-exemples), accompagnées d'un
  glossaire anglais–français intégré.
- **Architecture formelle complète (D1–D11)** :
  - Corps de travail $\mathbb{R}$ (`real=True`, D1) et politique de coercition des flottants
    (`float_policy`, D2) ;
  - Oracle de nullité à 4 verdicts (`ZERO`, `NONZERO`, `CONDITIONAL`, `UNKNOWN`, D3) et discussion
    par cas (`CaseSplit`, D4) ;
  - Objets `Vector` et `Matrix` immuables (D5) appuyés sur `DomainMatrix` (D10) ;
  - Traceur contextuel arborescent (`tracing`, `section`, `record`) à 4 niveaux (D6) et moteurs de
    rendu découplés (`text`, `latex`, `markdown`, `html`, D7) ;
  - Résultats typés (`GJResult`, `SolutionSet`, `GSResult`, `QRResult`, `LSResult`, D8) et pivot le
    plus simple (D11) ;
  - Modules `exercises` (générateurs exacts par matrices unimodulaires, transformée de Cayley,
    etc.), `compare` (exact vs flottant, matrice de Läuchli, Hilbert) et `plot` (figures 2D/3D).
