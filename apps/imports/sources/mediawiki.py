"""Generic MediaWiki wiki import."""
from __future__ import annotations

from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup

from apps.imports.sources.convert import (
    build_attribution_block,
    html_to_markdown,
    wrap_with_source_embed,
)
from apps.imports.sources.detect import mediawiki_page_title
from apps.imports.sources.fetch import FetchError, fetch_json, origin_of


def _api_candidates(url: str) -> list[str]:
    origin = origin_of(url)
    return [f"{origin}/w/api.php", f"{origin}/api.php"]


def resolve_mediawiki_api(url: str) -> str | None:
    for api_url in _api_candidates(url):
        try:
            probe = fetch_json(f"{api_url}?action=query&meta=siteinfo&format=json")
            if probe.get("query", {}).get("general"):
                return api_url
        except FetchError:
            continue
    return None


def fetch_mediawiki(url: str, *, api_url: str | None = None) -> dict:
    page_title = mediawiki_page_title(url)
    if not page_title:
        raise FetchError("Could not determine MediaWiki page title from URL")

    api = api_url or resolve_mediawiki_api(url)
    if not api:
        raise FetchError("No MediaWiki API found for this site")

    params = urlencode(
        {
            "action": "parse",
            "page": page_title,
            "prop": "text|displaytitle|sections",
            "format": "json",
            "redirects": "1",
            "disableeditsection": "1",
        }
    )
    data = fetch_json(f"{api}?{params}")
    if "error" in data:
        raise FetchError(data["error"].get("info", "MediaWiki API error"))

    parse_data = data["parse"]
    display_title = BeautifulSoup(parse_data.get("displaytitle", page_title), "html.parser").get_text()
    html = parse_data["text"]["*"]
    origin = origin_of(url)

    body_md = html_to_markdown(html, base_url=origin)
    site_name = urlparse(origin).netloc
    attribution = build_attribution_block(
        title=display_title,
        source_url=url,
        source_label=f"MediaWiki · {site_name}",
    )
    markdown = wrap_with_source_embed(url, display_title, f"{attribution}\n\n{body_md}")

    return {
        "title": display_title,
        "markdown": markdown,
        "source_type": "mediawiki",
        "source_url": url,
        "source_label": f"MediaWiki · {site_name}",
        "meta": {"api": api, "page": page_title},
    }
