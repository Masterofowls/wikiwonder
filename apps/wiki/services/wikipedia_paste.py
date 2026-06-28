"""Convert pasted or imported Wikipedia text into wiki markdown with citations."""
from __future__ import annotations

import re

from apps.imports.sources.detect import wikipedia_page_title
from apps.imports.sources.wikipedia_citations import fetch_wikipedia_citations
from apps.wiki.services.citations import replace_numeric_citations, strip_wikipedia_editorial_markers
from apps.wiki.services.wikilinks import process_all_wiki_links

WIKIPEDIA_PASTE_HINT = re.compile(r"\[\d{1,3}\].{40,}", re.DOTALL)
BR_TAG = re.compile(r"<br\s*/?>", re.I)
HTML_TAG = re.compile(r"<[^>]+>")
SECTION_LINE = re.compile(
    r"^(Main article|Further information|See also|Notes|References|External links)\s*:\s*(.+)$",
    re.I,
)
HEADING_CANDIDATE = re.compile(r"^[A-Z][A-Za-z0-9 ,\-–()'\"/]{2,90}$")
TABLE_HEADER = re.compile(r"^Compared URL Outcome Reason$", re.I)
TABLE_ROW = re.compile(
    r"^(https?://\S+|data:\S+)\s+(Success|Failure)\s+(.+)$",
    re.I,
)
SKIP_LEAD_LABELS = frozenset(
    {
        "introduction",
        "lead section",
        "overview",
        "summary",
    }
)
SUBJECT_TITLE = re.compile(
    r"the\s+(.+?)\s+\([A-Z]+\)\s+is\s+(?:a|an)\b",
    re.I,
)
SUBJECT_TITLE_PLAIN = re.compile(
    r"the\s+(.+?)\s+is\s+(?:a|an)\s+",
    re.I,
)
SENTENCE_STARTERS = frozenset(
    {
        "since",
        "when",
        "while",
        "because",
        "although",
        "if",
        "as",
        "after",
        "before",
        "during",
        "unlike",
        "there",
        "this",
        "these",
        "those",
        "note",
        "however",
        "therefore",
        "thus",
        "also",
    }
)
PROSE_HTML_TAGS = re.compile(r"<\s*(/?)\s*(script|style|iframe|link)\s*>", re.I)


def is_wikipedia_paste(text: str) -> bool:
    if not text or len(text) < 120:
        return False
    if WIKIPEDIA_PASTE_HINT.search(text):
        return True
    cite_count = len(re.findall(r"\[\d{1,3}\]", text))
    return cite_count >= 2 and len(text) > 400


def _preprocess_html_paste(text: str) -> str:
    """Normalize HTML fragments from browser copy-paste."""
    text = BR_TAG.sub("\n", text)
    text = re.sub(r"(?<![A-Za-z])n computing\b", "In computing", text)
    preserved: dict[str, str] = {}
    counter = 0

    def _keep_prose_tag(match: re.Match) -> str:
        nonlocal counter
        if match.group(1):
            return ""
        tag = match.group(2).lower()
        key = f"__PROSE_TAG_{counter}__"
        counter += 1
        preserved[key] = f"`<{tag}>`"
        return key

    text = PROSE_HTML_TAGS.sub(_keep_prose_tag, text)
    text = HTML_TAG.sub("", text)
    for key, value in preserved.items():
        text = text.replace(key, value)
    lines = [line.strip() for line in text.splitlines()]
    while len(lines) >= 2 and lines[0].lower() in SKIP_LEAD_LABELS and lines[1].lower() in SKIP_LEAD_LABELS:
        lines.pop(0)
    while lines and lines[0].lower() in SKIP_LEAD_LABELS:
        lines.pop(0)
    return "\n".join(lines)


def _title_from_source_url(source_url: str) -> str:
    parsed = wikipedia_page_title(source_url)
    if not parsed:
        return ""
    return parsed[1].replace("_", " ")


def _extract_title_from_content(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower() in SKIP_LEAD_LABELS:
            continue
        match = SUBJECT_TITLE.search(stripped)
        if match:
            name = match.group(1).strip()
            return name[0].upper() + name[1:] if name else name
        match = SUBJECT_TITLE_PLAIN.search(stripped)
        if match:
            name = match.group(1).strip()
            if 3 < len(name) < 80 and name.lower() not in SKIP_LEAD_LABELS:
                return name[0].upper() + name[1:] if name else name
        if len(stripped) > 40:
            break
    return ""


def _convert_comparison_tables(text: str) -> str:
    """Turn Wikipedia comparison-table paste blocks into markdown tables."""
    lines = text.splitlines()
    out: list[str] = []
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if TABLE_HEADER.match(stripped):
            rows: list[tuple[str, str, str]] = []
            idx += 1
            while idx < len(lines):
                row_line = lines[idx].strip()
                if not row_line:
                    break
                match = TABLE_ROW.match(row_line)
                if not match:
                    break
                rows.append((match.group(1), match.group(2), match.group(3).strip()))
                idx += 1
            if rows:
                out.append("| Compared URL | Outcome | Reason |")
                out.append("| --- | --- | --- |")
                for url, outcome, reason in rows:
                    out.append(f"| {url} | {outcome} | {reason} |")
                out.append("")
                continue
        out.append(lines[idx])
        idx += 1
    return "\n".join(out)


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
    if "<" in target:
        target = HTML_TAG.sub("", target).strip()
    if " and " in target:
        parts = [p.strip() for p in target.split(" and ")]
        links = " and ".join(f"[[{p}]]" for p in parts)
        return f"> **{kind}:** {links}"
    return f"> **{kind}:** [[{target}]]"


def _split_inline_heading(line: str) -> tuple[str | None, str]:
    """Split 'History The concept...' when heading was merged with body after <br> removal."""
    stripped = line.strip()
    for sep in (" ", "  "):
        parts = stripped.split(sep, 1)
        if len(parts) != 2:
            continue
        head, body = parts[0].strip(), parts[1].strip()
        if head.lower() in SENTENCE_STARTERS:
            return None, stripped
        if " " not in head and len(head) < 8:
            return None, stripped
        if (
            HEADING_CANDIDATE.match(head)
            and body
            and body[0].isupper()
            and not SECTION_LINE.match(stripped)
            and not TABLE_ROW.match(stripped)
        ):
            return head, body
    return None, stripped


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


def _structure_sections(text: str, *, source_url: str = "") -> str:
    lines = text.splitlines()
    out: list[str] = []
    title_set = False
    title = _title_from_source_url(source_url) or _extract_title_from_content(text)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue

        if stripped.lower() in SKIP_LEAD_LABELS and not title_set:
            continue

        inline_head, body = _split_inline_heading(stripped)
        if inline_head and body:
            out.append(f"## {inline_head}")
            out.append(body)
            continue

        hat = _format_hatline(stripped)
        if hat != stripped:
            out.append(hat)
            continue

        prev_blank = i == 0 or not lines[i - 1].strip()
        prev_line = lines[i - 1].strip() if i > 0 else ""
        prev_is_heading = prev_line.startswith("#") or (
            bool(prev_line) and HEADING_CANDIDATE.match(prev_line) and not prev_line.endswith(".")
        )
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        level = _detect_heading_level(
            stripped,
            prev_blank,
            next_line,
            prev_is_heading=prev_is_heading,
        )

        if not title_set and title and i < 5:
            out.append(f"# {title}")
            title_set = True
            if stripped.lower() not in SKIP_LEAD_LABELS:
                out.append(stripped)
            continue

        if not title_set and i == 0:
            extracted = _extract_title(stripped) or _extract_title_from_content(stripped)
            if extracted and extracted.lower() not in SKIP_LEAD_LABELS:
                out.append(f"# {extracted}")
                title_set = True
                if stripped != extracted and stripped.lower() not in SKIP_LEAD_LABELS:
                    out.append(stripped)
                continue

        if not title_set and level == 0 and i < 3 and len(stripped) < 120:
            if stripped.lower() not in SKIP_LEAD_LABELS:
                out.append(f"# {strip_wikipedia_editorial_markers(stripped)}")
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
    html_clean = _preprocess_html_paste(raw)
    cleaned = strip_wikipedia_editorial_markers(html_clean)
    tabular = _convert_comparison_tables(cleaned)
    structured = _structure_sections(tabular, source_url=source_url)
    with_cites = replace_numeric_citations(structured, refs)
    markdown = process_all_wiki_links(with_cites) if link_internal else with_cites

    title = ""
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if not title:
        title = _title_from_source_url(source_url) or _extract_title_from_content(cleaned)
    if not title:
        first = cleaned.splitlines()[0].strip() if cleaned else ""
        if first.lower() not in SKIP_LEAD_LABELS:
            title = strip_wikipedia_editorial_markers(first)[:255]

    cite_nums = set(re.findall(r"\[(\d{1,3})\]", raw))
    return {
        "markdown": markdown.strip() + "\n",
        "title": title,
        "citation_count": len(cite_nums),
        "references": refs,
        "source_url": source_url,
    }
