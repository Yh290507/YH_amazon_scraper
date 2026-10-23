"""Enregistre les produits dans un fichier CSV."""
import csv
import re
from config import CSV_PATH
from app.models.produit import Product
from app.scraper.parsing import parse_asin

class Depot:
    def __init__(self, path=CSV_PATH):
        self.path = path

    def save(self, products):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["Catégorie", "ASIN", "Titre", "Prix (€)", "Note (/5)", "Disponibilité", "Lien"],
            )
            writer.writeheader()
            # La catégorie en premier et le tri rendent le CSV plus simple à lire.
            for product in sorted(products, key=lambda item: item.category.casefold()):
                writer.writerow({
                    "Catégorie": product.category,
                    "ASIN": product.asin or parse_asin(product.url),
                    "Titre": product.title,
                    # Affichage français : l'unité est visible sur chaque ligne du CSV.
                    "Prix (€)": f"{product.price:.2f}".replace(".", ",") + " €" if product.price is not None else "",
                    "Note (/5)": f"{product.rating:.1f}" if product.rating is not None else "",
                    "Disponibilité": product.availability,
                    "Lien": product.url,
                })
        return self.path

    def load(self):
        """Relit les produits du CSV pour consulter les résultats plus tard."""
        if not self.path.exists():
            return []

        with self.path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            return [
                Product(
                    title=self._first_value(row, "Titre", "title"),
                    price=self._optional_number(self._first_value(row, "Prix (€)", "price")),
                    rating=self._optional_number(self._first_value(row, "Note (/5)", "rating")),
                    availability=self._first_value(row, "Disponibilité", "availability"),
                    category=self._first_value(row, "Catégorie", "category"),
                    url=self._first_value(row, "Lien", "url"),
                    asin=self._first_value(row, "ASIN", "asin") or parse_asin(
                        self._first_value(row, "Lien", "url")
                    ),
                )
                for row in csv.DictReader(csv_file)
            ]

    @staticmethod
    def _first_value(row, *keys):
        """Accepte les en-têtes français actuels et les anciens en-têtes anglais."""
        for key in keys:
            value = row.get(key)
            if value is not None:
                return value
        return ""

    @staticmethod
    def _optional_number(value):
        if not value:
            return None
        try:
            cleaned = re.sub(r"[^0-9,.\-]", "", value)
            if "," in cleaned and "." in cleaned:
                # Le dernier séparateur est le séparateur décimal.
                decimal_separator = "," if cleaned.rfind(",") > cleaned.rfind(".") else "."
                thousands_separator = "." if decimal_separator == "," else ","
                cleaned = cleaned.replace(thousands_separator, "")
                cleaned = cleaned.replace(decimal_separator, ".")
            else:
                cleaned = cleaned.replace(",", ".")
            return float(cleaned)
        except (AttributeError, ValueError):
            return None
