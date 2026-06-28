from django.http import JsonResponse
from django.views import View

from apps.search.services import instant_search


class InstantSearchAPIView(View):
    """JSON endpoint for header typeahead and live search."""

    def get(self, request):
        query = request.GET.get("q", "").strip()
        limit = min(int(request.GET.get("limit", 8)), 20)
        payload = instant_search(query, limit=limit)
        return JsonResponse({"query": query, **payload})
