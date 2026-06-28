"""Detect import source type from a URL."""
from __future__ import annotations

import re
from urllib.parse import urlparse

SOURCE_WIKIPEDIA = "wikipedia"
SOURCE_MEDIAWIKI = "mediawiki"
SOURCE_RSS = "rss"
SOURCE_DOCS = "docs"
SOURCE_WEB = "web"
SOURCE_AUTO = "auto"

SOURCE_LABELS = {
    SOURCE_WIKIPEDIA: "Wikipedia",
    SOURCE_MEDIAWIKI: "MediaWiki",
    SOURCE_RSS: "RSS / Atom",
    SOURCE_DOCS: "Documentation",
    SOURCE_WEB: "Web page",
    SOURCE_AUTO: "Auto-detect",
}

RSS_PATH_HINTS = ("/feed", "/feeds/", "/rss", "/atom", ".rss", ".atom", "/index.xml")
DOCS_HOST_HINTS = ("readthedocs.io", "readthedocs.org", "gitbook.io", "gitbook.com")
DOCS_PATH_HINTS = ("/docs/", "/documentation/", "/guide/", "/manual/", "/reference/")


def detect_source_type(url: str) -> str:
    """Best-effort source type from URL shape."""
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()

    if not host:
        return SOURCE_WEB

    if host.endswith("wikipedia.org") or ".wikipedia.org" in host:
        return SOURCE_WIKIPEDIA

    if ("/wiki/" in path or "action=edit" in (parsed.query or "")) and "wikipedia.org" not in host:
        return SOURCE_MEDIAWIKI

    if any(hint in path for hint in RSS_PATH_HINTS):
        return SOURCE_RSS
    if path.endswith((".rss", ".atom", ".xml")) and ("feed" in path or "rss" in path or "atom" in path):
        return SOURCE_RSS

    if any(h in host for h in DOCS_HOST_HINTS) or any(h in path for h in DOCS_PATH_HINTS):
        return SOURCE_DOCS
    if host.startswith("docs.") or host.startswith("developer."):
        return SOURCE_DOCS

    return SOURCE_WEB


def wikipedia_page_title(url: str) -> tuple[str, str] | None:
    """Return (lang_code, page_title) for a Wikipedia article URL."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    match = re.match(r"([a-z]{2,3})\.wikipedia\.org$", host)
    if not match:
        if host == "wikipedia.org":
            match = re.match(r"^/wiki/([^?#]+)", parsed.path)
            if match:
                from urllib.parse import unquote

                return "en", unquote(match.group(1).replace("_", " "))
        return None
    lang = match.group(1)
    path_match = re.match(r"^/wiki/([^?#]+)", parsed.path)
    if not path_match:
        return None
    from urllib.parse import unquote

    return lang, unquote(path_match.group(1).replace("_", " "))


def mediawiki_page_title(url: str) -> str | None:
    """Extract page title from common MediaWiki URL patterns."""
    parsed = urlparse(url)
    from urllib.parse import parse_qs, unquote

    if parsed.path.lower().endswith("/index.php"):
        qs = parse_qs(parsed.query)
        titles = qs.get("title", [])
        if titles:
            return unquote(titles[0].replace("_", " "))
    match = re.search(r"/wiki/([^?#]+)", parsed.path, re.I)
    if match:
        return unquote(match.group(1).replace("_", " "))
    return None
