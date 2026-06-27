import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_page_get_renders(client, django_user_model):
    user = django_user_model.objects.create_user("writer2", password="x")
    client.force_login(user)
    response = client.get(reverse("wiki:create_page"))
    assert response.status_code == 200, response.content[:500]
