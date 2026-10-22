"""Démarre le mini-projet : python main.py."""
from app.controllers.scraping_controller import ScrapingController
from app.models.depot import Depot
from app.scraper.amazon_scraper import AmazonScraper
from app.views.console_view import ConsoleView
from app.views.export_view import ExportView

if __name__ == "__main__":
    controller = ScrapingController(AmazonScraper(), Depot(), ConsoleView(), ExportView())
    controller.run()
