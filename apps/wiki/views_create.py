"""Authenticated wiki page creation with markdown paste and media uploads."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.imports.formats import parse_uploaded_file
from apps.imports.services import import_text_as_wiki_page
from apps.media.services import attach_files_to_page
from apps.wiki.models import WikiPage
from apps.wiki.services.markdown import extract_summary
from apps.wiki.services.pages import create_page_from_markdown


class CreateWikiPageView(LoginRequiredMixin, TemplateView):
    template_name = "wiki/create_page.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.ai.services import get_ai_service
        from apps.seo.services import site_defaults

        ctx["seo"] = site_defaults()
        ctx["ai_configured"] = get_ai_service().is_configured
        return ctx

    def post(self, request, *args, **kwargs):
        title = request.POST.get("title", "").strip()
        summary = request.POST.get("summary", "").strip()
        raw_content = request.POST.get("content", "").strip()
        publish = request.POST.get("publish", "on") == "on"
        raw_markdown = request.POST.get("raw_markdown", "on") == "on"
        use_ai = request.POST.get("use_ai") == "on" and not raw_markdown
        doc_file = request.FILES.get("document")
        media_files = request.FILES.getlist("media_files")
        cover = request.FILES.get("cover_image")

        if doc_file and not raw_content:
            parsed = parse_uploaded_file(doc_file)
            raw_content = parsed.get("markdown", "")
            if not title:
                title = parsed.get("title", "")

        if not raw_content:
            messages.error(request, "Paste markdown or upload a document.")
            return redirect("wiki:create_page")

        if not title:
            first_line = raw_content.splitlines()[0].lstrip("#").strip() if raw_content else "Untitled"
            title = first_line[:255] or "Untitled"

        if not summary:
            summary = extract_summary(raw_content)

        from apps.ai.services import get_ai_service

        ai = get_ai_service()
        if use_ai and ai.is_configured:
            enriched = ai.enrich_import(raw_content, title=title)
            raw_content = enriched["markdown"]
            title = enriched["title"] or title
            if not summary:
                summary = enriched["summary"]
            raw_markdown = True

        if raw_markdown or raw_content.lstrip().startswith(("#", "```", "-", "*", "|")):
            status = WikiPage.Status.PUBLISHED if publish else WikiPage.Status.DRAFT
            page = create_page_from_markdown(
                title=title,
                content=raw_content,
                author=request.user,
                status=status,
                split_sections=True,
            )
            if summary:
                page.summary = summary
                page.save(update_fields=["summary", "updated_at"])
        else:
            page = import_text_as_wiki_page(
                raw_content,
                title=title,
                author=request.user,
                use_ai=use_ai,
                publish=publish,
            )

        if cover:
            page.cover_image = cover
            page.save(update_fields=["cover_image", "updated_at"])

        attach_files_to_page(page, media_files)

        messages.success(request, f'Wiki page “{page.title}” created.')
        return redirect(page.get_absolute_url())
