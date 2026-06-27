"""Share, offline bookmarks, and reading-mode APIs."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from apps.wiki.models import Bookmark, WikiPage


class PageShareAPIView(View):
    """JSON payload for Web Share / copy-link UI."""

    def get(self, request, slug):
        page = WikiPage.objects.filter(slug=slug).first()
        if not page:
            return JsonResponse({"error": "Not found"}, status=404)
        if page.status != WikiPage.Status.PUBLISHED and not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)
        url = request.build_absolute_uri(page.get_absolute_url())
        return JsonResponse({
            "title": page.title,
            "text": page.summary or page.title,
            "url": url,
            "slug": page.slug,
        })


class BookmarkOfflineAPIView(LoginRequiredMixin, View):
    """URLs to prefetch in service worker for offline bookmark reading."""

    def get(self, request):
        bookmarks = Bookmark.objects.filter(user=request.user).select_related("page")
        urls = []
        for bm in bookmarks:
            if bm.page.status == WikiPage.Status.PUBLISHED:
                urls.append(request.build_absolute_uri(bm.page.get_absolute_url()))
        return JsonResponse({"urls": urls, "count": len(urls)})
