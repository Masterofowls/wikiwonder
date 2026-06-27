"""WikiWonder URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.wiki.sitemaps import WikiPageSitemap
from config.health import HealthView

sitemaps = {"pages": WikiPageSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("health/", HealthView.as_view(), name="health"),
    path("markdownx/", include("markdownx.urls")),
    path("", include("pwa.urls")),
    path("", include("apps.wiki.urls")),
    path("api/", include("apps.wiki.api_urls")),
    path("api/search/", include("apps.search.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/import/", include("apps.imports.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # CMS pages — must remain last (catch-all routing)
    path("", include("cms.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "WikiWonder Admin"
admin.site.site_title = "WikiWonder"
admin.site.index_title = "Content Management"
