"""Extract and analyze wiki links between pages."""
from __future__ import annotations

import re
from urllib.parse import unquote

from apps.wiki.models import WikiPage
from apps.wiki.services.wikilinks import (
    WIKIPEDIA_ARTICLE_URL,
    normalize_wiki_title,
    resolve_wiki_slug,
)

INTERNAL_LINK = re.compile(r"\]\(/wiki/([^)/\s]+)/?\)")
WIKILINK_SYNTAX = re.compile(r"\[\[([^\]|]+)")
EXTERNAL_MD = re.compile(r"\]\((https?://[^)]+)\)")


def extract_link_targets(content: str) -> dict:
    """Return {internal_slugs, wikipedia_titles, external_urls} from markdown."""
    internal: set[str] = set()
    wikipedia: set[str] = set()
    external: set[str] = set()

    for match in INTERNAL_LINK.finditer(content or ""):
        slug = unquote(match.group(1)).strip("/")
        if slug:
            internal.add(slug)

    for match in EXTERNAL_MD.finditer(content or ""):
        url = match.group(1).strip()
        wp = WIKIPEDIA_ARTICLE_URL.match(url)
        if wp:
            wikipedia.add(normalize_wiki_title(unquote(wp.group(2))))
        elif url.startswith("http"):
            external.add(url)

    for match in WIKILINK_SYNTAX.finditer(content or ""):
        title = match.group(1).strip()
        slug = resolve_wiki_slug(title)
        if slug:
            internal.add(slug)
        else:
            wikipedia.add(normalize_wiki_title(title))

    return {
        "internal_slugs": sorted(internal),
        "wikipedia_titles": sorted(wikipedia),
        "external_urls": sorted(external),
    }


def get_backlinks(slug: str) -> list[WikiPage]:
    """Pages that link to the given slug (published only)."""
    slug = slug.strip("/")
    pages = WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED).only(
        "id", "title", "slug", "content", "summary"
    )
    results: list[WikiPage] = []
    needles = (
        f"](/wiki/{slug}/)",
        f"](/wiki/{slug})",
        f"/wiki/{slug}/",
    )
    for page in pages:
        if page.slug == slug:
            continue
        body = page.content or ""
        if any(n in body for n in needles):
            results.append(page)
            continue
        targets = extract_link_targets(body)
        if slug in targets["internal_slugs"]:
            results.append(page)
    return results
