"""Import wiki pages from external URLs."""
from __future__ import annotations

from apps.ai.services import get_ai_service
from apps.imports.sources import (
    SOURCE_AUTO,
    SOURCE_WIKIPEDIA,
    fetch_from_url,
    list_supported_sources,
)
from apps.wiki.models import WikiPage
from apps.wiki.services.markdown import extract_summary, split_markdown_into_sections
from apps.wiki.services.pages import create_page_from_markdown


def preview_url_import(
    url: str,
    *,
    source_type: str = SOURCE_AUTO,
    use_ai: bool = False,
    max_feed_entries: int = 25,
    download_media: bool = False,
    user=None,
) -> dict:
    """Fetch URL content and return preview payload without saving."""
    from apps.imports.sources.detect import detect_source_type
    from apps.imports.sources.wikipedia import fetch_wikipedia

    url = (url or "").strip()
    resolved = source_type if source_type != SOURCE_AUTO else detect_source_type(url)
    user_id = getattr(user, "pk", None)

    if resolved == SOURCE_WIKIPEDIA:
        fetched = fetch_wikipedia(url, download_media=download_media, user_id=user_id)
    else:
        fetched = fetch_from_url(url, source_type=source_type, max_feed_entries=max_feed_entries)
    markdown = fetched["markdown"]
    title = fetched["title"]
    service = get_ai_service()
    ai_used = False

    if use_ai and service.is_configured:
        enriched = service.enrich_import(markdown, title=title)
        markdown = enriched["markdown"]
        title = enriched.get("title") or title
        summary = enriched.get("summary") or extract_summary(markdown)
        ai_used = True
    else:
        summary = extract_summary(markdown)

    sections = split_markdown_into_sections(markdown)
    return {
        "title": title,
        "markdown": markdown,
        "summary": summary,
        "sections": sections,
        "section_count": len(sections),
        "source_type": fetched["source_type"],
        "source_url": fetched["source_url"],
        "source_label": fetched["source_label"],
        "meta": fetched.get("meta", {}),
        "ai_used": ai_used,
    }


def import_url_as_wiki_page(
    url: str,
    *,
    title: str = "",
    author=None,
    source_type: str = SOURCE_AUTO,
    use_ai: bool = False,
    publish: bool = False,
    max_feed_entries: int = 25,
    download_media: bool = False,
) -> WikiPage:
    """Fetch remote content and create a wiki page."""
    preview = preview_url_import(
        url,
        source_type=source_type,
        use_ai=use_ai,
        max_feed_entries=max_feed_entries,
        download_media=download_media,
        user=author,
    )
    resolved_title = title or preview["title"]
    status = WikiPage.Status.PUBLISHED if publish else WikiPage.Status.DRAFT
    page = create_page_from_markdown(
        title=resolved_title,
        content=preview["markdown"],
        author=author,
        status=status,
        split_sections=True,
    )
    if preview.get("summary"):
        page.summary = preview["summary"]
        page.save(update_fields=["summary", "updated_at"])
    return page


def get_supported_sources() -> list[dict]:
    return list_supported_sources()
