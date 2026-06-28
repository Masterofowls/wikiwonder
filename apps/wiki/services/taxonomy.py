"""Category and tag helpers for wiki pages."""
from __future__ import annotations

import re

from django.utils.text import slugify

from apps.wiki.models import Category, Tag, WikiPage


def parse_tag_names(raw: str) -> list[str]:
    """Split comma/semicolon/newline-separated tag names."""
    if not raw:
        return []
    parts = re.split(r"[,;\n]+", raw)
    seen: set[str] = set()
    names: list[str] = []
    for part in parts:
        name = part.strip()[:60]
        key = name.lower()
        if name and key not in seen:
            seen.add(key)
            names.append(name)
    return names


def get_or_create_tags(names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in names:
        slug = slugify(name) or "tag"
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
        if tag.name != name:
            tag.name = name
            tag.save(update_fields=["name"])
        tags.append(tag)
    return tags


def create_category(*, name: str, description: str = "") -> Category:
    name = name.strip()[:120]
    if not name:
        raise ValueError("Category name is required")
    slug = slugify(name) or "category"
    base = slug
    counter = 1
    while Category.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return Category.objects.create(name=name, slug=slug, description=description.strip()[:500])


def apply_page_taxonomy(
    page: WikiPage,
    *,
    category_id: str | None = None,
    new_category_name: str = "",
    tag_names: list[str] | None = None,
    user=None,
) -> None:
    """Assign category and tags to a wiki page."""
    if new_category_name.strip() and user and getattr(user, "is_staff", False):
        page.category = create_category(name=new_category_name)
        page.save(update_fields=["category", "updated_at"])
    elif category_id:
        try:
            page.category = Category.objects.get(pk=int(category_id))
            page.save(update_fields=["category", "updated_at"])
        except (Category.DoesNotExist, ValueError, TypeError):
            pass
    elif category_id == "":
        page.category = None
        page.save(update_fields=["category", "updated_at"])

    if tag_names is not None:
        tags = get_or_create_tags(tag_names)
        page.tags.set(tags)


def suggest_tags(query: str, *, limit: int = 12) -> list[dict]:
    query = query.strip()
    if len(query) < 1:
        return []
    tags = Tag.objects.filter(name__icontains=query).order_by("name")[:limit]
    return [{"name": t.name, "slug": t.slug} for t in tags]
