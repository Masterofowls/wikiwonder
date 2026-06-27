"""Wiki-style embed blocks and URL highlighting in markdown."""
from __future__ import annotations

import re

EMBED_PATTERN = re.compile(
    r"```wiki-(?P<type>embed|media|code|graph|pdf|video|audio|url)\s*"
    r"(?P<attrs>[^\n]*)\n(?P<body>.*?)```",
    re.DOTALL | re.IGNORECASE,
)

ATTR_PATTERN = re.compile(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))')


def _parse_attrs(raw: str) -> dict[str, str]:
    attrs = {}
    for match in ATTR_PATTERN.finditer(raw or ""):
        key = match.group(1).lower()
        val = match.group(2) or match.group(3) or match.group(4) or ""
        attrs[key] = val
    return attrs


def _replace_embed(match: re.Match) -> str:
    from apps.previews.services import build_preview

    block_type = match.group("type").lower()
    attrs = _parse_attrs(match.group("attrs"))
    body = match.group("body").strip()
    type_map = {
        "embed": attrs.get("type", "url"),
        "media": attrs.get("type", "image"),
        "code": "code",
        "graph": "graph",
        "pdf": "pdf",
        "video": "video",
        "audio": "audio",
        "url": "url",
    }
    preview = build_preview(
        url=attrs.get("url", ""),
        content=body,
        block_type=type_map.get(block_type, block_type),
        title=attrs.get("title", ""),
        description=attrs.get("description", attrs.get("caption", "")),
        language=attrs.get("lang", attrs.get("language", "")),
        metadata=attrs,
    )
    return preview.get("html", "")


def process_embeds(text: str) -> str:
    if not text:
        return ""
    return EMBED_PATTERN.sub(_replace_embed, text)


URL_IN_TEXT = re.compile(r"(?<![\"'=])(https?://[^\s<>\"]+)")


def highlight_urls(text: str) -> str:
    """Wrap bare URLs in markdown source with highlight markup."""

    def repl(match: re.Match) -> str:
        url = match.group(1).rstrip(".,);]")
        suffix = match.group(1)[len(url) :]
        return f'[`{url}`]({url}){{.wiki-url-highlight}}{suffix}'

    return URL_IN_TEXT.sub(repl, text)
