"""Web UI for importing wiki pages from external URLs."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.imports.sources.fetch import FetchError
from apps.imports.url_import import (
    get_supported_sources,
    import_url_as_wiki_page,
    preview_url_import,
)


class ImportFromUrlView(LoginRequiredMixin, TemplateView):
    template_name = "wiki/import_url.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.ai.services import get_ai_service
        from apps.seo.services import site_defaults

        ctx["seo"] = site_defaults()
        ctx["sources"] = get_supported_sources()
        ctx["ai_configured"] = get_ai_service().is_configured
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "import")
        url = request.POST.get("url", "").strip()
        source_type = request.POST.get("source_type", "auto")
        use_ai = request.POST.get("use_ai") == "on"
        publish = request.POST.get("publish") == "on"
        download_media = request.POST.get("download_media") == "on"
        title_override = request.POST.get("title", "").strip()

        if not url:
            messages.error(request, "Enter a URL to import.")
            return redirect("wiki:import_url")

        if action == "preview":
            try:
                preview = preview_url_import(
                    url,
                    source_type=source_type,
                    use_ai=use_ai,
                    download_media=download_media,
                    user=request.user,
                )
            except FetchError as exc:
                messages.error(request, str(exc))
                return redirect("wiki:import_url")

            ctx = self.get_context_data()
            ctx.update(
                {
                    "preview": preview,
                    "form_url": url,
                    "form_source_type": source_type,
                    "form_use_ai": use_ai,
                    "form_publish": publish,
                    "form_download_media": download_media,
                    "form_title": title_override or preview["title"],
                }
            )
            return self.render_to_response(ctx)

        try:
            page = import_url_as_wiki_page(
                url,
                title=title_override,
                author=request.user,
                source_type=source_type,
                use_ai=use_ai,
                publish=publish,
                download_media=download_media,
            )
        except FetchError as exc:
            messages.error(request, str(exc))
            return redirect("wiki:import_url")

        messages.success(request, f'Imported “{page.title}” from {url}')
        return redirect(page.get_absolute_url())
