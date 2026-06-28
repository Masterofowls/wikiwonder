"""Apply Wikipedia import metadata (tags, cover, aliases) to a wiki page."""
from __future__ import annotations

from django.core.files.base import ContentFile
from django.utils.text import slugify

from apps.imports.sources.wikipedia_media import download_cover_file
from apps.wiki.models import Tag, WikiPage, WikiPageAlias


def apply_wikipedia_tags(page: WikiPage, category_names: list[str]) -> int:
    """Map Wikipedia categories to Tag M2M; returns count attached."""
    if not category_names:
        return 0
    tags: list[Tag] = []
    for name in category_names:
        clean = name.strip()[:60]
        if not clean:
            continue
        tag, _ = Tag.objects.get_or_create(
            slug=slugify(clean) or "tag",
            defaults={"name": clean},
        )
        tags.append(tag)
    if tags:
        page.tags.add(*tags)
    return len(tags)


def apply_wikipedia_aliases(page: WikiPage, titles: list[str]) -> int:
    """Store alternate titles for fuzzy wikilink resolution."""
    seen: set[str] = set()
    count = 0
    for title in titles:
        for candidate in (title.strip(), title.replace("_", " ").strip()):
            if not candidate or candidate.lower() in seen:
                continue
            seen.add(candidate.lower())
            WikiPageAlias.objects.get_or_create(page=page, alias=candidate)
            count += 1
    return count


def apply_wikipedia_cover(page: WikiPage, cover_image: dict | None) -> bool:
    """Download lead/thumbnail image as page cover when none set."""
    if page.cover_image or not cover_image:
        return False
    downloaded = download_cover_file(cover_image)
    if not downloaded:
        return False
    body, ext = downloaded
    filename = f"{page.slug or slugify(page.title) or 'cover'}-cover.{ext}"
    page.cover_image.save(filename, ContentFile(body), save=True)
    return True


def apply_wikipedia_import_metadata(page: WikiPage, preview: dict) -> dict:
    """Persist tags, aliases, cover image, and source URL from import preview."""
    meta = preview.get("meta") or {}
    applied: dict = {}

    source_url = preview.get("source_url") or ""
    if source_url and not page.source_url:
        page.source_url = source_url
        page.save(update_fields=["source_url", "updated_at"])
        applied["source_url"] = source_url

    tag_count = apply_wikipedia_tags(page, meta.get("categories") or [])
    if tag_count:
        applied["tags"] = tag_count

    alias_titles = [preview.get("title", "")]
    alias_titles.extend(meta.get("alias_titles") or [])
    alias_count = apply_wikipedia_aliases(page, alias_titles)
    if alias_count:
        applied["aliases"] = alias_count

    if apply_wikipedia_cover(page, meta.get("cover_image")):
        applied["cover_image"] = True

    return applied
