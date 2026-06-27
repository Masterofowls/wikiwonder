from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.wiki.serializers import BookmarkViewSet, WikiPageViewSet

router = DefaultRouter()
router.register("pages", WikiPageViewSet, basename="page")
router.register("bookmarks", BookmarkViewSet, basename="bookmark")

urlpatterns = [
    path("", include(router.urls)),
]
