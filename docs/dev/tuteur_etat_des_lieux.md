# Tuteur : état des lieux avant la phase 6

Étape 6.0 du [plan de développement v6](plans/plan_developpement_v6.md), établie le 21 octobre 2026 sur la branche `development`.

## Modules

Tout le code est dans `tutor/` (noms anglais) ; `tuteur/` ne fait que réexporter ces noms sous des noms de modules français.

| `tutor/` | Lignes | Rôle | Réexporté par `tuteur/` | Couverture |
|:---|---:|:---|:---|---:|
| `verifiers.py` | 1 193 | Vérificateurs (cascade `if v_type in (...)`), forme attendue, diagnostics | `verificateurs.py` | 81 % |
| `catalog.py` | 951 | Lecture des fiches YAML, séance (`ExerciseSession`), validation des fiches | `catalogue.py` | 81 % |
| `lock.py` | 297 | Proxys verrouillés (`LockedVector`, `LockedMatrix`, `LockedNamespace`) | `verrou.py` | 99 % |
| `lab.py` | 248 | Laboratoire de contre-exemples | `labo.py` | 74 % |
| `journal.py` | 192 | Journal des tentatives, persistance JSON | `journal.py` | 85 % |
| `panel.py` | 126 | Panneau ipywidgets et panneau de repli | `panneau.py` | 100 % |
| `hints.py` | 124 | Échelle d'indices à 4 paliers, exercice jumeau | `indices.py` | 100 % |

Couverture mesurée avec `test_tuteur.py`, `test_caracterisation_tuteur.py`, `test_catalogue_et_nouveautes.py` et `test_tuteur_verrou_indices_panneau.py`. Ce dernier fichier, ajouté à l'étape 6.0, fige le comportement de `verrou`, `indices` et `panneau` avant tout déplacement : chaque opération des proxys verrouillés (refusée puis permise), le déblocage différé des indices (tentatives, délai), les boutons du panneau ipywidgets et le panneau de repli.

Les deux modules au-delà de 350 lignes (`verifiers.py`, `catalog.py`) sont ceux que découpent les étapes 6.1 à 6.3.

## Appels à `eval` (corrigés à l'étape 6.4)

À l'étape 6.0, le tuteur comptait douze appels à `eval`, tous avec `{"__builtins__": {}}`. **Cette précaution ne suffisait pas** : un attribut comme `__globals__` rendait les fonctions intégrées, donc tout Python. Par exemple, `_parse_answer("Vector.__init__.__globals__['__builtins__']['len']('abcd')")` renvoyait 4. De même, `sympify` d'une chaîne, et `Vector` ou `Matrix` construits avec des chaînes (ils passent par `sympify`), exécutaient du code.

| Fichier | Appels | Texte évalué | Origine du texte |
|:---|:---:|:---|:---|
| `hints.py` | 1 | champ `jumeau` d'une fiche (`generateurs.…(…)`) | fiche YAML |
| `catalog.py` | 1 | littéraux `Vector([...])`, `Matrix([...])` trouvés dans un indice | fiche YAML |
| `lab.py` | 7 | prédicats du laboratoire (`<=`, `>=`, `==`, `!=`) | fiche YAML |
| `verifiers.py` | 2 (+ 7 `sympify`) | expressions et formules d'une fiche ; réponses saisies sous forme de texte | fiche YAML, saisie de l'élève |
| `panel.py` | 1 | réponse saisie dans le panneau | saisie de l'élève |
| `lock.py` | (via `Vector`, `Matrix`) | chaînes des données (`[1, a]`) | fiche YAML |

Depuis l'étape 6.4, tout passe par l'interpréteur `tutor/evaluation_sure.py` (`evaluer` à la place d'`eval`, `expression` à la place de `sympify` d'une chaîne, `lire_donnee` pour les données des fiches). `tests/test_evaluation_sure.py` essaie les évasions connues à chaque point d'entrée et interdit le retour d'`eval`, d'`exec` ou de `sympify` dans `tutor/`, `tuteur/` et `exercises/`.

## Tests du tuteur et ipywidgets

`test_seance_type_6_4_from_section_7_8` et `test_phase0_english_nomenclature_api` échouaient quand ipywidgets était installé, `str()` d'un vrai `VBox` ne contenant pas l'énoncé. Ils simulent désormais l'absence d'ipywidgets ; `test_panneau_ipywidgets_affiche_enonce` vérifie le panneau graphique, et un job de CI (« Tuteur avec ipywidgets ») exécute les tests du tuteur avec l'option `tuteur` installée.

## Suite de la phase

| Étape | Effet sur les modules |
|:---:|:---|
| 6.1 | Fait : registre `tutor/registry.py` ; `catalog.py` passe de 951 à 716 lignes. |
| 6.2 | Fait : paquet `tutor/verifiers/`, un module par type (vérification, contrôle croisé, enregistrement et forme attendue) et `commun.py` ; le plus gros module fait 212 lignes. Le paquet rejoindra `tuteur/verificateurs/` avec le reste du code à l'étape 6.6 (le faire dès maintenant créerait un import circulaire, `tuteur/` réexportant `tutor/`). |
| 6.3 | Fait : `catalog.py` (716 lignes après 6.1) découpé en `catalog.py` (fiches, thèmes, glossaire, 223 lignes), `session.py` (séance, 320 lignes) et `validation.py` (validation des fiches, 211 lignes) ; ils deviendront `catalogue.py`, `seance.py` et `validation.py` dans `tuteur/` à l'étape 6.6. |
| 6.4, 6.5, 6.7 | Fait : `tutor/evaluation_sure.py` remplace les douze `eval` et les `sympify` de chaînes ; champ `jumeau` analysé par l'interpréteur avec le seul espace de noms des générateurs ; tests d'évasion. |
| 6.6 | Le code passe dans `tuteur/` ; `tutor/` réexporte les noms anglais. |
