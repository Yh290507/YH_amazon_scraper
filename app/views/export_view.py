"""Confirmation de création des fichiers de collecte."""
from config import DB_PATH, RECAP_PATH


class ExportView:
    def show_saved_path(self, path, count, image_count=0):
        print(f"\nCSV enregistré : {path} ({count} produits)")
        print(f"Images enregistrées : {image_count} dans le dossier images de cette recherche")
        print(f"Base SQLite : {DB_PATH}")
        print(f"Récapitulatif des collectes : {RECAP_PATH}")
