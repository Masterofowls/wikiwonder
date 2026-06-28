"""Detect broken internal and external links in wiki content."""
from __future__ import annotations

import urllib.error
import urllib.request
from urllib.parse import unquote

from apps.wiki.models import WikiPage
from apps.wiki.services.link_graph import extract_link_targets
from apps.wiki.services.wikilinks import resolve_wiki_slug

USER_AGENT = "WikiWonder/1.0 LinkChecker"


def check_internal_links(content: str) -> list[dict]:
    """Return list of {target, status, resolved_slug?} for broken internal links."""
    targets = extract_link_targets(content)
    published = set(
        WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED).values_list("slug", flat=True)
    )
    broken: list[dict] = []
    for slug in targets["internal_slugs"]:
        clean = unquote(slug).strip("/")
        if clean not in published:
            resolved = resolve_wiki_slug(clean.replace("-", " "))
            if resolved and resolved in published:
                broken.append({"target": clean, "status": "redirectable", "resolved_slug": resolved})
            else:
                broken.append({"target": clean, "status": "missing"})
    return broken


def check_external_url(url: str, *, timeout: int = 8) -> str:
    """Return ok, redirect, client_error, server_error, or unreachable."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            if 200 <= code < 300:
                return "ok"
            if 300 <= code < 400:
                return "redirect"
            if 400 <= code < 500:
                return "client_error"
            return "server_error"
    except urllib.error.HTTPError as exc:
        if exc.code in (405, 501):
            return check_external_url_get(url, timeout=timeout)
        if 400 <= exc.code < 500:
            return "client_error"
        return "server_error"
    except Exception:
        return check_external_url_get(url, timeout=timeout)


def check_external_url_get(url: str, *, timeout: int = 8) -> str:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 300:
                return "ok"
            if 300 <= resp.status < 400:
                return "redirect"
            if 400 <= resp.status < 500:
                return "client_error"
            return "server_error"
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code < 500:
            return "client_error"
        return "server_error"
    except Exception:
        return "unreachable"


def check_external_links(content: str, *, max_urls: int = 15) -> list[dict]:
    targets = extract_link_targets(content)
    results: list[dict] = []
    for url in targets["external_urls"][:max_urls]:
        if "wikipedia.org" in url:
            results.append({"url": url, "status": "ok"})
            continue
        results.append({"url": url, "status": check_external_url(url)})
    return results


def audit_page_links(page: WikiPage) -> dict:
    internal = check_internal_links(page.content or "")
    external = check_external_links(page.content or "")
    return {
        "page": page.slug,
        "broken_internal": [x for x in internal if x["status"] == "missing"],
        "fixable_internal": [x for x in internal if x["status"] == "redirectable"],
        "external": external,
        "broken_external": [x for x in external if x["status"] in ("client_error", "unreachable")],
    }
