# Changelog — `linalg_pedagopy`

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
- **Couverture du recueil VMLS** : 33 exercices couverts complètement (`●`) + exercices `3.3` et `3.13` illustrant le laboratoire de contre-exemples, accompagnés d'un glossaire anglais–français intégré.
- **Architecture formelle complète (D1–D11)** :
  - Corps de travail $\mathbb{R}$ (`real=True`, D1) et politique de coercition des flottants (`float_policy`, D2) ;
  - Oracle de nullité à 4 verdicts (`ZERO`, `NONZERO`, `CONDITIONAL`, `UNKNOWN`, D3) et discussion par cas (`CaseSplit`, D4) ;
  - Objets `Vector` et `Matrix` immuables (D5) appuyés sur `DomainMatrix` (D10) ;
  - Traceur contextuel arborescent (`tracing`, `section`, `record`) à 4 niveaux (D6) et moteurs de rendu découplés (`text`, `latex`, `markdown`, `html`, D7) ;
  - Résultats typés (`GJResult`, `SolutionSet`, `GSResult`, `QRResult`, `LSResult`, D8) et pivot le plus simple (D11) ;
  - Modules `exercises` (générateurs exacts par matrices unimodulaires, transformée de Cayley, etc.), `compare` (exact vs flottant, matrice de Läuchli, Hilbert) et `plot` (figures 2D/3D).
