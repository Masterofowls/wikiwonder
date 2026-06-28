"""Fetch citation metadata from Wikipedia articles via the MediaWiki API."""
from __future__ import annotations

import re
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from apps.imports.sources.detect import wikipedia_page_title
from apps.imports.sources.fetch import FetchError, fetch_json


def fetch_wikipedia_citations(source_url: str) -> dict[str, dict]:
    """Fetch citation URLs/labels from a Wikipedia article via the parse API."""
    parsed = wikipedia_page_title(source_url)
    if not parsed:
        return {}
    lang, page_title = parsed
    params = urlencode(
        {
            "action": "parse",
            "page": page_title,
            "prop": "text",
            "format": "json",
            "redirects": "1",
        }
    )
    api = f"https://{lang}.wikipedia.org/w/api.php?{params}"
    try:
        data = fetch_json(api)
    except FetchError:
        return {}

    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return {}

    soup = BeautifulSoup(html, "html5lib")
    refs: dict[str, dict] = {}
    for li in soup.select("ol.references li[id^='cite_note-']"):
        note_id = li.get("id", "")
        num_match = re.search(r"cite_note-(\d+)", note_id)
        if not num_match:
            continue
        num = num_match.group(1)
        ext = li.select_one("a.external, a[href^='http']")
        url = ext.get("href", "") if ext else ""
        label = li.get_text(" ", strip=True)
        label = re.sub(r"^\[\d+\]\s*", "", label)
        label = label[:240] if label else f"Citation {num}"
        refs[num] = {"url": url or f"#cite-note-{num}", "label": label}
    return refs
