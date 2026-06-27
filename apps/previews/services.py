"""Multi-format document and media preview builders."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from django.utils.html import escape

PREVIEW_TYPES = frozenset({
    "image", "gif", "video", "audio", "pdf", "doc", "docx", "html", "htm",
    "fb2", "md", "markdown", "graph", "code", "url", "csv", "json", "xlsx",
})


def detect_type(url: str = "", filename: str = "", hint: str = "") -> str:
    if hint and hint in PREVIEW_TYPES:
        return hint.replace("docx", "doc").replace("htm", "html").replace("markdown", "md")
    name = filename or urlparse(url).path
    ext = Path(name).suffix.lower().lstrip(".")
    mapping = {
        "jpg": "image", "jpeg": "image", "png": "image", "webp": "image", "svg": "image",
        "gif": "gif", "mp4": "video", "webm": "video", "mov": "video",
        "mp3": "audio", "wav": "audio", "ogg": "audio", "m4a": "audio",
        "pdf": "pdf", "doc": "doc", "docx": "doc", "html": "html", "htm": "html",
        "fb2": "fb2", "md": "md", "markdown": "md", "json": "json", "csv": "csv",
        "xlsx": "xlsx", "xls": "xlsx",
    }
    return mapping.get(ext, hint or "url")


def _meta(title: str = "", description: str = "", **extra) -> dict:
    return {"title": title, "description": description, **extra}


def build_preview(
    *,
    url: str = "",
    content: str = "",
    block_type: str = "",
    title: str = "",
    description: str = "",
    language: str = "",
    metadata: dict | None = None,
) -> dict:
    """Return preview payload: type, html, meta, annotations_ready."""
    metadata = metadata or {}
    kind = detect_type(url=url, hint=block_type)
    safe_title = escape(title or "Preview")
    safe_desc = escape(description or "")

    if kind in {"image", "gif"}:
        src = url or metadata.get("src", "")
        html_out = (
            f'<figure class="wiki-media wiki-media--{kind}">'
            f'<img src="{escape(src)}" alt="{safe_title}" loading="lazy" class="wiki-media__img" />'
            f'<figcaption class="wiki-media__caption"><strong>{safe_title}</strong>'
            f"{f'<p>{safe_desc}</p>' if safe_desc else ''}</figcaption></figure>"
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description), "embed_url": src}

    if kind == "video":
        src = url or metadata.get("src", "")
        poster = metadata.get("poster", "")
        poster_attr = f' poster="{escape(poster)}"' if poster else ""
        html_out = (
            f'<figure class="wiki-media wiki-media--video">'
            f'<video controls class="wiki-media__video" src="{escape(src)}"{poster_attr}></video>'
            f'<figcaption class="wiki-media__caption">{safe_title}</figcaption></figure>'
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description), "embed_url": src}

    if kind == "audio":
        src = url or metadata.get("src", "")
        html_out = (
            f'<figure class="wiki-media wiki-media--audio">'
            f'<audio controls class="wiki-media__audio" src="{escape(src)}"></audio>'
            f'<figcaption class="wiki-media__caption">{safe_title}</figcaption></figure>'
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description), "embed_url": src}

    if kind == "pdf":
        src = url or metadata.get("src", "")
        html_out = (
            f'<figure class="wiki-media wiki-media--pdf">'
            f'<iframe class="wiki-media__pdf" src="{escape(src)}" title="{safe_title}" '
            f'loading="lazy"></iframe>'
            f'<figcaption class="wiki-media__caption">{safe_title}</figcaption></figure>'
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description), "embed_url": src}

    if kind == "html":
        src = url or ""
        if src:
            html_out = (
                f'<figure class="wiki-media wiki-media--html">'
                f'<iframe class="wiki-media__html" sandbox="allow-scripts" src="{escape(src)}" '
                f'title="{safe_title}"></iframe></figure>'
            )
        else:
            html_out = (
                f'<figure class="wiki-media wiki-media--html">'
                f'<div class="wiki-media__html-inline">{content}</div></figure>'
            )
        return {"type": kind, "html": html_out, "meta": _meta(title, description)}

    if kind == "md":
        import markdown as md_lib

        rendered = md_lib.markdown(content or metadata.get("text", ""), extensions=["extra", "fenced_code"])
        html_out = f'<div class="wiki-media wiki-media--md">{rendered}</div>'
        return {"type": kind, "html": html_out, "meta": _meta(title, description)}

    if kind == "code":
        lang = language or metadata.get("language", "text")
        body = escape(content or metadata.get("code", ""))
        html_out = (
            f'<figure class="wiki-media wiki-media--code">'
            f'<pre><code class="language-{escape(lang)}">{body}</code></pre>'
            f'{f"<figcaption>{safe_desc}</figcaption>" if safe_desc else ""}'
            f"</figure>"
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description, language=lang)}

    if kind == "graph":
        graph_type = language or metadata.get("graph_type", "mermaid")
        dsl = content or metadata.get("dsl", "")
        html_out = (
            f'<figure class="wiki-media wiki-media--graph" data-graph-type="{escape(graph_type)}">'
            f'<pre class="wiki-graph-source">{escape(dsl)}</pre>'
            f'<div class="wiki-graph-render" data-graph-dsl="{escape(dsl)}"></div>'
            f'<figcaption class="wiki-media__caption">{safe_title}</figcaption></figure>'
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description, graph_type=graph_type)}

    if kind == "fb2":
        excerpt = metadata.get("excerpt") or _extract_fb2_excerpt(content)
        html_out = (
            f'<figure class="wiki-media wiki-media--fb2">'
            f'<div class="wiki-fb2-preview"><h4>{safe_title}</h4>'
            f'<p>{escape(excerpt[:500])}</p></div></figure>'
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, excerpt[:200])}

    if kind == "json":
        try:
            parsed = json.loads(content or metadata.get("json", "{}"))
            pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pretty = content
        html_out = f'<pre class="wiki-media wiki-media--json"><code>{escape(pretty)}</code></pre>'
        return {"type": kind, "html": html_out, "meta": _meta(title, description)}

    if kind in {"csv", "xlsx"}:
        html_out = (
            f'<figure class="wiki-media wiki-media--table">'
            f'<p class="wiki-media__caption">{safe_title} ({kind.upper()})</p>'
            f'<a class="wiki-url-highlight" href="{escape(url)}" target="_blank" rel="noopener">Open file</a>'
            f"</figure>"
        )
        return {"type": kind, "html": html_out, "meta": _meta(title, description), "embed_url": url}

    if kind == "url" or url:
        html_out = (
            f'<a class="wiki-url-highlight" href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
            f'<span class="wiki-url-highlight__label">{safe_title or escape(url)}</span>'
            f"</a>"
        )
        return {"type": "url", "html": html_out, "meta": _meta(title or url, description), "embed_url": url}

    return {"type": "unknown", "html": "", "meta": _meta(title, description)}


def _extract_fb2_excerpt(xml_text: str) -> str:
    if not xml_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", xml_text)
    return " ".join(text.split())[:800]


def extract_pdf_meta(file_path: str | Path) -> dict:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        info = reader.metadata or {}
        return {
            "pages": len(reader.pages),
            "title": info.get("/Title", ""),
            "author": info.get("/Author", ""),
        }
    except Exception:
        return {}


def extract_docx_text(file_path: str | Path, max_chars: int = 2000) -> str:
    try:
        from docx import Document

        doc = Document(str(file_path))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(parts)
        return text[:max_chars]
    except Exception:
        return ""


def preview_from_block(block) -> dict:
    """Build preview from a ContentBlock instance."""
    url = block.source_url
    if block.file and not url:
        url = block.file.url
    preview = build_preview(
        url=url,
        content=block.content,
        block_type=block.block_type,
        title=block.title,
        description=block.description,
        language=block.language,
        metadata=block.metadata,
    )
    preview["id"] = block.pk
    preview["annotations"] = [
        {
            "id": a.pk,
            "label": a.label,
            "body": a.body,
            "x": a.x_percent,
            "y": a.y_percent,
            "start": a.start_offset,
            "end": a.end_offset,
        }
        for a in block.annotations.all()
    ]
    return preview
