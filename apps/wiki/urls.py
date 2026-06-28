from django.urls import path

from apps.wiki import (
    views,
    views_annotations,
    views_create,
    views_edit,
    views_export,
    views_import,
    views_suggest,
    views_translate,
    views_upload,
)
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
    path("wiki/import/", views_import.ImportFromUrlView.as_view(), name="import_url"),
    path("wiki/api/upload/", views_upload.EditorMediaUploadView.as_view(), name="editor_upload"),
    path("wiki/api/paste-wikipedia/", views_upload.WikipediaPasteView.as_view(), name="paste_wikipedia"),
    path("wiki/api/blocks/<int:block_id>/annotate/", views_annotations.BlockAnnotationCreateView.as_view(), name="block_annotate"),
    path("wiki/<slug:slug>/edit/", views_edit.EditWikiPageView.as_view(), name="edit_page"),
    path("wiki/<slug:slug>/translate/", views_translate.GenerateTranslationView.as_view(), name="generate_translation"),
    path("wiki/<slug:slug>/export/", views_export.PageExportView.as_view(), name="page_export"),
    path("wiki/<slug:slug>/suggest/", views_suggest.SuggestEditView.as_view(), name="suggest_edit"),
    path("wiki/suggestions/<int:pk>/approve/", views_suggest.ApproveSuggestionView.as_view(), name="approve_suggestion"),
    path("wiki/<slug:slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("wiki/<slug:slug>/preview/", views.PagePreviewView.as_view(), name="page_preview"),
    path("wiki/<slug:slug>/bookmark/", views.ToggleBookmarkView.as_view(), name="toggle_bookmark"),
    path("set-language/", views.SetLanguageView.as_view(), name="set_language"),
    path("feeds/latest/", LatestPagesFeed(), name="feed_latest"),
]
