"""modeltranslation registration for wiki content."""
from modeltranslation.translator import TranslationOptions, translator

from apps.media.models import ContentBlock
from apps.wiki.models import Category, WikiPage, WikiSection


class WikiPageTranslationOptions(TranslationOptions):
    fields = ("title", "summary", "content")


class WikiSectionTranslationOptions(TranslationOptions):
    fields = ("title", "content")


class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class ContentBlockTranslationOptions(TranslationOptions):
    fields = ("title", "description")


translator.register(WikiPage, WikiPageTranslationOptions)
translator.register(WikiSection, WikiSectionTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(ContentBlock, ContentBlockTranslationOptions)
