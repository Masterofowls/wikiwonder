from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import DetailView, ListView, TemplateView, View

from apps.previews.services import preview_from_block
from apps.search.services import wiki_page_queryset
from apps.seo.services import home_seo, wiki_page_seo
from apps.wiki.i18n_helpers import hreflang_links
from apps.wiki.models import Bookmark, Category, SharedLink, WikiPage
from apps.wiki.services.link_preview import fetch_link_preview
from apps.wiki.services.markdown import render_markdown


class HomeView(ListView):
    model = WikiPage
    template_name = "wiki/home.html"
    context_object_name = "pages"
    paginate_by = 12

    def get_queryset(self):
        return (
            WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
            .select_related("category", "author")
            .prefetch_related("tags")
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        published = WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
        agg = published.aggregate(pages=Count("id"), views=Sum("view_count"))
        ctx["featured"] = published.filter(is_featured=True).select_related("category")[:8]
        ctx["trending"] = published.order_by("-view_count").select_related("category")[:8]
        ctx["categories"] = Category.objects.filter(parent__isnull=True).prefetch_related("children")
        ctx["category_spotlights"] = [
            {
                "category": cat,
                "pages": WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED, category=cat)
                .select_related("category")[:4],
            }
            for cat in Category.objects.filter(parent__isnull=True).order_by("name")[:6]
            if cat.pages.filter(status=WikiPage.Status.PUBLISHED).exists()
        ]
        ctx["shared_links"] = SharedLink.objects.filter(is_featured=True)[:12]
        ctx["all_shared_links"] = SharedLink.objects.all()[:20]
        ctx["stats"] = {
            "pages": agg["pages"] or 0,
            "categories": Category.objects.count(),
            "links": SharedLink.objects.count(),
            "views": agg["views"] or 0,
        }
        ctx["seo"] = home_seo()
        query = self.request.GET.get("q", "").strip()
        ctx["search_query"] = query
        ctx["search_results"] = []
        ctx["search_total"] = 0
        ctx["search_has_more"] = False
        if len(query) >= 2:
            from apps.search.services import home_search

            search_data = home_search(query, limit=12)
            ctx["search_results"] = search_data["results"]
            ctx["search_total"] = search_data["total"]
            ctx["search_has_more"] = search_data["has_more"]
        return ctx


class PageDetailView(DetailView):
    model = WikiPage
    template_name = "wiki/page_detail.html"
    context_object_name = "page"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = WikiPage.objects.select_related("category", "author").prefetch_related(
            "sections", "tags", "content_blocks__annotations"
        )
        if not self.request.user.is_staff:
            qs = qs.filter(status=WikiPage.Status.PUBLISHED)
        return qs

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        WikiPage.objects.filter(pk=self.object.pk).update(view_count=F("view_count") + 1)
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sections = list(self.object.sections.all())
        ctx["sections"] = sections
        if sections:
            ctx["rendered_sections"] = [
                (section, render_markdown(section.content, page_slug=self.object.slug))
                for section in sections
            ]
            ctx["rendered_content"] = ""
        else:
            ctx["rendered_sections"] = []
            ctx["rendered_content"] = render_markdown(self.object.content, page_slug=self.object.slug)
        ctx["shared_links"] = self.object.shared_links.all()[:6]
        ctx["related_pages"] = (
            WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED, category=self.object.category)
            .exclude(pk=self.object.pk)
            .select_related("category")[:4]
            if self.object.category
            else WikiPage.objects.none()
        )
        ctx["is_bookmarked"] = False
        if self.request.user.is_authenticated:
            ctx["is_bookmarked"] = Bookmark.objects.filter(
                user=self.request.user, page=self.object
            ).exists()
        ctx["seo"] = wiki_page_seo(self.object)
        ctx["content_blocks"] = [
            preview_from_block(b) for b in self.object.content_blocks.all()
        ]
        ctx["hreflang_links"] = hreflang_links(self.request, self.object.get_absolute_url())
        ctx["share_api_url"] = reverse("page_share", kwargs={"slug": self.object.slug})
        ctx["django_meta"] = self.object.as_meta(request=self.request)
        from apps.ai.quota import quota_status
        from apps.ai.services import get_ai_service

        ai = get_ai_service()
        ctx["ai_configured"] = ai.is_configured
        ctx["ai_quota"] = quota_status(self.request.user) if self.request.user.is_authenticated else None
        from apps.wiki.permissions import can_edit_page

        ctx["can_edit"] = can_edit_page(self.request.user, self.object)
        ctx["can_annotate"] = ctx["can_edit"]
        from apps.wiki.services.lara_translate import get_lara_service

        lara = get_lara_service()
        ctx["lara_configured"] = lara.is_configured
        ctx["has_ru_translation"] = bool(getattr(self.object, "title_ru", None))
        from apps.wiki.services.markdown import is_media_metadata, sanitize_summary_text

        summary = self.object.summary or ""
        if is_media_metadata(summary):
            summary = sanitize_summary_text(summary)
        ctx["page_summary"] = summary if summary and not is_media_metadata(summary) else ""
        from apps.wiki.services.link_graph import get_backlinks

        ctx["backlinks"] = get_backlinks(self.object.slug)
        if self.request.user.is_staff:
            from apps.wiki.services.broken_links import audit_page_links

            ctx["link_audit"] = audit_page_links(self.object)
        return ctx


class SetLanguageView(View):
    """Persist UI language for modeltranslation + browser translate hints."""

    def post(self, request):
        lang = request.POST.get("language", "")
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
        if lang in dict(settings.LANGUAGES):
            if not url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                next_url = "/"
            translation.activate(lang)
            response = redirect(next_url)
            response.set_cookie(
                "wikiwonder_lang", lang, max_age=365 * 24 * 3600, samesite="Lax"
            )
            return response
        return redirect(next_url)


class PagePreviewView(DetailView):
    """Lightweight preview for cards and hover popovers."""

    model = WikiPage
    template_name = "wiki/page_preview.html"
    context_object_name = "page"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)


class CategoryView(ListView):
    model = WikiPage
    template_name = "wiki/category.html"
    context_object_name = "pages"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            WikiPage.objects.filter(category=self.category, status=WikiPage.Status.PUBLISHED)
            .select_related("author")
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = self.category
        return ctx


class SearchView(ListView):
    model = WikiPage
    template_name = "wiki/search.html"
    context_object_name = "pages"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        return wiki_page_queryset(q)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        ctx["query"] = query
        if len(query) >= 2:
            from apps.search.services import full_search_bundle

            bundle = full_search_bundle(query)
            ctx["search_categories"] = bundle["categories"]
            ctx["search_tags"] = bundle["tags"]
            ctx["search_links"] = bundle["links"]
            ctx["search_total"] = bundle["total"]
        else:
            ctx["search_categories"] = []
            ctx["search_tags"] = []
            ctx["search_links"] = []
            ctx["search_total"] = 0
        return ctx


class BookmarksView(LoginRequiredMixin, ListView):
    model = Bookmark
    template_name = "wiki/bookmarks.html"
    context_object_name = "bookmarks"
    paginate_by = 20

    def get_queryset(self):
        return (
            Bookmark.objects.filter(user=self.request.user)
            .select_related("page", "page__category")
            .order_by("-created_at")
        )


class ToggleBookmarkView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": "Authentication required"}, status=401)
            return redirect("account_login")
        page = get_object_or_404(WikiPage, slug=slug, status=WikiPage.Status.PUBLISHED)
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, page=page)
        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"bookmarked": bookmarked, "slug": slug, "title": page.title})
        return redirect(page.get_absolute_url())


class OfflineView(TemplateView):
    template_name = "wiki/offline.html"


class SharedLinksView(ListView):
    model = SharedLink
    template_name = "wiki/shared_links.html"
    context_object_name = "links"
    paginate_by = 24

    def get_queryset(self):
        return SharedLink.objects.select_related("page", "created_by").order_by("-created_at")


class SharedLinkDetailView(DetailView):
    model = SharedLink
    template_name = "wiki/shared_link_detail.html"
    context_object_name = "link"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        SharedLink.objects.filter(pk=self.object.pk).update(click_count=F("click_count") + 1)
        return response


class SharedLinkRedirectView(DetailView):
    """Direct redirect to external URL (for /go/<slug>/)."""

    model = SharedLink
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get(self, request, *args, **kwargs):
        link = self.get_object()
        SharedLink.objects.filter(pk=link.pk).update(click_count=F("click_count") + 1)
        return redirect(link.url)


class LinkPreviewAPIView(View):
    """JSON endpoint for live link preview cards."""

    def get(self, request):
        url = request.GET.get("url", "").strip()
        if not url:
            return JsonResponse({"error": "url required"}, status=400)
        try:
            return JsonResponse(fetch_link_preview(url))
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=502)


class LocalWikiPageAPIView(View):
    """Resolve a Wikipedia URL to a local wiki page if one exists."""

    def get(self, request):
        from urllib.parse import unquote

        from apps.wiki.services.wikilinks import (
            WIKIPEDIA_ARTICLE_URL,
            normalize_wiki_title,
            resolve_wiki_slug,
        )

        url = request.GET.get("url", "").strip()
        if not url:
            return JsonResponse({"error": "url required"}, status=400)
        match = WIKIPEDIA_ARTICLE_URL.match(url)
        if not match:
            return JsonResponse({"local": False})
        title = normalize_wiki_title(unquote(match.group(2)))
        slug = resolve_wiki_slug(title)
        if not slug:
            return JsonResponse({"local": False, "title": title})
        page = WikiPage.objects.filter(slug=slug, status=WikiPage.Status.PUBLISHED).first()
        if not page:
            return JsonResponse({"local": False, "title": title})
        return JsonResponse(
            {
                "local": True,
                "slug": page.slug,
                "title": page.title,
                "url": page.get_absolute_url(),
            }
        )


class PageLinkAuditView(LoginRequiredMixin, View):
    """Staff-only JSON link audit for a wiki page."""

    def get(self, request, slug):
        if not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)
        page = get_object_or_404(WikiPage, slug=slug)
        from apps.wiki.services.broken_links import audit_page_links

        return JsonResponse(audit_page_links(page))


class SharedLinkPreviewView(DetailView):
    model = SharedLink
    template_name = "wiki/partials/link_preview_card.html"
    context_object_name = "link"
    slug_field = "slug"
    slug_url_kwarg = "slug"
