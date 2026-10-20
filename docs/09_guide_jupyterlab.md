# 09. Utiliser le package dans JupyterLab

Ce guide pas à pas installe `linalg_pedagopy` dans un environnement dédié et l'utilise dans JupyterLab. Les commandes sont données pour **Windows avec Anaconda** ; sous macOS ou Linux, remplacez *Anaconda Prompt* par un terminal et adaptez le chemin du dossier.

Le package demande **Python 3.10 ou plus récent**.

---

## 1. Ouvrir un terminal dans le dossier du projet

Lancez **Anaconda Prompt** depuis le menu Démarrer, puis placez-vous dans le dossier du dépôt :

```bat
cd C:\chemin\vers\linalg-pedagopy
```

## 2. Créer un environnement dédié

```bat
conda create -n pedagopy python=3.12 -y
conda activate pedagopy
```

L'invite affiche alors `(pedagopy)`. Un environnement séparé évite les conflits avec les autres paquets.

## 3. Installer le package en mode éditable

```bat
pip install -e ".[tuteur,plot,compare,dev]"
```

| Extra | Contenu | Utile pour |
| :--- | :--- | :--- |
| `tuteur` | JupyterLab, ipywidgets | carnets et panneau interactif du tuteur |
| `plot` | Matplotlib | figures 2D/3D (`linalg_pedagopy.plot`) |
| `compare` | NumPy | comparaison exact / flottant (`linalg_pedagopy.compare`) |
| `dev` | pytest, hypothesis, mypy, ruff… | tests et qualité du code |

Avec `-e`, une modification du code dans `src/` est prise en compte sans réinstaller : il suffit de redémarrer le noyau du carnet.

## 4. Vérifier l'installation

```bat
pytest tests/ -q
```

Tous les tests doivent passer.

## 5. Lancer JupyterLab

```bat
jupyter lab
```

Créez un carnet (**File → New → Notebook**, noyau **Python 3**). JupyterLab ayant été lancé depuis l'environnement `pedagopy`, ce noyau est bien celui de l'environnement.

Deux carnets prêts à l'emploi sont fournis à la racine du dépôt :
- `tutoriel_linalg_pedagopy.ipynb`, généré à partir de `TUTORIAL.md` par `python convert_tutorial_to_ipynb.py` ;
- `problemes_exploratoires_linalg_pedagopy.ipynb`, généré par `python generate_exploratory_problems_ipynb.py`.
- `exercices/vecteurs_matrices.ipynb` : 20 exercices de calcul sur les vecteurs et les matrices, de difficulté croissante, avec `verifier(k, reponse)` et `indice(k)` ; corrigé dans `exercices/corrige_vecteurs_matrices.ipynb`. Ouvrez-les depuis le dossier `exercices/`. Les deux carnets se régénèrent avec `python generer_vecteurs_matrices.py`.

## 6. Premières cellules

**Import**

```python
import linalg_pedagopy as lp
lp.__version__
```

**Calcul exact et discussion de cas** : la dernière ligne d'une cellule s'affiche en Markdown et LaTeX, sans `print`.

```python
from linalg_pedagopy import Matrix, Vector, symbols, GaussJordan

a, = symbols("a")
res = GaussJordan(Matrix([[1, a], [a, 1]]), Vector([1, 1])).run()
res                         # discussion selon a, solutions en LaTeX
```

```python
res.explain(level=2)        # avec le détail des opérations de lignes
```

**Le tuteur**

```python
from linalg_pedagopy import tutor
tutor.catalog()             # les 35 exercices
```

```python
ex = tutor.exercise("moyenne-glissante")
ex.statement()
```

```python
ex.hint()                   # à répéter : paliers 1 à 4
```

```python
ex.verify(Matrix.zeros(3, 6))   # diagnostic d'une réponse fausse
```

```python
ex.panel()                  # panneau : indices, jumeau, réponse, bilan
```

**Une figure**

```python
from linalg_pedagopy import LeastSquares
from linalg_pedagopy.plot import plot_least_squares_geometry_3d

ls = LeastSquares(Matrix([[1, 0], [0, 1], [1, 1]]), Vector([1, 2, 4])).run()
plot_least_squares_geometry_3d(ls);
```

## 7. Les fois suivantes

```bat
cd C:\chemin\vers\linalg-pedagopy
conda activate pedagopy
jupyter lab
```

## 8. Dépannage

| Symptôme | Cause probable | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: linalg_pedagopy` | le noyau n'est pas celui de l'environnement | relancez `jupyter lab` après `conda activate pedagopy`, ou ajoutez `src/` à `sys.path` |
| `ex.panel()` affiche du texte au lieu de boutons | `ipywidgets` absent du noyau | `pip install -e ".[tuteur]"` puis redémarrez le noyau |
| Une modification du code n'est pas prise en compte | module déjà importé | **Kernel → Restart Kernel** |
| `ex.hint()` dit que tous les paliers sont débloqués | progression reprise depuis le journal | relisez avec `ex.hint(2)`, ou repartez de zéro avec `ex.reset()` |
| `UnknownExerciseError` | identifiant mal orthographié | le message propose l'identifiant le plus proche ; `tutor.catalog()` donne la liste |
| Une fiche modifiée n'est pas relue | catalogue mis en cache | `tutor.reload_catalog()` |

Le journal du tuteur est le fichier `.linalg_pedagopy_journal.json` du dossier du carnet (réglable par `config.journal_path`). Le supprimer remet à zéro la progression sur tous les exercices.
