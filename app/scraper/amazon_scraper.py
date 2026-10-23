"""Collecte les résultats Amazon avec Selenium et suit la pagination."""
import random
import time
from urllib.parse import urlencode, urljoin
from config import AMAZON_URL, CATEGORY_QUERIES, PAGES_MAX, DELAI_ENTRE_PAGES
from app.models.produit import Product
from app.scraper.driver import BrowserDriver
from app.scraper.parsing import clean_text, parse_asin, parse_price, parse_rating

RESULT_CARD = "div[data-component-type='s-search-result'], div.s-result-item[data-asin]:not([data-asin=''])"
NEXT_LINKS = (
    "a.s-pagination-next",
    "a[aria-label='Go to next page']",
    "a[aria-label='Page suivante']",
    "li.a-last a",
)

class AmazonScraper:
    def __init__(self, driver=None):
        self._provided_driver = driver
        self.driver = None
        self._has_navigated = False

    def _navigate(self, url):
        if self._has_navigated:
            time.sleep(random.uniform(*DELAI_ENTRE_PAGES))
        self.driver.open(url)
        self._has_navigated = True

    def _check_access(self):
        body = self.driver.body_text.lower()
        markers = (
            "captcha", "robot check", "vérifiez les caractères", "saisissez les caractères",
            "désolé, nous devons nous assurer", "automated access", "verify you are human",
        )
        if any(marker in body for marker in markers):
            raise RuntimeError("Amazon a affiché une vérification. Le scraper s'arrête sans la contourner.")

    def _first_text(self, element, selectors):
        for selector in selectors:
            try:
                for node in self.driver.find_in(element, selector):
                    value = clean_text(node.text)
                    if not value:
                        value = clean_text(node.get_attribute("textContent"))
                    if not value:
                        value = clean_text(node.get_attribute("aria-label") or node.get_attribute("title"))
                    if value:
                        return value
            except Exception:
                continue
        return ""

    def _extract_title(self, card):
        title = self._first_text(card, (
            "h2 a span", "h2 span", "h2", "[data-cy='title-recipe'] h2", "a[aria-label]",
        ))
        if title:
            return title
        ignored = ("sponsorisé", "sponsored", "étoiles", "sur 5", "livraison", "option")
        for line in (clean_text(line) for line in card.text.splitlines()):
            if len(line) >= 8 and not any(word in line.lower() for word in ignored):
                return line
        return ""

    def _extract_link(self, card):
        for selector in ("h2 a", "a[href*='/dp/']", "a[href*='/gp/product/']"):
            try:
                for node in self.driver.find_in(card, selector):
                    href = node.get_attribute("href")
                    if href and ("/dp/" in href or "/gp/product/" in href):
                        return urljoin(AMAZON_URL, href)
            except Exception:
                continue
        asin = card.get_attribute("data-asin")
        return f"{AMAZON_URL}/dp/{asin}" if asin else ""

    def _next_page_url(self):
        for selector in NEXT_LINKS:
            try:
                for node in self.driver.find_all(selector):
                    href = node.get_attribute("href")
                    classes = (node.get_attribute("class") or "").split()
                    if href and node.get_attribute("aria-disabled") != "true" and "s-pagination-disabled" not in classes:
                        return urljoin(AMAZON_URL, href)
            except Exception:
                continue
        return None

    def scrape(self):
        products = []
        self.driver = self._provided_driver or BrowserDriver()
        self._has_navigated = False
        try:
            for category, query_text in CATEGORY_QUERIES.items():
                page_url = f"{AMAZON_URL}/s?{urlencode({'k': query_text})}"
                for page_number in range(1, PAGES_MAX + 1):
                    print(f"Lecture page {page_number}/{PAGES_MAX} — catégorie : {category}")
                    self._navigate(page_url)
                    self._check_access()
                    try:
                        self.driver.wait_for(RESULT_CARD)
                    except Exception as exc:
                        self._check_access()
                        page_title = getattr(self.driver, "page_title", "titre indisponible")
                        current_url = getattr(self.driver, "current_url", page_url)
                        sample = " ".join(self.driver.body_text.split())[:300]
                        raise RuntimeError(
                            f"Les cartes Amazon ne sont pas apparues sur la page {page_number} ({category}). "
                            f"Onglet={page_title!r}; URL={current_url}; texte reçu={sample!r}. "
                            "Vérifie si Amazon a affiché une vérification ou si la pagination a changé."
                        ) from exc

                    cards = self.driver.find_all(RESULT_CARD)
                    page_products = 0
                    page_readable = 0
                    page_skipped = 0
                    for card in cards:
                        title = self._extract_title(card)
                        if not title:
                            page_skipped += 1
                            continue
                        link = self._extract_link(card)
                        asin = parse_asin(card.get_attribute("data-asin")) or parse_asin(link)
                        page_readable += 1
                        price_text = self._first_text(card, ("span.a-price span.a-offscreen",))
                        rating_text = self._first_text(card, ("span.a-icon-alt",))
                        try:
                            price = parse_price(price_text) if price_text else None
                        except ValueError:
                            price = None
                        try:
                            rating = parse_rating(rating_text) if rating_text else None
                        except ValueError:
                            rating = None

                        # Le CSV ne conserve que les fiches avec les données utiles
                        # aux statistiques et un lien produit exploitable.
                        if price is None or rating is None or not link:
                            page_skipped += 1
                            continue

                        availability = self._first_text(card, (
                            ".a-color-base.a-text-bold", "[data-cy='delivery-recipe']",
                        )) or "Non indiqué"
                        products.append(Product(
                            title=title,
                            price=price,
                            rating=rating,
                            availability=availability,
                            category=category,
                            url=link,
                            asin=asin,
                        ))
                        page_products += 1
                    if not page_readable:
                        page_title = getattr(self.driver, "page_title", "titre indisponible")
                        current_url = getattr(self.driver, "current_url", page_url)
                        sample = " ".join(self.driver.body_text.split())[:300]
                        raise RuntimeError(
                            f"Aucun produit lisible sur la page {page_number} ({category}) : "
                            f"{len(cards)} cartes détectées; onglet={page_title!r}; URL={current_url}; "
                            f"texte reçu={sample!r}."
                        )
                    print(
                        f"  {page_products} produits complets conservés; "
                        f"{page_skipped} fiches ignorées (titre, prix, note ou lien manquant)."
                    )
                    if page_number < PAGES_MAX:
                        next_url = self._next_page_url()
                        if not next_url:
                            print(f"  Aucun lien page suivante détecté pour {category}; fin de cette catégorie.")
                            break
                        page_url = next_url
        finally:
            driver = self.driver
            self.driver = None
            self._has_navigated = False
            if driver is not None:
                driver.close()
        return products

