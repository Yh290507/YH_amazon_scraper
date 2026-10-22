"""Affichage des produits et des trois statistiques demandées."""
class ConsoleView:
    def show_error(self, message):
        print(f"\nErreur : {message}")

    def show_results(self, products, stats):
        print(f"\n{len(products)} produits collectés :")
        for item in products:
            price_text = f"{item.price:.2f} €" if item.price is not None else "Prix non indiqué"
            rating_text = f"{item.rating:.1f}/5" if item.rating is not None else "Note non indiquée"
            print(f"- {item.title} | {price_text} | {rating_text} | {item.availability} | {item.category}")
        print("\nStatistiques")
        print(f"Prix moyen : {stats['average_price']:.2f} €")
        print(f"Prix maximum : {stats['max_price']:.2f} €")
        print("Nombre de produits par catégorie :")
        for category, count in stats["by_category"].items():
            print(f"  {category} : {count}")
