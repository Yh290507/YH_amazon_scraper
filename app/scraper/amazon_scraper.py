"""Collecte les résultats Amazon avec Selenium et suit la pagination."""
import json
import random
import time
from dataclasses import replace
from urllib.parse import urlencode, urljoin
from config import (
    AMAZON_URL, AMAZON_SEARCH_INDEX, DELAI_ENTRE_NAVIGATIONS,
    DETAIL_TIMEOUT, MAX_PRODUCTS_PER_PAGE, PAGES_MAX, collection_dir, keyword_slug,
)
from app.models.produit import Product
from app.scraper.driver import BrowserDriver
from app.scraper.image_downloader import ImageDownloader
from app.scraper.parsing import clean_text, parse_asin, parse_price, parse_rating

RESULT_CARD = "div[data-component-type='s-search-result'], div.s-result-item[data-asin]:not([data-asin=''])"
NEXT_LINKS = (
    "a.s-pagination-next",
    "a[aria-label='Go to next page']",
    "a[aria-label='Page suivante']",
    "li.a-last a",
)
DETAIL_PRICE_SELECTORS = (
    "#corePriceDisplay_desktop_feature_div span.a-offscreen",
    "#apex_desktop span.a-offscreen",
    "#priceblock_ourprice",
    "#priceblock_dealprice",
    "#price_inside_buybox",
    "span.a-price span.a-offscreen",
)
DETAIL_RATING_SELECTORS = (
    "#acrPopover span.a-icon-alt",
    "#averageCustomerReviews span.a-icon-alt",
    "[data-hook='rating-out-of-text']",
    "span.a-icon-alt",
)
BREADCRUMB_SELECTORS = (
    "#wayfinding-breadcrumbs_container a",
    "#wayfinding-breadcrumbs_feature_div a",
)

class AmazonScraper:
    def __init__(self, driver=None):
        self._provided_driver = driver
        self.driver = None
        self._has_navigated = False

    def _navigate(self, url):
        if self._has_navigated:
            time.sleep(random.uniform(*DELAI_ENTRE_NAVIGATIONS))
        self.driver.open(url)
        self._has_navigated = True

    def _check_access(self):
        body = self.driver.body_text.lower()
        internal_error_markers = (
            "erreur de système interne",
            "internal system error",
        )
        if any(marker in body for marker in internal_error_markers):
            raise RuntimeError(
                "Amazon a renvoyé sa page d'erreur interne au lieu des résultats. "
                "Ce n'est pas un problème de mot-clé ou de sélecteur CSS. "
                "Réessaie plus tard; le programme ne relance pas la requête en boucle."
            )

        verification_markers = (
            "captcha", "robot check", "vérifiez les caractères", "saisissez les caractères",
            "désolé, nous devons nous assurer", "automated access", "verify you are human",
            "unusual traffic", "trafic inhabituel", "unusual activity",
            "our systems have detected", "requests from your computer network",
        )
        if any(marker in body for marker in verification_markers):
            raise RuntimeError(
                "Amazon a affiché une vérification ou détecté un trafic inhabituel. "
                "Le scraper s'arrête sans réessayer ni contourner cette protection."
            )
        limit_markers = (
            "too many requests", "rate exceeded", "request was throttled",
            "service unavailable", "access denied", "http 429", "error 503",
        )
        if any(marker in body for marker in limit_markers):
            raise RuntimeError(
                "Amazon a signalé une limitation ou une indisponibilité. "
                "Le scraper s'arrête sans relancer les requêtes. Réessaie plus tard."
            )

    def _first_text(self, element, selectors):
        for selector in selectors:
            try:
                for node in self.driver.find_in(element, selector):
                    value = self._node_text(node)
                    if value:
                        return value
            except Exception:
                continue
        return ""

    def _first_page_text(self, selectors):
        for selector in selectors:
            try:
                for node in self.driver.find_all(selector):
                    value = self._node_text(node)
                    if value:
                        return value
            except Exception:
                continue
        return ""

    @staticmethod
    def _node_text(node):
        value = clean_text(node.text)
        if not value:
            value = clean_text(node.get_attribute("textContent"))
        if not value:
            value = clean_text(node.get_attribute("aria-label") or node.get_attribute("title"))
        return value

    @staticmethod
    def _optional_price(raw):
        try:
            return parse_price(raw) if raw else None
        except ValueError:
            return None

    @staticmethod
    def _optional_rating(raw):
        try:
            return parse_rating(raw) if raw else None
        except ValueError:
            return None

    def _extract_detail_values(self, product_url):
        """Lit le fil d'Ariane et complète les données sur la fiche produit."""
        self._navigate(product_url)
        self._check_access()
        try:
            self.driver.wait_for("#productTitle", timeout=DETAIL_TIMEOUT)
        except TypeError:
            # Compatibilité avec les pilotes injectés qui n'acceptent qu'un argument.
            self.driver.wait_for("#productTitle")
        except Exception:
            # Certains formats de fiche ne présentent pas le sélecteur du titre;
            # on tente quand même les sélecteurs de prix et de note.
            self._check_access()
        breadcrumb = self._extract_breadcrumb()
        price_text = self._first_page_text(DETAIL_PRICE_SELECTORS)
        rating_text = self._first_page_text(DETAIL_RATING_SELECTORS)
        return (
            self._optional_price(price_text),
            self._optional_rating(rating_text),
            breadcrumb[0],
            breadcrumb[1],
        )

    def _extract_breadcrumb(self):
        """Retourne la catégorie principale et le reste du fil d'Ariane Amazon."""
        for selector in BREADCRUMB_SELECTORS:
            try:
                nodes = self.driver.find_all(selector)
            except Exception:
                continue
            breadcrumb = []
            for node in nodes:
                label = self._node_text(node)
                if not label or label.casefold() in {"amazon.fr", "accueil", "home"}:
                    continue
                if not breadcrumb or label.casefold() != breadcrumb[-1].casefold():
                    breadcrumb.append(label)
            if breadcrumb:
                return breadcrumb[0], " > ".join(breadcrumb[1:])
        return "", ""

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

    def _extract_image_url(self, card):
        try:
            images = self.driver.find_in(card, "img.s-image") or self.driver.find_in(card, "img")
            for image in images:
                for attribute in ("src", "data-src"):
                    value = image.get_attribute(attribute) or ""
                    if value.startswith(("https://", "http://")):
                        return value
                dynamic_images = image.get_attribute("data-a-dynamic-image") or ""
                if dynamic_images:
                    try:
                        urls = json.loads(dynamic_images)
                        if urls:
                            return next(iter(urls))
                    except (TypeError, ValueError):
                        continue
        except Exception:
            pass
        return ""

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

    def scrape(self, keyword):
        products = []
        seen_products = set()
        visited_pages = set()
        keyword = clean_text(keyword)
        if not keyword:
            raise ValueError("Le mot-clé de recherche ne peut pas être vide.")
        image_downloader = ImageDownloader(collection_dir(keyword) / "images")
        self.driver = self._provided_driver or BrowserDriver()
        self._has_navigated = False
        try:
            page_url = f"{AMAZON_URL}/s?{urlencode({'k': keyword, 'i': AMAZON_SEARCH_INDEX})}"
            page_number = 0
            while page_url:
                if page_number >= PAGES_MAX:
                    print(f"Limite configurée atteinte : {PAGES_MAX} pages au maximum.")
                    break
                if page_url in visited_pages:
                    print("La pagination a renvoyé vers une page déjà visitée; arrêt pour éviter une boucle.")
                    break
                visited_pages.add(page_url)
                page_number += 1
                print(f"Lecture page {page_number} — recherche : {keyword}")
                try:
                    self._navigate(page_url)
                    self._check_access()
                except Exception as exc:
                    if products:
                        print(
                            f"Arrêt de la pagination après {len(products)} produits. "
                            f"Les résultats déjà lus seront conservés. Détail : {exc}"
                        )
                        break
                    raise
                try:
                    self.driver.wait_for(RESULT_CARD)
                except Exception as exc:
                    try:
                        self._check_access()
                    except RuntimeError as access_error:
                        if products:
                            print(
                                f"Arrêt de la pagination après {len(products)} produits. "
                                f"Les résultats déjà lus seront conservés. Détail : {access_error}"
                            )
                            break
                        raise
                    if products:
                        print(
                            f"La page {page_number} n'a pas fourni de cartes lisibles. "
                            f"Les {len(products)} produits déjà lus seront conservés."
                        )
                        break
                    page_title = getattr(self.driver, "page_title", "titre indisponible")
                    current_url = getattr(self.driver, "current_url", page_url)
                    sample = " ".join(self.driver.body_text.split())[:300]
                    raise RuntimeError(
                        f"Les cartes Amazon ne sont pas apparues sur la page {page_number} "
                        f"(recherche : {keyword}). Onglet={page_title!r}; URL={current_url}; "
                        f"texte reçu={sample!r}. Vérifie si Amazon a affiché une vérification "
                        "ou si la pagination a changé."
                    ) from exc

                cards = self.driver.find_all(RESULT_CARD)
                page_products = []
                page_readable = 0
                page_skipped = 0
                for card_index, card in enumerate(cards):
                    if len(page_products) >= MAX_PRODUCTS_PER_PAGE:
                        page_skipped += len(cards) - card_index
                        break
                    title = self._extract_title(card)
                    if not title:
                        page_skipped += 1
                        continue
                    page_readable += 1
                    link = self._extract_link(card)
                    asin = parse_asin(card.get_attribute("data-asin")) or parse_asin(link)
                    product_key = asin or link or title.casefold()
                    if product_key in seen_products:
                        page_skipped += 1
                        continue
                    seen_products.add(product_key)
                    price_text = self._first_text(card, ("span.a-price span.a-offscreen",))
                    rating_text = self._first_text(card, ("span.a-icon-alt",))
                    image_url = self._extract_image_url(card)
                    price = self._optional_price(price_text)
                    rating = self._optional_rating(rating_text)

                    availability = self._first_text(card, (
                        ".a-color-base.a-text-bold", "[data-cy='delivery-recipe']",
                    ))
                    brand = self._first_text(card, ("[data-cy='brand']", "[data-brand]"))
                    description = self._first_text(card, (
                        "[data-cy='product-description']", "[data-description]",
                    ))
                    page_products.append(Product(
                        title=title,
                        price=price,
                        rating=rating,
                        availability=availability,
                        category="Tech",
                        url=link,
                        asin=asin,
                        image_url=image_url,
                        brand=brand,
                        description=description,
                        keyword=keyword,
                    ))
                if not page_readable:
                    if products:
                        print(
                            f"Aucun produit lisible sur la page {page_number}; "
                            f"les {len(products)} produits déjà lus seront conservés."
                        )
                        break
                    page_title = getattr(self.driver, "page_title", "titre indisponible")
                    current_url = getattr(self.driver, "current_url", page_url)
                    sample = " ".join(self.driver.body_text.split())[:300]
                    raise RuntimeError(
                        f"Aucun produit lisible sur la page {page_number} "
                        f"(recherche : {keyword}) : {len(cards)} cartes détectées; "
                        f"onglet={page_title!r}; URL={current_url}; texte reçu={sample!r}."
                    )
                next_url = self._next_page_url()
                recovered_prices = 0
                recovered_ratings = 0
                subcategory_count = 0
                detail_attempts = 0
                detail_error = False
                for index, product in enumerate(page_products):
                    # Une fiche n'est ouverte que si la page de résultats ne fournit
                    # pas le prix ou la note; cela limite fortement les requêtes.
                    if not product.url or (
                        product.price is not None and product.rating is not None
                    ):
                        continue
                    detail_attempts += 1
                    try:
                        detail_price, detail_rating, category, subcategory = (
                            self._extract_detail_values(product.url)
                        )
                    except Exception as exc:
                        print(
                            "La lecture d'une fiche produit a échoué; les données déjà "
                            f"collectées sont conservées. Détail : {exc}"
                        )
                        detail_error = True
                        break
                    price = product.price if product.price is not None else detail_price
                    rating = product.rating if product.rating is not None else detail_rating
                    if product.price is None and price is not None:
                        recovered_prices += 1
                    if product.rating is None and rating is not None:
                        recovered_ratings += 1
                    if subcategory:
                        subcategory_count += 1
                    page_products[index] = replace(
                        product,
                        price=price,
                        rating=rating,
                        category="Tech",
                        subcategory=" > ".join(
                            part for part in (category, subcategory) if part
                        ),
                    )

                if not detail_error:
                    for index, product in enumerate(page_products):
                        if image_downloader.rate_limited:
                            break
                        category_slug = keyword_slug(product.category)
                        subcategory_slug = (
                            keyword_slug(product.subcategory)
                            if product.subcategory else "non-classee"
                        )
                        image_path = image_downloader.download(
                            product.image_url,
                            product.asin,
                            f"{category_slug}/{subcategory_slug}",
                        )
                        page_products[index] = replace(product, image_path=image_path)

                products.extend(page_products)
                missing_prices = sum(product.price is None for product in page_products)
                missing_ratings = sum(product.rating is None for product in page_products)
                print(
                    f"  {len(page_products)} produits conservés; "
                    f"{page_skipped} fiches ignorées (titre manquant ou doublon)."
                )
                print(
                    f"  Limite : {MAX_PRODUCTS_PER_PAGE} produits au maximum sur cette page; "
                    f"recherche limitée à {PAGES_MAX} pages dans le rayon électronique."
                )
                if detail_attempts:
                    print(
                        f"  Fiches consultées pour compléter prix ou notes : {detail_attempts}; "
                        f"sous-catégories lues dans le fil d'Ariane : {subcategory_count}. "
                        f"Prix et notes complétés : "
                        f"{recovered_prices} et "
                        f"{recovered_ratings}; il reste {missing_prices} prix et "
                        f"{missing_ratings} notes absents ou non détectés."
                    )
                if detail_error:
                    print("Arrêt de la recherche après l'échec d'accès à une fiche produit.")
                    break
                if image_downloader.rate_limited:
                    print(
                        "Amazon a limité le téléchargement des images (HTTP 429/503). "
                        "Les images restantes ne seront pas demandées et la recherche s'arrête."
                    )
                    break
                if not page_products:
                    print("Aucun nouveau produit sur cette page; arrêt de la pagination.")
                    break
                if not next_url:
                    print(f"  Aucune page suivante détectée pour « {keyword} »; fin de la recherche.")
                    break
                if next_url in visited_pages:
                    print("La page suivante a déjà été visitée; arrêt pour éviter une boucle.")
                    break
                if page_number >= PAGES_MAX:
                    print(f"Limite configurée atteinte : {PAGES_MAX} pages au maximum.")
                    break
                page_url = next_url
        finally:
            driver = self.driver
            self.driver = None
            self._has_navigated = False
            if driver is not None:
                driver.close()
        return products

