"""Wikipedia article import via the MediaWiki parse API."""
from __future__ import annotations

import re
from urllib.parse import quote, urlencode

from bs4 import BeautifulSoup

from apps.imports.sources.convert import (
    build_attribution_block,
    html_to_markdown,
    wrap_with_source_embed,
)
from apps.imports.sources.detect import wikipedia_page_title
from apps.imports.sources.fetch import FetchError, fetch_json, origin_of
from apps.wiki.services.citations import replace_numeric_citations
from apps.imports.sources.wikipedia_citations import fetch_wikipedia_citations
from apps.wiki.services.wikilinks import linkify_internal_pages, process_wikilink_syntax


def _inline_citation_markers(root) -> None:
    """Replace Wikipedia <sup class="reference"> with [n] markers before HTML→markdown."""
    for sup in root.select("sup.reference"):
        link = sup.select_one("a")
        label = link.get_text(strip=True) if link else sup.get_text(strip=True)
        num = re.sub(r"[^\d]", "", label) or label.strip("[]")
        if num:
            sup.replace_with(f"[{num}]")


def _clean_wikipedia_html(html: str) -> str:
    soup = BeautifulSoup(html, "html5lib")
    root = soup.select_one(".mw-parser-output") or soup
    _inline_citation_markers(root)
    for selector in (
        ".navbox",
        ".vertical-navbox",
        ".metadata",
        ".noprint",
        ".mw-editsection",
        ".mw-references-wrap",
        ".hatnote",
        ".sistersitebox",
        ".ambox",
        ".toc",
    ):
        for node in root.select(selector):
            node.decompose()
    return str(root)


def fetch_wikipedia(url: str) -> dict:
    parsed = wikipedia_page_title(url)
    if not parsed:
        raise FetchError("Not a valid Wikipedia article URL")

    lang, page_title = parsed
    api_base = f"https://{lang}.wikipedia.org/w/api.php"
    params = urlencode(
        {
            "action": "parse",
            "page": page_title,
            "prop": "text|displaytitle|sections",
            "format": "json",
            "redirects": "1",
            "disableeditsection": "1",
            "disabletoc": "1",
        }
    )
    data = fetch_json(f"{api_base}?{params}")
    if "error" in data:
        raise FetchError(data["error"].get("info", "Wikipedia API error"))

    parse_data = data["parse"]
    display_title = BeautifulSoup(parse_data.get("displaytitle", page_title), "html.parser").get_text()
    html = _clean_wikipedia_html(parse_data["text"]["*"])
    canonical = f"https://{lang}.wikipedia.org/wiki/{quote(page_title.replace(' ', '_'))}"

    body_md = html_to_markdown(html, base_url=origin_of(url))
    refs = fetch_wikipedia_citations(canonical)
    body_md = replace_numeric_citations(body_md, refs)
    body_md = process_wikilink_syntax(body_md)
    body_md = linkify_internal_pages(body_md)
    attribution = build_attribution_block(
        title=display_title,
        source_url=canonical,
        source_label=f"Wikipedia ({lang.upper()})",
        license_note="Content under CC BY-SA — verify license before republishing.",
    )
    source_label = f"Wikipedia ({lang.upper()})"
    markdown = f"{attribution}\n\n{body_md}"
    markdown = wrap_with_source_embed(canonical, display_title, markdown)

    sections = [
        {"index": s.get("index"), "title": s.get("line"), "level": s.get("level")}
        for s in parse_data.get("sections", [])
        if s.get("line") and s.get("toclevel", "2") in ("1", "2")
    ]

    return {
        "title": display_title,
        "markdown": markdown,
        "source_type": "wikipedia",
        "source_url": canonical,
        "source_label": source_label,
        "meta": {
            "lang": lang,
            "sections": sections[:40],
            "section_count": len(sections),
        },
    }
