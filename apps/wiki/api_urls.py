from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.wiki import views_sharing
from apps.wiki.serializers import BookmarkViewSet, WikiPageViewSet

router = DefaultRouter()
router.register("pages", WikiPageViewSet, basename="page")
router.register("bookmarks", BookmarkViewSet, basename="bookmark")

urlpatterns = [
    path(
        "bookmarks/offline/",
        views_sharing.BookmarkOfflineAPIView.as_view(),
        name="bookmarks_offline",
    ),
    path(
        "pages/<slug:slug>/share/",
        views_sharing.PageShareAPIView.as_view(),
        name="page_share",
    ),
    path("", include(router.urls)),
]
