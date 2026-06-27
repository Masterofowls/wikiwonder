"""Tests for wiki page creation and sharing."""
import pytest
from django.urls import reverse

from apps.media.services import attach_files_to_page
from apps.wiki.models import WikiPage
from apps.wiki.services.pages import create_page_from_markdown


@pytest.mark.django_db
class TestWikiCreate:
    def test_create_page_has_path(self, django_user_model):
        user = django_user_model.objects.create_user("author", password="x")
        page = create_page_from_markdown(
            "Test Wiki",
            "## Section\n\nBody content here.",
            author=user,
            status=WikiPage.Status.PUBLISHED,
        )
        assert page.slug
        assert page.get_absolute_url().startswith("/wiki/")
        assert page.sections.count() >= 1

    def test_create_page_view_redirects(self, client, django_user_model):
        user = django_user_model.objects.create_user("writer", password="x")
        client.force_login(user)
        response = client.post(
            reverse("wiki:create_page"),
            {
                "title": "My New Wiki",
                "content": "# Hello\n\nFull **markdown** paste test.",
                "raw_markdown": "on",
                "publish": "on",
            },
        )
        assert response.status_code == 302
        page = WikiPage.objects.get(title="My New Wiki")
        assert response.url == page.get_absolute_url()

    def test_api_create_returns_url(self, client, django_user_model):
        user = django_user_model.objects.create_user("apiuser", password="x")
        client.force_login(user)
        response = client.post(
            reverse("page-list"),
            {"title": "API Page", "content": "# Hi\n\nContent.", "status": "published"},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert "url" in data
        assert "path" in data
        assert data["path"].startswith("/wiki/")

    def test_attach_image_block(self, django_user_model):
        from django.core.files.uploadedfile import SimpleUploadedFile

        user = django_user_model.objects.create_user("media", password="x")
        page = create_page_from_markdown("Media Page", "Intro", author=user)
        upload = SimpleUploadedFile("photo.png", b"fakepng", content_type="image/png")
        blocks = attach_files_to_page(page, [upload])
        assert len(blocks) == 1
        page.refresh_from_db()
        assert "Photo" in page.content or "/media/blocks/" in page.content
