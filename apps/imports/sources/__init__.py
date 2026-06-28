"""Fetch wiki content from external URLs (Wikipedia, MediaWiki, RSS, docs, web)."""
from __future__ import annotations

import feedparser

from apps.imports.sources.detect import (
    SOURCE_AUTO,
    SOURCE_DOCS,
    SOURCE_LABELS,
    SOURCE_MEDIAWIKI,
    SOURCE_RSS,
    SOURCE_WEB,
    SOURCE_WIKIPEDIA,
    detect_source_type,
)
from apps.imports.sources.fetch import FetchError, fetch_text
from apps.imports.sources.html_page import fetch_docs, fetch_html_page
from apps.imports.sources.mediawiki import fetch_mediawiki
from apps.imports.sources.rss import fetch_rss
from apps.imports.sources.wikipedia import fetch_wikipedia

SUPPORTED_SOURCES = [
    {
        "id": SOURCE_WIKIPEDIA,
        "label": SOURCE_LABELS[SOURCE_WIKIPEDIA],
        "hint": "https://en.wikipedia.org/wiki/Python_(programming_language)",
    },
    {
        "id": SOURCE_MEDIAWIKI,
        "label": SOURCE_LABELS[SOURCE_MEDIAWIKI],
        "hint": "https://wiki.archlinux.org/title/Installation_guide",
    },
    {
        "id": SOURCE_RSS,
        "label": SOURCE_LABELS[SOURCE_RSS],
        "hint": "https://wikiwonder.fly.dev/feeds/latest/",
    },
    {
        "id": SOURCE_DOCS,
        "label": SOURCE_LABELS[SOURCE_DOCS],
        "hint": "https://docs.python.org/3/tutorial/index.html",
    },
    {
        "id": SOURCE_WEB,
        "label": SOURCE_LABELS[SOURCE_WEB],
        "hint": "Any public HTML article or blog post",
    },
    {
        "id": SOURCE_AUTO,
        "label": SOURCE_LABELS[SOURCE_AUTO],
        "hint": "Detect from URL automatically",
    },
]


def fetch_from_url(url: str, *, source_type: str = SOURCE_AUTO, max_feed_entries: int = 25) -> dict:
    """
    Fetch and convert remote content into wiki markdown.

    Returns dict with keys: title, markdown, source_type, source_url, source_label, meta.
    """
    url = (url or "").strip()
    if not url:
        raise FetchError("URL is required")
    if not url.startswith(("http://", "https://")):
        raise FetchError("URL must start with http:// or https://")

    resolved = source_type if source_type != SOURCE_AUTO else detect_source_type(url)

    if resolved == SOURCE_WIKIPEDIA:
        return fetch_wikipedia(url)
    if resolved == SOURCE_MEDIAWIKI:
        return fetch_mediawiki(url)
    if resolved == SOURCE_RSS:
        return fetch_rss(url, max_entries=max_feed_entries)
    if resolved == SOURCE_DOCS:
        return fetch_docs(url)

    if resolved == SOURCE_WEB:
        # Try RSS first when auto landed on web but URL might be a feed
        if _looks_like_feed(url):
            try:
                return fetch_rss(url, max_entries=max_feed_entries)
            except FetchError:
                pass
        # Try MediaWiki when URL has /wiki/
        if "/wiki/" in url:
            try:
                return fetch_mediawiki(url)
            except FetchError:
                pass
        return fetch_html_page(url)

    raise FetchError(f"Unsupported source type: {source_type}")


def _looks_like_feed(url: str) -> bool:
    lowered = url.lower()
    if any(x in lowered for x in ("/feed", "/rss", ".rss", ".atom", "/feeds/")):
        return True
    try:
        body, content_type = fetch_text(url)
        if "xml" in content_type or "rss" in content_type or "atom" in content_type:
            feed = feedparser.parse(body)
            return bool(feed.entries)
    except FetchError:
        return False
    return False


def list_supported_sources() -> list[dict]:
    return list(SUPPORTED_SOURCES)
