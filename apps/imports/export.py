"""Export wiki pages to multiple formats."""
from __future__ import annotations

import csv
import io
import json

from django.http import HttpResponse

from apps.wiki.models import WikiPage


def export_page(page: WikiPage, fmt: str = "md") -> dict | HttpResponse:
    fmt = (fmt or "md").lower()
    if fmt == "json":
        return {
            "slug": page.slug,
            "title": page.title,
            "summary": page.summary,
            "content": page.content,
            "status": page.status,
            "category": page.category.name if page.category else None,
            "tags": [t.name for t in page.tags.all()],
            "sections": [
                {"title": s.title, "content": s.content, "anchor": s.anchor}
                for s in page.sections.all()
            ],
        }

    if fmt == "md":
        lines = [f"# {page.title}", ""]
        if page.summary:
            lines += [page.summary, ""]
        lines.append(page.content or "")
        return {"format": "md", "content": "\n".join(lines), "filename": f"{page.slug}.md"}

    if fmt == "txt":
        text = f"{page.title}\n\n{page.summary}\n\n{page.content or ''}"
        return {"format": "txt", "content": text, "filename": f"{page.slug}.txt"}

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["slug", "title", "summary", "status", "category"])
        writer.writerow([
            page.slug,
            page.title,
            page.summary,
            page.status,
            page.category.name if page.category else "",
        ])
        return {"format": "csv", "content": output.getvalue(), "filename": f"{page.slug}.csv"}

    return {"error": f"Unsupported export format: {fmt}"}


def export_pages_queryset(qs, fmt: str = "json") -> dict:
    if fmt == "json":
        return {
            "pages": [
                export_page(p, "json") if isinstance(export_page(p, "json"), dict) else {}
                for p in qs
            ]
        }
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["slug", "title", "summary", "status", "updated_at"])
        for p in qs:
            writer.writerow([p.slug, p.title, p.summary, p.status, p.updated_at.isoformat()])
        return {"format": "csv", "content": output.getvalue(), "filename": "wiki-export.csv"}
    if fmt == "xlsx":
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Wiki Pages"
        ws.append(["slug", "title", "summary", "status", "updated_at"])
        for p in qs:
            ws.append([p.slug, p.title, p.summary, p.status, p.updated_at.isoformat()])
        buf = io.BytesIO()
        wb.save(buf)
        return {"format": "xlsx", "content_bytes": buf.getvalue(), "filename": "wiki-export.xlsx"}
    return {"error": f"Unsupported bulk format: {fmt}"}


def export_http_response(payload: dict) -> HttpResponse:
    if "content_bytes" in payload:
        resp = HttpResponse(
            payload["content_bytes"],
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    elif payload.get("format") == "json":
        resp = HttpResponse(json.dumps(payload, indent=2), content_type="application/json")
    else:
        resp = HttpResponse(payload.get("content", ""), content_type="text/plain; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{payload.get("filename", "export")}"'
    return resp
