"""Tests for edit, export, suggestions, and enriched health check."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.wiki.models import EditSuggestion, WikiPage
from apps.wiki.services.pages import create_page_from_markdown

User = get_user_model()


@pytest.fixture
def author(db):
    return User.objects.create_user("author", password="pass")


@pytest.fixture
def other(db):
    return User.objects.create_user("other", password="pass")


@pytest.fixture
def page(author):
    return create_page_from_markdown(
        "Editable Page",
        "## Intro\n\nHello world.",
        author=author,
        status=WikiPage.Status.PUBLISHED,
    )


@pytest.mark.django_db
class TestEditPage:
    def test_author_can_open_edit(self, client, author, page):
        client.force_login(author)
        url = reverse("wiki:edit_page", kwargs={"slug": page.slug})
        assert client.get(url).status_code == 200

    def test_non_author_forbidden(self, client, other, page):
        client.force_login(other)
        url = reverse("wiki:edit_page", kwargs={"slug": page.slug})
        assert client.get(url).status_code == 404


@pytest.mark.django_db
class TestPageExport:
    def test_export_markdown(self, client, page):
        url = reverse("wiki:page_export", kwargs={"slug": page.slug})
        response = client.get(url, {"format": "md"})
        assert response.status_code == 200
        assert b"Hello world" in response.content
        assert "attachment" in response["Content-Disposition"]


@pytest.mark.django_db
class TestEditSuggestions:
    def test_logged_in_user_can_suggest(self, client, other, page):
        client.force_login(other)
        url = reverse("wiki:suggest_edit", kwargs={"slug": page.slug})
        response = client.post(
            url,
            {"content": "## Updated\n\nNew text.", "change_summary": "Fix typo"},
        )
        assert response.status_code in (200, 302)
        assert EditSuggestion.objects.filter(page=page).exists()

    def test_staff_can_approve(self, client, author, page):
        staff = User.objects.create_user("staff", password="pass", is_staff=True)
        suggestion = EditSuggestion.objects.create(
            page=page,
            title=page.title,
            content="## Updated\n\nApproved.",
            change_summary="Improve intro",
            author=author,
        )
        client.force_login(staff)
        url = reverse("wiki:approve_suggestion", kwargs={"pk": suggestion.pk})
        response = client.post(url)
        assert response.status_code in (200, 302)
        suggestion.refresh_from_db()
        assert suggestion.status == EditSuggestion.Status.APPROVED


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_includes_media_probe(self, client):
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "database" in data
        assert "media" in data
