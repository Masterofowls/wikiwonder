"""Authenticated wiki page editing."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from apps.media.services import attach_files_to_page
from apps.wiki.models import WikiPage
from apps.wiki.permissions import can_edit_page
from apps.wiki.services.markdown import extract_summary
from apps.wiki.services.pages import update_page_content


class EditWikiPageView(LoginRequiredMixin, TemplateView):
    template_name = "wiki/create_page.html"

    def dispatch(self, request, *args, **kwargs):
        self.page = get_object_or_404(WikiPage, slug=kwargs["slug"])
        if not can_edit_page(request.user, self.page):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.ai.services import get_ai_service
        from apps.seo.services import site_defaults

        ctx["seo"] = site_defaults()
        ctx["ai_configured"] = get_ai_service().is_configured
        ctx["edit_mode"] = True
        ctx["page"] = self.page
        ctx["initial_title"] = self.page.title
        ctx["initial_summary"] = self.page.summary
        ctx["initial_content"] = self.page.content
        from django.urls import reverse

        ctx["form_action"] = reverse("wiki:edit_page", kwargs={"slug": self.page.slug})
        return ctx

    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug)
        if not can_edit_page(request.user, page):
            raise Http404

        title = request.POST.get("title", "").strip() or page.title
        summary = request.POST.get("summary", "").strip()
        raw_content = request.POST.get("content", "").strip()
        change_summary = request.POST.get("change_summary", "").strip()
        media_files = request.FILES.getlist("media_files")
        cover = request.FILES.get("cover_image")

        if not raw_content:
            messages.error(request, "Page content cannot be empty.")
            return redirect("wiki:edit_page", slug=page.slug)

        if not summary:
            summary = extract_summary(raw_content)

        page.title = title[:255]
        page.summary = summary
        if cover:
            page.cover_image = cover
        page.save(update_fields=["title", "summary", "cover_image", "updated_at"])

        update_page_content(
            page,
            raw_content,
            editor=request.user,
            change_summary=change_summary or "Updated via web editor",
            resplit=True,
        )

        attach_files_to_page(page, media_files)

        messages.success(request, f'Wiki page “{page.title}” updated.')
        return redirect(page.get_absolute_url())
