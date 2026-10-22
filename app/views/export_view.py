"""Confirmation de création du CSV."""
class ExportView:
    def show_saved_path(self, path, count):
        print(f"\nCSV enregistré : {path} ({count} produits)")
