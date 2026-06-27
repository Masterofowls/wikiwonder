"""Serve uploaded media in production (django.conf.urls.static is DEBUG-only)."""
from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.urls import re_path
from django.views.static import serve


def serve_media(request, path):
    """Serve files from MEDIA_ROOT; normalize trailing slashes from CMS redirects."""
    clean_path = path.rstrip("/")
    if not clean_path:
        raise Http404("Empty media path")

    if request.path.endswith("/") and not path.endswith("//"):
        canonical = request.path.rstrip("/")
        return HttpResponsePermanentRedirect(canonical)

    response = serve(request, clean_path, document_root=settings.MEDIA_ROOT)
    if response.status_code == 200 and "Cache-Control" not in response:
        response["Cache-Control"] = "public, max-age=86400, immutable"
    return response


def get_media_urlpatterns():
    if not (settings.DEBUG or getattr(settings, "SERVE_MEDIA", False)):
        return []
    prefix = settings.MEDIA_URL.lstrip("/")
    return [
        re_path(rf"^{prefix}(?P<path>.*)$", serve_media, name="media"),
    ]
