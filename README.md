# YH Amazon Scraper

Application console Python organisée en MVC. Elle recherche sur Amazon.fr avec Selenium à partir d'un mot-clé libre, classe les produits dans plusieurs catégories et enregistre les résultats dans des CSV et une base SQLite.

## Installation et lancement

Prérequis : Python 3.10+ et Google Chrome. Depuis la racine du projet, dans PowerShell :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Au démarrage, saisis le mot-clé tech de ton choix. La recherche est limitée au rayon électronique d'Amazon. Le programme lit au maximum trois pages et cinq produits par page, soit quinze produits au plus. Les fiches produit ne sont ouvertes que lorsqu'un prix ou une note manque dans les résultats. Cette limite réduit le nombre de requêtes; elle ne garantit pas qu'Amazon autorisera toujours l'accès. Si Amazon affiche une erreur ou limite l'accès, le programme s'arrête sans réessayer et conserve les produits déjà collectés. Une pause aléatoire de 8 à 15 secondes sépare les navigations, et une pause de 2 à 4 secondes sépare les téléchargements d'images.

Les produits conservés sont classés dans la catégorie `Tech`. Quand une fiche est consultée pour compléter un prix ou une note, le programme lit aussi son fil d'Ariane pour renseigner la sous-catégorie. Si le fil n'est pas disponible, la sous-catégorie reste vide. Le terminal affiche le prix moyen, le prix maximum, la note moyenne et les nombres par catégorie et sous-catégorie.

## Données enregistrées

Chaque recherche est rangée dans un dossier construit à partir du mot-clé :

```text
data/
├── produits.db
├── recap.csv
├── recherches/
│   └── mot-cle/
│       ├── produits.csv
│       └── images/
│           └── categorie/
│               └── sous-categorie/
```

- Chaque `produits.csv` contient le détail des produits d'une recherche : catégorie, sous-catégorie, mot-clé, ASIN, titre, marque et description quand ils sont visibles, prix, note, disponibilité, informations d'image et lien produit. Une nouvelle collecte avec le même mot-clé remplace son CSV détaillé.
- `produits.db` conserve l'historique de toutes les collectes et les produits associés à chacune.
- `recap.csv` ajoute une ligne par collecte avec la date, le mot-clé, la catégorie, le nombre de produits et le chemin du CSV détaillé.
- `images/` contient les images téléchargées quand leur URL est disponible, rangées par catégorie et sous-catégorie. Le chemin dans le CSV est relatif au dossier de la recherche.

Les prix affichés en euros et les notes sur 5 sont convertis en nombres lorsqu'ils sont reconnus (par exemple `1 299,99 €` et `4,5 sur 5 étoiles`). Les informations absentes restent vides. Les fiches sont conservées dès qu'un titre est lisible; une donnée manquante n'empêche pas les autres champs d'être enregistrés. Les statistiques de prix ignorent les lignes sans prix, et la note moyenne ignore celles sans note. Si Amazon n'affiche pas une valeur sur sa fiche, ou si son HTML change, le champ peut rester vide. Le programme s'arrête sans contourner une vérification Amazon.

## Organisation du code

- `main.py` démarre le programme.
- `config.py` règle le rayon Amazon, les limites de pages et de produits, les chemins de données et les délais.
- `app/controllers/` coordonne le déroulement.
- `app/models/` décrit les produits, calcule les statistiques et gère le CSV et SQLite. Lors de la prochaine sauvegarde, la colonne de sous-catégorie est ajoutée automatiquement aux bases créées avec une version antérieure du programme.
- `app/scraper/` pilote Selenium, lit les cartes de résultats et télécharge les images.
- `app/views/` gère les messages du terminal et les chemins de sortie.
