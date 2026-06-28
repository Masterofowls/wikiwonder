"""Internal wiki page links: [[Title]] syntax and auto-linking."""
from __future__ import annotations

import re

from django.utils.text import slugify

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
CODE_FENCE = re.compile(r"```[\s\S]*?```|`[^`]+`")


def get_published_wiki_index() -> list[tuple[str, str]]:
    """Return (title, slug) pairs sorted longest-title first."""
    from apps.wiki.models import WikiPage

    pages = list(
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED).values_list("title", "slug")
    )
    pages.sort(key=lambda item: len(item[0]), reverse=True)
    return pages


def resolve_wiki_slug(title: str, index: list[tuple[str, str]] | None = None) -> str | None:
    """Resolve page title or slug fragment to a published slug."""
    needle = title.strip().lower()
    if not needle:
        return None
    index = index or get_published_wiki_index()
    for page_title, slug in index:
        if page_title.lower() == needle or slug == slugify(title):
            return slug
    return None


def process_wikilink_syntax(text: str, index: list[tuple[str, str]] | None = None) -> str:
    """Convert [[Page Title]] or [[Page Title|label]] to internal markdown links."""
    index = index or get_published_wiki_index()

    def repl(match: re.Match) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or target).strip()
        slug = resolve_wiki_slug(target, index)
        if not slug:
            return label
        return f"[{label}](/wiki/{slug}/)"

    return WIKILINK.sub(repl, text)


def _split_protected(text: str) -> list[tuple[str, bool]]:
    """Split text into (segment, is_protected) alternating chunks."""
    parts: list[tuple[str, bool]] = []
    last = 0
    for match in MARKDOWN_LINK.finditer(text):
        if match.start() > last:
            parts.append((text[last : match.start()], False))
        parts.append((match.group(0), True))
        last = match.end()
    if last < len(text):
        parts.append((text[last:], False))
    return parts or [(text, False)]


def linkify_internal_pages(text: str, *, exclude_slug: str = "") -> str:
    """Auto-link phrases that match published wiki page titles (first match per title)."""
    index = [(t, s) for t, s in get_published_wiki_index() if s != exclude_slug]
    if not index:
        return text

    segments = _split_protected(text)
    out: list[str] = []
    linked_slugs: set[str] = set()

    for chunk, protected in segments:
        if protected:
            out.append(chunk)
            continue
        updated = chunk
        for title, slug in index:
            if slug in linked_slugs:
                continue
            pattern = re.compile(rf"(?<!\[)\b({re.escape(title)})\b(?!\])", re.IGNORECASE)
            if not pattern.search(updated):
                continue

            def link_repl(m: re.Match, _slug=slug) -> str:
                return f"[{m.group(1)}](/wiki/{_slug}/)"

            updated = pattern.sub(link_repl, updated, count=1)
            linked_slugs.add(slug)
        out.append(updated)
    return "".join(out)
