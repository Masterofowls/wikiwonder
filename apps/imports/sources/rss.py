"""RSS and Atom feed import."""
from __future__ import annotations

from urllib.parse import urlparse

import feedparser

from apps.imports.sources.convert import build_attribution_block, rss_entry_to_section
from apps.imports.sources.fetch import FetchError, fetch_text


def fetch_rss(url: str, *, max_entries: int = 25) -> dict:
    body, content_type = fetch_text(url)
    feed = feedparser.parse(body)
    if feed.bozo and not feed.entries:
        raise FetchError(getattr(feed, "bozo_exception", "Invalid feed") or "Invalid feed")

    feed_title = (feed.feed.get("title") or urlparse(url).netloc or "Feed").strip()
    feed_link = feed.feed.get("link") or url
    entries = list(feed.entries[:max_entries])

    if not entries:
        raise FetchError("Feed contains no entries")

    sections = [rss_entry_to_section(entry, idx + 1) for idx, entry in enumerate(entries)]
    body_md = "\n\n".join(sections)
    attribution = build_attribution_block(
        title=feed_title,
        source_url=feed_link,
        source_label="RSS / Atom feed",
    )
    markdown = f"{attribution}\n\n## Latest entries\n\n{body_md}"

    return {
        "title": feed_title,
        "markdown": markdown,
        "source_type": "rss",
        "source_url": url,
        "source_label": "RSS / Atom",
        "meta": {
            "entry_count": len(entries),
            "feed_link": feed_link,
            "content_type": content_type,
        },
    }
