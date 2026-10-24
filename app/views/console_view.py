"""Affichage des produits et des statistiques de collecte."""
class ConsoleView:
    def show_menu(self):
        print("\n=== Scraper Amazon ===")
        print("1. Lancer une recherche Amazon")
        print("2. Afficher les statistiques de la dernière collecte")
        print("3. Quitter")
        return input("Choix : ").strip()

    def ask_keyword(self):
        return input("Saisis un mot-clé tech à rechercher sur Amazon : ").strip()

    def show_error(self, message):
        print(f"\nErreur : {message}")

    def show_results(self, products, stats):
        print(f"\nProduits trouvés : {len(products)}")
        for index, product in enumerate(products, start=1):
            price = f"{product.price:.2f} €" if product.price is not None else "non indiqué"
            rating = f"{product.rating:.1f}/5" if product.rating is not None else "non indiquée"
            print(f"{index}. {product.title}")
            subcategory = product.subcategory or "non détectée"
            print(
                f"   Catégorie : {product.category} | Sous-catégorie : {subcategory}"
                f" | Prix : {price} | Note : {rating}"
            )
            if product.brand:
                print(f"   Marque : {product.brand}")

        print("\nStatistiques")
        for label, key in (("Prix moyen", "average_price"), ("Prix maximum", "max_price")):
            value = stats[key]
            display = f"{value:.2f} €" if value is not None else "non disponible"
            print(f"{label} : {display}")
        rating = stats["average_rating"]
        rating_display = f"{rating:.1f}/5" if rating is not None else "non disponible"
        print(f"Note moyenne : {rating_display}")
        categories = stats["by_category"]
        if categories:
            print("Nombre de produits par catégorie :")
            for category, count in categories.items():
                print(f"  {category} : {count}")
        subcategories = stats["by_subcategory"]
        if subcategories:
            print("Nombre de produits par catégorie et sous-catégorie détectées :")
            for (category, subcategory), count in subcategories.items():
                print(f"  {category} > {subcategory} : {count}")
        for keyword, count in stats["by_keyword"].items():
            print(f"  Recherche « {keyword} » : {count} produit(s)")

    def show_goodbye(self):
        print("Au revoir.")
