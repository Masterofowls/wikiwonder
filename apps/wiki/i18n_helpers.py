"""hreflang and browser translation helpers."""
from django.conf import settings
from django.utils.translation import get_language


def hreflang_links(request, canonical_path: str) -> list[dict]:
    """Build alternate language links for Chrome/Safari/Firefox translate."""
    base = settings.SITE_URL.rstrip("/")
    path = canonical_path if canonical_path.startswith("/") else f"/{canonical_path}"
    links = []
    for code, _name in settings.LANGUAGES:
        # Wiki routes are not prefixed yet; hreflang uses query ?lang= for now
        href = f"{base}{path}?lang={code}"
        links.append({"code": code, "href": href})
    links.append({"code": "x-default", "href": f"{base}{path}"})
    return links


def active_language() -> str:
    return get_language() or settings.LANGUAGE_CODE
