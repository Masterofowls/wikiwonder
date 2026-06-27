from django.contrib.sitemaps import Sitemap

from apps.wiki.models import Category, SharedLink, WikiPage


class WikiCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.filter(pages__status=WikiPage.Status.PUBLISHED).distinct()

    def location(self, obj):
        return f"/category/{obj.slug}/"


class SharedLinkSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return SharedLink.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at
