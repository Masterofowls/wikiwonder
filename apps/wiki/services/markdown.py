"""Markdown rendering and text processing utilities."""
import re

import bleach
import markdown
from django.utils.safestring import mark_safe

from apps.wiki.services.embeds import highlight_urls, process_embeds
from apps.wiki.services.media_links import (
    promote_bare_media_urls,
    promote_media_links_markdown,
    replace_media_anchors,
    wrap_standalone_media_images,
)

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS | {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "pre", "code", "blockquote", "hr",
    "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tr", "th", "td",
    "img", "a", "strong", "em", "del", "sup", "sub",
    "details", "summary", "figure", "figcaption", "video", "audio",
    "iframe", "span", "div",
}
ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel", "class", "target", "data-url"],
    "img": ["src", "alt", "title", "width", "height", "loading", "class"],
    "code": ["class"],
    "pre": ["class"],
    "th": ["scope"],
    "td": ["colspan", "rowspan"],
    "video": ["src", "controls", "poster", "class"],
    "audio": ["src", "controls", "class"],
    "iframe": ["src", "title", "loading", "sandbox", "class"],
    "span": ["class", "data-url"],
    "div": ["class", "data-graph-type", "data-graph-dsl"],
    "figure": ["class"],
    "figcaption": ["class"],
}


def render_markdown(text: str) -> str:
    """Convert markdown to sanitized HTML with embeds and URL highlights."""
    if not text:
        return ""
    text = promote_media_links_markdown(text)
    text = promote_bare_media_urls(text)
    text = highlight_urls(text)
    text = process_embeds(text)
    html = markdown.markdown(
        text,
        extensions=["extra", "codehilite", "toc", "tables", "fenced_code", "nl2br"],
    )
    html = replace_media_anchors(html)
    html = wrap_standalone_media_images(html)
    html = re.sub(
        r'<a href="(https?://[^"]+)"',
        (
            r'<a class="wiki-url-highlight wiki-ext-link" href="\1" '
            r'target="_blank" rel="noopener noreferrer" data-url="\1"'
        ),
        html,
    )
    html = re.sub(
        r'<a href="(/[^"]+)"',
        r'<a class="wiki-url-highlight wiki-int-link" href="\1" data-url="\1"',
        html,
    )
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    return mark_safe(clean)


def extract_summary(text: str, max_length: int = 200) -> str:
    """Extract plain-text summary from markdown."""
    plain = re.sub(r"[#*`_\[\]()]", "", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= max_length:
        return plain
    return plain[: max_length - 3].rsplit(" ", 1)[0] + "..."


def split_markdown_into_sections(content: str) -> list[dict]:
    """
    Split markdown content into sections by H2 headings.
    Returns list of {title, content, order, anchor}.
    """
    if not content.strip():
        return []

    pattern = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        return [{"title": "Introduction", "content": content.strip(), "order": 0, "anchor": "intro"}]

    sections = []
    preamble = content[: matches[0].start()].strip()
    if preamble:
        sections.append({
            "title": "Introduction",
            "content": preamble,
            "order": 0,
            "anchor": "introduction",
        })

    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()

        if level == 1 and sections:
            sections[-1]["content"] += f"\n\n# {title}\n\n{section_content}"
            continue

        anchor = re.sub(r"[^\w-]", "", title.lower().replace(" ", "-"))
        sections.append({
            "title": title,
            "content": section_content,
            "order": len(sections),
            "anchor": anchor or f"section-{len(sections)}",
        })

    return sections
