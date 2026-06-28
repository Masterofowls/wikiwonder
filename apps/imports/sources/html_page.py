"""Generic HTML page and documentation site import."""
from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from apps.imports.sources.convert import (
    build_attribution_block,
    html_to_markdown,
    wrap_with_source_embed,
)
from apps.imports.sources.fetch import FetchError, fetch_text, origin_of

CONTENT_SELECTORS = (
    "article",
    "main",
    '[role="main"]',
    ".documentation",
    ".document",
    ".markdown-body",
    ".rst-content",
    ".bd-content",
    ".page-content",
    ".content",
    ".post-content",
    ".entry-content",
    "#content",
    "#main-content",
    ".wiki-content",
    ".mw-parser-output",
)


def _extract_main_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html5lib")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        title = og["content"].strip()

    for selector in CONTENT_SELECTORS:
        node = soup.select_one(selector)
        if node and len(node.get_text(strip=True)) > 200:
            return str(node), title

    body = soup.body or soup
    return str(body), title


def fetch_html_page(url: str, *, source_label: str = "Web page") -> dict:
    html, content_type = fetch_text(url)
    if "html" not in content_type.lower() and "<html" not in html[:500].lower():
        raise FetchError("URL did not return HTML content")

    content_html, page_title = _extract_main_html(html)
    if not page_title:
        page_title = urlparse(url).path.rstrip("/").split("/")[-1].replace("-", " ").title() or "Imported page"

    body_md = html_to_markdown(content_html, base_url=origin_of(url))
    if len(body_md.strip()) < 80:
        raise FetchError("Page content too short — try a direct article URL")

    attribution = build_attribution_block(
        title=page_title,
        source_url=url,
        source_label=source_label,
    )
    markdown = wrap_with_source_embed(url, page_title, f"{attribution}\n\n{body_md}")

    return {
        "title": page_title,
        "markdown": markdown,
        "source_type": "web" if source_label == "Web page" else "docs",
        "source_url": url,
        "source_label": source_label,
        "meta": {"content_type": content_type},
    }


def fetch_docs(url: str) -> dict:
    host = urlparse(url).netloc.lower()
    label = "Documentation"
    if "readthedocs" in host:
        label = "Read the Docs"
    elif "gitbook" in host:
        label = "GitBook"
    return fetch_html_page(url, source_label=label)
