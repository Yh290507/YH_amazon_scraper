import unittest
from app.models.produit import Product
from app.scraper.parsing import parse_price, parse_rating

class ParsingAndStatisticsTests(unittest.TestCase):
    def test_price_in_euros(self):
        self.assertEqual(parse_price("1 299,99 €"), 1299.99)

    def test_rating(self):
        self.assertEqual(parse_rating("4,5 sur 5 étoiles"), 4.5)

    def test_three_statistics(self):
        products = [
            Product("Livre A", 10.0, 4.2, "Disponible", "Romans", "url-a"),
            Product("Livre B", 20.0, 4.7, "Disponible", "Romans", "url-b"),
            Product("Livre C", 30.0, None, "Disponible", "Poésie", "url-c"),
        ]
        stats = Product.statistics(products)
        self.assertEqual(stats["average_price"], 20.0)
        self.assertEqual(stats["max_price"], 30.0)
        self.assertEqual(stats["by_category"], {"Poésie": 1, "Romans": 2})
