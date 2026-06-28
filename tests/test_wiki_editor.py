"""Tests for editor upload and URL highlighting."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.wiki.services.embeds import highlight_urls
from apps.wiki.services.markdown import render_markdown


@pytest.mark.django_db
class TestEditorUpload:
    def test_upload_image_returns_markdown(self, client, django_user_model):
        user = django_user_model.objects.create_user("uploader", password="x")
        client.force_login(user)
        upload = SimpleUploadedFile("photo.png", b"fakepng", content_type="image/png")
        response = client.post(reverse("wiki:editor_upload"), {"file": upload})
        assert response.status_code == 200
        data = response.json()
        assert data["url"]
        assert data["type"] == "image"
        assert "![Photo" in data["markdown"]
        assert data["url"] in data["markdown"]

    def test_upload_gif_returns_markdown(self, client, django_user_model):
        user = django_user_model.objects.create_user("gifuser", password="x")
        client.force_login(user)
        upload = SimpleUploadedFile("anim.gif", b"GIF89a", content_type="image/gif")
        response = client.post(reverse("wiki:editor_upload"), {"file": upload})
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "gif"
        assert "![Anim" in data["markdown"]
        assert "/media/editor/" in data["url"]

    def test_upload_requires_login(self, client):
        upload = SimpleUploadedFile("photo.png", b"fakepng", content_type="image/png")
        response = client.post(reverse("wiki:editor_upload"), {"file": upload})
        assert response.status_code == 302

    def test_upload_rejects_unknown_type(self, client, django_user_model):
        user = django_user_model.objects.create_user("uploader2", password="x")
        client.force_login(user)
        upload = SimpleUploadedFile("notes.xyz", b"data", content_type="application/octet-stream")
        response = client.post(reverse("wiki:editor_upload"), {"file": upload})
        assert response.status_code == 400


class TestHighlightUrls:
    @pytest.mark.django_db
    def test_bare_url_becomes_markdown_link(self):
        text = "See https://example.com/docs for more."
        result = highlight_urls(text)
        assert "[https://example.com/docs](https://example.com/docs)" in result

    @pytest.mark.django_db
    def test_does_not_break_existing_markdown_links(self):
        text = "[Cross-site scripting (XSS)](https://en.wikipedia.org/wiki/Cross-site_scripting)"
        result = highlight_urls(text)
        assert result == text

    @pytest.mark.django_db
    def test_rendered_html_has_preview_classes(self):
        html = render_markdown("Visit https://example.com today.")
        assert "wiki-url-highlight" in html
        assert "wiki-ext-link" in html
        assert 'data-url="https://example.com"' in html
