# Amazon Scraper — mini-projet Selenium

Projet Python de web scraping Amazon.fr organisé selon l'arborescence du professeur. Selenium ouvre les pages dans Chrome et lit les éléments avec des sélecteurs CSS. Le projet n'utilise ni Requests ni BeautifulSoup.

## Fonctionnement

- effectue trois recherches Amazon, une par catégorie configurée;
- suit le lien « page suivante » sur chaque recherche jusqu'à trois pages au maximum;
- attend un délai aléatoire entre chaque navigation;
- récupère titre, prix, note, disponibilité et lien depuis les cartes de résultats;
- écrit les données dans exports/produits.csv;
- affiche la moyenne des prix, le prix maximum et le nombre de produits par catégorie.

La catégorie correspond au groupe de recherche défini dans config.py (Livres, Informatique, Cuisine). Les notes ou prix absents restent vides dans le CSV; les prix absents sont exclus des statistiques de moyenne et de maximum.

## Installation dans VS Code (Windows)

Prérequis : Python 3.10+, Google Chrome et l'extension Python de Microsoft dans VS Code.

1. Ouvre ce dossier dans VS Code.
2. Dans Terminal > Nouveau terminal, exécute :

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python main.py

Si PowerShell bloque l'activation : Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass puis réessaie. Au besoin, Ctrl+Shift+P > Python: Select Interpreter et sélectionne l'interpréteur .venv.

Selenium Manager prépare le pilote Chrome au premier lancement; Chrome et une connexion Internet sont nécessaires. Le CSV est exports/produits.csv.

## Configuration

Dans config.py, CATEGORY_QUERIES associe les catégories aux termes de recherche, PAGES_MAX fixe le maximum de pages à suivre pour chaque recherche, DELAI_ENTRE_PAGES règle la pause et HEADLESS permet de masquer/afficher Chrome (Chrome est visible par défaut pour faciliter le diagnostic).

## Arborescence du professeur

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

Le contrôleur orchestre le flux; les modèles représentent les données et leur sauvegarde CSV; le scraper suit la pagination et extrait les éléments; le driver pilote Selenium; les vues présentent les résultats.

## Accès au site

Amazon peut refuser une session automatisée ou modifier le HTML. Chrome reste visible par défaut pour que tu puisses voir la page chargée. Le programme s'arrête avec un diagnostic s'il ne détecte pas les cartes; il ne contourne pas une vérification. Vérifie que l'accès est autorisé pour le devoir.

Pour lancer les tests de parsing et de statistiques : python -m unittest discover -s tests.

