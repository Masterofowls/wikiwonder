"""Lara Translate integration for automatic wiki page translations."""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from apps.wiki.models import WikiPage

logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 6000


class LaraTranslateService:
    """Translate wiki content via Lara Translate SDK."""

    def __init__(self):
        self.access_key_id = getattr(settings, "LARA_ACCESS_KEY_ID", "")
        self.access_key_secret = getattr(settings, "LARA_ACCESS_KEY_SECRET", "")
        self.source_lang = getattr(settings, "LARA_SOURCE_LANGUAGE", "en")
        self.target_langs = getattr(settings, "LARA_TARGET_LANGUAGES", ["ru"])
        self._translator = None

    @property
    def is_configured(self) -> bool:
        return bool(self.access_key_id and self.access_key_secret)

    @property
    def translator(self):
        if not self.is_configured:
            raise ValueError("LARA_ACCESS_KEY_ID and LARA_ACCESS_KEY_SECRET are required")
        if self._translator is None:
            from lara_sdk import AccessKey, Translator

            credentials = AccessKey(
                id=self.access_key_id,
                secret=self.access_key_secret,
            )
            self._translator = Translator(credentials)
        return self._translator

    def _locale(self, code: str) -> str:
        """Map Django language code to Lara locale."""
        mapping = {
            "en": "en-US",
            "ru": "ru-RU",
            "de": "de-DE",
            "fr": "fr-FR",
            "es": "es-ES",
            "uk": "uk-UA",
        }
        if "-" in code:
            return code
        return mapping.get(code, f"{code}-{code.upper()}")

    def translate_text(self, text: str, *, target: str, source: str | None = None) -> str:
        if not text or not text.strip():
            return text
        source_locale = self._locale(source or self.source_lang)
        target_locale = self._locale(target)
        if len(text) <= MAX_CHUNK_CHARS:
            result = self.translator.translate(
                text,
                source=source_locale,
                target=target_locale,
                content_type="text",
                multiline=True,
            )
            return result.translation or text

        chunks = _split_text_chunks(text)
        translated = []
        for chunk in chunks:
            if not chunk.strip():
                translated.append(chunk)
                continue
            result = self.translator.translate(
                chunk,
                source=source_locale,
                target=target_locale,
                content_type="text",
                multiline=True,
            )
            translated.append(result.translation or chunk)
        return "".join(translated)


def _split_text_chunks(text: str) -> list[str]:
    """Split long markdown on blank lines without breaking mid-paragraph."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    parts = re.split(r"(\n\n+)", text)
    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) > MAX_CHUNK_CHARS and current:
            chunks.append(current)
            current = part
        else:
            current += part
    if current:
        chunks.append(current)
    return chunks or [text]


def get_lara_service() -> LaraTranslateService:
    return LaraTranslateService()


def auto_translate_wiki_page(page: WikiPage, *, force: bool = False) -> dict[str, bool]:
    """
    Populate modeltranslation fields for configured target languages.

    Returns {lang_code: success_bool} for each target language.
    """
    if not getattr(settings, "LARA_AUTO_TRANSLATE", True):
        return {}

    service = get_lara_service()
    if not service.is_configured:
        logger.debug("Lara Translate not configured; skipping auto-translation for page %s", page.pk)
        return {}

    results: dict[str, bool] = {}
    source = settings.LANGUAGE_CODE

    for target in service.target_langs:
        if target == source:
            continue
        try:
            _translate_page_fields(page, service, source=source, target=target, force=force)
            results[target] = True
        except Exception as exc:
            logger.exception("Lara translation failed for page %s → %s: %s", page.pk, target, exc)
            results[target] = False

    return results


def _translate_page_fields(
    page: WikiPage,
    service: LaraTranslateService,
    *,
    source: str,
    target: str,
    force: bool,
) -> None:
    title_field = f"title_{target}"
    summary_field = f"summary_{target}"
    content_field = f"content_{target}"

    if force or not getattr(page, title_field, None):
        setattr(page, title_field, service.translate_text(page.title, target=target, source=source))
    if force or not getattr(page, summary_field, None):
        summary_src = page.summary or ""
        if summary_src:
            setattr(
                page,
                summary_field,
                service.translate_text(summary_src, target=target, source=source),
            )
    if force or not getattr(page, content_field, None):
        content_src = page.content or ""
        if content_src:
            setattr(
                page,
                content_field,
                service.translate_text(content_src, target=target, source=source),
            )

    page.save()

    for section in page.sections.all():
        section_title_field = f"title_{target}"
        section_content_field = f"content_{target}"
        updates = []
        if force or not getattr(section, section_title_field, None):
            setattr(
                section,
                section_title_field,
                service.translate_text(section.title, target=target, source=source),
            )
            updates.append(section_title_field)
        if force or not getattr(section, section_content_field, None):
            setattr(
                section,
                section_content_field,
                service.translate_text(section.content, target=target, source=source),
            )
            updates.append(section_content_field)
        if updates:
            section.save(update_fields=[*updates, "updated_at"])
