"""WikiWonder URL configuration."""
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.seo.sitemaps import SharedLinkSitemap, WikiCategorySitemap
from apps.seo.views import RobotsTxtView
from apps.wiki.sitemaps import WikiPageSitemap
from config.health import HealthView
from config.media_urls import get_media_urlpatterns

sitemaps = {
    "pages": WikiPageSitemap,
    "categories": WikiCategorySitemap,
    "links": SharedLinkSitemap,
}

# Must precede CMS catch-all — otherwise django CMS treats /media/... as page slugs (301/404).
media_urlpatterns = get_media_urlpatterns()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("health/", HealthView.as_view(), name="health"),
    path("robots.txt", RobotsTxtView.as_view(), name="robots"),
    *media_urlpatterns,
    path("markdownx/", include("markdownx.urls")),
    path("", include("pwa.urls")),
    path("", include("apps.wiki.urls")),
    path("api/", include("apps.wiki.api_urls")),
    path("api/search/", include("apps.search.urls")),
    path("api/preview/", include("apps.previews.urls")),
    path("api/mcp/", include("apps.mcp.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/import/", include("apps.imports.urls")),
    path("django-check-seo/", include("django_check_seo.urls")),
    path("rosetta/", include("rosetta.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # CMS pages — must remain last (catch-all routing)
    path("", include("cms.urls")),
]

admin.site.site_header = "WikiWonder Admin"
admin.site.site_title = "WikiWonder"
admin.site.index_title = "Content Management"
