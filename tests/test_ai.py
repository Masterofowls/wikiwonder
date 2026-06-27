"""Tests for Cerebras AI integration."""
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestCerebrasAI:
    def test_status_unconfigured(self, client):
        with patch("apps.ai.views.get_ai_service") as mock_get:
            mock_get.return_value.is_configured = False
            mock_get.return_value.model = "gpt-oss-120b"
            response = client.get(reverse("ai_status"))
        assert response.status_code == 200
        assert response.json()["configured"] is False

    def test_format_requires_auth(self, client):
        response = client.post(reverse("ai_format"), {"text": "hello"}, content_type="application/json")
        assert response.status_code in (401, 403)

    def test_format_returns_markdown(self, client, django_user_model):
        user = django_user_model.objects.create_user("aiuser", password="x")
        client.force_login(user)

        mock_service = MagicMock()
        mock_service.is_configured = True
        mock_service.model = "gpt-oss-120b"
        mock_service.enrich_import.return_value = {
            "title": "Fast Inference",
            "markdown": "## Why speed matters\n\nContent here.",
            "summary": "A note on inference speed.",
        }

        with patch("apps.ai.views.get_ai_service", return_value=mock_service):
            response = client.post(
                reverse("ai_format"),
                {"text": "Why is fast inference important?", "title": ""},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.json()
        assert "markdown" in data
        assert data["title"] == "Fast Inference"
        mock_service.enrich_import.assert_called_once()

    def test_chat_endpoint(self, client, django_user_model):
        user = django_user_model.objects.create_user("chatuser", password="x")
        client.force_login(user)

        mock_service = MagicMock()
        mock_service.is_configured = True
        mock_service.model = "gpt-oss-120b"
        mock_service.chat.return_value = "Fast inference reduces latency."

        with patch("apps.ai.views.get_ai_service", return_value=mock_service):
            response = client.post(
                reverse("ai_chat"),
                {"content": "Why is fast inference important?"},
                content_type="application/json",
            )

        assert response.status_code == 200
        assert "Fast inference" in response.json()["content"]

    def test_service_chat(self, settings):
        settings.CEREBRAS_API_KEY = "test-key"
        settings.CEREBRAS_MODEL = "gpt-oss-120b"

        from apps.ai.services import CerebrasService

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Hello from Cerebras"))]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        service = CerebrasService()
        service._client = mock_client

        result = service.chat([{"role": "user", "content": "hi"}])
        assert result == "Hello from Cerebras"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-oss-120b"
        assert call_kwargs["stream"] is False
        assert call_kwargs["reasoning_effort"] == "medium"
