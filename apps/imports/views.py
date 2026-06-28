from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.imports.export import export_http_response, export_page, export_pages_queryset
from apps.imports.formats import parse_uploaded_file
from apps.imports.services import import_text_as_wiki_page, preview_import
from apps.imports.sources.fetch import FetchError
from apps.imports.url_import import (
    get_supported_sources,
    import_url_as_wiki_page,
    preview_url_import,
)
from apps.wiki.models import WikiPage
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
    data = WikiPageDetailSerializer(page, context={"request": request}).data
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_file(request):
    """Upload md/txt/json/csv/xlsx/pdf/docx/fb2/html and create a wiki page."""
    uploaded = request.FILES.get("file")
    if not uploaded:
        return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

    parsed = parse_uploaded_file(uploaded)
    title = request.data.get("title", "").strip() or parsed.get("title", "Imported page")
    publish = request.data.get("publish", False)
    use_ai = request.data.get("use_ai", False)

    page = import_text_as_wiki_page(
        parsed.get("markdown", ""),
        title=title,
        author=request.user,
        use_ai=use_ai,
        publish=publish,
    )
    data = WikiPageDetailSerializer(page, context={"request": request}).data
    return Response({
        **data,
        "import_format": parsed.get("format"),
        "import_meta": {k: v for k, v in parsed.items() if k not in {"markdown"}},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def export_page_view(request, slug):
    """Export a page: ?format=md|json|txt|csv"""
    fmt = request.GET.get("format", "md")
    page = WikiPage.objects.filter(slug=slug).first()
    if not page:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user.is_authenticated or page.status == WikiPage.Status.PUBLISHED:
        payload = export_page(page, fmt)
        if request.GET.get("download") == "1":
            return export_http_response(payload)
        return Response(payload)
    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_bulk(request):
    """Export all pages: ?format=json|csv|xlsx"""
    fmt = request.GET.get("format", "json")
    qs = WikiPage.objects.all().order_by("-updated_at")
    payload = export_pages_queryset(qs, fmt)
    if request.GET.get("download") == "1":
        return export_http_response(payload)
    return Response(payload)


@api_view(["GET"])
def supported_sources(request):
    """List supported remote import source types."""
    return Response({"sources": get_supported_sources()})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preview_url(request):
    """Preview import from a remote URL (Wikipedia, RSS, docs, web)."""
    url = request.data.get("url", "").strip()
    source_type = request.data.get("source_type", "auto")
    use_ai = request.data.get("use_ai", False)
    max_entries = int(request.data.get("max_feed_entries", 25))

    if not url:
        return Response({"error": "url is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = preview_url_import(
            url,
            source_type=source_type,
            use_ai=use_ai,
            max_feed_entries=max(1, min(max_entries, 50)),
        )
    except FetchError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_url_view(request):
    """Fetch a remote URL and create a wiki page."""
    url = request.data.get("url", "").strip()
    title = request.data.get("title", "").strip()
    source_type = request.data.get("source_type", "auto")
    use_ai = request.data.get("use_ai", False)
    publish = request.data.get("publish", False)
    max_entries = int(request.data.get("max_feed_entries", 25))

    if not url:
        return Response({"error": "url is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        page = import_url_as_wiki_page(
            url,
            title=title,
            author=request.user,
            source_type=source_type,
            use_ai=use_ai,
            publish=publish,
            max_feed_entries=max(1, min(max_entries, 50)),
        )
    except FetchError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    data = WikiPageDetailSerializer(page, context={"request": request}).data
    return Response(data, status=status.HTTP_201_CREATED)
