"""Tests for URL-based wiki import."""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.imports.sources.convert import html_to_markdown, normalize_wiki_markdown
from apps.imports.sources.detect import detect_source_type, wikipedia_page_title
from apps.imports.url_import import preview_url_import

User = get_user_model()

WIKI_API_RESPONSE = {
    "parse": {
        "displaytitle": "Python (programming language)",
        "text": {
            "*": '<div class="mw-parser-output"><h2>History</h2><p>Python was created by Guido van Rossum.</p></div>'
        },
        "sections": [{"index": "1", "line": "History", "level": "2", "toclevel": "1"}],
    }
}

RSS_BODY = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Test Feed</title><link>https://example.com</link>
<item><title>First post</title><link>https://example.com/1</link><description><p>Hello world</p></description></item>
</channel></rss>"""

HTML_BODY = """<!DOCTYPE html><html><head><title>Doc Page</title></head>
<body><main><h1>Guide</h1><p>This is documentation content with enough text to pass the minimum length check for import.</p></main></body></html>"""


@pytest.mark.django_db
class TestSourceDetection:
    def test_wikipedia_url(self):
        assert detect_source_type("https://en.wikipedia.org/wiki/Python") == "wikipedia"

    def test_rss_url(self):
        assert detect_source_type("https://example.com/feeds/latest/") == "rss"

    def test_docs_url(self):
        assert detect_source_type("https://docs.python.org/3/tutorial/") == "docs"

    def test_wikipedia_title_parse(self):
        assert wikipedia_page_title("https://en.wikipedia.org/wiki/Python_(programming_language)") == (
            "en",
            "Python (programming language)",
        )


@pytest.mark.django_db
class TestConverters:
    def test_html_to_markdown(self):
        md = html_to_markdown("<h2>Title</h2><p>Body text.</p>")
        assert "## Title" in md
        assert "Body text" in md

    def test_normalize_strips_excess_blank_lines(self):
        assert normalize_wiki_markdown("A\n\n\n\nB") == "A\n\nB"


@pytest.mark.django_db
class TestUrlImportPreview:
    @patch("apps.imports.sources.wikipedia.fetch_json")
    def test_wikipedia_preview(self, mock_json):
        mock_json.return_value = WIKI_API_RESPONSE
        result = preview_url_import(
            "https://en.wikipedia.org/wiki/Python_(programming_language)",
            source_type="wikipedia",
            use_ai=False,
        )
        assert result["title"] == "Python (programming language)"
        assert "Imported from" in result["markdown"]
        assert result["source_type"] == "wikipedia"
        assert result["section_count"] >= 1

    @patch("apps.imports.sources.rss.fetch_text")
    def test_rss_preview(self, mock_fetch):
        mock_fetch.return_value = (RSS_BODY, "application/rss+xml")
        result = preview_url_import("https://example.com/feed.xml", source_type="rss", use_ai=False)
        assert result["title"] == "Test Feed"
        assert "First post" in result["markdown"]
        assert result["source_type"] == "rss"

    @patch("apps.imports.sources.html_page.fetch_text")
    def test_html_preview(self, mock_fetch):
        mock_fetch.return_value = (HTML_BODY, "text/html")
        result = preview_url_import("https://example.com/guide", source_type="web", use_ai=False)
        assert result["title"] == "Doc Page"
        assert "Guide" in result["markdown"]


@pytest.mark.django_db
class TestImportViews:
    def test_sources_endpoint(self, client):
        response = client.get(reverse("import_sources"))
        assert response.status_code == 200
        assert "wikipedia" in {s["id"] for s in response.json()["sources"]}

    def test_import_page_requires_login(self, client):
        response = client.get(reverse("wiki:import_url"))
        assert response.status_code == 302

    def test_import_page_authenticated(self, client):
        user = User.objects.create_user("importer", password="test")
        client.force_login(user)
        response = client.get(reverse("wiki:import_url"))
        assert response.status_code == 200
        assert b"Import from URL" in response.content

    @patch("apps.imports.views.preview_url_import")
    def test_api_preview_url(self, mock_preview, client):
        user = User.objects.create_user("apiuser", password="test")
        client.force_login(user)
        mock_preview.return_value = {
            "title": "Test",
            "markdown": "## Hi",
            "summary": "Hi",
            "sections": [],
            "section_count": 1,
            "source_type": "web",
            "source_url": "https://example.com",
            "source_label": "Web page",
            "meta": {},
            "ai_used": False,
        }
        response = client.post(
            reverse("import_url_preview"),
            {"url": "https://example.com", "source_type": "web"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test"
