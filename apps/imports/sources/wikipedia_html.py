"""Transform Wikipedia article HTML into structured wiki markdown."""
from __future__ import annotations

import re
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup, Tag

from apps.imports.sources.convert import html_to_markdown, normalize_wiki_markdown

REMOVE_SELECTORS = (
    ".navbox",
    ".vertical-navbox",
    ".navbox-styles",
    ".metadata",
    ".noprint",
    ".mw-editsection",
    ".mw-jump-link",
    ".mw-references-wrap",
    ".reflist",
    ".references",
    ".sistersitebox",
    ".portal",
    ".toc",
    "#toc",
    ".catlinks",
    ".mw-indicators",
    ".shortdescription",
    ".mw-empty-elt",
    ".infobox-above",
    ".sidebar",
    ".side-box",
    ".mbox-small",
    ".ambox",
    ".tmbox",
    ".ombox",
    ".cmbox",
    ".fmbox",
    ".dablink",
    ".rellink",
    ".mw-cite-backlink",
    ".mw-headline-anchor",
    ".galleryframe",
    ".mw-gallery-traditional",
)

HATNOTE_SELECTORS = (".hatnote", ".dablink", ".rellink")


def _remove_junk(root: Tag) -> None:
    for selector in REMOVE_SELECTORS:
        for node in root.select(selector):
            node.decompose()


def _inline_citation_markers(root: Tag) -> None:
    for sup in root.select("sup.reference"):
        link = sup.select_one("a")
        label = link.get_text(strip=True) if link else sup.get_text(strip=True)
        num = re.sub(r"[^\d]", "", label) or label.strip("[]")
        if num:
            sup.replace_with(f"[{num}]")


def _convert_hatnotes(root: Tag) -> None:
    for selector in HATNOTE_SELECTORS:
        for node in root.select(selector):
            text = node.get_text(" ", strip=True)
            text = re.sub(r"^\s*Main article:\s*", "Main article: ", text, flags=re.I)
            text = re.sub(r"^\s*Further information:\s*", "Further information: ", text, flags=re.I)
            text = re.sub(r"^\s*See also:\s*", "See also: ", text, flags=re.I)
            match = re.match(
                r"^(Main article|Further information|See also|Notes|External links)\s*:\s*(.+)$",
                text,
                re.I,
            )
            if match:
                kind, target = match.group(1), match.group(2).strip()
                if " and " in target:
                    parts = [p.strip() for p in target.split(" and ")]
                    links = " and ".join(f"[[{p}]]" for p in parts)
                    block = f"> **{kind}:** {links}"
                else:
                    block = f"> **{kind}:** [[{target}]]"
                node.replace_with(BeautifulSoup(f"<blockquote>{block}</blockquote>", "html.parser"))
            else:
                node.replace_with(BeautifulSoup(f"<blockquote><em>{text}</em></blockquote>", "html.parser"))


def _wiki_href_to_title(href: str) -> str:
    href = unquote(href.split("#")[0])
    if href.startswith("./"):
        href = href[2:]
    if href.startswith("/wiki/"):
        href = href[6:]
    return href.replace("_", " ").strip()


def _convert_internal_links(root: Tag, lang: str) -> None:
    wiki_prefix = f"https://{lang}.wikipedia.org/wiki/"
    for anchor in root.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith("#"):
            continue
        if href.startswith("/wiki/") or href.startswith("./") or href.startswith(wiki_prefix):
            title = _wiki_href_to_title(href)
            if title.startswith("File:") or title.startswith("Category:"):
                anchor.replace_with(anchor.get_text())
                continue
            anchor.replace_with(f"[[{title}]]")
        elif href.startswith("//"):
            anchor["href"] = "https:" + href
        elif href.startswith("/"):
            anchor["href"] = urljoin(f"https://{lang}.wikipedia.org", href)


def _table_to_markdown(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue
        row = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in cells]
        rows.append(row)
    if not rows:
        return ""

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _convert_tables(root: Tag) -> None:
    for table in root.find_all("table"):
        md = _table_to_markdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"<pre class='wiki-table-md'>{md}</pre>", "html.parser"))
        else:
            table.decompose()


def _resolve_image_url(img: Tag, base_url: str) -> str:
    src = img.get("src") or ""
    if src.startswith("//"):
        src = "https:" + src
    elif src.startswith("/"):
        src = urljoin(base_url, src)
    srcset = img.get("srcset") or ""
    if srcset:
        parts = [p.strip().split()[0] for p in srcset.split(",") if p.strip()]
        if parts:
            best = parts[-1]
            if best.startswith("//"):
                best = "https:" + best
            if best.startswith("http"):
                src = best
    return src


def _convert_media(root: Tag, base_url: str) -> None:
    for thumb in root.select(".thumb, figure"):
        img = thumb.find("img")
        if not img:
            continue
        src = _resolve_image_url(img, base_url)
        if not src:
            continue
        caption = ""
        cap = thumb.select_one(".thumbcaption, figcaption")
        if cap:
            caption = cap.get_text(" ", strip=True)
        alt = caption or img.get("alt") or "Image"
        alt = alt.replace('"', "'")
        replacement = f'<p><img src="{src}" alt="{alt}" /></p>'
        if caption:
            replacement += f"<p><em>{caption}</em></p>"
        thumb.replace_with(BeautifulSoup(replacement, "html.parser"))

    for audio in root.find_all("audio"):
        source = audio.find("source")
        src = source.get("src") if source else audio.get("src")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            title = audio.get("title") or "Audio"
            audio.replace_with(
                BeautifulSoup(f'<p><a href="{src}">{title}</a></p>', "html.parser")
            )

    for video in root.find_all("video"):
        source = video.find("source")
        src = source.get("src") if source else video.get("src")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            title = video.get("title") or "Video"
            video.replace_with(
                BeautifulSoup(f'<p><a href="{src}">{title}</a></p>', "html.parser")
            )

    for img in root.find_all("img"):
        src = _resolve_image_url(img, base_url)
        if not src or "icon" in src.lower():
            img.decompose()
            continue
        img["src"] = src


def _normalize_headings(root: Tag) -> None:
    for level, tag in ((2, "h2"), (3, "h3"), (4, "h4"), (5, "h5")):
        for heading in root.find_all(tag):
            text = heading.get_text(" ", strip=True)
            if text:
                heading.string = text
                heading.name = f"h{level}"


def _extract_table_markdown(html: str) -> str:
    """Pull pre-converted table markdown blocks out of html2text output."""
    html = re.sub(
        r"```\s*(\|[^\n]+\|\n(?:\|[^\n]+\|\n?)+)\s*```",
        r"\1",
        html,
        flags=re.MULTILINE,
    )
    html = re.sub(
        r"<pre class=\"wiki-table-md\">(.*?)</pre>",
        lambda m: m.group(1),
        html,
        flags=re.DOTALL,
    )
    return html


def wikipedia_html_to_markdown(html: str, *, base_url: str, lang: str = "en") -> str:
    """Convert Wikipedia parse HTML to wiki markdown with structure preserved."""
    soup = BeautifulSoup(html or "", "html5lib")
    root = soup.select_one(".mw-parser-output") or soup
    _inline_citation_markers(root)
    _remove_junk(root)
    _convert_hatnotes(root)
    _convert_internal_links(root, lang)
    _convert_tables(root)
    _convert_media(root, base_url)
    _normalize_headings(root)

    md = html_to_markdown(str(root), base_url=base_url)
    md = _extract_table_markdown(md)
    md = re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", r"> \1", md, flags=re.DOTALL)
    md = normalize_wiki_markdown(md)
    return md
