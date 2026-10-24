"""Modèle de données et statistiques des produits Amazon."""
from collections import Counter
from dataclasses import dataclass
import re
import unicodedata


TECH_TERMS = (
    "tech", "technologie", "informatique", "ordinateur", "pc", "serveur",
    "data center", "processeur", "cpu", "gpu", "carte graphique", "carte mere",
    "memoire vive", "ram", "ssd", "disque dur", "stockage", "reseau", "routeur",
    "switch ethernet", "wifi", "wi-fi", "smartphone", "telephone", "iphone",
    "android", "tablette", "ipad", "chargeur", "usb", "cable", "coque telephone",
    "casque audio", "ecouteur", "imprimante", "ecran", "moniteur", "clavier",
    "souris", "webcam", "programmation", "python", "linux", "windows", "logiciel",
    "cybersecurite", "robotique", "intelligence artificielle", "domotique", "drone",
    "montre connectee", "appareil photo", "camera", "composant", "numerique",
    "raspberry pi", "nas", "batterie externe", "console de jeu",
)
BOOK_TERMS = (
    "livre", "roman", "manga", "bande dessinee", "bd", "ebook", "e-book",
    "litterature", "poesie", "dictionnaire", "manuel", "ouvrage", "broche", "poche",
    "lecture", "science fiction",
)
GAME_TERMS = (
    "jeu", "jeux", "jeu video", "jeux video", "jeu de societe", "jeux de societe",
    "gaming", "playstation", "xbox", "nintendo", "ps5", "ps4", "manette", "puzzle",
)


def _normalized_text(value):
    decomposed = unicodedata.normalize("NFKD", value or "").casefold()
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _contains_term(text, terms):
    for term in terms:
        normalized_term = _normalized_text(term)
        words = normalized_term.split()
        pattern = r"(?<![a-z0-9])" + r"\s+".join(
            re.escape(word) + r"s?" for word in words
        ) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            return True
    return False


def classify_category(keyword, title):
    """Classe un produit avec des mots-indices; la technologie est prioritaire."""
    text = _normalized_text(f"{keyword} {title}")
    if _contains_term(text, TECH_TERMS):
        return "Tech"
    if _contains_term(text, BOOK_TERMS):
        return "Livres"
    if _contains_term(text, GAME_TERMS):
        return "Jeux"
    return "Autres"

@dataclass(frozen=True)
class Product:
    title: str
    price: float | None
    rating: float | None
    availability: str
    category: str
    url: str
    subcategory: str = ""
    asin: str = ""
    image_path: str = ""
    image_url: str = ""
    brand: str = ""
    description: str = ""
    keyword: str = ""

    @staticmethod
    def statistics(products):
        prices = [item.price for item in products if item.price is not None]
        ratings = [item.rating for item in products if item.rating is not None]
        subcategories = Counter(
            (item.category, item.subcategory)
            for item in products if item.subcategory
        )
        return {
            "average_price": sum(prices) / len(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "average_rating": sum(ratings) / len(ratings) if ratings else None,
            "by_category": dict(sorted(Counter(item.category for item in products).items())),
            "by_subcategory": dict(sorted(subcategories.items())),
            "by_keyword": dict(sorted(Counter(
                item.keyword for item in products if item.keyword
            ).items())),
        }
