"""Tests for media blocks, previews, SEO, MCP, and import/export."""
import json
from pathlib import Path

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.imports.export import export_page
from apps.previews.services import build_preview
from apps.seo.services import robots_txt_content, wiki_page_seo
from apps.wiki.models import WikiPage
from apps.wiki.services.embeds import process_embeds
from apps.wiki.services.pages import create_page_from_markdown


@pytest.mark.django_db
class TestMediaServing:
    @override_settings(SERVE_MEDIA=True)
    def test_media_url_not_captured_by_cms(self, client, tmp_path):
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        sample = media_root / "covers" / "sample.png"
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_bytes(b"\x89PNG\r\n\x1a\n")

        response = client.get("/media/covers/sample.png")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("image/")

    @override_settings(SERVE_MEDIA=True)
    def test_media_trailing_slash_redirects_to_file(self, client):
        media_root = Path(settings.MEDIA_ROOT)
        sample = media_root / "covers" / "slash.png"
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_bytes(b"\x89PNG\r\n\x1a\n")

        response = client.get("/media/covers/slash.png/")
        assert response.status_code == 301
        assert response["Location"] == "/media/covers/slash.png"

        served = client.get("/media/covers/slash.png")
        assert served.status_code == 200


@pytest.mark.django_db
class TestPreviews:
    def test_pdf_preview(self):
        result = build_preview(url="https://example.com/doc.pdf", block_type="pdf", title="Paper")
        assert result["type"] == "pdf"
        assert "iframe" in result["html"]

    def test_code_preview(self):
        result = build_preview(content="print('hi')", block_type="code", language="python")
        assert "language-python" in result["html"]

    def test_wiki_embed_in_markdown(self):
        md = '```wiki-video url="https://example.com/v.mp4" title="Clip"\n```'
        html = process_embeds(md)
        assert "wiki-media--video" in html

    def test_media_link_renders_video(self):
        from apps.wiki.services.markdown import render_markdown

        md = "[My clip](/media/blocks/demo.mp4)"
        html = render_markdown(md)
        assert "wiki-media--video" in html
        assert "<video" in html
        assert 'wiki-url-highlight' not in html or "wiki-media--video" in html

    def test_media_image_link_renders_img(self):
        from apps.wiki.services.markdown import render_markdown

        md = "[Photo](/media/editor/1/photo.png)"
        html = render_markdown(md)
        assert "<img" in html
        assert "wiki-media" in html

    def test_malformed_image_markdown_hides_orphan_text(self):
        from apps.wiki.services.markdown import render_markdown

        md = "!Telegram Messenger 1024/media/editor/4/telegram-messenger-1024.png"
        html = render_markdown(md)
        assert "<img" in html
        assert "Telegram Messenger 1024" in html
        assert "!Telegram" not in html
        assert "<figcaption" not in html
        assert "/media/editor/4/telegram-messenger-1024.png" not in html.replace(
            'src="/media/editor/4/telegram-messenger-1024.png"', ""
        )

    def test_unfenced_wiki_video_renders_without_raw_text(self):
        from apps.wiki.services.markdown import render_markdown

        md = (
            'wiki-video url="/media/editor/4/test.mp4" '
            'title="226e464fba4686d8908ca64c5f504646 Ezgif.Com Gif Maker"'
        )
        html = render_markdown(md)
        assert "<video" in html
        assert "wiki-video url=" not in html
        assert "<figcaption" not in html
        assert "Ezgif" not in html

    def test_summary_strips_media_embeds(self):
        from apps.wiki.services.markdown import extract_summary, is_media_metadata

        md = 'wiki-video url="/media/editor/4/test.mp4" title="Hash Ezgif Maker"'
        assert is_media_metadata(extract_summary(md)) or extract_summary(md) == ""


@pytest.mark.django_db
class TestSEO:
    def test_robots_txt(self):
        content = robots_txt_content()
        assert "Sitemap:" in content
        assert "Disallow: /admin/" in content

    def test_page_seo(self, django_user_model):
        user = django_user_model.objects.create_user("seo", password="x")
        page = create_page_from_markdown("SEO Page", "Content", author=user, status=WikiPage.Status.PUBLISHED)
        seo = wiki_page_seo(page)
        assert seo["og_title"] == "SEO Page"
        assert seo["json_ld"]["@type"] == "Article"


@pytest.mark.django_db
class TestMCP:
    def test_mcp_tools_list(self, client):
        response = client.get(reverse("mcp:rpc"))
        assert response.status_code == 200
        assert "tools" in response.json()

    def test_mcp_search(self, client, django_user_model):
        django_user_model.objects.create_user("mcp", password="x")
        create_page_from_markdown("MCP Topic", "Unique keyword xyzzy", author=None, status=WikiPage.Status.PUBLISHED)
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "search_wiki", "arguments": {"query": "xyzzy"}},
        }
        response = client.post(reverse("mcp:rpc"), data=json.dumps(body), content_type="application/json")
        data = response.json()
        assert data["result"]["results"]


@pytest.mark.django_db
class TestExport:
    def test_export_markdown(self, django_user_model):
        user = django_user_model.objects.create_user("exp", password="x")
        page = create_page_from_markdown("Export Me", "## Hi", author=user)
        payload = export_page(page, "md")
        assert "# Export Me" in payload["content"]
