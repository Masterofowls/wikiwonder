"""API for image block annotations."""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from apps.media.models import BlockAnnotation, ContentBlock
from apps.wiki.permissions import can_edit_page


class BlockAnnotationCreateView(LoginRequiredMixin, View):
    """POST JSON { label, body, x_percent, y_percent } for image blocks."""

    def post(self, request, block_id):
        block = get_object_or_404(ContentBlock, pk=block_id)
        if not can_edit_page(request.user, block.page):
            return JsonResponse({"error": "Permission denied"}, status=403)
        if block.block_type not in {ContentBlock.BlockType.IMAGE, ContentBlock.BlockType.GIF}:
            return JsonResponse({"error": "Annotations only supported on images"}, status=400)

        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        body = (data.get("body") or "").strip()
        if not body:
            return JsonResponse({"error": "body is required"}, status=400)

        annotation = BlockAnnotation.objects.create(
            block=block,
            author=request.user,
            label=(data.get("label") or "")[:120],
            body=body,
            x_percent=data.get("x_percent"),
            y_percent=data.get("y_percent"),
        )
        return JsonResponse(
            {
                "id": annotation.pk,
                "label": annotation.label,
                "body": annotation.body,
                "x_percent": annotation.x_percent,
                "y_percent": annotation.y_percent,
            }
        )
