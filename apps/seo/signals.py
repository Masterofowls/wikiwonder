"""Keep django-check-seo Page/Keyword rows in sync with public wiki URLs."""
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from apps.wiki.models import WikiPage


def _sync_wiki_page_seo(page: WikiPage) -> None:
    from django_check_seo.models import Keyword
    from django_check_seo.models import Page as SeoPage

    path = page.get_absolute_url()
    seo_page, _ = SeoPage.objects.get_or_create(path=path)
    seo_page.keywords.clear()
    from apps.seo.services import page_keywords

    for name in page_keywords(page):
        keyword, _ = Keyword.objects.get_or_create(name=name)
        seo_page.keywords.add(keyword)


def _sync_home_seo() -> None:
    from django_check_seo.models import Keyword
    from django_check_seo.models import Page as SeoPage

    from apps.seo.services import _site_keywords

    seo_page, _ = SeoPage.objects.get_or_create(path="/")
    seo_page.keywords.clear()
    for name in _site_keywords():
        keyword, _ = Keyword.objects.get_or_create(name=name)
        seo_page.keywords.add(keyword)


@receiver(post_save, sender=WikiPage)
def sync_wikipage_seo_keywords(sender, instance, **kwargs):
    if instance.status == WikiPage.Status.PUBLISHED:
        _sync_wiki_page_seo(instance)


@receiver(m2m_changed, sender=WikiPage.tags.through)
def sync_wikipage_tags_seo(sender, instance, action, **kwargs):
    if action.startswith("post_") and instance.status == WikiPage.Status.PUBLISHED:
        _sync_wiki_page_seo(instance)


def ensure_site_seo_keywords(**kwargs):
    _sync_home_seo()
