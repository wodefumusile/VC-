"""Formatter Engine v2.0 — WeChat-compatible article formatting.

Independent from v1.0 content_formatter.
Accepts Markdown, HTML, or plain text.
Uses section+span pattern for ProseMirror compatibility.
"""

from __future__ import annotations

from loguru import logger
from .html_cleaner import normalize_input
from .structure_analyzer import analyze_and_enhance
from .renderer import render, load_template
from backend.services.image_handler import image_handler


def format_article(title: str, content: str, author: str = "",
                   template: str = "knowledge", images: list[dict] = None) -> dict:
    """Format article for WeChat Official Account.

    Full pipeline: normalize → enhance → render → inject images.

    Args:
        title: Article title (max 64 chars)
        content: Raw content (Markdown, HTML, or plain text)
        author: Author name
        template: Template name (technology/business/knowledge/personal)
        images: Optional image records [{position, image_url, type}, ...]

    Returns:
        {"title": str, "content_html": str, "summary": str, "template": str}
    """
    logger.info("FormatterEngine start | template={} | title_len={}", template, len(title))

    # Step 1: Normalize input to clean HTML
    html, fmt = normalize_input(content)
    logger.info("Normalized | format={} | html_len={}", fmt, len(html))

    # Step 2: Smart structure enhancement
    html = analyze_and_enhance(html)

    # Step 3: Render with section+span template
    result = render(title, html, author, template)

    # Step 4: Inject images if provided
    if images:
        result["content_html"] = image_handler.inject_images(result["content_html"], images)

    logger.success("FormatterEngine done | html_len={}", len(result["content_html"]))
    return result
