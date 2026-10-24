"""Réglages centralisés du scraper Amazon."""
from pathlib import Path
import re
import unicodedata

BASE_DIR = Path(__file__).resolve().parent
AMAZON_URL = "https://www.amazon.fr"
DATA_DIR = BASE_DIR / "data"
SEARCHES_DIR = DATA_DIR / "recherches"
DB_PATH = DATA_DIR / "produits.db"
RECAP_PATH = DATA_DIR / "recap.csv"
AMAZON_SEARCH_INDEX = "electronics"  # recherche limitée au rayon électronique
PAGES_MAX = 3
MAX_PRODUCTS_PER_PAGE = 5
DELAI_ENTRE_NAVIGATIONS = (8, 15)  # pause entre les navigations Selenium
DELAI_ENTRE_IMAGES = (2, 4)  # pause entre les téléchargements d'images
TIMEOUT = 35
DETAIL_TIMEOUT = 10  # attente maximale pour le chargement d'une fiche produit
HEADLESS = True  # True pour exécuter le navigateur en arrière-plan, False pour le mode visible


def keyword_slug(keyword):
    """Convertit un mot-clé en nom de dossier sûr et lisible."""
    normalized = unicodedata.normalize("NFKD", keyword)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return (slug or "recherche")[:60].rstrip("-") or "recherche"


def collection_dir(keyword):
    return SEARCHES_DIR / keyword_slug(keyword)

