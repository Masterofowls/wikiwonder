"""Wiki page creation, update, section sync, and revision history."""
from django.utils import timezone

from apps.wiki.models import PageRevision, WikiPage, WikiSection
from apps.wiki.services.markdown import extract_summary, split_markdown_into_sections


def create_page_from_markdown(
    title: str,
    content: str,
    *,
    author=None,
    category=None,
    status=WikiPage.Status.DRAFT,
    split_sections: bool = True,
) -> WikiPage:
    """Create a wiki page from markdown, optionally splitting into sections."""
    summary = extract_summary(content)
    page = WikiPage.objects.create(
        title=title,
        content=content,
        summary=summary,
        author=author,
        category=category,
        status=status,
        published_at=timezone.now() if status == WikiPage.Status.PUBLISHED else None,
    )

    if split_sections:
        sync_page_sections(page, content)

    _maybe_auto_translate(page)
    return page


def sync_page_sections(page: WikiPage, content: str | None = None) -> list[WikiSection]:
    """Split page content into sections and sync to database."""
    content = content or page.content
    sections_data = split_markdown_into_sections(content)

    page.sections.all().delete()
    created = []
    for data in sections_data:
        section = WikiSection.objects.create(
            page=page,
            title=data["title"],
            content=data["content"],
            order=data["order"],
            anchor=data["anchor"],
        )
        created.append(section)
    return created


def save_page_revision(page: WikiPage, *, editor, change_summary: str = "") -> PageRevision:
    return PageRevision.objects.create(
        page=page,
        editor=editor,
        title=page.title,
        content=page.content or "",
        change_summary=change_summary[:255],
    )


def update_page_content(
    page: WikiPage,
    content: str,
    *,
    editor=None,
    change_summary: str = "",
    resplit: bool = True,
) -> WikiPage:
    """Update page markdown, save revision, and optionally re-split sections."""
    if editor and (page.content or "") != content:
        save_page_revision(page, editor=editor, change_summary=change_summary)

    from apps.wiki.services.media_links import normalize_media_markdown

    content = normalize_media_markdown(content)
    page.content = content
    page.summary = extract_summary(content)
    page.save(update_fields=["content", "summary", "updated_at"])

    if resplit:
        sync_page_sections(page, content)

    _maybe_auto_translate(page, force=True)
    return page


def _maybe_auto_translate(page: WikiPage, *, force: bool = False) -> None:
    """Generate modeltranslation fields via Lara Translate when configured."""
    from apps.wiki.services.lara_translate import auto_translate_wiki_page

    auto_translate_wiki_page(page, force=force)
