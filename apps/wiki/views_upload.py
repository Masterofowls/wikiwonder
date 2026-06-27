"""Editor media uploads (images, video, audio) before page is saved."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from apps.media.services import markdown_snippet_for_upload, save_editor_upload

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
