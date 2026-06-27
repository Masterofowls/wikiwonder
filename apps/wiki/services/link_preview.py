"""Fetch Open Graph metadata for shared link previews."""
from __future__ import annotations

import contextlib
from html.parser import HTMLParser
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

if TYPE_CHECKING:
    from apps.wiki.models import SharedLink

USER_AGENT = "WikiWonder/1.0 LinkPreview (+https://github.com/wikiwonder)"
TIMEOUT = 8.0


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta: dict[str, str] = {}
        self.title = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "meta":
            key = attrs_dict.get("property") or attrs_dict.get("name", "")
            content = attrs_dict.get("content", "")
            if key and content:
                self.meta[key.lower()] = content
        elif tag == "title" and not self.title:
            self._in_title = True

    def handle_data(self, data):
        if getattr(self, "_in_title", False):
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def _extract_meta(html: str) -> dict[str, str]:
    parser = _MetaParser()
    with contextlib.suppress(Exception):
        parser.feed(html[:500_000])
    return parser.meta | ({"title": parser.title.strip()} if parser.title else {})


def fetch_link_preview(url: str) -> dict:
    """Fetch OG metadata for a URL. Returns preview dict safe for templates/API."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must use http or https")

    with httpx.Client(follow_redirects=True, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        html = resp.text

    meta = _extract_meta(html)
    title = (
        meta.get("og:title")
        or meta.get("twitter:title")
        or meta.get("title")
        or parsed.netloc
    )
    description = (
        meta.get("og:description")
        or meta.get("twitter:description")
        or meta.get("description")
        or ""
    )
    image = meta.get("og:image") or meta.get("twitter:image") or ""
    site_name = meta.get("og:site_name") or parsed.netloc.replace("www.", "")

    if image and image.startswith("/"):
        image = f"{parsed.scheme}://{parsed.netloc}{image}"

    favicon = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

    return {
        "url": url,
        "title": title[:255],
        "description": description[:1000],
        "image_url": image[:2048],
        "favicon_url": favicon[:2048],
        "site_name": site_name[:120],
    }


def enrich_shared_link(link: SharedLink) -> SharedLink:
    """Populate SharedLink fields from live URL metadata."""
    from apps.wiki.models import SharedLink

    if not isinstance(link, SharedLink):
        raise TypeError("Expected SharedLink instance")

    try:
        data = fetch_link_preview(link.url)
        link.title = link.title or data["title"]
        link.description = link.description or data["description"]
        link.image_url = link.image_url or data["image_url"]
        link.favicon_url = link.favicon_url or data["favicon_url"]
        link.site_name = link.site_name or data["site_name"]
    except Exception:
        if not link.title:
            link.title = urlparse(link.url).netloc
        if not link.site_name:
            link.site_name = urlparse(link.url).netloc.replace("www.", "")
    return link
