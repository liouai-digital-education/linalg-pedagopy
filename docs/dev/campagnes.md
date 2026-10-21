# Campagnes de tests du bac à sable

Étape 3.1 du [plan de développement v6](plans/plan_developpement_v6.md). Les carnets `tests2` à `test4` du bac à sable `bac-a-sable-linalg` ont fait l'objet d'un rapport d'évaluation (21 octobre 2026). Leurs cas sont repris dans le dépôt pour servir de filet de sécurité et de base de mesure.

## Où sont les cas

| Fichier | Rôle |
|:---|:---|
| `tests/campagnes.py` | Les 21 cas (`CAS_CAMPAGNES`) : carnet d'origine, phénomène illustré, calcul, marque « lent ». |
| `tests/test_caracterisation_campagnes.py` | Fige chaque cas dans `tests/references/campagnes/` : discussion de cas et explications en texte (niveaux 0 à 3), ou message d'erreur quand un plafond est atteint. |
| `scripts/mesurer_performances.py` | Mesure le temps, le nombre de branches et la taille des expressions (nombre d'opérations SymPy dans les matrices réduites). |
| `mesures/campagnes_3.1.0.json` | Mesures de référence avant toute correction (version 3.1.0). |

## Reconstitution

Les carnets ne sont pas dans le dépôt : les cas sont reconstruits à partir du rapport.

- **`test4` et `tests2`** : matrices du rapport ; seuls les seconds membres absents du rapport sont choisis.
- **`tests3`** : les 9 tests limites sont reconstitués d'après leur description (même phénomène, mêmes conditions). Le test 5 reproduit exactement la solution du rapport.
- **Matrice bloc-triangulaire 6 × 6** : le rapport ne la décrit que comme « 3 blocs 2 × 2 diagonaux couplés supérieurement ». Les blocs retenus, $\begin{bmatrix} a&1 \\ 1&a \end{bmatrix}$, $\begin{bmatrix} b&1 \\ 1&b \end{bmatrix}$, $\begin{bmatrix} a&b \\ 1&1 \end{bmatrix}$, reproduisent le phénomène : `max_cases=8` est dépassé, 10 branches avec `max_cases=16` (9 dans le rapport), 7 sous l'hypothèse $a \ne 1$ (6 dans le rapport).
- **Matrice bloc 4 × 4 de `tests2`** : le rapport signale `max_depth` atteint ; la matrice retenue (deux blocs $\begin{bmatrix} a&1 \\ 1&a \end{bmatrix}$ et $\begin{bmatrix} b&1 \\ 1&b \end{bmatrix}$) dépasse `max_cases=8`, ce qui illustre la même limite.

## Mesures de référence (3.1.0)

Une exécution par cas, Python 3.11, SymPy 1.14 ; les temps dépendent de la machine, les branches et les tailles non.

| Cas | Temps | Branches | Taille | Remarque |
|:---|---:|---:|---:|:---|
| `t2_asymetrie_factorisation_inverse` | 1,2 s | 3 | 80 | |
| `t2_blocs_4x4_inverse` | 2,7 s | — | — | `max_cases=8` dépassé |
| `t2_circulante_3_parametres_inverse` | 12,0 s | — | — | `max_depth=3` atteint |
| `t3_1_singuliere_partout` | 0,1 s | 2 | 1 | |
| `t3_2_saut_de_rang_3_vers_1` | 0,8 s | 3 | 12 | |
| `t3_3_surdetermine_3x2` | 0,1 s | 2 | 4 | |
| `t3_4_conditions_croisees` | 0,4 s | 3 | 12 | |
| `t3_5_pivot_quadratique` | 0,6 s | 3 | 19 | |
| `t3_6_parametre_au_denominateur` | 0,1 s | 2 | 5 | |
| `t3_7_rang_nul` | 0,0 s | 2 | 0 | |
| `t3_8_strategie_simplest` | 0,1 s | 2 | 7 | |
| `t3_9_homogene` | 0,4 s | 3 | 2 | |
| `t4_bloc_triangulaire_6x6` | 8,1 s | — | — | `max_cases=8` dépassé |
| `t4_bloc_triangulaire_6x6_hypothese` | 8,1 s | 7 | 25 | `max_cases=16`, $a \ne 1$ |
| `t4_bloc_triangulaire_6x6_max16` | 9,9 s | 10 | 26 | `max_cases=16` |
| `t4_equicorrelation_4x4` | 4,1 s | 6 | 42 | |
| `t4_equicorrelation_5x5_hypothese` | 6,4 s | 4 | 47 | $a \ne b$ |
| `t4_fleche_6x6` | 0,7 s | 2 | 32 | |
| `t4_permutee_cyclique_5x5` | 0,5 s | 2 | 62 | |
| `t4_tridiagonale_5x5` | 3,0 s | 5 | 57 | |
| `t4_vandermonde_4x4` | 0,9 s | 4 | 29 | |

Ces mesures précèdent l'étape 3.2, qui ne change ni les branches ni les temps de façon notable, mais modifie l'écriture des trois cas concernés.

Pour comparer après une modification : `python scripts/mesurer_performances.py --json mesures.json`, puis confronter à `mesures/campagnes_3.1.0.json`.

## Constats confirmés par la reconstitution

1. **Factorisation incohérente** (corrigé à l'étape 3.2, `factor_policy`) : `t3_5_pivot_quadratique` affiche la condition $a \ne \sqrt 2$ et $a \ne -\sqrt 2$, mais la solution garde $a^2 - 2$, et la branche singulière s'intitule « $a^2 - 2 = 0$ ». Même chose pour $a^2 + a - 3$ dans `t2_asymetrie_factorisation_inverse` et pour $a^2 - 3$ dans `t4_tridiagonale_5x5`.
2. **Témoins non réduits par la condition de la branche** (constat nouveau, corrigé à l'étape 3.2) : dans la branche $a^2 - 3 = 0$ de `t4_tridiagonale_5x5`, le témoin d'incompatibilité s'écrit $0 = a^4 - 3a^2 + 2$ au lieu de $0 = 2$ ; dans la branche $a^2 - 2 = 0$ de `t3_5_pivot_quadratique`, il reste $0 = 2 - a$.
3. **Plafonds** (messages corrigés à l'étape 3.4 ; nombre de branches : étape 9.3, méthode par blocs) : `t2_blocs_4x4_inverse`, `t2_circulante_3_parametres_inverse` et `t4_bloc_triangulaire_6x6` s'arrêtent sur un message qui ne dit ni quels facteurs sont en cause, ni combien de branches il aurait fallu.
4. **Branches combinées** (étape 9.3) : `t4_bloc_triangulaire_6x6_max16` produit 10 branches, produit des singularités de blocs indépendants. Leurs 10 résultats sont tous distincts : fusionner les branches identiques n'y change rien (mesure de l'étape 4.8).
5. **Facteur sans racine réelle** : `t4_permutee_cyclique_5x5` n'ouvre aucune branche pour $a^4 + a^3 + a^2 + a + 1$, comme l'indiquait le rapport.

## Pivot creux et remontée (étape 4.9)

Mesures des quatre combinaisons de `pivot_strategy` (`simplest`, `sparse`) et `reduction` (`simultaneous`, `back_substitution`) sur six cas des campagnes. La taille est le nombre maximal d'opérations SymPy dans une matrice de travail, sur toutes les étapes et toutes les branches.

| Cas | simplest / simultaneous | simplest / back_substitution | sparse / simultaneous | sparse / back_substitution |
|:---|---:|---:|---:|---:|
| Tridiagonale 5 × 5 | 3,1 s · 27 | 2,4 s · 27 | 3,2 s · 27 | 2,4 s · 27 |
| Flèche 6 × 6 | 0,8 s · 23 | 0,8 s · 23 | 0,7 s · 23 | 0,7 s · 23 |
| Permutée cyclique 5 × 5 | 0,5 s · 58 | 0,5 s · 58 | 0,5 s · 58 | 0,5 s · 58 |
| Équicorrélation 4 × 4 | 4,1 s · 40 | 4,0 s · 40 | 3,5 s · 25 | 3,3 s · 25 |
| Vandermonde 4 × 4 | 0,9 s · 26 | 0,9 s · 27 | 0,9 s · 26 | 0,9 s · 27 |
| Bloc-triangulaire 6 × 6 (a ≠ 1) | 8,3 s · 42 | 7,5 s · 30 | 8,4 s · 42 | 7,1 s · 30 |

Mêmes branches et mêmes résultats dans tous les cas, vérifiés pour des valeurs numériques des paramètres. Seul le témoin d'incompatibilité peut différer avec `sparse` (0 = −2 au lieu de 0 = 1), parce que les opérations de lignes ne sont pas les mêmes.

**Conclusion** : gains réels mais modestes (la taille maximale est le plus souvent celle de la forme réduite finale, identique dans tous les cas). Les deux options restent facultatives, et les réglages par défaut (`simplest`, `simultaneous`) sont conservés, ce qui laisse toutes les traces inchangées. Le gain décisif sur ces familles viendra des méthodes dédiées de la phase 9.

