"""Fetch and optionally mirror Wikipedia article media."""
from __future__ import annotations

import re
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from apps.imports.sources.fetch import FetchError, fetch_json, fetch_url
from apps.imports.sources.wikipedia_diagrams import upgrade_wikimedia_thumb_url
from apps.imports.sources.wikipedia_html import _resolve_image_url

IMAGE_MIMES = frozenset({"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"})
VIDEO_MIMES = frozenset({"video/webm", "video/ogg", "video/mp4"})
AUDIO_MIMES = frozenset({"audio/ogg", "audio/mpeg", "audio/wav", "audio/webm"})


def _api_url(lang: str, params: dict) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php?{urlencode({**params, 'format': 'json'})}"


def fetch_page_images(lang: str, page_title: str, *, limit: int = 40) -> list[dict]:
    """List image/video/audio files used on a Wikipedia page."""
    data = fetch_json(
        _api_url(
            lang,
            {
                "action": "query",
                "titles": page_title,
                "prop": "images",
                "imlimit": str(min(limit, 50)),
                "redirects": "1",
            },
        )
    )
    pages = data.get("query", {}).get("pages", {})
    images: list[str] = []
    for page in pages.values():
        for item in page.get("images", []):
            title = item.get("title", "")
            if title.startswith("File:"):
                images.append(title)
    if not images:
        return []

    file_titles = "|".join(images[:limit])
    info_data = fetch_json(
        _api_url(
            lang,
            {
                "action": "query",
                "titles": file_titles,
                "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata",
                "iiurlwidth": "1200",
                "redirects": "1",
            },
        )
    )
    results: list[dict] = []
    for page in info_data.get("query", {}).get("pages", {}).values():
        title = page.get("title", "")
        for info in page.get("imageinfo", []):
            mime = info.get("mime", "")
            url = info.get("thumburl") or info.get("url") or ""
            if mime == "image/svg+xml":
                url = info.get("thumburl") or url
            if url:
                url = upgrade_wikimedia_thumb_url(url)
            if not url:
                continue
            kind = "image"
            if mime in VIDEO_MIMES:
                kind = "video"
            elif mime in AUDIO_MIMES:
                kind = "audio"
            elif mime not in IMAGE_MIMES and not mime.startswith("image/"):
                continue
            caption = ""
            meta = info.get("extmetadata", {})
            if meta.get("ImageDescription", {}).get("value"):
                caption = BeautifulSoup(meta["ImageDescription"]["value"], "html.parser").get_text(
                    " ", strip=True
                )[:240]
            results.append(
                {
                    "title": title.replace("File:", ""),
                    "url": url,
                    "mime": mime,
                    "kind": kind,
                    "caption": caption,
                    "size": info.get("size", 0),
                }
            )
    return results


def extract_inline_media(html: str, *, base_url: str) -> list[dict]:
    """Pull media URLs already present in article HTML."""
    soup = BeautifulSoup(html or "", "html5lib")
    root = soup.select_one(".mw-parser-output") or soup
    found: list[dict] = []
    seen: set[str] = set()

    for img in root.select(
        ".thumb img, figure img, .infobox img, .gallerybox img, .mw-file-element, img[data-src]"
    ):
        src = _resolve_image_url(img, base_url)
        if not src or src in seen:
            continue
        seen.add(src)
        cap = ""
        parent = img.find_parent(["figure", "div", "li"])
        if parent:
            cap_el = parent.select_one(".thumbcaption, figcaption, .gallerytext")
            cap = cap_el.get_text(" ", strip=True) if cap_el else ""
        found.append({"title": img.get("alt") or "Image", "url": src, "kind": "image", "caption": cap})

    for tag_name, kind in (("video", "video"), ("audio", "audio")):
        for node in root.find_all(tag_name):
            source = node.find("source")
            src = (source.get("src") if source else node.get("src")) or ""
            if src.startswith("//"):
                src = "https:" + src
            if src and src not in seen:
                seen.add(src)
                found.append({"title": node.get("title") or kind.title(), "url": src, "kind": kind})

    return found


def media_to_markdown_snippet(item: dict, *, use_url: str | None = None) -> str:
    """Format one media item as wiki markdown embed."""
    url = use_url or item["url"]
    title = (item.get("caption") or item.get("title") or "Media").replace('"', "'")
    kind = item.get("kind", "image")
    if kind == "video":
        return f'```wiki-video url="{url}" title="{title}"\n```'
    if kind == "audio":
        return f'```wiki-audio url="{url}" title="{title}"\n```'
    return f"![{title}]({url})"


def mirror_media_to_storage(items: list[dict], *, user_id: int | None = None) -> dict[str, str]:
    """Download remote media to Django storage; return original_url → local_url map."""
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    mapping: dict[str, str] = {}
    prefix = f"imports/wikipedia/{user_id or 'anon'}"
    for item in items[:20]:
        url = item.get("url", "")
        if not url or url in mapping:
            continue
        try:
            body, content_type = fetch_url(url, timeout=30)
        except FetchError:
            continue
        if len(body) > 8 * 1024 * 1024:
            continue
        ext = _ext_from_mime(content_type, item.get("mime", ""), url)
        safe_name = re.sub(r"[^\w.\-]+", "-", item.get("title", "file"))[:80]
        path = default_storage.save(f"{prefix}/{safe_name}{ext}", ContentFile(body))
        mapping[url] = default_storage.url(path)
    return mapping


def _ext_from_mime(content_type: str, mime: str, url: str) -> str:
    ct = (mime or content_type or "").lower()
    if "svg" in ct:
        return ".svg"
    if "png" in ct:
        return ".png"
    if "gif" in ct:
        return ".gif"
    if "webp" in ct:
        return ".webp"
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "webm" in ct:
        return ".webm"
    if "ogg" in ct:
        return ".ogg"
    if "mp4" in ct:
        return ".mp4"
    if "." in url.rsplit("/", 1)[-1]:
        return "." + url.rsplit(".", 1)[-1].split("?")[0][:8]
    return ".bin"


def enrich_markdown_with_lead_media(
    markdown: str,
    media_items: list[dict],
    *,
    url_map: dict[str, str] | None = None,
    max_embeds: int = 6,
) -> str:
    """Prepend notable article images not already referenced in markdown body."""
    url_map = url_map or {}
    existing = set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown))
    existing.update(re.findall(r'url="([^"]+)"', markdown))
    embeds: list[str] = []
    for item in media_items:
        if len(embeds) >= max_embeds:
            break
        url = item.get("url", "")
        if not url or url in existing:
            continue
        local = url_map.get(url, url)
        embeds.append(media_to_markdown_snippet(item, use_url=local))
        existing.add(url)
    if not embeds:
        return markdown
    return "\n\n".join(embeds) + "\n\n" + markdown.lstrip()


def fetch_lead_image(lang: str, page_title: str) -> dict | None:
    """Fetch Wikipedia page thumbnail / original image for cover."""
    data = fetch_json(
        _api_url(
            lang,
            {
                "action": "query",
                "titles": page_title,
                "prop": "pageimages",
                "piprop": "thumbnail|original",
                "pithumbsize": 1200,
                "redirects": "1",
            },
        )
    )
    for page in data.get("query", {}).get("pages", {}).values():
        thumb = page.get("thumbnail", {})
        original = page.get("original", {})
        url = thumb.get("source") or original.get("source")
        if url:
            return {"url": url, "title": page_title, "kind": "image", "caption": "Lead image"}
    return None


def pick_cover_image(media_items: list[dict], lead: dict | None) -> dict | None:
    """Choose best image for page cover (lead > infobox > first thumb)."""
    if lead:
        return lead
    for item in media_items:
        if item.get("kind") == "image" and item.get("url"):
            return item
    return None


def download_cover_file(image: dict) -> tuple[bytes, str] | None:
    """Download cover bytes and extension."""
    url = image.get("url", "")
    if not url:
        return None
    try:
        body, content_type = fetch_url(url, timeout=30)
    except FetchError:
        return None
    if len(body) > 6 * 1024 * 1024:
        return None
    ext = _ext_from_mime(content_type, image.get("mime", ""), url)
    return body, ext
