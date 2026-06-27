from django.urls import path

from apps.ai import views

urlpatterns = [
    path("status/", views.ai_status, name="ai_status"),
    path("quota/", views.ai_quota, name="ai_quota"),
    path("format/", views.format_text, name="ai_format"),
    path("admin/assist/", views.admin_assist, name="ai_admin_assist"),
    path("page/summarize/", views.page_summarize, name="ai_page_summarize"),
    path("page/ask/", views.page_ask, name="ai_page_ask"),
    path("suggest-title/", views.suggest_title, name="ai_suggest_title"),
    path("chat/", views.chat, name="ai_chat"),
    path("chat/stream/", views.chat_stream, name="ai_chat_stream"),
]
