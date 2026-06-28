"""Tests for native Wikipedia URL import pipeline."""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.imports.sources.wikipedia_html import wikipedia_html_to_markdown

User = get_user_model()

SAMPLE_WIKI_HTML = """
<div class="mw-parser-output">
<div class="hatnote navigation-not-searchable">Main article: [[JSONP]]</div>
<div class="navbox">should be removed</div>
<h2><span class="mw-headline" id="History">History</span></h2>
<p>Introduced in 1995<sup class="reference"><a href="#cite_note-1">[1]</a></sup>.</p>
<table class="wikitable">
<tr><th>URL</th><th>Outcome</th></tr>
<tr><td>http://example.com/a</td><td>Success</td></tr>
</table>
<div class="thumb tright"><div class="thumbinner">
<img src="//upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Test.png/220px-Test.png" alt="Diagram">
<div class="thumbcaption">Example diagram</div>
</div></div>
</div>
"""

WIKI_API_RESPONSE = {
    "parse": {
        "displaytitle": "Same-origin policy",
        "text": {"*": SAMPLE_WIKI_HTML},
        "sections": [
            {"index": "1", "line": "History", "level": "2", "toclevel": "1", "anchor": "History"},
        ],
        "images": ["File:Test.png"],
    }
}


@pytest.mark.django_db
class TestWikipediaHtmlConverter:
    def test_strips_navbox_and_keeps_sections(self):
        md = wikipedia_html_to_markdown(SAMPLE_WIKI_HTML, base_url="https://en.wikipedia.org", lang="en")
        assert "navbox" not in md.lower()
        assert "## History" in md
        assert "[1]" in md
        assert "Main article" in md or "JSONP" in md

    def test_converts_table(self):
        md = wikipedia_html_to_markdown(SAMPLE_WIKI_HTML, base_url="https://en.wikipedia.org", lang="en")
        assert "| URL | Outcome |" in md or "| URL |" in md

    def test_converts_thumb_image(self):
        md = wikipedia_html_to_markdown(SAMPLE_WIKI_HTML, base_url="https://en.wikipedia.org", lang="en")
        assert "upload.wikimedia.org" in md
        assert "Example diagram" in md or "Diagram" in md

    def test_converts_figure_diagram_with_file_link(self):
        html = """
        <div class="mw-parser-output">
        <h2><span class="mw-headline" id="Mode">Mode of operation</span></h2>
        <figure class="mw-default-size" typeof="mw:File/Thumb">
          <a href="/wiki/File:ContentSecurityPolicy3_diagram.png" class="mw-file-description">
            <img src="//upload.wikimedia.org/wikipedia/commons/thumb/0/09/ContentSecurityPolicy3_diagram.png/250px-ContentSecurityPolicy3_diagram.png"
              srcset="//upload.wikimedia.org/wikipedia/commons/thumb/0/09/ContentSecurityPolicy3_diagram.png/500px-ContentSecurityPolicy3_diagram.png 2x"
              alt="Diagram" class="mw-file-element" />
          </a>
          <figcaption>Mapping between HTML5 and JavaScript features and Content Security Policy controls</figcaption>
        </figure>
        <p>Body text after diagram.</p>
        </div>
        """
        md = wikipedia_html_to_markdown(html, base_url="https://en.wikipedia.org", lang="en")
        assert "ContentSecurityPolicy3_diagram" in md
        assert "Mapping between HTML5" in md
        assert "![Mapping between HTML5" in md or "![" in md

    def test_converts_gallery_images(self):
        html = """
        <div class="mw-parser-output">
        <ul class="gallery mw-gallery-traditional">
          <li class="gallerybox">
            <div class="thumb"><img src="//upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Gallery.png/120px-Gallery.png" alt="A"></div>
            <div class="gallerytext">Gallery item A</div>
          </li>
        </ul>
        </div>
        """
        md = wikipedia_html_to_markdown(html, base_url="https://en.wikipedia.org", lang="en")
        assert "Gallery.png" in md
        assert "Gallery item A" in md


@pytest.mark.django_db
class TestWikipediaUrlImportAPI:
    @patch("apps.imports.sources.wikipedia.fetch_page_images", return_value=[])
    @patch("apps.imports.sources.wikipedia.fetch_wikipedia_citations", return_value={"1": {"url": "https://example.com/ref", "label": "Ref 1"}})
    @patch("apps.imports.sources.wikipedia.fetch_json")
    def test_import_wikipedia_api(self, mock_json, _mock_cites, _mock_images, client):
        mock_json.return_value = WIKI_API_RESPONSE
        user = User.objects.create_user("wikiimport", password="x")
        client.force_login(user)
        response = client.post(
            reverse("wiki:import_wikipedia"),
            {"url": "https://en.wikipedia.org/wiki/Same-origin_policy"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Same-origin policy"
        assert "Imported from" in data["markdown"]
        assert "## History" in data["markdown"]

    def test_import_wikipedia_requires_valid_url(self, client):
        user = User.objects.create_user("wikiimport2", password="x")
        client.force_login(user)
        response = client.post(
            reverse("wiki:import_wikipedia"),
            {"url": "https://example.com/not-wiki"},
            content_type="application/json",
        )
        assert response.status_code == 400
