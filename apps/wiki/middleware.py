"""Activate language from ?lang= query or wikiwonder_lang cookie."""
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
