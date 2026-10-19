# 04. Le tuteur interactif (`tutor` / `tuteur`)

Le module [`linalg_pedagopy.tutor`](../src/linalg_pedagopy/tutor/__init__.py), aussi accessible sous le nom français [`linalg_pedagopy.tuteur`](../src/linalg_pedagopy/tuteur/__init__.py), accompagne un étudiant sur une banque de **35 exercices nommés**. Il l'aide à trouver la méthode **sans jamais donner la solution** : indices gradués, exercice analogue résolu, laboratoire de contre-exemples et diagnostic précis des réponses fausses.

---

## 1. Principes pédagogiques

| Principe | Mise en œuvre |
| :--- | :--- |
| Vérifier par propriété, pas par corrigé figé | Toute réponse correcte est acceptée (par ex. n'importe quelle inverse à droite valable). |
| Diagnostiquer ce que calcule la réponse | « Votre ligne 2 calcule d₂ = p₄ − (p₁ + p₂ + p₃)/3 » plutôt que « faux ». |
| Aide graduée | 4 paliers : orientation, outil, démarrage, exercice jumeau résolu. Pas de palier « solution ». |
| Transposer une méthode | Le palier 4 résout un exercice **analogue** (autres données), à transposer. |
| Données verrouillées | Les vecteurs et matrices de l'énoncé ne peuvent pas servir à calculer la réponse à la place de l'étudiant tant que l'exercice n'est pas résolu. |
| S'engager avant d'explorer | Pour un vrai/faux, il faut enregistrer une prédiction avant d'ouvrir le laboratoire. |
| Un essai ne prouve pas un « toujours vrai » | Le laboratoire le rappelle et demande une justification. |
| Transparence | Un journal local garde la trace de la séance ; aucune note n'est calculée. |

---

## 2. Trouver un exercice : le catalogue

Chaque exercice a un **numéro** (1 à 35), un **identifiant** lisible, un **titre**, un **thème** et un **niveau** (★ à ★★★). La liste complète figure dans le [catalogue des exercices](08_catalogue_exercices.md).

```python
from linalg_pedagopy import tutor

cat = tutor.catalog()          # tableau Markdown dans JupyterLab
print(cat)                     # version texte, groupée par thème
print(len(cat))                # 35

print(tutor.themes())          # les 8 thèmes, dans l'ordre du cours
print(tutor.list_exercises("convolution"))   # ['convolution-vecteurs', 'produit-polynomes']

tutor.catalog("Inverses")      # filtrer par (partie du) thème
```

Un exercice s'ouvre par son identifiant, son numéro ou son titre exact. Une faute de frappe donne une suggestion :

```python
ex = tutor.exercise("moyenne-glissante")       # par identifiant
ex = tutor.exercise(16)                        # par numéro
ex = tutor.exercise("Écart à la moyenne glissante")   # par titre

try:
    tutor.exercise("moyene-glissante")
except Exception as err:
    print(err)   # Exercice 'moyene-glissante' introuvable. Vouliez-vous dire : moyenne-glissante ? ...
```

Les attributs `ex.id`, `ex.number` (alias `numero`), `ex.title` (alias `titre`), `ex.theme`, `ex.level` (alias `niveau`), `ex.type` et `ex.notions` décrivent l'exercice.

---

## 3. Une séance pas à pas

### 3.1 Lire l'énoncé

```python
ex = tutor.exercise("moyenne-glissante")
ex.statement()          # dans JupyterLab : rendu Markdown + LaTeX
print(ex.statement())
```

```text
### Exercice 16 — Écart à la moyenne glissante

*Matrices et applications linéaires · modélisation · niveau ★★☆*

$p \in \mathbb{R}^6$ est une série de prix. $d \in \mathbb{R}^3$ mesure, à partir du 4ᵉ jour, …
```

### 3.2 Demander de l'aide : les 4 paliers

Chaque appel à `ex.hint()` (alias `ex.indice()`) débloque le palier suivant :

| Palier | Titre | Exemple (exercice 16) |
| :---: | :--- | :--- |
| 1 | Orientation | « Quelle est la taille de $d$ ? celle de $p$ ? Qu'en déduisez-vous pour $A$ ? » |
| 2 | Outil | « La ligne $i$ de $A$ contient les coefficients de $d_i$ exprimé en fonction de $p_1, \dots, p_6$. » |
| 3 | Démarrage | « Écrivez $d_1$ en fonction des $p_j$, puis lisez ses coefficients. » |
| 4 | Exercice jumeau résolu | Résolution complète d'un exercice analogue (fenêtre de 2 jours, série de 5 prix). |

```python
print(ex.hint())     # **[Niveau 1 — Orientation]** …
print(ex.hint())     # **[Niveau 2 — Outil]** …
print(ex.hint(1))    # relire un palier déjà débloqué
```

Quand les quatre paliers sont débloqués, `ex.hint()` le dit et rappelle comment relire un palier, consulter le jumeau ou repartir de zéro. On ne peut pas sauter de palier : `ex.hint(3)` avant le palier 2 débloque le palier 2.

Pour imposer de l'effort entre deux indices, l'enseignant peut régler `config.hint_min_attempts` (nombre de tentatives) et `config.hint_min_delay_seconds` (délai).

### 3.3 L'exercice jumeau

```python
jumeau = ex.twin()        # alias ex.jumeau()
print(jumeau.title)       # Écart à la moyenne glissante (fenêtre $k=2$, $n=5$)
jumeau                    # dans JupyterLab : énoncé analogue + résolution pas à pas
```

`twin()` renvoie un `TwinExercise` (`title`, `statement`, `solution_summary`, `explanation`) et débloque le palier 4.

### 3.4 Soumettre une réponse

`ex.verify(reponse)` (alias `ex.verifier`) renvoie un `VerificationResult` immuable : `valid`, `diagnostic` et, pour certains contre-exemples, `simplicity_note`.

```python
from fractions import Fraction
from linalg_pedagopy import Matrix

t = Fraction(1, 3)
fausse = Matrix([[-t, -t, -t, 1, 0, 0],
                 [-t, -t, -t, 1, 0, 0],
                 [0, 0, -t, -t, -t, 1]])
r = ex.verify(fausse)
print(r.valid)        # False
print(r.diagnostic)
# Taille correcte (3 x 6). Lignes 1 et 3 correctes.
# Votre ligne 2 calcule d_2 = p_4 - (p_1 + p_2 + p_3)/3.
# Relisez la définition de d_2 : quel est le prix « du jour » pour i = 2 ?
```

Une réponse de forme inattendue (une liste à la place d'une matrice, par exemple) ne provoque pas d'erreur Python : le diagnostic indique la forme attendue. Une réponse correcte affiche « ✓ Réponse validée » et **déverrouille les données** de l'exercice.

### 3.5 Vrai ou faux : prédiction puis laboratoire

```python
from linalg_pedagopy import Vector

ex12 = tutor.exercise("orthogonalite-vrai-faux")
print(ex12.predict(a="peut être faux", b="toujours vrai", c="peut être faux"))

lab = ex12.lab()          # impossible avant predict(...)
rapport = lab.test(a=Vector([1, 0, 0]), b=Vector([1, 1, 0]), c=Vector([0, 0, 1]))
print(rapport.found_counterexample)   # True
print(rapport.message)
```

`lab.test(**instances)` renvoie un `LabReport` : `hypotheses_satisfied`, `results_by_part`, `found_counterexample`, `message`.

### 3.6 Bilan et reprise

```python
print(ex.summary())       # alias ex.bilan()
```

```text
**Bilan — Écart à la moyenne glissante**

- Statut : en cours
- Tentatives soumises : 1
- Paliers d'indices consultés : 1, 2
- Exercice jumeau consulté : non
- Essais au laboratoire : 0
- Temps passé : 95 s
- Dernier diagnostic : …
```

La progression est enregistrée dans un journal JSON (`config.journal_path`, par défaut `.linalg_pedagopy_journal.json` dans le dossier du carnet). En rouvrant l'exercice plus tard, on retrouve ses indices et ses tentatives. Pour repartir de zéro sur un exercice :

```python
ex.reset()                # alias ex.recommencer()
```

---

## 4. Le panneau JupyterLab

```python
ex.panel()                # alias ex.panneau()
```

Avec `ipywidgets` installé (extra `tuteur`), le panneau affiche :
- l'énoncé rendu en LaTeX ;
- les boutons **Indice suivant**, **Relire le palier…**, **Exercice jumeau** et **Bilan** ;
- une zone de réponse (par exemple `Matrix([[1, 0], [0, 1]])` ou `Vector([1, 2])`) et un bouton **Vérifier** ;
- une zone de retour où s'affichent indices, jumeau, diagnostic et bilan.

La zone de réponse n'accepte que `Vector`, `Matrix`, `sqrt`, `Rational`, `pi`, des nombres, listes, tuples, dictionnaires et chaînes. Sans `ipywidgets`, `panel()` affiche l'énoncé et le bilan en Markdown.

---

## 5. Le glossaire

```python
print(tutor.glossary("least squares"))   # **least squares** → Moindres carrés : …
print(tutor.glossary("noyau"))           # recherche aussi en français
tutor.glossary()                          # liste des 40 termes
```

---

## 6. Mode enseignant

```python
tutor.mode("teacher")            # ou "enseignant" ; équivalent : config.tutor_mode = "teacher"
ex = tutor.exercise("moyenne-glissante")
fiche = ex.teacher_sheet()       # TeacherSheet : la fiche complète (cible, indices, jumeau)
print(fiche["verification"]["cible"])
fiche                            # dans JupyterLab : rendu Markdown de la fiche
tutor.mode("student")            # ou "etudiant"
```

En mode étudiant, `teacher_sheet()` lève `PermissionError`. En mode enseignant, les données des exercices sont déverrouillées.

---

## 7. Protection contre les contournements

Dans un carnet, l'étudiant dispose de tout Python. Le tuteur empêche les raccourcis les plus directs :
- la fiche, la cible et l'état de la séance sont rangés dans des dictionnaires privés à clés faibles (`WeakKeyDictionary`) du module, pas sur l'objet `ex` ;
- `ExerciseSession`, `LockedVector`, `LockedMatrix` et `LockedNamespace` définissent `__slots__ = ("__weakref__",)` : pas de `__dict__` à inspecter, et toute affectation d'attribut est refusée ;
- tant que l'exercice n'est pas résolu, `ex.data.x.rms()`, `Vector(ex.data.x)` ou `ex.data.x[0]` lèvent `LockedExerciseDataError`.

Ce n'est pas une protection cryptographique : un étudiant déterminé peut lire les fichiers YAML. Le but est d'éviter que la réponse s'obtienne par une simple ligne de code.

---

## 8. Les fiches d'exercices

Les fiches sont des fichiers YAML dans [`src/linalg_pedagopy/tuteur/fiches/`](../src/linalg_pedagopy/tuteur/fiches/), un par exercice, nommés d'après leur identifiant.

```yaml
id: moyenne-glissante
numero: 16
titre: Écart à la moyenne glissante
theme: Matrices et applications linéaires
niveau: 2
type: modelisation
enonce: $p \in \mathbb{R}^6$ est une série de prix. … Trouver la matrice $A$ telle que $d = A p$.
notions:
- matrice comme application linéaire
donnees: {n: 6, m: 3}
verification:
  type: matrice
  inconnue: p
  nom_sortie: d
  taille_entree: 6
  taille_sortie: 3
  cible: d[i] = p[i+3] - (p[i] + p[i+1] + p[i+2]) / 3
indices:
- Quelle est la taille de $d$ ? celle de $p$ ? Qu'en déduisez-vous pour $A$ ?
- La ligne $i$ de $A$ contient les coefficients de $d_i$ …
- Écrivez $d_1$ en fonction des $p_j$, puis lisez ses coefficients.
jumeau: generateurs.moyenne_glissante(fenetre=2, n=5)
```

| Champ | Rôle |
| :--- | :--- |
| `id` | Identifiant (identique au nom du fichier). |
| `numero` | Position dans le catalogue (unique). |
| `titre`, `theme`, `niveau` | Métadonnées affichées (niveau 1, 2 ou 3). |
| `type` | `calcul`, `modelisation`, `dimensions`, `justification`, `contre_exemple` ou `vrai_faux`. |
| `enonce`, `notions` | Texte de l'énoncé (Markdown + LaTeX) et notions mobilisées. |
| `donnees` | Données verrouillées de l'exercice. |
| `verification` | Vérificateur : `type` parmi `produit_scalaire`, `matrice`, `formule`, `valeur`, `propriete`, `contre_exemple`, `labo`, `egalites`, `dimensions`, plus ses paramètres (`cible`, `lignes_cibles`…). |
| `indices` | Au moins 3 indices textuels (paliers 1 à 3). |
| `jumeau` | Appel d'un générateur d'exercice jumeau (voir le [guide 05](05_pedagogical_exercises_and_sessions.md)). |

### Valider une fiche

`validate_sheet` (alias `valider_fiche`) contrôle une fiche : champs et métadonnées présents, numéro unique, type de vérificateur valide, jumeau exécutable, **absence de fuite** dans les indices (aucun indice ne contient la cible, ni n'est accepté comme réponse) et contrôle croisé du vérificateur avec le solveur. Elle n'écrit rien dans le journal.

```python
rapport = tutor.validate_sheet("moyenne-glissante")
print(rapport.valid, rapport.errors)       # True ()

assert all(tutor.validate_sheet(i).valid for i in tutor.list_exercises())
```

Après avoir ajouté ou modifié une fiche pendant une séance, appelez `tutor.reload_catalog()` (alias `recharger_catalogue`).
