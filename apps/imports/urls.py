from django.urls import path

from apps.imports import views

urlpatterns = [
    path("preview/", views.preview, name="import_preview"),
    path("create/", views.create_page, name="import_create"),
    path("file/", views.import_file, name="import_file"),
    path("export/", views.export_bulk, name="export_bulk"),
    path("export/<slug:slug>/", views.export_page_view, name="export_page"),
]
