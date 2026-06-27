from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.imports.services import import_text_as_wiki_page, preview_import
from apps.wiki.serializers import WikiPageDetailSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preview(request):
    """Preview text import without creating a page."""
    raw_text = request.data.get("text", "").strip()
    title = request.data.get("title", "").strip()
    use_ai = request.data.get("use_ai", True)

    if not raw_text:
        return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

    result = preview_import(raw_text, title=title, use_ai=use_ai)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_page(request):
    """Import text and create a wiki page with sections."""
    raw_text = request.data.get("text", "").strip()
    title = request.data.get("title", "").strip()
    use_ai = request.data.get("use_ai", True)
    publish = request.data.get("publish", False)

    if not raw_text:
        return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

    page = import_text_as_wiki_page(
        raw_text,
        title=title,
        author=request.user,
        use_ai=use_ai,
        publish=publish,
    )
    serializer = WikiPageDetailSerializer(page)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
