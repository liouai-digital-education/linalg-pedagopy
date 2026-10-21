---
title: "linalg_pedagopy — Plan de développement v6"
subtitle: "Corriger ce que les campagnes de tests ont révélé, un moteur d'élimination réutilisable, les sous-espaces, les valeurs propres, puis les familles de matrices structurées"
author: "Cédric Bohnert"
date: "21 octobre 2026"
lang: fr
---

# 1. Objet et résumé

Ce plan remplace le plan v5 (`plan_developpement_v5.md`) à partir de la version 3.1.0, qui clôt ses phases 0 à 2. Il intègre deux documents reçus le 21 octobre 2026 :

- le **rapport d'évaluation des carnets** `tests1` à `test4` du bac à sable (résolution paramétrique, 9 tests limites, matrices pleines et creuses de 4 × 4 à 6 × 6, taxonomie des familles structurées, « règle des deux régimes ») ;
- le **référentiel d'architecture bases, sous-espaces et noyau** (obstacles didactiques, classes `Basis` et `Subspace`, algorithme de Zassenhaus, thème 10 du tuteur).

Les deux documents ont été relus et leurs exemples recalculés ; ils sont traités comme des **contributions à vérifier**, pas comme des spécifications (voir § 3).

Quatre décisions structurent la révision :

- **Corriger avant de refactoriser.** Les défauts relevés par les tests (factorisation incohérente, messages de plafond, signe des facteurs) changent des sorties ; ils passent avant l'extraction du moteur, qui doit rester une refactorisation pure.
- **Le moteur d'élimination reçoit les besoins des deux rapports** : extraction tracée du noyau, regroupement des branches identiques à l'affichage, pivots qui préservent les zéros, symboles non discutés (le $\lambda$ des valeurs propres, mais aussi les $x, y, z$ du passage générateurs → équations).
- **Les sous-espaces passent avant les valeurs propres.** Un espace propre est un sous-espace : on évite de livrer `Eigen` avec des tuples de vecteurs pour les migrer ensuite.
- **Les familles structurées viennent en dernier**, une fois les valeurs propres disponibles, car plusieurs raccourcis sont spectraux (compagnon, projecteur, rang 1 perturbé). La « règle des deux régimes » est adoptée sous forme d'un **avertissement réglable**, jamais d'un refus de calcul.

| Phase | Contenu | Nature | Effort estimé | Version |
|:----:|:---------------------------|:---------------------------|:--------:|:------:|
| 0–2 | Filet de sécurité, corrections et publication, déterminant (plan v5) | — | **fait** | 3.1.0 |
| 3 | Correctifs issus des campagnes de tests | correctifs | 1 à 2 séances | 0.3.1.1 |
| 4 | **Moteur d'élimination** réutilisable, noyau tracé, regroupement des branches | refactorisation + fonctionnalité | 3 à 4 séances | 0.3.1.2 |
| 5 | Allègement de `Matrix` (règle de délégation, registre de procédures) | refactorisation | 1 séance | 0.3.1.2 |
| 6 | Tuteur : registre des vérificateurs, suppression des `eval`, API française | refactorisation + sécurité | 2 séances | 0.3.1.2 (PyPI reporté) |
| 7 | **Bases et sous-espaces** (`Basis`, `Subspace`, Zassenhaus, thème 10) | fonctionnalité | 4 à 5 séances | 0.3.2.0 |
| 8 | **Valeurs propres, espaces propres, diagonalisation** | fonctionnalité | 3 à 4 séances | 0.3.3.0 |
| 9 | **Familles structurées** (« régime 2 ») | fonctionnalité | 3 à 4 séances | 0.3.4.0 |
| 10 | Extensions ultérieures ($\mathbb{C}$, circulantes, LU, géométrie…) | feuille de route | — | — |

Les versions suivent la numérotation `0.3.x.y` adoptée avec 0.3.1.1 (étiquettes `v0.3.x.y`) : le plan prévoyait d'abord 3.1.1, 3.1.2, 3.2.0… ; 3.0.1 et 3.1.0 restent les numéros des versions déjà publiées.

Une *séance* désigne une demi-journée à une journée de travail. Les phases 4.1 à 4.6, 5 et 6 ne changent **aucun comportement visible** ; les étapes qui changent des sorties (phase 3, étapes 4.7 à 4.9) ont chacune leur commit, avec régénération et relecture des références.

## 1.1 Correspondance avec le plan v5

| Plan v5 | Plan v6 |
|:-----------------|:----------------|
| Phases 0, 1, 2 | terminées (3.0.1, 3.1.0) |
| — | **Phase 3 — Correctifs issus des campagnes de tests** (nouvelle) |
| Phase 3 — Moteur d'élimination | Phase 4, enrichie (étapes 4.7 à 4.9) |
| Phase 4 — Alléger `Matrix` | Phase 5 |
| Phase 5 — Tuteur | Phase 6 |
| Phase 7 — « Sous-espaces comme objets » (piste) | **Phase 7 — Bases et sous-espaces** (avancée et détaillée) |
| Phase 6 — Valeurs propres | Phase 8 |
| — | **Phase 9 — Familles structurées** (nouvelle) |
| Phase 7 — Extensions | Phase 10 |

# 2. État des lieux (21 octobre 2026)

## 2.1 Versions publiées

- **3.0.1** : corrections de la phase 0 (domaine de l'oracle, condition d'un produit, `explain(level=0)`, réponses illisibles du tuteur, mypy), dépôt public, CI verte, documentation en ligne.
- **3.1.0** : déterminant exact tracé (Bareiss, élimination, cofacteurs, Sarrus), thème « Déterminants » (exercices 36 à 39), vérificateur `ensemble_valeurs`, `Matrix.inv()` qui annonce les valeurs singulières du paramètre.

## 2.2 Mesures

- **Tests** : 191 tests collectés par `pytest`.
- **Tuteur** : 39 exercices en 9 thèmes ; aucun sur les espaces vectoriels, la dimension, les sous-espaces ou les changements de base.
- **Plus gros modules** : `tutor/verifiers.py` (1 193 lignes), `tutor/catalog.py` (951), `exercises/generators.py` (834), `objects/matrix.py` (819), `algorithms/gauss_jordan.py` (721), `algorithms/determinant.py` (404).
- **`eval`** : douze appels subsistent dans `tutor/` (`lab.py` ×7, `verifiers.py` ×2, `catalog.py`, `hints.py`, `panel.py`).
- **`tuteur/`** : simples réexportations (263 lignes) ; le code reste dans `tutor/`. La migration du plan v5 (phase 5) est entièrement à faire.

## 2.3 Constats des campagnes de tests (`tests1` à `test4`)

| Constat | Origine | Traitement |
|:------------------------------|:-------------------|:-----------:|
| `max_cases=8` saturé par une matrice bloc-triangulaire 6 × 6 : les singularités de blocs indépendants se combinent (9 branches avec `max_cases=16`) | moteur : séparation pivot par pivot | 9.3 (la fusion de branches n'y change rien : 10 résultats distincts) |
| Circulante 3 × 3 à trois paramètres : inversion impossible sous les plafonds par défaut | combinatoire $2^k$ | 3.4, phase 10 (circulantes) |
| Solution factorisée sur $\mathbb{Q}$ (`a² − 2`) mais condition écrite sur $\mathbb{R}$ (`a ≠ ±√2`) | `_simplify_entry` (`sp.factor`) contre `_split_neq` (`sp.roots`) | 3.2 |
| Tridiagonale 5 × 5 : la remontée remplit les zéros hors diagonale (pivots de Chebyshev) | Gauss-Jordan complet | 4.9, 9.3 |
| Matrice flèche 6 × 6 : remplissage total si la première ligne sert de pivot ; évité par `simplest` | ordre des pivots | 4.9 |
| Équicorrélation 5 × 5 : fractions bivariées lourdes là où une formule de rang 1 suffit | absence de reconnaissance de structure | 9.3 |
| Permutée cyclique 5 × 5 : facteur $a^4 + a^3 + a^2 + a + 1$ sans racine réelle, **aucune branche parasite** | oracle déjà correct en une variable | 3.3 (non-régression) |

## 2.4 Constats du référentiel bases et noyau

- `Matrix.nullspace()` renvoie un tuple de vecteurs anonyme, sans dimension ambiante ni équations ; il construit le système complet $[A \mid 0]$.
- `GaussJordan._extract_nullspace()` assemble les vecteurs **sans étape de trace** : `explain(level=2)` ne montre pas comment les équations mènent à la base, ni pourquoi elle est libre.
- Ni `image()` (ou `colspace()`), ni `rowspace()`, ni bilan du théorème du rang.
- Aucun réglage de format des bases (fractions, entiers, orthonormée) dans `ConfigState`.

# 3. Relecture critique des deux rapports

## 3.1 Rapport d'évaluation des carnets

**Retenu** : tous les constats du § 2.3 ; le principe didactique des deux régimes (élimination pour les matrices génériques de petite taille, reconnaissance de structure au-delà) ; la priorité donnée aux raccourcis structurels sur la force brute.

**Ajusté** :

1. **Pas de plafond strict $N \le 4$.** Déclarer une matrice « générique », c'est constater qu'aucune structure n'a été reconnue : cela suppose les détecteurs de la phase 9. En attendant, un avertissement didactique réglable (`max_generic_dim`), qui ne bloque jamais le calcul (étape 3.5), puis enrichi par `A.structure()` (étape 9.2).
2. **Le critère de priorité est didactique, pas algorithmique.** Les complexités $O(n)$ (Thomas) et $O(n^2)$ (Levinson-Durbin) relèvent du calcul numérique. Pour un outil symbolique de L1–L2 et CPGE, la valeur est dans le **raisonnement par la structure** : récurrence sur le déterminant, formule de Sherman-Morrison, formule produit de Vandermonde. Les familles sont classées par fréquence dans les cours et les sujets d'examen (§ 12.3).
3. **Les circulantes exigent $\mathbb{C}$** (racines $n$-ièmes de l'unité), ce qui contredit la décision « $\mathbb{R}$ seul » ; elles sont reportées à la phase 10, avec l'option `field="C"`.
4. **L'axe 3 (élagage cyclotomique) est largement acquis** : le rapport constate lui-même l'absence de branche parasite sur $P_5$. Reste à vérifier les facteurs de signe constant à **plusieurs** paramètres ($a^2 + b^2 + 1$).
5. **`factor_policy`** change des sorties : commit dédié et références relues (étape 3.2).

## 3.2 Référentiel bases, sous-espaces et noyau

**Retenu** : les cinq obstacles didactiques (statut de $\ker A = \{0\}$ et de la base vide ; liberté de la base lue sur la sous-matrice identité ; confusion $\operatorname{Im} A$ / $\operatorname{Row} A$ ; fractions parasites ; sens de la matrice de passage) ; les objets `Basis` et `Subspace` ; l'algorithme de Zassenhaus ; le passage générateurs → équations cartésiennes ; le vérificateur qui accepte **toute** base correcte ; les tests de propriétés (théorème du rang, Grassmann, orthogonalité).

**Erreurs relevées (recalculées avec SymPy), à corriger avant toute reprise dans la documentation ou les fiches** :

1. **Scénario 3 (Zassenhaus) faux.** Avec $u_1 = (1, 0, 1, 0)$, $u_2 = (0, 1, 1, 1)$, $v_1 = (1, 1, 2, 1)$, $v_2 = (1, -1, 0, -1)$, on a $v_1 = u_1 + u_2$ et $v_2 = u_1 - u_2$, donc $G = F$ : $\dim(F + G) = 2$ et $\dim(F \cap G) = 2$, non 1. La ligne « $2 + 1 = 3 = \dim F + \dim G$ » est fausse ($\dim F + \dim G = 4$). L'exemple doit être refait avec une intersection de dimension 1.
2. **Scénario 1** : la forme échelonnée réduite est juste, mais un « hyperplan de codimension 2 » est contradictoire (un hyperplan est de codimension 1) ; $F$ est un sous-espace de dimension 3 de $\mathbb{R}^5$.
3. **Le code proposé ignore les paramètres** :
   - `Basis.__post_init__` appelle `rank()`, qui peut renvoyer un `CaseSplit` ;
   - `Subspace.contains` compare `eq.dot(v) == 0` structurellement au lieu d'interroger l'oracle ;
   - `Subspace.from_equations` remplace silencieusement un `CaseSplit` par une base vide, ce qui est mathématiquement faux ;
   - `Basis.to_integer` multiplie par le PPCM des dénominateurs : avec un paramètre (dénominateur $a - 1$), ce n'est valable que si $a \ne 1$, condition qui doit rejoindre la branche.
4. **Rupture d'API** : faire renvoyer un `Subspace` à `nullspace()` casse les appels existants, contre la règle de compatibilité (§ 4).
5. **Format des fiches** : l'exemple YAML (`hints`, `twin_exercise`, `verifier: "verificateurs.…"`) ne correspond pas au format réel (`enonce`, `indices`, `jumeau`, `verification.type`) ; une chaîne désignant une fonction à évaluer irait contre la suppression des `eval`.
6. **Configuration redondante** : `nullspace_basis_format` et `prefer_integer_bases` règlent la même chose ; une seule option est retenue.

# 4. Principes de conduite

Ceux du plan v5 restent en vigueur, avec deux ajouts :

- **Une étape = un commit** (ou une petite série), message en français `type(portée): résumé`.
- **Refactorisation pure** dans les étapes 4.1 à 4.6, et dans les phases 5 et 6 : aucun changement de sortie, garanti par les tests de caractérisation.
- **Toute correction de comportement** a son propre commit, régénère les références concernées (`LP_MAJ_REFERENCES=1`) et s'accompagne d'une relecture du diff des références.
- **Compatibilité de l'API publique** : tout nom importable aujourd'hui le reste au moins une version ; un changement de type de retour passe par une nouvelle méthode, pas par la modification de l'ancienne.
- **Chaque fonctionnalité nouvelle arrive complète** : code, tests, locale `fr.yaml`, rendu (texte, LaTeX, Markdown, HTML), documentation, au moins une fiche.
- **Calcul exact sur $\mathbb{R}$** ; **une trace affichée est valable pour toutes les valeurs des paramètres couvertes par sa branche.**
- **Extraire une abstraction quand elle a au moins deux utilisateurs concrets.**
- *Nouveau* — **Tout objet mathématique accepte les paramètres.** Une construction dont la validité dépend d'un paramètre (liberté d'une famille, dimension d'un sous-espace, multiplication par un facteur) renvoie un `CaseSplit` ou ajoute sa condition à la branche ; elle ne suppose jamais le cas générique en silence.
- *Nouveau* — **Les exemples des documents externes sont recalculés** avant d'entrer dans la documentation, une fiche ou un test.

# 5. Phase 3 — Correctifs issus des campagnes de tests

**Objectif** : figer les cas des carnets du bac à sable, puis corriger les défauts qu'ils révèlent, avant d'extraire le moteur.

| N° | Tâche | Détail |
|:-----:|:---------------------------|:-----------------------------------|
| 3.1 | Caractérisation des campagnes | Les 9 tests limites de `tests3` et les 6 familles de `test4` (tridiagonale 5 × 5, flèche 6 × 6, bloc-triangulaire 6 × 6, permutée cyclique 5 × 5, équicorrélation 4 × 4 et 5 × 5, Vandermonde 4 × 4) entrent dans `tests/test_caracterisation_algorithmes.py`, avec leurs références. Les cas lents (> 5 s) sont marqués `lent` et exclus de la CI rapide. Un script `scripts/mesurer_performances.py` enregistre leurs temps actuels : c'est la base de comparaison des phases 4 et 9. |
| 3.2 | Factorisation cohérente | Option `ConfigState.factor_policy` : `"rational"` (comportement actuel) ou `"real_radicals"` (**défaut dès 0.3.1.1**, décision 15.1.10). Avec `"real_radicals"`, les entrées d'une branche sont factorisées sur $\mathbb{Q}(\sqrt{d})$ dès que la condition de la branche fait apparaître $\sqrt{d}$ (`sp.factor(..., extension=...)`), de sorte que la solution du test 5 s'écrive avec $(a - \sqrt 2)(a + \sqrt 2)$ comme sa condition. Commit dédié, références relues. |
| 3.3 | Signe constant à plusieurs paramètres | L'oracle reconnaît les facteurs strictement positifs sur $\mathbb{R}^k$ : sommes de carrés plus une constante positive, formes quadratiques définies (critère des mineurs). Tests : $a^2 + b^2 + 1$, $a^2 + ab + b^2 + 1$ ; $P_5$ reste en non-régression. |
| 3.4 | Messages de plafond didactiques | Quand `max_cases` ou `max_depth` est atteint, le message nomme les facteurs responsables, le nombre de branches qu'il aurait fallu, et propose `assumptions="..."` ou un plafond plus élevé. Message en français dans `fr.yaml`. |
| 3.5 | Avertissement de taille | `ConfigState.max_generic_dim = 4` : au-delà, Gauss-Jordan sur une matrice contenant des paramètres émet un `PedagogicalWarning` (« l'élimination sur une matrice symbolique n × n produit une discussion peu lisible ; cherchez une structure remarquable »). Le calcul continue ; `max_generic_dim=None` désactive l'avertissement. |

**Critères de fin** : campagnes figées en références, test 5 cohérent, messages de plafond relus, version **0.3.1.1** (prévue d'abord sous le numéro 3.1.1).

# 6. Phase 4 — Moteur d'élimination réutilisable

**Objectif** : isoler dans `algorithms/elimination.py` la machinerie commune à Gauss-Jordan et au déterminant (étapes 4.1 à 4.6, refactorisation pure), puis l'enrichir des besoins des deux rapports (étapes 4.7 à 4.9, changements de sortie assumés).

## 6.1 Conception

La conception du plan v5 (§ 7.2) est reprise :

```python
@dataclass
class EliminationState:
    grid: list[list[sp.Expr]]       # matrice de travail (éventuellement augmentée)
    condition: Condition            # hypothèses de la branche courante
    pivots: list[tuple[int, int]]   # (ligne, colonne) des pivots trouvés
    swaps: int                      # nombre d'échanges (signe du déterminant)
    scale: sp.Expr                  # produit des facteurs de dilatation appliqués

class EliminationEngine:
    def __init__(self, *, pivot_strategy, reduce_above: bool, normalize_pivots: bool,
                 fraction_free: bool, split_col: int | None,
                 indeterminates: frozenset[sp.Symbol], max_depth: int, max_cases: int): ...
    def run(self, A_aug: Matrix, cond: Condition, depth: int,
            on_complete: Callable[[EliminationState], R]) -> R | CaseSplit[R]: ...
```

Les `indeterminates` (symboles jamais discutés par l'oracle) servent à deux clients prévus : le $\lambda$ de $\det(A - \lambda I)$ (phase 8) et les coordonnées $x_1, \dots, x_n$ du passage générateurs → équations cartésiennes (étape 7.5).

## 6.2 Étapes

| N° | Étape | Contrôle |
|:-----:|:-----------------------------------|:----------------------------|
| 4.1 | Extraire les fonctions pures (`_simplify_entry`, `_pivot_complexity_key`, choix du pivot) | tests verts |
| 4.2 | Extraire les opérations élémentaires tracées (échange, dilatation, transvection, étape de Bareiss) | traces identiques |
| 4.3 | Extraire la boucle d'élimination et `_split_on_factors` dans `EliminationEngine` | traces et `CaseSplit` identiques |
| 4.4 | Réécrire `GaussJordan._solve_under_condition` comme appel au moteur + `on_complete` | `gauss_jordan.py` < 400 lignes |
| 4.5 | Reconstruire `Determinant` (élimination et Bareiss) sur le moteur ; ajouter le `CaseSplit` du mode élimination paramétré | traces identiques ; nouveaux tests |
| 4.6 | Tests propres au moteur (mode triangulaire, comptage des échanges, indéterminées non discutées) | nouveaux tests verts |
| 4.7 | **Noyau tracé** : `EliminationEngine.kernel(A)` travaille sur $A$ sans colonne de zéros ; nouvelles étapes de trace `ker.free_vars` (variables libres), `ker.param_system` (variables principales en fonction des libres), `ker.vector` (vecteur obtenu en posant une variable libre à 1), `ker.identity_block` (sous-matrice identité qui prouve la liberté). `GaussJordan` et `Matrix.nullspace()` l'utilisent. | références relues (nouvelles étapes au niveau 2) |
| 4.8 | **Regroupement à l'affichage** (révisé, décision 15.1.11) : aux niveaux 0 et 1, les branches particulières dont le résumé est identique s'affichent ensemble (« Cas a = 3, a = 2 ou a = 1 : système incompatible ») ; le `CaseSplit` n'est pas modifié. La fusion véritable, prévue d'abord, demandait des conditions disjonctives pour retirer 4 branches sur 73 dans les cas de référence, et ne réglait pas la bloc-triangulaire 6 × 6 (10 résultats distincts). | références relues |
| 4.9 | **Pivots qui préservent les zéros** : stratégie `sparse` (critère de Markowitz : minimiser $(r_i - 1)(c_j - 1)$ parmi les candidats inconditionnellement non nuls), et mode `back_substitution` (forme échelonnée puis remontée, au lieu de Gauss-Jordan complet) pour limiter la croissance des expressions. | temps et tailles d'expressions comparés à l'étape 3.1 (tridiagonale, flèche) |

## 6.3 Risques

- **Régression dans l'ordre des branches ou des étapes** : couverte par les tests de caractérisation ; les étapes 4.7 à 4.9 viennent **après** que 4.1 à 4.6 ont été validées sans changement de sortie.
- **Regroupement trompeur** : deux branches au même résumé peuvent différer dans le détail ; le regroupement ne vaut qu'aux niveaux 0 et 1, et chaque branche garde sa trace au niveau 2.
- **Performance** : mesurée sur les cas de l'étape 3.1 avant et après.

**Critère de fin** : Gauss-Jordan et déterminant sur le moteur, noyau tracé, version **0.3.1.2** (avec les phases 5 et 6).

# 7. Phase 5 — Alléger `Matrix`

Contenu du plan v5 (§ 8), qui devient urgent : `matrix.py` fait 819 lignes avant l'ajout de `kernel()`, `image()`, `rowspace()`, `structure()`, `eigenvalues()`…

| N° | Tâche |
|:----------:|:-----------------------------------------------------------|
| 5.1 | Remplacer le crochet `_require_gj` par un registre générique `_procedures` (`"gauss_jordan"`, `"determinant"`, `"subspaces"`, `"eigen"`, `"structure"`), alimenté par `algorithms/__init__.py`, sans import circulaire. |
| 5.2 | Regrouper les méthodes de commodité dans une section délimitée ; aucune ne dépasse quelques lignes. |
| 5.3 | Déplacer la logique de `matmul(view=…)` dans `algorithms/products.py`. |
| 5.4 | Documenter la règle de délégation dans `docs/dev/architecture.md`, avec l'emplacement des futurs modules `objects/subspace.py` et `structure/`. |

Critère de fin : `matrix.py` sous 600 lignes, API inchangée, tests verts.

# 8. Phase 6 — Tuteur : découpage, suppression des `eval`, API française

Contenu du plan v5 (§ 9), inchangé sur le fond ; menée en parallèle des phases 3 à 5. Le registre des vérificateurs (6.1) est un **prérequis du thème 10** (phase 7) : chaque nouveau type de vérification doit s'ajouter en un module et une ligne d'enregistrement.

| N° | Tâche |
|:------:|:---------------------------------------|
| 6.0 | Faire le point sur `tuteur/` (aujourd'hui de simples réexportations) ; compléter les tests de `verrou`, `indices` et `panneau` avant tout déplacement. |
| 6.1 | Registre `{type: fonction}` des vérificateurs à la place des cascades `if v_type in (...)`. |
| 6.2 | Un module par vérificateur dans `tuteur/verificateurs/` ; la forme attendue rejoint chaque module. |
| 6.3 | Découper `catalog.py` en `catalogue.py`, `seance.py`, `validation.py` ; contrôle croisé par vérificateur. |
| 6.4 | `evaluation_sure.py` : interpréteur fondé sur `ast` (liste blanche), qui remplace les **douze** `eval`. |
| 6.5 | Champ `jumeau` des fiches analysé par l'interpréteur, avec le seul espace de noms des générateurs. |
| 6.6 | Code déplacé de `tutor/` vers `tuteur/` ; `tutor/` réexporte les noms anglais (silencieux en 0.3.1.2, `DeprecationWarning` dès 0.3.2.0, suppression en 0.4.0.0 : décision 15.1.13) ; documentation et carnets en noms français. |
| 6.7 | Tests de l'interpréteur (attributs privés, `__import__`, lambda, compréhensions, appels hors liste blanche refusés). |

Critère de fin : aucun fichier du tuteur au-delà d'environ 350 lignes, plus aucun `eval`, diagnostics identiques. Avec les phases 4 et 5 : version **0.3.1.2** ; la première publication sur PyPI, d'abord prévue ici, est reportée (décision du 21 octobre 2026).

# 9. Phase 7 — Bases et sous-espaces

**Objectif** : faire passer l'outil du calcul matriciel au raisonnement sur les sous-espaces, en servant de passerelle entre le mode matriciel et le mode structural (Dorier, Robert, Hillel, Sierpinska), tout en restant exact et valable sous paramètres.

## 9.1 Objets

| Élément | Description |
|:-----------------------------------|:-----------------------------------|
| `Basis` (`objects/subspace.py`) | Famille ordonnée **libre** de vecteurs de même taille, immuable. La base vide est admise (sous-espace $\{0\}$). La liberté est vérifiée par le moteur ; si elle dépend d'un paramètre, le constructeur `Basis.of(vecteurs, assumptions=...)` renvoie un `CaseSplit` (« libre si $a \ne 1$ ; liée si $a = 1$ »), et le constructeur direct exige une condition sous laquelle la liberté est inconditionnelle. Méthodes : `dim`, `ambient_dim`, `as_matrix()`, `coordinates(v)`, `reconstruct(coords)`, `to_integer()`, `orthonormalize()`. |
| `Subspace` | Sous-espace de $\mathbb{R}^n$ décrit **à la fois** par une base et par des équations cartésiennes, calculées à la demande. Constructeurs `Subspace.span(vecteurs)`, `Subspace.kernel(A)`, `Subspace.image(A)`, `Subspace.from_equations(A)`, avec les alias français `engendre`, `noyau`, `depuis_equations` ; méthode `equations()` ; chacun renvoie un `CaseSplit[Subspace]` quand la dimension dépend des paramètres. Opérations : `dim`, `codim`, `contains(v)` (oracle, éventuellement conditionnel), `+`, `&`, `is_direct_sum`, `is_supplementary`, `orthogonal()`, `decompose(v, G)`, `project(v)`. |
| `RankNullityReport` | Bilan $\operatorname{rg} A + \dim \ker A = n$ par branche, avec un tableau comparatif des branches (rang perdu = dimension gagnée par le noyau). |
| `FourSubspacesReport` | Les quatre sous-espaces fondamentaux de Strang, avec la vérification tracée $\ker A \perp \operatorname{Row} A$ et $\ker A^T \perp \operatorname{Im} A$. |

## 9.2 Étapes

| N° | Étape | Détail |
|:-----:|:-----------------------------------|:-----------------------------------|
| 7.1 | `Basis` et `Subspace` | Objets du § 9.1, sur le moteur de la phase 4 ; aucune comparaison structurelle `== 0`, toujours l'oracle. |
| 7.2 | Bases entières | `to_integer()` : sur $\mathbb{Q}$, multiplication par le PPCM des dénominateurs puis division par le PGCD des numérateurs (vecteur primitif) ; sur $\mathbb{Q}(\text{paramètres})$, partie primitive sur l'anneau des polynômes, **chaque facteur multiplié étant ajouté à la condition de la branche** et annoncé dans la trace (« on multiplie par $a - 1$, non nul dans cette branche »). |
| 7.3 | API de `Matrix` | `A.kernel()`, `A.image()` (alias `A.colspace()`) et `A.rowspace()` renvoient un `Subspace` (ou un `CaseSplit`) ; alias français documentés à côté : `A.noyau()`, `A.espace_lignes()` (décision 15.1.9). `A.nullspace()` **garde son tuple** et reçoit une option `format="canonical" \| "integer" \| "orthonormal"`. `A.rank_nullity()` et `A.four_subspaces()`. Méthodes de commodité de quelques lignes (règle de la phase 5). |
| 7.4 | Image et espace des lignes tracés | L'image est engendrée par les **colonnes de $A$ d'origine** aux indices des pivots, l'espace des lignes par les lignes non nulles de la forme réduite ; la trace rappelle ce que les opérations sur les lignes conservent (noyau, espace des lignes, relations entre colonnes) et ce qu'elles changent (espace des colonnes). |
| 7.5 | Générateurs → équations | Matrice $[V \mid x]$ avec $x_1, \dots, x_n$ déclarés `indeterminates` du moteur ; les lignes nulles à gauche donnent les $n - r$ équations de compatibilité. Exemple de référence : $\operatorname{Vect}((1,2,1), (-1,0,3))$ a pour équation $3x - 2y + z = 0$. |
| 7.6 | Zassenhaus | `algorithms/subspaces.py` : matrice $\begin{bmatrix} U & U \\ V & 0 \end{bmatrix}$, échelonnement tracé, lecture des bases de $F + G$ et de $F \cap G$, vérification de Grassmann affichée. Somme directe, supplémentaire, décomposition $x = x_F + x_G$ et projection sur $F$ parallèlement à $G$. Exemple de référence **refait** (intersection de dimension 1, § 3.2). |
| 7.7 | Orthogonalité | `Subspace.orthogonal()` ; projection orthogonale (avec `GramSchmidt` existant) ; quatre sous-espaces fondamentaux. |
| 7.8 | Changement de base | `Matrix.passage(B, B_prime)` : colonnes = coordonnées des vecteurs de $B'$ dans $B$ ; trace qui rappelle $X = P X'$, donc $X' = P^{-1} X$, et $M_{B'}(f) = P^{-1} M_B(f) P$. |
| 7.9 | Configuration | `ConfigState.basis_format` (`"canonical"`, `"integer"`, `"orthonormal"` ; **défaut `"canonical"`**, décision 15.1.12 ; valeurs en anglais comme les autres options de `ConfigState`) et `free_symbol` (`"t"` : $t_1, t_2, \dots$ pour les paramètres libres). Pas d'option redondante. |
| 7.10 | Rendu et locales | Clés `ker.*`, `im.*`, `sub.*`, `zass.*`, `passage.*` dans `fr.yaml` ; rendu texte, LaTeX, Markdown, HTML ; $\ker A = \{0\}$, $\dim = 0$, base $= \varnothing$ affichés explicitement (obstacle 1). |
| 7.11 | Tuteur : thème 10 « Bases, sous-espaces et dimension » | Huit fiches **au format du dépôt** : `base-noyau-canonique` (★), `noyau-sans-fraction` (★), `theoreme-rang-parametre` (★★), `image-vs-lignes` (★★), `intersection-zassenhaus` (★★), `passage-et-coordonnees` (★★), `somme-directe-suppl` (★★★), `generateurs-vers-equations` (★★★). Chacune avec trois paliers d'indices, un jumeau généré, des erreurs typiques diagnostiquées. |
| 7.12 | Vérificateurs | `base_sous_espace` : accepte **toute** base du sous-espace attendu (nombre de vecteurs = dimension, appartenance, liberté), avec un diagnostic distinct pour chaque échec (vecteur nul dans une base, famille liée, vecteur hors du sous-espace, colonnes de la forme réduite données pour l'image). `equations_cartesiennes` : système équivalent (même noyau), quel que soit le choix des équations. `matrice_passage` : diagnostic dédié de la confusion $P$ / $P^{-1}$. |
| 7.13 | Tests | Tests de propriétés `hypothesis` : $\dim \ker A + \operatorname{rg} A = n$ ; tout vecteur du noyau est orthogonal à toute ligne ; Grassmann ; $\operatorname{Vect}$ inchangé par `to_integer()` ; `decompose` reconstruit $v$. Cas paramétrés : $A(m) = \begin{bmatrix} 1&1&m \\ 1&m&1 \\ m&1&1 \end{bmatrix}$ ($\det = -(m-1)^2(m+2)$ ; noyau de dimension 0, 1 en $m = -2$, 2 en $m = 1$). Comparaison avec `sympy.Matrix.nullspace()` et `columnspace()`. |
| 7.14 | Documentation | Nouveau guide « Bases et sous-espaces », référence de l'API, section du tutoriel, mise à jour du catalogue. |

## 9.3 Critères de fin

`Subspace`, `Basis`, Zassenhaus et changement de base disponibles et valables sous paramètres ; 8 fiches validées ; documentation à jour ; version **0.3.2.0**.

# 10. Phase 8 — Valeurs propres, espaces propres, diagonalisation

Contenu du plan v5 (§ 10), avec trois ajustements :

1. **Les espaces propres sont des `Subspace`** : `EigenResult.eigenspaces` associe à chaque valeur propre un `Subspace` (dimension = multiplicité géométrique, base au format de `ConfigState.basis_format`).
2. **Le changement de base de la phase 7 est réutilisé** : `diagonalize()` renvoie $P$ et $D$ et la trace montre $D = P^{-1} A P$ avec le rappel du sens de passage (scénario 5 du référentiel : $A = \begin{bmatrix} 2&1 \\ 1&2 \end{bmatrix}$, valeurs propres 1 et 3).
3. **Puissances** : $A^n$ par diagonalisation ($P D^n P^{-1}$, $n$ symbolique), sinon par $\lambda I + N$ avec $N$ nilpotente (blocs de Jordan), sinon produits successifs.

| N° | Étape |
|:-----:|:-----------------------------------|
| 8.1 | `CharacteristicPolynomial(A)` par Bareiss, $\lambda$ indéterminée du moteur, factorisation sur $\mathbb{Q}$ (et selon `factor_policy`). |
| 8.2 | `Eigen(A)` : valeurs propres réelles et multiplicités ; partie sans racine réelle signalée ; racines non explicites renvoyées comme facteurs irréductibles. |
| 8.3 | Espaces propres comme `Subspace` ; diagnostic « multiplicité géométrique < multiplicité algébrique ». |
| 8.4 | Discussion selon un paramètre (discriminant ou résultant des facteurs de $\chi_A$). |
| 8.5 | `diagonalize()`, `power(n)`, vérification tracée $AP = PD$. |
| 8.6 | Tuteur : thème « Valeurs propres et diagonalisation », 5 fiches ; vérificateurs `couple_propre` et `diagonalisation`. |
| 8.7 | Tests (comparaison avec `eigenvects()`, Jordan, symétriques, rotations, $\begin{bmatrix} 1&a \\ 0&1 \end{bmatrix}$, $A^n$ pour $n = 0, \dots, 8$) et documentation. |

Critère de fin : version **0.3.3.0**.

# 11. Phase 9 — Familles structurées (« régime 2 »)

**Objectif** : reconnaître la structure d'une matrice et appliquer la méthode qui lui convient, avec une explication conceptuelle, au lieu de dérouler une élimination illisible.

## 11.1 Étapes

| N° | Étape | Détail |
|:-----:|:-----------------------------------|:-----------------------------------|
| 9.1 | Détecteurs (`structure/`) | Prédicats exacts, qui tiennent compte de l'oracle (une structure peut ne valoir que sous condition : $P^2 = P$ seulement si $a = 0$) : `is_block_triangular`, `is_tridiagonal`, `is_scalar_plus_rank_one` ($\alpha I + u v^T$, dont $aI + bJ$), `is_vandermonde`, `is_companion`, `is_projector`, `is_involution`, `is_antisymmetric`, `is_centrosymmetric`, `is_stochastic`, `is_triangular`, `is_diagonal`. |
| 9.2 | Diagnostic de structure | `A.structure()` : structures reconnues, méthode conseillée et raison didactique. L'avertissement de l'étape 3.5 cite la structure reconnue ou, à défaut, invite à en chercher une. |
| 9.3 | Méthodes dédiées | Par ordre de priorité (§ 11.2), chacune tracée, avec son explication et une vérification par la méthode générale sur les petites tailles. |
| 9.4 | Routage | `method="auto"` de `Determinant`, `GaussJordan`, `Eigen` consulte `structure()` et choisit la méthode dédiée ; `method="elimination"` reste toujours possible. Le routage change des sorties : commit dédié, références relues. |
| 9.5 | Tuteur : thème « Reconnaître une structure » | Fiches où la réponse attendue est d'abord la **méthode** (vérificateur `choix_methode`), puis le résultat : déterminant d'une tridiagonale par récurrence, inverse de $aI + bJ$, rang d'un projecteur par la trace, déterminant d'une antisymétrique de taille impaire. |
| 9.6 | Mesures | Temps et tailles d'expressions comparés à l'étape 3.1 sur les 6 familles de `test4`. |

## 11.2 Priorités des méthodes dédiées

| Ordre | Famille | Méthode | Raison de la priorité |
|:-----:|:----------------------|:----------------------------|:----------------------------|
| 1 | Bloc-triangulaire | $\det$ = produit des déterminants des blocs ; résolution bloc par bloc | supprime l'explosion de branches de `test4` |
| 2 | Tridiagonale | récurrence $D_n = a D_{n-1} - bc\, D_{n-2}$ ; résolution par substitution | très fréquente (L1–L2, CPGE) ; pivots de Chebyshev de `test4` |
| 3 | $\alpha I + u v^T$ ($aI + bJ$) | Sherman-Morrison ; spectre $a - b$ (ordre $n - 1$) et $a + (n-1)b$ | classique des concours ; fractions bivariées de `test4` |
| 4 | Vandermonde | $\det = \prod_{i<j} (x_j - x_i)$, interpolation de Lagrange | lien avec les polynômes |
| 5 | Compagnon | $\chi_A = \pm P$ ; suites récurrentes linéaires | pont entre polynômes et réduction |
| 6 | Projecteur, involution | $\operatorname{rg} P = \operatorname{Tr} P$, $\mathbb{R}^n = \ker P \oplus \operatorname{Im} P$ ; $S = 2P - I$ | s'appuie sur les sous-espaces (phase 7) |
| 7 | Antisymétrique | $\det = 0$ en taille impaire ; Pfaffien en taille paire | classique des concours |
| 8 | Centro-symétrique | découplage en deux blocs de taille $\lfloor n/2 \rfloor$ | changement de base (phase 7) |
| 9 | Stochastique | $\mathbf 1$ vecteur propre pour 1 ; chaîne de Markov à long terme | s'appuie sur les valeurs propres (phase 8) |

Critère de fin : familles 1 à 5 au moins livrées avec fiches et documentation ; version **0.3.4.0**.

# 12. Phase 10 — Extensions ultérieures

| Piste | Description | Dépend de |
|:----------------------------|:----------------------------|:-----------:|
| Corps $\mathbb{C}$ | Option `field="C"` : valeurs propres complexes, diagonalisation sur $\mathbb{C}$. | phase 8 |
| Circulantes | Diagonalisation dans la base de Fourier, valeurs propres par la transformée de Fourier discrète de la première ligne. | $\mathbb{C}$ |
| Toeplitz, Hankel, Cauchy, Hilbert | Formule de Cauchy pour le déterminant ; Hilbert comme exemple de mauvais conditionnement (avec `compare`). | phase 9 |
| Exercices paramétrés par graine | Données générées à partir d'une graine (numéro d'étudiant). | phase 6 |
| Géométrie de $\mathbb{R}^2$ et $\mathbb{R}^3$ | Droites et plans comme sous-espaces affines, intersections, distances, figures 3D. | phase 7 |
| Factorisation LU (avec permutation) | Tracée, reliée aux substitutions triangulaires. | phase 4 |
| Espaces autres que $\mathbb{R}^n$ | Polynômes $\mathbb{R}_n[X]$, matrices $M_n(\mathbb{R})$, via les coordonnées dans une base. | phase 7 |
| Rejeu de trace dans JupyterLab, générateur de sujets LaTeX/PDF, parcours adaptatif, locale anglaise | Pistes du plan v5, inchangées. | — |

# 13. Calendrier et dépendances

```text
Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 7 ──► Phase 8 ──► Phase 9 ──► Phase 10
(correctifs) (moteur)  (Matrix)  (sous-espaces) (valeurs   (structures)
   │                               ▲            propres)
   └──────► Phase 6 (tuteur, en parallèle de 3 à 5) ┘
```

| Ordre | Phase | Séances | Jalon | Version |
|:-------:|:--------|:--------:|:-------------------------------------------|:------:|
| 1 | Phase 3 | 1–2 | campagnes figées, factorisation cohérente, messages de plafond | 0.3.1.1 |
| 2 | Phase 4 | 3–4 | moteur commun, noyau tracé, regroupement des branches | — |
| 3 | Phase 5 | 1 | `Matrix` < 600 lignes, registre de procédures | — |
| 4 | Phase 6 | 2 | tuteur découpé, plus d'`eval`, API française | 0.3.1.2 (PyPI reporté) |
| 5 | Phase 7 | 4–5 | `Subspace`, Zassenhaus, changement de base, thème 10 | 0.3.2.0 |
| 6 | Phase 8 | 3–4 | `Eigen`, `diagonalize()`, 5 fiches | 0.3.3.0 |
| 7 | Phase 9 | 3–4 | détecteurs, méthodes dédiées 1 à 5, thème « structures » | 0.3.4.0 |

Total indicatif : **17 à 22 séances** jusqu'à la version 0.3.4.0.

# 14. Risques et parades

| Risque | Probabilité | Impact | Parade |
|:----------------------------|:-------:|:----:|:----------------------------|
| Régression invisible pendant les refactorisations | moyenne | fort | Tests de caractérisation, campagnes du bac à sable figées (3.1), commits atomiques. |
| Regroupement qui masque une différence didactique | faible | faible | Regroupement limité aux niveaux 0 et 1 et aux résumés identiques ; traces distinctes au niveau 2. |
| Objets de la phase 7 valables seulement dans le cas générique | forte | fort | Principe « tout objet accepte les paramètres » (§ 4) ; tests paramétrés systématiques ; aucune comparaison `== 0` hors oracle. |
| Base entière fausse pour une valeur du paramètre | moyenne | fort | Tout facteur de mise à l'échelle rejoint la condition de la branche (7.2). |
| Erreur reprise d'un document externe | moyenne | moyen | Exemples recalculés avant usage (§ 3.2, § 4). |
| Détecteur de structure trop permissif | moyenne | fort | Prédicats exacts par l'oracle ; méthode dédiée vérifiée par la méthode générale sur $n \le 4$. |
| Avertissement de taille perçu comme un refus | faible | moyen | Avertissement seulement, désactivable ; message qui oriente vers `structure()`. |
| Explosion de la taille des expressions | forte | moyen | Bareiss, pivots qui préservent les zéros (4.9), méthodes dédiées (phase 9). |
| Racines non explicites (degré ≥ 3) | forte | moyen | Politique du plan v5 (§ 10.2) : facteurs irréductibles renvoyés tels quels. |
| Import circulaire (registre, `Subspace` ↔ `Matrix`) | faible | moyen | Registre alimenté par `algorithms/__init__.py` ; `Subspace` n'importe `Matrix` que par le registre. |

# 15. Décisions

## 15.1 Décisions prises (21 octobre 2026)

1. Le plan v6 remplace le plan v5 à partir de la version 3.1.0.
2. Corrections issues des campagnes de tests **avant** l'extraction du moteur.
3. Sous-espaces (0.3.2.0) **avant** valeurs propres (0.3.3.0) ; familles structurées ensuite (0.3.4.0).
4. Règle des deux régimes : **avertissement réglable** au-delà de `max_generic_dim = 4`, jamais de refus de calcul.
5. Priorité des familles structurées selon leur fréquence dans les cours (§ 11.2) ; circulantes reportées avec $\mathbb{C}$.
6. `nullspace()` garde son type de retour ; les `Subspace` arrivent par de nouvelles méthodes (`kernel()`, `image()`, `rowspace()`).
7. Une seule option de format des bases (`basis_format`).
8. Décisions du plan v5 maintenues : $\mathbb{R}$ seul jusqu'à la phase 10, Bareiss par défaut avec paramètres, français comme API documentée du tuteur, PyPI à partir de la fin des refactorisations.

Réponses aux questions laissées ouvertes par la première rédaction du plan v6 :

9. **Langue du cœur de l'API** : noms anglais, cohérents avec `rref()`, `rank()`, `nullspace()`, `det()` (`kernel()`, `image()`, `rowspace()`, `Subspace.span()`…), avec des **alias français documentés** (`noyau()`, `espace_lignes()`, `Subspace.engendre()`…). Les valeurs des options de `ConfigState` restent en anglais. Le tuteur garde le français comme API principale.
10. **`factor_policy`** : `"real_radicals"` par défaut **dès 0.3.1.1** ; la factorisation sur $\mathbb{Q}(\sqrt d)$ ne s'applique que lorsque la condition de la branche contient $\sqrt d$. `"rational"` reste disponible.
11. **Fusion des branches** : `merge_branches=True` par défaut, désactivable ; les traces des branches fusionnées restent consultables. *Révisée le 21 octobre 2026 après mesure* : regroupement à l'affichage seulement (étape 4.8) ; le plafond de la bloc-triangulaire 6 × 6 relève de la méthode par blocs (étape 9.3).
12. **Format des bases** : `basis_format="canonical"` par défaut (fidèle à la méthode enseignée et à la trace) ; `"integer"` et `"orthonormal"` sur demande ; le tuteur accepte toute base correcte.
13. **Alias anglais du tuteur** (`tutor`, `verify_*`…) : silencieux en 0.3.1.2, `DeprecationWarning` à partir de 0.3.2.0, suppression en 0.4.0.0.

## 15.2 Questions encore ouvertes

Aucune à ce jour.

# 16. Définition de « terminé » (pour chaque étape)

- [ ] Tests unitaires et de caractérisation verts (`pytest`), carnets exécutés sans erreur (`python verifier_tout.py`).
- [ ] `valider_fiche` valide toutes les fiches (et les nouvelles).
- [ ] `ruff` sans erreur ; `mypy --strict` sans erreur sur son périmètre bloquant, étendu aux nouveaux modules.
- [ ] Toute référence régénérée a été relue (diff commenté dans le message de commit).
- [ ] Exemples mathématiques recalculés (documentation, fiches, tests).
- [ ] Documentation Markdown mise à jour, site HTML régénéré (`python scripts/build_docs_site.py`), liens vérifiés.
- [ ] `CHANGELOG.md` complété.
- [ ] CI verte sur GitHub.

# Annexe A — Point de reprise pour la prochaine séance

1. Tâche 3.1 **faite** : 21 cas reconstruits et figés (`tests/campagnes.py`, `docs/dev/campagnes.md`), mesures de référence dans `docs/dev/mesures/campagnes_3.1.0.json`.
2. Tâche 3.2 **faite** : `config.factor_policy` (`"real_radicals"` par défaut), `Condition.radicals()`, `Condition.reduce()` ; témoins réduits par la condition de la branche ; tests dans `tests/test_factorisation.py`.
3. Tâche 3.3 **faite** : complétion des carrés pour les polynômes de degré 2 à plusieurs paramètres (`sum_of_squares`, `strict_sign` dans `core/zero.py`) ; tests dans `tests/test_signe_constant.py`.
4. Tâche 3.4 **faite** : `CaseLimitError` et `case_limit_error` (`core/zero.py`) ; message en Python comme les autres exceptions, `core` ne pouvant pas lire la locale de `render` ; tests dans `tests/test_plafonds.py`.
5. Tâche 3.5 **faite** : `PedagogicalWarning` et `config.max_generic_dim` ; tests dans `tests/test_avertissement_taille.py`. **Phase 3 terminée : version 0.3.1.1** (étiquette `v0.3.1.1`).
6. Phase 4, tâche 4.1 **faite** : `algorithms/elimination.py` (fonctions pures et `_choose_pivot`), aucune sortie modifiée.
7. Tâche 4.2 **faite** : `RowOps` dans `elimination.py` ; traces du déterminant ajoutées aux tests de caractérisation.
8. Tâches 4.3 et 4.4 **faites** : `EliminationEngine`, `SplitRequest` ; `GaussJordan` réécrit sur le moteur (`_setup`, `_complete`), 496 lignes (objectif < 400 à reprendre avec l'extraction du noyau, étape 4.7).
9. Tâche 4.5 **faite** : élimination du déterminant sur le moteur, avec discussion par cas ; Bareiss garde sa boucle (il n'ouvre jamais de discussion) et partage `RowOps`.
10. Tâche 4.6 **faite** : `tests/test_elimination.py` (12 tests). Fin de la partie refactorisation de la phase 4.
11. Tâche 4.7 **faite** : `kernel_basis`, `trace_kernel`, clés `ker.*` ; noyau affiché pour une réduction sans second membre et pour une solution affine.
12. Tâche 4.8 **faite** (révisée) : regroupement à l'affichage (`group_branches`, `format_conditions_text` dans `render/text.py`).
13. Tâche 4.9 **faite** : `pivot_strategy="sparse"`, `reduction="back_substitution"`, mesures dans `docs/dev/campagnes.md` ; réglages par défaut conservés. **Phase 4 terminée.**
14. Phase 5 **faite** : registre `_procedures`, `algorithms/products.py`, `matrix.py` à 599 lignes, `docs/dev/architecture.md`.
15. Phase 6 **faite** (6.0 à 6.7) : registre des vérificateurs (`tuteur/registre.py`), un module par vérificateur (`tuteur/verificateurs/`), `catalogue.py` / `seance.py` / `validation.py`, interpréteur sûr `tuteur/evaluation_sure.py` à la place des `eval`, code dans `tuteur/` et `tutor/` en réexportation ; état des lieux dans `docs/dev/tuteur_etat_des_lieux.md`. Hors plan : traces en tableau (`explain().to_table()`).
16. **Version 0.3.1.2** (étiquette `v0.3.1.2`) : phases 4, 5 et 6. **Publication sur PyPI reportée** (décision du 21 octobre 2026).
17. Prochaine étape : phase 7 (bases et sous-espaces), tâche 7.1.

# Annexe B — Esquisse de l'API cible (version 0.3.4)

```python
from linalg_pedagopy import Matrix, Vector, Subspace, symbols

m, = symbols("m")
A = Matrix([[1, 1, m], [1, m, 1], [m, 1, 1]])
A.kernel()                      # CaseSplit : {0} si m ∉ {1, −2} ; droite si m = −2 ; plan si m = 1
A.rank_nullity()                # tableau : rang 3 / 2 / 1, noyau 0 / 1 / 2, somme 3 dans chaque branche
A.nullspace(format="integer")   # tuple de vecteurs, comme en 3.1 (compatibilité)

B = Matrix([[1, 2, 1], [2, 4, 2], [1, 1, 0]])
B.image()                       # colonnes 1 et 2 de B d'origine (pas celles de la forme réduite)
B.rowspace()                    # lignes non nulles de la forme réduite

F = Subspace.span([Vector([1, 2, 1]), Vector([-1, 0, 3])])
F.equations()                   # 3x − 2y + z = 0
G = Subspace.span([Vector([0, 0, 1])])
F.is_supplementary(G)           # True
F.decompose(Vector([1, 1, 1]), G)

U = Subspace.span([Vector([1, 0, 1, 0]), Vector([0, 1, 1, 1])])
W = Subspace.kernel(Matrix([[1, 0, 0, -1]]))
U + W, U & W                    # Zassenhaus tracé, Grassmann vérifiée
A.noyau(), B.espace_lignes()    # alias français documentés

C = Matrix([[2, 1], [1, 2]])
P, D = C.diagonalize()          # espaces propres comme Subspace ; D = P⁻¹ C P tracé

a, b = symbols("a b")
E = (a - b) * Matrix.identity(5) + b * Matrix.ones(5, 5)
E.structure()                   # « a I + b J : perturbation de rang 1 » → Sherman-Morrison
E.det()                         # (a − b)**4 * (a + 4b), sans élimination
```
