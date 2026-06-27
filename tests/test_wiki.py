"""WikiWonder tests."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.imports.services import plain_text_to_markdown, preview_import
from apps.wiki.models import WikiPage
from apps.wiki.services.markdown import split_markdown_into_sections
from apps.wiki.services.pages import create_page_from_markdown

User = get_user_model()


@pytest.mark.django_db
class TestMarkdownServices:
    def test_split_sections(self):
        content = "## First\n\nContent one.\n\n## Second\n\nContent two."
        sections = split_markdown_into_sections(content)
        assert len(sections) == 2
        assert sections[0]["title"] == "First"
        assert sections[1]["title"] == "Second"

    def test_plain_text_conversion(self):
        text = "INTRODUCTION\n\nSome text here.\n\n- Item one\n- Item two"
        md = plain_text_to_markdown(text)
        assert "## Introduction" in md
        assert "- Item one" in md


@pytest.mark.django_db
class TestWikiPages:
    def test_create_page_from_markdown(self):
        user = User.objects.create_user("testuser", password="test")
        page = create_page_from_markdown(
            "Test Page",
            "## Section A\n\nHello.\n\n## Section B\n\nWorld.",
            author=user,
            status=WikiPage.Status.PUBLISHED,
        )
        assert page.slug == "test-page"
        assert page.sections.count() == 2

    def test_home_page(self, client):
        response = client.get(reverse("wiki:home"))
        assert response.status_code == 200

    def test_rss_feed(self, client):
        response = client.get(reverse("wiki:feed_latest"))
        assert response.status_code == 200
        assert "application/atom+xml" in response["Content-Type"]


@pytest.mark.django_db
class TestImportPreview:
    def test_preview_without_ai(self):
        result = preview_import("Hello world.\n\nSome content.", use_ai=False)
        assert result["title"]
        assert result["markdown"]
        assert not result["ai_used"]
