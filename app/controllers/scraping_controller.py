"""Coordonne le scraping, l'enregistrement et l'affichage."""
import csv
import sqlite3
from app.models.produit import Product

class ScrapingController:
    def __init__(self, scraper, depot, console_view, export_view):
        self.scraper = scraper
        self.depot = depot
        self.console_view = console_view
        self.export_view = export_view

    def run(self):
        # La première action au lancement est directement la saisie du mot-clé.
        self.scrape_and_export()
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
        keyword = self.console_view.ask_keyword()
        if not keyword:
            self.console_view.show_error("Le mot-clé ne peut pas être vide.")
            return
        try:
            products = self.scraper.scrape(keyword)
            if not products:
                self.console_view.show_error("Aucun produit n'a été collecté.")
                return
            path = self.depot.save(products, keyword)
            self.console_view.show_results(products, Product.statistics(products))
            image_count = sum(bool(product.image_path) for product in products)
            self.export_view.show_saved_path(path, len(products), image_count)
        except Exception as exc:
            self.console_view.show_error(str(exc))

    def show_saved_results(self):
        try:
            products = self.depot.load()
        except (OSError, ValueError, csv.Error, sqlite3.Error) as exc:
            self.console_view.show_error(f"Impossible de lire les données enregistrées : {exc}")
            return
        if not products:
            self.console_view.show_error("Aucune collecte enregistrée. Lance d'abord une recherche.")
            return
        self.console_view.show_results(products, Product.statistics(products))
