"""Export wiki pages as downloadable files."""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from apps.imports.export import export_page
from apps.wiki.models import WikiPage
from apps.wiki.services.markdown import render_markdown


class PageExportView(View):
    """GET /wiki/<slug>/export/?format=md|html|txt"""

    def get(self, request, slug):
        page = get_object_or_404(
            WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED)
            if not request.user.is_staff
            else WikiPage.objects.all(),
            slug=slug,
        )
        fmt = (request.GET.get("format") or "md").lower()

        if fmt == "html":
            body = render_markdown(page.content)
            html = (
                f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
                f"<title>{page.title}</title>"
                f"<style>body{{font-family:system-ui;max-width:65ch;margin:2rem auto;padding:0 1rem;line-height:1.6}}"
                f"h1,h2,h3{{font-family:Georgia,serif}} img,video{{max-width:100%}}</style>"
                f"</head><body><h1>{page.title}</h1>{body}</body></html>"
            )
            resp = HttpResponse(html, content_type="text/html; charset=utf-8")
            resp["Content-Disposition"] = f'attachment; filename="{page.slug}.html"'
            return resp

        payload = export_page(page, fmt)
        if isinstance(payload, dict) and payload.get("error"):
            return HttpResponse(payload["error"], status=400)

        content_type = "text/markdown" if fmt == "md" else "text/plain; charset=utf-8"
        resp = HttpResponse(payload.get("content", ""), content_type=content_type)
        resp["Content-Disposition"] = f'attachment; filename="{payload.get("filename", page.slug)}"'
        return resp
