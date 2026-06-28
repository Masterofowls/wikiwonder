"""Tests for Lara Translate auto-translation."""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from apps.wiki.models import WikiPage
from apps.wiki.services.lara_translate import LaraTranslateService, auto_translate_wiki_page
from apps.wiki.services.pages import create_page_from_markdown

User = get_user_model()


@pytest.fixture
def author(db):
    return User.objects.create_user("author", password="pass")


@pytest.fixture
def page(author):
    with patch("apps.wiki.services.lara_translate.auto_translate_wiki_page"):
        return create_page_from_markdown(
            "Translate Me",
            "## Intro\n\nHello.",
            author=author,
            status=WikiPage.Status.PUBLISHED,
        )


@pytest.mark.django_db
class TestLaraTranslateService:
    @override_settings(
        LARA_ACCESS_KEY_ID="test-id",
        LARA_ACCESS_KEY_SECRET="test-secret",
        LARA_TARGET_LANGUAGES=["ru"],
    )
    @patch("lara_sdk.Translator")
    def test_translate_text(self, mock_translator_cls):
        mock_instance = mock_translator_cls.return_value
        mock_instance.translate.return_value = type("R", (), {"translation": "Привет"})()
        service = LaraTranslateService()
        assert service.translate_text("Hello", target="ru") == "Привет"
        mock_instance.translate.assert_called_once()

    @override_settings(LARA_ACCESS_KEY_ID="", LARA_ACCESS_KEY_SECRET="")
    def test_not_configured_skips(self):
        user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_user(
            "u1", password="x"
        )
        page = create_page_from_markdown(
            "Test",
            "## Section\n\nBody.",
            author=user,
            status=WikiPage.Status.DRAFT,
        )
        assert auto_translate_wiki_page(page) == {}


@pytest.mark.django_db
class TestAutoTranslatePage:
    @override_settings(
        LARA_ACCESS_KEY_ID="test-id",
        LARA_ACCESS_KEY_SECRET="test-secret",
        LARA_AUTO_TRANSLATE=True,
        LARA_TARGET_LANGUAGES=["ru"],
    )
    @patch("apps.wiki.services.lara_translate.auto_translate_wiki_page")
    def test_create_page_triggers_translation(self, mock_auto):
        user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_user(
            "u2", password="x"
        )
        create_page_from_markdown(
            "English title",
            "## Intro\n\nEnglish body.",
            author=user,
        )
        mock_auto.assert_called_once()

    @override_settings(
        LARA_ACCESS_KEY_ID="test-id",
        LARA_ACCESS_KEY_SECRET="test-secret",
        LARA_AUTO_TRANSLATE=True,
        LARA_TARGET_LANGUAGES=["ru"],
    )
    def test_auto_translate_sets_russian_fields(self):
        user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_user(
            "u3", password="x"
        )
        with patch("apps.wiki.services.lara_translate.auto_translate_wiki_page"):
            page = create_page_from_markdown(
                "Hello",
                "## Section\n\nWorld.",
                author=user,
                split_sections=True,
            )

        def fake_translate(text, *, target, source=None):
            return {
                "Hello": "Привет",
                "World.": "Мир.",
                "Section": "Раздел",
            }.get(text, f"{text}-RU")

        with patch.object(LaraTranslateService, "translate_text", side_effect=fake_translate):
            results = auto_translate_wiki_page(page, force=True)

        page.refresh_from_db()
        assert results == {"ru": True}
        assert page.title_ru == "Привет"
        assert "World.-RU" in (page.content_ru or "")
        section = page.sections.first()
        assert section.title_ru == "Раздел"


@pytest.mark.django_db
class TestGenerateTranslationView:
    @patch("apps.wiki.views_translate.auto_translate_wiki_page", return_value={"ru": True})
    @patch("apps.wiki.views_translate.get_lara_service")
    def test_author_can_generate_translation(self, mock_lara, mock_translate, client, author, page):
        mock_lara.return_value.is_configured = True
        client.force_login(author)
        url = reverse("wiki:generate_translation", kwargs={"slug": page.slug})
        response = client.post(url)
        assert response.status_code == 302
        assert response.url.endswith("?lang=ru")
        mock_translate.assert_called_once()

    def test_non_author_forbidden(self, client, page):
        other = User.objects.create_user("other", password="pass")
        client.force_login(other)
        url = reverse("wiki:generate_translation", kwargs={"slug": page.slug})
        assert client.post(url).status_code == 404
