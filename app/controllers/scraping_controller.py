"""Coordonne le scraping, l'enregistrement et l'affichage."""
from app.models.produit import Product

class ScrapingController:
    def __init__(self, scraper, depot, console_view, export_view):
        self.scraper = scraper
        self.depot = depot
        self.console_view = console_view
        self.export_view = export_view

    def run(self):
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
