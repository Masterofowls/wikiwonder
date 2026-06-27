"""MCP-style JSON-RPC tools for WikiWonder."""
from __future__ import annotations

import json

from django.core.serializers.json import DjangoJSONEncoder

from apps.imports.services import preview_import
from apps.search.services import instant_search
from apps.wiki.models import WikiPage
from apps.wiki.serializers import WikiPageDetailSerializer


def list_tools() -> list[dict]:
    return [
        {
            "name": "search_wiki",
            "description": "Instant full-text search across wiki pages, CMS pages, and links",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["query"],
            },
        },
        {
            "name": "get_page",
            "description": "Fetch a wiki page by slug",
            "inputSchema": {
                "type": "object",
                "properties": {"slug": {"type": "string"}},
                "required": ["slug"],
            },
        },
        {
            "name": "list_pages",
            "description": "List published wiki pages",
            "inputSchema": {
                "type": "object",
                "properties": {"limit": {"type": "integer"}},
            },
        },
        {
            "name": "preview_import",
            "description": "Preview converting raw text/markdown into a wiki page",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "title": {"type": "string"},
                    "use_ai": {"type": "boolean"},
                },
                "required": ["text"],
            },
        },
        {
            "name": "export_page",
            "description": "Export a wiki page as markdown or JSON",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "format": {"type": "string", "enum": ["md", "json"]},
                },
                "required": ["slug"],
            },
        },
    ]


def call_tool(name: str, arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    if name == "search_wiki":
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 8))
        return {"results": instant_search(query, limit=limit)}

    if name == "get_page":
        page = WikiPage.objects.filter(slug=arguments["slug"]).first()
        if not page:
            return {"error": "Page not found"}
        return WikiPageDetailSerializer(page).data

    if name == "list_pages":
        limit = int(arguments.get("limit", 20))
        qs = WikiPage.objects.filter(status=WikiPage.Status.PUBLISHED).order_by("-updated_at")[:limit]
        return {"pages": [{"slug": p.slug, "title": p.title, "url": p.get_absolute_url()} for p in qs]}

    if name == "preview_import":
        return preview_import(
            arguments.get("text", ""),
            title=arguments.get("title", ""),
            use_ai=arguments.get("use_ai", False),
        )

    if name == "export_page":
        from apps.imports.export import export_page

        slug = arguments["slug"]
        fmt = arguments.get("format", "md")
        page = WikiPage.objects.filter(slug=slug).first()
        if not page:
            return {"error": "Page not found"}
        return export_page(page, fmt)

    return {"error": f"Unknown tool: {name}"}


def handle_jsonrpc(body: dict) -> dict:
    """Minimal JSON-RPC 2.0 handler for MCP clients."""
    req_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "wikiwonder", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": list_tools()}
        elif method == "tools/call":
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(exc)}}

    payload = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
    return {"jsonrpc": "2.0", "id": req_id, "result": payload}
