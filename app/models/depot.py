"""Enregistre chaque collecte dans un CSV détaillé et dans SQLite."""
import csv
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, DB_PATH, RECAP_PATH, collection_dir
from app.models.produit import Product
from app.scraper.parsing import parse_asin


CSV_FIELDS = [
    "Catégorie", "Sous-catégorie", "Mot-clé recherché", "ASIN", "Titre", "Marque",
    "Description", "Prix (€)", "Note (/5)", "Disponibilité", "Image locale",
    "URL image", "Lien produit",
]


class Depot:
    def __init__(self, db_path=DB_PATH, recap_path=RECAP_PATH):
        self.db_path = Path(db_path)
        self.recap_path = Path(recap_path)

    def save(self, products, keyword=None):
        products = list(products)
        if not keyword:
            keyword = products[0].keyword if products else "recherche"
        keyword = " ".join(keyword.split()) or "recherche"
        category = self._collection_category(products)

        folder = collection_dir(keyword)
        folder.mkdir(parents=True, exist_ok=True)
        csv_path = folder / "produits.csv"
        self._save_csv(products, csv_path, keyword)

        collected_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self._save_database(products, category, keyword, collected_at, csv_path)
        self._append_recap(category, keyword, collected_at, len(products), csv_path)
        return csv_path

    @staticmethod
    def _collection_category(products):
        categories = sorted({product.category or "Autres" for product in products})
        if len(categories) == 1:
            return categories[0]
        return "Mixte" if categories else "Autres"

    def _save_csv(self, products, path, keyword):
        with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for product in products:
                writer.writerow({
                    "Catégorie": product.category or "Autres",
                    "Sous-catégorie": product.subcategory,
                    "Mot-clé recherché": product.keyword or keyword,
                    "ASIN": product.asin or parse_asin(product.url),
                    "Titre": product.title,
                    "Marque": product.brand,
                    "Description": product.description,
                    "Prix (€)": self._format_price(product.price),
                    "Note (/5)": f"{product.rating:.1f}" if product.rating is not None else "",
                    "Disponibilité": product.availability,
                    "Image locale": product.image_path,
                    "URL image": product.image_url,
                    "Lien produit": product.url,
                })

    @staticmethod
    def _format_price(price):
        return f"{price:.2f}".replace(".", ",") + " €" if price is not None else ""

    def _save_database(self, products, category, keyword, collected_at, csv_path):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                connection.executescript("""
                    CREATE TABLE IF NOT EXISTS collections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        collected_at TEXT NOT NULL,
                        product_count INTEGER NOT NULL,
                        csv_path TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        collection_id INTEGER NOT NULL REFERENCES collections(id),
                        category TEXT NOT NULL,
                        subcategory TEXT NOT NULL DEFAULT '',
                        keyword TEXT NOT NULL,
                        asin TEXT,
                        title TEXT NOT NULL,
                        brand TEXT,
                        description TEXT,
                        price REAL,
                        rating REAL,
                        availability TEXT,
                        image_path TEXT,
                        image_url TEXT,
                        product_url TEXT
                    );
                """)
                product_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(products)")
                }
                if "subcategory" not in product_columns:
                    connection.execute(
                        "ALTER TABLE products ADD COLUMN subcategory TEXT NOT NULL DEFAULT ''"
                    )
                cursor = connection.execute(
                    "INSERT INTO collections (category, keyword, collected_at, product_count, csv_path) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (category, keyword, collected_at, len(products), str(csv_path.relative_to(DATA_DIR))),
                )
                collection_id = cursor.lastrowid
                connection.executemany(
                    """INSERT INTO products (
                        collection_id, category, subcategory, keyword, asin, title, brand,
                        description, price, rating, availability, image_path, image_url,
                        product_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [(
                        collection_id,
                        product.category or "Autres",
                        product.subcategory,
                        product.keyword or keyword,
                        product.asin or parse_asin(product.url),
                        product.title,
                        product.brand,
                        product.description,
                        product.price,
                        product.rating,
                        product.availability,
                        product.image_path,
                        product.image_url,
                        product.url,
                    ) for product in products],
                )

    def _append_recap(self, category, keyword, collected_at, count, csv_path):
        self.recap_path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.recap_path.exists() and self.recap_path.stat().st_size > 0
        encoding = "utf-8" if exists else "utf-8-sig"
        with self.recap_path.open("a", newline="", encoding=encoding) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["Date de collecte", "Catégorie", "Mot-clé", "Nombre de produits", "CSV"],
            )
            if not exists:
                writer.writeheader()
            writer.writerow({
                "Date de collecte": collected_at,
                "Catégorie": category,
                "Mot-clé": keyword,
                "Nombre de produits": count,
                "CSV": str(csv_path.relative_to(DATA_DIR)),
            })

    def load(self):
        """Charge les produits de la collecte la plus récente dans SQLite."""
        if not self.db_path.exists():
            return []
        with closing(sqlite3.connect(self.db_path)) as connection:
            product_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(products)")
            }
            collection = connection.execute(
                "SELECT id FROM collections ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not collection:
                return []
            subcategory_column = "subcategory" if "subcategory" in product_columns else "''"
            rows = connection.execute(
                f"""SELECT category, {subcategory_column}, keyword, asin, title, brand,
                           description, price, rating, availability, image_path, image_url,
                           product_url FROM products WHERE collection_id = ? ORDER BY id""",
                (collection[0],),
            ).fetchall()
            return [self._product_from_database_row(row) for row in rows]

    @staticmethod
    def _product_from_database_row(row):
        return Product(
            category=row[0], subcategory=row[1] or "", keyword=row[2],
            asin=row[3] or "", title=row[4], brand=row[5] or "",
            description=row[6] or "", price=row[7], rating=row[8],
            availability=row[9] or "", image_path=row[10] or "",
            image_url=row[11] or "", url=row[12] or "",
        )
