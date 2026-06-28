"""Wikipedia article import via the MediaWiki parse API."""
from __future__ import annotations

from urllib.parse import quote, urlencode

from bs4 import BeautifulSoup

from apps.imports.sources.convert import (
    build_attribution_block,
    wrap_with_source_embed,
)
from apps.imports.sources.detect import wikipedia_page_title
from apps.imports.sources.fetch import FetchError, fetch_json, origin_of
from apps.imports.sources.wikipedia_categories import fetch_wikipedia_categories
from apps.imports.sources.wikipedia_citations import (
    fetch_wikipedia_citations,
    validate_citation_refs,
)
from apps.imports.sources.wikipedia_diagrams import embed_missing_diagrams
from apps.imports.sources.wikipedia_html import wikipedia_html_to_markdown
from apps.imports.sources.wikipedia_media import (
    enrich_markdown_with_lead_media,
    extract_inline_media,
    fetch_lead_image,
    fetch_page_images,
    mirror_media_to_storage,
    pick_cover_image,
)
from apps.wiki.services.citations import replace_numeric_citations
from apps.wiki.services.wikilinks import process_all_wiki_links


def fetch_wikipedia(
    url: str,
    *,
    download_media: bool = False,
    user_id: int | None = None,
) -> dict:
    """
    Fetch a Wikipedia article and convert to WikiWonder markdown.

    Strips navboxes/templates, preserves sections/tables/citations/media,
    resolves wikilinks, and optionally mirrors media to local storage.
    """
    parsed = wikipedia_page_title(url)
    if not parsed:
        raise FetchError("Not a valid Wikipedia article URL")

    lang, page_title = parsed
    api_base = f"https://{lang}.wikipedia.org/w/api.php"
    params = urlencode(
        {
            "action": "parse",
            "page": page_title,
            "prop": "text|displaytitle|sections|images",
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
    raw_html = parse_data["text"]["*"]
    display_title = BeautifulSoup(parse_data.get("displaytitle", page_title), "html.parser").get_text()
    canonical = f"https://{lang}.wikipedia.org/wiki/{quote(page_title.replace(' ', '_'))}"
    base_url = origin_of(url)

    body_md = wikipedia_html_to_markdown(raw_html, base_url=base_url, lang=lang)
    refs = fetch_wikipedia_citations(canonical)
    refs = validate_citation_refs(refs)
    body_md = replace_numeric_citations(body_md, refs)
    body_md = process_all_wiki_links(body_md)

    inline_media = extract_inline_media(raw_html, base_url=base_url)
    api_media = fetch_page_images(lang, page_title, limit=60)
    all_media = inline_media + [m for m in api_media if m["url"] not in {x["url"] for x in inline_media}]
    lead_image = fetch_lead_image(lang, page_title)
    cover_candidate = pick_cover_image(all_media, lead_image)
    categories = fetch_wikipedia_categories(lang, page_title)

    url_map: dict[str, str] = {}
    if download_media and all_media:
        url_map = mirror_media_to_storage(all_media, user_id=user_id)
        if url_map:
            for remote, local in url_map.items():
                body_md = body_md.replace(remote, local)
    else:
        body_md = embed_missing_diagrams(body_md, all_media, url_map=url_map)
        body_md = enrich_markdown_with_lead_media(body_md, all_media, max_embeds=6)

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
        {
            "index": s.get("index"),
            "title": s.get("line"),
            "level": int(s.get("level", 2)),
            "anchor": s.get("anchor", ""),
        }
        for s in parse_data.get("sections", [])
        if s.get("line") and s.get("line") not in ("References", "External links", "See also")
    ]

    return {
        "title": display_title,
        "markdown": markdown,
        "source_type": "wikipedia",
        "source_url": canonical,
        "source_label": source_label,
        "meta": {
            "lang": lang,
            "sections": sections[:50],
            "section_count": len(sections),
            "media": all_media[:30],
            "media_count": len(all_media),
            "citation_count": len(refs),
            "mirrored_media": len(url_map),
            "categories": categories,
            "cover_image": cover_candidate,
            "alias_titles": [display_title, page_title],
            "citation_status": {
                num: ref.get("status", "unknown") for num, ref in refs.items()
            },
        },
    }
