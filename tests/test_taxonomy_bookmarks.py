"""Tests for taxonomy and AJAX bookmarks."""
import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.search.services import instant_search
from apps.wiki.models import Category, Tag, WikiPage
from apps.wiki.services.pages import create_page_from_markdown
from apps.wiki.services.taxonomy import parse_tag_names

User = get_user_model()


@pytest.mark.django_db
class TestTaxonomy:
    def test_parse_tag_names(self):
        assert parse_tag_names("security, web; xss") == ["security", "web", "xss"]

    def test_create_page_with_tags_and_category(self, client):
        staff = User.objects.create_user("staff", password="x", is_staff=True)
        cat = Category.objects.create(name="Security", slug="security")
        client.force_login(staff)
        response = client.post(
            reverse("wiki:create_page"),
            {
                "title": "Tagged Page",
                "content": "# Hi\n\nBody.",
                "raw_markdown": "on",
                "publish": "on",
                "category": str(cat.pk),
                "tags": "xss, web security",
            },
        )
        assert response.status_code == 302
        page = WikiPage.objects.get(title="Tagged Page")
        assert page.category_id == cat.pk
        assert page.tags.count() == 2

    def test_quick_category_api_staff_only(self, client):
        user = User.objects.create_user("user", password="x")
        staff = User.objects.create_user("staff", password="x", is_staff=True)
        client.force_login(user)
        denied = client.post(
            reverse("wiki:quick_category"),
            json.dumps({"name": "New Cat"}),
            content_type="application/json",
        )
        assert denied.status_code == 403
        client.force_login(staff)
        ok = client.post(
            reverse("wiki:quick_category"),
            json.dumps({"name": "New Cat"}),
            content_type="application/json",
        )
        assert ok.status_code == 200
        assert Category.objects.filter(name="New Cat").exists()

    def test_search_finds_category_and_tags(self):
        cat = Category.objects.create(name="Web Security", slug="web-security")
        Tag.objects.create(name="XSS", slug="xss")
        WikiPage.objects.create(
            title="Cross-site scripting",
            slug="cross-site-scripting",
            content="XSS article",
            summary="XSS",
            status=WikiPage.Status.PUBLISHED,
            category=cat,
        )
        data = instant_search("xss")
        types = {r["type"] for r in data["results"]}
        assert "wiki" in types or "tag" in types


@pytest.mark.django_db
class TestBookmarkAjax:
    def test_toggle_bookmark_json(self, client, django_user_model):
        user = django_user_model.objects.create_user("reader", password="x")
        author = django_user_model.objects.create_user("author", password="x")
        page = create_page_from_markdown(
            "Bookmark Me",
            "Content",
            author=author,
            status=WikiPage.Status.PUBLISHED,
        )
        client.force_login(user)
        add = client.post(
            reverse("wiki:toggle_bookmark", kwargs={"slug": page.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert add.status_code == 200
        assert add.json()["bookmarked"] is True
        remove = client.post(
            reverse("wiki:toggle_bookmark", kwargs={"slug": page.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert remove.json()["bookmarked"] is False
