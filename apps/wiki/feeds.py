from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from apps.wiki.models import WikiPage


class LatestPagesFeed(Feed):
    title = "WikiWonder — Latest Pages"
    link = "/"
    description = "Recently updated wiki pages"
    feed_type = Atom1Feed

    def items(self):
        return WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED).order_by("-updated_at")[:25]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary or item.content[:300]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.updated_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_author_name(self, item):
        return item.author.get_full_name() if item.author else "WikiWonder"
