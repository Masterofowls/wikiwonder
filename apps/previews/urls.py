from django.urls import path

from apps.previews.views import BlockPreviewAPIView, PreviewAPIView

app_name = "previews"

urlpatterns = [
    path("", PreviewAPIView.as_view(), name="preview"),
    path("blocks/<int:pk>/", BlockPreviewAPIView.as_view(), name="block"),
]
