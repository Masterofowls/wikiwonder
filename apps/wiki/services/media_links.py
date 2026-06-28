"""Convert markdown links to media embeds (video, audio, image, gif, pdf)."""
from __future__ import annotations

import re

from django.utils.html import escape

from apps.previews.services import build_preview, detect_type
from apps.wiki.services.embeds import repair_unfenced_wiki_embeds

EMBEDABLE = frozenset({"image", "gif", "video", "audio", "pdf"})
MEDIA_URL_HINT = re.compile(r"/media/|/static/|\.(?:mp4|webm|mov|mp3|wav|ogg|m4a|gif|png|jpe?g|webp|svg|pdf)(?:\?|$)", re.I)
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_MEDIA_ANCHOR = re.compile(
    r'<a\b([^>]*?\bhref="([^"]+)"[^>]*)>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
MALFORMED_IMAGE = re.compile(
    r"!(?!\[)([^\n\[\]/]+?)(/media/[^\s<>\)\]]+)",
    re.IGNORECASE,
)


def repair_malformed_image_urls(text: str) -> str:
    """Fix `!Title/media/path.png` → `![Title](/media/path.png)` before bare-URL promotion."""

    def repl(match: re.Match) -> str:
        title = match.group(1).strip()
        url = match.group(2).strip()
        return f"![{title}]({url})"

    return MALFORMED_IMAGE.sub(repl, text)


def normalize_media_markdown(text: str) -> str:
    """Normalize common broken inline media markdown before save or render."""
    if not text:
        return text
    text = repair_unfenced_wiki_embeds(text)
    text = repair_malformed_image_urls(text)
    return text


def media_kind(url: str) -> str | None:
    if not url:
        return None
    kind = detect_type(url=url)
    return kind if kind in EMBEDABLE else None


def _looks_like_media_url(url: str) -> bool:
    return bool(MEDIA_URL_HINT.search(url))


def _wiki_embed(kind: str, url: str, title: str) -> str:
    safe_title = title.replace('"', "'") or kind.title()
    if kind in {"image", "gif"}:
        return f"![{safe_title}]({url})"
    return f'```wiki-{kind} url="{url}" title="{safe_title}"\n```'


def promote_media_links_markdown(text: str) -> str:
    """Turn [label](/media/file.ext) into images or wiki-* embed blocks."""

    def repl(match: re.Match) -> str:
        label, url = match.group(1).strip(), match.group(2).strip()
        kind = media_kind(url)
        if not kind and _looks_like_media_url(url):
            kind = detect_type(url=url)
            if kind not in EMBEDABLE:
                kind = None
        if not kind:
            return match.group(0)
        return _wiki_embed(kind, url, label)

    return MARKDOWN_LINK.sub(repl, text)


def promote_bare_media_urls(text: str) -> str:
    """Turn bare /media/... URLs into embeds before generic URL linkification."""
    text = repair_malformed_image_urls(text)

    def repl(match: re.Match) -> str:
        url = match.group(1).rstrip(".,);]")
        suffix = match.group(1)[len(url) :]
        if not _looks_like_media_url(url):
            return match.group(0)
        kind = media_kind(url)
        if not kind:
            return match.group(0)
        return _wiki_embed(kind, url, "") + suffix

    bare = re.compile(r"(?<![\"'=(\[])(/media/[^\s<>\"]+)")
    return bare.sub(repl, text)


def replace_media_anchors(html: str) -> str:
    """Replace leftover anchor tags to media files with rich embed HTML."""

    def repl(match: re.Match) -> str:
        url = match.group(2).strip()
        label = re.sub(r"<[^>]+>", "", match.group(3)).strip()
        kind = media_kind(url)
        if not kind:
            return match.group(0)
        preview = build_preview(url=url, block_type=kind, title=label or kind.title())
        return preview.get("html") or match.group(0)

    return HTML_MEDIA_ANCHOR.sub(repl, html)


def wrap_standalone_media_images(html: str) -> str:
    """Wrap bare <img src="/media/..."> in figure for consistent styling."""
    pattern = re.compile(
        r'(<p>)?<img([^>]*\bsrc="(/media/[^"]+)"[^>]*)>(</p>)?',
        re.IGNORECASE,
    )

    def repl(match: re.Match) -> str:
        attrs = match.group(2)
        if "wiki-media__img" in attrs:
            return match.group(0)
        src = match.group(3)
        alt_match = re.search(r'alt="([^"]*)"', attrs)
        alt = alt_match.group(1) if alt_match else ""
        attrs = re.sub(r'\s*alt="[^"]*"', "", attrs, count=1)
        kind = media_kind(src) or "image"
        return (
            f'<figure class="wiki-media wiki-media--{kind}">'
            f'<img{attrs} class="wiki-media__img" loading="lazy" alt="{escape(alt)}"></figure>'
        )

    return pattern.sub(repl, html)
