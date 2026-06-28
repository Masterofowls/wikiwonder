"""Convert pasted or imported Wikipedia text into wiki markdown with citations."""
from __future__ import annotations

import re

from apps.imports.sources.wikipedia_citations import fetch_wikipedia_citations
from apps.wiki.services.citations import replace_numeric_citations, strip_wikipedia_editorial_markers
from apps.wiki.services.wikilinks import linkify_internal_pages, process_wikilink_syntax

WIKIPEDIA_PASTE_HINT = re.compile(r"\[\d{1,3}\].{40,}", re.DOTALL)
SECTION_LINE = re.compile(
    r"^(Main article|Further information|See also|Notes|References|External links)\s*:\s*(.+)$",
    re.I,
)
HEADING_CANDIDATE = re.compile(r"^[A-Z][A-Za-z0-9 ,\-–()'\"/]{2,90}$")


def is_wikipedia_paste(text: str) -> bool:
    if not text or len(text) < 120:
        return False
    if WIKIPEDIA_PASTE_HINT.search(text):
        return True
    cite_count = len(re.findall(r"\[\d{1,3}\]", text))
    return cite_count >= 2 and len(text) > 400


def _extract_title(line: str) -> str:
    """Pull article title from a Wikipedia opener sentence."""
    clean = strip_wikipedia_editorial_markers(line)
    cite = re.search(r"\[\d{1,3}\]", clean)
    if cite:
        clean = clean[: cite.start()].strip()
    if " is " in clean:
        return clean.split(" is ", 1)[0].strip().rstrip(".")
    if len(clean) > 100 and "." in clean:
        return clean.split(".", 1)[0].strip()
    return clean[:120].strip()


def _format_hatline(line: str) -> str:
    match = SECTION_LINE.match(line.strip())
    if not match:
        return line
    kind, target = match.group(1), match.group(2).strip()
    if " and " in target:
        parts = [p.strip() for p in target.split(" and ")]
        links = " and ".join(f"[[{p}]]" for p in parts)
        return f"> **{kind}:** {links}"
    return f"> **{kind}:** [[{target}]]"


def _detect_heading_level(
    line: str,
    prev_blank: bool,
    next_line: str | None,
    *,
    prev_is_heading: bool = False,
) -> int:
    stripped = line.strip()
    if not stripped or stripped.startswith(">"):
        return 0
    if SECTION_LINE.match(stripped):
        return 0
    if stripped.endswith(".") or stripped.endswith(":"):
        return 0
    if re.search(r"\[\d{1,3}\]", stripped) and len(stripped) > 50:
        return 0
    if not HEADING_CANDIDATE.match(stripped):
        return 0
    if prev_is_heading:
        return 3 if "(" in stripped or len(stripped) < 60 else 2
    if not prev_blank and not stripped.isupper():
        return 0
    if "(" in stripped and len(stripped) < 55:
        return 3
    if next_line and next_line.strip():
        return 2
    return 0


def _structure_sections(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    title_set = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue

        hat = _format_hatline(stripped)
        if hat != stripped:
            out.append(hat)
            continue

        prev_blank = i == 0 or not lines[i - 1].strip()
        prev_line = lines[i - 1].strip() if i > 0 else ""
        prev_is_heading = prev_line.startswith("#")
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        level = _detect_heading_level(
            stripped,
            prev_blank,
            next_line,
            prev_is_heading=prev_is_heading,
        )

        if not title_set and i == 0:
            title = _extract_title(stripped)
            out.append(f"# {title}")
            title_set = True
            if stripped and stripped != title:
                out.append(stripped)
            continue

        if not title_set and level == 0 and i < 3 and len(stripped) < 120:
            title = strip_wikipedia_editorial_markers(stripped)
            out.append(f"# {title}")
            title_set = True
            continue

        if level == 2:
            out.append(f"## {stripped}")
        elif level == 3:
            out.append(f"### {stripped}")
        else:
            out.append(stripped)

    return "\n".join(out)


def normalize_wikipedia_paste(
    text: str,
    *,
    source_url: str = "",
    link_internal: bool = True,
) -> dict:
    """
    Normalize pasted Wikipedia plaintext to wiki markdown.

    Returns {markdown, title, citation_count, references}.
    """
    raw = text.strip()
    refs = fetch_wikipedia_citations(source_url) if source_url else {}
    cleaned = strip_wikipedia_editorial_markers(raw)
    structured = _structure_sections(cleaned)
    with_cites = replace_numeric_citations(structured, refs)
    with_wikilinks = process_wikilink_syntax(with_cites)
    markdown = linkify_internal_pages(with_wikilinks) if link_internal else with_wikilinks

    title = ""
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if not title:
        first = cleaned.splitlines()[0].strip()
        title = strip_wikipedia_editorial_markers(first)[:255]

    cite_nums = set(re.findall(r"\[(\d{1,3})\]", raw))
    return {
        "markdown": markdown.strip() + "\n",
        "title": title,
        "citation_count": len(cite_nums),
        "references": refs,
        "source_url": source_url,
    }
