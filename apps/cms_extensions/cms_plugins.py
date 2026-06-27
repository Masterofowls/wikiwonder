"""Custom django CMS plugins for rich Wikipedia-style blocks."""
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.previews.services import build_preview


class WikiEmbedPluginModel(CMSPlugin):
    block_type = models.CharField(max_length=20, default="url")
    source_url = models.URLField(blank=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    code_language = models.CharField(max_length=40, blank=True)


@plugin_pool.register_plugin
class WikiEmbedPlugin(CMSPluginBase):
    model = WikiEmbedPluginModel
    name = _("Wiki embed block")
    render_template = "cms_plugins/wiki_embed.html"
    cache = False

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        context["preview"] = build_preview(
            url=instance.source_url,
            content=instance.content,
            block_type=instance.block_type,
            title=instance.title,
            description=instance.description,
            language=instance.code_language,
        )
        return context


class WikiCodePluginModel(CMSPlugin):
    code = models.TextField()
    syntax = models.CharField(max_length=40, default="python")
    caption = models.CharField(max_length=255, blank=True)


@plugin_pool.register_plugin
class WikiCodePlugin(CMSPluginBase):
    model = WikiCodePluginModel
    name = _("Code snippet")
    render_template = "cms_plugins/wiki_code.html"
    cache = False

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        context["preview"] = build_preview(
            content=instance.code,
            block_type="code",
            title=instance.caption,
            language=instance.syntax,
        )
        return context
