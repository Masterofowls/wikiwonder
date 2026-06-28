"""Quick category/tag API for wiki editors."""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.views import View

from apps.wiki.services.taxonomy import create_category, suggest_tags


class QuickCategoryCreateView(LoginRequiredMixin, View):
    """POST JSON { name, description? } — staff only."""

    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({"error": "Staff only"}, status=403)
        try:
            payload = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        name = (payload.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "name is required"}, status=400)
        description = (payload.get("description") or "").strip()
        category = create_category(name=name, description=description)
        return JsonResponse(
            {
                "id": category.pk,
                "name": category.name,
                "slug": category.slug,
                "url": reverse("wiki:category", kwargs={"slug": category.slug}),
            }
        )


class TagSuggestView(LoginRequiredMixin, View):
    """GET ?q= — tag name autocomplete."""

    def get(self, request):
        query = request.GET.get("q", "")
        limit = min(int(request.GET.get("limit", 12)), 30)
        return JsonResponse({"tags": suggest_tags(query, limit=limit)})
