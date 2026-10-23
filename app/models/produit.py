"""Modèle de données et statistiques des produits Amazon."""
from collections import Counter
from dataclasses import dataclass

@dataclass(frozen=True)
class Product:
    title: str
    price: float | None
    rating: float | None
    availability: str
    category: str
    url: str
    asin: str = ""

    @staticmethod
    def statistics(products):
        prices = [item.price for item in products if item.price is not None]
        return {
            "average_price": sum(prices) / len(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "by_category": dict(sorted(Counter(item.category for item in products).items())),
        }
