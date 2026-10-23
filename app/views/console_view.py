"""Affichage des produits et des trois statistiques demandées."""
class ConsoleView:
    def show_menu(self):
        print("\n=== Scraper Amazon ===")
        print("1. Lancer le scraping")
        print("2. Afficher les statistiques du CSV")
        print("3. Quitter")
        return input("Choix : ").strip()

    def show_error(self, message):
        print(f"\nErreur : {message}")

    def show_results(self, products, stats):
        print(f"\nRésumé : {len(products)} produits")
        for label, key in (("Prix moyen", "average_price"), ("Prix maximum", "max_price")):
            value = stats[key]
            display = f"{value:.2f} €" if value is not None else "non disponible"
            print(f"{label} : {display}")
        print("Nombre de produits par catégorie :")
        for category, count in stats["by_category"].items():
            print(f"  {category} : {count}")

    def show_goodbye(self):
        print("Au revoir.")
