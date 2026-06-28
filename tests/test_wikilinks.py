"""Tests for wiki link resolution and URL highlighting."""
import pytest

from apps.wiki.models import WikiPage
from apps.wiki.services.embeds import highlight_urls
from apps.wiki.services.markdown import render_markdown
from apps.wiki.services.pages import create_page_from_markdown
from apps.wiki.services.wikilinks import (
    linkify_internal_pages,
    process_wikilink_syntax,
    resolve_markdown_links,
)


@pytest.mark.django_db
class TestHighlightUrls:
    def test_bare_url_becomes_markdown_link(self):
        text = "See https://example.com/docs for more."
        result = highlight_urls(text)
        assert "[https://example.com/docs](https://example.com/docs)" in result

    def test_does_not_break_existing_markdown_links(self):
        text = "[Cross-site scripting (XSS)](https://en.wikipedia.org/wiki/Cross-site_scripting)"
        result = highlight_urls(text)
        assert result == text
        assert "]([" not in result

    def test_rendered_html_has_preview_classes(self):
        html = render_markdown("Visit https://example.com today.")
        assert "wiki-url-highlight" in html
        assert "wiki-ext-link" in html


@pytest.mark.django_db
class TestWikiLinkResolution:
    def test_wikipedia_url_maps_to_local_page(self):
        create_page_from_markdown(
            "Cross-site scripting",
            "## Intro\n\nXSS.",
            status=WikiPage.Status.PUBLISHED,
        )
        md = "[XSS article](https://en.wikipedia.org/wiki/Cross-site_scripting)"
        resolved = resolve_markdown_links(md)
        assert "](/wiki/cross-site-scripting/)" in resolved
        assert "wikipedia.org" not in resolved

    def test_repairs_nested_broken_link(self):
        create_page_from_markdown(
            "Cross-site scripting",
            "## Intro\n\nXSS.",
            status=WikiPage.Status.PUBLISHED,
        )
        broken = (
            "[Cross-site scripting (XSS)]"
            "([https://en.wikipedia.org/wiki/Cross-site_scripting]"
            "(https://en.wikipedia.org/wiki/Cross-site_scripting))"
        )
        resolved = resolve_markdown_links(broken)
        assert "](/wiki/cross-site-scripting/)" in resolved
        assert "]([" not in resolved

    def test_relative_wikipedia_path_resolves_locally(self):
        create_page_from_markdown(
            "Same-origin policy",
            "## Intro\n\nSOP.",
            status=WikiPage.Status.PUBLISHED,
        )
        md = "[SOP](/wiki/Same-origin_policy)"
        resolved = resolve_markdown_links(md)
        assert "](/wiki/same-origin-policy/)" in resolved

    def test_external_when_no_local_page(self):
        md = "[Python](https://en.wikipedia.org/wiki/Python_(programming_language))"
        resolved = resolve_markdown_links(md)
        assert "wikipedia.org/wiki/Python" in resolved

    def test_render_resolves_wikipedia_to_local(self):
        create_page_from_markdown(
            "Cross-site scripting",
            "## Intro\n\nXSS.",
            status=WikiPage.Status.PUBLISHED,
        )
        create_page_from_markdown(
            "Same-origin policy",
            (
                "See [Cross-site scripting (XSS)]"
                "(https://en.wikipedia.org/wiki/Cross-site_scripting) for details."
            ),
            status=WikiPage.Status.PUBLISHED,
        )
        html = render_markdown(
            "See [Cross-site scripting (XSS)](https://en.wikipedia.org/wiki/Cross-site_scripting) for details.",
            page_slug="same-origin-policy",
        )
        assert 'href="/wiki/cross-site-scripting/"' in html
        assert "wikipedia.org" not in html

    def test_wikilink_syntax_with_fallback_external(self):
        text = process_wikilink_syntax("Read [[Python (programming language)]] today.")
        assert "wikipedia.org" in text

    def test_auto_link_internal_page(self):
        create_page_from_markdown(
            "Cross-site scripting",
            "## Intro\n\nXSS basics.",
            status=WikiPage.Status.PUBLISHED,
        )
        text = linkify_internal_pages("Learn about Cross-site scripting on our wiki.")
        assert "[Cross-site scripting](/wiki/cross-site-scripting/)" in text
