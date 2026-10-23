"""Réglages centralisés du scraper Amazon."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AMAZON_URL = "https://www.amazon.fr"
CATEGORY_QUERIES = {
    "Livres": "livres",
    "Informatique": "ordinateur portable",
    "Cuisine": "ustensiles de cuisine",
}
PAGES_MAX = 3  # maximum par catégorie (neuf pages de résultats au plus au total)
DELAI_ENTRE_PAGES = (3, 6)  # délai aléatoire entre les navigations Selenium
TIMEOUT = 35
HEADLESS = True
CSV_PATH = BASE_DIR / "exports" / "produits.csv"

