"""Unified instant search across wiki pages, shared links, and CMS content."""
from __future__ import annotations

from django.apps import apps
from django.db import connection
from django.db.models import Q

from apps.wiki.models import SharedLink, WikiPage


def _snippet(text: str, max_len: int = 120) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1].rstrip()}…"


def _wiki_results_icontains(query: str, limit: int) -> list[dict]:
    pages = (
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
        .filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query))
        .select_related("category")
        .order_by("-updated_at")[:limit]
    )
    return [
        {
            "type": "wiki",
            "title": page.title,
            "url": page.get_absolute_url(),
            "snippet": _snippet(page.summary or page.content),
            "category": page.category.name if page.category else "",
        }
        for page in pages
    ]


def _wiki_results_postgres(query: str, limit: int) -> list[dict]:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

    vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("summary", weight="B", config="english")
        + SearchVector("content", weight="C", config="english")
    )
    search_query = SearchQuery(query, search_type="websearch", config="english")
    pages = (
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
        .annotate(rank=SearchRank(vector, search_query))
        .filter(rank__gte=0.01)
        .select_related("category")
        .order_by("-rank", "-updated_at")[:limit]
    )
    return [
        {
            "type": "wiki",
            "title": page.title,
            "url": page.get_absolute_url(),
            "snippet": _snippet(page.summary or page.content),
            "category": page.category.name if page.category else "",
        }
        for page in pages
    ]


def _link_results(query: str, limit: int) -> list[dict]:
    links = (
        SharedLink.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(site_name__icontains=query)
        )
        .order_by("-is_featured", "-created_at")[:limit]
    )
    return [
        {
            "type": "link",
            "title": link.title,
            "url": link.get_absolute_url(),
            "snippet": _snippet(link.description or link.site_name or link.url),
            "category": link.site_name or "",
        }
        for link in links
    ]


def _cms_results_icontains(query: str, limit: int) -> list[dict]:
    if not apps.is_installed("cms"):
        return []
    from cms.models import PageContent

    contents = (
        PageContent.objects.filter(title__icontains=query)
        .select_related("page")
        .order_by("-creation_date")[:limit]
    )
    results = []
    for content in contents:
        page = content.page
        if page is None:
            continue
        try:
            url = page.get_absolute_url()
        except Exception:
            continue
        results.append(
            {
                "type": "cms",
                "title": content.title,
                "url": url,
                "snippet": "CMS page",
                "category": "Pages",
            }
        )
    return results


def _cms_results_postgres(query: str, limit: int) -> list[dict]:
    if not apps.is_installed("cms"):
        return []
    from cms.models import PageContent
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

    vector = SearchVector("title", weight="A", config="english")
    search_query = SearchQuery(query, search_type="websearch", config="english")
    contents = (
        PageContent.objects.annotate(rank=SearchRank(vector, search_query))
        .filter(rank__gte=0.01)
        .select_related("page")
        .order_by("-rank", "-creation_date")[:limit]
    )
    results = []
    for content in contents:
        page = content.page
        if page is None:
            continue
        try:
            url = page.get_absolute_url()
        except Exception:
            continue
        results.append(
            {
                "type": "cms",
                "title": content.title,
                "url": url,
                "snippet": "CMS page",
                "category": "Pages",
            }
        )
    return results


def instant_search(query: str, *, limit: int = 8) -> list[dict]:
    """Return ranked search hits for live typeahead and API consumers."""
    query = query.strip()
    if len(query) < 2:
        return []

    per_type = max(3, limit // 3)
    if connection.vendor == "postgresql":
        wiki = _wiki_results_postgres(query, per_type)
        cms = _cms_results_postgres(query, per_type)
    else:
        wiki = _wiki_results_icontains(query, per_type)
        cms = _cms_results_icontains(query, per_type)
    links = _link_results(query, per_type)

    combined = wiki + cms + links
    return combined[:limit]


def wiki_page_queryset(query: str):
    """Queryset for full search page (wiki pages only)."""
    query = query.strip()
    if not query:
        return WikiPage.objects.none()
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        vector = (
            SearchVector("title", weight="A", config="english")
            + SearchVector("summary", weight="B", config="english")
            + SearchVector("content", weight="C", config="english")
        )
        search_query = SearchQuery(query, search_type="websearch", config="english")
        return (
            WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
            .annotate(rank=SearchRank(vector, search_query))
            .filter(rank__gte=0.01)
            .select_related("category")
            .order_by("-rank", "-updated_at")
        )
    return (
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
        .filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query))
        .select_related("category")
        .order_by("-updated_at")
    )
