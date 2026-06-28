"""SEO helpers: Open Graph, JSON-LD, robots, meta."""
from __future__ import annotations

from django.conf import settings


def absolute_url(path: str) -> str:
    base = settings.SITE_URL.rstrip("/")
    if path.startswith("http"):
        return path
    return f"{base}{path if path.startswith('/') else '/' + path}"


def _site_keywords() -> list[str]:
    raw = getattr(settings, "SEO_SITE_KEYWORDS", "")
    if isinstance(raw, str):
        return [k.strip() for k in raw.split(",") if k.strip()]
    return list(raw)


def _clip(text: str, *, min_len: int = 0, max_len: int = 160) -> str:
    text = " ".join(text.split())
    if max_len and len(text) > max_len:
        text = text[: max_len - 1].rsplit(" ", 1)[0] + "…"
    if min_len and len(text) < min_len:
        suffix = f" — {settings.SITE_NAME} wiki and knowledge base."
        text = (text + suffix)[:max_len] if max_len else text + suffix
    return text


def page_keywords(page) -> list[str]:
    tags = list(page.tags.values_list("name", flat=True))
    if tags:
        return tags
    title_words = [w for w in page.title.split() if len(w) > 2][:3]
    return title_words or ["wiki"]


def wiki_page_seo(page) -> dict:
    keywords = page_keywords(page)
    primary = keywords[0]
    image = page.cover_url if hasattr(page, "cover_url") else ""
    if page.cover_image:
        image = absolute_url(page.cover_image.url)
    description = _clip(
        page.summary or f"{page.title} — {primary} article on {settings.SITE_NAME}.",
        min_len=50,
        max_len=160,
    )
    title = _clip(f"{page.title} — {primary} | {settings.SITE_NAME}", max_len=70)
    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "canonical": absolute_url(page.get_absolute_url()),
        "og_type": "article",
        "og_title": page.title,
        "og_description": description,
        "og_image": image,
        "og_url": absolute_url(page.get_absolute_url()),
        "twitter_card": "summary_large_image",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": page.title,
            "description": description,
            "keywords": ", ".join(keywords),
            "image": image,
            "datePublished": page.published_at.isoformat()
            if page.published_at
            else page.created_at.isoformat(),
            "dateModified": page.updated_at.isoformat(),
            "author": {"@type": "Person", "name": str(page.author or settings.SITE_NAME)},
            "publisher": {"@type": "Organization", "name": settings.SITE_NAME},
        },
    }


def site_defaults() -> dict:
    keywords = _site_keywords()
    description = _clip(
        getattr(
            settings,
            "SEO_SITE_DESCRIPTION",
            (
                f"{settings.SITE_NAME} is a free wiki and knowledge base for articles, "
                f"shared links, and collaborative notes. Browse encyclopedia-style pages, "
                f"bookmarks, and AI-assisted imports."
            ),
        ),
        min_len=50,
        max_len=160,
    )
    title = _clip(
        f"{settings.SITE_NAME} — Free Wiki & Knowledge Base Online",
        max_len=70,
    )
    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "canonical": settings.SITE_URL,
        "og_type": "website",
        "og_title": title,
        "og_description": description,
        "og_image": absolute_url("/static/icons/icon-512.png"),
        "og_url": settings.SITE_URL,
        "twitter_card": "summary_large_image",
    }


def home_seo() -> dict:
    """Home page SEO with primary keyword in title/description."""
    seo = site_defaults()
    keywords = seo["keywords"]
    primary = keywords[0] if keywords else "wiki"
    seo["title"] = _clip(
        f"{settings.SITE_NAME} — {primary.title()} Knowledge Base & Encyclopedia",
        max_len=70,
    )
    seo["og_title"] = seo["title"]
    seo["description"] = _clip(
        (
            f"Explore the {settings.SITE_NAME} {primary} knowledge base: encyclopedia articles, "
            f"shared links with previews, categories, bookmarks, and multilingual wiki pages."
        ),
        min_len=50,
        max_len=160,
    )
    seo["og_description"] = seo["description"]
    return seo


def robots_txt_content() -> str:
    base = settings.SITE_URL.rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /api/",
        "Disallow: /markdownx/",
        "",
        f"Sitemap: {base}/sitemap.xml",
    ]
    return "\n".join(lines) + "\n"
