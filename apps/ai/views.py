"""Cerebras AI API endpoints."""
import json
import logging

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ai.page_context import page_markdown_text
from apps.ai.quota import QuotaExceededError, consume_quota, quota_status
from apps.ai.services import get_ai_service
from apps.wiki.models import WikiPage

logger = logging.getLogger(__name__)


def _service_or_error():
    service = get_ai_service()
    if not service.is_configured:
        return None, Response(
            {
                "error": "Cerebras API key not configured. Set CEREBRAS_API_KEY in environment.",
                "configured": False,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return service, None


def _parse_messages(data) -> list[dict[str, str]] | None:
    messages = data.get("messages")
    if messages and isinstance(messages, list):
        cleaned = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role in {"system", "user", "assistant"} and content is not None:
                cleaned.append({"role": role, "content": str(content)})
        if cleaned:
            return cleaned
    content = (data.get("content") or data.get("text") or "").strip()
    if content:
        system = (data.get("system") or "").strip()
        out = []
        if system:
            out.append({"role": "system", "content": system})
        out.append({"role": "user", "content": content})
        return out
    return None


def _get_page_for_ai(slug: str, user) -> WikiPage | None:
    qs = WikiPage.objects.select_related("author").prefetch_related("sections")
    if user.is_staff:
        return qs.filter(slug=slug).first()
    return qs.filter(slug=slug, status=WikiPage.Status.PUBLISHED).first()


@api_view(["GET"])
def ai_status(request):
    """Report whether Cerebras is configured (no key exposure)."""
    service = get_ai_service()
    payload = {
        "configured": service.is_configured,
        "model": service.model if service.is_configured else None,
    }
    if request.user.is_authenticated:
        payload["quota"] = quota_status(request.user)
    return Response(payload)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_quota(request):
    return Response({"quota": quota_status(request.user)})


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def format_text(request):
    """Convert raw text to markdown using Cerebras AI."""
    raw_text = request.data.get("text", "").strip()
    title = request.data.get("title", "").strip()

    if not raw_text:
        return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

    service, err = _service_or_error()
    if err:
        return err

    try:
        result = service.enrich_import(raw_text, title=title)
        return Response({**result, "model": service.model})
    except Exception as exc:
        logger.exception("Cerebras format failed")
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def admin_assist(request):
    """Staff-only AI helper for admin/CMS editing (no daily quota)."""
    if not request.user.is_staff:
        return Response({"error": "Staff access required"}, status=status.HTTP_403_FORBIDDEN)

    action = (request.data.get("action") or "format").strip().lower()
    raw_text = (request.data.get("text") or request.data.get("content") or "").strip()
    title = (request.data.get("title") or "").strip()

    if not raw_text:
        return Response({"error": "text or content is required"}, status=status.HTTP_400_BAD_REQUEST)

    service, err = _service_or_error()
    if err:
        return err

    try:
        if action == "summary":
            summary = service.generate_summary(raw_text)
            return Response({"summary": summary, "model": service.model})
        if action == "title":
            suggested = service.suggest_title(raw_text)
            return Response({"title": suggested, "model": service.model})
        if action == "format":
            result = service.enrich_import(raw_text, title=title)
            return Response({**result, "model": service.model})
        return Response({"error": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        logger.exception("Cerebras admin assist failed")
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def page_summarize(request):
    """Summarize a wiki page (counts toward daily viewer quota)."""
    slug = (request.data.get("slug") or "").strip()
    if not slug:
        return Response({"error": "slug is required"}, status=status.HTTP_400_BAD_REQUEST)

    page = _get_page_for_ai(slug, request.user)
    if not page:
        return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

    service, err = _service_or_error()
    if err:
        return err

    try:
        with transaction.atomic():
            consume_quota(request.user)
            content = page_markdown_text(page)
            summary = service.summarize_wiki_page(page.title, content)
        return Response(
            {
                "summary": summary,
                "title": page.title,
                "slug": page.slug,
                "model": service.model,
                "quota": quota_status(request.user),
            }
        )
    except QuotaExceededError as exc:
        return Response(
            {
                "error": str(exc),
                "quota": quota_status(request.user),
                "remaining": exc.remaining,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    except Exception as exc:
        logger.exception("Page summarize failed")
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def page_ask(request):
    """Ask a question about wiki page content (counts toward daily viewer quota)."""
    slug = (request.data.get("slug") or "").strip()
    question = (request.data.get("question") or "").strip()
    if not slug:
        return Response({"error": "slug is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not question:
        return Response({"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST)

    page = _get_page_for_ai(slug, request.user)
    if not page:
        return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

    service, err = _service_or_error()
    if err:
        return err

    try:
        with transaction.atomic():
            consume_quota(request.user)
            content = page_markdown_text(page)
            answer = service.ask_about_wiki_page(page.title, content, question)
        return Response(
            {
                "answer": answer,
                "question": question,
                "title": page.title,
                "slug": page.slug,
                "model": service.model,
                "quota": quota_status(request.user),
            }
        )
    except QuotaExceededError as exc:
        return Response(
            {
                "error": str(exc),
                "quota": quota_status(request.user),
                "remaining": exc.remaining,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    except Exception as exc:
        logger.exception("Page ask failed")
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def suggest_title(request):
    raw_text = request.data.get("text", "").strip()
    if not raw_text:
        return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

    service, err = _service_or_error()
    if err:
        return err

    try:
        title = service.suggest_title(raw_text)
        return Response({"title": title, "model": service.model})
    except Exception as exc:
        logger.exception("Cerebras title suggestion failed")
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def chat(request):
    """General Cerebras chat completion (non-streaming)."""
    messages = _parse_messages(request.data)
    if not messages:
        return Response({"error": "messages or content is required"}, status=status.HTTP_400_BAD_REQUEST)

    service, err = _service_or_error()
    if err:
        return err

    try:
        content = service.chat(
            messages,
            max_completion_tokens=request.data.get("max_completion_tokens"),
            temperature=request.data.get("temperature"),
            top_p=request.data.get("top_p"),
            reasoning_effort=request.data.get("reasoning_effort"),
        )
        return Response({"content": content, "model": service.model})
    except Exception as exc:
        logger.exception("Cerebras chat failed")
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def chat_stream(request):
    """Streaming Cerebras chat completion (Server-Sent Events)."""
    messages = _parse_messages(request.data)
    if not messages:
        return Response({"error": "messages or content is required"}, status=status.HTTP_400_BAD_REQUEST)

    service, err = _service_or_error()
    if err:
        return err

    def event_stream():
        try:
            for delta in service.chat_stream(
                messages,
                max_completion_tokens=request.data.get("max_completion_tokens"),
                temperature=request.data.get("temperature"),
                top_p=request.data.get("top_p"),
                reasoning_effort=request.data.get("reasoning_effort"),
            ):
                yield f"data: {json.dumps({'content': delta})}\n\n"
            yield f"data: {json.dumps({'done': True, 'model': service.model})}\n\n"
        except Exception as exc:
            logger.exception("Cerebras stream failed")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
