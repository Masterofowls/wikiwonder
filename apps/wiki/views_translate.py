"""Generate translated wiki page content via Lara Translate."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from apps.wiki.models import WikiPage
from apps.wiki.permissions import can_edit_page
from apps.wiki.services.lara_translate import auto_translate_wiki_page, get_lara_service


class GenerateTranslationView(LoginRequiredMixin, View):
    """POST: generate or refresh Russian translation for a wiki page."""

    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug)
        if not can_edit_page(request.user, page):
            raise Http404

        service = get_lara_service()
        if not service.is_configured:
            messages.error(request, "Lara Translate is not configured.")
            return redirect(page.get_absolute_url())

        results = auto_translate_wiki_page(page, force=True)
        if results.get("ru"):
            page.refresh_from_db()
            messages.success(request, f'Russian translation generated for “{page.title}”.')
            return redirect(f"{page.get_absolute_url()}?lang=ru")

        messages.error(request, "Translation failed. Check Lara Translate credentials and try again.")
        return redirect(page.get_absolute_url())
