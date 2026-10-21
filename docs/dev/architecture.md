# Architecture du paquet

Guide pour les contributeurs : où placer un nouveau code, et quelles dépendances il peut avoir. Rédigé à l'étape 5.4 du [plan de développement v6](plans/plan_developpement_v6.md).

## Couches

| Couche | Dossier | Rôle | Peut importer |
|:---|:---|:---|:---|
| Configuration | `config.py` | État immuable et contextuel (`config`, `using_config`). | — |
| Noyau formel | `core/` | Scalaires exacts (`field.py`), oracle de nullité (`zero.py`), conditions et discussions par cas (`cases.py`), exceptions. | `config` |
| Trace | `trace/` | Étapes (`Step`, `StepKind`, `Highlight`) et traceur contextuel (`record`, `section`, `tracing`). | `core` |
| Objets | `objects/` | `Vector` et `Matrix` : représentation et opérations algébriques. | `core`, `trace` |
| Rendu | `render/` | Explications en texte, LaTeX, Markdown, HTML ; locales (`locales/fr.yaml`). | `core`, `trace`, `objects` |
| Algorithmes | `algorithms/` | Procédures tracées (`Procedure` → `Result`) : élimination, Gauss-Jordan, déterminant, Gram-Schmidt, QR, moindres carrés, produits. | toutes les couches précédentes |
| Usages | `exercises/`, `tutor/`, `tuteur/`, `compare/`, `plot/` | Séances interactives, tuteur, comparaisons numériques, figures. | toutes |

Une couche n'importe jamais une couche située plus bas dans ce tableau. Quand une couche basse a besoin d'un service d'une couche haute, elle passe par un **crochet** que la couche haute remplit à l'import :

- `core.field.register_trace_hook` : l'oracle émet des étapes de trace (`emit_core_event`) sans importer `trace` ;
- `core.cases.register_casesplit_explain_hook` : `CaseSplit.explain()` sans importer `render` ;
- `objects.matrix.register_procedure` : les méthodes de commodité de `Matrix` sans importer `algorithms` (ci-dessous).

## Règle de délégation de `Matrix`

`Matrix` contient :

1. la **représentation** : construction (`from_rows`, `identity`, `block`…), accès (`row`, `col`, indexation), conversions (`to_sympy`, `subs`) ;
2. les **opérations algébriques** : `+`, `-`, produit par un scalaire, transposée, `@` ;
3. des **méthodes de commodité de quelques lignes**, regroupées dans une section délimitée, qui délèguent à une procédure de `algorithms/` : `rref`, `rank`, `nullspace`, `inv`, `det`, `solve`, `gram`, `has_orthonormal_columns`, `matmul(view=…)`.

Toute logique d'algorithme (boucle, discussion de cas, trace) vit dans `algorithms/`. Les méthodes de commodité appellent le registre `_procedures`, rempli à l'import de `algorithms/` :

| Nom | Procédure | Module |
|:---|:---|:---|
| `gauss_jordan` | `GaussJordan` | `algorithms/gauss_jordan.py` |
| `determinant` | `Determinant` | `algorithms/determinant.py` |
| `matmul` | produit matriciel tracé selon une vue | `algorithms/products.py` |
| `gram` | matrice de Gram | `algorithms/products.py` |
| `orthonormal_check` | contrôle de `AᵀA = I` | `algorithms/products.py` |
| `singular_check` | annonce des valeurs singulières avant `inv()` | `algorithms/products.py` |

Pour ajouter une méthode de commodité (par exemple `eigenvalues()` en phase 8) :

1. écrire la procédure dans `algorithms/` ;
2. l'enregistrer en bas de son module : `register_procedure("eigen", Eigen)` ;
3. importer le module dans `algorithms/__init__.py` ;
4. ajouter à `Matrix` une méthode de quelques lignes : `_procedure("eigen")(self, …).run()`, et `_champ(res, "attribut")` pour en extraire un champ, branche par branche si le résultat est un `CaseSplit`.

`linalg_pedagopy/__init__.py` importe `algorithms/` : dès que le paquet est importé, le registre est rempli.

## Moteur d'élimination

`algorithms/elimination.py` regroupe ce que partagent les procédures qui échelonnent (phase 4) :

- fonctions pures : `_simplify_entry`, `_pivot_complexity_key`, `_choose_pivot`, `_result_entry` ;
- opérations de lignes tracées : `RowOps` (échange, dilatation, transvection, étape de Bareiss), paramétrées par le préfixe des clés de trace (`gj`, `det`) ;
- moteur : `EliminationEngine`, qui parcourt les colonnes, choisit les pivots et ouvre une discussion par cas quand un pivot peut s'annuler. La procédure lui fournit `setup` (grille de travail sous une condition) et `on_complete` (résultat d'une branche, ou `SplitRequest`) ;
- noyau : `kernel_basis` et `trace_kernel`.

`GaussJordan` et l'élimination du déterminant sont construits sur ce moteur. Bareiss garde sa boucle, car il n'ouvre jamais de discussion, et partage `RowOps`.

## Registre des vérificateurs du tuteur

Chaque type de vérificateur d'une fiche (`valeur`, `matrice`, `labo`…) est décrit une fois par un `VerifierType` (`tutor/registry.py`) : nom français et alias anglais, fonction de vérification, forme de réponse attendue (message quand la réponse est illisible), champs obligatoires de la fiche, contrôle croisé de la validation, et deux drapeaux (`requires_twin`, `checks_hint_leak`, faux pour le laboratoire). La séance (`ExerciseSession.verify`) et la validation des fiches (`validate_sheet`) lisent ce registre.

Pour ajouter un type (par exemple pour le thème 10 de la phase 7) :

1. créer un module `tutor/verifiers/nom.py` (un module par type ; outils communs dans `commun.py`) ;
2. y écrire la fonction de vérification `f(réponse, spécification, données)` et son contrôle croisé `g(séance, spécification, données) -> list[str]` ;
3. l'enregistrer en bas du module : `register_verifier(VerifierType("nom", ("alias",), sans_seance(f), "forme attendue", requires("champ", message=...), g))` ;
4. importer le module dans `tutor/verifiers/__init__.py`.

## Lecture de texte dans le tuteur

Le tuteur et les exercices ne lisent jamais un texte avec `eval`, `exec` ou `sympify` : un texte vient d'une fiche (peut-être écrite par un tiers) ou d'une saisie. Ils utilisent l'interpréteur `tutor/evaluation_sure.py` :

- `evaluer(texte, noms)` : sémantique de Python, seuls `noms` sont connus ;
- `expression(texte, noms)` : sémantique de `sympify` (entiers exacts, `^`, nom inconnu = symbole) ;
- `en_expression(valeur)` : `sympify` d'un objet qui peut contenir des chaînes ;
- `lire_donnee(valeur)` : données d'une fiche (`[1, a]`), symboles réels.

L'interpréteur n'accepte qu'une liste blanche de constructions, refuse les noms et attributs en `_`, les modules, et toute chaîne contenant « ( » ou « __ » transmise à un appel ou à une opération. Un test interdit le retour d'`eval` ou de `sympify` dans `tutor/`, `tuteur/` et `exercises/`.

## Traces et locales

Chaque étape de trace a une clé (`gj.row_add`, `det.bareiss_step`, `ker.vector`…) et des paramètres. Le texte de chaque clé est dans `render/locales/fr.yaml`, et `str.format` y insère les paramètres (accolades littérales doublées : `{{0}}`). Une nouvelle clé s'ajoute dans la section de son préfixe. Les messages d'exception restent écrits dans le code, `core` ne pouvant pas lire les locales de `render`.

## Tests

Voir [tests_et_verifications.md](tests_et_verifications.md). Toute refactorisation doit laisser les références de caractérisation identiques. Tout changement voulu de sortie a son propre commit, avec les références régénérées et relues.
