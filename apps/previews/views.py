from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from apps.media.models import ContentBlock
from apps.previews.services import build_preview, detect_type, preview_from_block


class PreviewAPIView(View):
    """GET /api/preview/?url=&type=&content="""

    def get(self, request):
        url = request.GET.get("url", "").strip()
        content = request.GET.get("content", "")
        block_type = request.GET.get("type", "")
        title = request.GET.get("title", "")
        description = request.GET.get("description", "")
        language = request.GET.get("language", "")

        if not url and not content and not block_type:
            return JsonResponse({"error": "url, content, or type required"}, status=400)

        result = build_preview(
            url=url,
            content=content,
            block_type=block_type,
            title=title,
            description=description,
            language=language,
        )
        result["detected_type"] = detect_type(url=url, hint=block_type)
        return JsonResponse(result)


class BlockPreviewAPIView(View):
    """GET /api/preview/blocks/<id>/"""

    def get(self, request, pk):
        block = get_object_or_404(ContentBlock.objects.prefetch_related("annotations"), pk=pk)
        return JsonResponse(preview_from_block(block))
