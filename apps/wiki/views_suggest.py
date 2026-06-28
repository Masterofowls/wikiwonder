"""Public edit suggestions (fork / PR-style workflow)."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.wiki.models import EditSuggestion, WikiPage


class SuggestEditView(LoginRequiredMixin, TemplateView):
    """Propose changes without direct publish rights."""

    template_name = "wiki/suggest_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.page = get_object_or_404(WikiPage, slug=kwargs["slug"], status=WikiPage.Status.PUBLISHED)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page"] = self.page
        ctx["initial_content"] = self.page.content
        ctx["initial_title"] = self.page.title
        return ctx

    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, status=WikiPage.Status.PUBLISHED)
        title = request.POST.get("title", "").strip() or page.title
        content = request.POST.get("content", "").strip()
        summary = request.POST.get("change_summary", "").strip()

        if not content:
            messages.error(request, "Suggested content cannot be empty.")
            return redirect("wiki:suggest_edit", slug=slug)

        EditSuggestion.objects.create(
            page=page,
            author=request.user,
            title=title[:255],
            content=content,
            change_summary=summary or "Suggested edit",
        )
        messages.success(request, "Your edit suggestion was submitted for review.")
        return redirect(page.get_absolute_url())


class ApproveSuggestionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            raise Http404
        suggestion = get_object_or_404(EditSuggestion, pk=pk, status=EditSuggestion.Status.PENDING)
        page = suggestion.page
        from apps.wiki.services.pages import update_page_content

        page.title = suggestion.title
        page.save(update_fields=["title", "updated_at"])
        update_page_content(
            page,
            suggestion.content,
            editor=request.user,
            change_summary=f"Applied suggestion #{suggestion.pk}",
        )
        suggestion.status = EditSuggestion.Status.APPROVED
        suggestion.reviewer = request.user
        suggestion.reviewed_at = timezone.now()
        suggestion.save(update_fields=["status", "reviewer", "reviewed_at"])
        messages.success(request, f"Applied suggestion for “{page.title}”.")
        return redirect(page.get_absolute_url())
