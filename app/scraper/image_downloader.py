"""Télécharge les images des produits dans le dossier de données."""
import hashlib
import random
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from config import DELAI_ENTRE_IMAGES


MAX_IMAGE_BYTES = 8 * 1024 * 1024
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class ImageDownloader:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.rate_limited = False

    def download(self, image_url, asin="", subdirectory=""):
        """Retourne un chemin relatif au dossier de la recherche."""
        if not image_url:
            return ""
        try:
            if urlparse(image_url).scheme not in ("http", "https"):
                return ""
        except ValueError:
            return ""

        safe_asin = re.sub(r"[^A-Za-z0-9_-]", "", asin or "")
        stem = safe_asin or hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:16]
        relative_directory = Path(subdirectory) if subdirectory else Path()
        target_directory = self.directory / relative_directory
        try:
            target_directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            return ""
        existing = next(target_directory.glob(f"{stem}.*"), None)
        if existing:
            return (Path("images") / relative_directory / existing.name).as_posix()

        request = Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
                "Referer": "https://www.amazon.fr/",
            },
        )
        time.sleep(random.uniform(*DELAI_ENTRE_IMAGES))
        try:
            with urlopen(request, timeout=15) as response:
                content_type = response.headers.get_content_type().lower()
                extension = IMAGE_EXTENSIONS.get(content_type)
                if not extension:
                    return ""
                content = response.read(MAX_IMAGE_BYTES + 1)
                if not content or len(content) > MAX_IMAGE_BYTES:
                    return ""
        except HTTPError as exc:
            if exc.code in (429, 503):
                self.rate_limited = True
            return ""
        except (URLError, TimeoutError, OSError, ValueError):
            return ""

        destination = target_directory / f"{stem}{extension}"
        try:
            destination.write_bytes(content)
        except OSError:
            return ""
        return (Path("images") / relative_directory / destination.name).as_posix()
