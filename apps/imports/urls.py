from django.urls import path

from apps.imports import views

urlpatterns = [
    path("preview/", views.preview, name="import_preview"),
    path("create/", views.create_page, name="import_create"),
]
