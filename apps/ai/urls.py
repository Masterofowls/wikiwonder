from django.urls import path

from apps.ai import views

urlpatterns = [
    path("format/", views.format_text, name="ai_format"),
    path("suggest-title/", views.suggest_title, name="ai_suggest_title"),
]
