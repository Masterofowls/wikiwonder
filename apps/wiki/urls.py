from django.urls import path

from apps.wiki import views
from apps.wiki import views_create
from apps.wiki import views_upload
from apps.wiki.feeds import LatestPagesFeed

app_name = "wiki"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("bookmarks/", views.BookmarksView.as_view(), name="bookmarks"),
    path("links/", views.SharedLinksView.as_view(), name="shared_links"),
    path("links/<slug:slug>/", views.SharedLinkDetailView.as_view(), name="shared_link"),
    path("links/<slug:slug>/preview/", views.SharedLinkPreviewView.as_view(), name="shared_link_preview"),
    path("go/<slug:slug>/", views.SharedLinkRedirectView.as_view(), name="shared_link_go"),
    path("api/link-preview/", views.LinkPreviewAPIView.as_view(), name="link_preview_api"),
    path("offline/", views.OfflineView.as_view(), name="offline"),
    path("category/<slug:slug>/", views.CategoryView.as_view(), name="category"),
    path("wiki/new/", views_create.CreateWikiPageView.as_view(), name="create_page"),
    path("wiki/api/upload/", views_upload.EditorMediaUploadView.as_view(), name="editor_upload"),
    path("wiki/<slug:slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("wiki/<slug:slug>/preview/", views.PagePreviewView.as_view(), name="page_preview"),
    path("wiki/<slug:slug>/bookmark/", views.ToggleBookmarkView.as_view(), name="toggle_bookmark"),
    path("set-language/", views.SetLanguageView.as_view(), name="set_language"),
    path("feeds/latest/", LatestPagesFeed(), name="feed_latest"),
]
