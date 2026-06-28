"""HTTP fetch helpers for remote import sources."""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

USER_AGENT = "WikiWonder/1.0 (+https://wikiwonder.fly.dev; wiki-import)"
DEFAULT_TIMEOUT = 25


class FetchError(Exception):
    """Raised when a remote resource cannot be fetched."""


def fetch_url(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, str]:
    """Fetch URL bytes and return (body, content_type)."""
    req_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        req_headers.update(headers)

    request = urllib.request.Request(url, headers=req_headers)
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
            return body, content_type
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Could not fetch {url}: {exc.reason}") from exc


def fetch_text(url: str, **kwargs) -> tuple[str, str]:
    body, content_type = fetch_url(url, **kwargs)
    charset = "utf-8"
    if "charset=" in content_type.lower():
        charset = content_type.lower().split("charset=")[-1].split(";")[0].strip()
    return body.decode(charset, errors="replace"), content_type


def fetch_json(url: str, **kwargs) -> Any:
    text, _ = fetch_text(url, **kwargs)
    return json.loads(text)


def origin_of(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
