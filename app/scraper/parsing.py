"""Nettoyage des valeurs textuelles extraites du DOM Selenium."""
import re

def clean_text(raw):
    return " ".join((raw or "").split())

def parse_price(raw):
    """Convertit un prix comme 1 299,99 € en float."""
    cleaned = re.sub(r"[^0-9,.]", "", raw).replace(",", ".")
    if not cleaned:
        raise ValueError(f"Prix illisible : {raw!r}")
    return float(cleaned)

def parse_rating(raw):
    """Lit la note moyenne (ex. '4,5 sur 5 étoiles') en nombre décimal."""
    match = re.search(r"(\d+(?:[.,]\d+)?)", raw or "")
    if not match:
        raise ValueError(f"Note illisible : {raw!r}")
    return float(match.group(1).replace(",", "."))
