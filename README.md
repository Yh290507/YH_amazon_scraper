# Amazon Scraper — mini-projet Selenium

Projet Python de web scraping Amazon.fr organisé selon l'arborescence du professeur. Selenium ouvre les pages dans Chrome et lit les éléments avec des sélecteurs CSS. Le projet n'utilise ni Requests ni BeautifulSoup.

## Fonctionnement

- effectue trois recherches Amazon, une par catégorie configurée;
- suit le lien « page suivante » sur chaque recherche jusqu'à trois pages au maximum;
- attend un délai aléatoire entre chaque navigation;
- récupère ASIN, titre, prix, note, disponibilité et lien depuis les cartes de résultats;
- conserve dans le CSV uniquement les fiches avec un titre, un prix, une note et un lien; les fiches incomplètes sont comptées dans le terminal puis ignorées;
- écrit les données dans exports/produits.csv, avec des en-têtes français, la catégorie et l'ASIN en tête, et les produits regroupés par catégorie;
- affiche la moyenne des prix, le prix maximum et le nombre de produits par catégorie;
- propose un menu pour lancer le scraping, relire les statistiques du CSV ou quitter.

Les catégories sont définies dans config.py : Livres, Informatique et Cuisine. Chaque produit est classé selon la recherche qui l'a trouvé. Une fiche sans prix, sans note ou sans lien produit n'est pas enregistrée, afin que les lignes du CSV utilisées pour les statistiques soient complètes. La disponibilité reste renseignée par « Non indiqué » quand Amazon ne l'affiche pas.

Dans le CSV, l'ASIN est l'identifiant Amazon du produit; il est pris dans la carte de résultat ou extrait du lien déjà collecté. « Prix (€) » affiche le prix de chaque article avec le symbole euro (par exemple `22,92 €`) et « Note (/5) » affiche sa note sur cinq (par exemple `4.2`). Le programme sait relire le prix formaté pour recalculer les statistiques. La colonne « Disponibilité » contient le texte de livraison affiché par Amazon; son éventuel montant en euros correspond aux frais ou conditions de livraison, pas au prix de l'article.

## Installation dans VS Code (Windows)

Prérequis : Python 3.10+, Google Chrome et l'extension Python de Microsoft dans VS Code.

1. Ouvre ce dossier dans VS Code.
2. Dans Terminal > Nouveau terminal, exécute :

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python main.py

Le menu propose trois choix : lancer le scraping, afficher les statistiques du dernier CSV enregistré, ou quitter. L'affichage reste résumé; les détails des produits sont dans le fichier CSV.

Si PowerShell bloque l'activation : Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass puis réessaie. Au besoin, Ctrl+Shift+P > Python: Select Interpreter et sélectionne l'interpréteur .venv.

Selenium Manager prépare le pilote Chrome au premier lancement; Chrome et une connexion Internet sont nécessaires. Le CSV est exports/produits.csv.

## Configuration

Dans config.py, CATEGORY_QUERIES associe chaque catégorie à son terme de recherche, PAGES_MAX fixe le maximum de pages à suivre pour chaque recherche, DELAI_ENTRE_PAGES règle la pause aléatoire entre navigations et HEADLESS=True masque Chrome par défaut. Passe HEADLESS à False pour voir le navigateur pendant le diagnostic.

## Arborescence

    README.md
    app/
      __init__.py
      controllers/__init__.py, scraping_controller.py
      models/__init__.py, depot.py, produit.py
      scraper/__init__.py, amazon_scraper.py, driver.py, parsing.py
      views/__init__.py, console_view.py, export_view.py
    config.py
    data/
    exports/
    main.py
    requirements.txt
    tests/__init__.py

Le contrôleur orchestre le flux; les modèles représentent les produits et calculent les statistiques; le dépôt lit et écrit le CSV; le scraper suit la pagination par catégorie et extrait les éléments; le driver pilote Selenium; les vues gèrent le menu et les résultats affichés.

## Accès au site

Amazon peut refuser une session automatisée ou modifier le HTML. Chrome est masqué par défaut; passe HEADLESS à False dans config.py pour voir la page chargée pendant le diagnostic. Le programme s'arrête avec un diagnostic s'il ne détecte pas les cartes; il ne contourne pas une vérification. Vérifie que l'accès est autorisé pour le devoir.

## Tests

Depuis la racine du projet, lance les tests de parsing et de statistiques avec :

```powershell
python -m unittest discover -s tests
```

