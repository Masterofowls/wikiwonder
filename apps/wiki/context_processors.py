from django.conf import settings
from django.utils.translation import get_language


def site_context(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
    }


def i18n_context(request):
    """Language list, hreflang hints, cookie consent flag."""
    from apps.wiki.i18n_helpers import active_language

    lang = active_language()
    consent = request.COOKIES.get("wikiwonder_cookie_consent")
    return {
        "CURRENT_LANGUAGE": lang,
        "AVAILABLE_LANGUAGES": settings.LANGUAGES,
        "COOKIE_CONSENT": consent == "accepted",
        "SHOW_COOKIE_BANNER": consent is None,
        "BROWSER_TRANSLATE_HINT": True,
    }
