"""Fly health, language, and Varnish cache middleware."""
from django.conf import settings
from django.utils import translation


class FlyHealthMiddleware:
    """Normalize Host header for Fly.io internal health probes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health/":
            host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost"
            if host.startswith("."):
                host = f"wikiwonder{host}"
            request.META["HTTP_HOST"] = host
        return self.get_response(request)


class QueryLanguageMiddleware:
    """Support browser auto-translate via explicit lang + hreflang hints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get("lang") or request.COOKIES.get("wikiwonder_lang")
        if lang and lang in dict(settings.LANGUAGES):
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        if lang and lang in dict(settings.LANGUAGES):
            response.setdefault("Content-Language", lang)
        return response


class PublicPageCacheMiddleware:
    """Set Cache-Control on anonymous GET responses so Varnish can cache wiki pages."""

    CACHEABLE_PREFIXES = ("/wiki/", "/category/", "/links/", "/search/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, "ENABLE_PUBLIC_PAGE_CACHE", True):
            return response
        if request.method not in ("GET", "HEAD"):
            return response
        if getattr(request, "user", None) and request.user.is_authenticated:
            return response
        if response.status_code != 200:
            return response
        if not request.path.startswith(self.CACHEABLE_PREFIXES) and request.path not in {"/", ""}:
            return response
        if "Cache-Control" in response:
            return response
        response["Cache-Control"] = "public, max-age=60, s-maxage=300, stale-while-revalidate=120"
        return response
