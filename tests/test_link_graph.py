"""Tests for link graph, broken links, and Wikipedia metadata."""

import pytest
from django.contrib.auth import get_user_model

from apps.imports.wikipedia_metadata import apply_wikipedia_import_metadata
from apps.wiki.models import Tag, WikiPage, WikiPageAlias
from apps.wiki.services.broken_links import check_internal_links
from apps.wiki.services.link_graph import extract_link_targets, get_backlinks

User = get_user_model()


@pytest.mark.django_db
class TestLinkGraph:
    def test_extract_internal_and_external_links(self):
        md = "See [Local](/wiki/existing/) and [Wiki](https://en.wikipedia.org/wiki/Foo) and [Ext](https://example.com/x)."
        targets = extract_link_targets(md)
        assert "existing" in targets["internal_slugs"]
        assert "Foo" in targets["wikipedia_titles"] or any("Foo" in t for t in targets["wikipedia_titles"])
        assert "https://example.com/x" in targets["external_urls"]

    def test_backlinks(self):
        target = WikiPage.objects.create(
            title="Target Page",
            slug="target-page",
            content="Body",
            status=WikiPage.Status.PUBLISHED,
        )
        WikiPage.objects.create(
            title="Linker",
            slug="linker",
            content="See [target](/wiki/target-page/).",
            status=WikiPage.Status.PUBLISHED,
        )
        WikiPage.objects.create(
            title="Unrelated",
            slug="unrelated",
            content="No links here.",
            status=WikiPage.Status.PUBLISHED,
        )
        backlinks = get_backlinks(target.slug)
        assert len(backlinks) == 1
        assert backlinks[0].slug == "linker"

    def test_broken_internal_link(self):
        broken = check_internal_links("[x](/wiki/missing-page/)")
        assert any(item["target"] == "missing-page" and item["status"] == "missing" for item in broken)


@pytest.mark.django_db
class TestWikipediaMetadata:
    def test_apply_tags_aliases_source(self):
        page = WikiPage.objects.create(title="Same-origin policy", slug="same-origin-policy", content="x")
        preview = {
            "title": "Same-origin policy",
            "source_url": "https://en.wikipedia.org/wiki/Same-origin_policy",
            "meta": {
                "categories": ["Web security", "HTTP"],
                "alias_titles": ["Same-origin policy", "Same origin policy"],
            },
        }
        applied = apply_wikipedia_import_metadata(page, preview)
        page.refresh_from_db()
        assert page.source_url.startswith("https://en.wikipedia.org")
        assert applied["tags"] == 2
        assert Tag.objects.filter(name="Web security").exists()
        assert WikiPageAlias.objects.filter(page=page, alias__iexact="Same origin policy").exists()
