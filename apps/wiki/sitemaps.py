from django.contrib.sitemaps import Sitemap

from apps.wiki.models import WikiPage


class WikiPageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at
