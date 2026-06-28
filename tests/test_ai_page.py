"""Tests for page AI features and daily quota."""
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from apps.ai.quota import QuotaExceededError, consume_quota, daily_limit, quota_status


@pytest.mark.django_db
class TestAIQuota:
    def test_consume_up_to_limit(self, django_user_model):
        user = django_user_model.objects.create_user("quotauser", password="x")
        limit = daily_limit()
        for _ in range(limit):
            consume_quota(user)
        with pytest.raises(QuotaExceededError):
            consume_quota(user)
        status = quota_status(user)
        assert status["remaining"] == 0
        assert status["used"] == limit

    def test_staff_unlimited(self, django_user_model):
        user = django_user_model.objects.create_user("staff", password="x", is_staff=True)
        for _ in range(daily_limit() + 5):
            consume_quota(user)
        assert quota_status(user)["unlimited"] is True


@pytest.mark.django_db
class TestPageAI:
    def test_summarize_requires_auth(self, client):
        response = client.post(
            reverse("ai_page_summarize"),
            {"slug": "test"},
            content_type="application/json",
        )
        assert response.status_code in (401, 403)

    def test_summarize_page(self, client, django_user_model):
        from apps.wiki.models import WikiPage
        from apps.wiki.services.pages import create_page_from_markdown

        user = django_user_model.objects.create_user("reader", password="x")
        page = create_page_from_markdown(
            "AI Test Page",
            "## Intro\n\nSome wiki content about testing.",
            author=user,
            status=WikiPage.Status.PUBLISHED,
        )
        client.force_login(user)

        mock_service = MagicMock()
        mock_service.is_configured = True
        mock_service.model = "gpt-oss-120b"
        mock_service.summarize_wiki_page.return_value = "- Point one\n- Point two"

        with patch("apps.ai.views.get_ai_service", return_value=mock_service):
            response = client.post(
                reverse("ai_page_summarize"),
                {"slug": page.slug},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.json()
        assert "Point one" in data["summary"]
        assert data["quota"]["used"] == 1

    def test_ask_page(self, client, django_user_model):
        from apps.wiki.models import WikiPage
        from apps.wiki.services.pages import create_page_from_markdown

        user = django_user_model.objects.create_user("asker", password="x")
        page = create_page_from_markdown(
            "Ask Page",
            "## Facts\n\nThe sky is blue.",
            author=user,
            status=WikiPage.Status.PUBLISHED,
        )
        client.force_login(user)

        mock_service = MagicMock()
        mock_service.is_configured = True
        mock_service.model = "gpt-oss-120b"
        mock_service.ask_about_wiki_page.return_value = "The article mentions the sky is blue."

        with patch("apps.ai.views.get_ai_service", return_value=mock_service):
            response = client.post(
                reverse("ai_page_ask"),
                {"slug": page.slug, "question": "What color is the sky?"},
                content_type="application/json",
            )

        assert response.status_code == 200
        assert "blue" in response.json()["answer"].lower()

    def test_admin_assist_staff_only(self, client, django_user_model):
        user = django_user_model.objects.create_user("regular", password="x")
        client.force_login(user)
        response = client.post(
            reverse("ai_admin_assist"),
            {"action": "summary", "text": "# Hello\n\nWorld"},
            content_type="application/json",
        )
        assert response.status_code == 403
