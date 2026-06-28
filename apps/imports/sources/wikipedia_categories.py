"""Fetch Wikipedia categories for tag mapping."""
from __future__ import annotations

from urllib.parse import quote, urlencode

from apps.imports.sources.fetch import fetch_json

SKIP_PREFIXES = (
    "Category:Articles",
    "Category:All articles",
    "Category:Wikipedia",
    "Category:CS1",
    "Category:Webarchive",
    "Category:Commons category",
    "Category:Pages using",
    "Category:Use ",
)


def fetch_wikipedia_categories(lang: str, page_title: str, *, limit: int = 20) -> list[str]:
    params = urlencode(
        {
            "action": "query",
            "titles": page_title,
            "prop": "categories",
            "cllimit": str(min(limit, 50)),
            "clshow": "!hidden",
            "format": "json",
            "redirects": "1",
        }
    )
    data = fetch_json(f"https://{lang}.wikipedia.org/w/api.php?{params}")
    names: list[str] = []
    for page in data.get("query", {}).get("pages", {}).values():
        for cat in page.get("categories", []):
            title = cat.get("title", "")
            if not title.startswith("Category:"):
                continue
            if any(title.startswith(p) for p in SKIP_PREFIXES):
                continue
            name = title.replace("Category:", "", 1).strip()
            if name and len(name) < 80:
                names.append(name)
    return names[:limit]


def fetch_wikipedia_category_articles(
    lang: str,
    category_title: str,
    *,
    limit: int = 50,
) -> list[str]:
    """Return article titles in a Wikipedia category (excludes subcategories)."""
    if not category_title.startswith("Category:"):
        category_title = f"Category:{category_title}"
    titles: list[str] = []
    cmcontinue = ""
    while len(titles) < limit:
        params: dict = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": str(min(50, limit - len(titles))),
            "cmtype": "page",
            "cmnamespace": "0",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = fetch_json(f"https://{lang}.wikipedia.org/w/api.php?{urlencode(params)}")
        for member in data.get("query", {}).get("categorymembers", []):
            title = member.get("title", "")
            if title and not title.startswith("Category:"):
                titles.append(title)
        cmcontinue = data.get("continue", {}).get("cmcontinue", "")
        if not cmcontinue:
            break
    return titles[:limit]


def wikipedia_article_urls(lang: str, titles: list[str]) -> list[str]:
    """Build canonical Wikipedia article URLs from titles."""
    return [
        f"https://{lang}.wikipedia.org/wiki/{quote(t.replace(' ', '_'))}"
        for t in titles
    ]
