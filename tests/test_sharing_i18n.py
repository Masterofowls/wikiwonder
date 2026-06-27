"""Tests for share API, offline bookmarks, and language switching."""
import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.wiki.models import Bookmark, WikiPage


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="reader", password="pass12345")


@pytest.fixture
def page(db):
    return WikiPage.objects.create(
        title="Share Test",
        slug="share-test",
        content="# Hello",
        status=WikiPage.Status.PUBLISHED,
    )


@pytest.mark.django_db
def test_page_share_api(client, page):
    res = client.get(f"/api/pages/{page.slug}/share/")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Share Test"
    assert "share-test" in data["url"]


@pytest.mark.django_db
def test_bookmarks_offline_requires_auth(client, page):
    res = client.get("/api/bookmarks/offline/")
    assert res.status_code == 302


@pytest.mark.django_db
def test_bookmarks_offline_urls(client, user, page):
    client.force_login(user)
    Bookmark.objects.create(user=user, page=page)
    res = client.get("/api/bookmarks/offline/")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 1
    assert "share-test" in data["urls"][0]


@pytest.mark.django_db
def test_set_language(client):
    res = client.post("/set-language/", {"language": "de", "next": "/"})
    assert res.status_code == 302
    assert client.cookies["wikiwonder_lang"].value == "de"
