"""Helpers for page-scoped AI prompts."""
from apps.wiki.models import WikiPage


def page_markdown_text(page: WikiPage, *, max_chars: int = 12000) -> str:
    """Build markdown context from page body and sections."""
    sections = list(page.sections.all().order_by("order"))
    if sections:
        chunks = [f"## {section.title}\n\n{section.content}" for section in sections]
        text = "\n\n".join(chunks)
    else:
        text = page.content or ""
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[Content truncated for AI context…]"
    return text
