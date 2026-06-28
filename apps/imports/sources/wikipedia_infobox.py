"""Extract Wikipedia infoboxes into markdown summary tables."""
from __future__ import annotations

import re

from bs4 import Tag


def extract_infobox_markdown(root: Tag) -> tuple[str, Tag | None]:
    """
    Convert first infobox table to markdown and remove it from the tree.

    Returns (markdown_block, infobox_element).
    """
    infobox = root.select_one("table.infobox, table.vertical-navbox.infobox")
    if not infobox:
        return "", None

    title = ""
    title_el = infobox.select_one(".infobox-title, th.infobox-header, caption")
    if title_el:
        title = title_el.get_text(" ", strip=True)

    rows: list[tuple[str, str]] = []
    for tr in infobox.find_all("tr"):
        header = tr.find("th")
        data = tr.find("td")
        if header and data:
            label = header.get_text(" ", strip=True)
            value = data.get_text(" ", strip=True)
            if label and value and label != title:
                rows.append((label, re.sub(r"\s+", " ", value)[:500]))
        elif data and not header:
            val = data.get_text(" ", strip=True)
            if val and not title:
                title = val

    if not rows and not title:
        return "", infobox

    lines = ["> **Infobox**"]
    if title:
        lines.append(f"> ### {title}")
    lines.append(">")
    if rows:
        lines.append("> | Field | Value |")
        lines.append("> | --- | --- |")
        for label, value in rows[:20]:
            safe_val = value.replace("|", "\\|")
            lines.append(f"> | {label} | {safe_val} |")
    return "\n".join(lines) + "\n\n", infobox
