"""Search API tests."""
import pytest
from django.urls import reverse

from apps.search.services import instant_search
from apps.wiki.models import WikiPage
from apps.wiki.services.pages import create_page_from_markdown


@pytest.mark.django_db
class TestInstantSearch:
    def test_instant_search_requires_min_length(self):
        assert instant_search("a") == []

    def test_instant_search_finds_wiki_page(self, django_user_model):
        user = django_user_model.objects.create_user("searcher", password="test")
        create_page_from_markdown(
            "PostgreSQL Guide",
            "## Intro\n\nDatabase content about postgres full text search.",
            author=user,
            status=WikiPage.Status.PUBLISHED,
        )
        results = instant_search("postgres")
        assert any(r["type"] == "wiki" and "PostgreSQL" in r["title"] for r in results)

    def test_search_api(self, client, django_user_model):
        user = django_user_model.objects.create_user("apiuser", password="test")
        create_page_from_markdown(
            "Alpine Tips",
            "Alpine.js reactive components.",
            author=user,
            status=WikiPage.Status.PUBLISHED,
        )
        response = client.get(reverse("search:instant"), {"q": "alpine"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
