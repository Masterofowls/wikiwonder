"""Convert HTML and raw text into WikiWonder markdown."""
from __future__ import annotations

import re
from datetime import UTC, datetime

import html2text

WIKI_EMBED_TYPES = frozenset({"video", "audio", "pdf", "image", "gif", "code", "graph", "embed", "url"})


def html_to_markdown(html: str, *, base_url: str = "") -> str:
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_links = False
    converter.ignore_images = False
    converter.protect_links = True
    converter.single_line_break = True
    converter.mark_code = True
    if base_url:
        converter.baseurl = base_url
    markdown = converter.handle(html or "")
    return normalize_wiki_markdown(markdown)


def normalize_wiki_markdown(text: str) -> str:
    """Clean up converted markdown for wiki rendering."""
    if not text:
        return ""
    cleaned = text.replace("\r\n", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n#+\s*$", "", cleaned)
    return cleaned.strip()


def build_attribution_block(
    *,
    title: str,
    source_url: str,
    source_label: str,
    license_note: str = "",
) -> str:
    """Lead blockquote citing the import source."""
    safe_title = title.strip() or "Untitled"
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"> **Imported from:** [{safe_title}]({source_url})",
        f"> **Source:** {source_label} · {date_str}",
    ]
    if license_note:
        lines.append(f"> **License:** {license_note}")
    return "\n".join(lines)


def wrap_with_source_embed(source_url: str, title: str, markdown: str) -> str:
    """Append a wiki-embed block pointing at the original."""
    embed = f'\n\n```wiki-embed url="{source_url}" title="{title}" type="url"\n```'
    return markdown.rstrip() + embed


def rss_entry_to_section(entry, index: int) -> str:
    """Format one RSS/Atom entry as a wiki subsection."""
    entry_title = getattr(entry, "title", f"Entry {index}") or f"Entry {index}"
    link = getattr(entry, "link", "") or ""
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "")

    lines = [f"### {entry_title.strip()}"]
    meta_bits = []
    if published:
        meta_bits.append(published[:10] if len(published) >= 10 else published)
    if link:
        meta_bits.append(f"[Read original]({link})")
    if meta_bits:
        lines.append(" · ".join(meta_bits))
    if summary:
        body = html_to_markdown(summary, base_url=link)
        if body:
            lines.append("")
            lines.append(body)
    return "\n".join(lines)
