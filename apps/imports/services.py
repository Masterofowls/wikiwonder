"""Automatic text import, conversion, and wiki page creation."""
import re

from apps.ai.services import get_ai_service
from apps.wiki.models import WikiPage
from apps.wiki.services.markdown import extract_summary, split_markdown_into_sections
from apps.wiki.services.pages import create_page_from_markdown


def plain_text_to_markdown(text: str) -> str:
    """Basic heuristic conversion without AI."""
    lines = text.strip().splitlines()
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                in_list = False
            result.append("")
            continue

        # Detect headings (ALL CAPS lines or numbered sections)
        if stripped.isupper() and len(stripped) > 3 and len(stripped) < 80:
            result.append(f"## {stripped.title()}")
            continue

        section_match = re.match(r"^(?:Section|Chapter|\d+\.)\s+(.+)$", stripped, re.I)
        if section_match:
            result.append(f"## {section_match.group(1)}")
            continue

        # Bullet points
        if re.match(r"^[-•*]\s+", stripped):
            if not in_list:
                in_list = True
            result.append(re.sub(r"^[-•*]\s+", "- ", stripped))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            if not in_list:
                in_list = True
            result.append(stripped)
            continue

        in_list = False
        result.append(stripped)

    return "\n".join(result)


def import_text_as_wiki_page(
    raw_text: str,
    *,
    title: str = "",
    author=None,
    use_ai: bool = True,
    publish: bool = False,
) -> WikiPage:
    """
    Import raw text, convert to markdown (optionally via AI),
    split into sections, and create a wiki page.
    """
    service = get_ai_service()

    if use_ai and service.is_configured:
        markdown = service.format_to_markdown(raw_text, title=title)
        if not title:
            title = service.suggest_title(raw_text)
    else:
        markdown = plain_text_to_markdown(raw_text)
        if not title:
            first_line = raw_text.strip().splitlines()[0] if raw_text.strip() else "Untitled"
            title = first_line[:255]

    status = WikiPage.Status.PUBLISHED if publish else WikiPage.Status.DRAFT
    return create_page_from_markdown(
        title=title,
        content=markdown,
        author=author,
        status=status,
        split_sections=True,
    )


def preview_import(raw_text: str, *, title: str = "", use_ai: bool = True) -> dict:
    """Preview import without saving."""
    service = get_ai_service()

    if use_ai and service.is_configured:
        markdown = service.format_to_markdown(raw_text, title=title)
        if not title:
            title = service.suggest_title(raw_text)
    else:
        markdown = plain_text_to_markdown(raw_text)
        if not title:
            first_line = raw_text.strip().splitlines()[0] if raw_text.strip() else "Untitled"
            title = first_line[:255]

    sections = split_markdown_into_sections(markdown)
    return {
        "title": title,
        "markdown": markdown,
        "summary": extract_summary(markdown),
        "sections": sections,
        "section_count": len(sections),
        "ai_used": use_ai and service.is_configured,
    }
