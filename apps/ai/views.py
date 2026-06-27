from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ai.services import get_ai_service


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def format_text(request):
    """Convert raw text to markdown using Cerebras AI."""
    raw_text = request.data.get("text", "").strip()
    title = request.data.get("title", "").strip()

    if not raw_text:
        return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

    service = get_ai_service()
    if not service.is_configured:
        return Response(
            {"error": "Cerebras API key not configured. Set CEREBRAS_API_KEY in environment."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        markdown = service.format_to_markdown(raw_text, title=title)
        suggested_title = title or service.suggest_title(raw_text)
        summary = service.generate_summary(markdown)
        return Response({
            "title": suggested_title,
            "markdown": markdown,
            "summary": summary,
        })
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def suggest_title(request):
    raw_text = request.data.get("text", "").strip()
    if not raw_text:
        return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

    service = get_ai_service()
    if not service.is_configured:
        return Response({"error": "AI not configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        title = service.suggest_title(raw_text)
        return Response({"title": title})
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
