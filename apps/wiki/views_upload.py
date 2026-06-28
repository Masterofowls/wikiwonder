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


class WikipediaUrlImportView(LoginRequiredMixin, View):
    """POST JSON { url, download_media? } → formatted wiki markdown from Wikipedia."""

    def post(self, request):
        try:
            payload = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        url = (payload.get("url") or "").strip()
        download_media = bool(payload.get("download_media"))
        if not url:
            return JsonResponse({"error": "url is required"}, status=400)

        from apps.imports.sources.detect import wikipedia_page_title
        from apps.imports.sources.fetch import FetchError
        from apps.imports.url_import import preview_url_import

        if not wikipedia_page_title(url):
            return JsonResponse({"error": "Not a valid Wikipedia article URL"}, status=400)

        try:
            preview = preview_url_import(
                url,
                source_type="wikipedia",
                download_media=download_media,
                user=request.user,
            )
        except FetchError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        return JsonResponse(
            {
                "title": preview["title"],
                "markdown": preview["markdown"],
                "summary": preview.get("summary", ""),
                "section_count": preview.get("section_count", 0),
                "media_count": preview.get("meta", {}).get("media_count", 0),
                "citation_count": preview.get("meta", {}).get("citation_count", 0),
                "category_count": len(preview.get("meta", {}).get("categories") or []),
                "source_url": preview["source_url"],
                "meta": preview.get("meta", {}),
            }
        )


class WikipediaBulkImportView(LoginRequiredMixin, View):
    """POST JSON { urls?, category_url?, download_media?, publish? } → bulk import results."""

    def post(self, request):
        try:
            payload = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        urls = [u.strip() for u in (payload.get("urls") or []) if u and u.strip()]
        category_url = (payload.get("category_url") or "").strip()
        download_media = bool(payload.get("download_media"))
        publish = bool(payload.get("publish"))

        from apps.imports.sources.detect import wikipedia_page_title
        from apps.imports.sources.wikipedia_categories import (
            fetch_wikipedia_category_articles,
            wikipedia_article_urls,
        )
        from apps.imports.url_import import bulk_import_wikipedia

        if category_url:
            parsed = wikipedia_page_title(category_url)
            if not parsed:
                return JsonResponse({"error": "Not a valid Wikipedia category URL"}, status=400)
            lang, cat_title = parsed
            titles = fetch_wikipedia_category_articles(lang, cat_title, limit=25)
            urls.extend(wikipedia_article_urls(lang, titles))

        if not urls:
            return JsonResponse({"error": "Provide urls or category_url"}, status=400)
        if len(urls) > 30:
            return JsonResponse({"error": "Maximum 30 URLs per bulk import"}, status=400)

        results = bulk_import_wikipedia(
            urls,
            author=request.user,
            download_media=download_media,
            publish=publish,
        )
        ok_count = sum(1 for r in results if r.get("ok"))
        return JsonResponse({"results": results, "imported": ok_count, "total": len(results)})
