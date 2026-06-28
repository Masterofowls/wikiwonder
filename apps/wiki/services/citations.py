"""Wikipedia-style numeric citations with hover previews."""
from __future__ import annotations

import re

CITATION_INLINE = re.compile(r"\[(\d{1,3})\]")
CITATION_DEF_LINE = re.compile(
    r"^\[cite-(\d{1,3})\]:\s*(\S+)\s+\"(.+)\"?\s*$",
    re.MULTILINE,
)
CITATION_DEF_LINE_LOOSE = re.compile(
    r"^\[cite-(\d{1,3})\]:\s*(\S+)(?:\s+\"(.+)\")?\s*$",
    re.MULTILINE,
)


def replace_numeric_citations(text: str, refs: dict[str, dict] | None = None) -> str:
    """
    Turn [1] into reference-style markdown [1][cite-1] and append ## References block.

    refs: { "1": {"url": "...", "label": "..."}, ... }
    """
    refs = refs or {}
    seen: set[str] = set()

    def repl(match: re.Match) -> str:
        num = match.group(1)
        seen.add(num)
        return f"[{num}][cite-{num}]"

    body = CITATION_INLINE.sub(repl, text)
    if not seen:
        return body

    lines = [body.rstrip(), "", "## References", ""]
    for num in sorted(seen, key=int):
        ref = refs.get(num, {})
        url = ref.get("url") or f"#cite-note-{num}"
        label = (ref.get("label") or f"Citation {num}").replace('"', "'")
        lines.append(f'[cite-{num}]: {url} "{label}"')
    return "\n".join(lines).strip() + "\n"


def strip_wikipedia_editorial_markers(text: str) -> str:
    """Remove [citation needed], [non-primary source needed], title letter notes like [a]."""
    text = re.sub(
        r"\[(?:citation needed|non-primary source needed|clarification needed)\]",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\[([a-z])\](?=\s|$|[.,;])", "", text, flags=re.I)
    return re.sub(r"  +", " ", text)


def enrich_citation_html(html: str) -> str:
    """Add preview classes to numeric citation links and reference anchors."""
    html = re.sub(
        r'<a href="([^"]+)"([^>]*)>(\d{1,3})</a>',
        (
            r'<a class="wiki-cite-ref wiki-url-highlight" href="\1"\2 '
            r'data-cite="\3" data-url="\1" title="Citation \3">\3</a>'
        ),
        html,
    )
    html = re.sub(
        r'<li id="(cite-note-\d+)"',
        r'<li id="\1" class="wiki-cite-note"',
        html,
    )
    html = re.sub(
        r'<ol class="references"',
        r'<ol class="references wiki-references"',
        html,
    )
    return html
