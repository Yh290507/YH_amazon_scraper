"""Coordonne le scraping, l'enregistrement et l'affichage."""
import csv
from app.models.produit import Product

class ScrapingController:
    def __init__(self, scraper, depot, console_view, export_view):
        self.scraper = scraper
        self.depot = depot
        self.console_view = console_view
        self.export_view = export_view

    def run(self):
        while True:
            choice = self.console_view.show_menu()
            if choice == "1":
                self.scrape_and_export()
            elif choice == "2":
                self.show_saved_results()
            elif choice == "3":
                self.console_view.show_goodbye()
                return
            else:
                self.console_view.show_error("Choix invalide. Entre 1, 2 ou 3.")

    def scrape_and_export(self):
        try:
            products = self.scraper.scrape()
            if not products:
                self.console_view.show_error("Aucun produit n'a été collecté.")
                return
            path = self.depot.save(products)
            self.console_view.show_results(products, Product.statistics(products))
            self.export_view.show_saved_path(path, len(products))
        except Exception as exc:
            self.console_view.show_error(str(exc))

    def show_saved_results(self):
        try:
            products = self.depot.load()
        except (OSError, ValueError, csv.Error) as exc:
            self.console_view.show_error(f"Impossible de lire le CSV : {exc}")
            return
        if not products:
            self.console_view.show_error("Aucun CSV disponible. Lance d'abord le scraping.")
            return
        self.console_view.show_results(products, Product.statistics(products))
