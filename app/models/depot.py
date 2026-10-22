"""Enregistre les produits dans un fichier CSV."""
import csv
from config import CSV_PATH

class Depot:
    def __init__(self, path=CSV_PATH):
        self.path = path

    def save(self, products):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["title", "price", "rating", "availability", "category", "url"])
            writer.writeheader()
            for product in products:
                writer.writerow({
                    "title": product.title,
                    "price": f"{product.price:.2f}" if product.price is not None else "",
                    "rating": f"{product.rating:.1f}" if product.rating is not None else "",
                    "availability": product.availability,
                    "category": product.category,
                    "url": product.url,
                })
        return self.path
