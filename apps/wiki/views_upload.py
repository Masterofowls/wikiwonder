"""Editor helpers: media upload and Wikipedia paste normalization."""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from apps.media.services import markdown_snippet_for_upload, save_editor_upload
from apps.wiki.services.wikipedia_paste import is_wikipedia_paste, normalize_wikipedia_paste

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class EditorMediaUploadView(LoginRequiredMixin, View):
    """POST multipart file → { url, type, markdown } for inline editor embedding."""

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return JsonResponse({"error": "file is required"}, status=400)
        if upload.size > MAX_UPLOAD_BYTES:
            return JsonResponse({"error": "File too large (max 10 MB)"}, status=400)

        try:
            saved = save_editor_upload(upload, user=request.user)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        return JsonResponse(
            {
                "url": saved["url"],
                "type": saved["type"],
                "markdown": markdown_snippet_for_upload(saved["url"], upload.name, saved["type"]),
                "filename": upload.name,
            }
        )


class WikipediaPasteView(LoginRequiredMixin, View):
    """POST JSON { text, source_url? } → formatted wiki markdown with citations."""

    def post(self, request):
        try:
            payload = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        text = (payload.get("text") or "").strip()
        source_url = (payload.get("source_url") or "").strip()
        if not text:
            return JsonResponse({"error": "text is required"}, status=400)
        if len(text) > 500_000:
            return JsonResponse({"error": "Text too large"}, status=400)

        if not is_wikipedia_paste(text) and not source_url:
            return JsonResponse(
                {"error": "Text does not look like a Wikipedia paste. Add a source URL or paste article content."},
                status=400,
            )

        result = normalize_wikipedia_paste(text, source_url=source_url)
        return JsonResponse(result)
