from django.urls import path

from apps.search.views import InstantSearchAPIView

app_name = "search"

urlpatterns = [
    path("", InstantSearchAPIView.as_view(), name="instant"),
]
