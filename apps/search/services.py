"""Unified instant search across wiki pages, shared links, and CMS content."""
from __future__ import annotations

from django.apps import apps
from django.db import connection
from django.db.models import Count, Q
from django.urls import reverse

from apps.wiki.models import Category, SharedLink, Tag, WikiPage


def _snippet(text: str, max_len: int = 120) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1].rstrip()}…"


def _wiki_page_filter(query: str) -> Q:
    return (
        Q(title__icontains=query)
        | Q(summary__icontains=query)
        | Q(content__icontains=query)
        | Q(category__name__icontains=query)
        | Q(tags__name__icontains=query)
    )


def _wiki_results_icontains(query: str, limit: int) -> list[dict]:
    pages = (
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
        .filter(_wiki_page_filter(query))
        .select_related("category")
        .prefetch_related("tags")
        .distinct()
        .order_by("-updated_at")[:limit]
    )
    return [_wiki_hit(page) for page in pages]


def _wiki_hit(page: WikiPage) -> dict:
    tag_names = ", ".join(t.name for t in page.tags.all()[:4])
    category = page.category.name if page.category else ""
    meta = category or tag_names
    return {
        "type": "wiki",
        "title": page.title,
        "url": page.get_absolute_url(),
        "snippet": _snippet(page.summary or page.content),
        "category": category,
        "tags": tag_names,
        "meta": meta,
    }


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
        .filter(Q(rank__gte=0.01) | _wiki_page_filter(query))
        .select_related("category")
        .prefetch_related("tags")
        .distinct()
        .order_by("-rank", "-updated_at")[:limit]
    )
    return [_wiki_hit(page) for page in pages]


def _category_results(query: str, limit: int) -> list[dict]:
    cats = (
        Category.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
        .annotate(page_count=Count("pages", filter=Q(pages__status=WikiPage.Status.PUBLISHED)))
        .order_by("name")[:limit]
    )
    return [
        {
            "type": "category",
            "title": cat.name,
            "url": reverse("wiki:category", kwargs={"slug": cat.slug}),
            "snippet": _snippet(cat.description or f"{cat.page_count} wiki pages"),
            "category": "Category",
            "tags": "",
            "meta": f"{cat.page_count} pages",
        }
        for cat in cats
    ]


def _tag_results(query: str, limit: int) -> list[dict]:
    tags = (
        Tag.objects.filter(name__icontains=query)
        .annotate(page_count=Count("pages", filter=Q(pages__status=WikiPage.Status.PUBLISHED)))
        .order_by("name")[:limit]
    )
    return [
        {
            "type": "tag",
            "title": tag.name,
            "url": f"{reverse('wiki:home')}?q={tag.name}",
            "snippet": f"Tag · {tag.page_count} wiki page{'s' if tag.page_count != 1 else ''}",
            "category": "Tag",
            "tags": "",
            "meta": f"{tag.page_count} pages",
        }
        for tag in tags
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
            "category": link.site_name or "Link",
            "tags": "",
            "meta": link.site_name or "External link",
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
                "category": "CMS",
                "tags": "",
                "meta": "CMS page",
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
                "category": "CMS",
                "tags": "",
                "meta": "CMS page",
            }
        )
    return results


def _collect_search_results(query: str, *, fetch_limit: int = 40) -> list[dict]:
    """Gather and rank all result types."""
    query = query.strip()
    if len(query) < 2:
        return []

    per_type = max(4, fetch_limit // 5)
    if connection.vendor == "postgresql":
        wiki = _wiki_results_postgres(query, per_type)
        cms = _cms_results_postgres(query, per_type)
    else:
        wiki = _wiki_results_icontains(query, per_type)
        cms = _cms_results_icontains(query, per_type)

    categories = _category_results(query, per_type)
    tags = _tag_results(query, per_type)
    links = _link_results(query, per_type)

    type_order = {"wiki": 0, "category": 1, "tag": 2, "link": 3, "cms": 4}
    combined = wiki + categories + tags + links + cms
    combined.sort(key=lambda item: type_order.get(item["type"], 9))
    return combined


def instant_search(query: str, *, limit: int = 8) -> dict:
    """Return ranked search hits for live typeahead and API consumers."""
    query = query.strip()
    empty = {"results": [], "count": 0, "total": 0, "has_more": False}
    if len(query) < 2:
        return empty

    combined = _collect_search_results(query, fetch_limit=max(limit * 3, 24))
    total = len(combined)
    results = combined[:limit]
    return {
        "results": results,
        "count": len(results),
        "total": total,
        "has_more": total > limit,
    }


def home_search(query: str, *, limit: int = 12) -> dict:
    """Inline search preview on the home page."""
    return instant_search(query, limit=limit)


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
            .filter(Q(rank__gte=0.01) | _wiki_page_filter(query))
            .select_related("category")
            .prefetch_related("tags")
            .distinct()
            .order_by("-rank", "-updated_at")
        )
    return (
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
        .filter(_wiki_page_filter(query))
        .select_related("category")
        .prefetch_related("tags")
        .distinct()
        .order_by("-updated_at")
    )


def full_search_bundle(query: str) -> dict:
    """Payload for the dedicated search results page."""
    query = query.strip()
    pages = list(wiki_page_queryset(query))
    combined = _collect_search_results(query, fetch_limit=60)
    categories = [r for r in combined if r["type"] == "category"]
    tags = [r for r in combined if r["type"] == "tag"]
    links = [r for r in combined if r["type"] == "link"]
    return {
        "pages": pages,
        "categories": categories,
        "tags": tags,
        "links": links,
        "total": len(pages) + len(categories) + len(tags) + len(links),
    }
