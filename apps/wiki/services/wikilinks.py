"""Internal wiki page links: [[Title]] syntax, auto-linking, and URL resolution."""
from __future__ import annotations

import re
from urllib.parse import quote, unquote

from django.utils.text import slugify

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE_FENCE = re.compile(r"```[\s\S]*?```|`[^`]+`")
WIKIPEDIA_ARTICLE_URL = re.compile(
    r"^https?://([a-z]{2,3})\.wikipedia\.org/wiki/([^?#]+)",
    re.I,
)
RELATIVE_WIKI_PATH = re.compile(r"^/wiki/([^?#]+)/?$", re.I)
BROKEN_NESTED_LINK = re.compile(
    r"\(\[(https?://[^\]]+)\]\((https?://[^)]+)\)\)",
)


def repair_broken_nested_links(text: str) -> str:
    """Fix nested links created when highlight_urls wrapped URLs inside markdown targets."""
    return BROKEN_NESTED_LINK.sub(r"(\2)", text)


def get_published_wiki_index() -> list[tuple[str, str]]:
    """Return (title, slug) pairs sorted longest-title first."""
    from apps.wiki.models import WikiPage

    pages = list(
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED).values_list("title", "slug")
    )
    pages.sort(key=lambda item: len(item[0]), reverse=True)
    return pages


def normalize_wiki_title(title: str) -> str:
    """Normalize Wikipedia/local title for matching (strip parentheticals)."""
    clean = unquote(title.replace("_", " ")).strip()
    clean = re.sub(r"\s*\([^)]*\)\s*$", "", clean).strip()
    return clean


def resolve_wiki_slug(title: str, index: list[tuple[str, str]] | None = None) -> str | None:
    """Resolve page title, alias, or slug fragment to a published slug."""
    raw = title.strip()
    if not raw:
        return None
    needle = raw.lower()
    normalized = normalize_wiki_title(raw).lower()
    index = index or get_published_wiki_index()

    from apps.wiki.models import WikiPageAlias

    alias_hit = (
        WikiPageAlias.objects.filter(alias__iexact=raw)
        .select_related("page")
        .first()
    )
    if alias_hit and alias_hit.page.status == alias_hit.page.Status.PUBLISHED:
        return alias_hit.page.slug
    alias_hit = (
        WikiPageAlias.objects.filter(alias__iexact=normalized)
        .select_related("page")
        .first()
    )
    if alias_hit and alias_hit.page.status == alias_hit.page.Status.PUBLISHED:
        return alias_hit.page.slug

    for page_title, slug in index:
        page_lower = page_title.lower()
        page_norm = normalize_wiki_title(page_title).lower()
        if needle in {page_lower, page_norm, slug}:
            return slug
        if normalized and normalized in {page_lower, page_norm}:
            return slug
        if slug == slugify(raw) or slug == slugify(normalized):
            return slug
    return None


def _local_wiki_href(slug: str) -> str:
    return f"/wiki/{slug}/"


def _wikipedia_href(lang: str, title: str) -> str:
    encoded = quote(title.replace(" ", "_"), safe="()")
    return f"https://{lang}.wikipedia.org/wiki/{encoded}"


def process_wikilink_syntax(text: str, index: list[tuple[str, str]] | None = None) -> str:
    """Convert [[Page Title]] or [[Page Title|label]] to internal markdown links."""
    index = index or get_published_wiki_index()

    def repl(match: re.Match) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or target).strip()
        slug = resolve_wiki_slug(target, index)
        if slug:
            return f"[{label}]({_local_wiki_href(slug)})"
        lang_match = re.match(r"^([a-z]{2}):(.+)$", target, re.I)
        if lang_match:
            lang, wp_title = lang_match.group(1), lang_match.group(2).strip()
            return f"[{label}]({_wikipedia_href(lang, wp_title)})"
        return f"[{label}]({_wikipedia_href('en', target)})"

    return WIKILINK.sub(repl, text)


def resolve_markdown_links(text: str, *, exclude_slug: str = "") -> str:
    """
    Rewrite markdown link targets:
    - Wikipedia article URLs → local /wiki/slug/ when page exists
    - Relative /wiki/Title paths → local slug or valid Wikipedia URL
    - Repair nested links broken by highlight_urls
    """
    text = repair_broken_nested_links(text)
    index = get_published_wiki_index()

    def repl(match: re.Match) -> str:
        label, url = match.group(1), match.group(2).strip()

        if url.startswith("#") or url.startswith("/media/"):
            return match.group(0)

        wp = WIKIPEDIA_ARTICLE_URL.match(url)
        if wp:
            lang, wp_title = wp.group(1), unquote(wp.group(2))
            title = normalize_wiki_title(wp_title)
            slug = resolve_wiki_slug(title, index)
            if slug and slug != exclude_slug:
                return f"[{label}]({_local_wiki_href(slug)})"
            return f"[{label}]({_wikipedia_href(lang, title or wp_title)})"

        rel = RELATIVE_WIKI_PATH.match(url)
        if rel:
            fragment = unquote(rel.group(1))
            title = normalize_wiki_title(fragment)
            slug = resolve_wiki_slug(title, index)
            if slug and slug != exclude_slug:
                return f"[{label}]({_local_wiki_href(slug)})"
            if "_" in fragment or slugify(fragment) != fragment.lower().replace("_", "-"):
                return f"[{label}]({_wikipedia_href('en', title or fragment)})"
            return match.group(0)

        return match.group(0)

    return MARKDOWN_LINK.sub(repl, text)


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
                norm_title = normalize_wiki_title(title)
                if norm_title and norm_title != title:
                    pattern = re.compile(
                        rf"(?<!\[)\b({re.escape(norm_title)})\b(?!\])",
                        re.IGNORECASE,
                    )
                    if not pattern.search(updated):
                        continue
                else:
                    continue

            def link_repl(m: re.Match, _slug=slug) -> str:
                return f"[{m.group(1)}]({_local_wiki_href(_slug)})"

            updated = pattern.sub(link_repl, updated, count=1)
            linked_slugs.add(slug)
        out.append(updated)
    return "".join(out)


def process_all_wiki_links(text: str, *, exclude_slug: str = "") -> str:
    """Full link pipeline for import and render."""
    if not text:
        return text
    text = repair_broken_nested_links(text)
    if "[[" in text:
        text = process_wikilink_syntax(text)
    if "](/wiki/" in text or "wikipedia.org/wiki/" in text or "[[" in text:
        text = resolve_markdown_links(text, exclude_slug=exclude_slug)
    if get_published_wiki_index():
        text = linkify_internal_pages(text, exclude_slug=exclude_slug)
    return text
