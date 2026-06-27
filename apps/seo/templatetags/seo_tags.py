import json

from django import template

from apps.seo.services import site_defaults, wiki_page_seo

register = template.Library()


@register.inclusion_tag("seo/meta_tags.html", takes_context=True)
def seo_meta(context):
    seo = context.get("seo") or site_defaults()
    return {"seo": seo}


@register.inclusion_tag("seo/json_ld.html", takes_context=True)
def seo_json_ld(context):
    seo = context.get("seo") or site_defaults()
    ld = seo.get("json_ld")
    return {"json_ld": json.dumps(ld) if ld else ""}


@register.inclusion_tag("seo/django_meta.html", takes_context=True)
def django_meta_tags(context):
    return {"m": context.get("django_meta")}


@register.simple_tag
def wiki_seo(page):
    return wiki_page_seo(page)
