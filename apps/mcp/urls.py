from django.urls import path

from apps.mcp.views import MCPView

app_name = "mcp"

urlpatterns = [
    path("", MCPView.as_view(), name="rpc"),
]
