"""Wikipedia diagram and gallery URL helpers."""
from __future__ import annotations

import re

THUMB_SIZE_RE = re.compile(r"/(\d+)px-")


def upgrade_wikimedia_thumb_url(url: str, *, max_width: int = 1200) -> str:
    """Request a larger Wikimedia thumbnail (250px → 1200px) when possible."""
    if not url or "upload.wikimedia.org" not in url:
        return url
    if "/thumb/" not in url:
        return url
    return THUMB_SIZE_RE.sub(f"/{max_width}px-", url, count=1)


def media_to_figure_markdown(src: str, alt: str, caption: str = "") -> str:
    """Inline markdown image block with optional caption."""
    label = (caption or alt or "Diagram").strip()
    label = re.sub(r"[\[\]]", "", label)[:240]
    src = upgrade_wikimedia_thumb_url(src)
    block = f"![{label}]({src})"
    if caption and caption.strip() and caption.strip() != label:
        block += f"\n\n*{caption.strip()}*"
    return block


def embed_missing_diagrams(
    markdown: str,
    media_items: list[dict],
    *,
    url_map: dict[str, str] | None = None,
) -> str:
    """
    Insert diagram images referenced by API but missing from converted markdown.

    Matches captions/titles to section context and avoids duplicating URLs already present.
    """
    url_map = url_map or {}
    existing = set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown))
    existing.update(re.findall(r'url="([^"]+)"', markdown))

    additions: list[str] = []
    for item in media_items:
        if item.get("kind") != "image":
            continue
        url = url_map.get(item.get("url", ""), item.get("url", ""))
        url = upgrade_wikimedia_thumb_url(url)
        if not url or url in existing:
            continue
        caption = item.get("caption") or item.get("title") or ""
        title = item.get("title") or ""
        # Skip tiny icons / flags in infobox unless they have descriptive captions
        if not caption and len(title) < 4:
            continue
        if caption and caption in markdown and url not in markdown:
            # Caption survived import but image was dropped — insert near caption
            snippet = media_to_figure_markdown(url, title, caption)
            markdown = markdown.replace(caption, f"{snippet}\n\n{caption}", 1)
            existing.add(url)
            continue
        additions.append(media_to_figure_markdown(url, title, caption))
        existing.add(url)

    if (
        additions
        and additions[0] not in markdown
        and not any(a.split("](")[1].split(")")[0] in markdown for a in additions if "](" in a)
    ):
        markdown = "\n\n".join(additions[:8]) + "\n\n" + markdown.lstrip()
    return markdown
