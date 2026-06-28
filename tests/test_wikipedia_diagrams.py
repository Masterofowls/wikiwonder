"""Tests for Wikipedia diagram URL helpers."""
from apps.imports.sources.wikipedia_diagrams import (
    embed_missing_diagrams,
    media_to_figure_markdown,
    upgrade_wikimedia_thumb_url,
)


def test_upgrade_wikimedia_thumb_url():
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Foo.png/250px-Foo.png"
    assert "1200px" in upgrade_wikimedia_thumb_url(url)


def test_media_to_figure_markdown():
    md = media_to_figure_markdown("https://example.com/d.png", "Alt", "Caption text")
    assert md.startswith("![Caption text](https://example.com/d.png)")


def test_embed_missing_diagrams_by_caption():
    body = "See Mapping between HTML5 and JavaScript features for details."
    media = [
        {
            "kind": "image",
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Diagram.png/250px-Diagram.png",
            "caption": "Mapping between HTML5 and JavaScript features",
            "title": "Diagram.png",
        }
    ]
    out = embed_missing_diagrams(body, media)
    assert "Diagram.png" in out or "250px-Diagram" in out
    assert "Mapping between HTML5" in out
