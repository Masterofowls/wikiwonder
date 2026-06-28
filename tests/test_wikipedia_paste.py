"""Tests for Wikipedia paste, citations, and internal wiki links."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.wiki.models import WikiPage
from apps.wiki.services.citations import replace_numeric_citations
from apps.wiki.services.markdown import render_markdown
from apps.wiki.services.pages import create_page_from_markdown
from apps.wiki.services.wikipedia_paste import is_wikipedia_paste, normalize_wikipedia_paste
from apps.wiki.services.wikilinks import linkify_internal_pages, process_wikilink_syntax, resolve_markdown_links

User = get_user_model()

XSS_SNIPPET = (
    "Cross-site scripting (XSS)[a] is a type of security vulnerability.[1] "
    "OWASP considers the term cross-site scripting to be a misnomer.[2]\n\n"
    "Background\n"
    "Main article: Web security and Same-origin policy\n"
    "Security on the web depends on a variety of mechanisms.[3]\n\n"
    "Types\n"
    "Non-persistent (reflected)\n"
    "The non-persistent cross-site scripting vulnerability is basic.[9]"
)


@pytest.mark.django_db
class TestWikipediaPaste:
    def test_detects_wikipedia_paste(self):
        assert is_wikipedia_paste(XSS_SNIPPET)

    def test_normalizes_structure_and_citations(self):
        result = normalize_wikipedia_paste(XSS_SNIPPET)
        md = result["markdown"]
        assert "# Cross-site scripting" in md.splitlines()[0]
        assert "## Background" in md
        assert "[1][cite-1]" in md
        assert "## References" in md
        assert '[cite-1]:' in md

    def test_hatnote_becomes_wikilink(self):
        result = normalize_wikipedia_paste(XSS_SNIPPET)
        md = result["markdown"]
        assert "> **Main article:**" in md
        assert "Web security" in md
        assert "Same-origin policy" in md


@pytest.mark.django_db
class TestWikiLinks:
    def test_wikilink_syntax_resolves(self):
        create_page_from_markdown(
            "Web security",
            "## Intro\n\nBasics.",
            status=WikiPage.Status.PUBLISHED,
        )
        text = process_wikilink_syntax("See [[Web security]] for details.")
        assert "](/wiki/web-security/)" in text

    def test_auto_link_internal_page(self):
        create_page_from_markdown(
            "Cross-site scripting",
            "## Intro\n\nXSS basics.",
            status=WikiPage.Status.PUBLISHED,
        )
        text = linkify_internal_pages("Learn about Cross-site scripting on our wiki.")
        assert "[Cross-site scripting](/wiki/cross-site-scripting/)" in text


@pytest.mark.django_db
class TestCitationRendering:
    def test_citation_links_have_preview_class(self):
        md = replace_numeric_citations("Security issue[1] and more[2].", {"1": {"url": "https://example.com/1", "label": "Ref one"}})
        html = render_markdown(md)
        assert "wiki-cite-ref" in html
        assert "data-cite=\"1\"" in html


@pytest.mark.django_db
class TestWikipediaPasteAPI:
    def test_api_formats_paste(self, client):
        user = User.objects.create_user("pasteuser", password="x")
        client.force_login(user)
        response = client.post(
            reverse("wiki:paste_wikipedia"),
            {"text": XSS_SNIPPET},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["citation_count"] >= 2
        assert "[1][cite-1]" in data["markdown"]


@pytest.mark.django_db
class TestSameOriginPolicyPaste:
    @pytest.fixture
    def sop_paste(self):
        from pathlib import Path

        return Path(__file__).parent.joinpath("fixtures", "sop_paste.txt").read_text(encoding="utf-8")

    def test_html_br_and_introduction_labels(self, sop_paste):
        result = normalize_wikipedia_paste(
            sop_paste,
            source_url="https://en.wikipedia.org/wiki/Same-origin_policy",
        )
        md = result["markdown"]
        assert result["title"] == "Same-origin policy"
        assert "<br" not in md
        assert md.startswith("# Same-origin policy")
        assert "In computing, the same-origin policy" in md
        assert "Introduction\nIntroduction" not in md

    def test_sections_table_and_hatnote(self, sop_paste):
        result = normalize_wikipedia_paste(
            sop_paste,
            source_url="https://en.wikipedia.org/wiki/Same-origin_policy",
        )
        md = result["markdown"]
        assert "## History" in md
        assert "## Implementation" in md
        assert "| Compared URL | Outcome | Reason |" in md
        assert "> **Main article:**" in md
        assert "JSONP" in md
        assert "`<script>`" in md
        assert "[1][cite-1]" in md
