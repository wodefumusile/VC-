"""HTML Cleaner — normalizes input from Markdown / HTML / plain text to clean HTML."""

from __future__ import annotations

import re
from loguru import logger


def normalize_input(text: str) -> tuple[str, str]:
    """Detect format and normalize to clean HTML.

    Args:
        text: Raw input (Markdown, HTML, or plain text)

    Returns:
        (html_content, detected_format)
    """
    text = text.strip()
    if not text:
        return "", "empty"

    # Detect HTML
    if bool(re.search(r"<(h[1-6]|p|div|section|ul|ol|li|br|strong|em|blockquote|img)", text)):
        logger.info("Detected HTML input")
        return _clean_html(text), "html"

    # Detect Markdown (##, **, - list, etc.)
    if bool(re.search(r"(^|\n)#{1,3}\s|(\*\*|__)|(^|\n)[-*+]\s|\[.+\]\(.+\)", text)):
        logger.info("Detected Markdown input")
        return _markdown_to_html(text), "markdown"

    # Plain text
    logger.info("Detected plain text input")
    return _plain_to_html(text), "text"


def _clean_html(html: str) -> str:
    """Clean and normalize HTML.

    - Strip script/style tags
    - Remove empty paragraphs
    - Normalize whitespace
    """
    # Remove script/style
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove empty paragraphs
    html = re.sub(r"<p[^>]*>\s*</p>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<p[^>]*><br\s*/?>\s*</p>", "", html, flags=re.IGNORECASE)
    # Normalize multiple newlines
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def _markdown_to_html(md: str) -> str:
    """Simple Markdown → HTML conversion.

    Handles: headings, bold, lists, blockquotes, links.
    """
    lines = md.strip().split("\n")
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append("")
            continue

        # Headings
        if re.match(r"^###\s", stripped):
            result.append(f"<h3>{stripped[4:]}</h3>")
            continue
        if re.match(r"^##\s", stripped):
            result.append(f"<h2>{stripped[3:]}</h2>")
            continue
        if re.match(r"^#\s", stripped):
            result.append(f"<h1>{stripped[2:]}</h1>")
            continue

        # Unordered list
        if re.match(r"^[-*+]\s", stripped):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{stripped[2:]}</li>")
            continue

        # Blockquote
        if stripped.startswith(">"):
            result.append(f"<blockquote>{stripped[1:].strip()}</blockquote>")
            continue

        # Close list if we were in one
        if in_list:
            result.append("</ul>")
            in_list = False

        # Regular paragraph
        result.append(f"<p>{stripped}</p>")

    if in_list:
        result.append("</ul>")

    return "\n".join(result)


def _plain_to_html(text: str) -> str:
    """Convert plain text to HTML paragraphs.

    Double newline = new paragraph.
    """
    paragraphs = re.split(r"\n\s*\n", text.strip())
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Check if it looks like a heading (short, starts with number/chinese num)
        if len(p) <= 40 and re.match(r"^(第[一二三四五六七八九十\d]|[一二三四五六七八九十\d]+[、．.])", p):
            result.append(f"<h2>{p}</h2>")
        else:
            result.append(f"<p>{p.replace(chr(10), ' ')}</p>")
    return "\n".join(result)
